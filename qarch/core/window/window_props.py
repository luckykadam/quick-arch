import bpy
from bpy.props import IntProperty, EnumProperty, FloatProperty, PointerProperty, BoolProperty

from ..fill import FillProperty, FillBars

class WindowProperty(bpy.types.PropertyGroup):

    # win_types = [
    #     ("CIRCULAR", "Circular", "", 0),
    #     ("RECTANGULAR", "Rectangular", "", 1),
    # ]

    # type: EnumProperty(
    #     name="Window Type",
    #     items=win_types,
    #     default="RECTANGULAR",
    #     description="Type of window",
    # )

    thickness: FloatProperty(
        name="Thickness",
        min=0.0,
        max=1.0,
        default=0.03,
        unit="LENGTH",
        description="Thickness of window",
    )

    # resolution: IntProperty(
    #     name="Resolution",
    #     min=3,
    #     max=128,
    #     default=20,
    #     description="Number of segements for the circle",
    # )

    hinge: EnumProperty(
        name="Hinge", items=[("LEFT", "Hinge Left", "", 0), ("RIGHT", "Hinge Right", "", 1)], default="LEFT", description="Hinge"
    )

    handle: EnumProperty(
        name="Handle", items=[("ROUND", "Round Handle", "", 0), ("STRAIGHT", "Straight Handle", "", 1)], default="ROUND", description="Handle Type"
    )

    add_bars: BoolProperty(name="Add Bars", default=False, description="Bars")
    flip_direction: BoolProperty(name="Flip Direction", default=False, description="Flip door/window directions")

    fill: PointerProperty(type=FillProperty)
    bars: PointerProperty(type=FillBars)

    def draw(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "flip_direction", toggle=True)

        row = col.row(align=True)
        row.prop(self, "thickness")

        row = col.row(align=True)
        row.prop(self, "hinge", expand=True)

        self.fill.draw(context, col)

        col.prop(self, "add_bars")
        if self.add_bars:
            self.bars.draw(col)

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "handle")
