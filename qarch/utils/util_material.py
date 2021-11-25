import bpy
import bmesh
from enum import Enum, auto
from functools import wraps
from contextlib import contextmanager

from .util_mesh import get_edit_mesh
from .util_object import bmesh_from_active_object


class AutoIndex(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class FaceMap(AutoIndex):
    """ Enum provides names for face_maps """

    SLABS = auto()
    WALLS = auto()
    FLOOR = auto()
    CEIL = auto()
    # COLUMNS = auto()

    # FRAME = auto()

    # WINDOW = auto()
    # DOOR = auto()

    BARS = auto()
    PANES = auto()
    PANELS = auto()
    LOUVERS = auto()

    RAILING_POSTS = auto()
    RAILING_WALLS = auto()
    RAILING_RAILS = auto()

    ROOF = auto()
    ROOF_HANGS = auto()


def add_faces_to_map(bm, faces_list, facemaps, obj=None):
    obj = obj or bpy.context.object
    for faces, facemap in zip(faces_list, facemaps):
        face_map = bm.faces.layers.face_map.active
        group_index = face_map_index_from_name(obj, facemap.name.lower())
        for face in faces:
            face[face_map] = group_index

        # -- if the facemap already has a material assigned, assign the new faces to the material
        # mat = obj.facemap_materials[group_index].material
        # mat_id = [idx for idx, m in enumerate(obj.data.materials) if m == mat]
        # if mat_id:
        #     for f in faces:
        #         f.material_index = mat_id[-1]


def add_facemaps(facemaps, obj=None):
    """ Creates a face_map called group.name.lower if none exists
        in the active object
    """
    obj = obj if obj else bpy.context.object

    for facemap in facemaps:
        if not obj.face_maps.get(facemap.name.lower()):
            obj.face_maps.new(name=facemap.name.lower())
            obj.facemap_materials.add()


def verify_facemaps_for_object(obj):
    """ Ensure object has a facemap layer """
    me = get_edit_mesh()
    bm = bmesh.from_edit_mesh(me)
    bm.faces.layers.face_map.verify()
    bmesh.update_edit_mesh(me, loop_triangles=True)


def set_material_for_active_facemap(material, context):
    obj = context.object
    index = obj.face_maps.active_index
    active_facemap = obj.face_maps[index]

    link_material(obj, material)
    mat_id = [
        idx for idx, mat in enumerate(obj.data.materials) if mat == material
    ].pop()

    with bmesh_from_active_object(context) as bm:

        face_map = bm.faces.layers.face_map.active
        for face in bm.faces:
            if face[face_map] == active_facemap.index:
                face.material_index = mat_id


def face_map_index_from_name(obj, name):
    for _, fmap in obj.face_maps.items():
        if fmap.name == name:
            return fmap.index
    return -1


def link_material(obj, mat):
    """ link material mat to obj
    """
    if not has_material(obj, mat.name):
        obj.data.materials.append(mat)


def has_material(obj, name):
    """ check if obj has a material with name
    """
    return name in obj.data.materials.keys()


def create_object_material(obj, mat_name):
    """ Create a new material and link it to the given object
    """
    if not has_material(obj, mat_name):
        mat = bpy.data.materials.new(mat_name)
        link_material(obj, mat)
        return mat
    return obj.data.materials.get(mat_name)


# def uv_map_active_editmesh_selection(faces, method):
#     # -- ensure we are in editmode
#     if not bpy.context.object.mode == "EDIT":
#         return

#     # -- if faces are not selected, do selection
#     selection_state = [f.select for f in faces]
#     for f in faces:
#         f.select_set(True)

#     # -- perform mapping
#     if method == "UNWRAP":
#         bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
#     elif method == "CUBE_PROJECTION":
#         bpy.ops.uv.cube_project(cube_size=0.5)

#     # -- restore previous selection state
#     for f, sel in zip(faces, selection_state):
#         f.select_set(sel)

@contextmanager
def map_new_faces(bm, facemap, obj=None):
    obj = obj or bpy.context.object
    faces = set(bm.faces)
    try:
        yield None
    finally:
        new_faces = set(bm.faces) - faces
        add_faces_to_map(bm, [list(new_faces)], [facemap], obj=obj)
