import bpy
from bpy.props import FloatProperty, EnumProperty, PointerProperty, BoolProperty

from ..fill import FillProperty


class DoorProperty(bpy.types.PropertyGroup):

    thickness: FloatProperty(
        name="Thickness",
        min=0.0,
        max=1.0,
        default=0.03,
        unit="LENGTH",
        description="Thickness of door",
    )

    # double_door: BoolProperty(
    #     name="Double Door", default=False, description="Double door"
    # )

    hinge: EnumProperty(
        name="Hinge", items=[("LEFT", "Hinge Left", "", 0), ("RIGHT", "Hinge Right", "", 1)], default="LEFT", description="Hinge"
    )

    knob: EnumProperty(
        name="Knob", items=[("ROUND", "Round Knob", "", 0), ("STRAIGHT", "Straight Knob", "", 1)], default="ROUND", description="Knob Type"
    )

    bottom_panel: BoolProperty(
        name="Bottom Panel", default=False, description="Bottom panel"
    )

    bottom_panel_height: FloatProperty(
        name="Bottom Panel Height",
        min=0.2,
        max=2.0,
        default=1.0,
        unit="LENGTH",
        description="Height of bottom panel",
    )

    fill: PointerProperty(type=FillProperty)
    flip_direction: BoolProperty(name="Flip Direction", default=False, description="Flip door/window directions")

    bottom_fill: PointerProperty(type=FillProperty)

    def draw(self, context, layout):

        col = layout.column(align=True)
        col.prop(self, "flip_direction", toggle=True)

        row = col.row(align=True)
        row.prop(self, "thickness")

        row = col.row(align=True)
        row.prop(self, "hinge", expand=True)

        self.fill.draw(context, col)

        row = col.row(align=True)
        row.prop(self, "bottom_panel")

        if self.bottom_panel:
            col = layout.column(align=True)
            col.prop(self, "bottom_panel_height")
            self.bottom_fill.draw(context, col)

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "knob")

        # row = col.row(align=True)
        # row.prop(self, "double_door")
