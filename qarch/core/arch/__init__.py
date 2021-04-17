import bpy
from .arch_prop import FillGlassPanesArch, ArchFillProperty, ArchProperty
from .arch_type import fill_arch, create_arch, add_arch_depth

classes = (FillGlassPanesArch, ArchFillProperty, ArchProperty)


def register_arch():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_arch():
    for cls in classes:
        bpy.utils.unregister_class(cls)
