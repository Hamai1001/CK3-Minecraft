package dev.ckcraft;

public final class CombatRules {
    private CombatRules() {}

    public static double health(GeneratedDesign.Enemy enemy, int prowess) {
        return Math.min(enemy.health_cap(), enemy.health_base() + (long)Math.max(0, prowess) * enemy.health_per_prowess());
    }

    public static double damage(GeneratedDesign.Enemy enemy, int prowess) {
        return Math.min(enemy.attack_cap(), enemy.attack_base() + (long)Math.max(0, prowess) / 10 * enemy.attack_per_ten_prowess());
    }
}
