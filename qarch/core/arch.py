import bmesh
from bmesh.types import BMEdge
from ..utils import (
    FaceMap,
    arc_edge,
    sort_verts,
    filter_geom,
    map_new_faces,
    get_bottom_faces,
    extrude_face_region,
    add_facemaps,
)


def fill_arch(bm, face, prop):
    """ Fill arch
    """
    if prop.fill_type == "GLASS_PANES":
        add_facemaps([FaceMap.PANES])
        pane_arch_face(bm, face, prop.glass_fill)


def create_arch(bm, top_edges, height, resolution, function, xyz, inner=False):
    """ Create arch using top edges of extreme frames
    """
    verts = sort_verts([v for e in top_edges for v in e.verts], xyz[0])
    arc_edges = bmesh.ops.connect_verts(bm, verts=[verts[1], verts[-2]] if inner else [verts[0], verts[-1]])["edges"].pop()
    arc = filter_geom(arc_edge(bm, arc_edges, resolution, height, xyz, function)["geom_split"], BMEdge)
    arch_face = min(arc[resolution//2].link_faces, key=lambda f: f.calc_center_bounds().z)
    frame_faces = list(set([f for e in arch_face.edges for f in e.link_faces if f is not arch_face]))
    return [arch_face], frame_faces


# @map_new_faces(FaceMap.PANES)
def pane_arch_face(bm, face, prop):
    bmesh.ops.inset_individual(
        bm, faces=[face], thickness=prop.pane_margin * 0.75, use_even_offset=True
    )
    bmesh.ops.translate(bm, verts=face.verts, vec=-face.normal * prop.pane_depth)


def add_arch_depth(bm, arch_face, depth, normal):
    """ Add depth to arch face
    """
    if depth > 0.0:
        arch_faces, frame_faces = extrude_face_region(bm, [arch_face], -depth, normal)
        return arch_faces[0], frame_faces
    else:
        return arch_face, []
