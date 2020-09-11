import bpy
import bmesh

from .door_types import build_door
from .add_door_props import AddDoorProperty

class QARCH_OT_add_door(bpy.types.Operator):
    """Create a door from selected faces"""

    bl_idname = "qarch.add_door"
    bl_label = "Add Door"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=AddDoorProperty)

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.mode == "EDIT_MESH"

    def execute(self, context):
        return build_door(context, self.props)

    def draw(self, context):
        self.props.draw(context, self.layout)
