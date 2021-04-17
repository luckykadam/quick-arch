import bpy

from .fill import register_fill, unregister_fill
from .door import register_door, unregister_door
from .roof_top import register_roof_top, unregister_roof_top
from .roof import register_roof, unregister_roof
from .floor import register_floor, unregister_floor
from .stairs import register_stairs, unregister_stairs
from .window import register_window, unregister_window
from .railing import register_railing, unregister_railing
from .balcony import register_balcony, unregister_balcony
from .generic import register_generic, unregister_generic
from .material import register_material, unregister_material
from .multigroup import register_multigroup, unregister_multigroup
from .asset import register_asset, unregister_asset, AssetPanelProperty
from .floorplan import register_floorplan, unregister_floorplan


# -- ORDER MATTERS --
register_funcs = (
    register_generic,
    register_material,
    register_railing,
    register_balcony,
    register_fill,
    register_door,
    register_roof_top,
    register_roof,
    register_floor,
    register_window,
    register_stairs,
    register_multigroup,
    register_asset,
    register_floorplan,
)

unregister_funcs = (
    unregister_generic,
    unregister_material,
    unregister_railing,
    unregister_balcony,
    unregister_fill,
    unregister_door,
    unregister_roof_top,
    unregister_roof,
    unregister_floor,
    unregister_window,
    unregister_stairs,
    unregister_multigroup,
    unregister_asset,
    unregister_floorplan,
)


def register_core():
    for func in register_funcs:
        func()
    bpy.types.Scene.qarch_asset_prop = bpy.props.PointerProperty(type=AssetPanelProperty)
    bpy.types.Scene.qarch_preview_collections = {}

def unregister_core():
    for func in unregister_funcs:
        func()
    for pcoll in bpy.types.Scene.qarch_preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    del bpy.types.Scene.qarch_asset_prop
    del bpy.types.Scene.qarch_preview_collections
