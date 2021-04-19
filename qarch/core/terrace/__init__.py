import bpy

from .terrace_ops import QARCH_OT_add_terrace
from .terrace_props import TerraceProperty

classes = (TerraceProperty, QARCH_OT_add_terrace)


def register_terrace():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_terrace():
    for cls in classes:
        bpy.utils.unregister_class(cls)
