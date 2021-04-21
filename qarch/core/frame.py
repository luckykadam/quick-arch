import bpy, bmesh
from bmesh.types import BMFace, BMEdge
from mathutils import Vector

from ..utils import (
    extrude_face_region,
    parse_components,
    calc_face_dimensions,
    local_xyz,
    common_vert,
    sort_verts,
    sort_edges,
    get_bottom_edges,
    calc_edge_median,
    subdivide_face_horizontally,
    subdivide_face_vertically,
    get_opposite_face,
    get_relative_offset,
    sort_faces,
    get_top_edges,
    get_closest_edges,
    filter_geom,
    boundary_edges,
    common_faces,
    subdivide_faces,
    clamp,
    extrude_edges,
    equal,
    subdivide_edge,
    subdivide_edges,
    vec_equal,
    edge_vector,
    duplicate_faces,
    get_top_faces,
    filter_invalid,
)

from .arch import create_arch

def create_multigroup_frame_and_dw(bm, dw_faces, arch_faces, frame_prop, components, door_prop, window_prop, add_arch, arch_prop):
    normal = dw_faces[0].normal.copy()
    x,y,_ = local_xyz(dw_faces[0])

    dws = parse_components(components)
    frame_origin = calc_edge_median(get_bottom_edges(list({e for f in dw_faces for e in f.edges}))[0])
    door_faces, window_faces, arch_faces, frame_faces = create_frame(bm, dw_faces, arch_faces, dws, frame_prop, door_prop, window_prop, add_arch, arch_prop)
    bar_faces = [] if window_prop and not window_prop.add_bars else duplicate_faces(bm, window_faces)
    if door_prop and door_prop.double:
        both_door_origins = [
            (
                common_vert(
                    sort_edges(f.edges, x)[0], sort_edges(f.edges, y)[0]
                ).co - door_prop.thickness*(normal if not door_prop.flip_direction else -normal),
                common_vert(
                    sort_edges(f.edges, -x)[0], sort_edges(f.edges, y)[0]
                ).co - door_prop.thickness*(normal if not door_prop.flip_direction else -normal),
            )
            for f in door_faces
        ]
        door_faces = [f for door_face in door_faces for f in subdivide_face_horizontally(bm, door_face, widths=[get_top_edges(door_face.edges)[0].calc_length()/2]*2)]
        door_origins = [o for origins in both_door_origins for o in origins]
    else:
        door_origins = [
            common_vert(
                sort_edges(f.edges, x if door_prop.hinge=="LEFT" else -x)[0],
                sort_edges(f.edges, y)[0]
            ).co - door_prop.thickness*(normal if not door_prop.flip_direction else -normal)
            for f in door_faces
        ]

    if window_prop and window_prop.double:
        both_window_origins = [
            (
                common_vert(
                    sort_edges(f.edges, x)[0], sort_edges(f.edges, y)[0]
                ).co - window_prop.thickness*(normal if not window_prop.flip_direction else -normal),
                common_vert(
                    sort_edges(f.edges, -x)[0], sort_edges(f.edges, y)[0]
                ).co - window_prop.thickness*(normal if not window_prop.flip_direction else -normal),
            )
            for f in window_faces
        ]
        window_faces = [f for window_face in window_faces for f in subdivide_face_horizontally(bm, window_face, widths=[get_top_edges(window_face.edges)[0].calc_length()/2]*2)]
        window_origins = [o for origins in both_window_origins for o in origins]
    else:
        window_origins = [
            common_vert(
                sort_edges(f.edges, x if window_prop.hinge=="LEFT" else -x)[0],
                sort_edges(f.edges, y)[0]
            ).co - window_prop.thickness*(normal if not window_prop.flip_direction else -normal)
            for f in window_faces
        ]

    arch_origins = [
        calc_edge_median(get_bottom_edges(f.edges)[0]) - arch_prop.thickness*(normal if not arch_prop.flip_direction else -normal)
        for f in arch_faces
    ]

    return (filter_invalid(door_faces),door_origins), (filter_invalid(window_faces),bar_faces,window_origins), (filter_invalid(arch_faces),arch_origins), (filter_invalid(frame_faces),frame_origin)


def create_frame(bm, dw_faces, arch_faces, dws, frame_prop, door_prop, window_prop, add_arch, arch_prop):
    normal = dw_faces[0].normal.copy()
    xyz = local_xyz(dw_faces[0])

    doors = []
    windows = []
    archs = []
    frames = []

    # create dw faces
    for i, (dw, f) in enumerate(zip(dws, dw_faces)):
        if dw['type'] == 'door':
            _, face_height = calc_face_dimensions(f)
            door_height = face_height - frame_prop.margin
            ds, fs = create_door_frame_split(bm, f, dw['count'], frame_prop.margin, i == 0, i == len(dws)-1)
            doors.extend(ds)
            frames.extend(fs)
        elif dw['type'] == 'window':
            _, face_height = calc_face_dimensions(f)
            window_height = face_height - 2 * frame_prop.margin
            ws, fs = create_window_frame_split(bm, f, dw['count'], frame_prop.margin, i == 0, i == len(dws)-1)
            windows.extend(ws)
            frames.extend(fs)
    # create arch faces
    if add_arch:
        top_edges = sort_edges(get_top_edges({e for f in frames for e in f.edges},n=2*(len(doors)+len(windows))+1),xyz[0])
        top_face = max(top_edges[0].link_faces, key=lambda f: f.calc_center_bounds().z)
        if arch_prop.curved:
            arc_end_verts = sort_verts(sort_verts(top_face.verts, xyz[1])[2*(len(doors)+len(windows))+2:2*(len(doors)+len(windows))+4],xyz[0])
            top_edge = bmesh.ops.connect_verts(bm, verts=arc_end_verts)['edges'][0]
            new_top_edges = subdivide_edge(bm, top_edge, xyz[0] ,[frame_prop.margin,top_edge.calc_length()-2*frame_prop.margin,frame_prop.margin])
            e1 = bmesh.ops.connect_verts(bm, verts=[sort_verts(top_edges[0].verts,xyz[0])[-1], sort_verts(new_top_edges[0].verts,xyz[0])[-1]])['edges'][0]
            e2 = bmesh.ops.connect_verts(bm, verts=[sort_verts(top_edges[-1].verts,xyz[0])[0], sort_verts(new_top_edges[-1].verts,xyz[0])[0]])['edges'][0]
            new_faces = sort_faces(list(set(list(e1.link_faces)+list(e2.link_faces))),xyz[0])
            frames += [new_faces[0], new_faces[-1]]
            archs, frame_faces = create_arch(bm,[new_top_edges[1]],arch_prop.arc_height-frame_prop.margin,arch_prop.arc_offset,arch_prop.resolution,local_xyz(arch_faces[0]), inner=True)
            if frame_faces:
                frames += frame_faces
            frames = [f for f in frames if f not in archs]
        else:
            top_edge = max(top_face.edges, key=lambda e: calc_edge_median(e).z)
            new_top_edges = subdivide_edge(bm, top_edge, xyz[0] ,[frame_prop.margin,top_edge.calc_length()-2*frame_prop.margin,frame_prop.margin])
            e1 = bmesh.ops.connect_verts(bm, verts=[sort_verts(top_edges[0].verts,xyz[0])[-1], sort_verts(new_top_edges[0].verts,xyz[0])[-1]])['edges'][0]
            e2 = bmesh.ops.connect_verts(bm, verts=[sort_verts(top_edges[-1].verts,xyz[0])[0], sort_verts(new_top_edges[-1].verts,xyz[0])[0]])['edges'][0]
            new_faces = sort_faces(list(set(list(e1.link_faces)+list(e2.link_faces))),xyz[0])
            frames += [new_faces[0], new_faces[-1]]
            new_faces = subdivide_faces(bm, [new_faces[1]], xyz[1], [e1.calc_length()-frame_prop.margin, frame_prop.margin])
            frames += [new_faces[1]]
            archs = [new_faces[0]]
            frames = [f for f in frames if f not in archs]

    # separate dw faces and add depth
    frame_inner_edges = {
        'doors': [[e for e in bmesh.ops.split_edges(bm, edges=f.edges)["edges"] if e not in f.edges] for f in doors],
        'windows': [[e for e in bmesh.ops.split_edges(bm, edges=f.edges)["edges"] if e not in f.edges] for f in windows],
        'archs': [[e for e in bmesh.ops.split_edges(bm, edges=f.edges)["edges"] if e not in f.edges] for f in archs],
    }
    if doors:
        add_dw_depth(bm, doors, frame_prop.thickness, frame_prop.thickness-door_prop.thickness, normal, door_prop.flip_direction)
    if windows:
        add_dw_depth(bm, windows, frame_prop.thickness, frame_prop.thickness-window_prop.thickness, normal, window_prop.flip_direction)
    if archs:
        add_dw_depth(bm, archs, frame_prop.thickness, frame_prop.thickness-arch_prop.thickness, normal, arch_prop.flip_direction)
    # add frame thickness
    frames += add_frame_thickness(bm, frames, frame_inner_edges, frame_prop.thickness, frame_prop.border_thickness, door_prop, window_prop, arch_prop, normal)

    return doors, windows, archs, frames


def add_dw_depth(bm, faces, frame_thickness, dw_depth, normal, flip=False):
    if flip:
        bmesh.ops.reverse_faces(bm, faces=faces)
        bmesh.ops.translate(bm, vec=-normal*(frame_thickness-dw_depth), verts=[v for f in faces for v in f.verts])
    else:
        bmesh.ops.translate(bm, vec=-normal*dw_depth, verts=[v for f in faces for v in f.verts])


def add_frame_thickness(bm, frames, frame_inner_edges, frame_thickness, border_thickness, door_prop, window_prop, arch_prop, normal):
    # add framee thickness
    bmesh.ops.translate(bm, vec=-normal*frame_thickness, verts=list({v for f in frames for v in f.verts}))
    a,b,c = extrude_face_region(bm, frames, frame_thickness, normal, keep_original=True)
    frame_faces = a+b+c
    # add frame border
    if not equal(border_thickness, 0):
        for inner_edges in frame_inner_edges.get('doors',[]):
            inner_faces = list({f for e in inner_edges for f in e.link_faces if equal(f.normal.dot(normal),0)})
            frame_faces += add_border(bm, inner_faces, frame_thickness-door_prop.thickness, border_thickness, normal if not door_prop.flip_direction else -normal)
        for inner_edges in frame_inner_edges.get('windows',[]):
            inner_faces = list({f for e in inner_edges for f in e.link_faces if equal(f.normal.dot(normal),0)})
            frame_faces += add_border(bm, inner_faces, frame_thickness-window_prop.thickness, border_thickness, normal if not window_prop.flip_direction else -normal)
        for inner_edges in frame_inner_edges.get('archs',[]):
            inner_faces = list({f for e in inner_edges for f in e.link_faces if equal(f.normal.dot(normal),0)})
            frame_faces += add_border(bm, inner_faces, frame_thickness-arch_prop.thickness, border_thickness, normal if not arch_prop.flip_direction else -normal)
    return frame_faces


def add_border(bm, faces, thickness, depth, direction):
    inner_edges = list({e for f in faces for e in f.edges if vec_equal(edge_vector(e), direction) or vec_equal(edge_vector(e), -direction)})
    widths = [inner_edges[0].calc_length() - thickness, thickness]
    new_edges = subdivide_edges(bm, inner_edges, direction, widths=widths)
    new_faces = list({f for e in new_edges for f in e.link_faces})
    border_faces = sort_faces(new_faces, -direction)[:len(new_edges)]
    new_border_faces = bmesh.ops.inset_region(bm, use_even_offset=True, faces=border_faces, depth=depth, use_boundary=True)["faces"]
    outer_edges = sort_edges([e for f in border_faces for e in f.edges if equal(edge_vector(e).dot(direction),0)], -direction)[:len(new_border_faces)]
    bmesh.ops.translate(bm, vec=-direction*min(depth,thickness), verts=list({v for e in outer_edges for v in e.verts}))
    return list(set(new_faces+new_border_faces))


def create_door_frame_split(bm, face, count, frame_margin, first=False, last=False):
    w,h = calc_face_dimensions(face)
    door_height = h-frame_margin
    door_width = (w-frame_margin*(count+1))/count
    # vertical frame
    h_widths = [frame_margin, door_width] * count + [frame_margin]
    h_faces = subdivide_face_horizontally(bm, face, h_widths)
    # horizontal frames
    v_widths = [door_height, frame_margin]
    v_faces = [f for h_face in h_faces[1::2] for f in subdivide_face_vertically(bm, h_face, v_widths)]
    return v_faces[::2], h_faces[::2] + v_faces[1::2]


def create_window_frame_split(bm, face, count, frame_margin, first=False, last=False):
    w,h = calc_face_dimensions(face)
    # vertical frame
    if first and last:
        window_width = (w - (count+1)*frame_margin)/count
        h_widths = [frame_margin, window_width] * count + [frame_margin]
    elif first:
        window_width = (w - count*frame_margin)/count
        h_widths = [frame_margin, window_width] * count
    elif last:
        window_width = (w - count*frame_margin)/count
        h_widths = [window_width, frame_margin] * count
    else:
        window_width = (w - (count-1)*frame_margin)/count
        h_widths = [window_width, frame_margin] * (count - 1) + [window_width]
    h_faces = subdivide_face_horizontally(bm, face, h_widths)
    # horizontal frames
    if first:
        work_faces = h_faces[1::2]
        v_frames = h_faces[::2]
    else:
        work_faces = h_faces[::2]
        v_frames = h_faces[1::2]
    v_widths = [frame_margin, h-2*(frame_margin), frame_margin]
    v_faces = [f for h_face in work_faces for f in subdivide_face_vertically(bm, h_face, v_widths)]

    return v_faces[1::3], v_frames + v_faces[::3] + v_faces[2::3]


def create_multigroup_hole(bm, face, size, offset, components, width_ratio, frame_margin, frame_depth, add_arch, arch_prop):
    """ Use properties from SizeOffset to subdivide face into regular quads
    """
    xyz = local_xyz(face)
    opposite_face = get_opposite_face(face, [f for f in bm.faces if f!=face])
    relative_offset = Vector(get_relative_offset(face, opposite_face))
    wall_thickness = abs(face.normal.dot(face.calc_center_bounds()-opposite_face.calc_center_bounds())) if equal(relative_offset.y, 0) else float("inf")
    wall_width,_ = calc_face_dimensions(face)
    opposite_wall_width,_ = calc_face_dimensions(opposite_face)

    n_doors_comp = len([c for c in parse_components(components) if c["type"]=="door"])
    dw_count = len(parse_components(components))

    f1 = create_multigroup_split(bm, face, size, offset, components, width_ratio, frame_margin)
    a1 = []
    if add_arch:
        top_edges = get_top_edges( {e for f in f1 for e in f.edges}, n=dw_count)
        top_face = max(top_edges[0].link_faces, key=lambda f: f.calc_center_bounds().z)
        a,b = subdivide_face_vertically(bm, top_face, [arch_prop.straight_height,calc_face_dimensions(top_face)[1]-arch_prop.straight_height])
        a1 = [a]
        top_edge = max(a.edges, key=lambda e: calc_edge_median(e).z)
        if arch_prop.curved:
            a1,_ = create_arch(bm, [top_edge], arch_prop.arc_height, arch_prop.arc_offset, arch_prop.resolution, local_xyz(face))
            f1 = [f for f in f1 if f not in a1]
    opposite_offset = Vector((wall_width - offset.x - size.x - ( wall_width/2 - opposite_wall_width/2 - relative_offset.x),offset.y))
    s1 = sort_edges(get_top_edges(boundary_edges(f1+a1), n=len(boundary_edges(f1+a1))-n_doors_comp),xyz[0])
    s1,_ = extrude_edges(bm, s1, -f1[0].normal, min(frame_depth, wall_thickness))

    if relative_offset.length < 0.5:
        f2 = create_multigroup_split(bm, opposite_face, size, opposite_offset, reversed(components), width_ratio, frame_margin)
        a2 = []
        if add_arch:
            top_edges = sort_edges(get_top_edges({e for f in f2 for e in f.edges},n=dw_count),xyz[0])
            top_face = max(top_edges[0].link_faces, key=lambda f: f.calc_center_bounds().z)
            a,b = subdivide_face_vertically(bm, top_face, [arch_prop.straight_height,calc_face_dimensions(top_face)[1]-arch_prop.straight_height])
            a2 = [a]
            top_edge = max(a.edges, key=lambda e: calc_edge_median(e).z)
            if arch_prop.curved:
                a2,_ = create_arch(bm, [top_edge], arch_prop.arc_height, arch_prop.arc_offset, arch_prop.resolution, local_xyz(opposite_face))
                f2 = [f for f in f2 if f not in a2]
        s2 = get_top_edges(boundary_edges(f2+a2), n=len(boundary_edges(f2+a2))-n_doors_comp)
        for e1 in s1:
            e2 = get_closest_edges(e1, s2)[0]
            bmesh.ops.contextual_create(bm, geom=list(e1.verts)+list(e2.verts))
        bmesh.ops.delete(bm, geom=list(set(f2+a2)), context="FACES")

    # add depth to frame faces
    dup_faces = filter_geom(bmesh.ops.duplicate(bm, geom=list(set(f1+a1)))["geom"], BMFace)
    bmesh.ops.translate(bm, vec=-f1[0].normal*frame_depth, verts=list({v for f in dup_faces for v in f.verts}))
    bmesh.ops.delete(bm, geom=list(set(f1+a1)), context="FACES")
    xyz = local_xyz(dup_faces[0])
    if add_arch:
        dw_faces,arch_faces = sort_faces(dup_faces,xyz[1])[:-1], [sort_faces(dup_faces,xyz[1])[-1]]
    else:
        dw_faces,arch_faces=dup_faces,[]
    return sort_faces(dw_faces, xyz[0]), arch_faces


def create_multigroup_split(bm, face, size, offset, components, width_ratio, frame_margin):
    direction,_,_ = local_xyz(face)
    wall_w, wall_h = calc_face_dimensions(face)
    # horizontal split
    h_widths = [offset.x, size.x, wall_w-offset.x-size.x]
    h_faces = subdivide_face_horizontally(bm, face, h_widths)
    # vertical split
    v_width = [offset.y+size.y, wall_h-size.y-offset.y]
    v_faces = subdivide_face_vertically(bm, h_faces[1], v_width)

    dws = parse_components(components)
    door_count = sum(dw["count"] for dw in dws if dw["type"]=="door")
    window_count = sum(dw["count"] for dw in dws if dw["type"]=="window")
    door_width = (size.x - frame_margin * (door_count+window_count+1)) / (door_count + width_ratio*window_count)
    window_width = width_ratio * (size.x - frame_margin * (door_count+window_count+1)) / (door_count + width_ratio*window_count)

    # adjacent doors/windows clubbed
    clubbed_widths = [clubbed_width(door_width, window_width, frame_margin, dw['type'], dw['count'], i == 0, i == len(dws)-1) for i, dw in enumerate(dws)]
    clubbed_faces = subdivide_face_horizontally(bm, v_faces[0], clubbed_widths)
    faces = [f if dw['type']=='door' else subdivide_face_vertically(bm, f, [offset.y, size.y])[1] for dw,f in zip(dws, clubbed_faces)]

    return sort_faces(faces, direction)


def clubbed_width(door_width, window_width, frame_thickness, type, count, first=False, last=False):
    if type == "door":
        return (door_width * count) + (frame_thickness * (count + 1))
    elif type == "window":
        if first and last:
            return (window_width * count) + (frame_thickness * (count + 1))
        elif first or last:
            return (window_width * count) + (frame_thickness * count)
        else:
            return (window_width * count) + (frame_thickness * (count - 1))


def count(dws):
    return sum(dw["count"] for dw in dws)
