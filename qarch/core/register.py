import bpy

from .fill import register_fill, unregister_fill
from .door import register_door, unregister_door
from .roof import register_roof, unregister_roof
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
    register_door,
    register_roof,
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
    unregister_door,
    unregister_roof,
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


def unregister_core():
    for func in unregister_funcs:
        func()
