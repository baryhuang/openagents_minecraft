// ============================================
// Gather Wood - Automated tree farming
// Uses Baritone to find and chop trees,
// visible in the client UI as human-like actions
// ============================================

const API = Java.type("baritone.api.BaritoneAPI");
const baritone = API.getProvider().getPrimaryBaritone();
const settings = API.getSettings();

// Config
const LOGS_TO_COLLECT = 32;
const LOG_TYPES = ["oak_log", "birch_log", "spruce_log", "dark_oak_log", "acacia_log", "jungle_log"];

Chat.log("\u00a7a[GatherWood] Starting wood gathering...");
Chat.log("\u00a7a[GatherWood] Target: " + LOGS_TO_COLLECT + " logs");

// Enable human-like settings
settings.allowSprint.value = true;
settings.allowParkour.value = true;

// Start mining logs
baritone.getCommandManager().execute("mine " + LOG_TYPES.join(" "));
Chat.log("\u00a7a[GatherWood] Baritone mining started - searching for trees...");

// Monitor progress
let lastCount = 0;
while (true) {
    Time.sleep(3000);

    // Count logs in inventory
    const inv = Player.getPlayer().getInventory();
    let logCount = 0;
    for (let i = 0; i < 36; i++) {
        const stack = inv.getSlot(i);
        if (stack) {
            const name = stack.getItemId();
            for (let j = 0; j < LOG_TYPES.length; j++) {
                if (name.indexOf(LOG_TYPES[j]) !== -1) {
                    logCount += stack.getCount();
                }
            }
        }
    }

    if (logCount !== lastCount) {
        Chat.log("\u00a7a[GatherWood] Collected " + logCount + "/" + LOGS_TO_COLLECT + " logs");
        lastCount = logCount;
    }

    if (logCount >= LOGS_TO_COLLECT) {
        baritone.getCommandManager().execute("stop");
        Chat.log("\u00a7a[GatherWood] \u00a76Done! Collected " + logCount + " logs!");
        break;
    }

    // Check if baritone is still active
    if (!baritone.getPathingControlManager().mostRecentInControl().isPresent()) {
        Chat.log("\u00a7e[GatherWood] Baritone stopped, restarting mine...");
        Time.sleep(2000);
        baritone.getCommandManager().execute("mine " + LOG_TYPES.join(" "));
    }
}
