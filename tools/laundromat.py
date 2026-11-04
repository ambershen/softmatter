# Renders the Laundromat's door swings, empty drums and pearl pile, registered to the room photo.
# blender -b --python tools/laundromat.py -- <room.jpg> <outdir> <plates|doors|pearls|wool> [machine]
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index('--') + 1:]
ROOM, OUT, MODE = ARGS[0], ARGS[1], ARGS[2]
ONLY = int(ARGS[3]) if len(ARGS) > 3 else None
os.makedirs(OUT, exist_ok=True)

# The photo's camera: 513px per metre on the washer fronts, horizon at mid-frame, 5m back.
IW, IH, PPM, FLOOR_PX, CAM_D = 1089, 1445, 513.0, 1300.0, 5.0
CAM_Y = (FLOOR_PX - IH / 2) / PPM
wx = lambda px: (px - IW / 2) / PPM
wy = lambda py: (FLOOR_PX - py) / PPM
MACHINES = [('cocoa', 368, 548), ('wool', 719, 548), ('pearl', 368, 1043), ('lace', 719, 1043)]
R_DOOR, R_GLASS = 126 / PPM, 100 / PPM
FRAMES, MAX_ANGLE = 20, 104
CROP = (345, 150, 215, 215)  # px left, right, up, down of the door centre

def scene_setup(samples):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for d in prefs.devices: d.use = d.type == 'METAL'
    s.cycles.device = 'GPU'; s.cycles.samples = samples
    s.cycles.use_denoising = True; s.cycles.max_bounces = 8
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = IW, IH, 100
    s.render.film_transparent = True
    s.view_settings.view_transform = 'Standard'; s.view_settings.look = 'None'
    cam = bpy.data.cameras.new('cam'); cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36
    cam.lens = PPM * CAM_D / IW * 36
    o = bpy.data.objects.new('cam', cam); s.collection.objects.link(o)
    o.location = (0, CAM_Y, CAM_D); o.rotation_euler = (0, 0, 0); s.camera = o
    return s, o

def lighting():
    w = bpy.data.worlds.new('dusk'); w.use_nodes = True; bpy.context.scene.world = w
    n, l = w.node_tree.nodes, w.node_tree.links
    bg = n['Background']; tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ')
    mr = n.new('ShaderNodeMapRange'); ramp = n.new('ShaderNodeValToRGB')
    mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = -1, 1
    l.new(tc.outputs['Generated'], sep.inputs[0]); l.new(sep.outputs['Y'], mr.inputs['Value'])
    l.new(mr.outputs[0], ramp.inputs['Fac'])
    cr = ramp.color_ramp; cr.elements[0].position = .35; cr.elements[0].color = (.05, .035, .03, 1)
    cr.elements[1].position = .85; cr.elements[1].color = (.55, .50, .62, 1)
    e = cr.elements.new(.53); e.color = (1.0, .62, .46, 1)
    l.new(ramp.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.5
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 2.3; sun.angle = math.radians(7); sun.color = (1, .76, .6)
    o = bpy.data.objects.new('sun', sun); bpy.context.scene.collection.objects.link(o)
    d = Vector((-.62, .34, .71)).normalized()   # towards the sun: front-left, low
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y')

def mat(name, base, rough=.5, metal=0., **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*base, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    for k, v in kw.items(): p.inputs[k.replace('_', ' ')].default_value = v
    return m

def lathe(name, profile, seg=160, mats=None):
    """Revolve (r, z, mat index) around +Z through the origin."""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); rings = []
    for r, z, _ in profile:
        rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for a in (2 * math.pi * k / seg for k in range(seg))])
    for i in range(len(rings) - 1):
        for k in range(seg):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]))
            f.material_index = profile[i][2]; f.smooth = True
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    for m in mats or []: me.materials.append(m)
    return o

def drum(cx, cy, hole=R_GLASS * 1.04):
    """Gasket and perforated steel drum behind the opening."""
    steel = mat('steel', (.2, .17, .15), .3, 1.)
    n, l = steel.node_tree.nodes, steel.node_tree.links; p = n['Principled BSDF']
    # perforations: a dark dot grid wrapped around the drum wall
    tc = n.new('ShaderNodeTexCoord'); vor = n.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 62; vor.inputs['Randomness'].default_value = 0
    ramp = n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = .14; ramp.color_ramp.elements[0].color = (0, 0, 0, 1); ramp.color_ramp.elements[1].position = .17
    l.new(tc.outputs['Object'], vor.inputs['Vector']); l.new(vor.outputs['Distance'], ramp.inputs['Fac'])
    mix = n.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.inputs['A'].default_value = (.01, .008, .008, 1); mix.inputs['B'].default_value = (.2, .17, .15, 1)
    l.new(ramp.outputs[0], mix.inputs['Factor']); l.new(mix.outputs['Result'], p.inputs['Base Color'])
    rubber = mat('rubber', (.018, .016, .017), .42)
    R = R_GLASS * 1.42
    flange = mat('flange', (.72, .47, .33), .5)
    prof = [(R_DOOR * 1.05, 0, 2), (R_DOOR * .99, -.005, 2), (R_GLASS * 1.14, -.012, 2), (R_GLASS * 1.08, -.03, 0), (R_GLASS * 1.0, -.06, 0), (R_GLASS * 1.1, -.10, 0), (R, -.125, 1), (R, -.52, 1), (R * .55, -.56, 1), (.001, -.57, 1)]
    o = lathe('drum', prof, 128, [rubber, steel, flange]); o.location = (wx(cx), wy(cy), 0)
    # the washer front: unseen, but it keeps the sun out so the drum is lit only through the opening
    front = lathe('front', [(hole, .002, 0), (5, .002, 0)], 96, [mat('front', (.7, .55, .45), .6)]); front.location = o.location
    front.visible_camera = False
    for i in range(3):   # three lifter paddles
        a = math.pi / 2 + i * 2 * math.pi / 3
        bpy.ops.mesh.primitive_cube_add(size=1, location=(wx(cx) + math.cos(a) * R * .93, wy(cy) + math.sin(a) * R * .93, -.33), rotation=(0, 0, a))
        c = bpy.context.object; c.scale = (.05, .045, .38); c.data.materials.append(mat('paddle', (.22, .19, .17), .3, 1.))
        for pl in c.data.polygons: pl.use_smooth = False
    return o

def cabinet():
    """Shadow catcher on the washer front, with the door's opening cut out."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, wy(800), 0), rotation=(math.pi * 0, 0, 0))
    o = bpy.context.object; o.scale = (6, 4, 1); o.is_shadow_catcher = True
    return o

def door(cx, cy, room):
    """Ring and glass bowl hinged on the left; the ring's front wears the photo so the first frame is seamless."""
    tex = bpy.data.images.load(room)
    photo = bpy.data.materials.new('ringphoto'); photo.use_nodes = True
    n, l = photo.node_tree.nodes, photo.node_tree.links; p = n['Principled BSDF']; out = n['Material Output']
    im = n.new('ShaderNodeTexImage'); im.image = tex; im.image.colorspace_settings.name = 'sRGB'; im.extension = 'EXTEND'
    uv = n.new('ShaderNodeUVMap'); uv.uv_map = 'photo'; l.new(uv.outputs[0], im.inputs['Vector'])
    p.inputs['Roughness'].default_value = .36; p.inputs['Metallic'].default_value = .08; l.new(im.outputs[0], p.inputs['Base Color'])
    em = n.new('ShaderNodeEmission'); l.new(im.outputs[0], em.inputs['Color'])
    mix = n.new('ShaderNodeMixShader'); mix.name = 'lit'; l.new(em.outputs[0], mix.inputs[1]); l.new(p.outputs[0], mix.inputs[2]); l.new(mix.outputs[0], out.inputs['Surface'])
    chrome = mat('chrome', (.8, .77, .75), .2, 1.)
    backm = mat('back', (.5, .43, .38), .5)
    seal = mat('seal', (.05, .042, .04), .4)
    r0, r1 = R_DOOR, R_GLASS
    prof = [(r1 * .98, .0, 3), (r1 * 1.0, .012, 0), (r1 * 1.1, .03, 0), (r0 * .94, .034, 0), (r0, .02, 0), (r0 * 1.005, -.006, 1), (r0 * .96, -.024, 2), (r1 * 1.03, -.03, 2), (r1 * .98, .0, 2)]
    ring = lathe('ring', prof, 192, [photo, chrome, backm, seal])
    # glass bowl, bulging into the drum
    glass = bpy.data.materials.new('glass'); glass.use_nodes = True
    n, l = glass.node_tree.nodes, glass.node_tree.links; n.remove(n['Principled BSDF']); out = n['Material Output']
    tr = n.new('ShaderNodeBsdfTransparent'); tr.inputs[0].default_value = (.96, .92, .88, 1)
    gl = n.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = .03
    fr = n.new('ShaderNodeLayerWeight'); fr.inputs[0].default_value = .07
    mx = n.new('ShaderNodeMixShader'); l.new(fr.outputs['Fresnel'], mx.inputs[0]); l.new(tr.outputs[0], mx.inputs[1]); l.new(gl.outputs[0], mx.inputs[2]); l.new(mx.outputs[0], out.inputs['Surface'])
    bowl = [(r1 * .985 * math.cos(t), -.095 * math.sin(t), 0) for t in (k / 18 * math.pi / 2 for k in range(19))]
    bowl[-1] = (.001, bowl[-1][1], 0)
    gb = lathe('bowl', bowl, 128, [glass])
    # hinge pivot at the door's left edge, a little proud of the cabinet
    piv = bpy.data.objects.new('pivot', None); bpy.context.scene.collection.objects.link(piv)
    piv.location = (wx(cx) - r0 - .012, wy(cy), .03)
    for o in (ring, gb):
        o.parent = piv; o.location = (r0 + .012, 0, -.03)
    bpy.context.view_layer.update()
    # project the photo onto the closed ring
    me = ring.data; u = me.uv_layers.new(name='photo')
    for lp in me.loops:
        v = ring.matrix_world @ me.vertices[lp.vertex_index].co
        k = PPM * CAM_D / (CAM_D - v.z)
        px, py = IW / 2 + v.x * k, IH / 2 - (v.y - CAM_Y) * k
        u.data[lp.index].uv = (px / IW, 1 - py / IH)
    return piv, photo.node_tree.nodes['lit']

def crop(s, cx, cy):
    l, r, u, d = CROP
    s.render.use_border, s.render.use_crop_to_border = True, True
    s.render.border_min_x, s.render.border_max_x = (cx - l) / IW, (cx + r) / IW
    s.render.border_max_y, s.render.border_min_y = 1 - (cy - u) / IH, 1 - (cy + d) / IH

def out_webp(s, path, q=88):
    s.render.image_settings.file_format = 'WEBP'; s.render.image_settings.color_mode = 'RGBA'; s.render.image_settings.quality = q
    s.render.filepath = path; bpy.ops.render.render(write_still=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

def pile(cx, cy, seed=11):
    """A heap of pearls in the bottom of the drum; only the ones the camera can reach are built."""
    import numpy as np
    R = random.Random(seed); R_IN = R_GLASS * 1.42 - .02; spheres = []; pts = np.zeros((0, 4), np.float32)
    # dart-throwing, so no two pearls line up: anything under the heap's surface that doesn't overlap stays
    for _ in range(90000):
        x, y, z, r = R.uniform(-R_IN, R_IN), R.uniform(-R_IN, .03), R.uniform(-.34, -.04), R.uniform(.0125, .0185)
        top = .015 - .11 * (x / R_IN) ** 2 + .025 * math.sin(x * 21 + z * 9) + .16 * (z + .05)
        if y > top or math.hypot(x, y) > R_IN - r or (z < -.1 and y < top - .08): continue
        if len(pts) and (np.linalg.norm(pts[:, :3] - (x, y, z), axis=1) < (pts[:, 3] + r) * .97).any(): continue
        pts = np.vstack([pts, (x, y, z, r)])
    spheres = pts.tolist()
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=1)
    t = bpy.data.meshes.new('t'); bm.to_mesh(t); bm.free()
    V, L, P, N = len(t.vertices), len(t.loops), len(t.polygons), len(spheres)
    co = np.empty(V * 3, np.float32); t.vertices.foreach_get('co', co); co = co.reshape(V, 3)
    lv = np.empty(L, np.int32); t.loops.foreach_get('vertex_index', lv)
    ls = np.empty(P, np.int32); t.polygons.foreach_get('loop_start', ls)
    sp = np.array(spheres, np.float32)
    me = bpy.data.meshes.new('pile'); me.vertices.add(V * N); me.loops.add(L * N); me.polygons.add(P * N)
    me.vertices.foreach_set('co', (co[None] * sp[:, None, 3:4] + sp[:, None, :3]).ravel())
    me.loops.foreach_set('vertex_index', (lv[None] + (np.arange(N, dtype=np.int32) * V)[:, None]).ravel())
    me.polygons.foreach_set('loop_start', (ls[None] + (np.arange(N, dtype=np.int32) * L)[:, None]).ravel())
    me.update(calc_edges=True); me.validate(); me.shade_smooth()
    palette = np.array([(.86, .76, .74, 1), (.88, .8, .72, 1), (.8, .79, .84, 1), (.88, .74, .7, 1)], np.float32)
    a = me.color_attributes.new('tone', 'FLOAT_COLOR', 'POINT')
    a.data.foreach_set('color', np.repeat(palette[np.random.default_rng(seed).integers(0, 4, N)], V, axis=0).ravel())
    o = bpy.data.objects.new('pile', me); bpy.context.scene.collection.objects.link(o); o.location = (wx(cx), wy(cy), 0)
    m = mat('pearl', (.86, .78, .74), .34, 0., Coat_Weight=1., Coat_Roughness=.07, Coat_IOR=1.8, Thin_Film_Thickness=380., Thin_Film_IOR=1.4, Subsurface_Weight=.55, Subsurface_Scale=.02)
    n, l = m.node_tree.nodes, m.node_tree.links; at = n.new('ShaderNodeVertexColor'); at.layer_name = 'tone'; l.new(at.outputs[0], n['Principled BSDF'].inputs['Base Color'])
    me.materials.append(m); print('PEARLS', N)

def pixels(path):
    import numpy as np
    im = bpy.data.images.load(path); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im)
    return a.reshape(h, w, 4)

def save(a, path, q=86):
    import numpy as np
    h, w, _ = a.shape; im = bpy.data.images.new('o', w, h, alpha=True); im.pixels.foreach_set(np.ascontiguousarray(a, np.float32).ravel())
    s = bpy.context.scene; f = s.render.image_settings; f.file_format = 'JPEG' if path.endswith('.jpg') else 'WEBP'; f.color_mode = 'RGB' if path.endswith('.jpg') else 'RGBA'; f.quality = q
    im.save_render(path, scene=s); bpy.data.images.remove(im)

def render_png(s, path):
    f = s.render.image_settings; f.file_format = 'PNG'; f.color_mode = 'RGBA'; s.render.filepath = path; bpy.ops.render.render(write_still=True); return pixels(path)

def disc(h, w, cx, cy, r, feather):
    import numpy as np
    yy, xx = np.mgrid[0:h, 0:w]; return np.clip((r - np.hypot(xx - cx, yy - cy)) / feather, 0, 1).astype(np.float32)

bpy.ops.wm.read_factory_settings(use_empty=True)
machines = [m for i, m in enumerate(MACHINES) if ONLY is None or i == ONLY]

if MODE == 'plates':     # gasket and empty drum, seen when the door swings away
    s, _ = scene_setup(160); lighting()
    for name, cx, cy in machines:
        o = drum(cx, cy, R_DOOR * 1.05); r = 134; l, t = cx - r, cy - r
        s.render.use_border, s.render.use_crop_to_border = True, True
        s.render.border_min_x, s.render.border_max_x, s.render.border_max_y, s.render.border_min_y = l / IW, (l + 2 * r) / IW, 1 - t / IH, 1 - (t + 2 * r) / IH
        a = render_png(s, os.path.join(OUT, f'_plate_{name}.png'))
        a[..., :3] = a[..., :3] * .86 + (.085, .055, .045)   # the film's lifted, warm blacks
        a[..., 3] *= disc(*a.shape[:2], r, r, r - 4, 3); save(a, os.path.join(OUT, f'drum-{name}.webp'), 84)
        for ob in list(s.collection.objects):
            if ob.type == 'MESH': bpy.data.objects.remove(ob)

if MODE == 'doors':      # the swing, as one sprite sheet per machine; each cell carries the door and its shadow
    import numpy as np
    s, _ = scene_setup(96); lighting()
    for name, cx, cy in machines:
        cab = cabinet(); piv, lit = door(cx, cy, ROOM); crop(s, cx, cy); cells = []
        for k in range(1, FRAMES + 1):
            ang = MAX_ANGLE * k / FRAMES
            piv.rotation_euler = (0, -math.radians(ang), 0); lit.inputs[0].default_value = min(1, ang / 45)
            cells.append(render_png(s, os.path.join(OUT, '_cell.png')))
        h, w = cells[0].shape[:2]; cols = 5; rows = FRAMES // cols
        sheet = np.zeros((h * rows, w * cols, 4), np.float32)
        for k, c in enumerate(cells):
            y = (rows - 1 - k // cols) * h; x = (k % cols) * w; sheet[y:y + h, x:x + w] = c
        save(sheet, os.path.join(OUT, f'door-{name}.webp'), 80); print('SHEET', name, w, h)
        for ob in list(s.collection.objects):
            if ob.type in ('MESH', 'EMPTY'): bpy.data.objects.remove(ob)

if MODE == 'pearls':     # replaces the drum contents in the photo with a rendered heap
    import numpy as np
    s, _ = scene_setup(128); lighting(); name, cx, cy = MACHINES[2]
    drum(cx, cy, R_GLASS * 1.3); pile(cx, cy); _, lit = door(cx, cy, ROOM); s.render.film_transparent = False
    s.render.use_border, s.render.use_crop_to_border = True, False   # only the drum needs rendering
    s.render.border_min_x, s.render.border_max_x, s.render.border_max_y, s.render.border_min_y = (cx - 112) / IW, (cx + 112) / IW, 1 - (cy - 112) / IH, 1 - (cy + 112) / IH
    # big soft windows that only reflections can see, as in a pearl photographed by a bright window
    for k, (dx, dy, dz, sx, sy, e) in enumerate([(-.5, .55, .8, 1.1, 1.3, 60), (.55, .3, .9, .7, 1., 26), (0, 1.0, .3, 1.3, .6, 26)]):
        win = bpy.data.lights.new(f'win{k}', 'AREA'); win.shape = 'RECTANGLE'; win.size, win.size_y, win.energy, win.color = sx, sy, e, (1, .95, .9)
        wo = bpy.data.objects.new(f'win{k}', win); s.collection.objects.link(wo); wo.visible_diffuse = wo.visible_transmission = wo.visible_volume_scatter = False
        wo.location = (wx(cx) + dx, wy(cy) + dy, dz); wo.rotation_mode = 'QUATERNION'
        wo.rotation_quaternion = (Vector((wx(cx), wy(cy) - .1, -.1)) - wo.location).normalized().to_track_quat('-Z', 'Y')
    a = render_png(s, os.path.join(OUT, '_pile.png'))
    room = pixels(ROOM); H, W = room.shape[:2]
    # soften and grain it like the film stock, then lay it in behind the rim
    b = a[..., :3].copy()
    for ax in (0, 1): b = (np.roll(b, 1, ax) + 2 * b + np.roll(b, -1, ax)) / 4
    b = b * np.array([1, .9, .8], np.float32)   # the glass's amber cast
    b = b + np.random.default_rng(3).normal(0, .012, b.shape[:2])[..., None]
    m = disc(H, W, cx, H - cy, 101, 5)[..., None]   # rows run bottom-up
    room[..., :3] = room[..., :3] * (1 - m) + b * m; room[..., 3] = 1
    save(np.clip(room, 0, 1), os.path.join(OUT, 'room.jpg'), 88)

if MODE == 'wool':       # cut-outs of the wool drum's own contents, so they match the photo exactly
    import numpy as np
    room = pixels(ROOM)[::-1]; S = 2     # rows top-down, and doubled so the masks stay smooth
    def crop(cx, cy, h, sy=1):
        ys = np.linspace(cy - h * sy, cy + h * sy, 2 * h * S); xs = np.linspace(cx - h, cx + h, 2 * h * S)
        y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int); fy, fx = (ys - y0)[:, None, None], (xs - x0)[None, :, None]
        a, b, c, d = room[y0][:, x0], room[y0][:, x0 + 1], room[y0 + 1][:, x0], room[y0 + 1][:, x0 + 1]
        return a * (1 - fy) * (1 - fx) + b * (1 - fy) * fx + c * fy * (1 - fx) + d * fy * fx
    def soft(v, lo, hi): t = np.clip((v - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)
    def blur(m, n):
        for _ in range(n):
            for ax in (0, 1): m = (np.roll(m, 1, ax) + 2 * m + np.roll(m, -1, ax)) / 4
        return m
    def write(name, a, alpha):
        a = a.copy(); a[..., 3] = alpha; save(np.ascontiguousarray(a[::-1]), os.path.join(OUT, name), 88)
    def grid(h):
        c = (np.arange(2 * h * S) + .5) / S - h; return np.meshgrid(c, c)
    # the heap: everything lighter than the dark drum, below the glass reflections and inside the rim
    h = 108; a = crop(719, 548, h); x, y = grid(h); lum = a[..., :3].max(2)
    m = soft(blur(soft(lum, .38, .48), 18), .2, .45) * soft(y, -32, -24) * (1 - soft(np.hypot(x, y), 100, 104)) * soft(np.hypot(x + 108, y - 8), 16, 22)
    write('wool-heap.webp', a, m)
    # two balls, stretched to true circles and trimmed inside their edges, and irregular lumps of knit
    for name, cx, cy, rx, ry in (('wool-ball-cream.webp', 686, 626, 35, 31), ('wool-ball-red.webp', 769, 621.7, 31.7, 31.7)):
        h = 38; a = crop(cx, cy, h, ry / rx); x, y = grid(h); write(name, a, 1 - soft(np.hypot(x, y) / rx, .9, .95))
    for name, cx, cy, rx, ry, ph in (('wool-knit-1.webp', 695, 567, 42, 25, 1.), ('wool-knit-2.webp', 748, 577, 36, 17, 3.)):
        h = 50; a = crop(cx, cy, h); x, y = grid(h); q = np.arctan2(y, x)
        edge = 1 + .13 * np.sin(q * 3 + ph) + .08 * np.sin(q * 5 + ph * 2) + .04 * np.sin(q * 11)
        write(name, a, 1 - soft(np.hypot(x / rx, y / ry) / edge, .92, 1.))
