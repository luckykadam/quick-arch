import bmesh, bpy
import mathutils, math
import numpy as np
from mathutils import Vector
from bmesh.types import BMVert, BMFace
from ...utils import (
    equal,
    vec_equal,
    select,
    FaceMap,
    filter_invalid,
    edge_vector,
    skeletonize,
    filter_geom,
    map_new_faces,
    add_faces_to_map,
    calc_edge_median,
    set_roof_type_hip,
    set_roof_type_gable,
    filter_vertical_edges,
    add_facemaps,
    extrude_face_region,
    split_faces,
    link_objects,
    make_parent,
    set_origin,
    verify_facemaps_for_object,
    managed_bmesh,
    mean_vector,
    boundary_edges,
    crash_safe,
    managed_bmesh_edit,
    extrude_face_region,
    get_top_edges,
    filter_horizontal_edges,
    deselect,
)
from ..validations import validate, some_selection, flat_face_validation


@crash_safe
@validate([some_selection, flat_face_validation], ["No faces seleted", "Roof creation not supported on non-flat n-gon!"])
def build_roof(context, props):
    """ Create Roof from context and prop, with validations. Intented to be called directly from operator.
    """
    verify_facemaps_for_object(context.object)
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        create_roof(bm, faces, props)
    return {"FINISHED"}


def create_roof(bm, faces, prop):
    """Create roof types
    """
    roof_origin = mean_vector([f.calc_center_median() for f in faces])
    if prop.type == "FLAT":
        roof = split_faces(bm, [faces], ["Roof"], delete_original=False)[0]
        link_objects([roof], bpy.context.object.users_collection)
        make_parent([roof], bpy.context.object)
        set_origin(roof, roof_origin)
        add_facemaps([FaceMap.ROOF, FaceMap.ROOF_HANGS], roof)
        create_flat_roof(roof, prop)
    elif prop.type == "GABLE":
        top_faces = create_gable_roof(bm, faces, prop)
        roof = split_faces(bm, [top_faces], ["Roof"], delete_original=False)[0]
        link_objects([roof], bpy.context.object.users_collection)
        make_parent([roof], bpy.context.object)
        set_origin(roof, roof_origin)
        add_facemaps([FaceMap.ROOF, FaceMap.ROOF_HANGS], roof)
        gable_process_open(roof, prop)
    elif prop.type == "HIP":
        top_faces = create_hip_roof(bm, faces, prop)
        roof = split_faces(bm, [top_faces], ["Roof"], delete_original=False)[0]
        link_objects([roof], bpy.context.object.users_collection)
        make_parent([roof], bpy.context.object)
        set_origin(roof, roof_origin)
        add_facemaps([FaceMap.ROOF, FaceMap.ROOF_HANGS], roof)
        gable_process_open(roof, prop)


# # @map_new_faces(FaceMap.ROOF)
def create_flat_roof(roof, prop):
    """Create a flat roof
    """
    verify_facemaps_for_object(roof)
    with managed_bmesh(roof) as bm:
        faces = list(bm.faces)
        bmesh.ops.reverse_faces(bm, faces=faces)
        # -- extrude up
        top_faces,surrounding_faces,_ = extrude_face_region(bm, faces, prop.thickness, Vector((0,0,1)), keep_original=True)
        add_faces_to_map(bm, [top_faces,surrounding_faces], [FaceMap.ROOF,FaceMap.ROOF_HANGS], roof)


def create_gable_roof(bm, faces, prop):
    """ Create gable roof
    """
    median = mean_vector([f.calc_center_median() for f in faces])
    original_edges = boundary_edges(faces)

    # -- get verts in anti-clockwise order (required by straight skeleton)
    verts = [v for v in reversed(sort_verts_clockwise(original_edges))]
    clean_verts = [v for i,v in enumerate(verts) if not equal(vert_angle(v, verts[i-1], verts[(i+1)%len(verts)]), math.pi)]
    points = [v.co.to_tuple()[:2] for v in clean_verts]

    # -- compute straight skeleton
    set_roof_type_gable()
    skeleton = skeletonize(points, [])
    height_scale = prop.height / max([arc.height for arc in skeleton])

    # -- create edges and vertices
    skeleton_edges = create_skeleton_verts_and_edges(
        bm, skeleton, original_edges, median, height_scale
    )

    # -- create faces
    top_faces = create_skeleton_faces(bm, clean_verts, skeleton_edges, original_edges)
    return [f for f in top_faces if f.normal.z > 0.001]


def create_hip_roof(bm, faces, prop):
    """Create a hip roof
    """
    median = mean_vector([f.calc_center_median() for f in faces])
    original_edges = boundary_edges(faces)

    # -- get verts in anti-clockwise order (required by straight skeleton)
    verts = [v for v in reversed(sort_verts_clockwise(original_edges))]
    clean_verts = [v for i,v in enumerate(verts) if not equal(vert_angle(v, verts[i-1], verts[(i+1)%len(verts)]), math.pi)]
    points = [v.co.to_tuple()[:2] for v in clean_verts]

    # -- compute straight skeleton
    set_roof_type_hip()
    skeleton = skeletonize(points, [])
    height_scale = prop.height / max([arc.height for arc in skeleton])

    # -- create edges and vertices
    skeleton_edges = create_skeleton_verts_and_edges(
        bm, skeleton, original_edges, median, height_scale
    )

    # -- create faces
    top_faces = create_skeleton_faces(bm, clean_verts, skeleton_edges, original_edges)
    return [f for f in top_faces if f.normal.z > 0.001]


def vert_angle(v, v_prev, v_next):
    v1 = (v_prev.co-v.co).normalized()
    v2 = (v_next.co-v.co).normalized()
    return v2.angle(v1)


def sort_verts_clockwise(boundary_edges):
    """ sort verts in anti clockwise direction
    """
    visited_edges = []
    e = list(boundary_edges)[0]
    v = e.verts[0]
    verts = []
    angle = 0
    while e not in visited_edges:
        visited_edges.append(e)
        e_next = [edge for edge in v.link_edges if edge in boundary_edges and edge != e][0]
        angle += interior_angle(e.other_vert(v), v , e_next.other_vert(v))
        v = e_next.other_vert(v)
        verts.append(v)
        e = e_next
    if angle > 0:
        return list(reversed(verts))
    return verts


def vert_at_loc(loc, verts, loc_z=None):
    """ Find all verts at loc(x,y), return the one with highest z coord
    """
    results = []
    for vert in verts:
        co = vert.co
        if equal(co.x, loc.x) and equal(co.y, loc.y):
            if loc_z:
                if equal(co.z, loc_z):
                    results.append(vert)
            else:
                results.append(vert)

    if results:
        return max([v for v in results], key=lambda v: v.co.z)
    return None


def create_skeleton_verts_and_edges(bm, skeleton, original_edges, median, height_scale):
    """ Create the vertices and edges from output of straight skeleton
    """
    skeleton_edges = []
    skeleton_verts = []
    for arc in skeleton:
        source = arc.source
        vsource = vert_at_loc(source, bm.verts)
        if not vsource:
            source_height = [arc.height for arc in skeleton if arc.source == source]
            ht = source_height.pop() * height_scale
            vsource = make_vert(bm, Vector((source.x, source.y, median.z + ht)))
            skeleton_verts.append(vsource)

        for sink in arc.sinks:
            vs = vert_at_loc(sink, bm.verts)
            if not vs:
                sink_height = min([arc.height for arc in skeleton if sink in arc.sinks])
                ht = height_scale * sink_height
                vs = make_vert(bm, Vector((sink.x, sink.y, median.z + ht)))
            skeleton_verts.append(vs)

            # create edge
            if vs != vsource:
                geom = bmesh.ops.contextual_create(bm, geom=[vsource, vs]).get("edges")
                skeleton_edges.extend(geom)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

    skeleton_edges = filter_invalid(skeleton_edges)
    S_verts = {v for e in skeleton_edges for v in e.verts}
    O_verts = {v for e in original_edges for v in e.verts}
    skeleton_verts = [v for v in skeleton_verts if v in S_verts and v not in O_verts]
    return join_intersections_and_get_skeleton_edges(bm, skeleton_verts, skeleton_edges)


def interior_angle(prev_v, v, next_v):
        """ Determine cross product between two edges with one vert in common. Increases in ACW direction
        """
        # XXX Order of vector creation is really important
        v1 = (prev_v.co - v.co).normalized()
        v2 = (next_v.co - v.co).normalized()
        v1.z = 0
        v2.z = 0
        return v1.cross(v2).z

# @map_new_faces(FaceMap.ROOF)
def create_skeleton_faces(bm, verts, skeleton_edges, original_edges):
    """ Create faces formed from hiproof verts and edges
    """

    def boundary_walk(v, reverse=False):
        """ Perform boundary walk using least interior angle
        """
        first = v
        prev = v
        v = [e for e in v.link_edges if e in skeleton_edges][0].other_vert(v)
        walk = [prev, v]
        # traverse on skeleton edges
        while True:
            linked_verts = [
                e.other_vert(v) for e in v.link_edges if e in skeleton_edges and e.other_vert(v) not in walk
            ]
            if not linked_verts:
                break
            v, prev = min(linked_verts, key=lambda next: interior_angle(prev, v, next)), v
            walk.append(v)
        # traverse on original edges
        while v!=first:
            linked_verts = [e.other_vert(v) for e in v.link_edges if e in original_edges and vec_equal((first.co-v.co).normalized(), (e.other_vert(v).co-v.co).normalized())]
            if not linked_verts:
                break
            v, prev = linked_verts[0], v
            if v == first:
                break
            walk.append(v)
        return walk

    result = []
    for v in filter_invalid(verts):
        walk = boundary_walk(v)
        result.extend(bmesh.ops.contextual_create(bm, geom=walk).get("faces"))
    return result


def make_vert(bm, location):
    """ Create a vertex at locatiosn
    """
    return bmesh.ops.create_vert(bm, co=location).get("vert").pop()


def join_intersecting_verts_and_edges(bm, edges, verts):
    """ Find all vertices that intersect/ lie at an edge and merge
        them to that edge
    """
    eps = 0.0001
    new_verts = []
    for v in verts:
        for e in edges:
            if v in e.verts:
                continue

            v1, v2 = e.verts
            ortho = edge_vector(e).orthogonal().normalized() * eps
            res = mathutils.geometry.intersect_line_line_2d(v.co, v.co, v1.co, v2.co)
            if res is None:
                res = mathutils.geometry.intersect_line_line_2d(v.co - ortho, v.co + ortho, v1.co, v2.co)

            if res:
                split_vert = v1
                split_factor = (v1.co - v.co).length / e.calc_length()
                new_edge, new_vert = bmesh.utils.edge_split(e, split_vert, split_factor)
                new_verts.append(new_vert)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    return filter_invalid(new_verts)


def join_intersections_and_get_skeleton_edges(bm, skeleton_verts, skeleton_edges):
    """ Join intersecting edges and verts and return all edges that are in skeleton_edges
    """
    new_verts = join_intersecting_verts_and_edges(bm, skeleton_edges, skeleton_verts)
    skeleton_verts = filter_invalid(skeleton_verts) + new_verts
    return list(set(e for v in skeleton_verts for e in v.link_edges))


def gable_process_box(bm, roof_faces, prop):
    """ Finalize box gable roof type
    """
    # -- extrude upward faces
    top_faces = [f for f in roof_faces if f.normal.z]
    result = bmesh.ops.extrude_face_region(bm, geom=top_faces).get("geom")

    # -- move abit upwards (by amount roof thickness)
    bmesh.ops.translate(
        bm, verts=filter_geom(result, BMVert), vec=(0, 0, prop.thickness)
    )
    bmesh.ops.delete(bm, geom=top_faces, context="FACES")

    # -- face maps
    link_faces = {
        f for fc in filter_geom(result, BMFace) for e in fc.edges
        for f in e.link_faces if not f.normal.z
    }
    link_faces.update(set(filter_invalid(roof_faces)))
    add_faces_to_map(bm, [list(link_faces)], [FaceMap.ROOF_HANGS])


def gable_process_open(roof, prop):
    """ Finalize open gable roof type
    """
    verify_facemaps_for_object(roof)
    with managed_bmesh(roof) as bm:
        top_faces = list(bm.faces)
        # -- extrude
        _, side_faces, _ = extrude_face_region(bm, top_faces, prop.thickness, Vector((0,0,1)))
        dissolve_edges = list({get_top_edges([e for e in f.edges if e not in filter_vertical_edges(f.edges, f.normal)])[0] for f in side_faces})

        # -- outset side faces
        bmesh.ops.inset_region(
            bm, use_even_offset=True, faces=side_faces, depth=prop.outset, use_boundary=True
        )

        # -- move lower vertical edges abit down (inorder to maintain roof slope)
        bmesh.ops.translate(bm, verts=list({v for f in side_faces for v in f.verts if filter_horizontal_edges(f.edges, f.normal)}), vec=(0, 0, -prop.outset / 2))

        # -- post cleanup
        bmesh.ops.dissolve_edges(bm, edges=dissolve_edges, use_verts=True)

        # -- facemaps
        linked = {f for fc in side_faces for e in fc.edges for f in e.link_faces}
        linked_top = [f for f in linked if f.normal.z > 0]
        linked_bot = [f for f in linked if f.normal.z < 0]
        add_faces_to_map(bm, [linked_top, side_faces + linked_bot], [FaceMap.ROOF, FaceMap.ROOF_HANGS], obj=roof)
