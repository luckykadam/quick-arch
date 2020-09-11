import bpy
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty, PointerProperty


def get_density(self):
    return self.get("density", self.get("initial_density", 5.0))


def set_density(self, value):
    self["density"] = value


class PostFillProperty(bpy.types.PropertyGroup):
    size: FloatProperty(
        name="Size",
        min=0.01,
        max=100.0,
        default=0.04,
        unit="LENGTH",
        description="Size of each post",
    )

    density: FloatProperty(
        name="Density",
        min=0.0,
        max=100.0,
        get=get_density,
        set=set_density,
        description="Number of posts along each edge per unit",
    )

    segments: IntProperty(
        name="Segments",
        min=3,
        max=64,
        default=4,
        description="Number of segments in each post",
    )

    def init(self, initial_density):
        self["initial_density"] = initial_density

    def draw(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "density")
        row.prop(self, "size")
        row = layout.row(align=True)
        row.prop(self, "segments")


class RailFillProperty(bpy.types.PropertyGroup):
    size: FloatProperty(
        name="Rail Size",
        min=0.01,
        max=100.0,
        default=0.025,
        unit="LENGTH",
        description="Size of each rail",
    )

    density: FloatProperty(
        name="Rail Density",
        min=0.0,
        max=100.0,
        default=5.0,
        description="Number of rails over each edge per unit",
    )

    segments: IntProperty(
        name="Segments",
        min=3,
        max=64,
        default=4,
        description="Number of segments in each rail",
    )

    def draw(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "density")
        row.prop(self, "size")
        row = layout.row(align=True)
        row.prop(self, "segments")


class WallFillProperty(bpy.types.PropertyGroup):
    width: FloatProperty(
        name="Wall Width",
        min=0.0,
        max=100.0,
        default=0.075,
        unit="LENGTH",
        description="Width of each wall",
    )

    def draw(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "width")


class RailProperty(bpy.types.PropertyGroup):

    fill_types = [
        ("POSTS", "Posts", "", 0),
        ("RAILS", "Rails", "", 1),
        ("WALL", "Wall", "", 2),
    ]

    fill: EnumProperty(
        name="Fill Type",
        items=fill_types,
        default="POSTS",
        description="Type of railing",
    )

    corner_post_width: FloatProperty(
        name="Width",
        min=0.01,
        max=100.0,
        default=0.06,
        unit="LENGTH",
        description="Width of each corner post",
    )

    corner_post_height: FloatProperty(
        name="Height",
        min=0.01,
        max=100.0,
        default=0.7,
        unit="LENGTH",
        description="Height of each corner post",
    )

    has_corner_post: BoolProperty(
        name="Corner Posts",
        default=True,
        description="Whether the railing has corner posts",
    )

    offset: FloatProperty(
        name="Offset",
        default=0.05,
        unit="LENGTH",
        description="Railings offset",
    )

    post_fill: PointerProperty(type=PostFillProperty)
    rail_fill: PointerProperty(type=RailFillProperty)
    wall_fill: PointerProperty(type=WallFillProperty)

    def init(self, stair_step_width=None, step_count=None):
        if stair_step_width and self.fill == "POSTS":
            if step_count > 1:
                initial_density = (step_count-1) / (stair_step_width * step_count)
            else:
                initial_density = (1 - 0.001) / (2 * stair_step_width)  # just enough to have 0 post on stairs
            self.post_fill.init(initial_density=initial_density)

    def draw(self, context, layout):
        
        col = layout.column(align=True)
        col.prop(self, "offset", text="Railing Offset")
        col.prop_menu_enum(self, "fill", text=self.fill.title())

        {
            "POSTS" : self.post_fill,
            "RAILS" : self.rail_fill,
            "WALL"  : self.wall_fill
        }.get(self.fill).draw(context, col)

        col.label(text="Corner Posts")
        row = col.row(align=True)
        row.prop(self, "corner_post_width")
        row.prop(self, "corner_post_height")
