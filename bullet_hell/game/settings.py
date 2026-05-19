import math
import os

WIDTH, HEIGHT = 600, 800
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 00)
BLUE = (0, 200, 255)
YELLOW = (255, 255, 0)

PLAYER_SPEED = 5
PLAYER_FOCUS_SPEED = 2
BULLET_SPEED = 4

BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

PLAYER_MAX_HEALTH = 5
PLAYER_BULLET_DAMAGE = 10

BOSS_MAX_HEALTH = 1000
BOSS_HITBOX_RADIUS = 20

BASE_DIR = os.path.dirname(__file__)
SCORE_FILE = os.path.join(BASE_DIR, "high_score.json")