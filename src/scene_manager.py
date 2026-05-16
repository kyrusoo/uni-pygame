# =============================================================================
# scene_manager.py — Orchestrates zones, transitions, and shared game state
#
# The SceneManager owns:
#   - All zone instances (home, forest, path, boss)
#   - The player (shared across zones)
#   - The inventory (shared across zones)
#   - Transition logic (fade, spawn point placement)
#
# main.py delegates all per-frame logic here.
# TODO: Add save/load, scene-specific music, loading screen between zones.
# =============================================================================

import pygame
import random
from src.settings import *
from src.player import Player
from src.boss import Boss
from src.attacks import AttackManager
from src.particles import ParticleSystem, ScreenShake
from src.inventory import Inventory
from src.zones import (HomeZone, ForestZone, PathZone,
                       ZONE_FLOOR_Y, BOSS_W, BOSS_H)
from src.world import World
from src.mobs import MobManager


# ── Fade transition helper ────────────────────────────────────────────────────

class FadeTransition:
    def __init__(self):
        self._alpha = 0
        self._dir = 0  # -1 = fade out, +1 = fade in
        self._done = False
        self._surface = None
        self.pending_zone = None
        self.pending_side = "left"

    def start_fade_out(self, to_zone: str, side: str):
        self._dir = 1  # darken
        self._alpha = 0
        self._done = False
        self.pending_zone = to_zone
        self.pending_side = side

    @property
    def fading(self):
        return self._dir != 0

    @property
    def at_black(self):
        return self._alpha >= 255

    def update(self, dt):
        if self._dir == 0:
            return

        # Накапливаем альфу во float, чтобы не зависать при мелком dt
        if self._dir == 1:  # Затемнение (Fade out)
            self._alpha += 900.0 * dt
            if self._alpha >= 255:
                self._alpha = 255
                self._dir = -1  # Включаем осветление
                self._done = False
        elif self._dir == -1:  # Осветление (Fade in)
            self._alpha -= 900.0 * dt
            if self._alpha <= 0:
                self._alpha = 0
                self._dir = 0  # Конец анимации
                self._done = True

    def draw(self, surface):
        if self._alpha <= 0:
            return
        if self._surface is None or self._surface.get_size() != surface.get_size():
            self._surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Принудительно кастим к int и ограничиваем рамками 0-255
        current_alpha = max(0, min(255, int(self._alpha)))
        self._surface.fill((0, 0, 0, current_alpha))
        surface.blit(self._surface, (0, 0))


# ── Zone notification banner ──────────────────────────────────────────────────

class ZoneBanner:
    def __init__(self):
        self._text = ""
        self._timer = 0.0
        self._font = pygame.font.SysFont("monospace", 36, bold=True)

    def show(self, text: str):
        self._text = text
        self._timer = 2.8

    def update(self, dt):
        self._timer = max(0.0, self._timer - dt)

    def draw(self, surface):
        if self._timer <= 0:
            return
        frac = min(1.0, self._timer / 0.6)  # fade in
        if self._timer < 0.6:
            frac = self._timer / 0.6  # fade out
        alpha = int(frac * 255)
        surf = self._font.render(self._text, True, (255, 220, 100))
        # Dark backing
        bg = pygame.Surface((surf.get_width() + 40, surf.get_height() + 16),
                            pygame.SRCALPHA)
        bg.fill((0, 0, 0, int(alpha * 0.6)))
        bx = SCREEN_WIDTH // 2 - bg.get_width() // 2
        by = SCREEN_HEIGHT // 3
        surface.blit(bg, (bx, by))
        # Apply alpha manually
        surf.set_alpha(alpha)
        surface.blit(surf, (bx + 20, by + 8))


# ── Scene manager ─────────────────────────────────────────────────────────────

class SceneManager:
    """
    Central coordinator. One instance lives for the whole game session.
    Call update() and draw() each frame from main.py.
    """

    ZONE_NAMES = {
        "home": "— Home —",
        "forest": "— Forest —",
        "path": "— Dungeon Path —",
        "boss": "— Boss Arena —",
    }

    def __init__(self):
        # ── Shared state ──────────────────────────────────────────────────
        self.inventory = Inventory()
        self.player = Player(x=200.0, y=float(ZONE_FLOOR_Y - Player.HEIGHT))
        self._sync_player_stats()

        # ── Zone instances (lazy — built on first visit) ───────────────────
        self._zones: dict = {}
        self._current_zone_id = "home"
        self._zone = self._get_zone("home")

        # ── Boss arena shared objects ──────────────────────────────────────
        self._boss_world = None
        self._boss = None
        self._boss_defeated = False

        # ── Per-zone attack / particle systems ────────────────────────────
        self.atk_mgr = AttackManager()
        self.psys = ParticleSystem()
        self.shake = ScreenShake()

        # ── Transition / UI helpers ────────────────────────────────────────
        self._fade = FadeTransition()
        self._banner = ZoneBanner()
        self._banner.show(self.ZONE_NAMES["home"])

        # Game states
        self.paused = False
        self.game_over = False
        self.victory = False

        # Fonts
        pygame.font.init()
        self._font_hint = pygame.font.SysFont("monospace", 13, bold=True)

    # ── Zone factory ──────────────────────────────────────────────────────────

    def _get_zone(self, zone_id: str):
        if zone_id not in self._zones:
            builders = {
                "home": HomeZone,
                "forest": ForestZone,
                "path": PathZone,
            }
            if zone_id in builders:
                self._zones[zone_id] = builders[zone_id]()
        return self._zones.get(zone_id)

    # ── Stat sync ─────────────────────────────────────────────────────────────

    def _sync_player_stats(self):
        """
        Push inventory equipment stats onto player each frame.
        Player.attack / defense / attack_range / attack_rate all come
        from equipped items.
        """
        inv = self.inventory
        base = PLAYER_DEFENSE
        self.player.defense = base + inv.total_defense
        self.player.attack = inv.weapon_damage or PLAYER_ATTACK
        self.player._atk_range = inv.weapon_range
        self.player._atk_rate_override = inv.weapon_rate

    # ── Transition ────────────────────────────────────────────────────────────

    def _do_transition(self, target_zone: str, side: str):
        """Actually switch zone and reposition player."""
        self._current_zone_id = target_zone
        self.atk_mgr.clear()

        if target_zone == "boss":
            self._enter_boss()
            return

        zone = self._get_zone(target_zone)
        self._zone = zone

        # Place player at correct side spawn
        if side == "left":
            sx, sy = zone.spawn_left
        else:
            sx, sy = zone.spawn_right

        self.player.rect.x = int(sx)
        self.player.rect.y = int(sy)
        self.player.vx = 0.0
        self.player.vy = 0.0

    def _enter_boss(self):
        """Build boss arena on first entry."""
        if self._boss_world is None:
            from src.world import World
            self._boss_world = World()
            self._boss = Boss(
                x=float(ARENA_WIDTH // 2),
                y=float(FLOOR_Y),
            )
        self.player.rect.x = 300
        self.player.rect.y = FLOOR_Y - Player.HEIGHT
        self.player.vx = 0.0
        self.player.vy = 0.0
        self._zone = None  # signals "we are in boss mode"

    @property
    def in_boss(self) -> bool:
        return self._current_zone_id == "boss"

    # ── Per-frame update ──────────────────────────────────────────────────────

    def update(self, dt: float, keys, events):
        # ── Pause / menu events ───────────────────────────────────────────
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and not self.game_over:
                    self.paused = not self.paused

                if event.key in (pygame.K_i, pygame.K_TAB):
                    self.inventory.open = not self.inventory.open

                if self.inventory.open:
                    self.inventory.handle_key(event.key, self.player)

                if event.key == pygame.K_r and (self.game_over or self.victory):
                    self._restart()

                if event.key == pygame.K_q:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.inventory.handle_click(
                    event.pos[0], event.pos[1],
                    (SCREEN_WIDTH, SCREEN_HEIGHT)
                )

        # ОБНОВЛЯЕМ ФЕЙДЕР И БАННЕР ТУТ ОДИН РАЗ ДЛЯ ВСЕХ СОСТОЯНИЙ
        self._fade.update(dt)
        self._banner.update(dt)

        if self.paused or self.game_over or self.victory:
            return

        if self.inventory.open:
            return  # freeze world while inventory is open

        # ── Fade / transition mid-frame ───────────────────────────────────
        if self._fade.fading and self._fade.at_black and self._fade.pending_zone:
            self._do_transition(self._fade.pending_zone, self._fade.pending_side)
            self._banner.show(self.ZONE_NAMES.get(self._fade.pending_zone, ""))
            self._fade.pending_zone = None

        # ── Sync stats from equipment ──────────────────────────────────────
        self._sync_player_stats()

        # ── Branch: boss arena vs normal zone ─────────────────────────────
        if self.in_boss:
            self._update_boss(dt, keys)
        else:
            self._update_zone(dt, keys)

    # ── Boss arena update ─────────────────────────────────────────────────────

    def _update_boss(self, dt, keys):
        from src.scene_manager import _calc_damage
        world = self._boss_world
        boss  = self._boss

        self.player.handle_input(keys, dt, self.atk_mgr, self.psys)
        self.player.update(dt, world, self.psys)

        if boss and boss.alive:
            boss.update(dt, self.player.rect, self.atk_mgr, self.psys, world)

        self.atk_mgr.update(dt, self.psys)

        # Player ↔ boss collision
        _resolve_boss_attacks(self.atk_mgr, self.player, boss,
                               self.psys, self.shake)

        self.psys.update(dt)
        world.update(self.player.rect, dt)
        self.shake.update(dt)

        if not self.player.alive and self.player.dead_timer > 1.5:
            self.game_over = True
        if boss and not boss.alive and boss.dead_timer > 2.5:
            if not self._boss_defeated:
                self._boss_defeated = True
                self.player.gain_xp(500)
                self.inventory.add("mid_boss_core", 2)
            self.victory = True

    # ── Normal zone update ────────────────────────────────────────────────────

    def _update_zone(self, dt, keys):
        zone = self._zone

        # Block input during fade transition
        if not self._fade.fading:
            self.player.handle_input(keys, dt, self.atk_mgr, self.psys)

        self.player.update(dt, zone, self.psys)

        # Mob updates
        drops = zone.mob_mgr.update(
            dt, self.player.rect, self.atk_mgr, self.psys, zone)
        for item_id in drops:
            self.inventory.add(item_id, 1)

        # Mob ↔ player attack resolution
        xp = zone.mob_mgr.resolve_player_attacks(
            self.atk_mgr, self.player, self.psys, self.shake)
        if xp:
            self.player.gain_xp(xp)
        zone.mob_mgr.resolve_mob_attacks_on_player(
            self.atk_mgr, self.player, self.psys, self.shake)

        # Harvesting: melee swing harvests nearby resource nodes
        if self.player._swing_anim > 0.2:  # just started swinging
            drops2 = zone.try_harvest(self.player.rect, self.atk_mgr)
            for item_id in drops2:
                self.inventory.add(item_id, 1)

        self.atk_mgr.update(dt, self.psys)
        self.psys.update(dt)

        # Zone update (respawn nodes, door states)
        zone.update(dt, self.player.rect)
        zone.update_camera(self.player.rect, dt)

        self.shake.update(dt)

        # ── Door interaction ──────────────────────────────────────────────
        if self._fade._dir == 0:  # Проверяем, что фейдер ВООБЩЕ ничего не делает (не темнеет и не светлеет)
            for door in zone.doors:
                if door.is_nearby(self.player.rect):
                    if keys[pygame.K_e] and not door.locked:
                        side = "right" if door.rect.x < zone.width // 2 else "left"
                        self._fade.start_fade_out(door.target_zone, side)
                        break

        # Player dead
        if not self.player.alive and self.player.dead_timer > 1.5:
            self.game_over = True

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, ui):
        shake_off = self.shake.offset if hasattr(self.shake, 'offset') else (0, 0)

        if self.in_boss:
            self._draw_boss(surface, ui)
        else:
            self._draw_zone(surface, ui)

        self._fade.draw(surface)
        self._banner.draw(surface)
        self.inventory.draw(surface)

    def _draw_zone(self, surface, ui):
        zone = self._zone
        cam = zone.camera.offset

        zone.draw_bg(surface)
        zone.draw_world(surface)
        self.atk_mgr.draw(surface, cam)
        self.player.draw(surface, cam)
        zone.draw_mobs(surface)
        self.psys.draw(surface, cam)

        # HUD
        ui.draw_zone_hud(surface, self.player, self._current_zone_id)

        # Door hints
        for door in zone.doors:
            if door.is_nearby(self.player.rect) and not door.locked:
                hint = self._font_hint.render(
                    "[E] Enter " + door.label, True, (220, 200, 120))
                surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                    SCREEN_HEIGHT - 80))

        # Bench hint
        for bench in zone.benches:
            if bench.is_nearby(self.player.rect):
                hint = self._font_hint.render(
                    "[I] Open inventory to craft", True, (200, 180, 100))
                surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                    SCREEN_HEIGHT - 60))

    def _draw_boss(self, surface, ui):
        world = self._boss_world
        boss = self._boss
        cam = world.camera.apply_shake(
            (int(self.shake.offset[0]), int(self.shake.offset[1]))
            if hasattr(self.shake, 'offset') else (0, 0))

        world.draw(surface)
        self.atk_mgr.draw(surface, cam)
        self.player.draw(surface, cam)
        if boss:
            boss.draw(surface, cam)
        self.psys.draw(surface, cam)

        ui.draw(surface, self.player, boss,
                self.paused, self.game_over, self.victory)

    # ── Restart ───────────────────────────────────────────────────────────────

    def _restart(self):
        self.__init__()


# ── Helper: boss damage resolution (same as original main.py) ────────────────

def _calc_damage(base, defense, crit_chance, crit_multi):
    import random
    raw = max(1, base - defense)
    is_crit = random.random() < crit_chance
    return (int(raw * crit_multi) if is_crit else raw), is_crit


def _resolve_boss_attacks(attack_manager, player, boss, particles, shake):
    consumed = set()
    for proj in attack_manager.projectiles:
        if not proj.alive:
            continue
        if proj.owner == 'boss' and player.alive and not player.invincible:
            if proj.rect.colliderect(player.rect):
                dmg, _ = _calc_damage(proj.damage, player.defense, 0.0, 1.0)
                player.take_damage(dmg, knockback_x=proj.vx * 0.3,
                                   knockback_y=-180, particles=particles)
                shake.add(0.35)
                if not proj.pierce:
                    proj.alive = False
        elif proj.owner == 'player' and boss and boss.alive:
            if proj.rect.colliderect(boss.rect):
                dmg, crit = _calc_damage(proj.damage, boss.defense,
                                         PLAYER_CRIT_CHANCE, PLAYER_CRIT_MULTI)
                boss.take_damage(dmg, crit, particles)
                shake.add(0.2)
                if not proj.pierce:
                    proj.alive = False

    for idx, hb in enumerate(attack_manager.hitboxes):
        if not hb.alive or idx in consumed:
            continue
        if hb.owner == 'boss' and player.alive and not player.invincible:
            if hb.rect.colliderect(player.rect):
                dmg, _ = _calc_damage(hb.damage, player.defense, 0.0, 1.0)
                player.take_damage(dmg, knockback_x=hb.knockback[0],
                                   knockback_y=hb.knockback[1],
                                   particles=particles)
                shake.add(0.45)
                consumed.add(idx)
        elif hb.owner == 'player' and boss and boss.alive:
            if hb.rect.colliderect(boss.rect):
                dmg, crit = _calc_damage(hb.damage, boss.defense,
                                         PLAYER_CRIT_CHANCE, PLAYER_CRIT_MULTI)
                boss.take_damage(dmg, crit, particles)
                shake.add(0.28 if not crit else 0.5)
                consumed.add(idx)