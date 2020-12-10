import bpy
import math
import bmesh
import operator
import functools as ft
from mathutils import Vector, Quaternion
from bmesh.types import BMVert, BMEdge, BMFace
from contextlib import contextmanager
from .util_common import local_xyz, equal, radius_to_side_length


def get_edit_mesh():
    """ Get editmode mesh
    """
    return bpy.context.edit_object.data


def select(elements):
    """ For each item in elements set select to True
    """
    for el in elements:
        el.select_set(True)


def deselect(elements):
    """ For each item in elements set select to False
    """
    for el in elements:
        el.select_set(False)


def filter_invalid(elements):
    """ Return only valid items in elements
    """
    return list(filter(lambda el: el.is_valid, elements))


def filter_geom(geom, _type):
    """ Find all elements of type _type in geom iterable
    """
    return list(filter(lambda x: isinstance(x, _type), geom))


def edge_vector(edge):
    """ Return the normalized vector between edge vertices
    """
    v1, v2 = edge.verts
    return (v2.co - v1.co).normalized()


def edge_slope(e):
    """ Calculate the slope of an edge, 'inf' for vertical edges
    """
    v = edge_vector(e)
    try:
        return v.z / v.xy.length
    except ZeroDivisionError:
        return float("inf")


def edge_is_vertical(e):
    """ Check if edge is vertical (infinite slope)
    """
    return edge_slope(e) == float("inf")


def edge_is_sloped(e):
    """ Check if edge slope is between vertical and horizontal axis
    """
    sl = edge_slope(e)
    return sl > float("-inf") and sl < float("inf") and sl != 0.0


def valid_ngon(face):
    """ faces with rectangular shape and undivided horizontal edges are valid
    """
    horizontal_edges = filter_horizontal_edges(face.edges, face.normal)
    return len(horizontal_edges) == 2 and is_rectangle(face)


def is_rectangle(face):
    """ check if face is rectangular
    """
    angles = [math.pi - l.calc_angle() for l in face.loops]
    right_angles = len([a for a in angles if math.pi/2-0.001 < a < math.pi/2+0.001])
    straight_angles = len([a for a in angles if -0.001 < a < 0.001])
    return right_angles == 4 and straight_angles == len(angles) - 4


def vec_equal(a, b):
    angle = a.angle(b)
    return angle < 0.001 and angle > -0.001


def vec_opposite(a, b):
    angle = a.angle(b)
    return angle < math.pi + 0.001 and angle > math.pi - 0.001


def is_parallel(a, b):
    return vec_equal(a, b) or vec_opposite(a, b)


def is_connected(v1, v2):
    return v1.index in { e.other_vert(v2).index for e in v2.link_edges }


# def sort_edges_clockwise(edges):
#     """ sort edges clockwise based on angle from their median center
#     """
#     median_reference = ft.reduce(operator.add, map(calc_edge_median, edges)) / len(
#         edges
#     )

#     def sort_function(edge):
#         vector_difference = median_reference - calc_edge_median(edge)
#         return math.atan2(vector_difference.y, vector_difference.x)

#     return sorted(edges, key=sort_function, reverse=True)


def filter_vertical_edges(edges, normal):
    """ Determine edges that are vertical based on a normal value
    """
    return [e for e in edges if equal(edge_vector(e).dot(Vector((0,0,1))), 1) or equal(edge_vector(e).dot(Vector((0,0,1))), -1)]


def filter_horizontal_edges(edges, normal):
    """ Determine edges that are horizontal based on a normal value
    """
    return [e for e in edges if equal(edge_vector(e).dot(Vector((0,0,1))), 0)]


def filter_parallel_edges(edges, dir):
    """ Determine edges that are parallel to a vector
    """
    return [e for e in edges if is_parallel(edge_vector(e), dir)]


def calc_edge_median(edge):
    """ Calculate the center position of edge
    """
    return calc_verts_median(edge.verts)


def calc_verts_median(verts):
    """ Determine the median position of verts
    """
    return ft.reduce(operator.add, [v.co for v in verts]) / len(verts)


def calc_face_dimensions(face):
    """ Determine the width and height of face
    """
    horizontal_edges = filter_horizontal_edges(face.edges, face.normal)
    vertical_edges = filter_vertical_edges(face.edges, face.normal)
    width = sum(e.calc_length() for e in horizontal_edges) / 2
    height = sum(e.calc_length() for e in vertical_edges) / 2
    return width, height


def face_with_verts(bm, verts, default=None):
    """ Find a face in the bmesh with the given verts
    """
    for face in bm.faces:
        equal = map(
            operator.eq,
            sorted(verts, key=operator.attrgetter("index")),
            sorted(face.verts, key=operator.attrgetter("index")),
        )
        if len(face.verts) == len(verts) and all(equal):
            return face
    return default


def subdivide_face_horizontally(bm, face, widths):
    """ Subdivide the face horizontally, widths from left to right (face x axis)
    """
    if len(widths) < 2:
        return [face]
    edges = filter_horizontal_edges(face.edges, face.normal)
    direction, _, _ = local_xyz(face)
    inner_edges = subdivide_edges(bm, edges, direction, widths)
    return sort_faces(list({f for e in inner_edges for f in e.link_faces}), direction)


def subdivide_face_vertically(bm, face, widths):
    """ Subdivide the face vertically, widths from bottom to top (face y axis)
    """
    if len(widths) < 2:
        return [face]
    edges = filter_vertical_edges(face.edges, face.normal)
    _, direction, _ = local_xyz(face)
    inner_edges = subdivide_edges(bm, edges, direction, widths)
    return sort_faces(list({f for e in inner_edges for f in e.link_faces}), direction)


def subdivide_faces(bm, faces, direction, widths):
    if len(widths) < 2:
        return [face]
    edges = list({e for f in faces for e in f.edges if equal(edge_vector(e).dot(direction), -1) or equal(edge_vector(e).dot(direction), 1)})
    inner_edges = subdivide_edges(bm, edges, direction, widths)
    return sort_faces(list({f for e in inner_edges for f in e.link_faces}), direction)


def subdivide_edges(bm, edges, direction, widths):
    """ Subdivide edges in a direction, widths in the direction
    """
    dir = direction.copy()
    cuts = len(widths) - 1
    n_edges = len(edges)
    res = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts)
    inner_edges = sort_edges(filter_geom(res.get("geom_inner"), BMEdge), dir)
    distance = sum(widths) / len(widths)
    final_position = 0.0
    for i in range(cuts):
        ith_cut = inner_edges[i*(n_edges-1):(i+1)*(n_edges-1)]
        original_position = (i + 1) * distance
        final_position += widths[i]
        diff = final_position - original_position
        bmesh.ops.translate(bm, verts=list({v for e in ith_cut for v in e.verts}), vec=diff * dir)
    return inner_edges


def arc_edge(bm, edge, resolution, height, xyz, function="SPHERE"):
    """ Subdivide the given edge and offset vertices to form an arc
    """
    length = edge.calc_length()
    median = calc_edge_median(edge)
    arc_direction = edge_vector(edge).cross(xyz[2])
    orient = xyz[1] if edge_is_vertical(edge) else xyz[0]
    ret = bmesh.ops.subdivide_edges(bm, edges=[edge], cuts=resolution)

    verts = sort_verts(
        list({v for e in filter_geom(ret["geom_split"], bmesh.types.BMEdge) for v in e.verts}),
        orient
    )
    theta = math.pi / (len(verts) - 1)

    def arc_sine(verts):
        for idx, v in enumerate(verts):
            v.co += arc_direction * math.sin(theta * idx) * height

    def arc_sphere(verts):
        for idx, v in enumerate(verts):
            angle = math.pi - (theta * idx)
            v.co = median + orient * math.cos(angle) * length / 2
            v.co += arc_direction * math.sin(angle) * height

    {"SINE": arc_sine, "SPHERE": arc_sphere}.get(function)(verts)
    return ret


def extrude_face(bm, face, extrude_depth):
    """extrude a face
    """
    extruded_face = bmesh.ops.extrude_discrete_faces(bm, faces=[face]).get("faces")[0]
    bmesh.ops.translate(bm, verts=extruded_face.verts, vec=extruded_face.normal * extrude_depth)
    surrounding_faces = list({f for edge in extruded_face.edges for f in edge.link_faces if f not in [extruded_face]})
    return extruded_face, surrounding_faces


def extrude_face_region(bm, faces, depth, normal, keep_original=False):
    """extrude a face and delete redundant faces
    """
    initial_locations = [f.calc_center_bounds() for f in faces]
    geom = bmesh.ops.extrude_face_region(bm, geom=faces).get("geom")
    verts = filter_geom(geom, BMVert)
    bmesh.ops.translate(bm, verts=verts, vec=normal * depth)

    if not keep_original:
        bmesh.ops.delete(bm, geom=faces, context="FACES")  # remove redundant faces

    extruded_faces = filter_geom(geom, BMFace)
    # order extruded faces as per initially passed
    final_locations = [loc + depth * normal for loc in initial_locations]
    extruded_faces = closest_faces(extruded_faces, final_locations)
    surrounding_faces = list({f for edge in filter_geom(geom, BMEdge) for f in edge.link_faces if f not in extruded_faces})
    return extruded_faces, surrounding_faces, (faces if keep_original else [])


def extrude_edges(bm, edges, depth, direction):
    geom = bmesh.ops.extrude_edge_only(bm, edges=edges)["geom"]
    faces = filter_geom(geom, BMFace)
    edges = filter_geom(geom, BMEdge)
    bmesh.ops.translate(bm, verts=list({v for e in edges for v in e.verts}), vec=depth*direction)
    return edges, faces


def duplicate_faces(bm, faces):
    return filter_geom(bmesh.ops.duplicate(bm, geom=faces)["geom"], BMFace)


def edge_to_cylinder(bm, edge, radius, up, n=4, fill=False):
    edge_vec = edge_vector(edge)
    theta = (n - 2) * math.pi / n
    length = radius_to_side_length(radius, n)

    dir = up.copy()
    dir.rotate(Quaternion(edge_vec, -math.pi + theta / 2).to_euler())
    bmesh.ops.translate(bm, verts=edge.verts, vec=dir * radius)
    all_verts = [v for v in edge.verts]
    dir.rotate(Quaternion(edge_vec, math.pi - theta / 2).to_euler())
    for i in range(0, n):
        ret = bmesh.ops.extrude_edge_only(bm, edges=[edge])
        edge = filter_geom(ret["geom"], BMEdge)[0]
        bmesh.ops.translate(bm, verts=edge.verts, vec=dir * length)
        dir.rotate(Quaternion(edge_vec, math.radians(360 / n)).to_euler())
        all_verts += edge.verts

    bmesh.ops.remove_doubles(bm, verts=all_verts, dist=0.001)

    if fill:  # fill holes
        valid_verts = [v for v in all_verts if v.is_valid]
        sorted_edges = sort_edges({e for v in valid_verts for e in v.link_edges}, edge_vec)
        top_edges = sorted_edges[-n:]
        bottom_edges = sorted_edges[:n]
        bmesh.ops.holes_fill(bm, edges=top_edges)
        bmesh.ops.holes_fill(bm, edges=bottom_edges)

    return filter_invalid(all_verts)


def closest_faces(faces, locations):
    def get_face(faces, location):
        for f in faces:
            if equal((f.calc_center_bounds() - location).length, 0):
                return f

    return [get_face(faces, l) for l in locations]


def create_face(bm, size, offset, xyz):
    """ Create a face in xy plane of xyz space
    """
    offset = offset.x * xyz[0] + offset.y * xyz[1]

    v1 = bmesh.ops.create_vert(bm, co=offset)["vert"][0]
    v2 = bmesh.ops.create_vert(bm, co=offset+size.x*xyz[0])["vert"][0]
    v3 = bmesh.ops.create_vert(bm, co=offset+size.x*xyz[0]+size.y*xyz[1])["vert"][0]
    v4 = bmesh.ops.create_vert(bm, co=offset+size.y*xyz[1])["vert"][0]

    return bmesh.ops.contextual_create(bm, geom=[v1, v2, v3, v4])["faces"][0]


def get_top_edges(edges, n=1):
    return sort_edges(edges, Vector((0, 0, -1)))[:n]


def get_bottom_edges(edges, n=1):
    return sort_edges(edges, Vector((0, 0, 1)))[:n]


def get_top_faces(faces, n=1):
    return sort_faces(faces, Vector((0, 0, -1)))[:n]


def get_bottom_faces(faces, n=1):
    return sort_faces(faces, Vector((0, 0, 1)))[:n]


def sort_faces(faces, direction):
    return sorted(faces, key=lambda f: direction.dot(f.calc_center_bounds()))


def sort_edges(edges, direction):
    return sorted(edges, key=lambda e: direction.dot(calc_edge_median(e)))


def sort_verts(verts, direction):
    return sorted(verts, key=lambda v: direction.dot(v.co))


def get_opposite_face(face, faces, n=1):
    return sorted([f for f in faces if f!=face], key=lambda f:(face.calc_center_bounds()-f.calc_center_bounds()).length)[0]


def get_closest_edges(edge, edges, n=1):
    c = edge.verts[0].co + edge.verts[1].co
    return sorted(edges, key=lambda e:((e.verts[0].co+e.verts[1].co)-c).length)[:n]


def rotational_sort(verts, normal, start):
    pass

def get_relative_offset(f1, f2):
    x,y,_ = local_xyz(f1)
    d = f1.calc_center_bounds() - f2.calc_center_bounds()
    return -d.dot(x), -d.dot(y)

def boundary_edges(faces):
    return {e for f in faces for e in f.edges if common_faces(e, faces)<2}

def common_faces(edge, faces):
    count = 0
    for f in faces:
        if edge in f.edges:
            count += 1
    return count

@contextmanager
def managed_bmesh(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    try:
        yield bm
    finally:
        bm.to_mesh(me)

@contextmanager
def managed_bmesh_edit(edit_object):
    bm = bmesh.from_edit_mesh(edit_object.data)
    bm.faces.ensure_lookup_table()
    try:
        yield bm
    finally:
        bmesh.update_edit_mesh(edit_object.data, True)

def shrink_face(bm, face, thickness):
    bmesh.ops.delete(bm, geom=bmesh.ops.inset_individual(bm, faces=[face], thickness=thickness, use_even_offset=True)["faces"], context="FACES")
