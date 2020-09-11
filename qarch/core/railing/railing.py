import math
import bmesh
from collections import namedtuple
from bmesh.types import BMFace, BMEdge, BMVert
from mathutils import Vector, Matrix, Quaternion
from ...utils import (
    clamp,
    FaceMap,
    filter_invalid,
    sort_edges,
    sort_verts,
    edge_vector,
    filter_geom,
    map_new_faces,
    edge_is_sloped,
    subdivide_edges,
    calc_verts_median,
    filter_vertical_edges,
    add_facemaps,
    managed_bmesh,
    verify_facemaps_for_object,
    add_faces_to_map,
    edge_to_cylinder,
    radius_to_side_length,
)


def create_railing(railings, prop, normal):
    verify_facemaps_for_object(railings)
    with managed_bmesh(railings) as bm:
        faces = [f for f in bm.faces]
        vertical_edges = list({e for f in faces for e in filter_vertical_edges(f.edges, f.normal)})
        cposts = make_corner_posts(bm, vertical_edges, prop, faces[0].normal)
        top_rails, fills = [], []
        for f in faces:
            top_rail, fill = make_fill(bm, f, prop)
            fills += fill
            top_rails += top_rail
        bmesh.ops.delete(bm, geom=faces, context="FACES")  # delete reference faces

        # add facemaps
        if prop.fill == "POSTS":
            fill_facemap = FaceMap.RAILING_POSTS
        elif prop.fill == "RAILS":
            fill_facemap = FaceMap.RAILING_RAILS
        else:
            fill_facemap = FaceMap.RAILING_WALLS
        facemaps = [FaceMap.RAILING_POSTS, FaceMap.RAILING_RAILS, fill_facemap]
        add_facemaps(facemaps, railings)
        add_faces_to_map(bm, [cposts, top_rails, fills], facemaps, railings)
    return cposts, top_rails, fills


# @map_new_faces(FaceMap.RAILING_POSTS)
def make_corner_posts(bm, edges, prop, up):
    posts = []
    for edge in edges:
        ret = bmesh.ops.duplicate(bm, geom=[edge])
        dup_edge = filter_geom(ret["geom"], BMEdge)[0]
        post = edge_to_cylinder(bm, dup_edge, prop.corner_post_width / 2, up, fill=True)
        # posts.append(list({f for v in post for f in v.link_faces}))
        posts += post
    return list({f for v in posts for f in v.link_faces})


def make_fill(bm, face, prop):
    # duplicate original face and resize
    ret = bmesh.ops.duplicate(bm, geom=[face])
    dup_face = filter_geom(ret["geom"], BMFace)[0]
    vertical = filter_vertical_edges(dup_face.edges, dup_face.normal)
    non_vertical = [e for e in dup_face.edges if e not in vertical]
    top_edge = sort_edges(non_vertical, Vector((0., 0., -1.)))[0]
    bmesh.ops.translate(bm, verts=top_edge.verts, vec=Vector((0., 0., -1.))*radius_to_side_length(prop.corner_post_width/2)/2)

    # make dupface fit flush between corner posts
    translate_bounds(bm, dup_face.verts, edge_vector(top_edge), radius_to_side_length(prop.corner_post_width/2)/2)

    # create railing top
    # add_facemaps(FaceMap.RAILING_RAILS)
    top_rail = create_railing_top(bm, top_edge, prop)

    # create fill
    if prop.fill == "POSTS":
        fill = create_fill_posts(bm, dup_face, prop)
    elif prop.fill == "RAILS":
        fill = create_fill_rails(bm, dup_face, prop)
    elif prop.fill == "WALL":
        # add_facemapss(FaceMap.RAILING_WALLS)
        fill = create_fill_walls(bm, dup_face, prop)

    return top_rail, fill


# @map_new_faces(FaceMap.RAILING_RAILS)
def create_railing_top(bm, top_edge, prop):
    ret = bmesh.ops.duplicate(bm, geom=[top_edge])
    top_dup_edge = filter_geom(ret["geom"], BMEdge)[0]
    vec = edge_vector(top_dup_edge)

    up = vec.copy()
    horizon = vec.cross(Vector((0., 0., 1.)))
    up.rotate(Quaternion(horizon, math.pi/2).to_euler())

    sloped = edge_is_sloped(top_dup_edge)
    cylinder = edge_to_cylinder(bm, top_dup_edge, prop.corner_post_width/2, up)
    if sloped:
        rotate_sloped_rail_bounds(bm, cylinder, vec)

    bmesh.ops.translate(bm, verts=top_edge.verts, vec=Vector((0., 0., -1.))*radius_to_side_length(prop.corner_post_width/2)/2)
    return list({f for v in cylinder for f in v.link_faces})


# @map_new_faces(FaceMap.RAILING_POSTS)
def create_fill_posts(bm, face, prop):
    result = []
    vertical_edges = filter_vertical_edges(face.edges, face.normal)
    sorted_edges = sort_edges(
        [e for e in face.edges if e not in vertical_edges], Vector((0.0, 0.0, -1.0))
    )

    # create posts
    top_edge = sorted_edges[0]
    bottom_edge = sorted_edges[-1]
    top_edge_vector = top_edge.verts[0].co - top_edge.verts[1].co
    top_edge_vector.z = 0
    n_posts = round(top_edge_vector.length * prop.post_fill.density)
    dir = edge_vector(top_edge)
    sloped = edge_is_sloped(top_edge)
    if n_posts != 0:
        inner_edges = subdivide_edges(
            bm, [top_edge, bottom_edge], dir, widths=[1.0] * (n_posts + 1)
        )
        for edge in inner_edges:
            ret = bmesh.ops.duplicate(bm, geom=[edge])
            dup_edge = filter_geom(ret["geom"], BMEdge)[0]
            up = face.normal
            vec = edge_vector(dup_edge)
            cylinder = edge_to_cylinder(bm, dup_edge, prop.post_fill.size/2, up, n=prop.post_fill.segments)
            if sloped:
                rotate_top_faces(bm, cylinder, vec, dir)
            result += list({f for v in cylinder for f in v.link_faces})
        # delete reference faces
        dup_faces = list({f for e in inner_edges for f in e.link_faces})
        bmesh.ops.delete(bm, geom=dup_faces, context="FACES")
        # result.append(list({f for v in cylinder for f in v.link_faces}))
    else:
        # delete reference faces
        bmesh.ops.delete(bm, geom=[face], context="FACES")
    return result


# @map_new_faces(FaceMap.RAILING_RAILS)
def create_fill_rails(bm, face, prop):
    # create rails
    result = []
    rail_size = min(prop.rail_fill.size, prop.corner_post_width)

    vertical_edges = filter_vertical_edges(face.edges, face.normal)
    n_rails = math.floor(vertical_edges[0].calc_length() * prop.rail_fill.density)
    if n_rails != 0:
        inner_edges = subdivide_edges(
            bm, vertical_edges, Vector((0.0, 0.0, 1.0)), widths=[1.0] * (n_rails + 1)
        )
        for edge in inner_edges:
            ret = bmesh.ops.duplicate(bm, geom=[edge])
            dup_edge = filter_geom(ret["geom"], BMEdge)[0]
            up = face.normal

            vec = edge_vector(dup_edge)
            sloped = edge_is_sloped(dup_edge)
            cylinder = edge_to_cylinder(bm, dup_edge, rail_size / 2, up, n=prop.rail_fill.segments)
            if sloped:
                rotate_sloped_rail_bounds(bm, cylinder, vec)
            result += list({f for v in cylinder for f in v.link_faces})
        # delete reference faces
        dup_faces = list({f for e in inner_edges for f in e.link_faces})
        bmesh.ops.delete(bm, geom=dup_faces, context="FACES")
        # result.append(list({f for v in cylinder for f in v.link_faces}))
    else:
        # delete reference faces
        bmesh.ops.delete(bm, geom=[face], context="FACES")
    return result


# @map_new_faces(FaceMap.RAILING_WALLS)
def create_fill_walls(bm, face, prop):
    # create walls
    wall_size = clamp(prop.wall_fill.width, 0.001, prop.corner_post_width)

    ret = bmesh.ops.duplicate(bm, geom=[face])
    dup_face = filter_geom(ret["geom"], BMFace)[0]
    bmesh.ops.translate(bm, verts=dup_face.verts, vec=-face.normal * wall_size / 2)
    ret = bmesh.ops.extrude_edge_only(bm, edges=dup_face.edges)
    verts = filter_geom(ret["geom"], BMVert)
    bmesh.ops.translate(bm, verts=verts, vec=face.normal * wall_size)
    f = bmesh.ops.contextual_create(bm, geom=verts).get("faces")

    # delete reference faces and hidden faces
    bmesh.ops.delete(bm, geom=[face] + filter_geom(ret["geom"], BMFace), context="FACES")
    return [f[-1], dup_face]


def translate_bounds(bm, verts, dir, trans):
    """ Translate the end verts inwards
    """
    if dir.z: # if rail is sloping, make vector horizontal
        left = dir.cross(Vector((0, 0, -1)))
        dir.rotate(Quaternion(left, math.atan(dir.z / dir.xy.length)).to_euler())

    vec = dir.xy*trans
    mid = len(verts) // 2
    vts = sort_verts(verts, dir)
    bmesh.ops.translate(bm, verts=vts[:mid], vec=(vec.x, vec.y, 0.0))
    bmesh.ops.translate(bm, verts=vts[-mid:], vec=(-vec.x, -vec.y, 0.0))


def rotate_top_faces(bm, cylinder, dir, left):
    """ Rotate the upper faces (align posts to slanted railing)
    """
    mid = len(cylinder) // 2
    vts = sort_verts(cylinder, dir)
    angle = math.atan(left.z / left.xy.length)
    bmesh.ops.rotate(
            bm, verts=vts[-mid:], cent=calc_verts_median(vts[-mid:]),
            matrix=Matrix.Rotation(angle, 4, dir.cross(-left))
        )


def rotate_sloped_rail_bounds(bm, cylinder_verts, dir):
    """ Rotate the end faces of sloping cylinder rail to be vertically aligned
    """
    mid = len(cylinder_verts) // 2
    vts = sort_verts(cylinder_verts, dir)
    angle = math.atan(dir.z / dir.xy.length)
    for bunch in [vts[:mid], vts[-mid:]]:
        bmesh.ops.rotate(
            bm, verts=bunch, cent=calc_verts_median(bunch),
            matrix=Matrix.Rotation(angle, 4, dir.cross(Vector((0, 0, -1))))
        )
