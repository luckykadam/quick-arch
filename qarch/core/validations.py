import bmesh, bpy
from mathutils import Vector

from ..utils import (
    get_edit_mesh,
    vec_equal,
    vec_opposite,
    equal,
    valid_ngon,
    calc_face_dimensions,
)


def validate(validations, messages=[]):
    def decorator(function):
        def inner(*args, **kwargs):
            # validate before executing
            bm = bmesh.from_edit_mesh(get_edit_mesh())
            faces = [face for face in bm.faces if face.select]
            for (val,msg) in zip(validations,messages):
                if not val(faces):
                    raise Exception(msg)
            # execute function
            return function(*args, **kwargs)
        return inner
    return decorator


def flat_face_validation(faces):
    if all([vec_equal(f.normal, Vector((0,0,1))) or vec_opposite(f.normal, Vector((0,0,1))) for f in faces]):
        return True
    else:
        return False
    

def ngon_validation(faces):
    if all([valid_ngon(f) for f in faces]):
        return True
    else:
        return False


def upright_face_validation(faces):
    if all([equal(f.normal.z, 0) for f in faces]):
        return True
    else:
        return False

def some_selection(faces):
    if len(faces) == 0:
        return False
    else:
        return True

def same_dimensions(faces):
    if len(faces) == 0:
        return False
    w,h = calc_face_dimensions(faces[0])
    return all(equal(calc_face_dimensions(f)[0], w) and equal(calc_face_dimensions(f)[1], h) for f in faces)