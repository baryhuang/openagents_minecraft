#!/bin/bash
# Minecraft Baritone Bot - One-shot installer
# Installs Fabric + Baritone + Control Mod for a given MC client directory
#
# Usage: ./install.sh <client_dir> <mc_version> [player_name]
# Example: ./install.sh /home/user/minecraft_bot/client 1.21.5 BaritoneBot

set -e

CLIENT_DIR="${1:?Usage: install.sh <client_dir> <mc_version> [player_name]}"
MC_VERSION="${2:?Provide MC version (e.g., 1.21.5)}"
PLAYER_NAME="${3:-BaritoneBot}"
GAME_DIR="$CLIENT_DIR/gameDir"
MODS_DIR="$GAME_DIR/mods"
SCHEMATICS_DIR="$GAME_DIR/schematics"

echo "=== Minecraft Baritone Bot Installer ==="
echo "Client dir: $CLIENT_DIR"
echo "MC version: $MC_VERSION"
echo "Player: $PLAYER_NAME"

# --- Step 1: Fabric Installer ---
echo "[1/5] Installing Fabric loader..."
mkdir -p "$MODS_DIR" "$SCHEMATICS_DIR"
FABRIC_INSTALLER="/tmp/fabric-installer.jar"
if [ ! -f "$FABRIC_INSTALLER" ]; then
    curl -sL -o "$FABRIC_INSTALLER" \
        "https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.1.1/fabric-installer-1.1.1.jar"
fi
echo '{"profiles":{},"selectedProfile":"","authenticationDatabase":{}}' > "$GAME_DIR/launcher_profiles.json"
java -jar "$FABRIC_INSTALLER" client -mcversion "$MC_VERSION" -dir "$GAME_DIR" -loader 0.18.5

# --- Step 2: Detect Fabric loader version ---
FABRIC_VERSION_DIR=$(ls -d "$GAME_DIR/versions/fabric-loader-"* 2>/dev/null | head -1)
FABRIC_VERSION=$(basename "$FABRIC_VERSION_DIR")
echo "Fabric version: $FABRIC_VERSION"

# --- Step 3: Download mods ---
echo "[2/5] Downloading Baritone..."
BARITONE_URL=$(curl -sL "https://api.github.com/repos/cabaletta/baritone/releases" | \
    python3 -c "
import json,sys
for r in json.load(sys.stdin):
    if '$MC_VERSION' in r.get('name','') or '$MC_VERSION' in r.get('body',''):
        for a in r['assets']:
            if 'api-fabric' in a['name']:
                print(a['browser_download_url']); sys.exit()
")
if [ -n "$BARITONE_URL" ]; then
    curl -sL -o "$MODS_DIR/baritone-api-fabric.jar" "$BARITONE_URL"
    echo "  Downloaded: $BARITONE_URL"
else
    echo "  WARNING: Could not find Baritone for $MC_VERSION. Download manually."
fi

echo "[3/5] Downloading Fabric API..."
FABRIC_API_URL=$(curl -s "https://api.modrinth.com/v2/project/P7dR8mSH/version?game_versions=%5B%22$MC_VERSION%22%5D&loaders=%5B%22fabric%22%5D" | \
    python3 -c "import json,sys; print(json.load(sys.stdin)[0]['files'][0]['url'])")
curl -sL -o "$MODS_DIR/fabric-api.jar" "$FABRIC_API_URL"
echo "  Downloaded: $FABRIC_API_URL"

# --- Step 4: Build control mod (if source exists) ---
echo "[4/5] Control mod..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MOD_DIR="$SCRIPT_DIR/../baritone-control-mod"
if [ -d "$MOD_DIR" ] && [ -f "$MOD_DIR/build.gradle" ]; then
    echo "  Building from source..."
    cd "$MOD_DIR"
    if [ -f "./gradlew" ]; then
        ./gradlew build -q
    else
        echo "  Run 'gradle wrapper && ./gradlew build' in $MOD_DIR first"
    fi
    cp "$MOD_DIR/build/libs/baritone-control-mod-1.0.0.jar" "$MODS_DIR/" 2>/dev/null || true
fi
if [ -f "$MODS_DIR/baritone-control-mod-1.0.0.jar" ]; then
    echo "  Control mod installed."
else
    echo "  WARNING: Control mod not found. Build it from baritone-control-mod/ directory."
fi

# --- Step 5: Generate classpath ---
echo "[5/5] Generating launch classpath..."
python3 - "$CLIENT_DIR" "$GAME_DIR" "$FABRIC_VERSION" <<'PYEOF'
import json, os, sys

client_dir, game_dir, fabric_ver = sys.argv[1], sys.argv[2], sys.argv[3]
lib_dir = f"{client_dir}/libraries"
fabric_lib_dir = f"{game_dir}/libraries"

with open(f"{game_dir}/versions/{fabric_ver}/{fabric_ver}.json") as f:
    fabric = json.load(f)
with open(f"{client_dir}/version.json") as f:
    vanilla = json.load(f)

def m2p(name):
    p = name.split(":")
    if len(p) >= 3:
        return f"{p[0].replace('.','/')}/{p[1]}/{p[2]}/{p[1]}-{p[2]}.jar"

fabric_arts = set()
cp = []
for lib in fabric.get("libraries", []):
    p = lib["name"].split(":")
    if len(p) >= 3: fabric_arts.add(f"{p[0]}:{p[1]}")
    path = m2p(lib["name"])
    if path:
        for base in [fabric_lib_dir, lib_dir]:
            if os.path.exists(f"{base}/{path}"):
                cp.append(f"{base}/{path}"); break

for lib in vanilla.get("libraries", []):
    p = lib["name"].split(":")
    if len(p) >= 3 and f"{p[0]}:{p[1]}" in fabric_arts: continue
    dl = lib.get("downloads",{}).get("artifact",{})
    path = dl.get("path","")
    if path and os.path.exists(f"{lib_dir}/{path}"):
        cp.append(f"{lib_dir}/{path}")

cp.append(f"{client_dir}/client.jar")
with open(f"{client_dir}/fabric_classpath.txt","w") as f:
    f.write(":".join(cp))
print(f"  {len(cp)} classpath entries")
PYEOF

echo ""
echo "=== Installation Complete ==="
echo "Launch with:"
echo "  java -Xmx2G -Djava.library.path=\"$CLIENT_DIR/natives\" \\"
echo "    -cp \"\$(cat $CLIENT_DIR/fabric_classpath.txt)\" \\"
echo "    net.fabricmc.loader.impl.launch.knot.KnotClient \\"
echo "    --username \"$PLAYER_NAME\" --version \"$FABRIC_VERSION\" \\"
echo "    --gameDir \"$GAME_DIR\" --assetsDir \"$CLIENT_DIR/assets\" \\"
echo "    --assetIndex 24 --accessToken 0 --userType legacy"
echo ""
echo "HTTP API will be on port 8655 once in-game."
