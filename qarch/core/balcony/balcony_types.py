import bpy, bmesh
from bmesh.types import BMVert, BMFace
from mathutils import Vector

from ...utils import (
    clamp,
    FaceMap,
    local_xyz,
    sort_edges,
    valid_ngon,
    filter_geom,
    create_face,
    get_top_faces,
    get_bottom_faces,
    add_faces_to_map,
    calc_face_dimensions,
    get_bottom_edges,
    calc_edge_median,
    split_faces,
    link_objects,
    make_parent,
    set_origin,
    managed_bmesh,
    extrude_face_region,
    add_faces_to_map,
    verify_facemaps_for_object,
    add_facemaps,
    map_new_faces,
    vec_equal,
    managed_bmesh_edit,
    crash_safe,
    deselect,
    verify_facemaps_for_object,
)

from ..validations import validate, some_selection, upright_face_validation 
from ..railing.railing import create_railing


@crash_safe
@validate([some_selection, upright_face_validation], ["No faces seleted", "Balcony creation not supported on non-upright n-gon!"])
def build_balcony(context, props):
    """ Create Balcony from context and prop, with validations. Intented to be called directly from operator.
    """
    verify_facemaps_for_object(context.object)
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        props.init(calc_face_dimensions(faces[0]))
        create_balcony(bm, faces, props)
    return {"FINISHED"}


def create_balcony(bm, faces, prop):
    """Generate balcony geometry
    """
    for f in faces:
        normal = f.normal.copy()
        (balcony_face,balcony_origin) = create_balcony_split(bm, f, prop)

        balcony = split_faces(bm, [[balcony_face]], ["Balcony"], delete_original=True)[0]
        # link objects and set origins
        link_objects([balcony], bpy.context.object.users_collection)
        make_parent([balcony], bpy.context.object)
        set_origin(balcony, balcony_origin)

        extrude_balcony(balcony, prop.width, normal)

        if prop.has_railing:
            add_railing_to_balcony(balcony, normal, prop)


def extrude_balcony(balcony, depth, normal):
    verify_facemaps_for_object(balcony)
    with managed_bmesh(balcony) as bm:
        face = bm.faces[0]
        normal = face.normal.copy()
        [front_face], surrounding_faces, _ = extrude_face_region(bm, [face], depth, normal)
        top_face = get_top_faces(surrounding_faces)[0]
        bottom_face = get_bottom_faces(surrounding_faces)[0]
        wall_faces = [front_face] + [f for f in surrounding_faces if f not in [top_face, bottom_face]]

        # add facemaps        
        add_facemaps([FaceMap.WALLS, FaceMap.FLOOR, FaceMap.CEIL], balcony)
        add_faces_to_map(bm, [wall_faces, [top_face], [bottom_face]], [FaceMap.WALLS, FaceMap.FLOOR, FaceMap.CEIL])
        # map_balcony_faces(bm, front)


def add_railing_to_balcony(balcony, balcony_normal, prop):
    """Add railing to the balcony
    """
    with managed_bmesh(balcony) as bm:
        top = get_top_faces(bm.faces)[0]

        ret = bmesh.ops.duplicate(bm, geom=[top])
        dup_top = filter_geom(ret["geom"], BMFace)[0]

        ret = bmesh.ops.inset_individual(
            bm, faces=[dup_top], thickness=prop.rail.offset, use_even_offset=True
        )
        bmesh.ops.delete(bm, geom=ret["faces"], context="FACES")

        edges = sort_edges(dup_top.edges, balcony_normal)[1:]
        railing_geom = bmesh.ops.extrude_edge_only(bm, edges=edges)["geom"]
        bmesh.ops.translate(
            bm, verts=filter_geom(railing_geom, BMVert), vec=(0., 0., prop.rail.corner_post_height)
        )

        bmesh.ops.delete(bm, geom=[dup_top], context="FACES")

        railing_faces = filter_geom(railing_geom, BMFace)
        [railings] = split_faces(bm, [railing_faces], ["Railings"], delete_original=True)
        create_railing(railings, prop.rail, balcony_normal)
        link_objects([railings], bpy.context.object.users_collection)
        make_parent([railings], balcony)


def create_balcony_split(bm, face, prop):
    """Use properties to create face
    """
    xyz = local_xyz(face)
    size = Vector((prop.length, prop.slab_height))
    f = create_face(bm, size, prop.offset  - Vector((calc_face_dimensions(face)[0]/2, calc_face_dimensions(face)[1]/2, 0)), xyz)
    bmesh.ops.translate(
        bm, verts=f.verts, vec=face.calc_center_bounds() + face.normal*prop.offset.z
    )
    if not vec_equal(f.normal, face.normal):
        bmesh.ops.reverse_faces(bm, faces=[f])
    return f, calc_edge_median(get_bottom_edges(f.edges, n=1)[0])
