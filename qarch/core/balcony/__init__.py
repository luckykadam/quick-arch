import bpy

from .balcony_ops import QARCH_OT_add_balcony
from .balcony_props import BalconyProperty

classes = (BalconyProperty, QARCH_OT_add_balcony)


def register_balcony():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_balcony():
    for cls in classes:
        bpy.utils.unregister_class(cls)
