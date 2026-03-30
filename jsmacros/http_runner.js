// ============================================
// HTTP Script Runner - Run JsMacros scripts via HTTP
// Bridges our HTTP control API with JsMacros scripts
// Start this as a service, then POST script names to run
// ============================================

// This polls a command file for script names to execute
// Combined with the existing HTTP API on port 8655

const SCRIPT_DIR = "/home/sbx_0cr8vKWlxLWU/minecraft_bot/client/gameDir/config/jsMacros/Macros/";
const CMD_FILE = "/home/sbx_0cr8vKWlxLWU/minecraft_bot/jsmacros_cmd.txt";

const File = Java.type("java.io.File");
const Files = Java.type("java.nio.file.Files");
const Path = Java.type("java.nio.file.Path");

Chat.log("\u00a7a[HTTPRunner] Script runner service started");
Chat.log("\u00a7a[HTTPRunner] Watching: " + CMD_FILE);

// Create command file if it doesn't exist
const cmdPath = Path.of(CMD_FILE);
if (!Files.exists(cmdPath)) {
    Files.writeString(cmdPath, "");
}

while (true) {
    Time.sleep(500);

    try {
        const content = Files.readString(cmdPath).trim();
        if (content.length === 0) continue;

        // Clear the file
        Files.writeString(cmdPath, "");

        Chat.log("\u00a7b[HTTPRunner] Running: " + content);

        if (content.endsWith(".js")) {
            // Run a script file
            JsMacros.runScript(SCRIPT_DIR + content);
        } else {
            // Treat as baritone command
            const API = Java.type("baritone.api.BaritoneAPI");
            API.getProvider().getPrimaryBaritone().getCommandManager().execute(content);
            Chat.log("\u00a7a[HTTPRunner] Baritone: " + content);
        }
    } catch (e) {
        Chat.log("\u00a7c[HTTPRunner] Error: " + e.getMessage());
    }
}
