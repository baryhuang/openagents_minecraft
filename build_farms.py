#!/usr/bin/env python3
"""
Build automatic resource farms for the Sakura Village.
Self-sustaining food and materials — the village feeds itself.

Auto-growing resources in Minecraft:
1. Wheat, Carrots, Potatoes, Beetroot — crop farms with water
2. Sugar Cane — grows on sand next to water, harvestable infinitely
3. Bamboo — fastest growing plant, fuel + scaffolding
4. Cactus — grows in sand, useful for dyes + XP
5. Pumpkins & Melons — grow on stems, infinite harvest
6. Sweet Berries — bush that regrows
7. Kelp — underwater, grows fast
8. Trees — saplings replant (cherry/oak)
9. Mushrooms — spread in dark areas
10. Cocoa Beans — grow on jungle logs
"""

import socket
import struct
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

    def cmd(self, c):
        self._send(2, 2, c)
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
# WHEAT & CROP FARM (10x10 with water channels)
# ============================================================
def build_crop_farm(r, ox, oy, oz, crop="wheat", label="Wheat"):
    """Auto-irrigated crop farm. 12x12 with water channels."""
    print(f"  Building {label} farm at {ox},{oy},{oz}...")

    # Clear area
    fill(r, ox - 1, oy, oz - 1, ox + 12, oy + 4, oz + 12, "air")

    # Border wall (wood)
    fill(r, ox - 1, oy, oz - 1, ox + 12, oy + 1, oz - 1, "spruce_planks")
    fill(r, ox - 1, oy, oz + 12, ox + 12, oy + 1, oz + 12, "spruce_planks")
    fill(r, ox - 1, oy, oz - 1, ox - 1, oy + 1, oz + 12, "spruce_planks")
    fill(r, ox + 12, oy, oz - 1, ox + 12, oy + 1, oz + 12, "spruce_planks")

    # Base layer
    fill(r, ox, oy - 1, oz, ox + 11, oy - 1, oz + 11, "dirt")

    # Water channels (cross pattern)
    fill(r, ox + 5, oy - 1, oz, ox + 6, oy - 1, oz + 11, "water")
    fill(r, ox, oy - 1, oz + 5, ox + 11, oy - 1, oz + 6, "water")

    # Farmland around water
    for x in range(ox, ox + 12):
        for z in range(oz, oz + 12):
            if not (ox + 5 <= x <= ox + 6 or oz + 5 <= z <= oz + 6):
                setblock(r, x, oy - 1, z, "farmland[moisture=7]")
                # Plant crops
                crop_block = {
                    "wheat": "wheat[age=7]",
                    "carrots": "carrots[age=7]",
                    "potatoes": "potatoes[age=7]",
                    "beetroots": "beetroots[age=3]",
                }[crop]
                setblock(r, x, oy, z, crop_block)

    # Torches for light (prevents uprooting at night)
    for x in [ox + 2, ox + 9]:
        for z in [oz + 2, oz + 9]:
            setblock(r, x, oy + 1, z, "torch")

    # Sign
    setblock(r, ox + 5, oy + 1, oz - 1, f'oak_sign[rotation=0]')


# ============================================================
# SUGAR CANE FARM (auto-grows, just harvest periodically)
# ============================================================
def build_sugarcane_farm(r, ox, oy, oz):
    """Sugar cane farm with water channels."""
    print(f"  Building Sugar Cane farm at {ox},{oy},{oz}...")

    fill(r, ox, oy, oz, ox + 11, oy + 5, oz + 7, "air")
    fill(r, ox, oy - 1, oz, ox + 11, oy - 1, oz + 7, "sand")

    # Alternating rows: water | sand+cane | sand+cane | water | ...
    for row in range(0, 8, 2):
        fill(r, ox, oy - 1, oz + row, ox + 11, oy - 1, oz + row, "water")
        if row + 1 < 8:
            fill(r, ox, oy - 1, oz + row + 1, ox + 11, oy - 1, oz + row + 1, "sand")
            for x in range(ox, ox + 12):
                fill(r, x, oy, oz + row + 1, x, oy + 2, oz + row + 1, "sugar_cane")

    # Border
    fill(r, ox - 1, oy - 1, oz - 1, ox + 12, oy, oz - 1, "spruce_planks")
    fill(r, ox - 1, oy - 1, oz + 8, ox + 12, oy, oz + 8, "spruce_planks")


# ============================================================
# PUMPKIN & MELON FARM (stems grow fruit on adjacent blocks)
# ============================================================
def build_pumpkin_melon_farm(r, ox, oy, oz):
    """Pumpkin + melon farm. Stems auto-grow fruit."""
    print(f"  Building Pumpkin & Melon farm at {ox},{oy},{oz}...")

    fill(r, ox, oy, oz, ox + 11, oy + 3, oz + 9, "air")
    fill(r, ox, oy - 1, oz, ox + 11, oy - 1, oz + 9, "dirt")

    # Pattern: [farmland+stem] [dirt for fruit] [water] [dirt for fruit] [farmland+stem]
    for row in range(0, 10, 5):
        # Water row
        fill(r, ox, oy - 1, oz + row + 2, ox + 11, oy - 1, oz + row + 2, "water")
        # Farmland + stem rows
        for dr in [0, 4]:
            z = oz + row + dr
            if z < oz + 10:
                fill(r, ox, oy - 1, z, ox + 11, oy - 1, z, "farmland[moisture=7]")
                for x in range(ox, ox + 12):
                    stem = "pumpkin_stem[age=7]" if (x % 2 == 0) else "melon_stem[age=7]"
                    setblock(r, x, oy, z, stem)
        # Fruit growth rows (dirt)
        for dr in [1, 3]:
            z = oz + row + dr
            if z < oz + 10:
                fill(r, ox, oy - 1, z, ox + 11, oy - 1, z, "dirt")
                # Place some mature fruit
                for x in range(ox, ox + 12, 3):
                    fruit = "pumpkin" if random.random() > 0.5 else "melon"
                    setblock(r, x, oy, z, fruit)

    # Border
    fill(r, ox - 1, oy - 1, oz - 1, ox + 12, oy, oz - 1, "spruce_planks")
    fill(r, ox - 1, oy - 1, oz + 10, ox + 12, oy, oz + 10, "spruce_planks")


# ============================================================
# BAMBOO GROVE (fastest growing, infinite fuel)
# ============================================================
def build_bamboo_grove(r, ox, oy, oz):
    """Dense bamboo grove — grows to max height automatically."""
    print(f"  Building Bamboo grove at {ox},{oy},{oz}...")

    fill(r, ox, oy, oz, ox + 7, oy + 10, oz + 7, "air")
    fill(r, ox, oy - 1, oz, ox + 7, oy - 1, oz + 7, "podzol")

    for x in range(ox, ox + 8):
        for z in range(oz, oz + 8):
            if random.random() > 0.3:
                h = random.randint(4, 10)
                for dy in range(h):
                    leaves = "large" if dy > h - 3 else ("small" if dy > h - 5 else "none")
                    setblock(r, x, oy + dy, z, f"bamboo[leaves={leaves}]")


# ============================================================
# BERRY BUSHES (sweet berries regrow after harvest)
# ============================================================
def build_berry_garden(r, ox, oy, oz):
    """Sweet berry garden — berries regrow automatically."""
    print(f"  Building Berry garden at {ox},{oy},{oz}...")

    fill(r, ox, oy, oz, ox + 7, oy + 2, oz + 7, "air")
    fill(r, ox, oy - 1, oz, ox + 7, oy - 1, oz + 7, "grass_block")

    for x in range(ox, ox + 8, 2):
        for z in range(oz, oz + 8, 2):
            setblock(r, x, oy, z, "sweet_berry_bush[age=3]")

    # Path through berries
    fill(r, ox + 3, oy - 1, oz, ox + 4, oy - 1, oz + 7, "gravel")
    fill(r, ox + 3, oy, oz, ox + 4, oy, oz + 7, "air")


# ============================================================
# TREE FARM (saplings auto-grow with bone meal or time)
# ============================================================
def build_tree_farm(r, ox, oy, oz):
    """Cherry + Oak sapling tree farm."""
    print(f"  Building Tree farm at {ox},{oy},{oz}...")

    fill(r, ox, oy, oz, ox + 15, oy + 12, oz + 7, "air")
    fill(r, ox, oy - 1, oz, ox + 15, oy - 1, oz + 7, "grass_block")

    # Plant saplings in grid
    saplings = ["cherry_sapling", "oak_sapling", "birch_sapling", "spruce_sapling"]
    for i, x in enumerate(range(ox + 2, ox + 14, 4)):
        for z in [oz + 2, oz + 5]:
            sap = saplings[i % len(saplings)]
            setblock(r, x, oy, z, sap)
            # Torch nearby for light
            setblock(r, x + 1, oy, z, "torch")

    # Border
    fill(r, ox - 1, oy, oz - 1, ox + 16, oy + 1, oz - 1, "oak_fence")
    fill(r, ox - 1, oy, oz + 8, ox + 16, oy + 1, oz + 8, "oak_fence")


# ============================================================
# CACTUS FARM (grows on sand, auto-breaks)
# ============================================================
def build_cactus_farm(r, ox, oy, oz):
    """Cactus auto-farm with sand columns."""
    print(f"  Building Cactus farm at {ox},{oy},{oz}...")

    fill(r, ox, oy, oz, ox + 7, oy + 5, oz + 7, "air")
    fill(r, ox, oy - 1, oz, ox + 7, oy - 1, oz + 7, "sand")

    # Cactus on every other block (they can't be adjacent)
    for x in range(ox, ox + 8, 2):
        for z in range(oz, oz + 8, 2):
            fill(r, x, oy, z, x, oy + 2, z, "cactus")


# ============================================================
# MUSHROOM CAVE (spreads in darkness)
# ============================================================
def build_mushroom_cave(r, ox, oy, oz):
    """Underground mushroom farm — mushrooms spread in the dark."""
    print(f"  Building Mushroom cave at {ox},{oy},{oz}...")

    # Dig out cave
    fill(r, ox, oy, oz, ox + 9, oy + 3, oz + 9, "air")
    # Floor
    fill(r, ox, oy - 1, oz, ox + 9, oy - 1, oz + 9, "mycelium")
    # Ceiling (must be dark)
    fill(r, ox, oy + 4, oz, ox + 9, oy + 4, oz + 9, "stone_bricks")
    # Walls
    fill(r, ox - 1, oy, oz - 1, ox - 1, oy + 4, oz + 10, "stone_bricks")
    fill(r, ox + 10, oy, oz - 1, ox + 10, oy + 4, oz + 10, "stone_bricks")
    fill(r, ox, oy, oz - 1, ox + 9, oy + 4, oz - 1, "stone_bricks")
    fill(r, ox, oy, oz + 10, ox + 9, oy + 4, oz + 10, "stone_bricks")
    # Door
    fill(r, ox + 4, oy, oz - 1, ox + 5, oy + 1, oz - 1, "air")

    # Plant mushrooms
    for x in range(ox, ox + 10, 2):
        for z in range(oz, oz + 10, 2):
            m = "red_mushroom" if random.random() > 0.5 else "brown_mushroom"
            setblock(r, x, oy, z, m)


# ============================================================
# MAIN BUILD
# ============================================================
def main():
    r = RCON()

    # Farm district — east of the village
    FX = 465  # east of village
    FY = 70
    FZ = 95   # starting z

    print("=== Building Village Farm District ===\n")

    # Clear farm area
    print("[1/9] Clearing farm district...")
    for cx in range(FX - 2, FX + 50, 30):
        for cz in range(FZ - 2, FZ + 60, 30):
            fill(r, cx, FY - 2, cz, min(cx + 29, FX + 49), FY + 12, min(cz + 29, FZ + 59), "air")
            fill(r, cx, FY - 2, cz, min(cx + 29, FX + 49), FY - 2, min(cz + 29, FZ + 59), "grass_block")
            fill(r, cx, FY - 3, cz, min(cx + 29, FX + 49), FY - 3, min(cz + 29, FZ + 59), "dirt")

    # Path from village to farms
    print("[2/9] Building path to farms...")
    fill(r, 460, FY - 1, FZ + 28, FX, FY - 1, FZ + 30, "gravel")

    # Build farms
    print("[3/9] Wheat farm...")
    build_crop_farm(r, FX, FY, FZ, "wheat", "Wheat")

    print("[4/9] Carrot & Potato farm...")
    build_crop_farm(r, FX + 16, FY, FZ, "carrots", "Carrot")

    print("[5/9] Sugar Cane farm...")
    build_sugarcane_farm(r, FX, FY, FZ + 16)

    print("[6/9] Pumpkin & Melon farm...")
    build_pumpkin_melon_farm(r, FX + 16, FY, FZ + 16)

    print("[7/9] Bamboo grove...")
    build_bamboo_grove(r, FX + 32, FY, FZ)

    print("[8/9] Berry garden & Tree farm...")
    build_berry_garden(r, FX + 32, FY, FZ + 10)
    build_tree_farm(r, FX, FY, FZ + 30)

    print("[9/9] Cactus farm & Mushroom cave...")
    build_cactus_farm(r, FX + 32, FY, FZ + 20)
    build_mushroom_cave(r, FX + 20, FY - 4, FZ + 32)

    # Entrance arch to farm district
    fill(r, FX - 1, FY, FZ + 28, FX - 1, FY + 4, FZ + 28, "dark_oak_log")
    fill(r, FX - 1, FY, FZ + 30, FX - 1, FY + 4, FZ + 30, "dark_oak_log")
    fill(r, FX - 1, FY + 4, FZ + 28, FX - 1, FY + 4, FZ + 30, "dark_oak_planks")
    setblock(r, FX - 1, FY + 5, FZ + 29, "dark_oak_slab")

    # Sakura tree at entrance
    print("  Planting sakura at farm entrance...")
    # Simple small cherry tree
    fill(r, FX - 3, FY, FZ + 25, FX - 3, FY + 4, FZ + 25, "cherry_log")
    for dy in range(3, 6):
        cr = 3 - abs(dy - 4)
        for dx in range(-cr, cr + 1):
            for dz in range(-cr, cr + 1):
                if abs(dx) + abs(dz) <= cr + 1 and random.random() > 0.2:
                    fill(r, FX - 3 + dx, FY + dy, FZ + 25 + dz,
                         FX - 3 + dx, FY + dy, FZ + 25 + dz,
                         "cherry_leaves[persistent=true]", "replace air")

    # Announce completion
    r.cmd("time set day")

    print(f"""
=== Farm District Complete! ===
Location: {FX}, {FY}, {FZ}

Auto-Growing Resources:
  1. Wheat Farm (12x12)      — bread, trading
  2. Carrot Farm (12x12)     — food, golden carrots
  3. Sugar Cane Farm (12x8)  — paper, books, rockets
  4. Pumpkin & Melon Farm    — food, jack-o-lanterns, glistering melon
  5. Bamboo Grove (8x8)      — scaffolding, fuel, sticks
  6. Sweet Berry Garden      — food, trading
  7. Tree Farm (16x8)        — cherry, oak, birch, spruce saplings
  8. Cactus Farm (8x8)       — green dye, XP
  9. Mushroom Cave (10x10)   — mushroom stew, suspicious stew

All farms are self-sustaining. Crops regrow, cane regenerates,
pumpkins/melons respawn on stems, bamboo grows infinitely,
mushrooms spread in the dark, berries regrow after picking.

The village can now feed itself forever.
""")

    r.close()


if __name__ == "__main__":
    main()
