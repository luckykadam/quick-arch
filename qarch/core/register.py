import bpy

from .fill import register_fill, unregister_fill
from .arch import register_arch, unregister_arch
from .door import register_door, unregister_door
from .roof_top import register_roof_top, unregister_roof_top
from .roof import register_roof, unregister_roof
from .terrace import register_terrace, unregister_terrace
from .floor import register_floor, unregister_floor
from .stairs import register_stairs, unregister_stairs
from .window import register_window, unregister_window
from .railing import register_railing, unregister_railing
from .balcony import register_balcony, unregister_balcony
from .generic import register_generic, unregister_generic
from .material import register_material, unregister_material
from .multigroup import register_multigroup, unregister_multigroup
from .asset import register_asset, unregister_asset
from .floorplan import register_floorplan, unregister_floorplan
from .settings import register_settings, unregister_settings, QuickArchSettings


# -- ORDER MATTERS --
register_funcs = (
    register_generic,
    register_material,
    register_railing,
    register_balcony,
    register_fill,
    register_arch,
    register_door,
    register_roof_top,
    register_roof,
    register_terrace,
    register_floor,
    register_window,
    register_stairs,
    register_multigroup,
    register_asset,
    register_floorplan,
    register_settings,
)

unregister_funcs = (
    unregister_generic,
    unregister_material,
    unregister_railing,
    unregister_balcony,
    unregister_fill,
    unregister_arch,
    unregister_door,
    unregister_roof_top,
    unregister_roof,
    unregister_terrace,
    unregister_floor,
    unregister_window,
    unregister_stairs,
    unregister_multigroup,
    unregister_asset,
    unregister_floorplan,
    unregister_settings,
)


def register_core():
    for func in register_funcs:
        func()
    bpy.types.Scene.qarch_settings = bpy.props.PointerProperty(type=QuickArchSettings)
    bpy.types.Scene.qarch_preview_collections = {}

def unregister_core():
    for func in unregister_funcs:
        func()
    for pcoll in bpy.types.Scene.qarch_preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    del bpy.types.Scene.qarch_settings
    del bpy.types.Scene.qarch_preview_collections
