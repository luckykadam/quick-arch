import bpy
import bmesh

from .custom_object_types import add_custom_object
from .custom_object_props import CustomObjectProperty

class QARCH_OT_add_custom_object(bpy.types.Operator):
    """Add a custom object to selected faces"""

    bl_idname = "qarch.add_custom_object"
    bl_label = "Add Custom Object"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=CustomObjectProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        return add_custom_object(context, self.props)

    def invoke(self, context, event):
        self.props.init()
        return self.execute(context)

    def draw(self, context):
        self.props.draw(context, self.layout)
