import bpy, bmesh
import os
from pathlib import Path
from ..generic import clamp_count
from ..fill import fill_face

from ...utils import (
    clamp,
    valid_ngon,
    calc_face_dimensions,
    split_faces,
    link_objects,
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
    import_obj,
    local_xyz,
    align_obj,
)

from ..frame import create_multigroup_hole, create_multigroup_frame_and_dw
from ..validations import validate, some_selection, ngon_validation, same_dimensions


@crash_safe
@validate([some_selection, ngon_validation, same_dimensions], ["No faces seleted", "Door creation not supported on non-rectangular n-gon!", "All selected faces need to be of same dimensions"])
def build_door(context, props):
    """ Create door from context and prop, with validations. Intented to be called directly from operator.
    """
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
            face = create_multigroup_hole(bm, aface, prop.size_offset.size, prop.size_offset.offset, 'd', 1, prop.frame.margin, prop.frame.depth)[0]
            (door_faces,door_origins), _, (frame_faces,frame_origin) = create_multigroup_frame_and_dw(bm, [face], prop.frame, 'd', prop.door, None)
            knobs,knob_origins,knob_scales = add_knobs(door_faces, prop.door.thickness, prop.door.knob, prop.door.hinge, prop.door.flip_direction)
            door = split_faces(bm, [[door_faces[0]]], ["Door" for f in door_faces])[0]
            frame = split_faces(bm, [frame_faces], ["Frame"])[0]
            # link objects and set origins
            link_objects([frame], bpy.context.object)
            link_objects([door], frame)
            set_origin(frame, frame_origin)
            set_origin(door, door_origins[0], frame_origin)

            # set knob origin, rotations and scale
            for knob,origin,scale in zip(knobs[0],knob_origins[0],knob_scales[0]):
                link_objects([knob], door)
                knob.matrix_local.translation = origin
                align_obj(knob, normal)
                knob.scale = scale

            fill_door(door, prop)
    return True


def fill_door(door, prop):
    """ Fill individual door face
    """
    with managed_bmesh(door) as bm:
        face = bm.faces[0]

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


def add_knobs(door_faces, door_thickness, knob_type, hinge, flip=False):
    knobs = []
    knob_origins = []
    knob_scales = []
    for door_face in door_faces:
        directory = Path(os.path.dirname(__file__)).parent.parent
        if knob_type == "ROUND":
            knob_front = import_obj(os.path.join(directory, 'assets', 'knob_round.obj'), "Knob")
            knob_back = import_obj(os.path.join(directory, 'assets', 'knob_round.obj'), "Knob")
        elif knob_type == "STRAIGHT":
            knob_front = import_obj(os.path.join(directory, 'assets', 'knob_straight.obj'), "Knob")
            knob_back = import_obj(os.path.join(directory, 'assets', 'knob_straight.obj'), "Knob")
        xyz = local_xyz(door_face)
        door_width,_ = calc_face_dimensions(door_face)
        if hinge == "LEFT":
            if flip:
                knob_origin_front = - xyz[0] * (door_width-0.06) + xyz[1] * 1.0 + xyz[2] * door_thickness
                knob_origin_back = - xyz[0] * (door_width-0.06) + xyz[1] * 1.0
            else:
                knob_origin_front = xyz[0] * (door_width-0.06) + xyz[1] * 1.0 + xyz[2] * door_thickness
                knob_origin_back = xyz[0] * (door_width-0.06) + xyz[1] * 1.0
        elif hinge == "RIGHT":
            if flip:
                knob_origin_front = xyz[0] * (door_width-0.06) + xyz[1] * 1.0 + xyz[2] * door_thickness
                knob_origin_back = xyz[0] * (door_width-0.06) + xyz[1] * 1.0
            else:
                knob_origin_front = - xyz[0] * (door_width-0.06) + xyz[1] * 1.0 + xyz[2] * door_thickness
                knob_origin_back = - xyz[0] * (door_width-0.06) + xyz[1] * 1.0
        if flip:
            if hinge == "LEFT":
                knob_front_scale = (1,-1,-1)
                knob_back_scale = (1,-1,1)
            else:
                knob_front_scale = (1,1,-1)
                knob_back_scale = (1,1,1)
        else:
            if hinge == "LEFT":
                knob_front_scale = (1,-1,1)
                knob_back_scale = (1,-1,-1)
            else:
                knob_front_scale = (1,1,1)
                knob_back_scale = (1,1,-1)
        knobs.append([knob_front,knob_back])
        knob_origins.append([knob_origin_front,knob_origin_back])
        knob_scales.append([knob_front_scale,knob_back_scale])

    return knobs, knob_origins, knob_scales
