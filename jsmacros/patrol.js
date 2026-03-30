// ============================================
// Patrol - Walk between waypoints in a loop
// Human-like exploration visible in client UI
// ============================================

const API = Java.type("baritone.api.BaritoneAPI");
const GoalBlock = Java.type("baritone.api.pathing.goals.GoalBlock");
const baritone = API.getProvider().getPrimaryBaritone();
const settings = API.getSettings();

// Enable human-like movement
settings.allowSprint.value = true;
settings.allowParkour.value = true;

// Define patrol waypoints (edit these for your world)
const pos = Player.getPlayer().getPos();
const cx = Math.floor(pos.x);
const cy = Math.floor(pos.y);
const cz = Math.floor(pos.z);

const waypoints = [
    { x: cx + 30, y: cy, z: cz,      name: "East"  },
    { x: cx + 30, y: cy, z: cz + 30, name: "SE"    },
    { x: cx,      y: cy, z: cz + 30, name: "South" },
    { x: cx - 30, y: cy, z: cz + 30, name: "SW"    },
    { x: cx - 30, y: cy, z: cz,      name: "West"  },
    { x: cx - 30, y: cy, z: cz - 30, name: "NW"    },
    { x: cx,      y: cy, z: cz - 30, name: "North" },
    { x: cx + 30, y: cy, z: cz - 30, name: "NE"    },
];

Chat.log("\u00a7d[Patrol] Starting patrol with " + waypoints.length + " waypoints");
Chat.log("\u00a7d[Patrol] Center: " + cx + ", " + cy + ", " + cz);
Chat.log("\u00a77[Patrol] Press ESC or run #stop to cancel");

let running = true;
let lap = 0;

while (running) {
    lap++;
    Chat.log("\u00a7d[Patrol] === Lap " + lap + " ===");

    for (let i = 0; i < waypoints.length; i++) {
        const wp = waypoints[i];
        Chat.log("\u00a7d[Patrol] Heading to " + wp.name + " (" + wp.x + ", " + wp.z + ")");

        baritone.getCustomGoalProcess().setGoalAndPath(new GoalBlock(wp.x, wp.y, wp.z));

        // Wait until we arrive or timeout (60s per waypoint)
        let elapsed = 0;
        while (elapsed < 60000) {
            Time.sleep(1000);
            elapsed += 1000;

            if (!baritone.getPathingBehavior().isPathing() &&
                !baritone.getPathingControlManager().mostRecentInControl().isPresent()) {
                break;
            }

            // Check distance to goal
            const p = Player.getPlayer().getPos();
            const dx = p.x - wp.x;
            const dz = p.z - wp.z;
            const dist = Math.sqrt(dx * dx + dz * dz);
            if (dist < 5) break;
        }

        const arrived = Player.getPlayer().getPos();
        Chat.log("\u00a7a[Patrol] Reached " + wp.name + " at " +
            Math.floor(arrived.x) + ", " + Math.floor(arrived.y) + ", " + Math.floor(arrived.z));

        // Brief pause at waypoint (human-like)
        Time.sleep(1000 + Math.floor(Math.random() * 2000));
    }

    Chat.log("\u00a7d[Patrol] Lap " + lap + " complete!");
}
