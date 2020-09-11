import bpy
from ...utils import plane, managed_bmesh, crash_safe

@crash_safe
def create_floorplan(bm, prop):
    """Create rectangular floorplan
    """
    obj = bpy.data.objects.new("Floorplan", bpy.data.meshes.new("Floorplan"))
    bpy.context.scene.collection.objects.link(obj)
    # deselect other objects
    for x in bpy.context.selected_objects:
        x.select_set(False)
    bpy.context.view_layer.objects.active = obj
    # select(bpy.context.view_layer.objects, False)
    obj.select_set(True)
    obj.location = bpy.context.scene.cursor.location
    with managed_bmesh(obj) as bm:
        plane(bm, prop.width / 2, prop.length / 2)
