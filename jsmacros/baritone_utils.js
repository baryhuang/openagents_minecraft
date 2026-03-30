// ============================================
// Baritone Utilities for JsMacros
// Provides helper functions for Baritone control
// ============================================

const API = Java.type("baritone.api.BaritoneAPI");
const GoalBlock = Java.type("baritone.api.pathing.goals.GoalBlock");
const GoalXZ = Java.type("baritone.api.pathing.goals.GoalXZ");
const GoalNear = Java.type("baritone.api.pathing.goals.GoalNear");

const baritone = API.getProvider().getPrimaryBaritone();
const settings = API.getSettings();

// Run a raw baritone command
function cmd(command) {
    baritone.getCommandManager().execute(command);
    Chat.log("[Bot] Executed: " + command);
}

// Navigate to x, y, z
function goto(x, y, z) {
    baritone.getCustomGoalProcess().setGoalAndPath(new GoalBlock(x, y, z));
    Chat.log("[Bot] Navigating to " + x + ", " + y + ", " + z);
}

// Navigate to x, z (any Y)
function gotoXZ(x, z) {
    baritone.getCustomGoalProcess().setGoalAndPath(new GoalXZ(x, z));
    Chat.log("[Bot] Navigating to x=" + x + " z=" + z);
}

// Mine a block type
function mine(blockName) {
    cmd("mine " + blockName);
}

// Stop all baritone processes
function stop() {
    cmd("stop");
}

// Check if pathing
function isPathing() {
    return baritone.getPathingBehavior().isPathing();
}

// Check if any process active
function isActive() {
    return baritone.getPathingControlManager().mostRecentInControl().isPresent();
}

// Wait until pathing is done
function waitUntilDone(timeoutMs) {
    const start = Time.time();
    const timeout = timeoutMs || 60000;
    while (isActive() && (Time.time() - start) < timeout) {
        Time.sleep(500);
    }
    return !isActive();
}

// Get player position
function getPos() {
    const p = Player.getPlayer();
    return { x: p.getX(), y: p.getY(), z: p.getZ() };
}

// Configure for human-like behavior
function humanMode() {
    settings.allowSprint.value = true;
    settings.allowParkour.value = true;
    settings.allowParkourAscend.value = true;
    settings.allowParkourPlace.value = true;
    settings.randomLooking.value = 0.01; // slight random head movement
    Chat.log("[Bot] Human-like mode enabled");
}
