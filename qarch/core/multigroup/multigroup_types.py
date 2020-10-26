import bpy, bmesh

import re
from ..frame import create_multigroup_frame_and_dw, create_multigroup_hole
from ..window.window_types import fill_window, add_handles
from ..door.door_types import fill_door, add_knobs
from ..fill.fill_types import fill_bars
from ...utils import (
    valid_ngon,
    popup_message,
    subdivide_face_horizontally,
    split_faces,
    link_objects,
    set_origin,
    calc_face_dimensions,
    managed_bmesh_edit,
    get_opposite_face,
    get_relative_offset,
    crash_safe,
    deselect,
    align_obj,
    managed_bmesh,
)
from ..validations import validate, some_selection, ngon_validation, same_dimensions


@crash_safe
@validate([some_selection, ngon_validation, same_dimensions], ["No faces seleted", "Multigroup creation not supported on non-rectangular n-gon!", "All selected faces need to be of same dimensions"])
def build_multigroup(context, props):
    """ Create multigroup from context and prop, with validations. Intented to be called directly from operator.
    """
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        props.init(
            calc_face_dimensions(faces[0]),
            calc_face_dimensions(get_opposite_face(faces[0], bm.faces)),
            get_relative_offset(faces[0], get_opposite_face(faces[0], bm.faces)),
            )
        create_multigroup(bm, faces, props)
    return {"FINISHED"}


def create_multigroup(bm, faces, prop):
    """ Create multigroup from face selection
    """

    # Prevent error when there are no components
    if len(prop.components) == 0:
        popup_message("No components are chosen", "No Components Error")
        return False

    # Prevent error when there are invalid chars
    if not re.match("^[dw]*$", prop.components):
        prop.components = re.sub("[^d|w|]", "", prop.components)

    for face in faces:
        array_faces = subdivide_face_horizontally(bm, face, widths=[prop.size_offset.size.x]*prop.count)
        for aface in array_faces:
            normal = aface.normal.copy()
            faces = create_multigroup_hole(bm, aface, prop.size_offset.size,  prop.size_offset.offset, prop.components, prop.width_ratio if prop.different_widths else 1, prop.frame.margin, prop.frame.depth)
            if prop.only_hole:
                bmesh.ops.delete(bm, geom=faces, context="FACES")
            else:
                (door_faces,door_origins), (window_faces,bar_faces,window_origins), (frame_faces,frame_origin) = create_multigroup_frame_and_dw(bm, faces, prop.frame, prop.components, prop.door, prop.window)
                knobs,knob_origins,knob_scales = add_knobs(door_faces, prop.door.thickness, prop.door.knob, prop.door.hinge, prop.door.flip_direction)
                handles,handle_origins,handle_scales = add_handles(window_faces, prop.window.thickness, prop.window.handle, prop.window.hinge, prop.window.flip_direction)
                doors = split_faces(bm, [[f] for f in door_faces], ["Door" for f in door_faces])
                windows = split_faces(bm, [[f] for f in window_faces], ["Window" for f in window_faces])
                frame = split_faces(bm, [frame_faces], ["Frame"])[0]

                # link objects and set origins
                link_objects([frame], bpy.context.object)
                link_objects(doors+windows, frame)
                set_origin(frame, frame_origin)
                for door,origin in zip(doors,door_origins):
                    set_origin(door, origin, frame_origin)
                for window,origin in zip(windows,window_origins):
                    set_origin(window, origin, frame_origin)

                # create bars
                if prop.window.add_bars:
                    for face,origin in zip(bar_faces,window_origins):
                        bars = split_faces(bm, [[face]], ["Bars"])[0]
                        link_objects([bars], frame)
                        set_origin(bars, origin, frame_origin)
                        with managed_bmesh(bars) as bars_bm:
                            fill_bars(bars_bm, bars, bars_bm.faces[0], prop.window.bars)

                # set knob origin, rotations and scale
                for door,knobs,origins,scales in zip(doors,knobs,knob_origins,knob_scales):
                    for knob,origin,scale in zip(knobs,origins,scales):
                        link_objects([knob], door)
                        knob.matrix_local.translation = origin
                        align_obj(knob, normal)
                        knob.scale = scale

                # set handle origin, rotations and scale
                for window,handles,origins,scales in zip(windows,handles,handle_origins,handle_scales):
                    for handle,origin,scale in zip(handles, origins, scales):
                        link_objects([handle], window)
                        handle.matrix_local.translation = origin
                        align_obj(handle, normal)
                        handle.scale = scale

                for door in doors:
                    fill_door(door, prop)
                for window in windows:
                    fill_window(window, prop)
    return True

