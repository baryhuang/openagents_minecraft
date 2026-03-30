// ============================================
// Craft Wooden Axe
// Converts oak logs -> planks -> sticks -> axe
// Uses the player inventory 2x2 grid + crafting table
// ============================================

const player = Player.getPlayer();
const inv = player.getInventory();

Chat.log("\u00a7a[CraftAxe] Starting axe crafting sequence...");

// Count oak logs
let logCount = 0;
for (let i = 0; i < 36; i++) {
    const stack = inv.getSlot(i);
    if (stack && stack.getItemId().indexOf("oak_log") !== -1) {
        logCount += stack.getCount();
    }
}

Chat.log("\u00a7a[CraftAxe] Have " + logCount + " oak logs");

if (logCount < 3) {
    Chat.log("\u00a7c[CraftAxe] Need at least 3 oak logs! Mining more...");
    const API = Java.type("baritone.api.BaritoneAPI");
    API.getProvider().getPrimaryBaritone().getCommandManager().execute("mine oak_log");

    // Wait until we have enough
    let waited = 0;
    while (logCount < 3 && waited < 60) {
        Time.sleep(3000);
        waited += 3;
        logCount = 0;
        for (let i = 0; i < 36; i++) {
            const stack = inv.getSlot(i);
            if (stack && stack.getItemId().indexOf("oak_log") !== -1) {
                logCount += stack.getCount();
            }
        }
    }
    API.getProvider().getPrimaryBaritone().getCommandManager().execute("stop");
    Time.sleep(500);
}

if (logCount < 3) {
    Chat.log("\u00a7c[CraftAxe] Still not enough logs. Aborting.");
} else {
    // Use player 2x2 crafting to make planks first
    // Open inventory
    Chat.log("\u00a7a[CraftAxe] Crafting planks from logs...");

    // We need to craft via the recipe system
    // In JsMacros, we can use the craft helper
    const container = player.openInventory();
    Time.sleep(500);

    // Craft planks: put 1 log in any 2x2 slot -> 4 planks
    // Slot 1-4 are the 2x2 crafting grid in player inventory
    // Slot 0 is the output
    container.click(inv.getMap().get("hotbar")[0], 0); // pick up logs from hotbar 0
    Time.sleep(200);
    container.click(1, 1); // right-click to place 1 log in crafting slot
    Time.sleep(200);
    container.click(1, 1); // place another
    Time.sleep(200);

    // Pick up result (4 planks per log)
    container.click(0, 0); // left click output = take planks
    Time.sleep(200);

    // Put planks in inventory
    container.click(inv.getMap().get("hotbar")[1], 0);
    Time.sleep(200);

    // Craft more planks with remaining log in cursor
    container.click(1, 0); // place in craft slot
    Time.sleep(200);
    container.click(0, 0); // take planks
    Time.sleep(200);
    container.click(inv.getMap().get("hotbar")[2], 0); // store
    Time.sleep(200);

    container.close();
    Time.sleep(500);

    Chat.log("\u00a7a[CraftAxe] Planks crafted! Now need a crafting table.");
    Chat.log("\u00a7a[CraftAxe] Place a crafting table and right-click it to finish.");
    Chat.log("\u00a76[CraftAxe] Recipe: 3 planks on top + 2 sticks below");

    // List what we have now
    const items = [];
    for (let i = 0; i < 36; i++) {
        const stack = inv.getSlot(i);
        if (stack && stack.getCount() > 0) {
            items.push(stack.getItemId() + " x" + stack.getCount());
        }
    }
    Chat.log("\u00a77[CraftAxe] Inventory: " + items.join(", "));
}
