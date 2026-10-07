package dev.ckcraft;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.nbt.NbtElement;
import net.minecraft.nbt.NbtIo;
import net.minecraft.nbt.NbtList;
import net.minecraft.nbt.NbtSizeTracker;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;
import net.minecraft.world.GameMode;
import net.minecraft.util.WorldSavePath;

/** Save recovery before touching inventory or position, including across crashes. */
public final class RecoveryStore {
    private final Path directory;

    public RecoveryStore(MinecraftServer server) throws IOException {
        directory = server.getSavePath(WorldSavePath.ROOT).resolve("ckcraft-recovery");
        Files.createDirectories(directory);
    }

    private Path file(ServerPlayerEntity player) { return directory.resolve(player.getUuidAsString() + ".dat"); }

    public NbtCompound read(ServerPlayerEntity player) throws IOException {
        Path path = file(player);
        return Files.exists(path) ? NbtIo.readCompressed(path, NbtSizeTracker.ofUnlimitedBytes()) : null;
    }

    public void write(ServerPlayerEntity player, NbtCompound nbt) throws IOException {
        Path dest = file(player);
        Path temp = dest.resolveSibling(dest.getFileName() + ".tmp");
        NbtIo.writeCompressed(nbt, temp);
        try { Files.move(temp, dest, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING); }
        catch (java.nio.file.AtomicMoveNotSupportedException ignored) { Files.move(temp, dest, StandardCopyOption.REPLACE_EXISTING); }
    }

    public NbtCompound capture(ServerPlayerEntity player, String session, String instance) throws IOException {
        if (Files.exists(file(player))) throw new IOException("A previous journey still needs recovery");
        NbtCompound nbt = new NbtCompound();
        nbt.putString("Session", session);
        nbt.putString("Instance", instance);
        nbt.putString("Outcome", "");
        nbt.putString("Dimension", player.getWorld().getRegistryKey().getValue().toString());
        nbt.putDouble("X", player.getX()); nbt.putDouble("Y", player.getY()); nbt.putDouble("Z", player.getZ());
        nbt.putFloat("Yaw", player.getYaw()); nbt.putFloat("Pitch", player.getPitch());
        nbt.putFloat("Health", player.getHealth());
        nbt.putInt("GameMode", player.interactionManager.getGameMode().getId());
        nbt.putInt("SelectedSlot", player.getInventory().selectedSlot);
        nbt.putInt("ExperienceLevel", player.experienceLevel);
        nbt.putInt("TotalExperience", player.totalExperience);
        nbt.putFloat("ExperienceProgress", player.experienceProgress);
        nbt.put("Inventory", player.getInventory().writeNbt(new NbtList()));
        player.getHungerManager().writeNbt(nbt);
        write(player, nbt);
        return nbt;
    }

    public void restore(MinecraftServer server, ServerPlayerEntity player, NbtCompound nbt) throws IOException {
        RegistryKey<net.minecraft.world.World> key = RegistryKey.of(RegistryKeys.WORLD, Identifier.of(nbt.getString("Dimension")));
        ServerWorld world = server.getWorld(key);
        if (world == null) throw new IOException("Original world dimension is unavailable; recovery retained");
        player.teleport(world, nbt.getDouble("X"), nbt.getDouble("Y"), nbt.getDouble("Z"), nbt.getFloat("Yaw"), nbt.getFloat("Pitch"));
        player.getInventory().clear();
        player.getInventory().readNbt(nbt.getList("Inventory", NbtElement.COMPOUND_TYPE));
        player.getInventory().selectedSlot = nbt.getInt("SelectedSlot");
        player.setHealth(Math.min(player.getMaxHealth(), nbt.getFloat("Health")));
        player.getHungerManager().readNbt(nbt);
        player.experienceLevel = nbt.getInt("ExperienceLevel");
        player.totalExperience = nbt.getInt("TotalExperience");
        player.experienceProgress = nbt.getFloat("ExperienceProgress");
        player.changeGameMode(GameMode.byId(nbt.getInt("GameMode")));
        player.fallDistance = 0;
        player.currentScreenHandler.sendContentUpdates();
        // Bridge delivery can finish before vanilla's next autosave. Persist
        // restored player data first, so a crash cannot lose the original items.
        // During DISCONNECT the player may already be removed from the manager;
        // keep recovery uncommitted in that case and restore on the next JOIN.
        boolean online = server.getPlayerManager().getPlayer(player.getUuid()) == player;
        if (online) server.getPlayerManager().saveAllPlayerData();
        nbt.putBoolean("Restored", online);
        write(player, nbt);
    }

    public void clear(ServerPlayerEntity player) throws IOException { Files.deleteIfExists(file(player)); }
}
