import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty


class RoofTopProperty(bpy.types.PropertyGroup):

    thickness: FloatProperty(
        name="Thickness",
        min=0.01,
        max=1.0,
        default=0.1,
        unit="LENGTH",
        description="Thickness of roof hangs",
    )

    outset: FloatProperty(
        name="Outset",
        min=0.01,
        max=1.0,
        default=0.1,
        unit="LENGTH",
        description="Outset of roof hangs",
    )

    def draw(self, context, layout):

        layout.separator()
        col = layout.column(align=True)
        col.prop(self, "thickness")
        col.prop(self, "outset")
