# =============================================================================
# mobs.py — Small enemies and medium boss entities
#
# Mob types:
#   Goblin     — melee rusher, drops mob_fang
#   Eyebat     — flying shooter, drops mob_eye
#   StoneGolem — slow tanky melee, drops stone + mob_fang (outdoor only)
#
# Medium bosses:
#   ForestGuardian — mid-boss 1 (Forest path)
#   CaveWarden     — mid-boss 2 (Cave path)
#
# TODO: Add patrol waypoints, ranged mobs with proper aim, mob spawners.
# =============================================================================

import pygame
import random
import math
from src.settings import *
from src.attacks import MeleeHitbox, Projectile
from src.particles import ParticleSystem


# ── Base Mob ──────────────────────────────────────────────────────────────────

class Mob:
    """Common mob base class. Concrete mobs override AI + draw."""

    def __init__(self, x, y, w, h, hp, defense, speed,
                 damage, xp_reward, drops: list[tuple[str, float]]):
        self.rect = pygame.Rect(int(x - w // 2), int(y - h), w, h)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1

        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.speed = speed
        self.damage = damage
        self.xp_reward = xp_reward
        self.drops = drops  # list of (item_id, drop_chance 0-1)

        self.alive = True
        self._iframe_timer = 0.0
        self._atk_timer = 0.0
        self._hit_flash = 0.0
        self._dead_timer = 0.0

        self._aggro_range = 500  # px, player must be this close to activate
        self._active = False

    @property
    def hp_frac(self):
        return max(0.0, self.hp / self.max_hp)

    @property
    def center(self):
        return float(self.rect.centerx), float(self.rect.centery)

    def take_damage(self, raw, particles: ParticleSystem,
                    knockback_x=0, knockback_y=0) -> int:
        if self._iframe_timer > 0 or not self.alive:
            return 0
        final = max(1, raw - self.defense)
        self.hp -= final
        self._iframe_timer = 0.3
        self._hit_flash = 0.15
        self.vx = knockback_x
        self.vy = knockback_y
        particles.emit_blood(self.rect.centerx, self.rect.centery, 8)
        particles.spawn_damage(self.rect.centerx, self.rect.top - 8, final,
                               color=C_DMG_BOSS)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return final

    def get_drops(self) -> list[str]:
        """Roll drop table; return list of item_ids dropped."""
        result = []
        for item_id, chance in self.drops:
            if random.random() < chance:
                result.append(item_id)
        return result

    def _apply_physics(self, dt, world):
        self.vy += GRAVITY * dt
        self.vy = min(self.vy, TERMINAL_VELOCITY)
        self.rect.x += int(self.vx * dt)
        self.rect, self.vx = world.resolve_horizontal(self.rect, self.vx)
        self.rect.y += int(self.vy * dt)
        self.rect, self.vy, self.on_ground = world.resolve_vertical(
            self.rect, self.vy)

    def _move_toward(self, tx, stop=60):
        dx = tx - self.rect.centerx
        if abs(dx) > stop:
            self.vx = math.copysign(self.speed, dx)
            self.facing = int(math.copysign(1, dx))
        else:
            self.vx = 0.0

    def update(self, dt, player_rect, attack_manager, particles, world):
        if not self.alive:
            self._dead_timer += dt
            return
        self._iframe_timer = max(0.0, self._iframe_timer - dt)
        self._atk_timer = max(0.0, self._atk_timer - dt)
        self._hit_flash = max(0.0, self._hit_flash - dt)

        # Activate when player is close enough
        dx = abs(self.rect.centerx - player_rect.centerx)
        dy = abs(self.rect.centery - player_rect.centery)
        if dx < self._aggro_range and dy < 400:
            self._active = True

        if not self._active:
            return

        self._ai(dt, player_rect, attack_manager, particles)
        self._apply_physics(dt, world)

    def _ai(self, dt, player_rect, attack_manager, particles):
        """Override in subclass."""
        pass

    def _try_melee(self, player_rect, attack_manager, reach=60,
                   knockback_x=250, knockback_y=-200):
        if self._atk_timer > 0:
            return
        if abs(self.rect.centerx - player_rect.centerx) < reach + 30:
            hb_w = reach
            hx = self.rect.right if self.facing == 1 else self.rect.left - hb_w
            attack_manager.add_hitbox(MeleeHitbox(
                hx, self.rect.top + 10, hb_w, self.rect.h - 10,
                damage=self.damage, owner='mob',
                knockback_x=knockback_x * self.facing,
                knockback_y=knockback_y,
                duration=0.18,
            ))
            self._atk_timer = 1.2

    def draw(self, surface, camera_offset):
        """Override in subclass for custom look."""
        cx = self.rect.x - camera_offset[0]
        cy = self.rect.y - camera_offset[1]
        col = (255, 255, 255) if self._hit_flash > 0 else (200, 80, 80)
        pygame.draw.rect(surface, col, (cx, cy, self.rect.w, self.rect.h))
        # HP bar above
        if self.hp < self.max_hp:
            bar_w = self.rect.w
            fill = int(bar_w * self.hp_frac)
            pygame.draw.rect(surface, (80, 10, 10), (cx, cy - 8, bar_w, 5))
            pygame.draw.rect(surface, (220, 50, 50), (cx, cy - 8, fill, 5))


# ── Goblin ────────────────────────────────────────────────────────────────────

class Goblin(Mob):
    W, H = 26, 38

    def __init__(self, x, y):
        super().__init__(x, y, self.W, self.H,
                         hp=40, defense=1, speed=140, damage=10,
                         xp_reward=15,
                         drops=[("mob_fang", 0.6), ("wood", 0.4)])
        self._jump_timer = random.uniform(1.5, 3.0)

    def _ai(self, dt, player_rect, attack_manager, particles):
        self._move_toward(player_rect.centerx, stop=45)
        self._try_melee(player_rect, attack_manager, reach=50, knockback_x=220)
        # Random small jumps
        self._jump_timer -= dt
        if self._jump_timer <= 0 and self.on_ground:
            self.vy = -480
            self._jump_timer = random.uniform(1.5, 3.5)

    def draw(self, surface, camera_offset):
        cx = self.rect.x - camera_offset[0]
        cy = self.rect.y - camera_offset[1]
        col = (255, 255, 255) if self._hit_flash > 0 else (80, 160, 60)
        # Body
        pygame.draw.rect(surface, col, (cx, cy + 8, self.W, self.H - 8))
        # Head
        pygame.draw.rect(surface, col, (cx + 2, cy, self.W - 4, 14))
        # Eyes
        ex = cx + (14 if self.facing == 1 else 4)
        pygame.draw.rect(surface, (255, 220, 0), (ex, cy + 3, 7, 5))
        # Ears
        pygame.draw.polygon(surface, col, [
            (cx, cy), (cx - 5, cy - 8), (cx + 4, cy)])
        pygame.draw.polygon(surface, col, [
            (cx + self.W, cy), (cx + self.W + 5, cy - 8), (cx + self.W - 4, cy)])
        if self.hp < self.max_hp:
            bar_w = self.W
            fill = int(bar_w * self.hp_frac)
            pygame.draw.rect(surface, (80, 10, 10), (cx, cy - 8, bar_w, 5))
            pygame.draw.rect(surface, (220, 50, 50), (cx, cy - 8, fill, 5))


# ── Eyebat ────────────────────────────────────────────────────────────────────

class Eyebat(Mob):
    W, H = 28, 22

    def __init__(self, x, y):
        super().__init__(x, y, self.W, self.H,
                         hp=25, defense=0, speed=110, damage=8,
                         xp_reward=12,
                         drops=[("mob_eye", 0.7), ("stick", 0.3)])
        self._hover_y = float(y - 60)
        self._bob_t = random.uniform(0, math.pi * 2)
        self._shoot_timer = random.uniform(2.0, 4.0)
        self._aggro_range = 600

    def _apply_physics(self, dt, world):
        # Eyebat flies — ignore gravity, just hover
        self._bob_t += dt * 2.0
        target_y = self._hover_y + math.sin(self._bob_t) * 20
        self.rect.y += int((target_y - self.rect.y) * 5 * dt)

    def _ai(self, dt, player_rect, attack_manager, particles):
        self._move_toward(player_rect.centerx, stop=160)
        # Keep floating about 80px above player
        self._hover_y = float(player_rect.top - 80)

        # Shoot projectile
        self._shoot_timer -= dt
        if self._shoot_timer <= 0:
            self._shoot_timer = random.uniform(2.0, 4.0)
            cx, cy = self.center
            dx = player_rect.centerx - cx
            dy = player_rect.centery - cy
            dist = math.hypot(dx, dy) or 1
            spd = 260.0
            proj = Projectile(cx, cy, dx / dist * spd, dy / dist * spd,
                              damage=self.damage, owner='mob',
                              color=(200, 50, 200), radius=6, lifetime=3.0)
            attack_manager.add_projectile(proj)
            particles.emit_magic(cx, cy)

    def draw(self, surface, camera_offset):
        cx = self.rect.x - camera_offset[0]
        cy = self.rect.y - camera_offset[1]
        col = (255, 255, 255) if self._hit_flash > 0 else (120, 50, 160)
        # Wing left
        pygame.draw.ellipse(surface, col, (cx - 14, cy + 4, 18, 10))
        # Wing right
        pygame.draw.ellipse(surface, col, (cx + self.W - 4, cy + 4, 18, 10))
        # Body (eye)
        pygame.draw.ellipse(surface, col, (cx, cy, self.W, self.H))
        # Pupil
        pupil_col = (255, 60, 60) if self._hit_flash <= 0 else (255, 255, 200)
        pygame.draw.circle(surface, pupil_col,
                           (cx + self.W // 2, cy + self.H // 2), 7)
        pygame.draw.circle(surface, (0, 0, 0),
                           (cx + self.W // 2, cy + self.H // 2), 3)
        if self.hp < self.max_hp:
            bar_w = self.W + 14
            fill = int(bar_w * self.hp_frac)
            pygame.draw.rect(surface, (80, 10, 10), (cx - 7, cy - 10, bar_w, 5))
            pygame.draw.rect(surface, (220, 50, 50), (cx - 7, cy - 10, fill, 5))


# ── Stone Golem ───────────────────────────────────────────────────────────────

class StoneGolem(Mob):
    W, H = 44, 60

    def __init__(self, x, y):
        super().__init__(x, y, self.W, self.H,
                         hp=120, defense=5, speed=70, damage=18,
                         xp_reward=35,
                         drops=[("stone", 0.9), ("mob_fang", 0.4)])

    def _ai(self, dt, player_rect, attack_manager, particles):
        self._move_toward(player_rect.centerx, stop=50)
        self._try_melee(player_rect, attack_manager, reach=60, knockback_x=400)

    def draw(self, surface, camera_offset):
        cx = self.rect.x - camera_offset[0]
        cy = self.rect.y - camera_offset[1]
        col = (255, 255, 255) if self._hit_flash > 0 else (110, 110, 100)
        # Body
        pygame.draw.rect(surface, col, (cx, cy + 14, self.W, self.H - 14))
        # Head (square)
        pygame.draw.rect(surface, col, (cx + 4, cy, self.W - 8, 20))
        # Eyes
        pygame.draw.rect(surface, (255, 140, 0), (cx + 8, cy + 4, 8, 6))
        pygame.draw.rect(surface, (255, 140, 0), (cx + self.W - 16, cy + 4, 8, 6))
        # Cracks
        pygame.draw.line(surface, (60, 60, 50),
                         (cx + 10, cy + 20), (cx + 18, cy + 40), 2)
        if self.hp < self.max_hp:
            bar_w = self.W
            fill = int(bar_w * self.hp_frac)
            pygame.draw.rect(surface, (80, 10, 10), (cx, cy - 8, bar_w, 5))
            pygame.draw.rect(surface, (220, 50, 50), (cx, cy - 8, fill, 5))


# ── Medium Boss base ──────────────────────────────────────────────────────────

class MediumBoss(Mob):
    """
    Medium boss: 3-attack AI, telegraphed, drops guardian_core.
    """

    def __init__(self, x, y, w, h, hp, defense, speed, damage, name, color):
        super().__init__(x, y, w, h, hp=hp, defense=defense, speed=speed,
                         damage=damage, xp_reward=120,
                         drops=[("mid_boss_core", 1.0),
                                ("mob_fang", 0.8),
                                ("mob_eye", 0.6)])
        self.name = name
        self.color = color
        self._phase2 = False
        self._state = "patrol"
        self._state_t = 2.0
        self._telegraph = 0.0
        self._pending = None
        self._aggro_range = 1200

    def _check_phase(self):
        if not self._phase2 and self.hp_frac < 0.5:
            self._phase2 = True
            self.speed *= 1.4
            self.damage = int(self.damage * 1.3)

    def update(self, dt, player_rect, attack_manager, particles, world):
        if not self.alive:
            self._dead_timer += dt
            if self._dead_timer < 2.5 and random.random() < 0.4:
                particles.emit_fire(
                    self.rect.centerx + random.randint(-30, 30),
                    self.rect.centery + random.randint(-20, 20), 10)
            return
        self._iframe_timer = max(0.0, self._iframe_timer - dt)
        self._atk_timer = max(0.0, self._atk_timer - dt)
        self._hit_flash = max(0.0, self._hit_flash - dt)
        self._check_phase()

        dx = abs(self.rect.centerx - player_rect.centerx)
        if dx < self._aggro_range:
            self._active = True
        if not self._active:
            return

        self._boss_ai(dt, player_rect, attack_manager, particles)
        self._apply_physics(dt, world)

    def _boss_ai(self, dt, player_rect, attack_manager, particles):
        self._state_t -= dt
        if self._state == "patrol":
            self._move_toward(player_rect.centerx, stop=80)
            if self._state_t <= 0:
                self._telegraph = 0.8
                self._pending = random.choice(["slam", "charge", "volley"])
                self._state = "telegraph"
                self._state_t = self._telegraph
        elif self._state == "telegraph":
            self.vx = 0
            if self._state_t <= 0:
                self._fire_attack(self._pending, player_rect, attack_manager, particles)
                self._state = "cooldown"
                self._state_t = 2.5 if not self._phase2 else 1.6
        elif self._state == "cooldown":
            self._move_toward(player_rect.centerx, stop=100)
            if self._state_t <= 0:
                self._state = "patrol"
                self._state_t = 0.5

    def _fire_attack(self, name, player_rect, attack_manager, particles):
        bx, by = float(self.rect.centerx), float(self.rect.centery)
        if name == "slam":
            self.vy = -550
            dx = player_rect.centerx - self.rect.centerx
            self.vx = math.copysign(min(abs(dx), 500), dx)
        elif name == "charge":
            dx = player_rect.centerx - self.rect.centerx
            self.vx = math.copysign(self.speed * 2.5, dx)
            attack_manager.add_hitbox(MeleeHitbox(
                self.rect.left, self.rect.top + 10,
                self.rect.w, self.rect.h - 10,
                damage=self.damage + 5, owner='mob',
                knockback_x=self.vx * 0.4, knockback_y=-240,
                duration=0.5,
            ))
        elif name == "volley":
            for i in range(5):
                angle = -math.pi / 2 + (i - 2) * 0.35
                spd = 280.0
                proj = Projectile(bx, by,
                                  math.cos(angle) * spd,
                                  math.sin(angle) * spd,
                                  damage=self.damage,
                                  owner='mob',
                                  color=self.color,
                                  radius=9)
                attack_manager.add_projectile(proj)
            particles.emit_fire(bx, by, 16)

    def draw(self, surface, camera_offset):
        cx = self.rect.x - camera_offset[0]
        cy = self.rect.y - camera_offset[1]
        col = (255, 255, 255) if self._hit_flash > 0 else self.color

        pygame.draw.rect(surface, col, (cx, cy, self.rect.w, self.rect.h))
        # Eyes
        ey = cy + 18
        for ex_off in (12, self.rect.w - 22):
            pygame.draw.circle(surface, (255, 220, 0),
                               (cx + ex_off, ey), 8)
        # Telegraph warning ring
        if self._state == "telegraph":
            frac = 1.0 - self._state_t / 0.8
            r = int(max(self.rect.w, self.rect.h) * 0.7 + frac * 30)
            if int(frac * 8) % 2 == 0:
                pygame.draw.circle(surface, (255, 80, 0),
                                   (cx + self.rect.w // 2, cy + self.rect.h // 2),
                                   r, 3)
        # HP bar
        bar_w = self.rect.w + 20
        fill = int(bar_w * self.hp_frac)
        bx2 = cx - 10
        pygame.draw.rect(surface, (80, 10, 10), (bx2, cy - 14, bar_w, 8))
        pygame.draw.rect(surface, (220, 50, 50), (bx2, cy - 14, fill, 8))
        name_s = pygame.font.SysFont("monospace", 11, bold=True).render(
            self.name, True, (255, 200, 200))
        surface.blit(name_s, (cx + self.rect.w // 2 - name_s.get_width() // 2,
                              cy - 26))


class ForestGuardian(MediumBoss):
    def __init__(self, x, y):
        super().__init__(x, y, w=64, h=88, hp=400, defense=4,
                         speed=130, damage=22,
                         name="Forest Guardian",
                         color=(60, 160, 60))


class CaveWarden(MediumBoss):
    def __init__(self, x, y):
        super().__init__(x, y, w=72, h=96, hp=550, defense=6,
                         speed=100, damage=28,
                         name="Cave Warden",
                         color=(90, 70, 130))


# ── Mob manager ───────────────────────────────────────────────────────────────

class MobManager:
    """Holds all mobs in the current zone. Handles updates + collision."""

    def __init__(self):
        self.mobs: list[Mob] = []
        self._loot_pending: list[tuple[str, float, float]] = []

    def add(self, mob: Mob):
        self.mobs.append(mob)

    def update(self, dt, player_rect, attack_manager, particles, world) -> list[str]:
        """Returns list of item_ids to give player (drops from dead mobs)."""
        drops = []
        for mob in self.mobs:
            mob.update(dt, player_rect, attack_manager, particles, world)
            if not mob.alive and mob._dead_timer < dt * 2:  # just died this frame
                drops.extend(mob.get_drops())
        self.mobs = [m for m in self.mobs
                     if m.alive or m._dead_timer < 3.0]
        return drops

    def draw(self, surface, camera_offset):
        for mob in self.mobs:
            mob.draw(surface, camera_offset)

    def resolve_player_attacks(self, attack_manager, player,
                               particles, shake) -> int:
        """
        Check player attacks against all mobs.
        Returns total XP earned this frame.
        """
        from src.settings import PLAYER_CRIT_CHANCE, PLAYER_CRIT_MULTI
        import random, math as _math
        xp_gained = 0
        consumed = set()

        for proj in attack_manager.projectiles:
            if proj.owner != 'player' or not proj.alive:
                continue
            for mob in self.mobs:
                if not mob.alive:
                    continue
                if proj.rect.colliderect(mob.rect):
                    raw = proj.damage
                    crit = random.random() < PLAYER_CRIT_CHANCE
                    final = max(1, int(raw * PLAYER_CRIT_MULTI) if crit
                    else raw - mob.defense)
                    mob.take_damage(final, particles, knockback_x=proj.vx * 0.2)
                    if not mob.alive:
                        xp_gained += mob.xp_reward
                    if not proj.pierce:
                        proj.alive = False
                    break

        for idx, hb in enumerate(attack_manager.hitboxes):
            if hb.owner != 'player' or not hb.alive or idx in consumed:
                continue
            for mob in self.mobs:
                if not mob.alive:
                    continue
                if hb.rect.colliderect(mob.rect):
                    raw = hb.damage
                    crit = random.random() < PLAYER_CRIT_CHANCE
                    final = max(1, int(raw * PLAYER_CRIT_MULTI) if crit
                    else raw - mob.defense)
                    mob.take_damage(final, particles,
                                    knockback_x=hb.knockback[0],
                                    knockback_y=hb.knockback[1])
                    if not mob.alive:
                        xp_gained += mob.xp_reward
                    consumed.add(idx)
                    break

        return xp_gained

    def resolve_mob_attacks_on_player(self, attack_manager, player,
                                      particles, shake):
        """Mob projectiles/hitboxes tagged 'mob' hit the player."""
        for proj in attack_manager.projectiles:
            if proj.owner != 'mob' or not proj.alive:
                continue
            if proj.rect.colliderect(player.rect) and not player.invincible:
                player.take_damage(proj.damage,
                                   knockback_x=proj.vx * 0.3,
                                   knockback_y=-160,
                                   particles=particles)
                shake.add(0.25)
                if not proj.pierce:
                    proj.alive = False

        for hb in attack_manager.hitboxes:
            if hb.owner != 'mob' or not hb.alive:
                continue
            if hb.rect.colliderect(player.rect) and not player.invincible:
                player.take_damage(hb.damage,
                                   knockback_x=hb.knockback[0],
                                   knockback_y=hb.knockback[1],
                                   particles=particles)
                shake.add(0.3)

    def clear(self):
        self.mobs.clear()
