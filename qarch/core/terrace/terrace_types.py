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
    get_closest_edges,
    get_top_edges,
)
from ..validations import validate, some_selection, flat_face_validation
from ..roof.roof_types import create_roof


@crash_safe
@validate([some_selection, flat_face_validation], ["No faces seleted", "Terrace creation not supported on non-flat n-gon!"])
def build_terrace(context, props):
    """ Create Terrace from context and prop, with validations. Intented to be called directly from operator.
    """
    verify_facemaps_for_object(context.object)
    add_facemaps([FaceMap.SLABS, FaceMap.WALLS, FaceMap.CEIL, FaceMap.FLOOR], context.object)
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        create_terrace(bm, faces, props)
    return {"FINISHED"}


def create_terrace(bm, faces, prop):
    """Create extrusions of floor geometry from a floorplan
    """
    n_faces = len(faces)
    slabs, walls, floors = extrude_slabs_and_walls(bm, faces, prop)

    add_faces_to_map(bm, [slabs, walls, floors], [FaceMap.SLABS, FaceMap.WALLS, FaceMap.FLOOR])

def extrude_slabs_and_walls(bm, faces, prop):
    """extrude edges alternating between slab and floor heights
    """
    slabs = []
    walls = []

    for f in faces:
        if not equal((f.normal-Vector((0,0,1))).length, 0):
            bmesh.ops.reverse_faces(bm, faces=[f])

    normal = Vector((0,0,1))

    # extrude vertically
    # ceils = []
    floors = []
    c = faces
    f = None

    # add slab
    f, s, c = extrude_slabs(
        bm, c, normal, prop.slab_height, prop.slab_outset)
    slabs += s
    # ceils += c
    floors += f

    # add walls
    c, w, f = extrude_walls(bm, f, normal, prop.wall_height,
                            prop.wall_thickness)
    walls += w
    # ceils += c
    floors += f

    bmesh.ops.delete(
        bm,
        geom=c,
        context="FACES")


    # fix normals of ceil and floor faces
    for f in floors:
        if not equal((f.normal-Vector((0,0,1))).length, 0):
            bmesh.ops.reverse_faces(bm, faces=[f])

    return slabs, walls, floors


def extrude_slabs(bm, faces, normal, height, outset):
    floor, slabs, ceil = extrude_face_region(
        bm, faces, height, normal, keep_original=True)
    dissolve_flat_edges(bm, slabs)
    slabs = filter_geom(bmesh.ops.region_extend(bm, geom=floor, use_faces=True)["geom"], BMFace)
    slabs += bmesh.ops.inset_region(bm, faces=slabs, depth=outset,
                                    use_even_offset=True, use_boundary=True)["faces"]
    return floor, slabs, ceil


def extrude_walls(bm, faces, normal, height, bounding_wall_thickness):
    # extrude exterior wall faces
    ceil, walls, floor = extrude_face_region(
        bm, faces, height, normal, keep_original=True)
    dup_floor = filter_geom(bmesh.ops.duplicate(
        bm, geom=floor)["geom"], BMFace)

    # inset room cluster
    bmesh.ops.delete(
        bm,
        geom=bmesh.ops.inset_region(bm, faces=dup_floor, thickness=bounding_wall_thickness,
                                    use_even_offset=True, use_boundary=True)["faces"],
        context="FACES")

    # extrude interior walls
    dup_ceil, inner_walls, dup_floor = extrude_face_region(
        bm, dup_floor, height, normal, keep_original=False)

    bmesh.ops.delete(bm, geom=dup_floor+dup_ceil, context="FACES")

    wall_tops = []
    for wall in walls:
        outer_edge = get_top_edges(wall.edges)[0]
        inner_edge = get_closest_edges(outer_edge, [get_top_edges(f.edges)[0] for f in inner_walls])[0]
        verts = [v for v in outer_edge.verts] + [v for v in inner_edge.verts]
        wall_tops += bmesh.ops.contextual_create(bm, geom=verts)["faces"]

    return ceil, walls+inner_walls+wall_tops, floor


def dissolve_flat_edges(bm, faces):
    flat_edges = list({
        e for f in faces for e in filter_vertical_edges(f.edges, f.normal)
        if len(e.link_faces) > 1 and equal(e.calc_face_angle(), 0)
    })
    bmesh.ops.dissolve_edges(bm, edges=flat_edges, use_verts=True)
