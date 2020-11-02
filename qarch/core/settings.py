import bpy


class QuickArchSettings(bpy.types.PropertyGroup):
    libpath: bpy.props.StringProperty(name="Library Path", description="Path to Chocofur style Asset Library", subtype="DIR_PATH")

def register_settings():
    bpy.utils.register_class(QuickArchSettings)

def unregister_settings():
    bpy.utils.unregister_class(QuickArchSettings)