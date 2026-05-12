import math
import os

WIDTH, HEIGHT = 600, 800
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 50)
BLUE = (0, 200, 255)

PLAYER_SPEED = 5
PLAYER_FOCUS_SPEED = 2
BULLET_SPEED = 4

BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')