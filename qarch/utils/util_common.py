import bpy
import traceback
import math
from math import radians
from mathutils import Vector, Euler


def equal(a, b, eps=0.001):
    """ Check if a and b are approximately equal with a margin of eps
    """
    return a == b or (abs(a - b) <= eps)


def clamp(value, minimum, maximum):
    """ Reset value between minimum and maximum
    """
    return max(min(value, maximum), minimum)


def args_from_props(props, names):
    """ returns a tuple with the properties in props for the given names
    """
    return tuple(getattr(props, name) for name in names)


def popup_message(message, title="Error", icon="ERROR"):
    def oops(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(oops, title=title, icon=icon)


def kwargs_from_props(props):
    """ Converts all properties in a props{bpy.types.PropertyGroup} into dict
    """
    valid_types = (
        int,
        str,
        bool,
        float,
        tuple,
        Vector,
        bpy.types.Material,
        bpy.types.Object,
    )

    result = {}
    for p in dir(props):
        if p.startswith("__") or p in ["rna_type", "bl_rna"]:
            continue

        prop = getattr(props, p)
        if isinstance(prop, valid_types):
            result[p] = prop
        elif isinstance(prop, bpy.types.PropertyGroup) and not isinstance(
            prop, type(props)
        ):
            # property group within this property
            result.update(kwargs_from_props(prop))
    return result


def crash_safe(func):
    """ Decorator to handle exceptions in bpy Operators safely
    """

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            popup_message(str(e), title="Operator Failed!")
            traceback.print_exc()
            return {"CANCELLED"}

    return inner


def get_limits(wall_dimensions, opposite_wall_dimensions, relative_offset):
    left_limit = max(0, wall_dimensions[0]/2-(opposite_wall_dimensions[0]/2-relative_offset[0])) + 0.01
    right_limit = wall_dimensions[0]-max(0, wall_dimensions[0]/2-opposite_wall_dimensions[0]/2-relative_offset[0]) - 0.01
    bottom_limit = min(0, wall_dimensions[1]/2-(opposite_wall_dimensions[1]/2-relative_offset[1])) + 0.01
    top_limit = wall_dimensions[1]-max(0, wall_dimensions[1]/2-opposite_wall_dimensions[1]/2-relative_offset[1]) - 0.01
    return (left_limit,right_limit,bottom_limit,top_limit)



def restricted_size(limits, offset, size_min, size):
    """ Get size restricted by various factors
    """
    limit_x = min(limits[1]-limits[0], limits[1]-offset[0])
    limit_y = min(limits[3]-limits[2], limits[3]-offset[1])
    
    x = clamp(size[0], size_min[0], limit_x)
    y = clamp(size[1], size_min[1], limit_y)
    return x, y


def restricted_offset(limits, size, offset):
    """ Get offset restricted by various factors
    """
    limit_x = limits[1] - size[0]
    limit_y = limits[3] - size[1]

    x = clamp(offset[0], limits[0], limit_x)
    y = clamp(offset[1], limits[2], limit_y)
    return x, y


def local_to_global(face, vec):
    """ Convert vector from local to global space, considering face normal as local z and world z as local y
    """
    x, y, z = local_xyz(face)
    global_offset = (x * vec.x) + (y * vec.y) + (z * vec.z)
    return global_offset


def local_xyz(face):
    """ Get local xyz directions
    """
    z = face.normal.copy()
    x = face.normal.copy()
    x.rotate(Euler((0.0, 0.0, radians(90)), "XYZ"))
    y = z.cross(x)
    return x, y, z


def radius_to_side_length(radius, n=4):
    theta = (n - 2) * math.pi / n
    return 2 * radius * math.cos(theta / 2)


def parse_components(components):
    char_to_type = {
        "d": "door",
        "w": "window",
    }
    previous = None
    dws = []
    for c in components:
        if c == previous:
            dws[-1]["count"] += 1
        else:
            if char_to_type.get(c):
                dws.append({"type": char_to_type.get(c), "count": 1})
                previous = c
            else:
                raise Exception("Unsupported component: {}".format(c))
    return dws


def infer_values(prop, components, width_ratio=1):
    n_w = sum(c=="w" for c in components)
    n_d = len(components)-n_w
    factor = n_w * width_ratio + n_d
    return {
        "Door Width": round((prop.size_offset.size[0]-prop.frame.margin*(len(components)+1))/factor,3),
        "Door Height" : round(prop.size_offset.size[1]+prop.size_offset.offset[1]-prop.frame.margin,3),
        "Window Width": round(width_ratio*(prop.size_offset.size[0]-prop.frame.margin*(len(components)+1))/factor,3),
        "Window Height": round(prop.size_offset.size[1]-prop.frame.margin,3),
    }
