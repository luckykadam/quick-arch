import bpy
import bmesh

from .add_window_props import AddWindowProperty
from .window_types import build_window

class QARCH_OT_add_window(bpy.types.Operator):
    """Create window from selected faces"""

    bl_idname = "qarch.add_window"
    bl_label = "Add Window"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=AddWindowProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        return build_window(context, self.props)


    def draw(self, context):
        self.props.draw(context, self.layout)
