#!/usr/bin/env python3
"""
Generate a Sponge Schematic v2 (.schem) file for a single family house.
Baritone can then build it block-by-block like a real player.
"""

import struct
import gzip
import io

# ============================================
# NBT Writer (minimal implementation)
# ============================================

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12

class NBTWriter:
    def __init__(self):
        self.buf = io.BytesIO()

    def write_byte(self, v):
        self.buf.write(struct.pack('>b', v))

    def write_short(self, v):
        self.buf.write(struct.pack('>h', v))

    def write_int(self, v):
        self.buf.write(struct.pack('>i', v))

    def write_long(self, v):
        self.buf.write(struct.pack('>q', v))

    def write_string(self, s):
        b = s.encode('utf-8')
        self.write_short(len(b))
        self.buf.write(b)

    def write_tag_header(self, tag_type, name):
        self.buf.write(struct.pack('>b', tag_type))
        self.write_string(name)

    def write_named_byte(self, name, v):
        self.write_tag_header(TAG_BYTE, name)
        self.write_byte(v)

    def write_named_short(self, name, v):
        self.write_tag_header(TAG_SHORT, name)
        self.write_short(v)

    def write_named_int(self, name, v):
        self.write_tag_header(TAG_INT, name)
        self.write_int(v)

    def write_named_string(self, name, v):
        self.write_tag_header(TAG_STRING, name)
        self.write_string(v)

    def write_named_byte_array(self, name, data):
        self.write_tag_header(TAG_BYTE_ARRAY, name)
        self.write_int(len(data))
        self.buf.write(bytes(data))

    def write_compound_start(self, name):
        self.write_tag_header(TAG_COMPOUND, name)

    def write_compound_end(self):
        self.buf.write(struct.pack('>b', TAG_END))

    def write_varint_array(self, name, values):
        """Write a byte array with varint-encoded values (for Sponge schematic BlockData)."""
        self.write_tag_header(TAG_BYTE_ARRAY, name)
        # Encode all values as varints first
        encoded = bytearray()
        for v in values:
            while v > 0x7F:
                encoded.append((v & 0x7F) | 0x80)
                v >>= 7
            encoded.append(v & 0x7F)
        self.write_int(len(encoded))
        self.buf.write(bytes(encoded))

    def get_data(self):
        return self.buf.getvalue()


# ============================================
# House Blueprint
# ============================================

def create_house():
    """
    Create a house blueprint as a 3D grid of block state strings.
    House: 13 wide (X), 12 tall (Y), 11 deep (Z)
    Includes foundation, walls, roof, interior, porch
    """
    W, H, D = 13, 12, 11  # width, height, depth
    AIR = "minecraft:air"

    # Initialize with air
    blocks = [[[AIR for _ in range(D)] for _ in range(H)] for _ in range(W)]

    def set_block(x, y, z, block):
        if 0 <= x < W and 0 <= y < H and 0 <= z < D:
            blocks[x][y][z] = block

    def fill_blocks(x1, y1, z1, x2, y2, z2, block):
        for x in range(min(x1,x2), max(x1,x2)+1):
            for y in range(min(y1,y2), max(y1,y2)+1):
                for z in range(min(z1,z2), max(z1,z2)+1):
                    set_block(x, y, z, block)

    # Coordinate system: house starts at (1,0,1), leaving room for porch/fence
    # House body: x=1..11, z=2..10 (11 wide, 9 deep)
    bx, bz = 1, 2  # house origin offset

    # === FOUNDATION (y=0) ===
    fill_blocks(bx, 0, bz, bx+10, 0, bz+8, "minecraft:stone_bricks")

    # === FLOOR (y=1) ===
    fill_blocks(bx, 1, bz, bx+10, 1, bz+8, "minecraft:oak_planks")

    # === WALLS (y=2..5) ===
    # Front wall (z=bz)
    fill_blocks(bx, 2, bz, bx+10, 5, bz, "minecraft:oak_planks")
    # Back wall (z=bz+8)
    fill_blocks(bx, 2, bz+8, bx+10, 5, bz+8, "minecraft:oak_planks")
    # Left wall (x=bx)
    fill_blocks(bx, 2, bz, bx, 5, bz+8, "minecraft:oak_planks")
    # Right wall (x=bx+10)
    fill_blocks(bx+10, 2, bz, bx+10, 5, bz+8, "minecraft:oak_planks")

    # === INTERIOR (hollow) ===
    fill_blocks(bx+1, 2, bz+1, bx+9, 4, bz+7, AIR)

    # === INTERIOR DIVIDER (z=bz+5) ===
    fill_blocks(bx+1, 2, bz+5, bx+9, 4, bz+5, "minecraft:stripped_oak_log")
    # Doorways in divider
    fill_blocks(bx+3, 2, bz+5, bx+4, 3, bz+5, AIR)
    fill_blocks(bx+7, 2, bz+5, bx+8, 3, bz+5, AIR)

    # Side divider (bedroom/bathroom)
    fill_blocks(bx+6, 2, bz+6, bx+6, 4, bz+7, "minecraft:stripped_oak_log")
    fill_blocks(bx+6, 2, bz+7, bx+6, 3, bz+7, AIR)  # doorway

    # === WINDOWS ===
    # Front
    fill_blocks(bx+2, 3, bz, bx+3, 4, bz, "minecraft:glass_pane")
    fill_blocks(bx+7, 3, bz, bx+8, 4, bz, "minecraft:glass_pane")
    # Back
    fill_blocks(bx+2, 3, bz+8, bx+3, 4, bz+8, "minecraft:glass_pane")
    fill_blocks(bx+8, 3, bz+8, bx+9, 4, bz+8, "minecraft:glass_pane")
    # Sides
    fill_blocks(bx, 3, bz+3, bx, 4, bz+4, "minecraft:glass_pane")
    fill_blocks(bx+10, 3, bz+3, bx+10, 4, bz+4, "minecraft:glass_pane")
    fill_blocks(bx, 3, bz+7, bx, 4, bz+7, "minecraft:glass_pane")
    fill_blocks(bx+10, 3, bz+7, bx+10, 4, bz+7, "minecraft:glass_pane")

    # === FRONT DOOR ===
    fill_blocks(bx+5, 2, bz, bx+5, 3, bz, AIR)
    set_block(bx+5, 2, bz, "minecraft:oak_door[facing=south,half=lower,open=false]")
    set_block(bx+5, 3, bz, "minecraft:oak_door[facing=south,half=upper,open=false]")

    # === CEILING (y=6) ===
    fill_blocks(bx, 6, bz, bx+10, 6, bz+8, "minecraft:oak_planks")

    # === ROOF (peaked, dark oak stairs) ===
    for i in range(6):
        ry = 7 + i
        rx1 = bx - 1 + i
        rx2 = bx + 11 - i
        if rx1 >= rx2:
            fill_blocks(rx1, ry, bz-1, rx1, ry, bz+9, "minecraft:dark_oak_slab")
            break
        fill_blocks(rx1, ry, bz-1, rx1, ry, bz+9,
                    "minecraft:dark_oak_stairs[facing=east,half=bottom]")
        fill_blocks(rx2, ry, bz-1, rx2, ry, bz+9,
                    "minecraft:dark_oak_stairs[facing=west,half=bottom]")

    # === PORCH ===
    fill_blocks(bx+3, 1, bz-1, bx+7, 1, bz-1, "minecraft:cobblestone_slab")
    set_block(bx+3, 2, bz-1, "minecraft:oak_fence")
    set_block(bx+3, 3, bz-1, "minecraft:oak_fence")
    set_block(bx+7, 2, bz-1, "minecraft:oak_fence")
    set_block(bx+7, 3, bz-1, "minecraft:oak_fence")
    fill_blocks(bx+3, 4, bz-1, bx+7, 4, bz-1, "minecraft:oak_slab")

    # === FURNITURE ===
    # Living room - couch
    fill_blocks(bx+1, 2, bz+3, bx+3, 2, bz+3,
                "minecraft:oak_stairs[facing=south]")
    # Coffee table
    set_block(bx+2, 2, bz+2, "minecraft:oak_fence")
    set_block(bx+2, 3, bz+2, "minecraft:oak_pressure_plate")
    # Bookshelf
    fill_blocks(bx+1, 2, bz+4, bx+1, 4, bz+4, "minecraft:bookshelf")
    # Carpet
    fill_blocks(bx+1, 2, bz+1, bx+4, 2, bz+1, "minecraft:red_carpet")

    # Kitchen
    set_block(bx+7, 2, bz+1, "minecraft:crafting_table")
    set_block(bx+8, 2, bz+1, "minecraft:furnace[facing=south]")
    set_block(bx+9, 2, bz+1, "minecraft:smoker[facing=south]")
    # Dining table
    set_block(bx+7, 2, bz+3, "minecraft:oak_fence")
    set_block(bx+7, 3, bz+3, "minecraft:oak_pressure_plate")
    set_block(bx+8, 2, bz+3, "minecraft:oak_fence")
    set_block(bx+8, 3, bz+3, "minecraft:oak_pressure_plate")
    # Chairs
    set_block(bx+7, 2, bz+2, "minecraft:oak_stairs[facing=south]")
    set_block(bx+8, 2, bz+2, "minecraft:oak_stairs[facing=south]")
    set_block(bx+7, 2, bz+4, "minecraft:oak_stairs[facing=north]")
    set_block(bx+8, 2, bz+4, "minecraft:oak_stairs[facing=north]")
    set_block(bx+9, 2, bz+4, "minecraft:chest[facing=west]")

    # Bedroom
    set_block(bx+1, 2, bz+7, "minecraft:red_bed[facing=south,part=head]")
    set_block(bx+1, 2, bz+6, "minecraft:red_bed[facing=south,part=foot]")
    set_block(bx+2, 2, bz+7, "minecraft:red_bed[facing=south,part=head]")
    set_block(bx+2, 2, bz+6, "minecraft:red_bed[facing=south,part=foot]")
    set_block(bx+3, 2, bz+7, "minecraft:lantern")
    fill_blocks(bx+1, 2, bz+6, bx+4, 2, bz+6, "minecraft:white_carpet")

    # Bathroom floor
    fill_blocks(bx+7, 1, bz+6, bx+9, 1, bz+7, "minecraft:smooth_stone")

    # Torches
    set_block(bx+1, 4, bz+1, "minecraft:torch")
    set_block(bx+9, 4, bz+1, "minecraft:torch")
    set_block(bx+1, 4, bz+7, "minecraft:torch")
    set_block(bx+9, 4, bz+7, "minecraft:torch")

    # Porch lantern
    set_block(bx+5, 4, bz-1, "minecraft:lantern[hanging=true]")

    return blocks, W, H, D


def write_schematic(blocks, width, height, depth, filename):
    """Write a Sponge Schematic v2 .schem file."""

    # Build palette: map block state strings to integer IDs
    palette = {}
    palette_id = 0

    # Flatten blocks in YZX order (Sponge schematic standard)
    block_data = []
    for y in range(height):
        for z in range(depth):
            for x in range(width):
                block = blocks[x][y][z]
                if block not in palette:
                    palette[block] = palette_id
                    palette_id += 1
                block_data.append(palette[block])

    # Write NBT
    nbt = NBTWriter()

    # Root compound "Schematic"
    nbt.write_compound_start("Schematic")

    nbt.write_named_int("Version", 2)
    nbt.write_named_int("DataVersion", 4325)  # MC 1.21.5 data version

    nbt.write_named_short("Width", width)
    nbt.write_named_short("Height", height)
    nbt.write_named_short("Length", depth)

    # Palette compound
    nbt.write_compound_start("Palette")
    for block_state, bid in palette.items():
        nbt.write_named_int(block_state, bid)
    nbt.write_compound_end()

    nbt.write_named_int("PaletteMax", len(palette))

    # BlockData as varint-encoded byte array
    nbt.write_varint_array("BlockData", block_data)

    # Metadata
    nbt.write_compound_start("Metadata")
    nbt.write_named_string("Name", "SingleFamilyHouse")
    nbt.write_named_string("Author", "ClaudeBot")
    nbt.write_compound_end()

    nbt.write_compound_end()  # end Schematic

    # GZip compress and write
    raw = nbt.get_data()
    with gzip.open(filename, 'wb') as f:
        f.write(raw)

    print(f"Schematic saved: {filename}")
    print(f"  Dimensions: {width}x{height}x{depth}")
    print(f"  Palette: {len(palette)} block types")
    print(f"  Total blocks: {len(block_data)} ({sum(1 for b in block_data if b != palette.get('minecraft:air', -1))} non-air)")

    # Print material list
    from collections import Counter
    flat = []
    for y in range(height):
        for z in range(depth):
            for x in range(width):
                b = blocks[x][y][z]
                if b != "minecraft:air":
                    flat.append(b.split("[")[0])  # strip properties
    counts = Counter(flat)
    print("\n  Materials needed:")
    for mat, count in counts.most_common():
        name = mat.replace("minecraft:", "")
        print(f"    {name}: {count}")

    return counts


def main():
    blocks, W, H, D = create_house()

    schem_dir = "/home/sbx_0cr8vKWlxLWU/minecraft_bot/client/gameDir/schematics"
    import os
    os.makedirs(schem_dir, exist_ok=True)

    counts = write_schematic(blocks, W, H, D, f"{schem_dir}/house.schem")
    return counts


if __name__ == "__main__":
    main()
