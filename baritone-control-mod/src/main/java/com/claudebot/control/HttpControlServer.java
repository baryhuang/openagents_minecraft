package com.claudebot.control;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.entity.Entity;
import net.minecraft.item.ItemStack;
import net.minecraft.util.math.BlockPos;
import net.minecraft.block.Block;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

public class HttpControlServer {
    private final int port;
    private HttpServer server;

    public HttpControlServer(int port) {
        this.port = port;
    }

    public void start() {
        try {
            server = HttpServer.create(new InetSocketAddress(port), 0);

            server.createContext("/status", this::handleStatus);
            server.createContext("/command", this::handleCommand);
            server.createContext("/goto", this::handleGoto);
            server.createContext("/mine", this::handleMine);
            server.createContext("/stop", this::handleStop);
            server.createContext("/look", this::handleLook);
            server.createContext("/chat", this::handleChat);
            server.createContext("/inventory", this::handleInventory);
            server.createContext("/attack", this::handleAttack);
            server.createContext("/place", this::handlePlace);
            server.createContext("/health", this::handleHealth);

            server.setExecutor(null);
            server.start();
        } catch (IOException e) {
            BaritoneControlMod.LOGGER.error("Failed to start HTTP server", e);
        }
    }

    // === Helper methods ===

    private String readBody(HttpExchange ex) throws IOException {
        try (InputStream is = ex.getRequestBody()) {
            return new String(is.readAllBytes(), StandardCharsets.UTF_8).trim();
        }
    }

    private void respond(HttpExchange ex, int code, String body) throws IOException {
        ex.getResponseHeaders().set("Content-Type", "application/json");
        ex.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        ex.sendResponseHeaders(code, bytes.length);
        try (OutputStream os = ex.getResponseBody()) {
            os.write(bytes);
        }
    }

    private String jsonOk(String msg) {
        return "{\"status\":\"ok\",\"message\":\"" + escapeJson(msg) + "\"}";
    }

    private String jsonError(String msg) {
        return "{\"status\":\"error\",\"message\":\"" + escapeJson(msg) + "\"}";
    }

    private String escapeJson(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
    }

    private ClientPlayerEntity getPlayer() {
        MinecraftClient mc = MinecraftClient.getInstance();
        return mc != null ? mc.player : null;
    }

    /** Run on main thread and wait for result */
    private <T> T runOnTick(java.util.function.Supplier<T> action) throws Exception {
        CompletableFuture<T> future = new CompletableFuture<>();
        BaritoneControlMod.TICK_QUEUE.add(() -> {
            try {
                future.complete(action.get());
            } catch (Exception e) {
                future.completeExceptionally(e);
            }
        });
        return future.get(5, TimeUnit.SECONDS);
    }

    // === Baritone helpers ===

    private boolean isBaritoneAvailable() {
        try {
            Class.forName("baritone.api.BaritoneAPI");
            return true;
        } catch (ClassNotFoundException e) {
            return false;
        }
    }

    private void baritoneCommand(String cmd) {
        try {
            baritone.api.IBaritone bari = baritone.api.BaritoneAPI.getProvider().getPrimaryBaritone();
            bari.getCommandManager().execute(cmd);
        } catch (Exception e) {
            BaritoneControlMod.LOGGER.error("Baritone command failed: " + cmd, e);
        }
    }

    // === Endpoints ===

    private void handleStatus(HttpExchange ex) throws IOException {
        try {
            String result = runOnTick(() -> {
                ClientPlayerEntity p = getPlayer();
                if (p == null) return jsonError("Not in game");
                double x = p.getX(), y = p.getY(), z = p.getZ();
                float yaw = p.getYaw(), pitch = p.getPitch();
                boolean baritoneAvail = isBaritoneAvailable();
                boolean pathing = false;
                if (baritoneAvail) {
                    try {
                        pathing = baritone.api.BaritoneAPI.getProvider().getPrimaryBaritone()
                                .getPathingBehavior().isPathing();
                    } catch (Exception ignored) {}
                }
                return String.format(
                    "{\"status\":\"ok\",\"x\":%.2f,\"y\":%.2f,\"z\":%.2f,\"yaw\":%.1f,\"pitch\":%.1f," +
                    "\"health\":%.1f,\"food\":%d,\"baritone_available\":%b,\"pathing\":%b}",
                    x, y, z, yaw, pitch, p.getHealth(), p.getHungerManager().getFoodLevel(),
                    baritoneAvail, pathing
                );
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handleCommand(HttpExchange ex) throws IOException {
        try {
            String body = readBody(ex);
            if (body.isEmpty()) {
                respond(ex, 400, jsonError("No command provided. POST a baritone command string."));
                return;
            }
            String result = runOnTick(() -> {
                if (!isBaritoneAvailable()) return jsonError("Baritone not loaded");
                baritoneCommand(body);
                return jsonOk("Executed: " + body);
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handleGoto(HttpExchange ex) throws IOException {
        try {
            String body = readBody(ex); // expect "x y z"
            String[] parts = body.split("\\s+");
            if (parts.length < 3) {
                respond(ex, 400, jsonError("Provide: x y z"));
                return;
            }
            int x = Integer.parseInt(parts[0]);
            int y = Integer.parseInt(parts[1]);
            int z = Integer.parseInt(parts[2]);
            String result = runOnTick(() -> {
                if (!isBaritoneAvailable()) return jsonError("Baritone not loaded");
                try {
                    baritone.api.IBaritone bari = baritone.api.BaritoneAPI.getProvider().getPrimaryBaritone();
                    bari.getCustomGoalProcess().setGoalAndPath(
                        new baritone.api.pathing.goals.GoalBlock(x, y, z)
                    );
                    return jsonOk("Navigating to " + x + " " + y + " " + z);
                } catch (Exception e) {
                    return jsonError("Goto failed: " + e.getMessage());
                }
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handleMine(HttpExchange ex) throws IOException {
        try {
            String body = readBody(ex); // block name e.g. "diamond_ore"
            if (body.isEmpty()) {
                respond(ex, 400, jsonError("Provide block name, e.g. diamond_ore"));
                return;
            }
            String result = runOnTick(() -> {
                if (!isBaritoneAvailable()) return jsonError("Baritone not loaded");
                baritoneCommand("mine " + body);
                return jsonOk("Mining: " + body);
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handleStop(HttpExchange ex) throws IOException {
        try {
            String result = runOnTick(() -> {
                if (!isBaritoneAvailable()) return jsonError("Baritone not loaded");
                baritoneCommand("stop");
                return jsonOk("Stopped all Baritone processes");
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handleLook(HttpExchange ex) throws IOException {
        try {
            String body = readBody(ex); // "yaw pitch"
            String[] parts = body.split("\\s+");
            if (parts.length < 2) {
                respond(ex, 400, jsonError("Provide: yaw pitch"));
                return;
            }
            float yaw = Float.parseFloat(parts[0]);
            float pitch = Float.parseFloat(parts[1]);
            String result = runOnTick(() -> {
                ClientPlayerEntity p = getPlayer();
                if (p == null) return jsonError("Not in game");
                p.setYaw(yaw);
                p.setPitch(pitch);
                return jsonOk("Looking at yaw=" + yaw + " pitch=" + pitch);
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handleChat(HttpExchange ex) throws IOException {
        try {
            String body = readBody(ex);
            if (body.isEmpty()) {
                respond(ex, 400, jsonError("Provide chat message"));
                return;
            }
            String result = runOnTick(() -> {
                ClientPlayerEntity p = getPlayer();
                if (p == null) return jsonError("Not in game");
                if (body.startsWith("/")) {
                    MinecraftClient.getInstance().getNetworkHandler()
                        .sendChatCommand(body.substring(1));
                } else {
                    MinecraftClient.getInstance().getNetworkHandler()
                        .sendChatMessage(body);
                }
                return jsonOk("Sent: " + body);
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handleInventory(HttpExchange ex) throws IOException {
        try {
            String result = runOnTick(() -> {
                ClientPlayerEntity p = getPlayer();
                if (p == null) return jsonError("Not in game");
                StringBuilder sb = new StringBuilder("{\"status\":\"ok\",\"items\":[");
                boolean first = true;
                for (int i = 0; i < p.getInventory().size(); i++) {
                    ItemStack stack = p.getInventory().getStack(i);
                    if (!stack.isEmpty()) {
                        if (!first) sb.append(",");
                        first = false;
                        sb.append(String.format("{\"slot\":%d,\"item\":\"%s\",\"count\":%d}",
                            i, stack.getItem().toString(), stack.getCount()));
                    }
                }
                sb.append("]}");
                return sb.toString();
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handleAttack(HttpExchange ex) throws IOException {
        try {
            String result = runOnTick(() -> {
                MinecraftClient mc = MinecraftClient.getInstance();
                if (mc.player == null) return jsonError("Not in game");
                if (mc.targetedEntity != null) {
                    mc.player.attack(mc.targetedEntity);
                    mc.player.swingHand(net.minecraft.util.Hand.MAIN_HAND);
                    return jsonOk("Attacked " + mc.targetedEntity.getName().getString());
                }
                return jsonError("No entity in crosshair");
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handlePlace(HttpExchange ex) throws IOException {
        try {
            String result = runOnTick(() -> {
                MinecraftClient mc = MinecraftClient.getInstance();
                if (mc.player == null) return jsonError("Not in game");
                if (mc.crosshairTarget != null &&
                    mc.crosshairTarget.getType() == net.minecraft.util.hit.HitResult.Type.BLOCK) {
                    net.minecraft.util.hit.BlockHitResult blockHit =
                        (net.minecraft.util.hit.BlockHitResult) mc.crosshairTarget;
                    mc.interactionManager.interactBlock(mc.player,
                        net.minecraft.util.Hand.MAIN_HAND, blockHit);
                    mc.player.swingHand(net.minecraft.util.Hand.MAIN_HAND);
                    return jsonOk("Used item / placed block");
                }
                return jsonError("No block targeted");
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }

    private void handleHealth(HttpExchange ex) throws IOException {
        try {
            String result = runOnTick(() -> {
                ClientPlayerEntity p = getPlayer();
                if (p == null) return jsonError("Not in game");
                return String.format(
                    "{\"status\":\"ok\",\"health\":%.1f,\"food\":%d,\"saturation\":%.1f,\"armor\":%d,\"xp_level\":%d}",
                    p.getHealth(), p.getHungerManager().getFoodLevel(),
                    p.getHungerManager().getSaturationLevel(), p.getArmor(), p.experienceLevel
                );
            });
            respond(ex, 200, result);
        } catch (Exception e) {
            respond(ex, 500, jsonError(e.getMessage()));
        }
    }
}
