import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty


class FloorProperty(bpy.types.PropertyGroup):
    floor_count: IntProperty(
        name="Floor Count", min=1, max=1000, default=1, description="Number of floors"
    )

    floor_height: FloatProperty(
        name="Floor Height",
        min=0.01,
        max=1000.0,
        default=2.8,
        unit="LENGTH",
        description="Height of each floor",
    )

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

    # bounding_wall_thickness: FloatProperty(
    #     name="Bounding Wall Thickness",
    #     min=0.01,
    #     max=1000.0,
    #     default=0.2,
    #     unit="LENGTH",
    #     description="Thickness of bounding walls",
    # )

    # internal_wall_thickness: FloatProperty(
    #     name="Internal Wall Thickness",
    #     min=0.01,
    #     max=1000.0,
    #     default=0.12,
    #     unit="LENGTH",
    #     description="Thickness of internal walls",
    # )

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
        col.label(text="Floors")
        row = col.row(align=True)
        row.prop(self, "floor_count")
        row.prop(self, "floor_height")

        col.label(text="Walls")
        row = col.row(align=True)
        # row.prop(self, "bounding_wall_thickness")
        # row.prop(self, "internal_wall_thickness")
        row.prop(self, "wall_thickness")

        col.label(text="Slabs")
        row = col.row(align=True)
        row.prop(self, "slab_height")
        row.prop(self, "slab_outset")
