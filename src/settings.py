# =============================================================================
# settings.py — Global constants and configuration
# All tunable values live here to avoid magic numbers throughout the codebase.
# TODO: Load these from a JSON/YAML config file for easy modding support.
# =============================================================================

# ── Window ────────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
TITLE         = "Boss Rush"
FPS           = 60

# ── Physics ───────────────────────────────────────────────────────────────────
GRAVITY          = 1800.0   # px / s²
TERMINAL_VELOCITY = 900.0  # px / s  (max fall speed)

# ── Camera ────────────────────────────────────────────────────────────────────
CAMERA_LERP = 6.0           # smoothing factor (higher = tighter)

# ── Player ────────────────────────────────────────────────────────────────────
PLAYER_SPEED        = 300.0
PLAYER_JUMP_FORCE   = -700.0
PLAYER_DASH_SPEED   = 750.0
PLAYER_DASH_DURATION = 0.18   # seconds
PLAYER_DASH_COOLDOWN = 0.9
PLAYER_MAX_HP       = 100
PLAYER_MAX_MANA     = 80
PLAYER_DEFENSE      = 5
PLAYER_ATTACK       = 20
PLAYER_ATTACK_RANGE = 70      # melee hitbox reach (px)
PLAYER_ATTACK_RATE  = 0.35    # seconds between swings
PLAYER_IFRAMES      = 0.6     # invincibility duration after hit
PLAYER_CRIT_CHANCE  = 0.15    # 0–1
PLAYER_CRIT_MULTI   = 2.0

# Ranged
PLAYER_MANA_COST_SHOT  = 12
PLAYER_MANA_REGEN      = 8.0   # per second
PLAYER_PROJECTILE_SPEED = 620.0
PLAYER_RANGED_ATTACK    = 15
PLAYER_RANGED_COOLDOWN  = 0.5

# ── Boss ──────────────────────────────────────────────────────────────────────
BOSS_MAX_HP          = 1500
BOSS_DEFENSE         = 8
BOSS_SPEED_PHASE1    = 160.0
BOSS_SPEED_PHASE2    = 260.0
BOSS_ENRAGE_HP_FRAC  = 0.35   # enrage below this fraction of max HP
BOSS_WIDTH           = 96
BOSS_HEIGHT          = 120

# ── Projectiles ───────────────────────────────────────────────────────────────
BOSS_PROJ_SPEED      = 340.0
BOSS_PROJ_DAMAGE     = 18
BOSS_FIREBALL_SPEED  = 220.0
BOSS_FIREBALL_DAMAGE = 30

# ── Arena / World ─────────────────────────────────────────────────────────────
ARENA_WIDTH  = 3200
ARENA_HEIGHT = 900
FLOOR_Y      = 830          # y-position of main floor top surface

# Parallax layer scroll factors (0 = static, 1 = moves with camera)
PARALLAX_LAYERS = [0.1, 0.25, 0.45]

# ── Particles ─────────────────────────────────────────────────────────────────
SCREEN_SHAKE_DECAY  = 12.0   # how fast shake dissipates
MAX_PARTICLES       = 400

# ── Colors ────────────────────────────────────────────────────────────────────
# Dark-fantasy palette
C_BG_SKY        = (10,  8,  22)
C_BG_FAR        = (20, 15, 40)
C_BG_MID        = (30, 22, 55)
C_BG_NEAR       = (40, 30, 65)
C_FLOOR         = (50, 40, 70)
C_PLATFORM      = (70, 55, 90)
C_PLATFORM_TOP  = (100, 80, 120)

C_PLAYER        = (90, 190, 255)
C_PLAYER_DASH   = (180, 230, 255)
C_PLAYER_SWORD  = (220, 220, 100)
C_PLAYER_MANA   = (60, 120, 230)

C_BOSS_P1       = (180, 50,  50)
C_BOSS_P2       = (230, 80,  20)
C_BOSS_ENRAGE   = (255, 30,  10)
C_BOSS_EYE      = (255, 255, 80)
C_BOSS_PROJ     = (255, 120, 30)
C_BOSS_FIREBALL = (255, 60, 10)

C_HP_BAR_BG     = (60, 10, 10)
C_HP_BAR_FG     = (220, 50, 50)
C_HP_BAR_FG2    = (255, 200, 0)   # enraged
C_MANA_BAR_BG   = (10, 20, 60)
C_MANA_BAR_FG   = (60, 120, 250)
C_BOSS_HP_BG    = (40, 10, 10)
C_BOSS_HP_FG    = (200, 30, 30)

C_DMG_PLAYER    = (255, 100, 100)
C_DMG_BOSS      = (255, 240, 60)
C_DMG_CRIT      = (255, 80, 255)
C_HEAL          = (80, 255, 130)

C_WHITE         = (255, 255, 255)
C_BLACK         = (0, 0, 0)
C_GRAY          = (120, 120, 120)
