// ============================================
// Auto Eat - Automatically eat food when hungry
// Runs as a background service
// ============================================

const HUNGER_THRESHOLD = 14; // eat when food drops below this (max 20)

Chat.log("\u00a7a[AutoEat] Service started! Threshold: " + HUNGER_THRESHOLD + "/20");

const FOOD_ITEMS = [
    "cooked_beef", "cooked_porkchop", "cooked_mutton", "cooked_chicken",
    "cooked_salmon", "cooked_cod", "golden_carrot", "golden_apple",
    "bread", "baked_potato", "mushroom_stew", "rabbit_stew",
    "beetroot_soup", "apple", "melon_slice", "sweet_berries",
    "carrot", "potato", "beetroot", "dried_kelp", "cookie"
];

while (true) {
    Time.sleep(2000);

    const player = Player.getPlayer();
    if (!player) continue;

    const food = player.getFoodLevel();
    if (food >= HUNGER_THRESHOLD) continue;

    Chat.log("\u00a7e[AutoEat] Hungry! Food: " + food + "/20, looking for food...");

    // Find food in inventory
    const inv = player.getInventory();
    let foodSlot = -1;
    for (let i = 0; i < 36; i++) {
        const stack = inv.getSlot(i);
        if (stack) {
            const name = stack.getItemId();
            for (let j = 0; j < FOOD_ITEMS.length; j++) {
                if (name.indexOf(FOOD_ITEMS[j]) !== -1) {
                    foodSlot = i;
                    break;
                }
            }
            if (foodSlot >= 0) break;
        }
    }

    if (foodSlot >= 0) {
        // Move food to hotbar slot 8 (last slot) and select it
        const stack = inv.getSlot(foodSlot);
        Chat.log("\u00a7a[AutoEat] Eating " + stack.getItemId() + " from slot " + foodSlot);

        if (foodSlot >= 9) {
            // Swap to hotbar
            inv.swap(foodSlot, 35); // slot 35 = hotbar slot 8
        }

        // Select the hotbar slot and use
        player.getInventory().setSelectedSlot(8);
        Time.sleep(200);

        // Hold right click to eat
        KeyBind.pressKey("key.use");
        Time.sleep(2000); // eating takes ~1.6s
        KeyBind.releaseKey("key.use");

        Chat.log("\u00a7a[AutoEat] Done eating! Food now: " + player.getFoodLevel());
    } else {
        Chat.log("\u00a7c[AutoEat] No food in inventory!");
    }
}
