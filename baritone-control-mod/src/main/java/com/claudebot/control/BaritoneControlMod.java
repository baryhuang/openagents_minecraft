package com.claudebot.control;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.MinecraftClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.ConcurrentLinkedQueue;

public class BaritoneControlMod implements ClientModInitializer {
    public static final Logger LOGGER = LoggerFactory.getLogger("baritone-control");
    public static final ConcurrentLinkedQueue<Runnable> TICK_QUEUE = new ConcurrentLinkedQueue<>();
    private static HttpControlServer httpServer;

    @Override
    public void onInitializeClient() {
        LOGGER.info("Baritone Control Mod initializing...");

        // Process queued actions on the client tick (main thread)
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            Runnable task;
            while ((task = TICK_QUEUE.poll()) != null) {
                try {
                    task.run();
                } catch (Exception e) {
                    LOGGER.error("Error running queued task", e);
                }
            }
        });

        // Start HTTP server on port 8655
        httpServer = new HttpControlServer(8655);
        httpServer.start();
        LOGGER.info("Baritone Control HTTP API started on port 8655");
    }
}
