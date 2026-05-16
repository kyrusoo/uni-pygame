# =============================================================================
# ui.py — HUD elements, boss health bar, menus, overlays
# TODO: Add minimap, ability cooldown icons, item tooltips, animated fonts.
# =============================================================================

import pygame
import math
from src.settings import *


def _lerp_color(a, b, t):
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


class UI:
    """Renders all HUD and overlay elements."""

    def __init__(self):
        pygame.font.init()
        self.font_sm = pygame.font.SysFont("monospace", 14, bold=True)
        self.font_md = pygame.font.SysFont("monospace", 20, bold=True)
        self.font_lg = pygame.font.SysFont("monospace", 28, bold=True)
        self.font_xl = pygame.font.SysFont("monospace", 44, bold=True)
        self.font_xxl = pygame.font.SysFont("monospace", 64, bold=True)

        # Animated values for smooth bar transitions
        self._hp_display = 1.0  # fraction 0–1
        self._mana_display = 1.0
        self._boss_display = 1.0

        self._time = 0.0

    # ── Smooth bar lerp ───────────────────────────────────────────────────────

    def _update_bars(self, player, boss, dt):
        spd = 4.0 * dt
        self._hp_display += (player.hp_frac - self._hp_display) * spd
        self._mana_display += (player.mana_frac - self._mana_display) * spd
        if boss and boss.alive:
            self._boss_display += (boss.hp_frac - self._boss_display) * spd

    # ── Core draw helpers ─────────────────────────────────────────────────────

    def _bar(self, surface, x, y, w, h, frac, color_bg, color_fg,
             border=2, label=""):
        pygame.draw.rect(surface, color_bg, (x, y, w, h))
        fill_w = max(0, int(w * frac))
        pygame.draw.rect(surface, color_fg, (x, y, fill_w, h))
        pygame.draw.rect(surface, C_WHITE, (x, y, w, h), border)
        if label:
            txt = self.font_sm.render(label, True, C_WHITE)
            surface.blit(txt, (x + 4, y + h // 2 - txt.get_height() // 2))

    # ── Player HUD ────────────────────────────────────────────────────────────

    def _draw_player_hud(self, surface, player):
        PAD = 14
        W = 200
        H = 20

        # HP bar
        self._bar(surface, PAD, PAD, W, H,
                  self._hp_display, C_HP_BAR_BG, C_HP_BAR_FG,
                  label=f"HP {player.hp}/{player.max_hp}")

        # Mana bar
        self._bar(surface, PAD, PAD + H + 6, W, H,
                  self._mana_display, C_MANA_BAR_BG, C_MANA_BAR_FG,
                  label=f"MP {int(player.mana)}/{player.max_mana}")

        # Defense + level
        info = f"DEF {player.defense}  LVL {player.level}"
        surf = self.font_sm.render(info, True, C_WHITE)
        surface.blit(surf, (PAD, PAD + H * 2 + 14))

        # XP bar
        xp_frac = player.xp / player.xp_next
        self._bar(surface, PAD, PAD + H * 3 + 18, W, 8,
                  xp_frac, (20, 20, 60), (80, 160, 255), border=1)

        # Dash cooldown indicator
        dash_frac = 1.0 - (player._dash_cd_timer / PLAYER_DASH_COOLDOWN) \
            if player._dash_cd_timer > 0 else 1.0
        dash_color = (100, 200, 255) if dash_frac >= 1.0 else (60, 80, 120)
        self._bar(surface, PAD, PAD + H * 3 + 30, W // 2, 8,
                  dash_frac, (40, 40, 80), dash_color, border=1)
        lbl = self.font_sm.render("DASH", True,
                                  C_WHITE if dash_frac >= 1.0 else C_GRAY)
        surface.blit(lbl, (PAD + W // 2 + 4, PAD + H * 3 + 29))

    # ── Boss health bar ───────────────────────────────────────────────────────

    def _draw_boss_bar(self, surface, boss):
        if not boss or not boss.alive:
            return

        W = SCREEN_WIDTH - 160
        H = 28
        x = 80
        y = SCREEN_HEIGHT - 58

        # Background strip
        strip = pygame.Surface((W + 20, H + 30), pygame.SRCALPHA)
        strip.fill((0, 0, 0, 160))
        surface.blit(strip, (x - 10, y - 12))

        fg = C_HP_BAR_FG2 if boss.enraged else C_BOSS_HP_FG

        # Phase indicator below bar
        phase_txt = "— ENRAGED —" if boss.enraged else f"Phase {boss.phase}"
        phase_color = (255, 80, 20) if boss.enraged else C_WHITE
        phase_surf = self.font_sm.render(phase_txt, True, phase_color)
        surface.blit(phase_surf, (x, y - 14))

        self._bar(surface, x, y, W, H,
                  self._boss_display, C_BOSS_HP_BG, fg,
                  border=2)

        # Boss name
        name = "MALVORTEX THE DREAD TITAN"
        name_surf = self.font_md.render(name, True, C_WHITE)
        surface.blit(name_surf, (SCREEN_WIDTH // 2 - name_surf.get_width() // 2,
                                 y - 22))

        # HP numbers
        hp_txt = f"{max(0, boss.hp)} / {boss.max_hp}"
        hp_surf = self.font_sm.render(hp_txt, True, C_WHITE)
        surface.blit(hp_surf, (x + W - hp_surf.get_width() - 4, y + 6))

    # ── Controls reminder ─────────────────────────────────────────────────────

    def _draw_controls(self, surface):
        lines = [
            "A/D: Move   SPACE: Jump   SHIFT: Dash",
            "Z: Melee   X: Magic Bolt   ESC: Pause",
        ]
        y = SCREEN_HEIGHT - 38
        for line in lines:
            surf = self.font_sm.render(line, True, (140, 140, 140))
            surface.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))
            y += 18

    # ── Pause menu ────────────────────────────────────────────────────────────

    def draw_pause(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        title = self.font_xl.render("PAUSED", True, C_WHITE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2,
                             SCREEN_HEIGHT // 2 - 80))

        hints = ["ESC  — Resume", "R    — Restart", "Q    — Quit"]
        for i, h in enumerate(hints):
            s = self.font_md.render(h, True, (200, 200, 200))
            surface.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2,
                             SCREEN_HEIGHT // 2 + i * 34))

    # ── Game Over / Victory ───────────────────────────────────────────────────

    def draw_game_over(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        t = self.font_xxl.render("YOU DIED", True, (220, 40, 40))
        surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2,
                         SCREEN_HEIGHT // 2 - 70))

        sub = self.font_md.render("Press R to restart  |  Q to quit",
                                  True, (180, 180, 180))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2,
                           SCREEN_HEIGHT // 2 + 30))

    def draw_victory(self, surface, player):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        t = self.font_xxl.render("BOSS SLAIN!", True, (255, 220, 50))
        surface.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2,
                         SCREEN_HEIGHT // 2 - 80))

        stats = [
            f"HP Remaining: {player.hp} / {player.max_hp}",
            f"Level: {player.level}",
            "Press R to restart  |  Q to quit",
        ]
        for i, line in enumerate(stats):
            s = self.font_md.render(line, True, (220, 220, 220))
            surface.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2,
                             SCREEN_HEIGHT // 2 - 10 + i * 34))

    # ── Main draw call ────────────────────────────────────────────────────────

    def update(self, dt, player, boss):
        self._time += dt
        self._update_bars(player, boss, dt)

    def draw(self, surface, player, boss, paused,
             game_over, victory, show_controls=True):
        self._draw_player_hud(surface, player)
        self._draw_boss_bar(surface, boss)

        if show_controls and self._time < 8.0:
            self._draw_controls(surface)

        if paused:
            self.draw_pause(surface)
        elif game_over:
            self.draw_game_over(surface)
        elif victory:
            self.draw_victory(surface, player)

    # ── Zone HUD (for non-boss zones) ─────────────────────────────────────────

    def draw_zone_hud(self, surface, player, zone_name=""):
        """Simplified HUD for exploration zones (no boss bar)."""
        self._draw_player_hud(surface, player)

        # Zone name label
        if zone_name and self._time < 5.0:
            zone_label = {
                "home": "— Home —",
                "forest": "— Forest —",
                "path": "— Dungeon Path —",
            }.get(zone_name, zone_name)

            frac = min(1.0, self._time / 0.5) if self._time < 4.5 else (5.0 - self._time) / 0.5
            alpha = int(frac * 255)

            label_surf = self.font_lg.render(zone_label, True, (200, 180, 100))
            label_surf.set_alpha(alpha)
            surface.blit(label_surf, (SCREEN_WIDTH // 2 - label_surf.get_width() // 2, 40))