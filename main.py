#!/usr/bin/env python3
# =============================================================================
# main.py — Entry point and main game loop
#
# Responsibilities:
#   - Window / clock setup
#   - Scene management (gameplay, pause, game-over, victory)
#   - Connecting Player ↔ Boss ↔ World ↔ AttackManager ↔ ParticleSystem
#   - Collision resolution between attacks and entities
#   - Screen shake compositionw
#
# TODO: Add a title screen, multiple boss arenas, save/load system.
# =============================================================================

import sys
import random
import math
import pygame

# Ensure src package is importable when run from project root
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.settings  import *
from src.world     import World
from src.player    import Player
from src.boss      import Boss
from src.attacks   import AttackManager
from src.particles import ParticleSystem, ScreenShake
from src.ui        import UI


# ── Damage calculation ────────────────────────────────────────────────────────

def calc_damage(base: int, defense: int,
                crit_chance: float, crit_multi: float) -> tuple[int, bool]:
    """
    Returns (final_damage, is_crit).
    final_damage = max(1, base - defense) * (crit_multi if crit else 1)k
    """
    raw   = max(1, base - defense)
    is_crit = random.random() < crit_chance
    return (int(raw * crit_multi) if is_crit else raw), is_crit


# ── Collision resolution ──────────────────────────────────────────────────────

def resolve_attacks(attack_manager: AttackManager,
                    player: Player,
                    boss: Boss,
                    particles: ParticleSystem,
                    shake: ScreenShake):
    """
    Check every live attack against its target entity.
    Player attacks → boss
    Boss attacks   → player
    """
    consumed_hitboxes = set()

    # ── Projectiles ───────────────────────────────────────────────────────
    for proj in attack_manager.projectiles:
        if not proj.alive:
            continue

        if proj.owner == 'boss' and player.alive and not player.invincible:
            if proj.rect.colliderect(player.rect):
                dmg, crit = calc_damage(
                    proj.damage, player.defense,
                    0.0, 1.0,   # boss crits not used here
                )
                player.take_damage(dmg, knockback_x=proj.vx * 0.3,
                                   knockback_y=-180, particles=particles)
                shake.add(0.35)
                if not proj.pierce:
                    proj.alive = False

        elif proj.owner == 'player' and boss.alive:
            if proj.rect.colliderect(boss.rect):
                dmg, crit = calc_damage(
                    proj.damage, boss.defense,
                    PLAYER_CRIT_CHANCE, PLAYER_CRIT_MULTI,
                )
                boss.take_damage(dmg, crit, particles)
                shake.add(0.2)
                if not proj.pierce:
                    proj.alive = False

    # ── Melee hitboxes ────────────────────────────────────────────────────
    for idx, hb in enumerate(attack_manager.hitboxes):
        if not hb.alive or idx in consumed_hitboxes:
            continue

        if hb.owner == 'boss' and player.alive and not player.invincible:
            if hb.rect.colliderect(player.rect):
                dmg, _ = calc_damage(hb.damage, player.defense, 0.0, 1.0)
                player.take_damage(dmg,
                                   knockback_x=hb.knockback[0],
                                   knockback_y=hb.knockback[1],
                                   particles=particles)
                shake.add(0.45)
                consumed_hitboxes.add(idx)

        elif hb.owner == 'player' and boss.alive:
            if hb.rect.colliderect(boss.rect):
                dmg, crit = calc_damage(
                    hb.damage, boss.defense,
                    PLAYER_CRIT_CHANCE, PLAYER_CRIT_MULTI,
                )
                boss.take_damage(dmg, crit, particles)
                shake.add(0.28 if not crit else 0.5)
                consumed_hitboxes.add(idx)


# ── Game factory ─────────────────────────────────────────────────────────────

def make_game():
    """Construct a fresh game state. Called at start and on restart."""
    world   = World()
    player  = Player(x=400.0, y=float(FLOOR_Y - Player.HEIGHT))
    boss    = Boss(x=float(ARENA_WIDTH // 2), y=float(FLOOR_Y))
    atk_mgr = AttackManager()
    psys    = ParticleSystem()
    shake   = ScreenShake()
    ui      = UI()
    return world, player, boss, atk_mgr, psys, shake, ui


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    world, player, boss, atk_mgr, psys, shake, ui = make_game()

    paused    = False
    game_over = False
    victory   = False

    running = True
    while running:
        # ── Delta time ────────────────────────────────────────────────────
        raw_dt = clock.tick(FPS) / 1000.0
        dt     = min(raw_dt, 0.05)   # clamp to avoid spiral of death

        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not game_over and not victory:
                        paused = not paused

                if event.key == pygame.K_r:
                    world, player, boss, atk_mgr, psys, shake, ui = make_game()
                    paused    = False
                    game_over = False
                    victory   = False

                if event.key == pygame.K_q:
                    running = False

        # ── Update ────────────────────────────────────────────────────────
        if not paused and not game_over and not victory:
            keys = pygame.key.get_pressed()

            # Player input → spawn attacks
            player.handle_input(keys, dt, atk_mgr, psys)

            # Entity updates
            player.update(dt, world, psys)
            boss.update(dt, player.rect, atk_mgr, psys, world)

            # Attack system
            atk_mgr.update(dt, psys)
            resolve_attacks(atk_mgr, player, boss, psys, shake)

            # Particles
            psys.update(dt)

            # Camera
            world.update(player.rect, dt)

            # Screen shake
            shake_off = shake.update(dt)

            # State transitions
            if not player.alive and player.dead_timer > 1.5:
                game_over = True
            if not boss.alive and boss.dead_timer > 2.5:
                victory = True
                player.gain_xp(500)   # big XP dump on kill

            # UI
            ui.update(dt, player, boss)
        else:
            shake_off = (0, 0)

        # ── Draw ──────────────────────────────────────────────────────────
        cam_off = world.camera.apply_shake(shake_off)

        # World (background + platforms)
        world.draw(screen)
        # Re-draw platforms with shake offset
        # (world.draw uses camera.offset; we re-apply shake manually below)

        # Redraw with shake — blit everything to a temp surface then offset
        # For simplicity, we draw directly; shake only affects entity layers:
        atk_mgr.draw(screen, cam_off)
        player.draw(screen, cam_off)
        boss.draw(screen, cam_off)
        psys.draw(screen, cam_off)

        # UI (always screen-space, no camera offset)
        ui.draw(screen, player, boss, paused, game_over, victory)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
