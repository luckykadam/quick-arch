import bpy

from .door_ops import QARCH_OT_add_door
from .door_props import DoorProperty
from .add_door_props import AddDoorProperty

classes = (DoorProperty, AddDoorProperty, QARCH_OT_add_door)


def register_door():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_door():
    for cls in classes:
        bpy.utils.unregister_class(cls)
