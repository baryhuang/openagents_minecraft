#!/usr/bin/env python3
"""
Build a massive mansion village with sakura (cherry blossom) trees.
Uses RCON for instant construction visible in the client UI.
"""

import socket
import struct
import time
import random

RCON_HOST = "localhost"
RCON_PORT = 25575
RCON_PASS = "claude123"


class RCON:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((RCON_HOST, RCON_PORT))
        self._send(1, 3, RCON_PASS)
        self._recv()

    def cmd(self, command):
        self._send(2, 2, command)
        return self._recv()

    def _send(self, rid, pt, p):
        d = struct.pack('<ii', rid, pt) + p.encode() + b'\x00\x00'
        self.sock.send(struct.pack('<i', len(d)) + d)

    def _recv(self):
        size = struct.unpack('<i', self.sock.recv(4))[0]
        data = b""
        while len(data) < size:
            data += self.sock.recv(size - len(data))
        return data[8:-2].decode()

    def close(self):
        self.sock.close()


def fill(r, x1, y1, z1, x2, y2, z2, block, mode=""):
    cmd = f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block}"
    if mode:
        cmd += f" {mode}"
    return r.cmd(cmd)


def setblock(r, x, y, z, block):
    return r.cmd(f"setblock {x} {y} {z} {block}")


# ============================================================
# SAKURA TREE
# ============================================================
def build_sakura_tree(r, x, y, z, size="medium"):
    """Build a cherry blossom tree."""
    trunk_h = {"small": 4, "medium": 6, "large": 8}[size]
    canopy_r = {"small": 3, "medium": 4, "large": 5}[size]

    # Trunk
    fill(r, x, y, z, x, y + trunk_h, z, "cherry_log")

    # Branch out at top
    for dx, dz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        bx, bz = x + dx * 2, z + dz * 2
        setblock(r, x + dx, y + trunk_h - 1, z + dz, "cherry_log")
        setblock(r, bx, y + trunk_h, bz, "cherry_log")

    # Canopy - cherry leaves (pink!)
    top = y + trunk_h
    for dy in range(-1, 3):
        cr = canopy_r - abs(dy)
        if cr <= 0:
            continue
        for dx in range(-cr, cr + 1):
            for dz in range(-cr, cr + 1):
                dist = abs(dx) + abs(dz)
                if dist <= cr + 1 and random.random() > 0.15:
                    lx, ly, lz = x + dx, top + dy, z + dz
                    fill(r, lx, ly, lz, lx, ly, lz,
                         "cherry_leaves[persistent=true]", "replace air")

    # Hanging petals (pink particles effect via extra leaves below)
    for _ in range(6):
        dx = random.randint(-canopy_r, canopy_r)
        dz = random.randint(-canopy_r, canopy_r)
        for dy in range(-3, -1):
            if random.random() > 0.5:
                setblock(r, x + dx, top + dy, z + dz,
                         "cherry_leaves[persistent=true]")


# ============================================================
# JAPANESE MANSION
# ============================================================
def build_mansion(r, ox, oy, oz, label="Main Mansion"):
    """Build a large Japanese-style mansion. 25x15 footprint."""
    print(f"  Building {label}...")
    W, D = 25, 15

    # Foundation - dark stone
    fill(r, ox, oy - 1, oz, ox + W, oy - 1, oz + D, "deepslate_bricks")
    fill(r, ox - 1, oy - 1, oz - 1, ox + W + 1, oy - 2, oz + D + 1, "deepslate_tiles")

    # Raised floor - dark oak
    fill(r, ox, oy, oz, ox + W, oy, oz + D, "dark_oak_planks")

    # Walls - spruce + white (Japanese paper wall style)
    # Outer walls
    fill(r, ox, oy + 1, oz, ox + W, oy + 5, oz, "spruce_planks")
    fill(r, ox, oy + 1, oz + D, ox + W, oy + 5, oz + D, "spruce_planks")
    fill(r, ox, oy + 1, oz, ox, oy + 5, oz + D, "spruce_planks")
    fill(r, ox + W, oy + 1, oz, ox + W, oy + 5, oz + D, "spruce_planks")

    # Interior hollow
    fill(r, ox + 1, oy + 1, oz + 1, ox + W - 1, oy + 4, oz + D - 1, "air")

    # White paper wall panels (quartz for white)
    fill(r, ox + 1, oy + 2, oz, ox + W - 1, oy + 4, oz, "white_stained_glass_pane")
    fill(r, ox + 1, oy + 2, oz + D, ox + W - 1, oy + 4, oz + D, "white_stained_glass_pane")
    fill(r, ox, oy + 2, oz + 1, ox, oy + 4, oz + D - 1, "white_stained_glass_pane")
    fill(r, ox + W, oy + 2, oz + 1, ox + W, oy + 4, oz + D - 1, "white_stained_glass_pane")

    # Spruce frame strips (horizontal beams)
    fill(r, ox, oy + 1, oz, ox + W, oy + 1, oz, "spruce_planks")
    fill(r, ox, oy + 5, oz, ox + W, oy + 5, oz, "spruce_planks")
    fill(r, ox, oy + 1, oz + D, ox + W, oy + 1, oz + D, "spruce_planks")
    fill(r, ox, oy + 5, oz + D, ox + W, oy + 5, oz + D, "spruce_planks")

    # Corner pillars (dark oak logs)
    for cx, cz in [(ox, oz), (ox + W, oz), (ox, oz + D), (ox + W, oz + D)]:
        fill(r, cx, oy + 1, cz, cx, oy + 5, cz, "dark_oak_log")

    # Mid pillars
    for cx in [ox + 6, ox + 12, ox + 18]:
        fill(r, cx, oy + 1, oz, cx, oy + 5, oz, "dark_oak_log")
        fill(r, cx, oy + 1, oz + D, cx, oy + 5, oz + D, "dark_oak_log")

    # Interior divider walls (rooms)
    fill(r, ox + 9, oy + 1, oz + 1, ox + 9, oy + 4, oz + D - 1, "spruce_planks")
    fill(r, ox + 9, oy + 2, oz + 1, ox + 9, oy + 4, oz + D - 1, "white_stained_glass_pane")
    fill(r, ox + 9, oy + 1, oz + 5, ox + 9, oy + 2, oz + 6, "air")  # sliding door

    fill(r, ox + 17, oy + 1, oz + 1, ox + 17, oy + 4, oz + D - 1, "spruce_planks")
    fill(r, ox + 17, oy + 2, oz + 1, ox + 17, oy + 4, oz + D - 1, "white_stained_glass_pane")
    fill(r, ox + 17, oy + 1, oz + 5, ox + 17, oy + 2, oz + 6, "air")

    # Front doors
    fill(r, ox + 12, oy + 1, oz, ox + 13, oy + 3, oz, "air")

    # === ROOF - pagoda style (dark oak stairs) ===
    # Ceiling
    fill(r, ox, oy + 6, oz, ox + W, oy + 6, oz + D, "dark_oak_planks")

    # Pagoda overhang
    fill(r, ox - 2, oy + 6, oz - 2, ox + W + 2, oy + 6, oz + D + 2, "dark_oak_slab[type=top]")

    # Peaked roof
    for i in range(8):
        ry = oy + 7 + i
        rz1 = oz - 1 + i
        rz2 = oz + D + 1 - i
        if rz1 >= rz2:
            fill(r, ox - 1, ry, rz1, ox + W + 1, ry, rz1, "dark_oak_slab")
            break
        fill(r, ox - 1, ry, rz1, ox + W + 1, ry, rz1,
             "dark_oak_stairs[facing=south,half=bottom]")
        fill(r, ox - 1, ry, rz2, ox + W + 1, ry, rz2,
             "dark_oak_stairs[facing=north,half=bottom]")

    # Roof ridge ornament
    ridge_z = oz + D // 2
    fill(r, ox - 1, oy + 7 + D // 2, ridge_z, ox + W + 1, oy + 7 + D // 2, ridge_z,
         "dark_oak_slab")

    # === INTERIOR FURNITURE ===
    # Main hall - center room
    # Tatami mats (smooth sandstone for tan color)
    fill(r, ox + 10, oy, oz + 1, ox + 16, oy, oz + D - 1, "smooth_sandstone")

    # Low table
    for tx in range(ox + 11, ox + 16):
        setblock(r, tx, oy + 1, oz + 7, "spruce_trapdoor[facing=south,half=top,open=false]")

    # Left room - bedroom
    fill(r, ox + 1, oy, oz + 1, ox + 8, oy, oz + D - 1, "smooth_sandstone")
    # Futon beds
    setblock(r, ox + 2, oy + 1, oz + 3, "red_bed[facing=south,part=foot]")
    setblock(r, ox + 2, oy + 1, oz + 4, "red_bed[facing=south,part=head]")
    setblock(r, ox + 4, oy + 1, oz + 3, "red_bed[facing=south,part=foot]")
    setblock(r, ox + 4, oy + 1, oz + 4, "red_bed[facing=south,part=head]")
    # Lanterns
    setblock(r, ox + 1, oy + 1, oz + 1, "lantern")
    setblock(r, ox + 8, oy + 1, oz + 1, "lantern")

    # Right room - study
    fill(r, ox + 18, oy, oz + 1, ox + W - 1, oy, oz + D - 1, "smooth_sandstone")
    fill(r, ox + 18, oy + 1, oz + 1, ox + 18, oy + 3, oz + 1, "bookshelf")
    fill(r, ox + 18, oy + 1, oz + 2, ox + 18, oy + 3, oz + 2, "bookshelf")
    fill(r, ox + 18, oy + 1, oz + 3, ox + 18, oy + 3, oz + 3, "bookshelf")
    setblock(r, ox + 22, oy + 1, oz + 7, "lectern")

    # Lanterns along ceiling
    for lx in range(ox + 3, ox + W, 6):
        setblock(r, lx, oy + 5, oz + D // 2, "lantern[hanging=true]")

    # Engawa (veranda/porch)
    fill(r, ox - 1, oy, oz - 1, ox + W + 1, oy, oz - 1, "spruce_slab")
    fill(r, ox - 1, oy, oz + D + 1, ox + W + 1, oy, oz + D + 1, "spruce_slab")

    # Steps
    fill(r, ox + 11, oy - 1, oz - 2, ox + 14, oy - 1, oz - 2, "stone_brick_stairs[facing=south]")
    fill(r, ox + 11, oy, oz - 2, ox + 14, oy, oz - 2, "spruce_slab")


# ============================================================
# GUEST HOUSE (smaller version)
# ============================================================
def build_guest_house(r, ox, oy, oz, facing="south"):
    """Build a smaller Japanese guest house. 9x7 footprint."""
    W, D = 9, 7

    # Foundation
    fill(r, ox, oy - 1, oz, ox + W, oy - 1, oz + D, "deepslate_bricks")
    # Floor
    fill(r, ox, oy, oz, ox + W, oy, oz + D, "spruce_planks")

    # Walls
    fill(r, ox, oy + 1, oz, ox + W, oy + 4, oz, "spruce_planks")
    fill(r, ox, oy + 1, oz + D, ox + W, oy + 4, oz + D, "spruce_planks")
    fill(r, ox, oy + 1, oz, ox, oy + 4, oz + D, "spruce_planks")
    fill(r, ox + W, oy + 1, oz, ox + W, oy + 4, oz + D, "spruce_planks")

    # Interior
    fill(r, ox + 1, oy + 1, oz + 1, ox + W - 1, oy + 3, oz + D - 1, "air")

    # Paper walls
    fill(r, ox + 1, oy + 2, oz, ox + W - 1, oy + 3, oz, "white_stained_glass_pane")
    fill(r, ox + 1, oy + 2, oz + D, ox + W - 1, oy + 3, oz + D, "white_stained_glass_pane")

    # Pillars
    for cx, cz in [(ox, oz), (ox + W, oz), (ox, oz + D), (ox + W, oz + D)]:
        fill(r, cx, oy + 1, cz, cx, oy + 4, cz, "dark_oak_log")

    # Door
    fill(r, ox + 4, oy + 1, oz, ox + 5, oy + 2, oz, "air")

    # Roof
    fill(r, ox - 1, oy + 5, oz - 1, ox + W + 1, oy + 5, oz + D + 1, "dark_oak_slab[type=top]")
    for i in range(5):
        ry = oy + 6 + i
        rz1 = oz - 1 + i
        rz2 = oz + D + 1 - i
        if rz1 >= rz2:
            fill(r, ox - 1, ry, rz1, ox + W + 1, ry, rz1, "dark_oak_slab")
            break
        fill(r, ox - 1, ry, rz1, ox + W + 1, ry, rz1,
             "dark_oak_stairs[facing=south,half=bottom]")
        fill(r, ox - 1, ry, rz2, ox + W + 1, ry, rz2,
             "dark_oak_stairs[facing=north,half=bottom]")

    # Tatami floor
    fill(r, ox + 1, oy, oz + 1, ox + W - 1, oy, oz + D - 1, "smooth_sandstone")
    # Bed
    setblock(r, ox + 2, oy + 1, oz + 4, "red_bed[facing=south,part=foot]")
    setblock(r, ox + 2, oy + 1, oz + 5, "red_bed[facing=south,part=head]")
    # Lantern
    setblock(r, ox + W // 2, oy + 4, oz + D // 2, "lantern[hanging=true]")
    # Veranda
    fill(r, ox, oy, oz - 1, ox + W, oy, oz - 1, "spruce_slab")


# ============================================================
# TORII GATE
# ============================================================
def build_torii(r, x, y, z, facing="ns"):
    """Build a torii gate."""
    if facing == "ns":
        # Posts
        fill(r, x - 2, y, z, x - 2, y + 5, z, "red_nether_bricks")
        fill(r, x + 2, y, z, x + 2, y + 5, z, "red_nether_bricks")
        # Top beam (kasagi)
        fill(r, x - 3, y + 5, z, x + 3, y + 5, z, "red_nether_bricks")
        fill(r, x - 3, y + 6, z, x + 3, y + 6, z, "red_nether_brick_slab")
        # Cross beam (nuki)
        fill(r, x - 2, y + 4, z, x + 2, y + 4, z, "red_nether_bricks")
    else:
        fill(r, x, y, z - 2, x, y + 5, z - 2, "red_nether_bricks")
        fill(r, x, y, z + 2, x, y + 5, z + 2, "red_nether_bricks")
        fill(r, x, y + 5, z - 3, x, y + 5, z + 3, "red_nether_bricks")
        fill(r, x, y + 6, z - 3, x, y + 6, z + 3, "red_nether_brick_slab")
        fill(r, x, y + 4, z - 2, x, y + 4, z + 2, "red_nether_bricks")


# ============================================================
# STONE LANTERN
# ============================================================
def build_stone_lantern(r, x, y, z):
    """Build a Japanese stone lantern (toro)."""
    setblock(r, x, y, z, "stone_brick_wall")
    setblock(r, x, y + 1, z, "stone_brick_wall")
    setblock(r, x, y + 2, z, "lantern")
    setblock(r, x, y + 3, z, "stone_brick_slab")


# ============================================================
# MAIN BUILD
# ============================================================
def main():
    r = RCON()

    # Village center at 400, 70, 100 (away from existing builds)
    VX, VY, VZ = 400, 70, 100

    print("=== Building Sakura Mansion Village ===")
    print(f"Center: {VX}, {VY}, {VZ}")

    # Step 1: Clear and flatten area (80x80)
    print("\n[1/6] Clearing and flattening terrain...")
    for cx in range(VX - 10, VX + 70, 30):
        for cz in range(VZ - 10, VZ + 70, 30):
            fill(r, cx, VY, cz, min(cx + 29, VX + 69), VY + 30, min(cz + 29, VZ + 69), "air")
            fill(r, cx, VY - 1, cz, min(cx + 29, VX + 69), VY - 1, min(cz + 29, VZ + 69), "grass_block")
            fill(r, cx, VY - 4, cz, min(cx + 29, VX + 69), VY - 2, min(cz + 29, VZ + 69), "dirt")

    # Step 2: Gravel paths
    print("\n[2/6] Laying paths...")
    # Main north-south path
    fill(r, VX + 28, VY - 1, VZ - 5, VX + 30, VY - 1, VZ + 65, "gravel")
    fill(r, VX + 27, VY, VZ - 5, VX + 27, VY, VZ + 65, "stone_brick_slab[type=bottom]")
    fill(r, VX + 31, VY, VZ - 5, VX + 31, VY, VZ + 65, "stone_brick_slab[type=bottom]")

    # East-west cross path
    fill(r, VX - 5, VY - 1, VZ + 28, VX + 65, VY - 1, VZ + 30, "gravel")
    fill(r, VX - 5, VY, VZ + 27, VX + 65, VY, VZ + 27, "stone_brick_slab[type=bottom]")
    fill(r, VX - 5, VY, VZ + 31, VX + 65, VY, VZ + 31, "stone_brick_slab[type=bottom]")

    # Path to mansion (south)
    fill(r, VX + 28, VY - 1, VZ + 32, VX + 30, VY - 1, VZ + 50, "gravel")

    # Step 3: Main Mansion (south side, center)
    print("\n[3/6] Building main mansion...")
    build_mansion(r, VX + 17, VY, VZ + 40, "Main Mansion")

    # Step 4: Guest houses & buildings
    print("\n[4/6] Building village structures...")

    # Guest house 1 - northwest
    print("  Building Guest House 1 (NW)...")
    build_guest_house(r, VX + 2, VY, VZ + 5)

    # Guest house 2 - northeast
    print("  Building Guest House 2 (NE)...")
    build_guest_house(r, VX + 45, VY, VZ + 5)

    # Guest house 3 - west
    print("  Building Guest House 3 (W)...")
    build_guest_house(r, VX + 2, VY, VZ + 20)

    # Guest house 4 - east
    print("  Building Guest House 4 (E)...")
    build_guest_house(r, VX + 45, VY, VZ + 20)

    # Tea house (tiny, by the pond)
    print("  Building Tea House...")
    build_guest_house(r, VX + 2, VY, VZ + 42)

    # Torii gates
    print("  Building Torii Gates...")
    build_torii(r, VX + 29, VY, VZ - 3, "ew")  # entrance
    build_torii(r, VX + 29, VY, VZ + 35, "ew")  # before mansion

    # Step 5: Sakura trees
    print("\n[5/6] Planting sakura trees...")
    tree_spots = [
        # Along main path
        (VX + 24, VZ + 5, "medium"), (VX + 34, VZ + 5, "medium"),
        (VX + 24, VZ + 15, "large"), (VX + 34, VZ + 15, "large"),
        (VX + 24, VZ + 25, "medium"), (VX + 34, VZ + 25, "medium"),
        (VX + 24, VZ + 38, "large"), (VX + 34, VZ + 38, "large"),
        # Around mansion
        (VX + 14, VZ + 42, "large"), (VX + 45, VZ + 42, "large"),
        (VX + 14, VZ + 52, "medium"), (VX + 45, VZ + 52, "medium"),
        # Near guest houses
        (VX + 14, VZ + 8, "small"), (VX + 42, VZ + 8, "small"),
        (VX + 14, VZ + 23, "small"), (VX + 42, VZ + 23, "small"),
        # Grove in corners
        (VX + 3, VZ + 55, "large"), (VX + 7, VZ + 58, "medium"),
        (VX + 55, VZ + 55, "large"), (VX + 52, VZ + 58, "medium"),
        (VX + 1, VZ - 2, "large"), (VX + 57, VZ - 2, "large"),
        # Extra scattered
        (VX + 20, VZ + 0, "medium"), (VX + 40, VZ + 0, "medium"),
    ]
    for i, (tx, tz, size) in enumerate(tree_spots):
        print(f"  Planting tree {i + 1}/{len(tree_spots)}...")
        build_sakura_tree(r, tx, VY, tz, size)

    # Step 6: Details
    print("\n[6/6] Adding details...")

    # Stone lanterns along paths
    lantern_spots = [
        (VX + 26, VZ + 0), (VX + 32, VZ + 0),
        (VX + 26, VZ + 10), (VX + 32, VZ + 10),
        (VX + 26, VZ + 20), (VX + 32, VZ + 20),
        (VX + 26, VZ + 33), (VX + 32, VZ + 33),
        (VX + 10, VZ + 26), (VX + 48, VZ + 26),
        (VX + 20, VZ + 26), (VX + 38, VZ + 26),
    ]
    for lx, lz in lantern_spots:
        build_stone_lantern(r, lx, VY, lz)

    # Pond (east side)
    print("  Building koi pond...")
    fill(r, VX + 48, VY - 2, VZ + 35, VX + 56, VY - 2, VZ + 42, "clay")
    fill(r, VX + 49, VY - 1, VZ + 36, VX + 55, VY - 1, VZ + 41, "water")
    fill(r, VX + 50, VY - 1, VZ + 37, VX + 54, VY - 1, VZ + 40, "water")
    # Lily pads
    for _ in range(4):
        px = random.randint(VX + 50, VX + 54)
        pz = random.randint(VZ + 37, VZ + 40)
        setblock(r, px, VY, pz, "lily_pad")
    # Stone border
    fill(r, VX + 47, VY, VZ + 34, VX + 57, VY, VZ + 34, "mossy_stone_brick_slab")
    fill(r, VX + 47, VY, VZ + 43, VX + 57, VY, VZ + 43, "mossy_stone_brick_slab")
    fill(r, VX + 47, VY, VZ + 34, VX + 47, VY, VZ + 43, "mossy_stone_brick_slab")
    fill(r, VX + 57, VY, VZ + 34, VX + 57, VY, VZ + 43, "mossy_stone_brick_slab")

    # Bamboo garden (west side)
    print("  Planting bamboo garden...")
    for bx in range(VX + 0, VX + 8, 2):
        for bz in range(VZ + 32, VZ + 38, 2):
            h = random.randint(3, 6)
            fill(r, bx, VY, bz, bx, VY + h, bz, "bamboo[leaves=large]")

    # Flower gardens
    print("  Planting flower gardens...")
    flowers = ["pink_tulip", "allium", "azure_bluet", "white_tulip",
               "oxeye_daisy", "peony"]
    for fx in range(VX + 15, VX + 42, 3):
        for fz in [VZ + 37, VZ + 38]:
            f = random.choice(flowers)
            setblock(r, fx, VY, fz, f)

    # Set time to day, clear weather
    r.cmd("time set 6000")
    r.cmd("weather clear")

    print(f"\n=== Village Complete! ===")
    print(f"Center: {VX + 29}, {VY}, {VZ + 29}")
    print(f"Main mansion entrance: {VX + 29}, {VY}, {VZ + 40}")
    print("Features: Main mansion, 5 guest houses, 2 torii gates,")
    print(f"  {len(tree_spots)} sakura trees, koi pond, bamboo garden,")
    print(f"  {len(lantern_spots)} stone lanterns, flower gardens")

    r.close()
    return VX, VY, VZ


if __name__ == "__main__":
    main()
