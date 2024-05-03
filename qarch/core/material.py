import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
)

from ..utils import (
    create_object_material,
    bmesh_from_active_object,
    set_material_for_active_facemap,
    set_facemap_for_selected,
    select_facemap,
    deselect_facemap,
    FaceMap
)


class QARCH_UL_fmaps(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, skip, _skip, _skip_):
        fmap = item
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.prop(fmap, "name", text="", emboss=False, icon="FACE_MAPS")
        elif self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)

if bpy.app.version < (4,0,0):
    def clear_empty_facemaps(context):
        """ Remove all facemaps that don't have any faces assigned
        """
        obj = context.object
        with bmesh_from_active_object(context) as bm:

            face_map = bm.faces.layers.face_map.active
            used_indices = {f[face_map] for f in bm.faces}
            all_indices = {f.index for f in obj.face_maps}
            tag_remove_indices = all_indices - used_indices

            # -- remove face maps
            tag_remove_maps = [obj.face_maps[idx] for idx in tag_remove_indices]
            for fmap in tag_remove_maps:
                obj.face_maps.remove(fmap)

            # -- remove facemap materials:
            for idx in reversed(list(tag_remove_indices)):
                obj.facemap_materials.remove(idx)


    class QARCH_OT_fmaps_clear(bpy.types.Operator):
        """Remove all empty face maps"""

        bl_idname = "qarch.face_map_clear"
        bl_label = "Clear empty face maps"
        bl_options = {"REGISTER", "UNDO"}

        @classmethod
        def poll(cls, context):
            obj = context.object
            return obj and obj.type == "MESH"

        def execute(self, context):
            clear_empty_facemaps(context)
            return {"FINISHED"}


    class QARCH_OT_create_facemap_material(bpy.types.Operator):
        """Create and assign a new material for the active facemap"""

        bl_idname = "qarch.create_facemap_material"
        bl_label = "Assign New Material"
        bl_options = {"REGISTER", "UNDO"}

        @classmethod
        def poll(cls, context):
            obj = context.object
            active_facemap = obj.face_maps[obj.face_maps.active_index]
            mat = obj.facemap_materials[active_facemap.index].material
            return obj and obj.type == "MESH" and not mat

        def execute(self, context):
            obj = context.object
            active_facemap = obj.face_maps[obj.face_maps.active_index]

            # -- create new material
            mat = create_object_material(obj, "mat_" + active_facemap.name)
            mat_id = [idx for idx, m in enumerate(obj.data.materials) if m == mat].pop()
            obj.active_material_index = mat_id # make the new material active

            # -- assign to active facemap
            set_material_for_active_facemap(mat, context)
            obj.facemap_materials[active_facemap.index].material = mat
            return {"FINISHED"}
else:  # version 4.0 layers
    def clear_empty_facemaps(context):
        """ Remove all facemaps that don't have any faces assigned
        """
        pass  # nothing to do here


    class QARCH_OT_fmaps_clear(bpy.types.Operator):
        """Remove all empty face maps"""

        bl_idname = "qarch.face_map_clear"
        bl_label = "Clear empty face maps"
        bl_options = {"REGISTER", "UNDO"}

        @classmethod
        def poll(cls, context):
            obj = context.object
            return obj and obj.type == "MESH"

        def execute(self, context):
            clear_empty_facemaps(context)
            return {"FINISHED"}


    class QARCH_OT_create_facemap_material(bpy.types.Operator):
        """Create and assign a new material for the active facemap"""

        bl_idname = "qarch.create_facemap_material"
        bl_label = "Assign New Material"
        bl_options = {"REGISTER", "UNDO"}

        var_face_map: bpy.props.IntProperty(default=0)

        @classmethod
        def poll(cls, context):
            obj = context.object
            if not obj or (obj.type != "MESH"):
                return False
            active_poly_index = obj.data.polygons.active or 0
            mat = obj.data.polygons[active_poly_index].material_index
            # this is not the same behavior as before, default material slot is 0
            # we could create a default white in slot 0 so all user materials are "created"
            return mat==0

        def execute(self, context):
            obj = context.object
            active_facemap = self.var_face_map

            # -- create new material
            mat = create_object_material(obj, "mat_" + FaceMap(active_facemap).name)

            # -- assign to active facemap
            set_material_for_active_facemap(mat, context, active_facemap)
            return {"FINISHED"}

    class QARCH_OT_face_map_assign(bpy.types.Operator):
        """Assign a facemap for the selected faces"""

        bl_idname = "qarch.face_map_assign"
        bl_label = "Assign faces to map"
        bl_options = {"REGISTER", "UNDO"}

        var_face_map: bpy.props.IntProperty(default=0)

        @classmethod
        def poll(cls, context):
            obj = context.object
            if not obj or (obj.type != "MESH") or (obj.data.polygons.active is None):
                return False
            return True

        def execute(self, context):
            set_facemap_for_selected(self.var_face_map, context)

            return {"FINISHED"}


    class QARCH_OT_face_map_select(bpy.types.Operator):
        """Create and assign a new material for the active facemap"""

        bl_idname = "qarch.face_map_select"
        bl_label = "Select faces in map"
        bl_options = {"REGISTER", "UNDO"}

        var_face_map: bpy.props.IntProperty(default=0)

        @classmethod
        def poll(cls, context):
            obj = context.object
            if not obj or (obj.type != "MESH"):
                return False
            return True

        def execute(self, context):
            select_facemap(self.var_face_map, context)

            return {"FINISHED"}

    class QARCH_OT_face_map_deselect(bpy.types.Operator):
        """Create and assign a new material for the active facemap"""

        bl_idname = "qarch.face_map_deselect"
        bl_label = "Deselect faces in map"
        bl_options = {"REGISTER", "UNDO"}

        var_face_map: bpy.props.IntProperty(default=0)

        @classmethod
        def poll(cls, context):
            obj = context.object
            if not obj or (obj.type != "MESH"):
                return False
            return True

        def execute(self, context):
            deselect_facemap(self.var_face_map, context)

            return {"FINISHED"}

def update_facemap_material(self, context):
    """ Assign the updated material to all faces belonging to active facemap
    """
    set_material_for_active_facemap(self.material, context)
    return None


class FaceMapMaterial(bpy.types.PropertyGroup):
    """ Tracks materials for each facemap created for an object
    """

    material: PointerProperty(type=bpy.types.Material, update=update_facemap_material)

    auto_map: BoolProperty(
        name="Auto UV Mapping",
        default=True,
        description="Automatically UV Map faces belonging to active facemap.")

    mapping_methods = [
        ("UNWRAP", "Unwrap", "", 0),
        ("CUBE_PROJECTION", "Cube_Projection", "", 1),
    ]

    uv_mapping_method: EnumProperty(
        name="UV Mapping Method",
        items=mapping_methods,
        default="CUBE_PROJECTION",
        description="How to perform UV Mapping"
    )


if bpy.app.version < (4,0,0):
    classes = (
        FaceMapMaterial,
        QARCH_UL_fmaps,
        QARCH_OT_fmaps_clear,
        QARCH_OT_create_facemap_material,
    )
else:
    classes = (
        FaceMapMaterial,
        QARCH_UL_fmaps,
        QARCH_OT_fmaps_clear,
        QARCH_OT_create_facemap_material,
        QARCH_OT_face_map_assign,
        QARCH_OT_face_map_select,
        QARCH_OT_face_map_deselect,
    )


def register_material():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.facemap_materials = CollectionProperty(type=FaceMapMaterial)


def unregister_material():
    for cls in classes:
        bpy.utils.unregister_class(cls)
