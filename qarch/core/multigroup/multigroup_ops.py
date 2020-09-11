import bpy
import bmesh

from .multigroup_types import build_multigroup
from .multigroup_props import MultigroupProperty


class QARCH_OT_add_multigroup(bpy.types.Operator):
    """Create multiple door/window group from selected faces"""

    bl_idname = "qarch.add_multigroup"
    bl_label = "Add Multigroup"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=MultigroupProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        return build_multigroup(context, self.props)

    def draw(self, context):
        self.props.draw(context, self.layout)
