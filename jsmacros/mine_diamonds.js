// ============================================
// Mine Diamonds - Smart strip mining
// Uses Baritone to mine at optimal Y level
// All actions visible in the client UI
// ============================================

const API = Java.type("baritone.api.BaritoneAPI");
const GoalBlock = Java.type("baritone.api.pathing.goals.GoalBlock");
const baritone = API.getProvider().getPrimaryBaritone();
const settings = API.getSettings();

// Diamond Y level (best at Y=-59 in 1.21.5, but also Y=11 for caves)
const MINE_Y = -59;
const TARGET_DIAMONDS = 10;

Chat.log("\u00a7b[MineDiamonds] Starting diamond mining operation!");
Chat.log("\u00a7b[MineDiamonds] Target: " + TARGET_DIAMONDS + " diamonds");
Chat.log("\u00a7b[MineDiamonds] Optimal Y level: " + MINE_Y);

// Step 1: First check if we have a pickaxe
let hasPick = false;
const inv = Player.getPlayer().getInventory();
for (let i = 0; i < 36; i++) {
    const stack = inv.getSlot(i);
    if (stack) {
        const name = stack.getItemId();
        if (name.indexOf("pickaxe") !== -1) {
            hasPick = true;
            Chat.log("\u00a7a[MineDiamonds] Found pickaxe: " + name);
            break;
        }
    }
}

if (!hasPick) {
    Chat.log("\u00a7c[MineDiamonds] No pickaxe found! Craft one first.");
    Chat.log("\u00a7c[MineDiamonds] Aborting.");
} else {
    // Step 2: Configure Baritone for mining
    settings.allowSprint.value = true;
    settings.mineScanDroppedItems.value = true;

    // Step 3: Go to diamond level first
    const pos = Player.getPlayer().getPos();
    if (pos.y > MINE_Y + 10) {
        Chat.log("\u00a7e[MineDiamonds] Current Y=" + Math.floor(pos.y) + ", digging down to Y=" + MINE_Y);
        baritone.getCustomGoalProcess().setGoalAndPath(
            new GoalBlock(Math.floor(pos.x), MINE_Y, Math.floor(pos.z))
        );

        // Wait to reach depth
        let waited = 0;
        while (baritone.getPathingBehavior().isPathing() && waited < 120) {
            Time.sleep(2000);
            waited += 2;
            const curY = Math.floor(Player.getPlayer().getPos().y);
            if (waited % 10 === 0) {
                Chat.log("\u00a77[MineDiamonds] Descending... Y=" + curY);
            }
        }
    }

    // Step 4: Mine diamonds
    Chat.log("\u00a7b[MineDiamonds] Now mining for diamonds and deepslate_diamond_ore...");
    baritone.getCommandManager().execute("mine diamond_ore deepslate_diamond_ore");

    // Step 5: Monitor
    while (true) {
        Time.sleep(5000);

        let diamondCount = 0;
        for (let i = 0; i < 36; i++) {
            const stack = inv.getSlot(i);
            if (stack) {
                const name = stack.getItemId();
                if (name.indexOf("diamond") !== -1 && name.indexOf("ore") === -1) {
                    diamondCount += stack.getCount();
                }
            }
        }

        if (diamondCount > 0) {
            Chat.log("\u00a7b[MineDiamonds] Diamonds: " + diamondCount + "/" + TARGET_DIAMONDS);
        }

        if (diamondCount >= TARGET_DIAMONDS) {
            baritone.getCommandManager().execute("stop");
            Chat.log("\u00a7a[MineDiamonds] \u00a76SUCCESS! Found " + diamondCount + " diamonds!");
            break;
        }

        // Restart if baritone stopped
        if (!baritone.getPathingControlManager().mostRecentInControl().isPresent()) {
            Chat.log("\u00a7e[MineDiamonds] Restarting mine search...");
            Time.sleep(2000);
            baritone.getCommandManager().execute("mine diamond_ore deepslate_diamond_ore");
        }
    }
}
