import os, bpy
import bpy.utils.previews
from bpy.props import FloatVectorProperty

def get_asset_types(self, context):
    directory = context.scene.qarch_settings.libpath
    if not os.path.exists(directory):
        return []
    dirs = [d for d in os.listdir(directory) if not d.startswith('.')]
    return [(dir,dir,dir) for dir in dirs]

def get_categories(self, context):
    if not self.asset_type:
        return []
    directory = os.path.join(context.scene.qarch_settings.libpath,self.asset_type)
    dirs = [d for d in os.listdir(directory) if not d.startswith('.')]
    return [(dir,dir,dir) for dir in dirs]

def get_assets(self, context):
    if not self.category:
        return []
    directory = os.path.join(context.scene.qarch_settings.libpath,self.asset_type,self.category)
    dirs = [d[:-6] for d in os.listdir(directory) if not d.startswith('.') and d.endswith('.blend') and not os.path.isdir(os.path.join(directory,d))]
    images_directory = os.path.join(context.scene.qarch_settings.libpath,self.asset_type,self.category,"renders")
    collection_id = "{}.{}".format(self.asset_type,self.category)
    if collection_id in bpy.types.Scene.qarch_preview_collections:
        pcoll = bpy.types.Scene.qarch_preview_collections[collection_id]
    else:
        pcoll = bpy.utils.previews.new()
    bpy.types.Scene.qarch_preview_collections[collection_id] = pcoll
    enum_items = []
    for i,dir in enumerate(dirs):
        image_path = os.path.join(images_directory, dir+".jpg")
        thumb = pcoll.get(image_path)
        if not thumb:
            thumb = pcoll.load(image_path, image_path, 'IMAGE')
        enum_items.append((dir,dir,"",thumb.icon_id,i))
    pcoll.previews = enum_items
    return enum_items


class AssetProperty(bpy.types.PropertyGroup):

    offset: FloatVectorProperty(
        name="Offset",
        subtype="TRANSLATION",
        size=3,
        unit="LENGTH",
        description="Offset in face's space",
    )

    asset_type: bpy.props.EnumProperty(name="Asset Type", items=get_asset_types)
    category: bpy.props.EnumProperty(name="Category", items=get_categories)
    asset: bpy.props.EnumProperty(name="Asset", items=get_assets)
    track: bpy.props.EnumProperty(name="Track", items=[('X','X','X'),('Y','Y','Y'),('Z','Z','Z'),('-X','-X','-X'),('-Y','-Y','-Y'),('-Z','-Z','-Z')], default="Z")
    up: bpy.props.EnumProperty(name="Up", items=[('X','X','X'),('Y','Y','Y'),('Z','Z','Z')], default="Y")

    def init(self):
        self.offset = (0,0,0)

    def draw(self, context, layout):

        col = layout.column()
        col.prop(self, "asset_type")
        col.prop(self, "category")
        col = col.column()
        col.scale_y = 1.5
        col.template_icon_view(self, 'asset', show_labels=True)

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