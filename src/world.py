# =============================================================================
# world.py — Arena layout, platform collision, background rendering, camera
# TODO: Load tile maps from Tiled JSON; add destructible terrain; lighting.
# =============================================================================

import pygame
import math
from src.settings import *


class Platform:
    """A single solid rectangular platform."""

    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface, camera_offset):
        sx = self.rect.x - camera_offset[0]
        sy = self.rect.y - camera_offset[1]

        # Body
        body_rect = pygame.Rect(sx, sy + 6, self.rect.w, self.rect.h - 6)
        pygame.draw.rect(surface, C_PLATFORM, body_rect)

        # Highlighted top edge
        pygame.draw.rect(surface, C_PLATFORM_TOP,
                         (sx, sy, self.rect.w, 6))


class Camera:
    """
    Smooth-following camera with world-bounds clamping.
    offset: world-space coordinate of the top-left screen corner.
    """

    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def follow(self, target_rect: pygame.Rect, dt: float):
        """Lerp toward keeping target centered."""
        target_x = target_rect.centerx - SCREEN_WIDTH // 2
        target_y = target_rect.centery - SCREEN_HEIGHT // 2

        lerp_speed = CAMERA_LERP * dt
        self.x += (target_x - self.x) * lerp_speed
        self.y += (target_y - self.y) * lerp_speed

        # Clamp to arena bounds
        self.x = max(0, min(self.x, ARENA_WIDTH - SCREEN_WIDTH))
        self.y = max(0, min(self.y, ARENA_HEIGHT - SCREEN_HEIGHT))

    @property
    def offset(self) -> tuple[int, int]:
        return int(self.x), int(self.y)

    def apply_shake(self, shake_offset: tuple[int, int]) -> tuple[int, int]:
        return (self.offset[0] + shake_offset[0],
                self.offset[1] + shake_offset[1])


class ParallaxBackground:
    """
    Multi-layer parallax using solid color bands and simple shapes
    to suggest a dark cavern / abyss atmosphere.
    TODO: Replace bands with actual sprite sheets for production.
    """

    def __init__(self):
        self._time = 0.0
        self._layers = [
            {"factor": 0.10, "color": C_BG_FAR},
            {"factor": 0.25, "color": C_BG_MID},
            {"factor": 0.45, "color": C_BG_NEAR},
        ]

    def update(self, dt):
        self._time += dt

    def draw(self, surface, camera_x: float):
        # Sky base
        surface.fill(C_BG_SKY)

        # Distant "mountain" silhouettes per layer
        for i, layer in enumerate(self._layers):
            scroll = camera_x * layer["factor"]
            color = layer["color"]
            # Draw simple repeating arch shapes
            for col in range(-1, SCREEN_WIDTH // 200 + 2):
                bx = int(col * 200 - scroll % 200)
                by = SCREEN_HEIGHT - 200 - i * 60
                # Arch / hill silhouette
                points = [
                    (bx, SCREEN_HEIGHT),
                    (bx, by + 80),
                    (bx + 40, by + 20),
                    (bx + 100, by),
                    (bx + 160, by + 20),
                    (bx + 200, by + 80),
                    (bx + 200, SCREEN_HEIGHT),
                ]
                pygame.draw.polygon(surface, color, points)

        # Animated glowing runes in background (ambience)
        for k in range(6):
            t = self._time * 0.5 + k * 1.1
            rx = int(80 + k * 200 - (camera_x * 0.08) % SCREEN_WIDTH)
            ry = int(SCREEN_HEIGHT * 0.35 + math.sin(t) * 12)
            glow = int(120 + math.sin(t * 1.3) * 40)
            pygame.draw.circle(surface, (glow, glow // 3, glow // 6),
                               (rx % SCREEN_WIDTH, ry), 4)


class World:
    """
    Holds all static geometry and exposes collision helpers.
    The arena floor is one big platform; floating platforms add verticality.
    """

    def __init__(self):
        self.camera = Camera()
        self.bg = ParallaxBackground()
        self.platforms: list[Platform] = self._build_arena()

    def _build_arena(self) -> list[Platform]:
        plats = []

        # ── Floor ──────────────────────────────────────────────────────────
        plats.append(Platform(0, FLOOR_Y, ARENA_WIDTH, 100))

        # ── Left / right walls (invisible bounds) ──────────────────────────
        # (handled via clamping in player movement)

        # ── Floating platforms ─────────────────────────────────────────────
        # Symmetrical layout suitable for a boss fight
        layout = [
            # (x,    y,   w,  h)
            (400, 640, 250, 24),
            (800, 560, 300, 24),
            (1200, 490, 250, 24),
            (1600, 430, 300, 24),  # centre-ish (boss area)
            (2000, 490, 250, 24),
            (2400, 560, 300, 24),
            (2800, 640, 250, 24),

            # Upper tier
            (600, 420, 180, 24),
            (1100, 360, 200, 24),
            (1550, 310, 250, 24),
            (2000, 360, 200, 24),
            (2500, 420, 180, 24),
        ]
        for x, y, w, h in layout:
            plats.append(Platform(x, y, w, h))

        return plats

    # ── Collision helpers ─────────────────────────────────────────────────────

    def get_platform_rects(self) -> list[pygame.Rect]:
        return [p.rect for p in self.platforms]

    def resolve_vertical(self, entity_rect: pygame.Rect,
                         vy: float) -> tuple[pygame.Rect, float, bool]:
        """
        Push entity out of platforms vertically.
        Returns (corrected_rect, corrected_vy, on_ground).
        Only top-landing is checked (Terraria style: fall through sides).
        """
        on_ground = False
        for plat in self.platforms:
            if entity_rect.colliderect(plat.rect):
                if vy >= 0:  # falling → land on top
                    if entity_rect.bottom > plat.rect.top and \
                            entity_rect.centery < plat.rect.top + 40:
                        entity_rect.bottom = plat.rect.top
                        vy = 0.0
                        on_ground = True
                elif vy < 0:  # jumping → hit ceiling
                    entity_rect.top = plat.rect.bottom
                    vy = 0.0
        return entity_rect, vy, on_ground

    def resolve_horizontal(self, entity_rect: pygame.Rect,
                           vx: float) -> tuple[pygame.Rect, float]:
        """Clamp entity to arena horizontal bounds."""
        if entity_rect.left < 0:
            entity_rect.left = 0
            vx = max(0.0, vx)
        if entity_rect.right > ARENA_WIDTH:
            entity_rect.right = ARENA_WIDTH
            vx = min(0.0, vx)
        return entity_rect, vx

    # ── Update / draw ─────────────────────────────────────────────────────────

    def update(self, player_rect: pygame.Rect, dt: float,
               shake_offset: tuple[int, int] = (0, 0)):
        self.bg.update(dt)
        self.camera.follow(player_rect, dt)

    def draw(self, surface: pygame.Surface):
        cam = self.camera.offset
        self.bg.draw(surface, self.camera.x)
        for plat in self.platforms:
            plat.draw(surface, cam)
