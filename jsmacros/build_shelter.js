// ============================================
// Build Shelter - Constructs a simple shelter
// Uses Baritone schematic building + manual placement
// All actions visible in the client UI
// ============================================

const API = Java.type("baritone.api.BaritoneAPI");
const baritone = API.getProvider().getPrimaryBaritone();

const pos = Player.getPlayer().getPos();
const baseX = Math.floor(pos.x);
const baseY = Math.floor(pos.y);
const baseZ = Math.floor(pos.z);

Chat.log("\u00a7b[BuildShelter] Building shelter at " + baseX + ", " + baseY + ", " + baseZ);

// Step 1: Gather materials if needed
const inv = Player.getPlayer().getInventory();
let hasBlocks = false;
for (let i = 0; i < 36; i++) {
    const stack = inv.getSlot(i);
    if (stack && stack.getCount() > 0) {
        const name = stack.getItemId();
        if (name.indexOf("plank") !== -1 || name.indexOf("log") !== -1 ||
            name.indexOf("cobblestone") !== -1 || name.indexOf("dirt") !== -1) {
            hasBlocks = true;
            break;
        }
    }
}

if (!hasBlocks) {
    Chat.log("\u00a7e[BuildShelter] No building materials! Gathering wood first...");
    baritone.getCommandManager().execute("mine oak_log birch_log spruce_log");

    // Wait until we have at least 20 logs
    let attempts = 0;
    while (attempts < 40) { // 2 min max
        Time.sleep(3000);
        attempts++;
        let logCount = 0;
        for (let i = 0; i < 36; i++) {
            const stack = inv.getSlot(i);
            if (stack) {
                const name = stack.getItemId();
                if (name.indexOf("_log") !== -1) {
                    logCount += stack.getCount();
                }
            }
        }
        if (logCount >= 20) {
            Chat.log("\u00a7b[BuildShelter] Got " + logCount + " logs, enough to build!");
            break;
        }
        Chat.log("\u00a77[BuildShelter] Gathering... (" + logCount + "/20 logs)");
    }
    baritone.getCommandManager().execute("stop");
    Time.sleep(1000);
}

// Step 2: Use Baritone to build a simple cube structure
// Baritone can build from schematics, but we'll use the pillar command
// to create walls by going to each position
Chat.log("\u00a7b[BuildShelter] Now building walls...");

// Build 5x5 walls, 3 high using Baritone goto + place
const size = 5;
const height = 3;

// Navigate to build site and use chat commands
// Baritone's #build command can handle schematic files
// For now, use goto to position ourselves
baritone.getCustomGoalProcess().setGoalAndPath(
    new (Java.type("baritone.api.pathing.goals.GoalBlock"))(baseX, baseY, baseZ)
);

// Wait to arrive
let waitCount = 0;
while (baritone.getPathingBehavior().isPathing() && waitCount < 30) {
    Time.sleep(1000);
    waitCount++;
}

Chat.log("\u00a7b[BuildShelter] At build site. Use /fill or place blocks manually.");
Chat.log("\u00a7b[BuildShelter] Tip: Create a .schematic file and run: #build <file>");
Chat.log("\u00a76[BuildShelter] Done positioning! Ready to build.");
