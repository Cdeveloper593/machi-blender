#!/usr/bin/env python3
"""MACHI (Blender edition) — a clay-diorama Japanese town on a floating island,
one continuous camera flight from morning to lantern-lit night.

Build:  blender -b -P build_town.py        (saves machi.blend next to this file)
The timeline (24 fps, frames 0..2112) is split into 11 segments of 192 frames
with SHARED boundary frames, so the scroll-world seams are exact by
construction: dive1 0-192, conn1 192-384, dive2 384-576, conn2 576-768,
dive3 768-960, conn3 960-1152, dive4 1152-1344, conn4 1344-1536,
dive5 1536-1728, conn5 1728-1920, dive6 1920-2112.
"""
import bpy
import math
import os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- reset ----
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ------------------------------------------------------------ materials ----
def mat(name, color, rough=0.85, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return m

GRASS   = mat("grass",   (0.34, 0.60, 0.25))
GRASS2  = mat("grass2",  (0.28, 0.53, 0.22))
EARTH   = mat("earth",   (0.55, 0.40, 0.27))
EARTH2  = mat("earth2",  (0.65, 0.50, 0.36))
ROCK    = mat("rock",    (0.45, 0.42, 0.40))
STONE   = mat("stone",   (0.62, 0.60, 0.57), 0.95)
STONE_D = mat("stone_d", (0.48, 0.47, 0.45), 0.95)
PLASTER = mat("plaster", (0.93, 0.87, 0.74))
PLASTER2= mat("plaster2",(0.88, 0.78, 0.62))
WOOD    = mat("wood",    (0.55, 0.36, 0.22), 0.8)
WOOD_D  = mat("wood_d",  (0.40, 0.26, 0.16), 0.8)
ROOF_NV = mat("roof_navy",(0.20, 0.24, 0.30), 0.7)
ROOF_TR = mat("roof_terra",(0.72, 0.38, 0.24), 0.75)
ROOF_GN = mat("roof_green",(0.25, 0.38, 0.30), 0.7)
VERMIL  = mat("vermilion",(0.76, 0.20, 0.12), 0.6)
WATER   = mat("water",   (0.28, 0.54, 0.68), 0.25)
PINK    = mat("pink",    (0.96, 0.62, 0.71))
PINK2   = mat("pink2",   (0.92, 0.60, 0.68))
PINE    = mat("pine",    (0.20, 0.38, 0.22))
WILLOW  = mat("willow",  (0.45, 0.62, 0.32))
TRUNK   = mat("trunk",   (0.42, 0.30, 0.20), 0.95)
CREAM   = mat("cream",   (0.96, 0.92, 0.82))
INDIGO  = mat("indigo",  (0.16, 0.20, 0.38))
RED     = mat("red",     (0.78, 0.25, 0.18), 0.65)
TEAL    = mat("teal",    (0.20, 0.45, 0.48), 0.7)
GOLD    = mat("gold",    (0.85, 0.62, 0.25), 0.6)
FOX     = mat("fox",     (0.90, 0.52, 0.22), 0.9)
WHITE   = mat("white",   (0.97, 0.96, 0.93))
# emissive family (strength animated over the day)
PAPER   = mat("paper_lantern", (0.98, 0.85, 0.62), 0.6, emit=(1.0, 0.72, 0.38), emit_strength=0.25)
GLOW    = mat("stone_glow",    (0.98, 0.82, 0.55), 0.6, emit=(1.0, 0.70, 0.34), emit_strength=0.15)
WINDOW  = mat("window",        (0.55, 0.48, 0.38), 0.4, emit=(1.0, 0.76, 0.42), emit_strength=0.0)
GIANT   = mat("giant_lantern", (0.99, 0.87, 0.66), 0.55, emit=(1.0, 0.74, 0.40), emit_strength=0.3)
GIANT_R = mat("giant_rib",     (0.72, 0.22, 0.14), 0.6)

# -------------------------------------------------------------- helpers ----
def link(obj, material=None):
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj

def box(name, loc, scale, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (scale[0] / 2, scale[1] / 2, scale[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    o.dimensions = scale
    if material:
        o.data.materials.append(material)
    return o

def cyl(name, loc, radius, depth, material, vertices=20, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if material:
        o.data.materials.append(material)
    return o

def cone(name, loc, r1, r2, depth, material, vertices=20, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=depth,
                                    location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if material:
        o.data.materials.append(material)
    return o

def ball(name, loc, radius, material, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    if material:
        o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth = True
    return o

def prism(name, loc, w, d, h, material, rot=(0, 0, 0)):
    """Gable roof: ridge along local X, origin at base centre."""
    hw, hd = w / 2, d / 2
    verts = [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
             (-hw, 0, h), (hw, 0, h)]
    faces = [(0, 1, 5, 4), (3, 2, 1, 0), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    o.location = loc
    o.rotation_euler = rot
    link(o, material)
    return o

# --------------------------------------------------------------- island ----
cyl("island_side", (0, 0, -2.95), 30, 5.2, EARTH, vertices=56)
cyl("island_strata", (0, 0, -5.6), 27.5, 1.4, EARTH2, vertices=56)
cone("island_rock", (0, 0, -9.6), 25, 4, 7.0, ROCK, vertices=56)
cyl("grass_top", (0, 0, -0.25), 29.7, 0.5, GRASS, vertices=56)
# shrine hill (truncated cone, flat top) NW
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=10.5, depth=4.8, location=(-14, 12, 2.15))
hill = bpy.context.object
hill.name = "hill"
# taper: scale top via vertex edit is overkill — use a cone instead
bpy.data.objects.remove(hill, do_unlink=True)
cone("hill", (-14, 12, 2.15), 10.5, 5.6, 4.8, GRASS2, vertices=40)

def path(name, loc, size, rotz=0.0):
    return box(name, loc, (size[0], size[1], 0.1), STONE, rot=(0, 0, rotz))

path("street", (1, -2, 0.03), (30, 5.4))
path("canal_walk_s", (0, -10.6, 0.03), (33, 1.6))
path("canal_walk_n", (0, -15.6, 0.03), (33, 1.6))
path("shrine_path", (-14, 2.5, 0.05), (3.2, 12))
path("market_lane", (17, 2, 0.03), (4.6, 20))
path("torii_path", (2, -6.5, 0.04), (3.0, 7))
cyl("plaza", (-20, -4, 0.02), 6.4, 0.12, STONE, vertices=36)

# ---------------------------------------------------------------- canal ----
box("canal_bed", (0, -13.1, -0.10), (33, 4.6, 0.24), STONE_D)
box("canal_water", (0, -13.1, 0.08), (33, 3.8, 0.10), WATER)
box("canal_bank_s", (0, -15.35, 0.10), (33, 0.7, 0.70), STONE)
box("canal_bank_n", (0, -10.85, 0.10), (33, 0.7, 0.70), STONE)
# stepped stone bridge at x=2
for i, (dy, dz) in enumerate([(-2.2, 0.25), (-1.5, 0.62), (-0.75, 0.92), (0, 1.05),
                              (0.75, 0.92), (1.5, 0.62), (2.2, 0.25)]):
    box(f"bridge_{i}", (2, -13.1 + dy, dz / 2), (2.6, 0.85, dz + 0.3), STONE)
for sx in (0.85, 3.15):
    box(f"bridge_rail_{sx}", (sx, -13.1, 1.35), (0.18, 4.6, 0.16), STONE_D)

# --------------------------------------------------------------- torii -----
def torii(name, loc, s=1.0, rotz=0.0):
    x, y, z = loc
    for dx in (-1.5, 1.5):
        cyl(f"{name}_leg", (x + dx * s, y, z + 1.9 * s), 0.16 * s, 3.8 * s, VERMIL, vertices=12)
    box(f"{name}_top", (x, y, z + 4.05 * s), (4.6 * s, 0.34 * s, 0.42 * s), VERMIL)
    box(f"{name}_mid", (x, y, z + 3.1 * s), (3.6 * s, 0.24 * s, 0.3 * s), VERMIL)
    for o in bpy.context.scene.objects:
        if o.name.startswith(name):
            o.rotation_euler.z = rotz

torii("torii_main", (2, -9.2, 0), 1.15)
torii("torii_shrine", (-14, 6.2, 4.3), 0.8)

# -------------------------------------------------------------- buildings --
def house(name, loc, w, d, hb, roof_mat, body_mat=PLASTER, face=-1, shop=False):
    """face=-1: front (door/windows/awning) on the -Y side; face=+1: on +Y."""
    x, y, z = loc
    fy = y + face * (d / 2)          # front wall plane
    box(name + "_body", (x, y, z + hb / 2), (w, d, hb), body_mat)
    prism(name + "_roof", (x, y, z + hb), w + 0.7, d + 0.8, hb * 0.62, roof_mat)
    box(name + "_door", (x, fy + face * 0.03, z + 0.75), (0.95, 0.08, 1.5), WOOD_D)
    for wx in (-w / 4, w / 4):
        box(name + f"_win{wx}", (x + wx, fy + face * 0.04, z + hb * 0.58),
            (0.85, 0.06, 0.8), WINDOW)
    if shop:
        box(name + "_awning", (x, fy + face * 0.55, z + hb - 0.55),
            (w * 0.92, 1.15, 0.08), RED, rot=(face * 0.5, 0, 0))
        box(name + "_sign", (x + w / 4, fy + face * 0.18, z + hb + 0.15),
            (0.5, 0.1, 1.1), CREAM)
        box(name + "_noren", (x, fy + face * 0.1, z + 1.55),
            (1.1, 0.05, 0.55), INDIGO)

# shotengai — shops lining the street (street runs along X at y=-2)
shop_specs = [
    (-9.5, -6.2, 4.6, ROOF_NV), (-4.6, -6.2, 4.2, ROOF_TR), (0.2, -6.2, 4.8, ROOF_NV),
    (5.2, -6.2, 4.3, ROOF_GN), (10.0, -6.2, 4.6, ROOF_TR),
]
for i, (x, y, w, rm) in enumerate(shop_specs):
    house(f"shop_s{i}", (x, y, 0), w, 3.6, 2.6, rm, PLASTER if i % 2 else PLASTER2, face=1, shop=True)
north_specs = [
    (-8.0, 2.3, 4.4, ROOF_TR), (-3.2, 2.3, 4.0, ROOF_NV), (2.2, 2.3, 4.7, ROOF_GN),
    (7.2, 2.3, 4.2, ROOF_NV), (11.8, 2.3, 4.4, ROOF_TR),
]
for i, (x, y, w, rm) in enumerate(north_specs):
    house(f"shop_n{i}", (x, y, 0), w, 3.6, 2.6, rm, PLASTER2 if i % 2 else PLASTER,
          face=-1, shop=True)  # front on the street (south) side

# homes NE + scattered
house("home1", (10, 10, 0), 4.4, 4.0, 2.7, ROOF_NV)
house("home2", (9.5, 16.5, 0), 4.0, 3.8, 2.5, ROOF_TR)
house("home3", (4, 13.5, 0), 4.6, 4.0, 2.8, ROOF_GN)
house("home4", (-4, 9, 0), 3.8, 3.6, 2.4, ROOF_NV)
house("home5", (-22, 6, 0), 4.2, 3.8, 2.6, ROOF_TR)
house("home6", (-24, -12, 0), 4.0, 3.6, 2.5, ROOF_NV)
house("home7", (20, -14.5, 0), 4.2, 3.8, 2.6, ROOF_GN)
house("bakery_annex", (-13.5, -6.4, 0), 3.4, 3.2, 2.3, ROOF_TR, PLASTER2, face=1, shop=True)

# ---------------------------------------------------------------- shrine ---
SX, SY, SZ = -14, 12.6, 4.55  # shrine terrace height (hill top)
box("shrine_terrace", (SX, SY, SZ - 0.25), (10, 7.5, 0.5), STONE)
box("shrine_base", (SX, SY + 0.6, SZ + 0.3), (6.4, 4.6, 0.6), STONE_D)
for dx in (-2.6, -0.9, 0.9, 2.6):
    cyl(f"shrine_col{dx}", (SX + dx, SY - 0.9, SZ + 1.9), 0.17, 2.6, VERMIL, vertices=10)
box("shrine_hall", (SX, SY + 1.1, SZ + 1.5), (6.2, 2.6, 2.1), PLASTER)
prism("shrine_roof", (SX, SY + 0.6, SZ + 2.55), 8.2, 5.6, 2.2, ROOF_NV)
box("shrine_offer", (SX, SY - 0.9, SZ + 0.75), (1.3, 0.6, 0.7), WOOD_D)
box("shrine_window", (SX, SY - 0.25, SZ + 1.6), (1.6, 0.08, 0.95), WINDOW)
box("shrine_window_l", (SX - 2.1, SY - 0.25, SZ + 1.6), (0.75, 0.08, 0.95), WINDOW)
box("shrine_window_r", (SX + 2.1, SY - 0.25, SZ + 1.6), (0.75, 0.08, 0.95), WINDOW)
# stone steps down the south slope of the hill
for i in range(9):
    t = i / 8
    box(f"step_{i}", (SX, 7.6 - i * 0.85, 4.35 - i * 0.52), (3.4, 0.95, 0.35), STONE)

# ---------------------------------------------------------- stone lanterns -
def stone_lantern(name, loc):
    x, y, z = loc
    box(name + "_base", (x, y, z + 0.12), (0.55, 0.55, 0.24), STONE_D)
    cyl(name + "_post", (x, y, z + 0.55), 0.09, 0.65, STONE, vertices=8)
    box(name + "_fire", (x, y, z + 1.0), (0.44, 0.44, 0.34), GLOW)
    cone(name + "_roof", (x, y, z + 1.32), 0.48, 0.02, 0.3, STONE_D, vertices=4)
    ball(name + "_jewel", (x, y, z + 1.55), 0.09, STONE_D)

for i, (x, y, z) in enumerate([(-15.8, 5.4, 3.3), (-12.2, 5.4, 3.3), (-15.8, 0.4, 0.05),
                               (-12.2, 0.4, 0.05), (-4, -10.2, 0), (8, -10.2, 0),
                               (-4, -16.0, 0), (8, -16.0, 0), (15.2, -6, 0), (18.8, 10, 0)]):
    stone_lantern(f"slantern_{i}", (x, y, z))

# paper lanterns on poles along the street + canal
def paper_lantern(name, loc, r=0.21):
    ball(name, loc, r, PAPER, scale=(1, 1, 1.2))
    cyl(name + "_cap", (loc[0], loc[1], loc[2] + r * 1.25), r * 0.45, 0.07, WOOD_D, vertices=10)

for i, x in enumerate(range(-11, 13, 4)):
    cyl(f"pole_s{i}", (x, -4.9, 1.5), 0.05, 3.0, WOOD_D, vertices=8)
    paper_lantern(f"plantern_s{i}", (x, -4.9, 3.15))
    cyl(f"pole_n{i}", (x + 2, 1.0, 1.5), 0.05, 3.0, WOOD_D, vertices=8)
    paper_lantern(f"plantern_n{i}", (x + 2, 1.0, 3.15))

paper_lantern("shrine_lamp_l", (SX - 2.6, SY - 1.6, SZ + 2.2), 0.24)
paper_lantern("shrine_lamp_r", (SX + 2.6, SY - 1.6, SZ + 2.2), 0.24)

# ----------------------------------------------------------------- trees ---
def cherry(name, loc, s=1.0):
    x, y, z = loc
    cyl(name + "_trunk", (x, y, z + 0.9 * s), 0.14 * s, 1.8 * s, TRUNK, vertices=8)
    ball(name + "_a", (x, y, z + 2.3 * s), 1.15 * s, PINK)
    ball(name + "_b", (x + 0.8 * s, y + 0.3 * s, z + 1.9 * s), 0.85 * s, PINK2)
    ball(name + "_c", (x - 0.75 * s, y - 0.25 * s, z + 2.0 * s), 0.8 * s, PINK)

def pine(name, loc, s=1.0):
    x, y, z = loc
    cyl(name + "_trunk", (x, y, z + 0.8 * s), 0.12 * s, 1.6 * s, TRUNK, vertices=8)
    for i, (r, dz) in enumerate([(1.25, 1.9), (0.95, 2.7), (0.6, 3.45)]):
        cone(f"{name}_c{i}", (x, y, z + dz * s), r * s, 0.05, 1.5 * s, PINE, vertices=10)

def willow(name, loc, s=1.0):
    x, y, z = loc
    cyl(name + "_trunk", (x, y, z + 1.0 * s), 0.17 * s, 2.0 * s, TRUNK, vertices=8)
    for i, (dx, dy, rz) in enumerate([(0, 0, 0), (0.85, 0.2, 0.5), (-0.85, -0.15, -0.5), (0.1, 0.8, 0.2)]):
        b = ball(f"{name}_w{i}", (x + dx * s, y + dy * s, z + 2.0 * s), 0.95 * s, WILLOW,
                 scale=(0.75, 0.75, 1.5))
        b.rotation_euler.z = rz

cherry("cherry1", (6.5, -8.6, 0), 1.1)
cherry("cherry2", (-7.5, -8.8, 0), 0.95)
cherry("cherry3", (-23, 18, 0), 1.2)
cherry("cherry4", (13, 5.5, 0), 0.9)
cherry("cherry5", (-5.5, 19.5, 0), 1.0)
pine("pine1", (-24, 14, 0), 1.25)
pine("pine2", (22, 6, 0), 1.1)
pine("pine3", (-4, -18.5, 0), 1.0)
pine("pine4", (24, -8, 0), 1.2)
pine("pine5", (-25, -2, 0), 1.05)
willow("willow1", (-8, -11.6, 0), 1.1)
willow("willow2", (11, -14.8, 0), 1.0)
willow("willow3", (-13, -14.6, 0), 0.9)

# ------------------------------------------------------------ night market -
def stall(name, loc, canopy_mat, rotz=0.0):
    x, y, z = loc
    box(name + "_counter", (x, y, z + 0.55), (2.6, 1.1, 1.1), WOOD)
    for dx in (-1.2, 1.2):
        for dy in (-0.45, 0.45):
            cyl(f"{name}_pole{dx}{dy}", (x + dx, y + dy, z + 1.5), 0.05, 3.0, WOOD_D, vertices=6)
    box(name + "_canopy", (x, y, z + 3.05), (3.1, 1.7, 0.09), canopy_mat, rot=(0.16, 0, 0))
    box(name + "_canopy2", (x, y, z + 3.12), (3.1, 0.55, 0.1), CREAM, rot=(0.16, 0, 0))
    # goods on the counter
    for i, gm in enumerate((RED, GOLD, TEAL, PINK2)):
        ball(f"{name}_good{i}", (x - 0.9 + i * 0.6, y, z + 1.25), 0.17, gm)
    paper_lantern(name + "_lamp", (x, y + 0.8, z + 2.6), 0.19)

stall("stall_w1", (14.3, -4, 0), RED)
stall("stall_w2", (14.3, 0.5, 0), TEAL)
stall("stall_w3", (14.3, 5, 0), GOLD)
stall("stall_w4", (14.3, 9.5, 0), RED)
for i, (y, cm) in enumerate([( -1.8, GOLD), (2.7, RED), (7.2, TEAL)]):
    g_stall = stall(f"stall_e{i}", (19.7, y, 0), cm)
# lantern strings across the alley
for sx in (-3.5, 1.0, 5.5):
    for k in range(7):
        t = k / 6
        lx = 14.9 + t * 4.2
        lz = 3.6 - math.sin(t * math.pi) * 0.45
        paper_lantern(f"string_{sx}_{k}", (lx, sx + 2, lz), 0.16)
# the fox shopkeeper (a nod to the AI version's kitsune)
FX, FY = 15.6, 0.5
cone("fox_body", (FX, FY, 0.55), 0.34, 0.12, 1.1, FOX, vertices=12)
ball("fox_head", (FX, FY, 1.35), 0.30, FOX)
cone("fox_ear_l", (FX - 0.16, FY, 1.68), 0.10, 0.01, 0.28, FOX, vertices=6)
cone("fox_ear_r", (FX + 0.16, FY, 1.68), 0.10, 0.01, 0.28, FOX, vertices=6)
cone("fox_tail", (FX - 0.45, FY - 0.3, 0.5), 0.16, 0.05, 0.9, WHITE, vertices=8, rot=(0.7, 0, 0.5))
ball("fox_snout", (FX, FY - 0.26, 1.28), 0.13, WHITE)

# ------------------------------------------------------------ giant lantern -
GX, GY = -20.5, -4
cyl("lantern_stage", (GX, GY, 0.25), 3.9, 0.5, WOOD, vertices=28)
for dx in (-3.1, 3.1):
    for dy in (-3.1, 3.1):
        cyl(f"yagura_{dx}{dy}", (GX + dx, GY + dy, 3.1), 0.14, 5.7, WOOD_D, vertices=8)
box("yagura_top", (GX, GY, 6.1), (7.0, 7.0, 0.35), WOOD_D)
box("yagura_beam", (GX, GY, 5.6), (7.0, 0.3, 0.3), WOOD_D)
lantern = ball("giant_lantern", (GX, GY, 3.35), 2.55, GIANT, scale=(1, 1, 1.12))
for i, dz in enumerate((-1.9, -0.95, 0.0, 0.95, 1.9)):
    r = 2.55 * math.sqrt(max(0.05, 1 - (dz / 2.86) ** 2))
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.055, major_segments=36,
                                     minor_segments=8, location=(GX, GY, 3.35 + dz))
    rib = bpy.context.object
    rib.name = f"giant_rib_{i}"
    rib.data.materials.append(GIANT_R)
cyl("giant_cap_t", (GX, GY, 6.28), 0.55, 0.3, WOOD_D, vertices=14)
cyl("giant_cap_b", (GX, GY, 0.62), 0.55, 0.3, WOOD_D, vertices=14)
# festival drums + crates near the plaza
cyl("drum", (-16.2, -8.6, 0.65), 0.62, 1.3, RED, vertices=16, rot=(math.pi / 2, 0, 0))
box("crate1", (-16.8, 0.8, 0.4), (0.8, 0.8, 0.8), WOOD)
box("crate2", (-16.0, 0.9, 0.35), (0.7, 0.7, 0.7), WOOD_D)
box("barrel1", (12.6, -5.6, 0.45), (0.85, 0.85, 0.9), WOOD)
cyl("barrel2", (13.4, -5.4, 0.45), 0.42, 0.9, WOOD_D, vertices=14)

# ------------------------------------------------------- camera + target ---
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 38
cam_data.clip_end = 1200
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
scene.camera = cam
target = bpy.data.objects.new("CamTarget", None)
bpy.context.collection.objects.link(target)
track = cam.constraints.new(type="TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"

# (frame, cam pos, target pos) — boundaries shared between segments
WAYPOINTS = [
    (0,    (46, -52, 34),   (0, -1, 0)),      # arrival: high wide over the island
    (192,  (11, -17, 7.5),  (-2, -3, 1.5)),   # dive1 ends over the torii path
    (384,  (-11.5, -2, 2.3), (8, -2, 1.6)),   # street level, west end of shotengai
    (672,  (2, -6.5, 6.5),   (-8, -12, 0.5)),  # conn2 mid: arc over the rooftops
    (576,  (13.5, -2, 2.1), (24, -4, 1.2)),   # east end of the street
    (768,  (-16, -13.5, 5.5), (4, -13, 0)),   # above the canal, west end
    (960,  (15, -13.2, 2.4), (22, -11, 1)),   # low over the canal, east end
    (1056, (0, -6, 9.5),     (-10, 4, 4.5)),   # conn3 mid: high arc across town
    (1152, (-14, -3.5, 2.6), (-14, 10, 6.0)),  # shrine steps base
    (1344, (-14, 5.2, 5.4), (-14, 12.6, 6.6)),  # through the torii, face-on to the shrine
    (1440, (1, -2, 7.5),     (10, -4, 1.5)),   # conn4 mid: high over the street
    (1536, (17, -8.5, 3.2), (17, 1, 1.4)),    # night market, south mouth
    (1728, (17, 9.5, 2.4), (17, 16, 1.2)),    # deep in the market
    (1824, (2, 4, 8.5),      (-12, -2, 3.0)),  # conn5 mid: aerial arc west
    (1920, (-12.5, -5, 5.5), (-20.5, -4, 3.2)),  # lantern plaza approach
    (2112, (-13.8, -4.3, 3.5), (-20.5, -4, 3.4)),# lantern fills the frame, glowing
]
for f, cp, tp in WAYPOINTS:
    cam.location = cp
    cam.keyframe_insert(data_path="location", frame=f)
    target.location = tp
    target.keyframe_insert(data_path="location", frame=f)

# ------------------------------------------------------------- lighting ----
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.0
sun_data.angle = 0.12
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)

# (frame, energy, color, rotation_euler)
SUN_KEYS = [
    (0,    3.6,  (1.0, 0.88, 0.72), (0.95, 0.10, -1.00)),   # morning, warm east
    (384,  4.0,  (1.0, 0.98, 0.94), (0.50, 0.00, -0.35)),   # late morning, high
    (768,  3.2,  (1.0, 0.72, 0.45), (1.15, 0.10,  0.70)),   # golden afternoon
    (1152, 1.40, (1.0, 0.50, 0.32), (1.35, 0.15,  0.95)),   # dusk, embers
    (1536, 0.30, (0.45, 0.55, 0.90), (0.70, -0.30, 2.60)),  # night, moonlight
    (2112, 0.30, (0.45, 0.55, 0.90), (0.70, -0.30, 2.60)),
]
for f, e, c, r in SUN_KEYS:
    sun_data.energy = e
    sun_data.keyframe_insert(data_path="energy", frame=f)
    sun_data.color = c
    sun_data.keyframe_insert(data_path="color", frame=f)
    sun.rotation_euler = r
    sun.keyframe_insert(data_path="rotation_euler", frame=f)

hemi_data = bpy.data.lights.new("Fill", type="SUN")
hemi_data.energy = 0.5
hemi_data.use_shadow = False
hemi_data.angle = 1.2
hemi = bpy.data.objects.new("Fill", hemi_data)
hemi.rotation_euler = (0.4, 0.3, 2.8)
bpy.context.collection.objects.link(hemi)
for f, e in [(0, 0.3), (1152, 0.2), (1536, 0.08), (2112, 0.08)]:
    hemi_data.energy = e
    hemi_data.keyframe_insert(data_path="energy", frame=f)

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
BG_KEYS = [
    (0,    (0.95, 0.92, 0.84), 0.30),
    (384,  (0.96, 0.93, 0.85), 0.32),
    (768,  (0.97, 0.85, 0.68), 0.30),
    (1152, (0.50, 0.40, 0.52), 0.22),
    (1536, (0.05, 0.06, 0.13), 0.14),
    (2112, (0.04, 0.05, 0.12), 0.14),
]
for f, c, st in BG_KEYS:
    bg.inputs[0].default_value = (*c, 1.0)
    bg.inputs[0].keyframe_insert(data_path="default_value", frame=f)
    bg.inputs[1].default_value = st
    bg.inputs[1].keyframe_insert(data_path="default_value", frame=f)

# backdrop: giant inside-out sphere, pure emission = the studio backdrop colour
BACKDROP = mat("backdrop", (0.95, 0.92, 0.84), 1.0, emit=(0.95, 0.92, 0.84), emit_strength=1.1)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=300, location=(0, 0, 0))
bd = bpy.context.object
bd.name = "backdrop"
bd.data.materials.append(BACKDROP)
for _p in bd.data.polygons:
    _p.use_smooth = True
bd.data.materials[0].use_backface_culling = False
for _attr, _val in (("visible_shadow", False), ("visible_diffuse", False),
                    ("visible_glossy", False), ("visible_transmission", False)):
    try:
        setattr(bd, _attr, _val)
    except Exception:
        pass
_bd_bsdf = BACKDROP.node_tree.nodes["Principled BSDF"]
for f, c, st in BG_KEYS:
    _bd_bsdf.inputs["Emission Color"].default_value = (*c, 1.0)
    _bd_bsdf.inputs["Emission Color"].keyframe_insert(data_path="default_value", frame=f)
    _bd_bsdf.inputs["Emission Strength"].default_value = 1.1 if f < 1500 else 1.0
    _bd_bsdf.inputs["Emission Strength"].keyframe_insert(data_path="default_value", frame=f)

def emit_keys(material, keys):
    bsdf = material.node_tree.nodes["Principled BSDF"]
    inp = bsdf.inputs["Emission Strength"]
    for f, v in keys:
        inp.default_value = v
        inp.keyframe_insert(data_path="default_value", frame=f)

emit_keys(PAPER,  [(0, 0.25), (768, 0.35), (1152, 1.5), (1536, 2.3), (2112, 2.3)])
emit_keys(GLOW,   [(0, 0.15), (1152, 1.7), (1536, 2.5), (2112, 2.5)])
emit_keys(WINDOW, [(0, 0.0), (960, 0.05), (1152, 0.7), (1536, 1.9), (2112, 1.9)])
emit_keys(GIANT,  [(0, 0.3), (1152, 1.3), (1536, 2.5), (2112, 2.9)])


# ------------------------------------------------- join static geometry ----
# Everything except camera/lights/target is static: join per material so the
# software rasteriser gets ~25 draw calls instead of ~480.
_by_mat = {}
for o in list(bpy.data.objects):
    if o.type == "MESH" and o.data.materials:
        _by_mat.setdefault(o.data.materials[0].name, []).append(o)
for _mname, _objs in _by_mat.items():
    if len(_objs) < 2:
        continue
    bpy.ops.object.select_all(action="DESELECT")
    for _o in _objs:
        _o.select_set(True)
    bpy.context.view_layer.objects.active = _objs[0]
    bpy.ops.object.join()
    bpy.context.view_layer.objects.active.name = "joined_" + _mname
print("joined into", len(bpy.data.objects), "objects")

# -------------------------------------------------------------- render -----
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 1
# llvmpipe tuning: screen-space GI/raytracing off, cheaper shadow marching
scene.eevee.use_fast_gi = False
scene.eevee.use_raytracing = False
scene.eevee.shadow_step_count = 3
scene.eevee.shadow_resolution_scale = 0.5
try:
    scene.eevee.use_shadows = True
except Exception:
    pass
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_start = 0
scene.frame_end = 2112
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(HERE, "renders", "frame_")
scene.view_settings.view_transform = "AgX"
for _look in ("Medium High Contrast", "Medium Contrast"):
    try:
        scene.view_settings.look = _look
        break
    except Exception:
        pass

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "machi.blend"))
print("BUILT machi.blend — objects:", len(bpy.data.objects))
