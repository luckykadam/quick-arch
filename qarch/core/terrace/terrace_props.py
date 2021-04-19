import bpy
from bpy.props import FloatProperty

class TerraceProperty(bpy.types.PropertyGroup):
    slab_height: FloatProperty(
        name="Slab Height",
        min=0.01,
        max=1000.0,
        default=0.2,
        unit="LENGTH",
        description="Height of each slab",
    )

    slab_outset: FloatProperty(
        name="Slab Outset",
        min=0.0,
        max=10.0,
        default=0.1,
        unit="LENGTH",
        description="Outset of each slab",
    )

    wall_height: FloatProperty(
        name="Wall Height",
        min=0.01,
        max=10.0,
        default=1.0,
        unit="LENGTH",
        description="Height of walls",
    )

    wall_thickness: FloatProperty(
        name="Wall Thickness",
        min=0.01,
        max=1000.0,
        default=0.12,
        unit="LENGTH",
        description="Thickness of walls",
    )

    def draw(self, context, layout):

        layout.separator()
        col = layout.column(align=True)
        row = col.row(align=True)
        # row.prop(self, "bounding_wall_thickness")
        # row.prop(self, "internal_wall_thickness")
        row.prop(self, "wall_height")
        row.prop(self, "wall_thickness")

        col.label(text="Slabs")
        row = col.row(align=True)
        row.prop(self, "slab_height")
        row.prop(self, "slab_outset")
