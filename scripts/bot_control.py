#!/usr/bin/env python3
"""
Minecraft Bot Control via Baritone HTTP API

The Minecraft Java client runs with Fabric + Baritone + our control mod.
This script sends commands to the bot via HTTP on port 8655.
All actions are performed in the real client — visible in the game UI.

Usage:
    python3 bot_control.py status
    python3 bot_control.py goto 100 64 200
    python3 bot_control.py mine diamond_ore
    python3 bot_control.py chat "hello world"
    python3 bot_control.py command "explore"
    python3 bot_control.py stop
    python3 bot_control.py look 90 0
    python3 bot_control.py inventory
    python3 bot_control.py health
    python3 bot_control.py attack
    python3 bot_control.py place
"""

import sys
import json
import urllib.request
import urllib.error

API_BASE = "http://localhost:8655"


def api_call(endpoint, data=None):
    url = f"{API_BASE}/{endpoint}"
    req = urllib.request.Request(url)
    body = data.encode("utf-8") if data else b""
    try:
        with urllib.request.urlopen(req, body, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"status": "error", "message": f"Connection failed: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def print_result(result):
    print(json.dumps(result, indent=2))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "status":
        print_result(api_call("status"))

    elif cmd == "goto":
        if len(sys.argv) < 5:
            print("Usage: bot_control.py goto x y z")
            return
        coords = f"{sys.argv[2]} {sys.argv[3]} {sys.argv[4]}"
        print_result(api_call("goto", coords))

    elif cmd == "mine":
        if len(sys.argv) < 3:
            print("Usage: bot_control.py mine <block_name>")
            return
        print_result(api_call("mine", sys.argv[2]))

    elif cmd == "chat":
        if len(sys.argv) < 3:
            print("Usage: bot_control.py chat <message>")
            return
        print_result(api_call("chat", " ".join(sys.argv[2:])))

    elif cmd == "command":
        if len(sys.argv) < 3:
            print("Usage: bot_control.py command <baritone_command>")
            return
        print_result(api_call("command", " ".join(sys.argv[2:])))

    elif cmd == "stop":
        print_result(api_call("stop"))

    elif cmd == "look":
        if len(sys.argv) < 4:
            print("Usage: bot_control.py look <yaw> <pitch>")
            return
        print_result(api_call("look", f"{sys.argv[2]} {sys.argv[3]}"))

    elif cmd == "inventory":
        print_result(api_call("inventory"))

    elif cmd == "health":
        print_result(api_call("health"))

    elif cmd == "attack":
        print_result(api_call("attack"))

    elif cmd == "place":
        print_result(api_call("place"))

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
