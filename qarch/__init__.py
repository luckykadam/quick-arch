import bpy
from .core import register_core, unregister_core

bl_info = {
    "name": "Quick Arch",
    "author": "Lucky Kadam (luckykadam94@gmail.com)",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Toolshelf > Quick Arch",
    "description": "Architectural Tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh",
}


class QARCH_PT_mesh_tools(bpy.types.Panel):

    bl_label = "Mesh Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick Arch"

    def draw(self, context):
        layout = self.layout

        # Draw Operators
        # ``````````````
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("qarch.add_floorplan")
        row = col.row(align=True)
        row.operator("qarch.add_floors")
        row.operator("qarch.add_roof")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("qarch.add_window")
        row.operator("qarch.add_door")
        col.operator("qarch.add_multigroup")

        col = layout.column(align=True)
        col.operator("qarch.add_balcony")
        col.operator("qarch.add_stairs")

        col = layout.column(align=True)
        col.operator("qarch.add_asset", icon="ADD")


class QARCH_PT_material_tools(bpy.types.Panel):

    bl_label = "Material Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Quick Arch"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type == "MESH"

    def draw(self, context):
        layout = self.layout

        ob = context.object
        facemap = ob.face_maps.active

        rows = 2
        if facemap:
            rows = 4

        if not len(ob.face_maps):
            return

        layout.label(text="Face Maps")

        row = layout.row()
        args = ob, "face_maps", ob.face_maps, "active_index"
        row.template_list("QARCH_UL_fmaps", "", *args, rows=rows)

        col = row.column(align=True)
        col.operator("object.face_map_add", icon="ADD", text="")
        col.operator("object.face_map_remove", icon="REMOVE", text="")
        # col.separator()
        # col.operator("qarch.face_map_clear", icon="TRASH", text="")

        if ob.face_maps and (ob.mode == "EDIT" and ob.type == "MESH"):
            row = layout.row()

            sub = row.row(align=True)
            sub.operator("object.face_map_assign", text="Assign")
            sub.operator("object.face_map_remove_from", text="Remove")

            sub = row.row(align=True)
            sub.operator("object.face_map_select", text="Select")
            sub.operator("object.face_map_deselect", text="Deselect")

        if ob.face_maps:
            face_map_index = ob.face_maps.active_index
            face_map_material = ob.facemap_materials[face_map_index]

            # layout.label(text="UV Mapping")

            # col = layout.column()
            # row = col.row(align=True)
            # row.alignment = "LEFT"
            # row.prop(face_map_material, "auto_map", text="Auto")
            # row.prop(face_map_material, "uv_mapping_method", text="")

            # layout.label(text="Material")
            # layout.operator("qarch.create_facemap_material")
            # layout.template_ID_preview(face_map_material, "material", hide_buttons=True)


class QARCH_PT_preferences(bpy.types.Panel):
    bl_label = "Preferences"
    bl_parent_id = "QARCH_PT_mesh_tools"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.use_property_split = True
        col.use_property_decorate = False
        col.prop(context.scene.qarch_prefs, "libpath")


classes = (QARCH_PT_mesh_tools, QARCH_PT_material_tools, QARCH_PT_preferences)


def register():
    register_core()
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    unregister_core()
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    import os

    os.system("clear")

    # -- custom unregister for script watcher
    for tp in dir(bpy.types):
        if "QARCH_" in tp:
            bpy.utils.unregister_class(getattr(bpy.types, tp))

    register()
