import bmesh, bpy
import mathutils
from mathutils import Vector
from ...utils import (
    FaceMap,
    add_faces_to_map,
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
    crash_safe,
    managed_bmesh_edit,
    get_top_edges,
    filter_horizontal_edges,
    deselect,
)
from ..validations import validate, some_selection, flat_face_validation


@crash_safe
@validate([some_selection], ["No faces seleted"])
def build_roof_top(context, props):
    """ Create Roof Top from context and prop, with validations. Intented to be called directly from operator.
    """
    verify_facemaps_for_object(context.object)
    with managed_bmesh_edit(context.edit_object) as bm:
        faces = [f for f in bm.faces if f.select]
        deselect(faces)
        create_roof_top(bm, faces, props)
    return {"FINISHED"}


def create_roof_top(bm, faces, prop):
    """Create roof top
    """
    roof_origin = mean_vector([f.calc_center_bounds() for f in faces])
    roof = split_faces(bm, [faces], ["Roof"], delete_original=False)[0]
    link_objects([roof], bpy.context.object.users_collection)
    make_parent([roof], bpy.context.object)
    set_origin(roof, roof_origin)
    add_facemaps([FaceMap.ROOF, FaceMap.ROOF_HANGS], roof)
    gable_process_open(roof, prop)


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
