import bpy

from .floorplan_types import create_floorplan
from .floorplan_props import FloorplanProperty


class QARCH_OT_add_floorplan(bpy.types.Operator):
    """Create a starting building floorplan"""

    bl_idname = "qarch.add_floorplan"
    bl_label = "Create Floorplan"
    bl_options = {"REGISTER", "UNDO"}

    props: bpy.props.PointerProperty(type=FloorplanProperty)

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        return create_floorplan(context, self.props)

    def draw(self, context):
        self.props.draw(context, self.layout)
