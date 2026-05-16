import pygame
import math
from settings import *

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed, color=RED):
        super().__init__()
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (4, 4), 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed

    def update(self):
        self.pos += self.vel
        self.rect.center = self.pos
        if not (0 <= self.pos.x <= WIDTH and 0 <= self.pos.y <= HEIGHT):
            self.kill()

class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((4, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = -10                                   # Negative goes UP
        self.damage = PLAYER_BULLET_DAMAGE

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()