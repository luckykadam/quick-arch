import bpy

from .stairs_ops import QARCH_OT_add_stairs
from .stairs_props import StairsProperty

classes = (StairsProperty, QARCH_OT_add_stairs)


def register_stairs():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_stairs():
    for cls in classes:
        bpy.utils.unregister_class(cls)
