#!/bin/bash
# Launch Minecraft 1.21.5 with Fabric + Baritone + Control Mod
# The client UI will be visible and controllable via HTTP API on port 8655

CLIENT_DIR="/home/sbx_0cr8vKWlxLWU/minecraft_bot/client"
GAME_DIR="$CLIENT_DIR/gameDir"
NATIVES_DIR="$CLIENT_DIR/natives"
ASSETS_DIR="$CLIENT_DIR/assets"

# Read classpath from generated file
CLASSPATH=$(cat "$CLIENT_DIR/fabric_classpath.txt")

# Player name (offline mode)
PLAYER_NAME="${1:-BaritoneBot}"

echo "=== Launching Minecraft 1.21.5 Fabric Client ==="
echo "Player: $PLAYER_NAME"
echo "Game Dir: $GAME_DIR"
echo "Mods: $(ls $GAME_DIR/mods/)"
echo "HTTP Control API will be on port 8655"
echo "================================================="

exec java \
  -Xmx2G \
  -Xms512M \
  -Djava.library.path="$NATIVES_DIR" \
  -Dorg.lwjgl.util.Debug=true \
  -cp "$CLASSPATH" \
  net.fabricmc.loader.impl.launch.knot.KnotClient \
  --username "$PLAYER_NAME" \
  --version "fabric-loader-0.18.5-1.21.5" \
  --gameDir "$GAME_DIR" \
  --assetsDir "$ASSETS_DIR" \
  --assetIndex 24 \
  --accessToken 0 \
  --userType legacy \
  2>&1 | tee "$CLIENT_DIR/fabric_client.log"
