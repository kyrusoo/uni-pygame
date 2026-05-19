# =============================================================================
# attacks.py — Projectile and melee hitbox objects
# All active "damage instances" in the world live here.
# TODO: Add area-of-effect attacks, homing projectiles, piercing shots.
# =============================================================================

import pygame
import math
from src.settings import *


class Projectile:
    """
    Generic projectile moving in a straight line.
    owner: 'player' | 'boss'  — used to determine collision targets.
    """

    def __init__(self, x, y, vx, vy, damage, owner,
                 color=C_BOSS_PROJ, radius=8, lifetime=3.0,
                 pierce=False):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.damage = damage
        self.owner = owner
        self.color = color
        self.radius = radius
        self.lifetime = lifetime
        self.alive = True
        self.pierce = pierce  # passes through without destroying self
        # glow / trail tick
        self._trail_timer = 0.0

    @property
    def rect(self) -> pygame.Rect:
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    @property
    def center(self) -> tuple[float, float]:
        return self.x, self.y

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
        # Out-of-arena cull
        if not (-200 < self.x < ARENA_WIDTH + 200):
            self.alive = False

    def draw(self, surface, camera_offset):
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])
        # Outer glow
        pygame.draw.circle(surface, self.color,
                           (sx, sy), self.radius + 3)
        # Core
        bright = tuple(min(255, c + 80) for c in self.color)
        pygame.draw.circle(surface, bright,
                           (sx, sy), self.radius)


class Fireball(Projectile):
    """
    Slow, large projectile with gravity and arc.
    Emits fire particles while alive.
    """

    def __init__(self, x, y, vx, vy):
        super().__init__(x, y, vx, vy,
                         damage=BOSS_FIREBALL_DAMAGE,
                         owner='boss',
                         color=C_BOSS_FIREBALL,
                         radius=16,
                         lifetime=4.0)
        self._gravity = 200.0

    def update(self, dt):
        self.vy += self._gravity * dt
        super().update(dt)


class MeleeHitbox:
    """
    Instantaneous rect-based melee attack — lives for exactly one frame
    (or a short duration) then is consumed.
    """

    def __init__(self, x, y, w, h, damage, owner,
                 knockback_x=0, knockback_y=-120, duration=0.12):
        self.rect = pygame.Rect(x, y, w, h)
        self.damage = damage
        self.owner = owner
        self.knockback = (knockback_x, knockback_y)
        self.lifetime = duration
        self.alive = True

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface, camera_offset):
        # Debug-style translucent overlay (remove in final build)
        # Uncomment below to visualise hitboxes:
        # r = pygame.Rect(self.rect.x - camera_offset[0],
        #                 self.rect.y - camera_offset[1],
        #                 self.rect.w, self.rect.h)
        # pygame.draw.rect(surface, (255, 0, 0), r, 2)
        pass


class AttackManager:
    """
    Central list of all live attacks.
    Both Player and Boss push new attacks here;
    main loop drives updates and collision resolution.
    """

    def __init__(self):
        self.projectiles: list[Projectile | Fireball] = []
        self.hitboxes: list[MeleeHitbox] = []

    def add_projectile(self, proj: Projectile):
        self.projectiles.append(proj)

    def add_hitbox(self, hb: MeleeHitbox):
        self.hitboxes.append(hb)

    def update(self, dt, particles):
        # Update + cull dead objects
        for p in self.projectiles:
            p.update(dt)
        for h in self.hitboxes:
            h.update(dt)
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.hitboxes = [h for h in self.hitboxes if h.alive]

    def draw(self, surface, camera_offset):
        for p in self.projectiles:
            p.draw(surface, camera_offset)
        for h in self.hitboxes:
            h.draw(surface, camera_offset)

    def clear(self):
        self.projectiles.clear()
        self.hitboxes.clear()
