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
        qarch_asset_prop = context.scene.qarch_asset_prop
        for f in faces:
            if qarch_asset_prop.asset_type and qarch_asset_prop.category and qarch_asset_prop.asset:
                add_object(f, props.offset, qarch_asset_prop.libpath, qarch_asset_prop.asset_type, qarch_asset_prop.category, qarch_asset_prop.asset, props.track, props.up)
    return {"FINISHED"}

def add_object(face, offset, libpath, asset_type, category, asset, track, up):
    filepath = (os.path.join(libpath, asset_type, category, asset + ".blend"))

    objects = import_blend(filepath)

    if vec_equal(face.normal, Vector((0,0,1))):
        xyz = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]
    elif vec_equal(face.normal, Vector((0,0,-1))):
        xyz = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,-1))]
    else:
        xyz = local_xyz(face) 
    local_offset = xyz[0]*offset.x + xyz[1]*offset.y + xyz[2]*offset.z
    
    for obj in objects:
        obj.matrix_local.translation = face.calc_center_bounds() + local_offset
        align_obj(obj, face.normal, track=track, up=up)