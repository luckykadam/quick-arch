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
        bm = bmesh.new()  # create an empty BMesh
        bm.from_mesh(context.object.data)  # fill it in from a Mesh

    yield bm

    if context.mode == "EDIT_MESH":
        bmesh.update_edit_mesh(me, loop_triangles=True)
    elif context.mode == "OBJECT":
        bm.to_mesh(context.object.data)
        bm.free()


def link_objects(objs, collections):
    for obj in objs:
        for collection in collections:
            collection.objects.link(obj)


def make_parent(objs, parent):
    for obj in objs:
        obj.parent = parent 


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
    with bpy.data.libraries.load(path, link=linked) as (data_from, data_to):
        data_to.objects = data_from.objects
        if hasattr(data_from, "groups") and data_from.groups:
            data_to.groups = data_from.groups

    parent_objs = [ob for ob in data_to.objects if not ob.parent]

    link_objects(parent_objs, bpy.context.object.users_collection)
    make_parent(parent_objs, bpy.context.object)
    def process_object(obj):
        for child in obj.children:
            process_object(child)
        obj.make_local()
        obj.select_set(False)

    for obj in parent_objs:
        process_object(obj)

    return parent_objs


def align_obj(obj, dir, track='Z', up='Y'):
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = dir.to_track_quat(track, up)
