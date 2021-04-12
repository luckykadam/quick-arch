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
    verts = sort_verts(list({v for e in top_edges for v in e.verts}), xyz[0])
    arc_edges = bmesh.ops.connect_verts(bm, verts=[verts[1], verts[-2]] if inner else [verts[0], verts[-1]])["edges"].pop()
    arc = filter_geom(arc_edge(bm, arc_edges, resolution, height, xyz, function)["geom_split"], BMEdge)
    arch_face = min(arc[resolution//2].link_faces, key=lambda f: f.calc_center_bounds().z)
    bottom_face = None
    if len(verts)==2 or (len(verts)==4 and inner):
        verts = sort_verts(list({v for e in arc for v in e.verts}), xyz[0])
        new_edge = bmesh.ops.connect_verts(bm, verts=[verts[0],verts[-1]])['edges'].pop()
        bottom_face = get_bottom_faces(new_edge.link_faces).pop()
    frame_faces = []
    if inner:
        frame_faces.append(max(arc[resolution//2].link_faces, key=lambda f: f.calc_center_bounds().z))
    return [arch_face], frame_faces, bottom_face


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
