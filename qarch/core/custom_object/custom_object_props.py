import os, bpy
from bpy.props import FloatVectorProperty

def get_asset_types(self, context):
    directory = context.scene.qarch_prefs.libpath
    if not os.path.exists(directory):
        return []
    dirs = [d for d in os.listdir(directory) if not d.startswith('.')]
    return [(dir,dir,dir) for dir in dirs]

def get_categories(self, context):
    if not self.asset_type:
        return []
    directory = os.path.join(context.scene.qarch_prefs.libpath,self.asset_type)
    dirs = [d for d in os.listdir(directory) if not d.startswith('.')]
    return [(dir,dir,dir) for dir in dirs]

def get_asset_names(self, context):
    if not self.category:
        return []
    directory = os.path.join(context.scene.qarch_prefs.libpath,self.asset_type,self.category)
    dirs = [d[:-6] for d in os.listdir(directory) if not d.startswith('.') and d.endswith('.blend') and not os.path.isdir(os.path.join(directory,d))]
    return [(dir,dir,dir) for dir in dirs]


class CustomObjectProperty(bpy.types.PropertyGroup):

    offset: FloatVectorProperty(
        name="Offset",
        subtype="TRANSLATION",
        size=3,
        unit="LENGTH",
        description="Offset in face's space",
    )

    asset_type: bpy.props.EnumProperty(name="Asset Type", items=get_asset_types)
    category: bpy.props.EnumProperty(name="Category", items=get_categories)
    asset_name: bpy.props.EnumProperty(name="Asset Name", items=get_asset_names)
    track: bpy.props.EnumProperty(name="Track", items=[('X','X','X'),('Y','Y','Y'),('Z','Z','Z'),('-X','-X','-X'),('-Y','-Y','-Y'),('-Z','-Z','-Z')], default="Z")
    up: bpy.props.EnumProperty(name="Up", items=[('X','X','X'),('Y','Y','Y'),('Z','Z','Z')], default="X")

    def init(self):
        self.offset = (0,0,0)

    def draw(self, context, layout):

        col = layout.column()
        col.prop(self, "asset_type")
        col.prop(self, "category")
        col.prop(self, "asset_name")

        layout.separator()
        # layout.label(text="Alignment")
        row = layout.row(align=True)
        row.label(text="Offset ")
        row.column().prop(self, "offset", text="")

        row = layout.row(align=True)
        row.label(text="Track")
        row.prop(self, "track", expand=True)

        row = layout.row(align=True)
        row.label(text="Up")
        row.prop(self, "up", expand=True)