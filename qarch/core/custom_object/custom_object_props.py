import bpy
from bpy.props import FloatVectorProperty

def get_mesh_objects():
    objs = [obj for obj in bpy.context.scene.objects if obj.type=="MESH" and obj!=bpy.context.object]
    return [("", "NONE", "NONE")] + [(obj.name, obj.name, obj.name) for obj in objs]

def objects(self, context):
    objects = self.get("objects", [])
    return [tuple(x) for x in objects]

class CustomObjectProperty(bpy.types.PropertyGroup):

    offset: FloatVectorProperty(
        name="Offset",
        subtype="TRANSLATION",
        size=3,
        unit="LENGTH",
        description="Offset in face's space",
    )

    obj: bpy.props.EnumProperty(name="Object", items=objects)
    track: bpy.props.EnumProperty(name="Track", items=[('X','X','X'),('Y','Y','Y'),('Z','Z','Z'),('-X','-X','-X'),('-Y','-Y','-Y'),('-Z','-Z','-Z')], default="Z")
    up: bpy.props.EnumProperty(name="Up", items=[('X','X','X'),('Y','Y','Y'),('Z','Z','Z')], default="X")

    def init(self):
        self["objects"] = get_mesh_objects()
        self.offset = (0,0,0)

    def draw(self, context, layout):

        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text="Offset: ")
        row.column().prop(self, "offset", text="")

        col = layout.column()
        row = col.row()
        row.prop(self, "obj")

        row = col.row()
        row.label(text="Track")
        row.prop(self, "track", expand=True)

        row = col.row()
        row.label(text="Up")
        row.prop(self, "up", expand=True)