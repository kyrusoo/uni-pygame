# =============================================================================
# zones.py — Zone/scene data: layout, mobs, interactables, transitions
#
# Zones:
#   "home"    — Safe house. Crafting bench, no enemies. Door to forest.
#   "forest"  — Outdoor farming. Trees/stones to harvest, Goblins, StoneGolems.
#               Door back home, door to dungeon path.
#   "path"    — Dungeon corridor. Eyebats + two medium bosses block the way.
#               Door to boss arena once both mid-bosses are dead.
#   "boss"    — Final arena. Malvortex. (uses original World/Boss)
#
# TODO: Add more zones, weather effects, day/night cycle.
# =============================================================================

import pygame
import random
from src.settings import *
from src.world import World, Platform, Camera, ParallaxBackground
from src.mobs import (MobManager, Goblin, Eyebat, StoneGolem,
                      ForestGuardian, CaveWarden)

# ── Zone floor & arena sizes ──────────────────────────────────────────────────
HOME_W, HOME_H = 1400, 900
FOREST_W, FOREST_H = 3600, 900
PATH_W, PATH_H = 3000, 900
BOSS_W, BOSS_H = ARENA_WIDTH, ARENA_HEIGHT

ZONE_FLOOR_Y = 830  # same as main FLOOR_Y


# ── Resource node (tree / stone) ──────────────────────────────────────────────

class ResourceNode:
    """
    Clickable/attackable world object that drops materials.
    kind: 'tree' | 'stone'
    """

    def __init__(self, x, y, kind="tree"):
        self.kind = kind
        self.x = x
        self.y = y
        self.hp = 40 if kind == "tree" else 60
        self.max_hp = self.hp
        self.alive = True
        self.respawn_timer = 0.0
        self._shake = 0.0

        w = 40 if kind == "tree" else 36
        h = 80 if kind == "tree" else 44
        self.rect = pygame.Rect(int(x - w // 2), int(y - h), w, h)

    @property
    def drop_item(self):
        return "wood" if self.kind == "tree" else "stone"

    def hit(self, damage=10) -> list[str]:
        """Strike the node. Returns list of drops if destroyed."""
        if not self.alive:
            return []
        self._shake = 0.15
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            qty = random.randint(3, 6)
            return [self.drop_item] * qty
        return []

    def update(self, dt):
        self._shake = max(0.0, self._shake - dt)
        if not self.alive:
            self.respawn_timer += dt
            if self.respawn_timer > 20.0:
                self.alive = True
                self.hp = self.max_hp
                self.respawn_timer = 0.0

    def draw(self, surface, camera_offset):
        if not self.alive:
            return
        ox = int(self._shake * 6 * (1 if int(self._shake * 20) % 2 == 0 else -1))
        cx = self.rect.x - camera_offset[0] + ox
        cy = self.rect.y - camera_offset[1]

        if self.kind == "tree":
            # Trunk
            trunk_x = cx + self.rect.w // 2 - 6
            pygame.draw.rect(surface, (100, 60, 20),
                             (trunk_x, cy + 44, 12, 36))
            # Canopy (3 circles)
            for dy2, r in [(44, 22), (26, 28), (10, 22)]:
                pygame.draw.circle(surface, (30, 120, 40),
                                   (cx + self.rect.w // 2, cy + dy2), r)
        else:
            # Stone cluster
            pygame.draw.ellipse(surface, (110, 110, 100),
                                (cx, cy + 12, self.rect.w, self.rect.h - 12))
            pygame.draw.ellipse(surface, (80, 80, 70),
                                (cx + 6, cy, 22, 18))
            pygame.draw.line(surface, (60, 60, 55),
                             (cx + 8, cy + 20), (cx + 18, cy + 36), 2)

        # HP bar
        if self.hp < self.max_hp:
            bw = self.rect.w
            fill = int(bw * self.hp / self.max_hp)
            pygame.draw.rect(surface, (60, 30, 10), (cx, cy - 8, bw, 5))
            pygame.draw.rect(surface, (180, 120, 40), (cx, cy - 8, fill, 5))


# ── Door / transition trigger ──────────────────────────────────────────────────

class Door:
    """
    A visible door rectangle. When player overlaps + presses E,
    triggers a zone transition.
    """

    def __init__(self, x, y, target_zone: str, label: str,
                 locked=False, lock_hint=""):
        self.rect = pygame.Rect(x, y, 40, 70)
        self.target_zone = target_zone
        self.label = label
        self.locked = locked
        self.lock_hint = lock_hint
        self._font = None

    def _get_font(self):
        if not self._font:
            pygame.font.init()
            self._font = pygame.font.SysFont("monospace", 12, bold=True)
        return self._font

    def is_nearby(self, player_rect: pygame.Rect) -> bool:
        expanded = self.rect.inflate(60, 20)
        return expanded.colliderect(player_rect)

    def draw(self, surface, camera_offset):
        cx = self.rect.x - camera_offset[0]
        cy = self.rect.y - camera_offset[1]
        font = self._get_font()

        # Frame
        pygame.draw.rect(surface, (80, 55, 30), (cx - 4, cy - 4,
                                                 self.rect.w + 8, self.rect.h + 4))
        # Door fill
        col = (50, 30, 10) if not self.locked else (40, 40, 50)
        pygame.draw.rect(surface, col, (cx, cy, self.rect.w, self.rect.h))
        # Handle
        pygame.draw.circle(surface, (200, 170, 80),
                           (cx + self.rect.w - 8, cy + self.rect.h // 2), 4)

        # Lock icon
        if self.locked:
            pygame.draw.rect(surface, (180, 160, 40),
                             (cx + 12, cy + 20, 16, 14))
            pygame.draw.arc(surface, (180, 160, 40),
                            pygame.Rect(cx + 14, cy + 10, 12, 16),
                            0, 3.14, 3)

        # Label above
        lbl_col = (120, 80, 30) if self.locked else (200, 180, 100)
        lbl = font.render(("[LOCKED] " if self.locked else "[E] ") + self.label,
                          True, lbl_col)
        surface.blit(lbl, (cx + self.rect.w // 2 - lbl.get_width() // 2,
                           cy - 18))

        if self.locked and self.lock_hint:
            hint = font.render(self.lock_hint, True, (160, 80, 80))
            surface.blit(hint, (cx + self.rect.w // 2 - hint.get_width() // 2,
                                cy - 32))


# ── Crafting bench ────────────────────────────────────────────────────────────

class CraftingBench:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 30, y - 24, 60, 24)
        self._font = None

    def _get_font(self):
        if not self._font:
            pygame.font.init()
            self._font = pygame.font.SysFont("monospace", 12, bold=True)
        return self._font

    def is_nearby(self, player_rect):
        return self.rect.inflate(80, 40).colliderect(player_rect)

    def draw(self, surface, camera_offset):
        cx = self.rect.x - camera_offset[0]
        cy = self.rect.y - camera_offset[1]
        # Table top
        pygame.draw.rect(surface, (120, 80, 35), (cx, cy, self.rect.w, 8))
        # Legs
        for lx in (cx + 4, cx + self.rect.w - 14):
            pygame.draw.rect(surface, (90, 60, 25), (lx, cy + 8, 10, 16))
        # Label
        font = self._get_font()
        lbl = font.render("[I] Crafting Bench", True, (200, 160, 80))
        surface.blit(lbl, (cx + self.rect.w // 2 - lbl.get_width() // 2,
                           cy - 16))


# ── Zone base ─────────────────────────────────────────────────────────────────

class Zone:
    """
    Base class for all named zones.
    Subclasses define platforms, doors, mobs, resource nodes.
    """

    name = "base"
    width = 1400
    height = 900
    floor_y = ZONE_FLOOR_Y

    # Spawn point for player entering from left / right
    spawn_left = (120, ZONE_FLOOR_Y - 52)
    spawn_right = (1280, ZONE_FLOOR_Y - 52)

    def __init__(self):
        self.camera = Camera()
        self.bg = ParallaxBackground()
        self.platforms: list[Platform] = []
        self.doors: list[Door] = []
        self.nodes: list[ResourceNode] = []
        self.benches: list[CraftingBench] = []
        self.mob_mgr = MobManager()

        self._build()

    def _build(self):
        """Override to add platforms, doors, mobs, nodes."""
        pass

    # ── Shared physics helpers ────────────────────────────────────────────────

    def get_platform_rects(self):
        return [p.rect for p in self.platforms]

    def resolve_vertical(self, entity_rect, vy):
        on_ground = False
        for plat in self.platforms:
            if entity_rect.colliderect(plat.rect):
                if vy >= 0:
                    if (entity_rect.bottom > plat.rect.top and
                            entity_rect.centery < plat.rect.top + 40):
                        entity_rect.bottom = plat.rect.top
                        vy = 0.0
                        on_ground = True
                elif vy < 0:
                    entity_rect.top = plat.rect.bottom
                    vy = 0.0
        return entity_rect, vy, on_ground

    def resolve_horizontal(self, entity_rect, vx):
        if entity_rect.left < 0:
            entity_rect.left = 0
            vx = max(0.0, vx)
        if entity_rect.right > self.width:
            entity_rect.right = self.width
            vx = min(0.0, vx)
        return entity_rect, vx

    # ── Camera ────────────────────────────────────────────────────────────────

    @property
    def camera_offset(self):
        return self.camera.offset

    def update_camera(self, player_rect, dt):
        self.camera.follow(player_rect, dt)
        self.camera.x = max(0, min(self.camera.x,
                                   self.width - SCREEN_WIDTH))
        self.camera.y = max(0, min(self.camera.y,
                                   self.height - SCREEN_HEIGHT))

    # ── Resource node harvesting ──────────────────────────────────────────────

    def try_harvest(self, player_rect, attack_manager) -> list[str]:
        """Called when player swings melee. Returns list of drops."""
        drops = []
        for node in self.nodes:
            if not node.alive:
                continue
            expanded = node.rect.inflate(80, 20)
            if expanded.colliderect(player_rect):
                drops.extend(node.hit(10))
        return drops

    # ── Update / draw ─────────────────────────────────────────────────────────

    def update(self, dt, player_rect):
        self.bg.update(dt)
        for node in self.nodes:
            node.update(dt)

    def draw_bg(self, surface):
        self.bg.draw(surface, self.camera.x)
        for p in self.platforms:
            p.draw(surface, self.camera.offset)

    def draw_world(self, surface):
        cam = self.camera.offset
        for node in self.nodes:
            node.draw(surface, cam)
        for bench in self.benches:
            bench.draw(surface, cam)
        for door in self.doors:
            door.draw(surface, cam)

    def draw_mobs(self, surface):
        self.mob_mgr.draw(surface, self.camera.offset)


# =============================================================================
# ── Zone: HOME ───────────────────────────────────────────────────────────────
# Safe zone. Crafting bench in the middle. Door to forest on the right.
# =============================================================================

class HomeZone(Zone):
    name = "home"
    width = HOME_W
    spawn_left = (200, ZONE_FLOOR_Y - 52)
    spawn_right = (HOME_W - 200, ZONE_FLOOR_Y - 52)

    def _build(self):
        # Floor
        self.platforms.append(Platform(0, ZONE_FLOOR_Y, self.width, 80))
        # Interior platforms / shelves
        self.platforms.append(Platform(300, 680, 200, 20))
        self.platforms.append(Platform(700, 600, 240, 20))
        self.platforms.append(Platform(1050, 680, 200, 20))

        # Crafting bench center
        self.benches.append(CraftingBench(HOME_W // 2, ZONE_FLOOR_Y))

        # Door to forest (right wall)
        self.doors.append(Door(
            self.width - 80, ZONE_FLOOR_Y - 70,
            target_zone="forest",
            label="Forest →",
        ))

    def draw_bg(self, surface):
        # Cozy indoor look — warm dark brown walls
        surface.fill((22, 14, 8))
        cam = self.camera.offset

        # Wall planks
        for wy in range(0, SCREEN_HEIGHT, 40):
            col = (28, 18, 10) if (wy // 40) % 2 == 0 else (24, 15, 8)
            pygame.draw.rect(surface, col, (0, wy, SCREEN_WIDTH, 40))

        # Floor surface (visible part)
        floor_sy = ZONE_FLOOR_Y - cam[1]
        pygame.draw.rect(surface, (60, 38, 18),
                         (0, floor_sy, SCREEN_WIDTH, SCREEN_HEIGHT))

        # Fireplace on left wall
        fp_x = 140 - cam[0]
        fp_y = ZONE_FLOOR_Y - 100 - cam[1]
        pygame.draw.rect(surface, (50, 30, 10), (fp_x, fp_y, 60, 90))
        pygame.draw.rect(surface, (20, 12, 5), (fp_x + 10, fp_y + 20, 40, 70))
        import math, time
        t = time.time()
        for fi in range(4):
            fr = (fp_x + 15 + fi * 8,
                  fp_y + 55 + int(math.sin(t * 4 + fi) * 6))
            pygame.draw.circle(surface, (255, 120, 20), fr, 7 - fi)

        # Window on right
        win_x = self.width - 300 - cam[0]
        win_y = ZONE_FLOOR_Y - 200 - cam[1]
        pygame.draw.rect(surface, (60, 80, 120), (win_x, win_y, 80, 60))
        pygame.draw.rect(surface, (100, 80, 40), (win_x, win_y, 80, 60), 4)
        pygame.draw.line(surface, (100, 80, 40),
                         (win_x + 40, win_y), (win_x + 40, win_y + 60), 3)
        pygame.draw.line(surface, (100, 80, 40),
                         (win_x, win_y + 30), (win_x + 80, win_y + 30), 3)

        # Draw platforms over
        for p in self.platforms:
            p.draw(surface, self.camera.offset)


# =============================================================================
# ── Zone: FOREST ─────────────────────────────────────────────────────────────
# Outdoor farming zone. Trees and stones, Goblins and StoneGolems.
# =============================================================================

class ForestZone(Zone):
    name = "forest"
    width = FOREST_W
    spawn_left = (150, ZONE_FLOOR_Y - 52)
    spawn_right = (FOREST_W - 150, ZONE_FLOOR_Y - 52)

    def _build(self):
        # Ground
        self.platforms.append(Platform(0, ZONE_FLOOR_Y, self.width, 80))

        # Varied terrain platforms
        layout = [
            (300, 700, 160, 20), (650, 650, 200, 20),
            (1000, 590, 180, 20), (1350, 660, 220, 20),
            (1700, 600, 160, 20), (2050, 660, 200, 20),
            (2400, 590, 180, 20), (2750, 650, 220, 20),
            (3100, 700, 160, 20), (3400, 640, 200, 20),
        ]
        for x, y, w, h in layout:
            self.platforms.append(Platform(x, y, w, h))

        # Trees and stones scattered across
        tree_xs = [250, 500, 750, 1100, 1450, 1800, 2200, 2600, 3000, 3350]
        stone_xs = [400, 700, 950, 1250, 1650, 2000, 2400, 2800, 3150]
        for tx in tree_xs:
            self.nodes.append(ResourceNode(tx, ZONE_FLOOR_Y, "tree"))
        for sx in stone_xs:
            self.nodes.append(ResourceNode(sx, ZONE_FLOOR_Y, "stone"))

        # Doors
        self.doors.append(Door(
            40, ZONE_FLOOR_Y - 70,
            target_zone="home",
            label="← Home",
        ))
        self.doors.append(Door(
            self.width - 80, ZONE_FLOOR_Y - 70,
            target_zone="path",
            label="Dungeon Path →",
        ))

        # Mobs — spread across the zone (spawn a few at fixed positions)
        mob_spawns_goblin = [600, 1000, 1400, 1900, 2300, 2700, 3100]
        mob_spawns_golem = [900, 1600, 2500, 3300]
        for mx in mob_spawns_goblin:
            self.mob_mgr.add(Goblin(mx, ZONE_FLOOR_Y))
        for mx in mob_spawns_golem:
            self.mob_mgr.add(StoneGolem(mx, ZONE_FLOOR_Y))

    def draw_bg(self, surface):
        """Forest outdoor aesthetic with sky and parallax."""
        # Sky gradient
        surface.fill((60, 100, 140))

        # Parallax background (hills/mountains)
        self.bg.draw(surface, self.camera.x)

        # Ground/grass layer
        cam = self.camera.offset
        floor_sy = ZONE_FLOOR_Y - cam[1]
        pygame.draw.rect(surface, (40, 80, 40),
                         (0, floor_sy, SCREEN_WIDTH, SCREEN_HEIGHT))

        # Grass edge highlight
        pygame.draw.rect(surface, (60, 120, 60),
                         (0, floor_sy, SCREEN_WIDTH, 8))

        # Draw platforms
        for p in self.platforms:
            p.draw(surface, self.camera.offset)


# =============================================================================
# ── Zone: PATH ───────────────────────────────────────────────────────────────
# Dungeon corridor. Two medium bosses + Eyebats block the way to the arena.
# =============================================================================

class PathZone(Zone):
    name = "path"
    width = PATH_W
    spawn_left = (150, ZONE_FLOOR_Y - 52)
    spawn_right = (PATH_W - 150, ZONE_FLOOR_Y - 52)

    def __init__(self):
        self._mid_bosses_defeated = 0
        super().__init__()

    def _build(self):
        self.platforms.append(Platform(0, ZONE_FLOOR_Y, self.width, 80))

        # Dungeon-style stepped layout
        layout = [
            (200, 700, 200, 20), (500, 640, 180, 20),
            (850, 580, 220, 20), (1150, 520, 180, 20),
            (1500, 580, 200, 20), (1800, 640, 180, 20),
            (2100, 580, 220, 20), (2400, 520, 200, 20),
            (2700, 640, 180, 20),
        ]
        for x, y, w, h in layout:
            self.platforms.append(Platform(x, y, w, h))

        # Door back to forest
        self.doors.append(Door(
            40, ZONE_FLOOR_Y - 70,
            target_zone="forest",
            label="← Forest",
        ))

        # Boss arena door — locked until mid-bosses die
        self._boss_door = Door(
            self.width - 80, ZONE_FLOOR_Y - 70,
            target_zone="boss",
            label="Boss Arena →",
            locked=True,
            lock_hint="Defeat both Guardians!",
        )
        self.doors.append(self._boss_door)

        # Medium bosses
        self.mob_mgr.add(ForestGuardian(900, ZONE_FLOOR_Y))
        self.mob_mgr.add(CaveWarden(2200, ZONE_FLOOR_Y))

        # Eyebat swarms between bosses
        for bx in [500, 700, 1300, 1600, 1900, 2500, 2700]:
            self.mob_mgr.add(Eyebat(bx, ZONE_FLOOR_Y - 120))

    def update(self, dt, player_rect):
        super().update(dt, player_rect)
        # Count dead medium bosses to unlock door
        from src.mobs import MediumBoss
        active_bosses = sum(1 for m in self.mob_mgr.mobs if isinstance(m, MediumBoss))
        if active_bosses == 0:
            self._boss_door.locked = False

    def draw_bg(self, surface):
        # Dark dungeon stone aesthetic
        surface.fill((12, 10, 18))
        cam = self.camera.offset
        # Stone brick pattern
        for row in range(0, SCREEN_HEIGHT, 32):
            for col in range(0, SCREEN_WIDTH, 64):
                offset_x = 32 if (row // 32) % 2 else 0
                bx = col + offset_x - (cam[0] % 64)
                col_shade = (28, 24, 36) if (row + col) % 128 < 64 else (22, 18, 30)
                pygame.draw.rect(surface, col_shade, (bx, row, 62, 30))

        # Torch sconces every ~400px
        for tx in range(200, self.width, 400):
            sx = tx - cam[0]
            sy = 200
            if -20 < sx < SCREEN_WIDTH + 20:
                pygame.draw.rect(surface, (80, 60, 30), (sx - 4, sy, 8, 16))
                import math, time
                flicker = int(math.sin(time.time() * 6 + tx) * 4)
                pygame.draw.circle(surface, (255, 140, 40), (sx, sy - 4 + flicker), 10)
                pygame.draw.circle(surface, (255, 220, 80), (sx, sy - 4 + flicker), 5)

        for p in self.platforms:
            p.draw(surface, self.camera.offset)
