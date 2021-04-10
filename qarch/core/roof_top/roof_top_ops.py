import bpy
from .roof_top_types import build_roof_top
from .roof_top_props import RoofTopProperty


class QARCH_OT_add_roof_top(bpy.types.Operator):
    """Create roof top from selected roof faces"""

    bl_idname = "qarch.add_roof_top"
    bl_label = "Add Roof Top"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=RoofTopProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        return build_roof_top(context, self.props)

    def draw(self, context):
        self.props.draw(context, self.layout)
