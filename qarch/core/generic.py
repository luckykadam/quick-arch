import bpy
from bpy.props import (
    IntProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
)

from ..utils import (
    clamp,
    restricted_size,
    restricted_offset,
)


def get_count(self):
    """ Return count value with a default of 1
    """
    return self.get("count", 1)


def set_count(self, value):
    """ Set count value ensuring that element fit nicely in parent
    """
    # -- Make each element in array fit into the parent
    # parent_width = self["limits"][1] - self["limits"][0]
    # if self.size_offset.size.x > parent_width / value:
    #     self.size_offset.size.x = parent_width / value

    # # -- keep horizontal offset within bounds of parent face
    # element_width = parent_width / value
    # item_width = self.size_offset.size.x
    # max_offset = (element_width / 2) - (item_width / 2)
    # self.size_offset.offset.x = clamp(
    #     self.size_offset.offset.x, -max_offset, max_offset
    # )

    # -- set count
    self["count"] = value


def clamp_count(face_width, frame_width, prop):
    prop.count = clamp(prop.count, 1, int(face_width / frame_width) - 1)


CountProperty = IntProperty(
    name="Count",
    min=1,
    max=100,
    set=set_count,
    get=get_count,
    description="Number of elements",
)


class SizeOffsetProperty(bpy.types.PropertyGroup):
    """ Convinience PropertyGroup used for regular Quad Inset (see window and door)"""

    def get_size(self):
        # if self["restricted"]:
        #     return self["default_size"]
        #     # return self.get("size", restricted_size(
        #     #     self["limits"], self.offset, (0.1, 0.1), self["default_size"]
        #     # ))
        # else:
            # return self.get("size", self["default_size"])
        return self.get("size", self["default_size"])

    def set_size(self, value):
        self["size"] = restricted_size(self["limits"], self.offset, (0.1, 0.1), value) if self["restricted"] else value
        # if self["restricted"]:
        #     # value = (clamp(value[0], 0.1, self["limits"][1] - self["limits"][0] - 0.0001), value[1])
        #     self["size"] = restricted_size(
        #         self["limits"], self.offset, (0.1, 0.1), value
        #     )
        # else:
        #     self["size"] = value

    size: FloatVectorProperty(
        name="Size",
        get=get_size,
        set=set_size,
        subtype="XYZ",
        size=2,
        unit="LENGTH",
        description="Size of geometry",
    )

    def get_offset(self):
        return self.get("offset", self["default_offset"])

    def set_offset(self, value):
        self["offset"] = restricted_offset(self["limits"], self.size, value) if self["restricted"] else value

    offset: FloatVectorProperty(
        name="Offset",
        get=get_offset,
        set=set_offset,
        subtype="TRANSLATION",
        size=2,
        unit="LENGTH",
        description="Offset in face's space",
    )

    show_props: BoolProperty(default=False)

    def init(self, limits, default_size=(1.0, 1.0), default_offset=(0.0, 0.0), restricted=True):
        self["limits"] = limits
        self["default_size"] = default_size
        self["default_offset"] = default_offset
        self["restricted"] = restricted

    def draw(self, context, box):

        row = box.row(align=False)
        col = row.column(align=True)
        col.prop(self, "size")

        col = row.column(align=True)
        col.prop(self, "offset")


class FrameProperty(bpy.types.PropertyGroup):

    thickness: FloatProperty(
        name="Thickness",
        min=0.01,
        max=1.0,
        default=0.08,
        unit="LENGTH",
        description="Thickness of Frame",
    )

    depth: FloatProperty(
        name="Depth",
        step=1,
        min=-1.0,
        max=1.0,
        default=0.04,
        unit="LENGTH",
        description="Depth of Frame",
    )

    margin: FloatProperty(
        name="Margin",
        min=0.01,
        max=1.0,
        step=1,
        default=0.05,
        unit="LENGTH",
        description="Margin of Frame",
    )

    border_thickness: FloatProperty(
        name="Border Thickness",
        min=0.0,
        max=1.0,
        default=0.01,
        unit="LENGTH",
        description="Thickness of Frame Border",
    )

    def draw(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "depth")
        row.prop(self, "thickness")
        row = col.row(align=True)
        row.prop(self, "margin")
        row.prop(self, "border_thickness")



classes = (
    SizeOffsetProperty,
    FrameProperty,
)


def register_generic():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_generic():
    for cls in classes:
        bpy.utils.unregister_class(cls)
