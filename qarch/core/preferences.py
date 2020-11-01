import bpy


class QuickArchPreferences(bpy.types.PropertyGroup):
    libpath: bpy.props.StringProperty(name="Library Path", description="Path to Chocofur style Asset Library")

def register_preferences():
    bpy.utils.register_class(QuickArchPreferences)

def unregister_preferences():
    bpy.utils.unregister_class(QuickArchPreferences)