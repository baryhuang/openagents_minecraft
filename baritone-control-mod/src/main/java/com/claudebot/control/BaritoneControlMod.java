package com.claudebot.control;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.ConcurrentLinkedQueue;

public class BaritoneControlMod implements ClientModInitializer {
    public static final Logger LOGGER = LoggerFactory.getLogger("baritone-control");
    public static final ConcurrentLinkedQueue<Runnable> TICK_QUEUE = new ConcurrentLinkedQueue<>();
    private static HttpControlServer httpServer;

    // Mouse lock: when true, player rotation is forced to lockedYaw/lockedPitch every tick
    public static volatile boolean mouseLocked = true;
    public static volatile float lockedYaw = 0f;
    public static volatile float lockedPitch = 0f;
    // Allow Baritone to control look direction even when mouse is locked
    public static volatile boolean allowBaritoneRotation = true;
    // Track last Baritone-set rotation to detect Baritone changes
    private static float lastBaritoneYaw = 0f;
    private static float lastBarittonePitch = 0f;
    private static boolean firstTick = true;

    @Override
    public void onInitializeClient() {
        LOGGER.info("Baritone Control Mod initializing...");

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            // Process queued actions on the client tick (main thread)
            Runnable task;
            while ((task = TICK_QUEUE.poll()) != null) {
                try {
                    task.run();
                } catch (Exception e) {
                    LOGGER.error("Error running queued task", e);
                }
            }

            // Mouse lock: override mouse-driven rotation every tick
            if (mouseLocked && client.player != null) {
                ClientPlayerEntity p = client.player;

                if (firstTick) {
                    // Initialize locked rotation to current player rotation
                    lockedYaw = p.getYaw();
                    lockedPitch = p.getPitch();
                    lastBaritoneYaw = lockedYaw;
                    lastBarittonePitch = lockedPitch;
                    firstTick = false;
                }

                if (allowBaritoneRotation) {
                    // If Baritone changed the rotation (pathfinding look), adopt it
                    float curYaw = p.getYaw();
                    float curPitch = p.getPitch();
                    if (Math.abs(curYaw - lastBaritoneYaw) > 0.1f ||
                        Math.abs(curPitch - lastBarittonePitch) > 0.1f) {
                        // Rotation changed since last tick — Baritone or code did it, adopt
                        lockedYaw = curYaw;
                        lockedPitch = curPitch;
                    }
                }

                // Force rotation to locked values (overrides mouse input)
                p.setYaw(lockedYaw);
                p.setPitch(lockedPitch);
                p.headYaw = lockedYaw;
                lastBaritoneYaw = lockedYaw;
                lastBarittonePitch = lockedPitch;
            }
        });

        // Start HTTP server on port 8655
        httpServer = new HttpControlServer(8655);
        httpServer.start();
        LOGGER.info("Baritone Control HTTP API started on port 8655");
        LOGGER.info("Mouse input LOCKED by default. Use /mouselock endpoint to toggle.");
    }
}
