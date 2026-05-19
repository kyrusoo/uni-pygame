# =============================================================================
# boss.py — Multi-phase boss "Malvortex the Dread Titan"
#
# Phase 1  (HP > 35%): patrol + projectile volley + ground slam
# Phase 2  (HP ≤ 35%): faster, enraged color, adds fireball arc + charge
#
# Attack FSM states:
#   idle → telegraph → attack → cooldown → idle
#
# TODO: Add minion spawning, beam attack, second boss form.
# =============================================================================

import pygame
import math
import random
from src.settings import *
from src.attacks import Projectile, Fireball, MeleeHitbox
from src.particles import ParticleSystem

# ── Attack identifiers ────────────────────────────────────────────────────────
ATKS = {
    "PATROL": 0,
    "PROJ_VOLLEY": 1,  # spray of projectiles
    "GROUND_SLAM": 2,  # leap + landing shockwave
    "CHARGE": 3,  # horizontal rush (phase 2)
    "FIREBALL_ARC": 4,  # arc of 5 fireballs (phase 2)
}


class Boss:
    """
    Malvortex — the main boss entity.
    All AI logic is driven by a lightweight FSM with timers.
    """

    def __init__(self, x: float, y: float):
        self.rect = pygame.Rect(
            int(x - BOSS_WIDTH // 2), int(y - BOSS_HEIGHT),
            BOSS_WIDTH, BOSS_HEIGHT,
        )

        # ── Stats ─────────────────────────────────────────────────────────
        self.max_hp = BOSS_MAX_HP
        self.hp = self.max_hp
        self.defense = BOSS_DEFENSE
        self.alive = True

        # Physics
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.on_ground = True
        self.facing = -1  # faces left (toward player) initially

        # ── Phase / AI state ──────────────────────────────────────────────
        self.phase = 1  # 1 or 2
        self.enraged = False
        self.ai_state = "idle"
        self.state_timer = 1.2  # initial pause before first attack
        self.current_atk = ATKS["PATROL"]

        # Telegraph timer (show warning before striking)
        self._telegraph_timer = 0.0
        self._pending_attack = None

        # Cooldown lookup (seconds) per attack
        self._cooldowns = {
            ATKS["PATROL"]: 0.0,
            ATKS["PROJ_VOLLEY"]: 3.5,
            ATKS["GROUND_SLAM"]: 5.0,
            ATKS["CHARGE"]: 4.0,
            ATKS["FIREBALL_ARC"]: 4.5,
        }

        # Damage numbers / flash
        self._hit_flash = 0.0
        self._flash_color = C_BOSS_P1

        # Animation
        self._eye_pulse = 0.0
        self._bob_offset = 0.0

        # ── Death ─────────────────────────────────────────────────────────
        self.dead_timer = 0.0

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def hp_frac(self) -> float:
        return max(0.0, self.hp / self.max_hp)

    @property
    def center(self) -> tuple[float, float]:
        return float(self.rect.centerx), float(self.rect.centery)

    @property
    def speed(self) -> float:
        return BOSS_SPEED_PHASE2 if self.phase == 2 else BOSS_SPEED_PHASE1

    # ── Damage ────────────────────────────────────────────────────────────────

    def take_damage(self, raw_damage: int, crit: bool,
                    particles: ParticleSystem) -> int:
        if not self.alive:
            return 0

        final = max(1, raw_damage - self.defense)
        self.hp -= final
        self._hit_flash = 0.12
        color = C_DMG_CRIT if crit else C_DMG_BOSS

        particles.emit_hit(self.rect.centerx, self.rect.centery,
                           color, count=14, speed=220, gravity=300)
        particles.spawn_damage(
            self.rect.centerx,
            self.rect.top - 15,
            final,
            color=color,
            crit=crit,
        )

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.dead_timer = 0.0

        return final

    # ── Phase check ───────────────────────────────────────────────────────────

    def _check_phase(self):
        if self.phase == 1 and self.hp_frac <= BOSS_ENRAGE_HP_FRAC:
            self.phase = 2
            self.enraged = True

    # ── AI FSM ────────────────────────────────────────────────────────────────

    def _pick_next_attack(self) -> int:
        if self.phase == 1:
            choices = [
                ATKS["PROJ_VOLLEY"],
                ATKS["PROJ_VOLLEY"],
                ATKS["GROUND_SLAM"],
            ]
        else:
            choices = [
                ATKS["PROJ_VOLLEY"],
                ATKS["GROUND_SLAM"],
                ATKS["CHARGE"],
                ATKS["FIREBALL_ARC"],
                ATKS["FIREBALL_ARC"],
            ]
        return random.choice(choices)

    def _begin_telegraph(self, attack_id: int):
        """Show warning before executing attack."""
        self._pending_attack = attack_id
        self._telegraph_timer = 0.9
        self.ai_state = "telegraph"
        self.vx = 0.0  # stop moving during telegraph

    def _execute_attack(self, attack_id: int, player_rect: pygame.Rect,
                        attack_manager, particles: ParticleSystem):
        """Fire the telegraphed attack."""
        px = float(player_rect.centerx)
        py = float(player_rect.centery)
        bx = float(self.rect.centerx)
        by = float(self.rect.centery)

        if attack_id == ATKS["PROJ_VOLLEY"]:
            count = 7 if not self.enraged else 11
            for i in range(count):
                angle = -math.pi / 2 + (i - count // 2) * 0.28
                vx = math.cos(angle) * BOSS_PROJ_SPEED
                vy = math.sin(angle) * BOSS_PROJ_SPEED
                proj = Projectile(bx, by + 20, vx, vy,
                                  damage=BOSS_PROJ_DAMAGE,
                                  owner='boss',
                                  color=C_BOSS_PROJ,
                                  radius=9)
                attack_manager.add_projectile(proj)
            particles.emit_fire(bx, by, 20)

        elif attack_id == ATKS["GROUND_SLAM"]:
            # Leap toward player
            dx = px - bx
            spd = min(abs(dx), 600)
            self.vx = math.copysign(spd, dx)
            self.vy = -600.0

        elif attack_id == ATKS["CHARGE"]:
            # Fast horizontal rush
            self.vx = math.copysign(BOSS_SPEED_PHASE2 * 2.2, px - bx)
            # Brief MeleeHitbox while charging
            hb_x = self.rect.left if self.vx < 0 else self.rect.right - 20
            attack_manager.add_hitbox(MeleeHitbox(
                hb_x, self.rect.top + 20, 80, 80,
                damage=35, owner='boss',
                knockback_x=self.vx * 0.5,
                knockback_y=-250,
                duration=0.45,
            ))

        elif attack_id == ATKS["FIREBALL_ARC"]:
            for i in range(5):
                angle = -math.pi + i * (math.pi / 4)
                vx = math.cos(angle) * BOSS_FIREBALL_SPEED
                vy = math.sin(angle) * BOSS_FIREBALL_SPEED - 150
                fb = Fireball(bx, by, vx, vy)
                attack_manager.add_projectile(fb)
            particles.emit_fire(bx, by, 30)

    def _land_shockwave(self, attack_manager):
        """Called when boss lands from a slam."""
        # Shockwave hitboxes on both sides
        for side in (-1, 1):
            hb_x = self.rect.centerx + side * 30
            attack_manager.add_hitbox(MeleeHitbox(
                hb_x, self.rect.bottom - 30,
                220, 50,
                damage=25, owner='boss',
                knockback_x=side * 380, knockback_y=-300,
                duration=0.3,
            ))

    # ── Patrol movement ───────────────────────────────────────────────────────

    def _move_toward_player(self, player_rect: pygame.Rect, dt: float):
        px = float(player_rect.centerx)
        bx = float(self.rect.centerx)
        dx = px - bx
        spd = self.speed
        if abs(dx) > 80:
            self.vx = math.copysign(spd, dx)
            self.facing = int(math.copysign(1, dx))
        else:
            self.vx = 0.0

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float, player_rect: pygame.Rect,
               attack_manager, particles: ParticleSystem, world):

        if not self.alive:
            self.dead_timer += dt
            # Death explosion particles
            if self.dead_timer < 2.0 and random.random() < 0.4:
                particles.emit_fire(
                    self.rect.centerx + random.randint(-40, 40),
                    self.rect.centery + random.randint(-40, 40),
                    random.randint(6, 16),
                )
            return

        self._check_phase()
        self._eye_pulse += dt * 3.0
        self._bob_offset = math.sin(self._eye_pulse) * 4
        self._hit_flash = max(0.0, self._hit_flash - dt)
        self.state_timer = max(0.0, self.state_timer - dt)

        # ── AI state machine ──────────────────────────────────────────────
        if self.ai_state == "idle":
            self._move_toward_player(player_rect, dt)
            if self.state_timer <= 0:
                next_atk = self._pick_next_attack()
                self._begin_telegraph(next_atk)

        elif self.ai_state == "telegraph":
            self._telegraph_timer -= dt
            self.vx = 0.0  # stand still, menace player
            if self._telegraph_timer <= 0:
                self._execute_attack(self._pending_attack, player_rect,
                                     attack_manager, particles)
                self.ai_state = "attack"
                self.state_timer = 0.55

        elif self.ai_state == "attack":
            # For charge — keep moving until timer expires
            if self._pending_attack == ATKS["CHARGE"]:
                pass  # vx already set
            else:
                self._move_toward_player(player_rect, dt)

            if self.state_timer <= 0:
                cd = self._cooldowns.get(self._pending_attack, 3.0)
                if self.enraged:
                    cd *= 0.65
                self.state_timer = cd
                self.ai_state = "cooldown"
                self.vx = 0.0

        elif self.ai_state == "cooldown":
            self._move_toward_player(player_rect, dt)
            if self.state_timer <= 0:
                self.ai_state = "idle"
                self.state_timer = 0.4

        # ── Physics ───────────────────────────────────────────────────────
        self.vy += GRAVITY * dt
        self.vy = min(self.vy, TERMINAL_VELOCITY)

        prev_on_ground = self.on_ground

        self.rect.x += int(self.vx * dt)
        self.rect, self.vx = world.resolve_horizontal(self.rect, self.vx)

        self.rect.y += int(self.vy * dt)
        self.rect, self.vy, self.on_ground = world.resolve_vertical(
            self.rect, self.vy
        )

        # Ground slam landing shockwave
        if self.on_ground and not prev_on_ground and \
                self._pending_attack == ATKS["GROUND_SLAM"]:
            self._land_shockwave(attack_manager)
            particles.emit_dust(self.rect.centerx, self.rect.bottom, 20)

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int]):
        cx = self.rect.x - camera_offset[0]
        cy = self.rect.y - camera_offset[1] + int(self._bob_offset)

        if not self.alive:
            # Fade out
            alpha = max(0, int(255 * (1.0 - self.dead_timer / 2.0)))
            s = pygame.Surface((BOSS_WIDTH, BOSS_HEIGHT), pygame.SRCALPHA)
            s.fill((*C_BOSS_P1, alpha))
            surface.blit(s, (cx, cy))
            return

        # Pick body color by phase / hit flash
        if self._hit_flash > 0:
            body_color = (255, 255, 255)
        elif self.enraged:
            # Pulsing between two reds
            t = self._eye_pulse
            mix = (math.sin(t * 4) + 1) / 2
            body_color = (
                int(C_BOSS_P2[0] * mix + C_BOSS_ENRAGE[0] * (1 - mix)),
                int(C_BOSS_P2[1] * mix + C_BOSS_ENRAGE[1] * (1 - mix)),
                int(C_BOSS_P2[2] * mix + C_BOSS_ENRAGE[2] * (1 - mix)),
            )
        else:
            body_color = C_BOSS_P1

        # ── Body ──────────────────────────────────────────────────────────
        pygame.draw.rect(surface, body_color, (cx, cy, BOSS_WIDTH, BOSS_HEIGHT))

        # Armored shoulder plates
        pygame.draw.rect(surface, (body_color[0] // 2,) * 3,
                         (cx - 12, cy + 10, 16, 30))
        pygame.draw.rect(surface, (body_color[0] // 2,) * 3,
                         (cx + BOSS_WIDTH - 4, cy + 10, 16, 30))

        # ── Main eye ──────────────────────────────────────────────────────
        eye_glow = int(180 + math.sin(self._eye_pulse) * 75)
        eye_x = cx + BOSS_WIDTH // 2
        eye_y = cy + 30
        pygame.draw.circle(surface, (eye_glow, eye_glow // 2, 0),
                           (eye_x, eye_y), 20)
        pygame.draw.circle(surface, C_BOSS_EYE, (eye_x, eye_y), 12)
        pygame.draw.circle(surface, (0, 0, 0), (eye_x, eye_y), 5)

        # ── Small side eyes (enraged) ──────────────────────────────────────
        if self.enraged:
            for dx in (-25, 25):
                ex, ey = cx + BOSS_WIDTH // 2 + dx, cy + 50
                pygame.draw.circle(surface, C_BOSS_EYE, (ex, ey), 8)

        # ── Telegraph warning flash ────────────────────────────────────────
        if self.ai_state == "telegraph":
            frac = 1.0 - (self._telegraph_timer / 0.9)
            r = max(BOSS_WIDTH, BOSS_HEIGHT) + 20
            # Pulsing ring
            pulse_r = int(r + frac * 40)
            if int(frac * 8) % 2 == 0:
                pygame.draw.circle(surface, (255, 60, 0),
                                   (cx + BOSS_WIDTH // 2, cy + BOSS_HEIGHT // 2),
                                   pulse_r, 3)

        # ── Enrage flame aura ─────────────────────────────────────────────
        if self.enraged and random.random() < 0.6:
            fx = cx + random.randint(0, BOSS_WIDTH)
            fy = cy + random.randint(0, BOSS_HEIGHT)
            r2 = random.randint(4, 10)
            pygame.draw.circle(surface, C_BOSS_FIREBALL, (fx, fy), r2)
