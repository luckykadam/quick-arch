import bpy
from .floor_types import build_floors
from .floor_props import FloorProperty


class QARCH_OT_add_floors(bpy.types.Operator):
    """Create floors from the current edit mesh"""

    bl_idname = "qarch.add_floors"
    bl_label = "Add Floors"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=FloorProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        return build_floors(context, self.props)

    def draw(self, context):
        self.props.draw(context, self.layout)
