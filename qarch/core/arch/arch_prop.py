import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty, PointerProperty, BoolProperty

class FillGlassPanesArch(bpy.types.PropertyGroup):

    pane_border: FloatProperty(
        name="Pane Border",
        min=0.01,
        max=1.0,
        default=0.01,
        unit="LENGTH",
        description="Borders of each pane",
    )

    margin: FloatProperty(
        name="Margin",
        min=0.01,
        max=1.0,
        default=0.1,
        unit="LENGTH",
        description="Margin",
    )

    pane_gap: FloatProperty(
        name="Gap",
        step=1,
        min=0.01,
        max=1.0,
        default=0.01,
        unit="LENGTH",
        description="Gap between panes",
    )

    glass_thickness: FloatProperty(
        name="Glass Thickness",
        step=1,
        min=0.01,
        max=0.1,
        default=0.002,
        unit="LENGTH",
        description="Thickness of glass",
    )

    def draw(self, layout):

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "margin")
        row.prop(self, "pane_gap")
        row = col.row(align=True)
        row.prop(self, "pane_border")
        row.prop(self, "glass_thickness")


class ArchFillProperty(bpy.types.PropertyGroup):

    fill_types = [
        ("NONE", "None", "", 0),
        ("GLASS_PANES", "Glass Panes", "", 1),
    ]

    fill_type: EnumProperty(
        name="Fill Type",
        items=fill_types,
        default="NONE",
        description="Type of fill for arch",
    )

    glass_fill: PointerProperty(type=FillGlassPanesArch)

    def draw(self, context, layout):

        prop_name = (
            "Fill Type"
            if self.fill_type == "NONE"
            else self.fill_type.title().replace("_", " ")
        )
        # col = layout.column(align=True)
        layout.prop_menu_enum(self, "fill_type", text=prop_name)

        # -- draw fill types
        fill_map = {
            "GLASS_PANES": self.glass_fill,
        }
        fill = fill_map.get(self.fill_type)
        if fill:
            fill.draw(layout)


class ArchProperty(bpy.types.PropertyGroup):
    """ Convinience PropertyGroup to create arched features """

    # def get_height(self):
    #     return self.get("height", min(self["parent_height"], self["default_height"]))

    # def set_height(self, value):
    #     self["height"] = clamp(value, 0.1, self["parent_height"] - 0.0001)

    resolution: IntProperty(
        name="Arc Resolution",
        min=1,
        max=128,
        default=12,
        description="Number of segements for the arc",
    )

    straight_height: FloatProperty(
        name="Height",
        # get=get_height,
        # set=set_height,
        min=0.1,
        max=2.0,
        default=0.4,
        unit="LENGTH",
        description="Height of the straight part",
    )

    arc_height: FloatProperty(
        name="Arc Height",
        # get=get_height,
        # set=set_height,
        min=0.1,
        max=2.0,
        default=0.2,
        unit="LENGTH",
        description="Height of the arc",
    )

    arc_offset: FloatProperty(
        name="Arc Angle",
        # get=get_height,
        # set=set_height,
        min=0.0,
        max=4.0,
        default=0.4,
        unit="LENGTH",
        description="Offset of arc center",
    )

    thickness: FloatProperty(
        name="Thickness",
        min=0.0,
        max=1.0,
        default=0.03,
        unit="LENGTH",
        description="Thickness of arch",
    )

    func_items = [("SINE", "Sine", "", 0), ("SPHERE", "Sphere", "", 1)]
    function: EnumProperty(
        name="Offset Function",
        items=func_items,
        default="SPHERE",
        description="Type of offset for arch",
    )
    flip_direction: BoolProperty(name="Flip Direction", default=False, description="Flip arch directions")
    curved: BoolProperty(name="Curved Top", default=False, description="Curved Top")
    fill: PointerProperty(type=ArchFillProperty)

    def init(self, parent_height):
        self["parent_height"] = parent_height
        self["default_height"] = 0.4

    def draw(self, context, layout):

        col = layout.column()
        col = col.column(align=True)
        col.prop(self, "straight_height")
        row = col.row(align=True)
        row.prop(self, "flip_direction")
        row.prop(self, "curved")

        if self.curved:
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop(self, "function", expand=True)
            col.prop(self, "resolution")
            col.prop(self, "arc_height")
            col.prop(self, "arc_offset")
            col.prop(self, "thickness")

        self.fill.draw(context, col)
