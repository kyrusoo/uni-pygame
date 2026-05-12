import pygame
import os
from settings import *


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # Get the path of the current file (game/player.py)
        current_dir = os.path.dirname(__file__)
        # Go up one level to 'bullet_hell', then into 'assets'
        asset_path = os.path.join(current_dir, "..", "assets", "spaceship.png")

        self.image = pygame.image.load(asset_path).convert_alpha()
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        self.pos = pygame.Vector2(self.rect.center)
        self.radius = 4  # Tiny hitbox!

    def update(self):
        keys = pygame.key.get_pressed()
        speed = PLAYER_FOCUS_SPEED if keys[pygame.K_LSHIFT] else PLAYER_SPEED

        move = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  move.x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move.x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:    move.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  move.y = 1

        if move.length() > 0:
            self.pos += move.normalize() * speed

        self.rect.center = self.pos
        # Screen boundaries
        self.pos.x = max(16, min(WIDTH - 16, self.pos.x))
        self.pos.y = max(16, min(HEIGHT - 16, self.pos.y))

    def draw_focus_dot(self, screen):
        # Draw the hitbox dot when holding Shift
        if pygame.key.get_pressed()[pygame.K_LSHIFT]:
            pygame.draw.circle(screen, WHITE, self.rect.center, 3)
            pygame.draw.circle(screen, RED, self.rect.center, 2)