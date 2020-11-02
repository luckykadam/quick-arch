import bpy
import bmesh
from contextlib import contextmanager

from .util_mesh import select, get_edit_mesh


def select_object(obj):
    """ Link object to active scene
    """
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


@contextmanager
def bmesh_from_active_object(context=None):
    context = context or bpy.context

    if context.mode == "EDIT_MESH":
        me = get_edit_mesh()
        bm = bmesh.from_edit_mesh(me)
    elif context.mode == "OBJECT":
        bm = bm_from_obj(context.object)

    yield bm

    if context.mode == "EDIT_MESH":
        bmesh.update_edit_mesh(me, True)
    elif context.mode == "OBJECT":
        bm_to_obj(bm, context.object)


def link_objects(objs, parent):
    collection = parent.users_collection[0]
    for obj in objs:
        obj.parent = parent
        for c in obj.users_collection:
            c.objects.unlink(obj)
        if obj.name not in collection.objects:
            collection.objects.link(obj)


def import_obj(path, name):
    """ Import object exported with up=Z and forward=X
    """
    current_selected = bpy.context.selected_objects
    bpy.ops.import_scene.obj(filepath=path, axis_up='Z', axis_forward="X")
    obj = [obj for obj in bpy.context.selected_objects if obj not in current_selected][0]
    obj.select_set(False)
    obj.name=name
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return obj


def import_blend(path, linked=True):
    """ Import object exported with up=Z and forward=X
    """
    with bpy.data.libraries.load(path, linked) as (data_from, data_to):
        data_to.objects = data_from.objects
        if hasattr(data_from, "groups") and data_from.groups:
            data_to.groups = data_from.groups
    return data_to.objects


def align_obj(obj, dir, track='Z', up='Y'):
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = dir.to_track_quat(track, up)
