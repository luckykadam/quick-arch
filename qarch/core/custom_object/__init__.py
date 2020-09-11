import bpy

from .custom_object_ops import QARCH_OT_add_custom_object
from .custom_object_props import CustomObjectProperty

classes = (CustomObjectProperty, QARCH_OT_add_custom_object)


def register_custom_object():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_custom_object():
    for cls in classes:
        bpy.utils.unregister_class(cls)
