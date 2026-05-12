import pygame
import sys
import math
from settings import *
from player import Player
from bullets import Bullet
from map import Map


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.map = Map()
        self.player = Player()

        self.all_sprites = pygame.sprite.Group(self.player)
        self.enemy_bullets = pygame.sprite.Group()
        self.angle_step = 1

    def spawn_pattern(self):
        # Example: Spiral Pattern
        self.angle_step += 0.2
        for i in range(4):
            angle = self.angle_step + (i * math.pi / 2) # 4 streams
            b = Bullet(WIDTH // 2, 200, angle, BULLET_SPEED)
            self.all_sprites.add(b)
            self.enemy_bullets.add(b)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Logic
            self.map.update()
            self.spawn_pattern()
            self.all_sprites.update()

            # Collision check
            if pygame.sprite.spritecollide(self.player, self.enemy_bullets, False, pygame.sprite.collide_circle):
                print("Game Over!")

            # Render
            self.map.draw(self.screen)
            self.all_sprites.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
