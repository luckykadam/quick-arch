import bpy, os

def get_asset_types(self, context):
    directory = context.scene.qarch_asset_prop.libpath
    if not os.path.exists(directory):
        return []
    dirs = [d for d in os.listdir(directory) if not d.startswith('.')]
    return [(dir,dir,dir) for dir in dirs]

def get_categories(self, context):
    if not self.asset_type:
        return []
    directory = os.path.join(context.scene.qarch_asset_prop.libpath,self.asset_type)
    dirs = [d for d in os.listdir(directory) if not d.startswith('.')]
    return [(dir,dir,dir) for dir in dirs]

def get_assets(self, context):
    if not self.category:
        return []
    directory = os.path.join(context.scene.qarch_asset_prop.libpath,self.asset_type,self.category)
    dirs = [d[:-6] for d in os.listdir(directory) if not d.startswith('.') and d.endswith('.blend') and not os.path.isdir(os.path.join(directory,d))]
    images_directory = os.path.join(context.scene.qarch_asset_prop.libpath,self.asset_type,self.category,"renders")
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

class AssetPanelProperty(bpy.types.PropertyGroup):
    libpath: bpy.props.StringProperty(name="Library Path", description="Path to Chocofur style Asset Library", subtype="DIR_PATH")
    asset_type: bpy.props.EnumProperty(name="Asset Type", items=get_asset_types)
    category: bpy.props.EnumProperty(name="Category", items=get_categories)
    asset: bpy.props.EnumProperty(name="Asset", items=get_assets)
