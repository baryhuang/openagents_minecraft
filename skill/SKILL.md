---
name: minecraft-bot
description: Use when the user wants to set up a Minecraft Java bot with Baritone, control a Minecraft bot via API, build structures in Minecraft, or automate Minecraft gameplay with visible client UI. Triggers on "minecraft bot", "baritone", "mine blocks", "build house", "minecraft automation".
argument-hint: <setup|status|goto|mine|build|stop|command> [args...]
user-invocable: true
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch]
---

# Minecraft Baritone Bot Skill

Control a Minecraft Java Edition client via Baritone pathfinding + HTTP API.
All actions are visible in the real Minecraft client UI (not headless).

## Architecture

```
External Script ──► HTTP API (port 8655) ──► Fabric Mod ──► Baritone ──► Minecraft Client UI
```

## Success Path (Proven Steps)

### Phase 1: One-Time Setup

Only run these steps if the infrastructure isn't already running.

#### 1. Install Fabric Loader

```bash
# Download Fabric installer
curl -L -o /tmp/fabric-installer.jar \
  "https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.1.1/fabric-installer-1.1.1.jar"

# Create launcher profile (required before install)
GAME_DIR="<path>/client/gameDir"
echo '{"profiles":{},"selectedProfile":"","authenticationDatabase":{}}' > "$GAME_DIR/launcher_profiles.json"

# Install Fabric (substitute your MC version)
java -jar /tmp/fabric-installer.jar client \
  -mcversion 1.21.5 -dir "$GAME_DIR" -loader 0.18.5
```

#### 2. Download Mods

Place these JARs in `$GAME_DIR/mods/`:

| Mod | Source | Purpose |
|-----|--------|---------|
| Baritone API Fabric | [GitHub releases](https://github.com/cabaletta/baritone/releases) | Pathfinding + automation |
| Fabric API | [Modrinth API](https://api.modrinth.com/v2/project/P7dR8mSH/version) | Mod framework |
| Baritone Control Mod | Build from source (see below) | HTTP API bridge |

**Get download URLs programmatically:**
```bash
# Fabric API (substitute game version)
curl -s "https://api.modrinth.com/v2/project/P7dR8mSH/version?game_versions=%5B%221.21.5%22%5D&loaders=%5B%22fabric%22%5D" \
  | python3 -c "import json,sys; v=json.load(sys.stdin)[0]; print(v['files'][0]['url'])"
```

#### 3. Build the Control Mod

The control mod exposes an HTTP server on port 8655 inside the Minecraft client.

**Key files:**
- `build.gradle` — Fabric Loom + Baritone API dependency
- `BaritoneControlMod.java` — Client initializer, tick queue, starts HTTP server
- `HttpControlServer.java` — HTTP endpoints that delegate to Baritone API
- `fabric.mod.json` — Mod metadata

**Critical patterns in HttpControlServer.java:**

```java
// All HTTP handlers must run on the main thread via tick queue:
private <T> T runOnTick(Supplier<T> action) throws Exception {
    CompletableFuture<T> future = new CompletableFuture<>();
    BaritoneControlMod.TICK_QUEUE.add(() -> {
        try { future.complete(action.get()); }
        catch (Exception e) { future.completeExceptionally(e); }
    });
    return future.get(5, TimeUnit.SECONDS);
}

// Baritone API access (avoid 'var' with baritone package name):
baritone.api.IBaritone bari = baritone.api.BaritoneAPI.getProvider().getPrimaryBaritone();
bari.getCustomGoalProcess().setGoalAndPath(new baritone.api.pathing.goals.GoalBlock(x, y, z));
bari.getCommandManager().execute("mine diamond_ore");
```

**Build:**
```bash
# Requires Gradle 8.x + Java 21
./gradlew build
cp build/libs/baritone-control-mod-1.0.0.jar "$GAME_DIR/mods/"
```

#### 4. Build Classpath & Launch Script

**Classpath generation (Python):**
- Parse Fabric version JSON for Fabric libraries
- Parse vanilla version JSON for MC libraries
- **Exclude vanilla ASM jars** that duplicate Fabric's newer versions
- Write joined classpath to file

**CRITICAL: Deduplicate ASM jars.** Fabric brings ASM 9.9, vanilla has ASM 9.6. If both are on classpath, you get `IllegalStateException: duplicate ASM classes`.

```python
# Track fabric artifact group:name, skip vanilla duplicates
fabric_artifacts = set()
for lib in fabric_libs:
    parts = lib["name"].split(":")
    fabric_artifacts.add(f"{parts[0]}:{parts[1]}")

for lib in vanilla_libs:
    parts = lib["name"].split(":")
    if f"{parts[0]}:{parts[1]}" in fabric_artifacts:
        continue  # SKIP - fabric has newer version
    cp.append(resolve_path(lib))
```

**Launch command:**
```bash
java -Xmx2G -Djava.library.path="$NATIVES_DIR" \
  -cp "$CLASSPATH" \
  net.fabricmc.loader.impl.launch.knot.KnotClient \
  --username "BotName" \
  --version "fabric-loader-0.18.5-1.21.5" \
  --gameDir "$GAME_DIR" \
  --assetsDir "$ASSETS_DIR" \
  --assetIndex 24 \
  --accessToken 0 --userType legacy
```

#### 5. Server Configuration

The MC server MUST have:
```properties
online-mode=false
enforce-secure-profile=false
```

Without `enforce-secure-profile=false`, the client gets "Invalid Session" errors.

#### 6. Connect to Server

Navigate UI with keyboard (Tab + Enter) — NOT mouse coordinates (Minecraft uses GLFW, not X11 coords):
```
Title Screen → Tab Tab Enter (Multiplayer) → Tab Tab Enter (Proceed warning) → Tab Enter (Join Server)
```

Use `python-xlib` for X11 input if xdotool is unavailable.

---

### Phase 2: Control the Bot

#### HTTP API Endpoints (port 8655)

| Endpoint | Body | Action |
|----------|------|--------|
| `GET /status` | — | Position, health, food, baritone state |
| `POST /goto` | `x y z` | Baritone pathfind to coordinates |
| `POST /mine` | `block_name` | Baritone auto-mine (e.g., `oak_log`) |
| `POST /command` | `cmd` | Any Baritone command (`explore`, `farm`, `build schematic.schem x y z`) |
| `POST /stop` | — | Stop all Baritone processes |
| `POST /chat` | `message` | Send chat message or `/command` |
| `POST /look` | `yaw pitch` | Change view direction |
| `GET /inventory` | — | List inventory items |
| `GET /health` | — | Health, food, armor, XP |
| `POST /attack` | — | Attack entity in crosshair |
| `POST /place` | — | Use item / place block at crosshair |

**Python control example:**
```python
import urllib.request, json
def api(endpoint, data=None):
    req = urllib.request.Request(f"http://localhost:8655/{endpoint}")
    body = data.encode() if data else b""
    with urllib.request.urlopen(req, body, timeout=10) as r:
        return json.loads(r.read())

api("goto", "100 64 200")      # Navigate
api("command", "mine oak_log")  # Mine
api("stop")                     # Stop
```

#### RCON for Server Commands

Use RCON (port 25575) for commands the client can't execute:
```python
# Give items, change gamemode, teleport, fill/setblock
rcon("give BotName diamond_pickaxe 1")
rcon("gamemode survival BotName")
rcon("fill x1 y1 z1 x2 y2 z2 oak_planks")
```

#### Building with Schematics

1. Generate a Sponge Schematic v2 (`.schem`) file — NBT format, GZip compressed
2. Place in `$GAME_DIR/schematics/`
3. Give bot materials: `rcon("give BotName oak_planks 64")` etc.
4. Run: `api("command", "build house.schem 100 64 200")`
5. Baritone places blocks one-by-one like a human player
6. **Note:** Baritone handles simple blocks well (planks, stone, logs) but struggles with directional blocks (stairs, doors, beds) in survival — finish those via RCON `/setblock`

#### JsMacros Integration

JsMacrosCE can run JavaScript inside the client with Baritone access:
```javascript
const API = Java.type("baritone.api.BaritoneAPI");
const baritone = API.getProvider().getPrimaryBaritone();
baritone.getCommandManager().execute("mine oak_log");
baritone.getCustomGoalProcess().setGoalAndPath(new GoalBlock(x, y, z));
```

Scripts go in `$GAME_DIR/config/jsMacros/Macros/`. Trigger via JsMacros keybind (J key).

---

## Gotchas & Lessons Learned

1. **ASM duplication** — Always filter vanilla ASM jars from classpath when Fabric is present
2. **`var` keyword** — Never use `var baritone = baritone.api...` (self-referencing). Use explicit type: `baritone.api.IBaritone bari = ...`
3. **Private methods** — `MinecraftClient.doItemUse()` is private. Use `mc.interactionManager.interactBlock()` instead
4. **Tick thread** — All game state access MUST happen on the render/client tick thread via CompletableFuture queue
5. **Invalid Session** — Requires BOTH `online-mode=false` AND `enforce-secure-profile=false` on server
6. **Mouse clicks** — Don't use screen coordinates for MC menus. Use Tab/Enter keyboard navigation instead
7. **Baritone build limits** — Baritone places simple blocks well but pauses when missing materials. Complex directional blocks (stairs, doors) often need RCON `/setblock` fallback
8. **Creative mode** — Baritone build pauses in creative. Use survival mode for `#build`
9. **Food** — Bot gets hungry during long tasks. Monitor food level via `/health` endpoint
