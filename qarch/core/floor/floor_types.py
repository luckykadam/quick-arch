import bmesh
from bmesh.types import BMFace
from mathutils import Vector

from ...utils import (
    FaceMap,
    filter_geom,
    add_faces_to_map,
    extrude_face_region,
    equal,
    crash_safe,
    filter_vertical_edges,
    managed_bmesh_edit,
    verify_facemaps_for_object,
    add_facemaps,
    deselect,
    is_connected,
    mean_vector,
)
from ..validations import validate, some_selection, flat_face_validation
from ..roof.roof_types import create_roof


@crash_safe
@validate([some_selection, flat_face_validation], ["No faces seleted", "Floor creation not supported on non-flat n-gon!"])
def build_floors(context, props):
    """ Create Floors from context and prop, with validations. Intented to be called directly from operator.
    """
    verify_facemaps_for_object(context.object)
    add_facemaps([FaceMap.SLABS, FaceMap.WALLS, FaceMap.CEIL, FaceMap.FLOOR], context.object)
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        top_faces = create_floors(bm, faces, props)
        if props.add_roof:
            create_roof(bm, top_faces, props.roof_prop)
    return {"FINISHED"}


def create_floors(bm, faces, prop):
    """Create extrusions of floor geometry from a floorplan
    """
    n_faces = len(faces)
    slabs, walls, ceils, floors = extrude_slabs_and_floors(bm, faces, prop)

    add_faces_to_map(bm, [slabs, walls, ceils, floors], [FaceMap.SLABS, FaceMap.WALLS, FaceMap.CEIL, FaceMap.FLOOR])
    return ceils[-n_faces:]

def extrude_slabs_and_floors(bm, faces, prop):
    """extrude edges alternating between slab and floor heights
    """
    slabs = []
    walls = []

    for f in faces:
        if not equal((f.normal-Vector((0,0,1))).length, 0):
            bmesh.ops.reverse_faces(bm, faces=[f])

    normal = Vector((0,0,1))

    # extrude vertically
    ceils = []
    floors = []
    c = faces
    f = None
    for i in range(prop.floor_count):
        # add slab
        f, s, c = extrude_slabs(
            bm, c, normal, prop.slab_height, prop.slab_outset)
        slabs += s
        ceils += c
        floors += f

        # add walls
        c, w, f = extrude_walls(bm, f, normal, prop.floor_height,
                                prop.wall_thickness, prop.wall_thickness)
        walls += w
        ceils += c
        floors += f

    # fix normals of ceil and floor faces
    for f in floors:
        if not equal((f.normal-Vector((0,0,1))).length, 0):
            bmesh.ops.reverse_faces(bm, faces=[f])

    for f in ceils:
        if not equal((f.normal-Vector((0,0,-1))).length, 0):
            bmesh.ops.reverse_faces(bm, faces=[f])

    return slabs, walls, ceils, floors


def extrude_slabs(bm, faces, normal, height, outset):
    floor, slabs, ceil = extrude_face_region(
        bm, faces, height, normal, keep_original=True)
    dissolve_flat_edges(bm, slabs)
    slabs = filter_geom(bmesh.ops.region_extend(bm, geom=floor, use_faces=True)["geom"], BMFace)
    slabs += bmesh.ops.inset_region(bm, faces=slabs, depth=outset,
                                    use_even_offset=True, use_boundary=True)["faces"]
    return floor, slabs, ceil


def calculate_diff(v, original_positions, original_directions, final_positions):
    linked_verts = {e.other_vert(v) for e in v.link_edges}
    print("{} linked_verts: {}".format(v.index, [v.index for v in linked_verts]))
    linked_verts_displacement = [ (final_positions[v2.index]-original_positions[v2.index]).dot(original_directions[(v2.index,v.index)]) for v2 in linked_verts ]
    return mean_vector(linked_verts_displacement)

def extrude_walls(bm, faces, normal, height, bounding_wall_thickness, internal_wall_thickness):
    # extrude exterior wall faces
    ceil, walls, floor = extrude_face_region(
        bm, faces, height, normal, keep_original=True)
    dup_floor = filter_geom(bmesh.ops.duplicate(
        bm, geom=floor)["geom"], BMFace)
    # print("initial_verts: {}".format({v.index for f in dup_floor for v in f.verts}))
    # verts = {v for f in dup_floor for v in f.verts}
    old_verts = {v for f in dup_floor for v in f.verts}
    original_positions = { v.index: v.co for v in old_verts }
    # print("original_positions: {}".format(original_positions))
    original_directions = { (v1.index,v2.index):(v2.co - v1.co).normalized() for v1 in old_verts for v2 in old_verts if v1.index!=v2.index and is_connected(v1,v2)}
    # print("original_directions: {}".format(original_directions))
    for v in old_verts:
        linked_verts = {e.other_vert(v) for e in v.link_edges}
        print("{} linked_verts: {}".format(v.index, [v.index for v in linked_verts]))

    # inset room cluster
    bmesh.ops.delete(
        bm,
        geom=bmesh.ops.inset_region(bm, faces=dup_floor, thickness=bounding_wall_thickness-internal_wall_thickness/2,
                                    use_even_offset=True, use_boundary=True)["faces"],
        context="FACES")
    # print("final_verts: {}".format({v.index for f in dup_floor for v in f.verts}))
    new_verts = {v for f in dup_floor for v in f.verts}
    for v in new_verts:
        linked_verts = {e.other_vert(v) for e in v.link_edges}
        print("{} linked_verts: {}".format(v.index, [v.index for v in linked_verts]))
    final_positions = { v.index: v.co for v in new_verts }
    for v in new_verts:
        print("displacement {}: {}".format(v.index, (final_positions[v.index]-original_positions[v.index]).length))
    # print("final_positions: {}".format(final_positions))
    diff = { v.index: calculate_diff(v, original_positions, original_directions, final_positions) for v in new_verts }
    print("diff: {}".format(diff))
    # innset individual room
    bmesh.ops.delete(
        bm,
        geom=bmesh.ops.inset_individual(bm, faces=dup_floor, thickness=internal_wall_thickness/2,
                                    use_even_offset=True)["faces"],
        context="FACES")

    # extrude interior walls
    dup_ceil, inner_walls, dup_floor = extrude_face_region(
        bm, dup_floor, height, normal, keep_original=False)

    bmesh.ops.delete(bm, geom=dup_floor+dup_ceil, context="FACES")
    return ceil, walls+inner_walls, floor


def slide_edge(bm, edge, distance):
    link_edges = [e for v in edge.verts for e in v.link_edges if e != edge]
    for v, e in zip(edge.verts, link_edges):
        other_vert = e.other_vert(v)
        dir = (other_vert.co - v.co)/e.calc_length()
        v.co += dir * distance


def dissolve_flat_edges(bm, faces):
    flat_edges = list({
        e for f in faces for e in filter_vertical_edges(f.edges, f.normal)
        if len(e.link_faces) > 1 and equal(e.calc_face_angle(), 0)
    })
    bmesh.ops.dissolve_edges(bm, edges=flat_edges, use_verts=True)
