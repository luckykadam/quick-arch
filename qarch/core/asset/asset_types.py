import os, bpy, bmesh
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
    import_blend,
)

from ..validations import validate, some_selection


@crash_safe
@validate([some_selection], ["No faces seleted"])
def add_asset(context, props):
    """ Add custom object as linked object.
    """
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        for f in faces:
            if props.asset_type and props.category and props.asset_name:
                add_object(f, props.offset, context.scene.qarch_prefs.libpath, props.asset_type, props.category, props.asset_name, props.track, props.up)
    return {"FINISHED"}

def add_object(face, offset, libpath, asset_type, category, asset_name, track, up):
    filepath = (os.path.join(libpath, asset_type, category, asset_name + ".blend"))

    objects = import_blend(filepath)

    parent_objs = [ob for ob in objects if not ob.parent]
    link_objects(parent_objs, bpy.context.object)
    if vec_equal(face.normal, Vector((0,0,1))):
        xyz = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]
    elif vec_equal(face.normal, Vector((0,0,-1))):
        xyz = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,-1))]
    else:
        xyz = local_xyz(face) 
    local_offset = xyz[0]*offset.x + xyz[1]*offset.y + xyz[2]*offset.z
    
    for obj in parent_objs:
        obj.matrix_local.translation = face.calc_center_median() + local_offset
        align_obj(obj, face.normal, track=track, up=up)