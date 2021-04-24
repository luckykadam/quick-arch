import bpy, bmesh
import os
from pathlib import Path
from ..generic import clamp_count
from ..fill import fill_face
from ..arch import fill_arch

from ...utils import (
    clamp,
    valid_ngon,
    calc_face_dimensions,
    split_faces,
    link_objects,
    make_parent,
    calc_edge_median,
    set_origin,
    subdivide_face_horizontally,
    subdivide_face_vertically,
    extrude_face_region,
    managed_bmesh,
    managed_bmesh_edit,
    get_opposite_face,
    get_relative_offset,
    crash_safe,
    deselect,
    import_blend,
    local_xyz,
    align_obj,
    shrink_face,
    verify_facemaps_for_object,
)

from ..frame import create_multigroup_hole, create_multigroup_frame_and_dw
from ..validations import validate, some_selection, ngon_validation, same_dimensions


@crash_safe
@validate([some_selection, ngon_validation, same_dimensions], ["No faces seleted", "Door creation not supported on non-rectangular n-gon!", "All selected faces need to be of same dimensions"])
def build_door(context, props):
    """ Create door from context and prop, with validations. Intented to be called directly from operator.
    """
    verify_facemaps_for_object(context.object)
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        props.init(
            calc_face_dimensions(faces[0]),
            calc_face_dimensions(get_opposite_face(faces[0], bm.faces)),
            get_relative_offset(faces[0], get_opposite_face(faces[0], bm.faces)),
            )
        create_door(bm, faces, props)
    return {"FINISHED"}


def create_door(bm, faces, prop):
    """Create door from face selection
    """
    for face in faces:
        clamp_count(calc_face_dimensions(face)[0], prop.frame.margin * 2, prop)
        array_faces = subdivide_face_horizontally(bm, face, widths=[prop.size_offset.size.x] * prop.count)
        for aface in array_faces:
            normal = aface.normal.copy()
            dw_faces, arch_faces = create_multigroup_hole(bm, aface, prop.size_offset.size, prop.size_offset.offset, 'd', 1, prop.frame.margin, prop.frame.depth, prop.add_arch, prop.arch, prop.only_hole)
            if prop.only_hole:
                bmesh.ops.delete(bm, geom=dw_faces+arch_faces, context="FACES")
            else:
                (door_faces,door_origins), _, (arch_faces,arch_origins), (frame_faces,frame_origin) = create_multigroup_frame_and_dw(bm, dw_faces, arch_faces, prop.frame, 'd', prop.door, None, prop.add_arch, prop.arch)
                knobs,knob_origins,knob_scales = add_knobs(door_faces, door_origins, prop.door.thickness, prop.door.knob, prop.door.flip_direction)
                doors = split_faces(bm, [[f] for f in door_faces], ["Door" for f in door_faces])
                frame = split_faces(bm, [frame_faces], ["Frame"])[0]
                # link objects and set origins
                link_objects([frame], bpy.context.object.users_collection)
                make_parent([frame], bpy.context.object)
                link_objects(doors, bpy.context.object.users_collection)
                make_parent(doors, frame)
                for knob,door in zip(knobs,doors):
                    # link_objects(knob, bpy.context.object.users_collection)
                    make_parent(knob, door)
                set_origin(frame, frame_origin)
                for door,origin in zip(doors,door_origins):
                    set_origin(door, origin, frame_origin)

                # set knob origin, rotations and scale
                for knob,origin,scale in zip(knobs,knob_origins,knob_scales):
                    knob[0].matrix_local.translation = origin[0]
                    align_obj(knob[0], normal)
                    knob[0].scale = scale[0]
                    knob[1].matrix_local.translation = origin[1]
                    align_obj(knob[1], normal)
                    knob[1].scale = scale[1]

                # create arch
                if prop.add_arch:
                    archs = split_faces(bm, [[f] for f in arch_faces], ["Arch" for f in arch_faces])
                    link_objects(archs, bpy.context.object.users_collection)
                    make_parent(archs, bpy.context.object)
                    for arch,arch_origin in zip(archs,arch_origins):
                        set_origin(arch, arch_origin)
                    for arch in archs:
                        fill_arch(arch, prop)

                for door in doors:
                    fill_door(door, prop)
    return True


def fill_door(door, prop):
    """ Fill individual door face
    """
    with managed_bmesh(door) as bm:
        face = bm.faces[0]
        shrink_face(bm, face, 0.002)
        # validate_fill_props(prop)
        back, surrounding, front = extrude_face_region(bm, [face], prop.door.thickness, -face.normal, keep_original=True)
        bmesh.ops.reverse_faces(bm, faces=front+surrounding+back)

        if prop.door.bottom_panel:
            _,door_height = calc_face_dimensions(front[0])
            bottom_panel_height = min(prop.door.bottom_panel_height, door_height-0.2)
            bottom_front, top_front = subdivide_face_vertically(bm, front[0], widths=[bottom_panel_height, door_height-bottom_panel_height])
            bottom_back, top_back = subdivide_face_vertically(bm, back[0], widths=[bottom_panel_height, door_height-bottom_panel_height])
            fill_face(bm, door, bottom_front, bottom_back, prop.door.bottom_fill)
            fill_face(bm, door, top_front, top_back, prop.door.fill)
        else:
            fill_face(bm, door, front[0], back[0], prop.door.fill)


def validate_fill_props(prop):
    if prop.door.fill.fill_type == "LOUVER":
        # XXX keep louver depth less than window depth
        fill = prop.door.fill.louver_fill
        depth = getattr(prop, "door_depth", getattr(prop, "dw_depth", 1e10))
        fill.louver_depth = min(fill.louver_depth, depth)


def add_knobs(door_faces, door_origins, door_thickness, knob_type, flip=False):
    knobs = []
    knob_origins = []
    knob_scales = []
    for door_face,door_origin in zip(door_faces,door_origins):
        directory = Path(os.path.dirname(__file__)).parent.parent
        if knob_type == "ROUND":
            knob_front = import_blend(os.path.join(directory, 'assets', 'knob_round.blend'))[0]
            knob_back = import_blend(os.path.join(directory, 'assets', 'knob_round.blend'))[0]
        elif knob_type == "STRAIGHT":
            knob_front = import_blend(os.path.join(directory, 'assets', 'knob_straight.blend'))[0]
            knob_back = import_blend(os.path.join(directory, 'assets', 'knob_straight.blend'))[0]
        xyz = local_xyz(door_face)
        door_width,_ = calc_face_dimensions(door_face)
        hinge = "LEFT" if local_xyz(door_face)[0].dot(door_origin-door_face.calc_center_bounds()) < 0 else "RIGHT"
        if hinge == "LEFT":
            knob_origin_front = xyz[0] * (door_width-0.06) + xyz[1] * 0.9 + xyz[2] * door_thickness
            knob_origin_back = xyz[0] * (door_width-0.06) + xyz[1] * 0.9
            knob_front_scale = (1,1,-1) if flip else (-1,1,1)
            knob_back_scale = (1,1,1) if flip else (-1,1,-1)
        elif hinge == "RIGHT":
            knob_origin_front = - xyz[0] * (door_width-0.06) + xyz[1] * 0.9 + xyz[2] * door_thickness
            knob_origin_back = - xyz[0] * (door_width-0.06) + xyz[1] * 0.9
            knob_front_scale = (-1,1,-1) if flip else (1,1,1)
            knob_back_scale = (-1,1,1) if flip else (1,1,-1)
        knobs.append([knob_front,knob_back])
        knob_origins.append([knob_origin_front,knob_origin_back])
        knob_scales.append([knob_front_scale,knob_back_scale])

    return knobs, knob_origins, knob_scales
