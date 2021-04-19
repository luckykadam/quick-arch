import bpy
from .terrace_types import build_terrace
from .terrace_props import TerraceProperty


class QARCH_OT_add_terrace(bpy.types.Operator):
    """Create terrace from the current edit mesh"""

    bl_idname = "qarch.add_terrace"
    bl_label = "Add Terrace"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=TerraceProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        return build_terrace(context, self.props)

    def draw(self, context):
        self.props.draw(context, self.layout)
