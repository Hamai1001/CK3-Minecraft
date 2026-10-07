package dev.ckcraft;

import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.file.Path;
import java.util.UUID;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.block.Blocks;
import net.minecraft.component.DataComponentTypes;
import net.minecraft.component.type.AttributeModifiersComponent;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.mob.ZombieEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.GameMode;
import net.minecraft.world.World;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Singleplayer development slice. No game-window or console input is injected. */
public final class CKCraft implements ModInitializer {
    public static final Logger LOG = LoggerFactory.getLogger("ckcraft");
    private static final RegistryKey<World> CAMPAIGN = RegistryKey.of(RegistryKeys.WORLD, Identifier.of("ckcraft", "campaign"));
    private BridgeClient bridge;
    private RecoveryStore recovery;
    private boolean busy;
    private long ticks;
    private long nextWarning;
    private Journey journey;
    private NbtCompound returning;
    private UUID returningPlayer;
    private final String instance = UUID.randomUUID().toString();

    private static final class Journey {
        final ServerPlayerEntity player;
        final JsonObject request;
        final GeneratedDesign.Scenario design;
        final NbtCompound original;
        final long deadline;
        ZombieEntity enemy;
        boolean fighting;

        Journey(ServerPlayerEntity player, JsonObject request, NbtCompound original) {
            this.player = player; this.request = request; this.original = original;
            design = GeneratedDesign.SCENARIOS.get(request.get("scenario").getAsString());
            deadline = System.currentTimeMillis() + design.timeout_seconds()*1000L;
        }
    }

    @Override public void onInitialize() {
        ServerLifecycleEvents.SERVER_STARTED.register(server -> {
            ticks = 0; busy = false;
            if (server.isDedicated()) { LOG.warn("CKCraft 0.1 supports singleplayer only."); return; }
            try { recovery = new RecoveryStore(server); }
            catch (IOException error) { LOG.error("Cannot prepare inventory recovery", error); return; }
            String config = System.getenv("CKCRAFT_BRIDGE_CONFIG");
            if (config == null || config.isBlank()) { LOG.info("Bridge inactive. Set CKCRAFT_BRIDGE_CONFIG to the private bridge.json path."); return; }
            bridge = new BridgeClient(Path.of(config));
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
            if (bridge != null) bridge.close();
            bridge = null; recovery = null; journey = null; returning = null; returningPlayer = null;
        });
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            if (recovery == null) return;
            try {
                NbtCompound saved = recovery.read(handler.player);
                if (saved != null) {
                    if (saved.getString("Outcome").isEmpty()) saved.putString("Outcome", "aborted");
                    if (!saved.getBoolean("Restored")) recovery.restore(server, handler.player, saved);
                    returning = saved; returningPlayer = handler.player.getUuid();
                    handler.player.sendMessage(Text.literal("CKCraft: Vorherige Reise wiederhergestellt; Ergebnis wird erneut übermittelt."), false);
                }
            } catch (IOException error) { LOG.error("Recovery failed; original inventory retained on disk", error); }
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            if (journey != null && journey.player == handler.player) finish(server, "aborted");
        });
        ServerTickEvents.END_SERVER_TICK.register(this::tick);
        ServerEntityEvents.ENTITY_LOAD.register((entity,world) -> {
            if (entity.getCommandTags().contains("ckcraft_duelist") && (journey == null || journey.enemy == null || !journey.enemy.getUuid().equals(entity.getUuid()))) entity.discard();
        });
        ServerLivingEntityEvents.ALLOW_DEATH.register((entity, source, amount) -> {
            if (journey != null && entity == journey.player) {
                entity.setHealth(1);
                finish(journey.player.getServer(), journey.design.lost());
                return false;
            }
            return true;
        });
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
            if (journey != null && journey.enemy != null && entity.getUuid().equals(journey.enemy.getUuid()) && journey.fighting) finish(journey.player.getServer(), journey.design.won());
        });
        CommandRegistrationCallback.EVENT.register((dispatcher, access, environment) ->
            dispatcher.register(CommandManager.literal("ckcraft")
                .then(CommandManager.literal("status").executes(ctx -> {
                    ctx.getSource().sendFeedback(() -> Text.literal(bridge == null ? "CKCraft: Verbindung inaktiv." : returning != null ? "CKCraft: Rückgabe ausstehend." : journey == null ? "CKCraft: Wartet auf CK3." : "CKCraft: " + journey.design.label()), false);
                    return 1;
                }))
                .then(CommandManager.literal("return").executes(ctx -> {
                    ServerPlayerEntity player = ctx.getSource().getPlayerOrThrow();
                    if (journey == null || journey.player != player) return 0;
                    finish(player.getServer(), journey.design.enemy().equals("none") ? journey.design.won() : journey.design.aborted());
                    return 1;
                }))));
    }

    private void tick(MinecraftServer server) {
        ticks++;
        if (journey != null) {
            if (server.getPlayerManager().getPlayerList().size() != 1) { finish(server, "aborted"); return; }
            if (System.currentTimeMillis() > journey.deadline) { finish(server, journey.design.aborted()); return; }
            if (!journey.player.getServerWorld().getRegistryKey().equals(CAMPAIGN)) { finish(server, journey.design.aborted()); return; }
            if (journey.enemy != null) {
                // Chunk unload/reload recreates the Entity object. Its UUID is
                // stable; keep controlling the actual loaded opponent.
                var loaded = journey.player.getServerWorld().getEntity(journey.enemy.getUuid());
                if (loaded instanceof ZombieEntity current) {
                    journey.enemy = current;
                    if (journey.fighting) {
                        current.setAiDisabled(false);
                        current.setInvulnerable(false);
                        current.setTarget(journey.player);
                    }
                }
            }
            if (journey.enemy != null && !journey.fighting && journey.player.squaredDistanceTo(0.5,journey.design.floor_y()+1,journey.design.distance()/2.0) < 25) {
                journey.fighting = true;
                journey.enemy.setInvulnerable(false);
                journey.enemy.setAiDisabled(false);
                journey.enemy.setTarget(journey.player);
                journey.player.sendMessage(Text.literal("Das Duell beginnt! /ckcraft return bricht es ohne Belohnung ab."), false);
            }
            if (bridge != null && !busy && ticks%40 == 0) {
                String owned = journey.request.get("id").getAsString();
                busy = true;
                bridge.get().whenComplete((snapshot,error) -> server.execute(() -> {
                    busy = false;
                    if (error != null) return;
                    if (journey != null && journey.request.get("id").getAsString().equals(owned)
                        && (snapshot.get("session").isJsonNull() || !snapshot.getAsJsonObject("session").get("id").getAsString().equals(owned))) {
                        finish(server, "aborted");
                    }
                }));
            }
            return;
        }
        if (bridge == null || recovery == null || busy || ticks%40 != 0) return;
        if (server.getPlayerManager().getPlayerList().size() != 1 || server.isDedicated()) return;
        if (returning != null) { sendResult(server); return; }
        ServerPlayerEntity player = server.getPlayerManager().getPlayerList().getFirst();
        busy = true;
        bridge.get().whenComplete((snapshot,error) -> server.execute(() -> {
            if (error != null) { busy = false; warn(server); return; }
            if (snapshot.get("session").isJsonNull()) { busy = false; return; }
            JsonObject request = snapshot.getAsJsonObject("session");
            if (!request.get("status").getAsString().equals("WAITING")) { busy = false; return; }
            if (player.isDisconnected() || !player.isAlive() || server.getPlayerManager().getPlayerList().size() != 1) { busy = false; return; }
            JsonObject claim = payload(request.get("id").getAsString(),player.getUuidAsString(),instance);
            bridge.post("/v1/claim", claim).whenComplete((claimed,claimError) -> server.execute(() -> {
                busy = false;
                if (claimError != null) { warn(server); return; }
                start(server,player,claimed.getAsJsonObject("session"));
            }));
        }));
    }

    private void start(MinecraftServer server, ServerPlayerEntity player, JsonObject request) {
        GeneratedDesign.Scenario design = GeneratedDesign.SCENARIOS.get(request.get("scenario").getAsString());
        ServerWorld world = server.getWorld(CAMPAIGN);
        if (design == null || world == null || player.isDisconnected() || !player.isAlive()) {
            LOG.error("Cannot enter campaign dimension; claimed request requires recovery/abort.");
            abortUnstarted(request,player);
            return;
        }
        try {
            NbtCompound original = recovery.capture(player,request.get("id").getAsString(),instance);
            journey = new Journey(player,request,original);
            for (int x=-design.radius(); x<=design.radius(); x++) for (int z=-design.radius(); z<=design.radius(); z++) {
                world.setBlockState(new BlockPos(x,design.floor_y(),z),
                    (x==0 ? Blocks.COBBLESTONE : x%design.light_spacing()==0 && z%design.light_spacing()==0 ? Blocks.SEA_LANTERN : Blocks.GRASS_BLOCK).getDefaultState(),3);
                for (int y=1; y<=4; y++) world.setBlockState(new BlockPos(x,design.floor_y()+y,z),Blocks.AIR.getDefaultState(),3);
                if (Math.abs(x)==design.radius() || Math.abs(z)==design.radius()) {
                    world.setBlockState(new BlockPos(x,design.floor_y()+1,z),Blocks.OAK_FENCE.getDefaultState(),3);
                    world.setBlockState(new BlockPos(x,design.floor_y()+2,z),Blocks.OAK_FENCE.getDefaultState(),3);
                }
            }
            world.setBlockState(new BlockPos(0,design.floor_y(),design.distance()/2),Blocks.GOLD_BLOCK.getDefaultState(),3);
            player.teleport(world,0.5,design.floor_y()+1,-design.distance()/2.0,0,0);
            player.changeGameMode(GameMode.ADVENTURE);
            player.getInventory().clear();
            player.getInventory().setStack(0,new ItemStack(Items.IRON_SWORD));
            player.getInventory().setStack(1,new ItemStack(Items.COOKED_BEEF,8));
            player.getInventory().selectedSlot = 0;
            player.equipStack(EquipmentSlot.CHEST,new ItemStack(Items.IRON_CHESTPLATE));
            player.setHealth(player.getMaxHealth());
            player.getHungerManager().setFoodLevel(20);
            player.fallDistance = 0;
            player.sendMessage(Text.literal("CK3: " + request.get("name").getAsString() + " · Provinz " + request.get("province").getAsInt() + " · Kampfgeschick " + request.get("prowess").getAsInt()), false);
            player.sendMessage(Text.literal("Folge dem Weg. /ckcraft return bringt dich zurück. Diese Szene nutzt echte CK3-Daten und vorläufige Minecraft-Grafik."), false);
            if (!design.enemy().equals("none")) {
                ZombieEntity enemy = EntityType.ZOMBIE.create(world);
                if (enemy == null) throw new IOException("Could not create duelist");
                GeneratedDesign.Enemy rule = GeneratedDesign.ENEMIES.get(design.enemy());
                int prowess = request.get("opponent_prowess").getAsInt();
                enemy.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(CombatRules.health(rule,prowess));
                enemy.getAttributeInstance(EntityAttributes.GENERIC_ATTACK_DAMAGE).setBaseValue(CombatRules.damage(rule,prowess));
                enemy.setHealth(enemy.getMaxHealth());
                enemy.setCustomName(Text.literal(request.get("opponent_name").getAsString() + " · CK3 " + request.get("opponent").getAsInt() + " · Kampfgeschick " + prowess));
                enemy.setCustomNameVisible(true);
                enemy.addCommandTag("ckcraft_duelist");
                enemy.setBaby(false); enemy.setPersistent(); enemy.setAiDisabled(true); enemy.setInvulnerable(true);
                enemy.equipStack(EquipmentSlot.HEAD,new ItemStack(Items.IRON_HELMET));
                ItemStack weapon = new ItemStack(net.minecraft.registry.Registries.ITEM.get(Identifier.of(rule.weapon())));
                if (rule.weapon_modifiers().equals("none")) weapon.set(DataComponentTypes.ATTRIBUTE_MODIFIERS,AttributeModifiersComponent.DEFAULT);
                enemy.equipStack(EquipmentSlot.MAINHAND,weapon);
                enemy.refreshPositionAndAngles(0.5,design.floor_y()+1,design.distance()/2.0,180,0);
                journey.enemy = enemy;
                if (!world.spawnEntity(enemy)) throw new IOException("Duelist could not be spawned");
                LOG.info("CKCraft duelist spawned: health={}, damage={}",enemy.getHealth(),enemy.getAttributeValue(EntityAttributes.GENERIC_ATTACK_DAMAGE));
            }
        } catch (Exception error) {
            LOG.error("Could not prepare journey; attempting recovery",error);
            if (journey != null) finish(server,"aborted");
            else abortUnstarted(request,player);
        }
    }

    private void abortUnstarted(JsonObject request,ServerPlayerEntity player) {
        JsonObject body = payload(request.get("id").getAsString(),player.getUuidAsString(),instance);
        body.addProperty("outcome", "aborted");
        // No player state was touched. Preserve any unrelated recovery file.
        bridge.post("/v1/result",body).exceptionally(error -> {
            LOG.error("Unstarted journey could not be aborted; CK3 cancellation required");
            return null;
        });
    }

    private void finish(MinecraftServer server, String outcome) {
        if (journey == null) return;
        Journey current = journey;
        journey = null;
        if (current.enemy != null) {
            var world = server.getWorld(CAMPAIGN);
            var loaded = world == null ? null : world.getEntity(current.enemy.getUuid());
            if (loaded != null) loaded.discard();
            current.enemy.discard();
        }
        current.original.putString("Outcome",outcome);
        try {
            recovery.write(current.player,current.original);
            recovery.restore(server,current.player,current.original);
            returning = current.original;
            returningPlayer = current.player.getUuid();
            current.player.sendMessage(Text.literal("CKCraft: " + GeneratedDesign.OUTCOMES.get(outcome).label() + ". CK3 muss die Rückgabe noch bestätigen."), false);
        } catch (IOException error) { LOG.error("Return recovery retained on disk; stop and investigate before another journey",error); }
    }

    private void sendResult(MinecraftServer server) {
        ServerPlayerEntity player = server.getPlayerManager().getPlayer(returningPlayer);
        if (player == null) return;
        JsonObject body = payload(returning.getString("Session"),player.getUuidAsString(),returning.getString("Instance"));
        body.addProperty("outcome",returning.getString("Outcome"));
        busy = true;
        bridge.post("/v1/result",body).whenComplete((result,error) -> server.execute(() -> {
            busy = false;
            if (error != null) { warn(server); return; }
            try { recovery.clear(player); returning = null; returningPlayer = null; }
            catch (IOException io) { LOG.error("Could not clear completed inventory recovery",io); }
        }));
    }

    private static JsonObject payload(String session,String player,String instance) {
        JsonObject body = new JsonObject();
        body.addProperty("session",session); body.addProperty("player",player); body.addProperty("instance",instance);
        return body;
    }

    private void warn(MinecraftServer server) {
        if (ticks >= nextWarning) {
            nextWarning = ticks+600;
            LOG.warn("Bridge unavailable or request rejected; no CK3 result is assumed. Check bridge status.");
        }
    }
}
