# =============================================================================
# player.py — Player entity: movement, combat, mana, leveling, rendering
# TODO: Add sprite sheets, animation FSM, equipment slots, skill tree.
# =============================================================================

import pygame
import math
from src.settings import *
from src.attacks  import Projectile, MeleeHitbox
from src.particles import ParticleSystem


class Player:
    """
    The hero character.  Uses axis-aligned bounding box (AABB) physics.
    All velocity in px/s; all timers in seconds.
    """

    WIDTH  = 28
    HEIGHT = 52

    def __init__(self, x: float, y: float):
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)

        # ── Physics ───────────────────────────────────────────────────────
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.on_ground: bool = False
        self.facing: int = 1          # 1 = right, -1 = left

        # ── Stats ─────────────────────────────────────────────────────────
        self.max_hp   = PLAYER_MAX_HP
        self.hp       = self.max_hp
        self.max_mana = PLAYER_MAX_MANA
        self.mana     = self.max_mana
        self.defense  = PLAYER_DEFENSE
        self.attack   = PLAYER_ATTACK
        self.level    = 1
        self.xp       = 0
        self.xp_next  = 100   # XP needed for next level

        # ── Timers / state ────────────────────────────────────────────────
        self._iframe_timer    = 0.0   # invincibility frames remaining
        self._atk_timer       = 0.0   # melee cooldown
        self._ranged_timer    = 0.0   # ranged cooldown
        self._dash_timer      = 0.0   # dash duration
        self._dash_cd_timer   = 0.0   # dash cooldown
        self._dash_vx         = 0.0   # locked dash velocity
        self._is_dashing      = False
        self._jump_buffer     = 0.0   # coyote + buffer window
        self._swing_anim      = 0.0   # sword swing visual timer
        self._hit_flash       = 0.0   # red flash when hurt

        # ── Status flags ──────────────────────────────────────────────────
        self.alive  = True
        self.dead_timer = 0.0   # delay before game-over screen

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def center(self) -> tuple[float, float]:
        return float(self.rect.centerx), float(self.rect.centery)

    @property
    def invincible(self) -> bool:
        return self._iframe_timer > 0

    @property
    def can_dash(self) -> bool:
        return self._dash_cd_timer <= 0 and not self._is_dashing

    @property
    def hp_frac(self) -> float:
        return max(0.0, self.hp / self.max_hp)

    @property
    def mana_frac(self) -> float:
        return max(0.0, self.mana / self.max_mana)

    # ── Input & actions ───────────────────────────────────────────────────────

    def handle_input(self, keys, dt,
                     attack_manager, particles: ParticleSystem):
        if not self.alive:
            return

        # Horizontal movement
        if not self._is_dashing:
            self.vx = 0.0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.vx    = -PLAYER_SPEED
                self.facing = -1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.vx    = PLAYER_SPEED
                self.facing = 1

        # Jump (with coyote time & jump buffer)
        if keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]:
            self._jump_buffer = 0.12
        if self._jump_buffer > 0 and self.on_ground:
            self.vy           = PLAYER_JUMP_FORCE
            self._jump_buffer = 0.0
            particles.emit_dust(self.rect.centerx, self.rect.bottom)

        # Dash (Shift)
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.can_dash:
            self._start_dash()
            particles.emit_hit(self.rect.centerx, self.rect.centery,
                               C_PLAYER_DASH, count=8, speed=120, gravity=0)

        # Melee attack (Z / J)
        if (keys[pygame.K_z] or keys[pygame.K_j]) and self._atk_timer <= 0:
            self._melee_attack(attack_manager, particles)

        # Ranged attack (X / K)
        if (keys[pygame.K_x] or keys[pygame.K_k]) and self._ranged_timer <= 0:
            self._ranged_attack(attack_manager, particles)

    def _start_dash(self):
        self._is_dashing    = True
        self._dash_timer    = PLAYER_DASH_DURATION
        self._dash_cd_timer = PLAYER_DASH_COOLDOWN
        self._iframe_timer  = PLAYER_DASH_DURATION  # invincible during dash
        self._dash_vx       = PLAYER_DASH_SPEED * self.facing
        self.vy             = 0.0   # cancel vertical momentum

    def _melee_attack(self, attack_manager, particles: ParticleSystem):
        self._atk_timer  = PLAYER_ATTACK_RATE
        self._swing_anim = 0.25

        # Build hitbox in front of player
        hb_w = PLAYER_ATTACK_RANGE
        hb_h = self.HEIGHT
        if self.facing == 1:
            hx = self.rect.right
        else:
            hx = self.rect.left - hb_w

        kb_x = 300 * self.facing
        hb = MeleeHitbox(
            hx, self.rect.top, hb_w, hb_h,
            damage=self.attack,
            owner='player',
            knockback_x=kb_x, knockback_y=-200,
            duration=0.12,
        )
        attack_manager.add_hitbox(hb)
        particles.emit_hit(
            self.rect.centerx + self.facing * 40,
            self.rect.centery,
            C_PLAYER_SWORD, count=6, speed=120, gravity=200,
        )

    def _ranged_attack(self, attack_manager, particles: ParticleSystem):
        if self.mana < PLAYER_MANA_COST_SHOT:
            return
        self.mana          -= PLAYER_MANA_COST_SHOT
        self._ranged_timer  = PLAYER_RANGED_COOLDOWN

        cx, cy = self.center
        vx     = PLAYER_PROJECTILE_SPEED * self.facing
        proj   = Projectile(
            cx, cy, vx, 0,
            damage=PLAYER_RANGED_ATTACK,
            owner='player',
            color=C_PLAYER_MANA,
            radius=7,
        )
        attack_manager.add_projectile(proj)
        particles.emit_magic(cx + self.facing * 20, cy)

    # ── Take damage ───────────────────────────────────────────────────────────

    def take_damage(self, raw_damage: int,
                    knockback_x: float = 0,
                    knockback_y: float = 0,
                    particles: ParticleSystem = None) -> int:
        if self.invincible or not self.alive:
            return 0

        final = max(1, raw_damage - self.defense)
        self.hp             -= final
        self._iframe_timer   = PLAYER_IFRAMES
        self._hit_flash      = 0.25
        self.vx              = knockback_x
        self.vy              = knockback_y

        if particles:
            particles.emit_blood(self.rect.centerx, self.rect.centery, 10)
            particles.spawn_damage(
                self.rect.centerx, self.rect.top - 10, final,
                color=C_DMG_PLAYER,
            )

        if self.hp <= 0:
            self.hp    = 0
            self.alive = False

        return final

    # ── XP / Leveling ─────────────────────────────────────────────────────────

    def gain_xp(self, amount: int):
        """Award XP and level up if threshold reached."""
        self.xp += amount
        while self.xp >= self.xp_next:
            self.xp     -= self.xp_next
            self.level  += 1
            self.xp_next = int(self.xp_next * 1.4)
            self._on_level_up()

    def _on_level_up(self):
        """Apply level-up bonuses. TODO: Show selection UI (pick perk)."""
        self.max_hp  += 15
        self.hp       = self.max_hp   # full heal on level-up
        self.attack  += 3
        self.defense += 1
        self.max_mana += 10
        self.mana     = self.max_mana

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float, world, particles: ParticleSystem):
        if not self.alive:
            self.dead_timer += dt
            return

        # ── Timers ────────────────────────────────────────────────────────
        self._iframe_timer  = max(0.0, self._iframe_timer  - dt)
        self._atk_timer     = max(0.0, self._atk_timer     - dt)
        self._ranged_timer  = max(0.0, self._ranged_timer  - dt)
        self._dash_cd_timer = max(0.0, self._dash_cd_timer - dt)
        self._swing_anim    = max(0.0, self._swing_anim    - dt)
        self._hit_flash     = max(0.0, self._hit_flash     - dt)
        self._jump_buffer   = max(0.0, self._jump_buffer   - dt)

        # ── Dash state ────────────────────────────────────────────────────
        if self._is_dashing:
            self._dash_timer -= dt
            self.vx           = self._dash_vx
            self.vy           = 0.0
            if self._dash_timer <= 0:
                self._is_dashing = False
                self.vx          = 0.0

        # ── Gravity ───────────────────────────────────────────────────────
        if not self._is_dashing:
            self.vy += GRAVITY * dt
            self.vy  = min(self.vy, TERMINAL_VELOCITY)

        # ── Mana regeneration ─────────────────────────────────────────────
        self.mana = min(self.max_mana, self.mana + PLAYER_MANA_REGEN * dt)

        # ── Move & collide ────────────────────────────────────────────────
        self.rect.x += int(self.vx * dt)
        self.rect, self.vx = world.resolve_horizontal(self.rect, self.vx)

        self.rect.y += int(self.vy * dt)
        was_on_ground = self.on_ground
        self.rect, self.vy, self.on_ground = world.resolve_vertical(
            self.rect, self.vy
        )
        if self.on_ground and not was_on_ground and self.vy == 0:
            particles.emit_dust(self.rect.centerx, self.rect.bottom)

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int]):
        cx = self.rect.x - camera_offset[0]
        cy = self.rect.y - camera_offset[1]

        # Flash white on iframe
        body_color = C_PLAYER
        if self._iframe_timer > 0:
            if int(self._iframe_timer * 10) % 2 == 0:
                return   # blink by skipping draw
        if self._hit_flash > 0:
            body_color = (255, 80, 80)

        # Body
        pygame.draw.rect(surface, body_color,
                         (cx, cy, self.WIDTH, self.HEIGHT))

        # Eyes (visor)
        eye_x = cx + (8 if self.facing == 1 else 6)
        pygame.draw.rect(surface, (255, 255, 200), (eye_x, cy + 10, 12, 6))

        # Sword swing arc
        if self._swing_anim > 0:
            frac   = self._swing_anim / 0.25
            angle  = self.facing * frac * 90 - 45
            rad    = math.radians(angle)
            sx     = cx + self.WIDTH // 2 + int(math.cos(rad) * 50) * self.facing
            sy     = cy + 20 + int(math.sin(rad) * 30)
            pygame.draw.line(surface, C_PLAYER_SWORD,
                             (cx + self.WIDTH // 2, cy + 20),
                             (sx, sy), 5)

        # Dash trail ghost
        if self._is_dashing:
            ghost = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            ghost.fill((*C_PLAYER_DASH, 80))
            surface.blit(ghost, (cx - self.facing * 20, cy))
