import bpy
from .roof_types import build_roof
from .roof_props import RoofProperty


class QARCH_OT_add_roof(bpy.types.Operator):
    """Create roof from selected upward facing faces"""

    bl_idname = "qarch.add_roof"
    bl_label = "Add Roof"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=RoofProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        return build_roof(context, self.props)

    def draw(self, context):
        self.props.draw(context, self.layout)
