import bpy, bmesh
import os
from pathlib import Path

from ..generic import clamp_count
from ..fill import fill_face, fill_bars

from ...utils import (
    clamp,
    valid_ngon,
    calc_face_dimensions,
    subdivide_face_horizontally,
    split_faces,
    link_objects,
    set_origin,
    extrude_face_region,
    managed_bmesh,
    managed_bmesh_edit,
    get_opposite_face,
    get_relative_offset,
    crash_safe,
    duplicate_faces,
    deselect,
    import_obj,
    local_xyz,
    align_obj,
)
from ..frame import create_multigroup_hole, create_multigroup_frame_and_dw
from ..validations import validate, some_selection, ngon_validation, same_dimensions


@crash_safe
@validate([some_selection, ngon_validation, same_dimensions], ["No faces seleted", "Window creation not supported on non-rectangular n-gon!", "All selected faces need to be of same dimensions"])
def build_window(context, props):
    """ Create window from context and prop, with validations. Intented to be called directly from operator.
    """
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        props.init(
            calc_face_dimensions(faces[0]),
            calc_face_dimensions(get_opposite_face(faces[0], bm.faces)),
            get_relative_offset(faces[0], get_opposite_face(faces[0], bm.faces)),
            )
        create_window(bm, faces, props)
    return {"FINISHED"}


def create_window(bm, faces, prop):
    """Generate a window
    """
    for face in faces:
        clamp_count(calc_face_dimensions(face)[0], prop.frame.thickness * 2, prop)
        array_faces = subdivide_face_horizontally(bm, face, widths=[prop.size_offset.size.x]*prop.count)
        for aface in array_faces:
            normal = aface.normal.copy()
            face = create_multigroup_hole(bm, aface, prop.size_offset.size, prop.size_offset.offset, 'w', 1, prop.frame.margin, prop.frame.depth)[0]
            _, (window_faces,bar_faces,window_origins), (frame_faces,frame_origin) = create_multigroup_frame_and_dw(bm, [face], prop.frame, 'w', None, prop.window)
            handles,handle_origins,handle_scales = add_handles(window_faces, prop.window.thickness, prop.window.handle, prop.window.hinge, prop.window.flip_direction)
            window = split_faces(bm, [[window_faces[0]]], ["Window" for f in window_faces])[0]
            frame = split_faces(bm, [frame_faces], ["Frame"])[0]
            # link objects and set origins
            link_objects([frame], bpy.context.object)
            link_objects([window], frame)
            link_objects(handles[0], window)
            set_origin(frame, frame_origin)
            set_origin(window, window_origins[0], frame_origin)

            # create bars
            if prop.window.add_bars:
                bars = split_faces(bm, [bar_faces], ["Bars"])[0]
                link_objects([bars], frame)
                set_origin(bars, window_origins[0], frame_origin)
                with managed_bmesh(bars) as bm:
                    fill_bars(bm, bars, bm.faces[0], prop.window.bars)

            # set handle origin, rotations and scale
            for handle,origin,scale in zip(handles[0],handle_origins[0],handle_scales[0]):
                handle.matrix_local.translation = origin
                align_obj(handle, normal)
                handle.scale = scale

            fill_window(window, prop)
    return True


def fill_window(window, prop):
    """Create extra elements on face
    """
    with managed_bmesh(window) as bm:
        face = bm.faces[0]

        # validate_fill_props(prop)
        back, surrounding, front = extrude_face_region(bm, [face], prop.window.thickness, -face.normal, keep_original=True)
        bmesh.ops.reverse_faces(bm, faces=front+surrounding+back)
        fill_face(bm, window, front[0], back[0], prop.window.fill)


def add_handles(window_faces, window_thickness, handle_type, hinge, flip=False):
    handles = []
    handle_origins = []
    handle_scales = []
    for window_face in window_faces:
        directory = Path(os.path.dirname(__file__)).parent.parent
        if handle_type == "STRAIGHT":
            # handle_front = import_obj(directory+"/assets/handle_straight.obj", "Handle")
            handle_back = import_obj(os.path.join(directory, 'assets', 'handle_straight.obj'), "Handle")
        if handle_type == "ROUND":
            # handle_front = import_obj(directory+"/assets/handle_round.obj", "Handle")
            handle_back = import_obj(os.path.join(directory, 'assets', 'handle_round.obj'), "Handle")
        xyz = local_xyz(window_face)
        window_width,_ = calc_face_dimensions(window_face)
        if hinge == "LEFT":
            if flip:
                # handle_origin_front = - xyz[0] * (window_width-0.06) + xyz[1] * 0.5 + xyz[2] * window_thickness
                handle_origin_back = - xyz[0] * (window_width-0.06) + xyz[1] * 0.5
            else:
                # handle_origin_front = xyz[0] * (window_width-0.06) + xyz[1] * 0.5 + xyz[2] * window_thickness
                handle_origin_back = xyz[0] * (window_width-0.06) + xyz[1] * 0.5
        elif hinge == "RIGHT":
            if flip:
                # handle_origin_front = xyz[0] * (window_width-0.06) + xyz[1] * 0.5 + xyz[2] * window_thickness
                handle_origin_back = xyz[0] * (window_width-0.06) + xyz[1] * 0.5
            else:
                # handle_origin_front = - xyz[0] * (window_width-0.06) + xyz[1] * 0.5 + xyz[2] * window_thickness
                handle_origin_back = - xyz[0] * (window_width-0.06) + xyz[1] * 0.5
        if flip:
            if hinge == "LEFT":
                # handle_front_scale = (1,-1,-1)
                handle_back_scale = (1,-1,1)
            else:
                # handle_front_scale = (1,1,-1)
                handle_back_scale = (1,1,1)
        else:
            if hinge == "LEFT":
                # handle_front_scale = (1,-1,1)
                handle_back_scale = (1,-1,-1)
            else:
                # handle_front_scale = (1,1,1)
                handle_back_scale = (1,1,-1)
        # handles.append([handle_front])
        # handle_origins.append([handle_origin_front])
        # handle_scales.append([handle_front_scale])
        handles.append([handle_back])
        handle_origins.append([handle_origin_back])
        handle_scales.append([handle_back_scale])
    return handles, handle_origins, handle_scales


def validate_fill_props(prop):
    if prop.window.fill.fill_type == "BAR":
        # XXX keep bar depth smaller than window depth
        fill = prop.window.fill.bar_fill
        fill.bar_depth = min(fill.bar_depth, prop.window.depth)
    elif prop.window.fill.fill_type == "LOUVER":
        # XXX keep louver depth less than window depth
        fill = prop.window.fill.louver_fill
        depth = getattr(prop, "door_depth", getattr(prop, "dw_depth", 1e10))
        fill.louver_depth = min(fill.louver_depth, depth)