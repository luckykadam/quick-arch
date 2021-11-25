import bmesh
from bmesh.types import BMEdge
from ...utils import (
    FaceMap,
    arc_edge,
    sort_verts,
    filter_geom,
    map_new_faces,
    get_bottom_faces,
    extrude_face_region,
    add_facemaps,
    managed_bmesh,
    shrink_face,
    verify_facemaps_for_object,
    calc_face_dimensions,
    add_faces_to_map,
)


def fill_arch(arch, prop):
    """ Fill arch
    """
    with managed_bmesh(arch) as bm:
        face = bm.faces[0]
        shrink_face(bm, face, 0.002)

        # validate_fill_props(prop)
        back, surrounding, front = extrude_face_region(bm, [face], prop.arch.thickness, -face.normal, keep_original=True)
        bmesh.ops.reverse_faces(bm, faces=front+surrounding+back)
        fill_arch_face(bm, arch, front[0], back[0], prop.arch.fill)


def fill_arch_face(bm, obj, front_face, back_face, prop):
    verify_facemaps_for_object(obj)
    if prop.fill_type == "GLASS_PANES":
        add_facemaps([FaceMap.PANES])
        fill_arch_pane(bm, obj, front_face, back_face, prop.glass_fill)


# @map_new_faces(FaceMap.PANES)
def fill_arch_pane(bm, obj, front_face, back_face, prop):
    dw_thickness = (front_face.calc_center_bounds()-back_face.calc_center_bounds()).length

    for face in [front_face, back_face]:
        width, height = calc_face_dimensions(face)
        if not round(width, 1) or not round(height, 1):
            return

        # XXX Ensure margin is less than parent face size
        min_dimension = min(calc_face_dimensions(face))
        prop.margin = min(
            prop.margin, min_dimension / 2)

        bmesh.ops.inset_individual(bm, faces=[face], use_even_offset=True, thickness=prop.margin)
        # quads, _ = subdivide_face_into_quads(bm, face, prop.count_x, prop.count_y, prop.pane_gap)

        # XXX Ensure pane border is less that size of each quad)
        # min_dimension = min(sum([calc_face_dimensions(q) for q in quads], ()))
        # prop.pane_border = min(prop.pane_border, min_dimension / 2)

        depth = (dw_thickness - prop.glass_thickness)/2
        bmesh.ops.inset_individual(
            bm, faces=[face], use_even_offset=True, thickness=prop.pane_border, depth=-depth
        )
        add_faces_to_map(bm, [[face]], [FaceMap.PANES], obj=obj)



def create_arch(bm, top_edges, height, offset, resolution, xyz, inner=False):
    """ Create arch using top edges of extreme frames
    """
    verts = sort_verts(list({v for e in top_edges for v in e.verts}), xyz[0])
    arc_edges = bmesh.ops.connect_verts(bm, verts=[verts[1], verts[-2]] if inner else [verts[0], verts[-1]])["edges"].pop()
    arc = arc_edge(bm, arc_edges, resolution, height, offset, xyz)
    arch_face = min(arc[resolution//2].link_faces, key=lambda f: f.calc_center_bounds().z)
    frame_faces = []
    if inner:
        frame_faces.append(max(arc[resolution//2].link_faces, key=lambda f: f.calc_center_bounds().z))
    return [arch_face], frame_faces


def add_arch_depth(bm, arch_face, depth, normal):
    """ Add depth to arch face
    """
    if depth > 0.0:
        arch_faces, frame_faces = extrude_face_region(bm, [arch_face], -depth, normal)
        return arch_faces[0], frame_faces
    else:
        return arch_face, []
