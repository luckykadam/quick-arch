import bpy

from .roof_top_ops import QARCH_OT_add_roof_top
from .roof_top_props import RoofTopProperty

classes = (RoofTopProperty, QARCH_OT_add_roof_top)


def register_roof_top():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_roof_top():
    for cls in classes:
        bpy.utils.unregister_class(cls)
