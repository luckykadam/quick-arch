import os, bpy
import bpy.utils.previews
from bpy.props import FloatVectorProperty

class AssetProperty(bpy.types.PropertyGroup):

    offset: FloatVectorProperty(
        name="Offset",
        subtype="TRANSLATION",
        size=3,
        unit="LENGTH",
        description="Offset in face's space",
    )

    track: bpy.props.EnumProperty(name="Track", items=[('X','X','X'),('Y','Y','Y'),('Z','Z','Z'),('-X','-X','-X'),('-Y','-Y','-Y'),('-Z','-Z','-Z')], default="Z")
    up: bpy.props.EnumProperty(name="Up", items=[('X','X','X'),('Y','Y','Y'),('Z','Z','Z')], default="Y")

    def init(self):
        self.offset = (0,0,0)

    def draw(self, context, layout):

        row = layout.row(align=True)
        row.label(text="Offset ")
        row.column().prop(self, "offset", text="")

        row = layout.row(align=True)
        row.label(text="Track")
        row.prop(self, "track", expand=True)

        row = layout.row(align=True)
        row.label(text="Up")
        row.prop(self, "up", expand=True)