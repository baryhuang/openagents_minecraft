#!/usr/bin/env python3
"""
Build a single family house in Minecraft using RCON commands.
The house is built block-by-block visible in the client UI.
"""

import socket
import struct
import time
import json
import urllib.request

RCON_HOST = "localhost"
RCON_PORT = 25575
RCON_PASS = "claude123"
API_BASE = "http://localhost:8655"

class RCON:
    def __init__(self, host, port, password):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self._send(1, 3, password)
        self._recv()

    def cmd(self, command):
        self._send(2, 2, command)
        return self._recv()

    def _send(self, req_id, ptype, payload):
        data = struct.pack('<ii', req_id, ptype) + payload.encode() + b'\x00\x00'
        self.sock.send(struct.pack('<i', len(data)) + data)

    def _recv(self):
        size = struct.unpack('<i', self.sock.recv(4))[0]
        data = self.sock.recv(size)
        return data[8:-2].decode()

    def close(self):
        self.sock.close()


def bot_api(endpoint, data=None):
    req = urllib.request.Request(f"{API_BASE}/{endpoint}")
    body = data.encode() if data else b""
    with urllib.request.urlopen(req, body, timeout=10) as resp:
        return json.loads(resp.read().decode())


def fill(rcon, x1, y1, z1, x2, y2, z2, block, replace=None):
    cmd = f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block}"
    if replace:
        cmd += f" replace {replace}"
    return rcon.cmd(cmd)


def setblock(rcon, x, y, z, block):
    return rcon.cmd(f"setblock {x} {y} {z} {block}")


def build_house(rcon, bx, by, bz):
    """
    Build a single family house at position (bx, by, bz).
    House is 11 wide (x) x 9 deep (z) x 6 tall (y).
    Features: living room, bedroom, kitchen, bathroom, porch, roof.
    """
    print("=== Building Single Family House ===")
    print(f"Location: {bx}, {by}, {bz}")

    # Dimensions
    W, D, H = 11, 9, 5  # width, depth, wall height

    # ---- STEP 1: Clear area and lay foundation ----
    print("[1/8] Clearing area and laying foundation...")
    # Clear above
    fill(rcon, bx-1, by, bz-1, bx+W+1, by+H+4, bz+D+1, "air")
    # Foundation - stone bricks
    fill(rcon, bx, by-1, bz, bx+W, by-1, bz+D, "stone_bricks")
    # Floor - oak planks
    fill(rcon, bx, by, bz, bx+W, by, bz+D, "oak_planks")
    time.sleep(0.5)

    # ---- STEP 2: Walls ----
    print("[2/8] Building walls...")
    # Front wall (z = bz)
    fill(rcon, bx, by+1, bz, bx+W, by+H, bz, "oak_planks")
    # Back wall (z = bz+D)
    fill(rcon, bx, by+1, bz+D, bx+W, by+H, bz+D, "oak_planks")
    # Left wall (x = bx)
    fill(rcon, bx, by+1, bz, bx, by+H, bz+D, "oak_planks")
    # Right wall (x = bx+W)
    fill(rcon, bx+W, by+1, bz, bx+W, by+H, bz+D, "oak_planks")
    time.sleep(0.5)

    # ---- STEP 3: Interior (hollow out) ----
    print("[3/8] Hollowing interior...")
    fill(rcon, bx+1, by+1, bz+1, bx+W-1, by+H-1, bz+D-1, "air")
    time.sleep(0.3)

    # ---- STEP 4: Interior dividing wall ----
    print("[4/8] Adding interior walls...")
    # Divider wall at z = bz+5 (splits into front rooms / back rooms)
    fill(rcon, bx+1, by+1, bz+5, bx+W-1, by+H-1, bz+5, "stripped_oak_log")
    # Doorway in divider
    fill(rcon, bx+3, by+1, bz+5, bx+4, by+2, bz+5, "air")
    fill(rcon, bx+7, by+1, bz+5, bx+8, by+2, bz+5, "air")

    # Side divider for bedroom vs bathroom (back section)
    fill(rcon, bx+6, by+1, bz+6, bx+6, by+H-1, bz+D-1, "stripped_oak_log")
    fill(rcon, bx+6, by+1, bz+7, bx+6, by+2, bz+7, "air")  # doorway
    time.sleep(0.3)

    # ---- STEP 5: Windows ----
    print("[5/8] Adding windows...")
    # Front windows
    fill(rcon, bx+2, by+2, bz, bx+3, by+3, bz, "glass_pane")
    fill(rcon, bx+7, by+2, bz, bx+8, by+3, bz, "glass_pane")
    # Back windows
    fill(rcon, bx+2, by+2, bz+D, bx+3, by+3, bz+D, "glass_pane")
    fill(rcon, bx+8, by+2, bz+D, bx+9, by+3, bz+D, "glass_pane")
    # Side windows
    fill(rcon, bx, by+2, bz+3, bx, by+3, bz+4, "glass_pane")
    fill(rcon, bx+W, by+2, bz+3, bx+W, by+3, bz+4, "glass_pane")
    fill(rcon, bx, by+2, bz+7, bx, by+3, bz+7, "glass_pane")
    fill(rcon, bx+W, by+2, bz+7, bx+W, by+3, bz+7, "glass_pane")
    time.sleep(0.3)

    # ---- STEP 6: Door ----
    print("[6/8] Adding front door and porch...")
    # Front door (center of front wall)
    fill(rcon, bx+5, by+1, bz, bx+5, by+2, bz, "air")
    setblock(rcon, bx+5, by+1, bz, "oak_door[facing=south,half=lower,open=false]")
    setblock(rcon, bx+5, by+2, bz, "oak_door[facing=south,half=upper,open=false]")

    # Porch - cobblestone slab steps
    fill(rcon, bx+3, by, bz-1, bx+7, by, bz-1, "cobblestone_slab")
    fill(rcon, bx+4, by-1, bz-2, bx+6, by-1, bz-2, "cobblestone")
    # Porch pillars
    fill(rcon, bx+3, by+1, bz-1, bx+3, by+3, bz-1, "oak_fence")
    fill(rcon, bx+7, by+1, bz-1, bx+7, by+3, bz-1, "oak_fence")
    # Porch roof
    fill(rcon, bx+3, by+4, bz-1, bx+7, by+4, bz-1, "oak_slab")

    # Back door
    fill(rcon, bx+5, by+1, bz+D, bx+5, by+2, bz+D, "air")
    setblock(rcon, bx+5, by+1, bz+D, "oak_door[facing=north,half=lower,open=false]")
    setblock(rcon, bx+5, by+2, bz+D, "oak_door[facing=north,half=upper,open=false]")
    time.sleep(0.3)

    # ---- STEP 7: Roof ----
    print("[7/8] Building roof...")
    # Ceiling
    fill(rcon, bx, by+H, bz, bx+W, by+H, bz+D, "oak_planks")

    # Peaked roof with stairs
    for i in range(0, 7):
        ry = by + H + 1 + i
        rx1 = bx - 1 + i
        rx2 = bx + W + 1 - i
        if rx1 >= rx2:
            # Peak
            fill(rcon, rx1, ry, bz-1, rx1, ry, bz+D+1, "dark_oak_slab[type=bottom]")
            break
        fill(rcon, rx1, ry, bz-1, rx1, ry, bz+D+1, "dark_oak_stairs[facing=east,half=bottom]")
        fill(rcon, rx2, ry, bz-1, rx2, ry, bz+D+1, "dark_oak_stairs[facing=west,half=bottom]")
    time.sleep(0.3)

    # ---- STEP 8: Interior furniture ----
    print("[8/8] Furnishing interior...")

    # LIVING ROOM (front-left: bx+1..bx+5, bz+1..bz+4)
    # Couch (stairs as seats)
    fill(rcon, bx+1, by+1, bz+3, bx+3, by+1, bz+3, "oak_stairs[facing=south]")
    # Table
    setblock(rcon, bx+2, by+1, bz+2, "oak_fence")
    setblock(rcon, bx+2, by+2, bz+2, "oak_pressure_plate")
    # Carpet
    fill(rcon, bx+1, by+1, bz+1, bx+4, by+1, bz+1, "red_carpet")
    fill(rcon, bx+1, by+1, bz+2, bx+1, by+1, bz+2, "red_carpet")
    # Bookshelf
    fill(rcon, bx+1, by+1, bz+4, bx+1, by+3, bz+4, "bookshelf")
    # Fireplace
    setblock(rcon, bx+4, by+1, bz+4, "campfire[lit=true]")
    setblock(rcon, bx+4, by+2, bz+4, "stone_brick_wall")
    setblock(rcon, bx+4, by+3, bz+4, "stone_brick_wall")

    # KITCHEN (front-right: bx+6..bx+W-1, bz+1..bz+4)
    # Counter
    fill(rcon, bx+7, by+1, bz+1, bx+W-1, by+1, bz+1, "smooth_stone_slab[type=double]")
    setblock(rcon, bx+7, by+1, bz+1, "crafting_table")
    setblock(rcon, bx+8, by+1, bz+1, "furnace[facing=south]")
    setblock(rcon, bx+9, by+1, bz+1, "smoker[facing=south]")
    # Sink (cauldron)
    setblock(rcon, bx+W-1, by+1, bz+2, "cauldron")
    # Dining table
    setblock(rcon, bx+7, by+1, bz+3, "oak_fence")
    setblock(rcon, bx+7, by+2, bz+3, "oak_pressure_plate")
    setblock(rcon, bx+8, by+1, bz+3, "oak_fence")
    setblock(rcon, bx+8, by+2, bz+3, "oak_pressure_plate")
    # Chairs
    setblock(rcon, bx+7, by+1, bz+2, "oak_stairs[facing=south]")
    setblock(rcon, bx+8, by+1, bz+2, "oak_stairs[facing=south]")
    setblock(rcon, bx+7, by+1, bz+4, "oak_stairs[facing=north]")
    setblock(rcon, bx+8, by+1, bz+4, "oak_stairs[facing=north]")
    # Chest for storage
    setblock(rcon, bx+W-1, by+1, bz+4, "chest[facing=west]")

    # BEDROOM (back-left: bx+1..bx+5, bz+6..bz+D-1)
    # Bed
    setblock(rcon, bx+1, by+1, bz+D-1, "red_bed[facing=south,part=head]")
    setblock(rcon, bx+1, by+1, bz+D-2, "red_bed[facing=south,part=foot]")
    setblock(rcon, bx+2, by+1, bz+D-1, "red_bed[facing=south,part=head]")
    setblock(rcon, bx+2, by+1, bz+D-2, "red_bed[facing=south,part=foot]")
    # Nightstand
    setblock(rcon, bx+3, by+1, bz+D-1, "oak_trapdoor[facing=south,half=top,open=false]")
    setblock(rcon, bx+3, by+2, bz+D-1, "lantern[hanging=false]")
    # Wardrobe (barrels)
    fill(rcon, bx+5, by+1, bz+D-1, bx+5, by+3, bz+D-1, "barrel[facing=west]")
    # Carpet
    fill(rcon, bx+1, by+1, bz+6, bx+4, by+1, bz+6, "white_carpet")
    fill(rcon, bx+1, by+1, bz+7, bx+4, by+1, bz+7, "white_carpet")

    # BATHROOM (back-right: bx+7..bx+W-1, bz+6..bz+D-1)
    # "Bathtub" - cauldrons
    setblock(rcon, bx+W-1, by+1, bz+D-1, "water_cauldron[level=3]")
    setblock(rcon, bx+W-2, by+1, bz+D-1, "water_cauldron[level=3]")
    # Toilet (hopper)
    setblock(rcon, bx+W-1, by+1, bz+6, "hopper[facing=down]")
    # Mirror (item frame would need entity, use glass)
    setblock(rcon, bx+W-1, by+2, bz+7, "glass_pane")
    # Bathroom floor
    fill(rcon, bx+7, by, bz+6, bx+W-1, by, bz+D-1, "smooth_stone")

    # ---- LIGHTING ----
    # Torches inside
    setblock(rcon, bx+1, by+3, bz+1, "wall_torch[facing=south]")
    setblock(rcon, bx+W-1, by+3, bz+1, "wall_torch[facing=south]")
    setblock(rcon, bx+1, by+3, bz+D-1, "wall_torch[facing=north]")
    setblock(rcon, bx+W-1, by+3, bz+D-1, "wall_torch[facing=north]")
    # Lantern on porch
    setblock(rcon, bx+5, by+3, bz-1, "lantern[hanging=true]")

    # ---- EXTERIOR DETAILS ----
    # Flower pots on front
    setblock(rcon, bx+2, by+1, bz-1, "potted_red_tulip")
    setblock(rcon, bx+8, by+1, bz-1, "potted_blue_orchid")
    # Path to front door
    fill(rcon, bx+5, by-1, bz-3, bx+5, by-1, bz-2, "gravel")
    # Fence around yard
    fill(rcon, bx-2, by+1, bz-3, bx+W+2, by+1, bz-3, "oak_fence")
    fill(rcon, bx-2, by+1, bz+D+2, bx+W+2, by+1, bz+D+2, "oak_fence")
    fill(rcon, bx-2, by+1, bz-3, bx-2, by+1, bz+D+2, "oak_fence")
    fill(rcon, bx+W+2, by+1, bz-3, bx+W+2, by+1, bz+D+2, "oak_fence")
    # Gate
    setblock(rcon, bx+5, by+1, bz-3, "oak_fence_gate[facing=south,open=false]")

    print("\n=== House Complete! ===")
    print(f"Front door at: {bx+5}, {by+1}, {bz}")
    print("Rooms: Living Room, Kitchen, Bedroom, Bathroom")
    print("Features: Porch, Peaked Roof, Fireplace, Furniture, Yard Fence")


def main():
    # Get bot position
    status = bot_api("status")
    bx = int(status["x"])
    by = int(status["y"])
    bz = int(status["z"])

    # Build house 5 blocks in front of bot
    house_x = bx + 5
    house_y = by
    house_z = bz

    print(f"Bot at: {bx}, {by}, {bz}")
    print(f"Building house at: {house_x}, {house_y}, {house_z}")

    rcon = RCON(RCON_HOST, RCON_PORT, RCON_PASS)

    try:
        build_house(rcon, house_x, house_y, house_z)

        # Move bot to look at the house
        print("\nMoving bot to admire the house...")
        bot_api("goto", f"{house_x+5} {house_y+1} {house_z-5}")
    finally:
        rcon.close()


if __name__ == "__main__":
    main()
