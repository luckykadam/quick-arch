import bpy

from .asset_ops import QARCH_OT_add_asset
from .asset_props import AssetProperty

classes = (AssetProperty, QARCH_OT_add_asset)


def register_asset():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_asset():
    for cls in classes:
        bpy.utils.unregister_class(cls)
