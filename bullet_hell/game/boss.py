import pygame
import math
from settings import *
from bullets import Bullet

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((100, 100))
        self.image.fill((200, 200, 200))
        pygame.draw.rect(self.image, RED, (10, 10, 60, 40))
        self.rect = self.image.get_rect(center=(WIDTH//2, 150))

        self.max_health = BOSS_MAX_HEALTH
        self.health = BOSS_MAX_HEALTH

        # Hitbox (Smaller than the 80x60 visual image)
        self.radius = BOSS_HITBOX_RADIUS
        self.angle_offset = 0

    def update(self):
         # Boss health guard
         if self.health <= 0:
            self.health = 0
            self.kill()

    def shoot(self, all_sprites, enemy_bullets):
        self.angle_offset += 0.05
        for i in range(4):
            angle = self.angle_offset + (i * (math.pi / 2))
            b = Bullet(self.rect.centerx, self.rect.centery, math.degrees(angle), 4)
            all_sprites.add(b)
            enemy_bullets.add(b)