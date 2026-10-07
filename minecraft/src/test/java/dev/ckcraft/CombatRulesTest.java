package dev.ckcraft;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CombatRulesTest {
    @Test void importedProwessActuallyChangesTheOpponent() {
        var enemy = GeneratedDesign.ENEMIES.get("courtier");
        assertTrue(CombatRules.health(enemy,30) > CombatRules.health(enemy,3));
        assertTrue(CombatRules.damage(enemy,30) > CombatRules.damage(enemy,3));
    }
    @Test void hostileOrExtremeInputCannotOverflowCombat() {
        var enemy = GeneratedDesign.ENEMIES.get("courtier");
        assertEquals(enemy.health_cap(),CombatRules.health(enemy,Integer.MAX_VALUE));
        assertEquals(enemy.attack_cap(),CombatRules.damage(enemy,Integer.MAX_VALUE));
        assertEquals(enemy.health_base(),CombatRules.health(enemy,-100));
    }
    @Test void FreeTravelDoesNotAcquireCombatStats() {
        var enemy = GeneratedDesign.ENEMIES.get(GeneratedDesign.SCENARIOS.get("free_travel").enemy());
        assertEquals(0,CombatRules.health(enemy,100));
        assertEquals(0,CombatRules.damage(enemy,100));
    }
}
