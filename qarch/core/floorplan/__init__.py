import bpy

from .floorplan_ops import QARCH_OT_add_floorplan
from .floorplan_props import FloorplanProperty

classes = (FloorplanProperty, QARCH_OT_add_floorplan)


def register_floorplan():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_floorplan():
    for cls in classes:
        bpy.utils.unregister_class(cls)
