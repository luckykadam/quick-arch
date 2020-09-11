import bpy
from .balcony_types import build_balcony
from .balcony_props import BalconyProperty


class QARCH_OT_add_balcony(bpy.types.Operator):
    """Create a balcony from selected faces"""

    bl_idname = "qarch.add_balcony"
    bl_label = "Add Balcony"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=BalconyProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        return build_balcony(context, self.props)

    def draw(self, context):
        self.props.draw(context, self.layout)
