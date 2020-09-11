import bpy, bmesh
from mathutils import Vector
from ...utils import (
    link_objects,
    set_origin,
    managed_bmesh_edit,
    crash_safe,
    deselect,
    local_xyz,
    align_obj,
    vec_equal,
)

from ..validations import validate, some_selection


@crash_safe
@validate([some_selection], ["No faces seleted"])
def add_custom_object(context, props):
    """ Add custom object as linked object.
    """
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        for f in faces:
            if props.obj:
                _add_custom_object(f, props.offset, props.obj, props.track, props.up)
    return {"FINISHED"}

def _add_custom_object(face, offset, obj_name, track, up):

    new_obj = bpy.data.objects.new(obj_name, bpy.data.objects[obj_name].data)
    link_objects([new_obj], bpy.context.object)
    if vec_equal(face.normal, Vector((0,0,1))):
        xyz = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]
    elif vec_equal(face.normal, Vector((0,0,-1))):
        xyz = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,-1))]
    else:
        xyz = local_xyz(face) 
    local_offset = xyz[0]*offset.x + xyz[1]*offset.y + xyz[2]*offset.z
    new_obj.matrix_local.translation = face.calc_center_median() + local_offset
    align_obj(new_obj, face.normal, track=track, up=up)