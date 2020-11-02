import os, bpy
import bmesh

from .asset_types import add_asset
from .asset_props import CustomObjectProperty

class QARCH_OT_add_asset(bpy.types.Operator):
    """Add an asset from Chocofur style library to selected faces. To enable - set Library Path in Quick Arch Settings"""

    bl_idname = "qarch.add_asset"
    bl_label = "Add Asset"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=CustomObjectProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH" and os.path.isdir(bpy.context.scene.qarch_settings.libpath)

    def execute(self, context):
        return add_asset(context, self.props)

    def invoke(self, context, event):
        self.props.init()
        return self.execute(context)

    def draw(self, context):
        self.props.draw(context, self.layout)
