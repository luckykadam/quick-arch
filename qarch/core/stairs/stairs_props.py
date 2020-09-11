import bpy
from bpy.props import (
    IntProperty,
    BoolProperty,
    FloatProperty,
    PointerProperty,
    EnumProperty,
    FloatVectorProperty,
)

from ..railing.railing_props import RailProperty


class StairsProperty(bpy.types.PropertyGroup):

    offset: FloatVectorProperty(
        name="Offset",
        subtype="TRANSLATION",
        size=3,
        unit="LENGTH",
        description="Offset in face's space",
    )

    width: FloatProperty(
        name="Stairs Width",
        min=0.01,
        max=100.0,
        default=1.0,
        unit="LENGTH",
        description="Width of stairs",
    )

    step_count: IntProperty(
        name="Step Count", min=1, max=100, default=3, description="Number of steps"
    )

    step_width: FloatProperty(
        name="Step Width",
        min=0.01,
        max=100.0,
        default=0.2,
        unit="LENGTH",
        description="Width of each step",
    )

    step_height: FloatProperty(
        name="Step Height",
        min=0.01,
        max=100.0,
        default=0.12,
        unit="LENGTH",
        description="Height of each step",
    )

    landing_width: FloatProperty(
        name="Landing Width",
        min=0.01,
        max=100.0,
        default=1.0,
        unit="LENGTH",
        description="Width of each stairs landing",
    )

    landing: BoolProperty(
        name="Has Landing", default=True, description="Whether the stairs have a landing"
    )

    bottom_types = [
        ("FILLED", "Filled", "", 0),
        ("SLOPE", "Slope", "", 2),
        ("BLOCKED", "Blocked", "", 1),
    ]

    bottom: EnumProperty(
        name="Bottom Type",
        items=bottom_types,
        default="FILLED",
        description="Bottom type of stairs",
    )

    railing_left: BoolProperty(
        name="Left", default=True, description="Whether the stairs have railing on left"
    )

    railing_right: BoolProperty(
        name="Right", default=True, description="Whether the stairs have railing on right"
    )

    rail: PointerProperty(type=RailProperty)

    def init(self, wall_dimensions):
        if not self.get("initial_offset"):
            self.offset = (((wall_dimensions[0]-self.width)/2, 0, 0))
            self["initial_offset"] = self.offset
        self.rail.init(self.step_width, self.step_count)

    def draw(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text="Offset: ")
        row.column().prop(self, "offset", text="")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Stairs")
        row = col.row(align=True)
        row.prop(self, "width")
        row.prop(self, "step_count")
        row = col.row(align=True)
        row.prop(self, "step_height")
        row.prop(self, "step_width")

        col = layout.column()
        col.prop(self, "landing")
        if self.landing:
            col.prop(self, "landing_width")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Bottom")
        row = col.row(align=True)
        row.prop(self, "bottom", expand=True)

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Railings")
        row = col.row(align=True)
        row.prop(self, "railing_left")
        row.prop(self, "railing_right")
        col = layout.column(align=True)
        if self.railing_left or self.railing_right:
            self.rail.draw(context, col)
