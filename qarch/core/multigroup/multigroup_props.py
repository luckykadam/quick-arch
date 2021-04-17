import bpy
from bpy.props import StringProperty, PointerProperty, BoolProperty, FloatProperty

from ..generic import SizeOffsetProperty, CountProperty, FrameProperty
from ..arch import ArchProperty
from ..door.door_props import DoorProperty
from ..window.window_props import WindowProperty
from ...utils import get_limits, infer_values


class MultigroupProperty(bpy.types.PropertyGroup):

    components: StringProperty(
        name="Components",
        default="dw",
        description="Components (Door and Windows): example: 'wdw' for a door surrounded by windows",
    )

    count: CountProperty
    only_hole: BoolProperty(name="Only hole", default=False, description="Only hole. No door/window/frame")
    arch: PointerProperty(type=ArchProperty)
    size_offset: PointerProperty(type=SizeOffsetProperty)
    frame: PointerProperty(type=FrameProperty)
    door: PointerProperty(type=DoorProperty)
    window: PointerProperty(type=WindowProperty)
    add_arch: BoolProperty(name="Add Arch", default=False, description="Add arch over door/window")
    different_widths: BoolProperty(name="Different w/d Widths", default=False, description="Different window/door widths")
    width_ratio: FloatProperty(name="w/d Width ratio", default=1.2, min=0.1, max=10, description="Ration of Window to Door width")
    infer_values_switch: BoolProperty(name="Inferred Values", default=False, description="Inferred values")

    def init(self, wall_dimensions, opposite_wall_dimensions, relative_offset):
        self["limits"] = get_limits(wall_dimensions, opposite_wall_dimensions, relative_offset)
        self.size_offset.init(
            self["limits"],
            default_size=(2.0, 1.2),
            default_offset=((wall_dimensions[0]-2.0)/2, 0.8),
        )
        # call set_offset and set_size to restrict values
        self.size_offset.offset = self.size_offset.offset
        self.size_offset.size = self.size_offset.size

    def draw(self, context, layout):

        self.size_offset.draw(context, layout)

        col = layout.column(align=True)
        col.prop(self, "components", text="Components")
        col.prop(self, "only_hole")

        if not self.only_hole:

            layout.separator()
            col = layout.column(align=True)
            col.label(text="Frame")
            self.frame.draw(context, col)

            if "d" in self.components:
                layout.separator()
                col = layout.column()
                col.label(text="Door")
                self.door.draw(context, col)

            if "w" in self.components:
                layout.separator()
                col = layout.column()
                col.label(text="Window")
                self.window.draw(context, col)

        layout.separator()
        col = layout.column(align=True)
        col.prop(self, "different_widths")
        if self.different_widths:
            col.prop(self, "width_ratio")

        layout.separator()
        col = layout.column(align=True)
        col.prop(self, "add_arch")
        if self.add_arch:
            self.arch.draw(context, col)

        layout.separator()
        col = layout.column(align=True)
        if not self.infer_values_switch:
            col.prop(self, "infer_values_switch", icon="RIGHTARROW", emboss=False)
        else:
            col.prop(self, "infer_values_switch", icon="DOWNARROW_HLT", emboss=False)
            values = infer_values(self, self.components, 1 if not self.different_widths else self.width_ratio)
            if 'd' in self.components:
                for key,value in values.items():
                    if key.startswith("Door"):
                        row = col.row(align=True)
                        row.label(text=str(key))
                        row.label(text=str(value))
            if 'w' in self.components:
                for key,value in values.items():
                    if key.startswith("Window"):
                        row = col.row(align=True)
                        row.label(text=str(key))
                        row.label(text=str(value))
