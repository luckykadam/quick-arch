import bpy

from .roof_ops import QARCH_OT_add_roof
from .roof_props import RoofProperty

classes = (RoofProperty, QARCH_OT_add_roof)


def register_roof():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_roof():
    for cls in classes:
        bpy.utils.unregister_class(cls)
