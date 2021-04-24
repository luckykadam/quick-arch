import bpy, bmesh
import math

from math import radians
from mathutils import Vector, Quaternion, Euler
from bmesh.types import BMFace, BMEdge

from ...utils import (
    FaceMap,
    vec_equal,
    local_xyz,
    valid_ngon,
    sort_faces,
    sort_edges,
    sort_verts,
    filter_geom,
    create_face,
    extrude_face,
    edge_is_sloped,
    subdivide_edges,
    add_faces_to_map,
    filter_parallel_edges,
    subdivide_face_vertically,
    calc_face_dimensions,
    calc_edge_median,
    split_faces,
    link_objects,
    make_parent,
    set_origin,
    get_bottom_edges,
    get_top_faces,
    managed_bmesh,
    add_faces_to_map,
    add_facemaps,
    verify_facemaps_for_object,
    map_new_faces,
    managed_bmesh_edit,
    crash_safe,
    deselect,
)
from ..validations import validate, some_selection, upright_face_validation 
from ..railing.railing import create_railing


@crash_safe
@validate([some_selection, upright_face_validation], ["No faces seleted", "Stairs creation not supported on non-upright n-gon!"])
def build_stairs(context, props):
    """ Create Stairs from context and prop, with validations. Intented to be called directly from operator.
    """
    verify_facemaps_for_object(context.object)
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        props.init(calc_face_dimensions(faces[0]))
        create_stairs(bm, faces, props)
    return {"FINISHED"}


def create_stairs(bm, faces, prop):
    """Extrude steps from selected faces
    """

    for f in faces:
        (stairs_face,stairs_origin) = create_stairs_split(bm, f, prop)
        # add_faces_to_map(bm, [f], FaceMap.WALLS)

        stairs = split_faces(bm, [[stairs_face]], ["Stairs"], delete_original=True)[0]
        # link objects and set origins
        link_objects([stairs], bpy.context.object.users_collection)
        make_parent([stairs], bpy.context.object)
        set_origin(stairs, stairs_origin)

        normal = f.normal.copy()
        create_steps(stairs, prop)

        if prop.railing_left or prop.railing_right:
            add_railing_to_stairs(stairs, normal, prop)

    return True


def create_steps(stairs, prop):
    """ Create stair steps with landing"""
    verify_facemaps_for_object(stairs)
    add_facemaps([FaceMap.WALLS, FaceMap.FLOOR], stairs)

    with managed_bmesh(stairs) as bm:
        with map_new_faces(bm, FaceMap.WALLS, obj=stairs):
            face = bm.faces[0]
            if prop.landing:
                step_widths = [prop.landing_width] + [prop.step_width] * prop.step_count
            else:
                step_widths = [prop.step_width] * prop.step_count

            if prop.bottom == "FILLED":
                top_faces, front_faces = create_filled_steps(bm, face, step_widths, prop.step_height)
            elif prop.bottom == "BLOCKED":
                top_faces, front_faces = create_blocked_steps(bm, face, step_widths, prop.step_height)
            elif prop.bottom == "SLOPE":
                top_faces, front_faces = create_slope_steps(bm, face, step_widths, prop.step_height)

        # add facemaps
        add_faces_to_map(bm, [top_faces+front_faces], [FaceMap.FLOOR], stairs)


# @map_new_faces(FaceMap.WALLS)
def create_filled_steps(bm, face, step_widths, step_height):
    """ Create filled stair steps with landing"""

    normal = face.normal.copy()
    top_faces = []
    front_faces = []

    # create steps
    front_face = face
    for i, step_width in enumerate(step_widths):
        if i == 0:
            front_face, surrounding_faces = extrude_face(bm, front_face, step_width)
            top_faces.append([f for f in surrounding_faces if vec_equal(f.normal, Vector((0., 0., 1.)))][0])
        else:
            bottom_face = list({f for e in front_face.edges for f in e.link_faces if vec_equal(f.normal, Vector((0., 0., -1.)))})[0]
            top_face, front_face, _ = extrude_step(bm, bottom_face, normal, step_height, step_width)
            top_faces.append(top_face)
        front_faces.append(front_face)
    # front_faces.append(front_face)
    return top_faces, front_faces


# @map_new_faces(FaceMap.WALLS)
def create_blocked_steps(bm, face, step_widths, step_height):
    """ Create blocked steps with landing"""

    normal = face.normal.copy()
    top_faces = []
    front_faces = []

    # create steps
    front_face = face
    for i, step_width in enumerate(step_widths):
        if i == 0:
            front_face, surrounding_faces = extrude_face(bm, front_face, step_width)
            top_faces.append([f for f in surrounding_faces if vec_equal(f.normal, Vector((0., 0., 1.)))][0])
        else:
            bottom_face = list({f for e in front_face.edges for f in e.link_faces if vec_equal(f.normal, Vector((0., 0., -1.)))})[0]
            edges = filter_parallel_edges(bottom_face.edges, normal)
            widths = [edges[0].calc_length() - step_height, step_height]

            inner_edges = subdivide_edges(bm, edges, normal, widths=widths)
            bottom_face = sort_faces(list({f for e in inner_edges for f in e.link_faces}), normal)[1]

            top_face, front_face, _ = extrude_step(bm, bottom_face, normal, step_height, step_width)
            top_faces.append(top_face)
        front_faces.append(front_face)
    return top_faces, front_faces


# @map_new_faces(FaceMap.WALLS)
def create_slope_steps(bm, face, step_widths, step_height):
    """ Create slope steps with landing"""

    normal = face.normal.copy()
    top_faces = []
    front_faces = []

    # create steps
    front_face = face
    for i, step_width in enumerate(step_widths):
        if i == 0:
            front_face, surrounding_faces = extrude_face(bm, front_face, step_width)
            top_faces.append([f for f in surrounding_faces if vec_equal(f.normal, Vector((0., 0., 1.)))][0])
        else:
            bottom_face = list({f for e in front_face.edges for f in e.link_faces if vec_equal(f.normal, Vector((0., 0., -1.)))})[0]

            e1 = sort_edges(bottom_face.edges, normal)[0]
            edges = filter_parallel_edges(bottom_face.edges, normal)
            widths = [edges[0].calc_length() - step_height, step_height]
            inner_edges = subdivide_edges(bm, edges, normal, widths=widths)
            bottom_face = sort_faces(list({f for e in inner_edges for f in e.link_faces}), normal)[1]
            e2 = sort_edges(bottom_face.edges, normal)[0]

            top_face, front_face, _ = extrude_step(bm, bottom_face, normal, step_height, step_width)
            top_faces.append(top_face)

            bmesh.ops.translate(bm, verts=e2.verts, vec=-2*normal*step_width/2)
            bmesh.ops.remove_doubles(bm, verts=list(e1.verts)+list(e2.verts), dist=0.001)
        front_faces.append(front_face)
    return top_faces, front_faces


def extrude_step(bm, face, normal, step_height, step_width):
    """ Extrude a stair step from previous bottom face
    """
    # extrude down
    n = face.normal.copy()
    face = bmesh.ops.extrude_discrete_faces(bm, faces=[face]).get("faces")[0]
    bmesh.ops.translate(bm, vec=n * step_height, verts=face.verts)

    # extrude front
    front_face = list({f for e in face.edges for f in e.link_faces if vec_equal(f.normal, normal)})[0]
    front_face, surrounding_faces = extrude_face(bm, front_face, step_width)
    flat_edges = list({e for f in surrounding_faces for e in f.edges if e.calc_face_angle() < 0.001 and e.calc_face_angle() > -0.001})
    bmesh.ops.dissolve_edges(bm, edges=flat_edges, use_verts=True)
    top_face = list({f for e in front_face.edges for f in e.link_faces if vec_equal(f.normal, Vector((0., 0., 1.)))})[0]
    bottom_face = list({f for e in front_face.edges for f in e.link_faces if vec_equal(f.normal, Vector((0., 0., -1.)))})[0]

    return top_face, front_face, bottom_face


def subdivide_next_step(bm, ret_face, remaining, step_height):
    """ cut the next face step height
    """
    return subdivide_face_vertically(bm, ret_face, widths=[remaining*step_height, step_height])[0]


def create_stairs_split(bm, face, prop):
    """Use properties to create face
    """
    xyz = local_xyz(face)
    size = Vector((prop.width, prop.step_height))
    f = create_face(bm, size, prop.offset - Vector((calc_face_dimensions(face)[0]/2, (calc_face_dimensions(face)[1]/2) - prop.step_height * (prop.step_count if prop.landing else prop.step_count - 1), 0)), xyz)
    bmesh.ops.translate(
        bm, verts=f.verts, vec=face.calc_center_bounds() + face.normal*prop.offset.z
    )
    if not vec_equal(f.normal, face.normal):
        bmesh.ops.reverse_faces(bm, faces=[f])
    return f, calc_edge_median(get_bottom_edges(f.edges, n=1)[0])


def add_railing_to_stairs(stairs, normal, prop):
    with managed_bmesh(stairs) as bm:
        top_faces = [f for f in bm.faces if vec_equal(f.normal, Vector((0.,0.,1.)))]
        steps = sort_faces(top_faces, normal)
        first_step = steps[0]
        last_step = steps[-1]

        # create railing initial edges
        if prop.landing:
            v1, v2 = railing_verts(bm, sort_verts(first_step.verts, normal)[:2], normal, prop.rail.offset, prop.rail.corner_post_width/2)
            v3, v4 = railing_verts(bm, sort_verts(first_step.verts, normal)[-2:], normal, prop.rail.offset, -prop.step_width/2)
            v5, v6 = railing_verts(bm, sort_verts(last_step.verts, normal)[:2], normal, prop.rail.offset, prop.step_width/2)
            e1 = bmesh.ops.contextual_create(bm, geom=(v1, v3))["edges"][0]
            e2 = bmesh.ops.contextual_create(bm, geom=[v3, v5])["edges"][0]
            e3 = bmesh.ops.contextual_create(bm, geom=[v2, v4])["edges"][0]
            e4 = bmesh.ops.contextual_create(bm, geom=[v4, v6])["edges"][0]
            railing_edges = [e1, e2, e3, e4]
        else:
            v1, v2 = railing_verts(bm, sort_verts(first_step.verts, normal)[:2], normal, prop.rail.offset, prop.step_width/2)
            v3, v4 = railing_verts(bm, sort_verts(last_step.verts, normal)[:2], normal, prop.rail.offset, prop.step_width/2)
            e1 = bmesh.ops.contextual_create(bm, geom=(v1, v3))["edges"][0]
            e2 = bmesh.ops.contextual_create(bm, geom=[v2, v4])["edges"][0]
            railing_edges = [e1, e2]

        # extrude edges
        ret = bmesh.ops.extrude_edge_only(bm, edges=railing_edges)
        top_edges = filter_geom(ret["geom"], BMEdge)
        top_verts = list({v for e in top_edges for v in e.verts})
        bmesh.ops.translate(bm, verts=top_verts, vec=Vector((0., 0., 1.))*prop.rail.corner_post_height)
        railing_faces = filter_geom(ret["geom"], BMFace)

        # filter non useful faces (based on left/right railings)
        useful_railing_faces = railing_faces
        x = normal.copy()
        x.rotate(Euler((0.0, 0.0, radians(90)), "XYZ"))
        n = len(useful_railing_faces)
        if prop.railing_left and not prop.railing_right:
            useful_railing_faces = sort_faces(railing_faces, x)[:n//2]
            bmesh.ops.delete(bm, geom=sort_faces(railing_faces, x)[n//2:], context="FACES")
        elif prop.railing_right and not prop.railing_left:
            useful_railing_faces = sort_faces(railing_faces, x)[n//2:]
            bmesh.ops.delete(bm, geom=sort_faces(railing_faces, x)[:n//2], context="FACES")

        # split useful railing facces to new object and create railings
        [railings] = split_faces(bm, [useful_railing_faces], ["Railings"], delete_original=True)
        create_railing(railings, prop.rail, normal)
        link_objects([railings], bpy.context.object.users_collection)
        make_parent([railings], stairs)
        # post_process_railing(bm, res, prop)


def railing_verts(bm, verts, normal, offset, depth):
    tangent = normal.copy()
    tangent.rotate(Quaternion(Vector((0.0, 0.0, 1.0)), math.pi / 2).to_euler())
    verts = sort_verts(verts, tangent)
    co1 = verts[0].co + depth * normal
    co2 = verts[1].co + depth * normal
    v1 = bmesh.ops.create_vert(bm, co=co1)["vert"][0]
    v2 = bmesh.ops.create_vert(bm, co=co2)["vert"][0]
    bmesh.ops.translate(bm, verts=[v1], vec=tangent * offset)
    bmesh.ops.translate(bm, verts=[v2], vec=-tangent * offset)
    return v1, v2


def post_process_railing(bm, railing, prop):
    fill = railing.fill
    if prop.rail.fill == "WALL":
        for wall in fill:

            # XXX check if any of the wall edges are sloped
            sloped_edges = [e for f in wall for e in f.edges if edge_is_sloped(e)]
            if sloped_edges:
                # -- translate bottom edges down by step height
                srted = sort_edges(sloped_edges, Vector((0, 0, 1)))
                bottom = srted[:len(srted) // 2]
                bmesh.ops.translate(
                    bm, verts=[v for e in bottom for v in e.verts], vec=(0, 0, -prop.step_height)
                )
