# =============================================================================
# particles.py — Particle system and screen-shake manager
# Supports: hit sparks, dust, blood, magic, fire, damage text pop-ups.
# TODO: Add pooling for zero-allocation recycling; add emitter objects.
# =============================================================================

import pygame
import random
import math
from src.settings import *


class Particle:
    """Single visual particle — short-lived sprite with velocity + fade."""

    __slots__ = (
        "x", "y", "vx", "vy", "lifetime", "max_lifetime",
        "color", "size", "gravity", "shrink",
    )

    def __init__(self, x, y, vx, vy, color, size=4,
                 lifetime=0.5, gravity=0.0, shrink=True):
        self.x, self.y   = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.color       = color
        self.size        = size
        self.lifetime    = lifetime
        self.max_lifetime = lifetime
        self.gravity     = gravity   # individual gravity override
        self.shrink      = shrink

    @property
    def alive(self):
        return self.lifetime > 0

    def update(self, dt):
        self.vy += self.gravity * dt
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.lifetime -= dt

    def draw(self, surface, camera_offset):
        frac  = max(0.0, self.lifetime / self.max_lifetime)
        alpha = int(frac * 255)
        size  = max(1, int(self.size * frac)) if self.shrink else self.size

        # Cheap alpha: blend color toward black
        r = int(self.color[0] * frac)
        g = int(self.color[1] * frac)
        b = int(self.color[2] * frac)

        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])
        pygame.draw.rect(surface, (r, g, b),
                         (sx - size // 2, sy - size // 2, size, size))


class DamageNumber:
    """Floating damage text that rises and fades."""

    def __init__(self, x, y, value, color, crit=False):
        self.x, self.y  = float(x), float(y)
        self.value       = value
        self.color       = color
        self.crit        = crit
        self.lifetime    = 1.1
        self.max_lt      = 1.1
        self.vy          = -90.0 if not crit else -130.0
        self.font_size   = 20 if not crit else 28

    @property
    def alive(self):
        return self.lifetime > 0

    def update(self, dt):
        self.y  += self.vy * dt
        self.vy += 40 * dt   # slow down rise
        self.lifetime -= dt

    def draw(self, surface, font, camera_offset):
        frac = max(0.0, self.lifetime / self.max_lt)
        r = min(255, int(self.color[0]))
        g = min(255, int(self.color[1]))
        b = min(255, int(self.color[2]))
        label = f"CRIT {self.value}!" if self.crit else str(self.value)
        text  = font.render(label, True, (r, g, b))
        sx = int(self.x - camera_offset[0]) - text.get_width() // 2
        sy = int(self.y - camera_offset[1])
        surface.blit(text, (sx, sy))


class ParticleSystem:
    """Manages all active particles and damage numbers."""

    def __init__(self):
        self.particles: list[Particle]    = []
        self.numbers:   list[DamageNumber] = []
        # Pre-build small font
        pygame.font.init()
        self.font_small = pygame.font.SysFont("monospace", 18, bold=True)
        self.font_crit  = pygame.font.SysFont("monospace", 26, bold=True)

    # ── Emission helpers ──────────────────────────────────────────────────────

    def emit_hit(self, x, y, color, count=12, speed=180, gravity=400):
        """Sparks for melee/projectile impact."""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd   = random.uniform(speed * 0.4, speed)
            vx    = math.cos(angle) * spd
            vy    = math.sin(angle) * spd - random.uniform(0, speed * 0.3)
            size  = random.randint(3, 7)
            lt    = random.uniform(0.25, 0.6)
            self._add(Particle(x, y, vx, vy, color, size, lt, gravity))

    def emit_dust(self, x, y, count=6):
        """Landing / movement dust."""
        for _ in range(count):
            vx = random.uniform(-60, 60)
            vy = random.uniform(-80, -20)
            lt = random.uniform(0.3, 0.6)
            self._add(Particle(x, y, vx, vy, C_GRAY, 5, lt, 150))

    def emit_blood(self, x, y, count=18):
        for _ in range(count):
            angle = random.uniform(-math.pi, 0)   # upward arc
            spd   = random.uniform(40, 200)
            vx    = math.cos(angle) * spd
            vy    = math.sin(angle) * spd
            size  = random.randint(4, 9)
            lt    = random.uniform(0.4, 0.9)
            self._add(Particle(x, y, vx, vy, (200, 20, 20), size, lt, 600))

    def emit_fire(self, x, y, count=10):
        """Boss fire attack particles."""
        for _ in range(count):
            vx = random.uniform(-80, 80)
            vy = random.uniform(-200, -60)
            lt = random.uniform(0.3, 0.7)
            c  = random.choice([C_BOSS_FIREBALL, C_BOSS_PROJ, (255, 220, 0)])
            self._add(Particle(x, y, vx, vy, c, random.randint(5, 12), lt, -80))

    def emit_magic(self, x, y, count=8):
        """Player ranged shot burst."""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd   = random.uniform(60, 150)
            vx    = math.cos(angle) * spd
            vy    = math.sin(angle) * spd
            lt    = random.uniform(0.2, 0.45)
            self._add(Particle(x, y, vx, vy, C_PLAYER_MANA, 5, lt, 0))

    def spawn_damage(self, x, y, value, color=C_DMG_BOSS, crit=False):
        self.numbers.append(DamageNumber(x, y, value, color, crit))

    # ── Core loop ─────────────────────────────────────────────────────────────

    def _add(self, p: Particle):
        if len(self.particles) < MAX_PARTICLES:
            self.particles.append(p)

    def update(self, dt):
        self.particles = [p for p in self.particles if p.alive]
        self.numbers   = [n for n in self.numbers   if n.alive]
        for p in self.particles:
            p.update(dt)
        for n in self.numbers:
            n.update(dt)

    def draw(self, surface, camera_offset):
        for p in self.particles:
            p.draw(surface, camera_offset)
        font = self.font_crit   # reuse for all — size encoded in color/text
        for n in self.numbers:
            n.draw(surface, font, camera_offset)


# ── Screen shake ──────────────────────────────────────────────────────────────

class ScreenShake:
    """Simple trauma-based screen shake."""

    def __init__(self):
        self.trauma  = 0.0   # 0–1, squares to get shake intensity
        self.offset  = [0, 0]

    def add(self, amount: float):
        """Trauma is additive but capped at 1."""
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt) -> tuple[int, int]:
        self.trauma = max(0.0, self.trauma - SCREEN_SHAKE_DECAY * dt)
        intensity   = self.trauma ** 2 * 18   # max 18px displacement
        self.offset[0] = random.randint(-1, 1) * intensity
        self.offset[1] = random.randint(-1, 1) * intensity
        return int(self.offset[0]), int(self.offset[1])
