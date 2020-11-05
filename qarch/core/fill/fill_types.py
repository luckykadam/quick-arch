import bmesh, math
from enum import Enum, auto
from mathutils import Vector, Matrix
from bmesh.types import BMEdge, BMVert, BMFace
from ...utils import (
    FaceMap,
    filter_invalid,
    filter_geom,
    map_new_faces,
    add_faces_to_map,
    calc_edge_median,
    calc_face_dimensions,
    filter_vertical_edges,
    filter_horizontal_edges,
    add_facemaps,
    verify_facemaps_for_object,
    edge_to_cylinder,
    duplicate_faces,
    subdivide_edges,
    local_xyz,
    get_closest_edges,
    subdivide_face_vertically,
    sort_faces,
)


class FillUser(Enum):
    DOOR = auto()
    WINDOW = auto()


def fill_face(bm, obj, front_face, back_face, fill_prop):
    verify_facemaps_for_object(obj)
    if fill_prop.fill_type == "PANELS":
        add_facemaps([FaceMap.PANELS], obj=obj)
        fill_panel(bm, obj, front_face, back_face, fill_prop.panel_fill)
    elif fill_prop.fill_type == "GLASS_PANES":
        add_facemaps([FaceMap.PANES], obj=obj)
        fill_glass_panes(bm, obj, front_face, back_face, fill_prop.glass_fill)
    # elif fill_prop.fill_type == "BAR":
    #     add_facemaps([FaceMap.BARS], obj=obj)
    #     fill_bars(bm, obj, front_face, fill_prop.bar_fill)
    elif fill_prop.fill_type == "LOUVER":
        add_facemaps([FaceMap.LOUVERS], obj=obj)
        fill_louver(bm, obj, front_face, back_face, fill_prop.louver_fill)


def fill_panel(bm, obj, front_face, back_face, prop):
    """Create panels on face
    """
    if prop.count_x + prop.count_y == 0:
        return

    for face in [front_face, back_face]:
        width, height = calc_face_dimensions(face)
        
        # XXX Ensure margin is less than parent face size
        min_dimension = min(calc_face_dimensions(face))
        prop.margin = min(
            prop.margin, min_dimension / 2)

        bmesh.ops.inset_individual(bm, faces=[face], thickness=prop.margin)
        quads, _ = subdivide_face_into_quads(bm, face, prop.count_x, prop.count_y, prop.panel_gap)

        # XXX Ensure panel border is less that size of each quad)
        min_dimension = min(sum([calc_face_dimensions(q) for q in quads], ()))
        prop.panel_border = min(prop.panel_border, min_dimension / 2)

        bmesh.ops.inset_individual(
            bm, faces=quads, use_even_offset=True, depth=-prop.panel_depth
        )
        add_faces_to_map(bm, [quads], [FaceMap.PANELS], obj=obj)
        bmesh.ops.inset_individual(
            bm, faces=quads, thickness=prop.panel_border, use_even_offset=True, depth=prop.panel_depth
        )


def fill_glass_panes(bm, obj, front_face, back_face, prop, user=FillUser.DOOR):
    """Create glass panes on face
    """
    if prop.count_x + prop.count_y == 0:
        return
    dw_thickness = (front_face.calc_center_bounds()-back_face.calc_center_bounds()).length

    for face in [front_face, back_face]:
        width, height = calc_face_dimensions(face)
        if not round(width) or not round(height):
            return

        # XXX Ensure margin is less than parent face size
        min_dimension = min(calc_face_dimensions(face))
        prop.margin = min(
            prop.margin, min_dimension / 2)

        bmesh.ops.inset_individual(bm, faces=[face], thickness=prop.margin)
        quads, _ = subdivide_face_into_quads(bm, face, prop.count_x, prop.count_y, prop.pane_gap)

        # XXX Ensure pane border is less that size of each quad)
        min_dimension = min(sum([calc_face_dimensions(q) for q in quads], ()))
        prop.pane_border = min(prop.pane_border, min_dimension / 2)

        depth = (dw_thickness - prop.glass_thickness)/2
        bmesh.ops.inset_individual(
            bm, faces=quads, use_even_offset=True, thickness=prop.pane_border, depth=-depth
        )
        add_faces_to_map(bm, [quads], [FaceMap.PANES], obj=obj)


def fill_bars(bm, obj, face, prop):
    """ Create horizontal and vertical bars along a face
    """
    if prop.bar_count_x + prop.bar_count_y == 0:
        return

    bmesh.ops.translate(bm, verts=face.verts, vec=face.normal * prop.bar_depth)
    width, height = calc_face_dimensions(face)
    xyz = local_xyz(face)
    add_facemaps([FaceMap.BARS], obj=obj)

    with map_new_faces(bm, FaceMap.BARS, obj):
        dup_face = duplicate_faces(bm, [face])[0]
        # horizontal
        horizontal_edges = subdivide_edges(bm, filter_vertical_edges(face.edges, xyz[2]), xyz[1], [height/(prop.bar_count_x+1)]*(prop.bar_count_x+1))
        horizontal_faces = list({f for e in horizontal_edges for f in e.link_faces})
        for edge in horizontal_edges:
            edge_to_cylinder(bm, edge, prop.bar_radius, xyz[2])
        bmesh.ops.delete(bm, geom=horizontal_faces, context="FACES")
        # vertical
        vertical_edges = subdivide_edges(bm, filter_horizontal_edges(dup_face.edges, xyz[2]), xyz[0], [height/(prop.bar_count_y+1)]*(prop.bar_count_y+1))
        vertical_faces = list({f for e in vertical_edges for f in e.link_faces})
        for edge in vertical_edges:
            edge_to_cylinder(bm, edge, prop.bar_radius, xyz[2])
        bmesh.ops.delete(bm, geom=vertical_faces, context="FACES")


def fill_louver(bm, obj, front_face, back_face, prop):
    """Create louvers from face
    """
    xyz = local_xyz(front_face)
    dw_thickness = (front_face.calc_center_bounds()-back_face.calc_center_bounds()).length
    # XXX Louver margin should not exceed smallest face dimension
    prop.margin = min(prop.margin, min(calc_face_dimensions(front_face)) / 2)

    # create frame
    bmesh.ops.inset_individual(bm, faces=[front_face], thickness=prop.margin)
    bmesh.ops.inset_individual(bm, faces=[back_face], thickness=prop.margin)
    front_edges = [e for e in bmesh.ops.split_edges(bm, edges=front_face.edges)["edges"] if e not in front_face.edges]
    back_edges = [e for e in bmesh.ops.split_edges(bm, edges=back_face.edges)["edges"] if e not in back_face.edges]

    # fill gaps
    for front_edge in front_edges:
        back_edge = get_closest_edges(front_edge, back_edges)[0]
        bmesh.ops.contextual_create(bm, geom=list(front_edge.verts)+list(back_edge.verts))
    bmesh.ops.delete(bm, geom=[back_face], context="FACES")
    bmesh.ops.translate(bm, verts=front_face.verts, vec=-xyz[2]*dw_thickness/2)

    # divide into lauvers
    louver_count = math.floor(calc_face_dimensions(front_face)[1]/prop.louver_width)
    extra_width = calc_face_dimensions(front_face)[1] - louver_count*prop.louver_width
    if round(extra_width,3) == 0:
        lauver_faces = subdivide_face_vertically(bm, front_face, widths=[prop.louver_width]*louver_count)
    else:
        lauver_faces = subdivide_face_vertically(bm, front_face, widths=[extra_width]+[prop.louver_width]*louver_count)[1:]
    bmesh.ops.split_edges(bm, edges=list({e for f in lauver_faces for e in f.edges}))
    for f in lauver_faces:
        bmesh.ops.rotate(bm, verts=f.verts, cent=f.calc_center_bounds(), matrix=Matrix.Rotation(math.radians(30.0), 3, -xyz[0]))
    lauver_faces += filter_geom(bmesh.ops.solidify(bm, geom=lauver_faces, thickness=0.005)["geom"], BMFace)
    add_faces_to_map(bm, [lauver_faces], [FaceMap.LOUVERS], obj=obj)


def subdivide_face_into_quads(bm, face, x, y, gap):
    """subdivide a face(quad) into more quads
    """
    if x==1 and y==1:
        return [face], []

    xyz = local_xyz(face)
    width, height = calc_face_dimensions(face)
    quad_width = (width-(x-1)*gap)/x
    quad_height = (height-(y-1)*gap)/y

    v_widths = [quad_height, gap] * (y-1) + [quad_height]
    h_widths = [quad_width, gap] * (x-1) + [quad_width]

    v_edges = filter_vertical_edges(face.edges, face.normal)
    h_edges = filter_horizontal_edges(face.edges, face.normal)

    edges = []
    if x > 0:
        edges += subdivide_edges(bm, v_edges, xyz[1], v_widths)
    if y > 0:
        edges += subdivide_edges(bm, h_edges+edges, xyz[0], h_widths)

    faces = sort_faces(list({f for e in filter_invalid(edges) for f in e.link_faces}), xyz[1])
    quads = []
    gaps = []
    for i in range(0, 2*y-1, 2):
        row = sort_faces(faces[i*(2*x-1):(i+1)*(2*x-1)], xyz[0])
        quads += row[::2]
        gaps += row[1::2]
    return quads, gaps
