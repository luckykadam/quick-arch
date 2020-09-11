import bpy
from bpy.props import BoolProperty, FloatProperty, PointerProperty, FloatVectorProperty

from ..railing.railing_props import RailProperty


class BalconyProperty(bpy.types.PropertyGroup):

    offset: FloatVectorProperty(
        name="Offset",
        subtype="TRANSLATION",
        size=3,
        unit="LENGTH",
        description="Offset in face's space",
    )

    slab_height: FloatProperty(
        name="Slab Height",
        min=0.01,
        max=100.0,
        default=0.2,
        unit="LENGTH",
        description="Height of balcony slab",
    )

    length: FloatProperty(
        name="Length",
        min=0.01,
        max=100.0,
        default=2.0,
        unit="LENGTH",
        description="Length of balcony",
    )

    width: FloatProperty(
        name="Width",
        min=0.01,
        max=100.0,
        default=1.0,
        unit="LENGTH",
        description="Width of balcony",
    )

    has_railing: BoolProperty(
        name="Add Railing", default=True, description="Whether the balcony has railing"
    )

    rail: PointerProperty(type=RailProperty)

    def init(self, wall_dimensions):
        if not self.get("initial_offset"):
            self.offset = (((wall_dimensions[0]-self.length)/2, 0, 0))
            self["initial_offset"] = self.offset
        

    def draw(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text="Offset: ")
        row.column().prop(self, "offset", text="")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Balcony")
        row = col.row(align=True)
        row.prop(self, "slab_height")
        row = col.row(align=True)
        row.prop(self, "width")
        row.prop(self, "length")

        layout.separator()
        col = layout.column(align=True)
        col.prop(self, "has_railing")
        if self.has_railing:
            self.rail.draw(context, col)
