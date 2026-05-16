import pygame
import sys
from settings import *
from player import *
from bullets import *
from map import *
from boss import *


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)

        self.map = Map()
        self.player = Player()
        self.boss = Boss()

        # Sprite Groups
        self.all_sprites = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()

        self.all_sprites.add(self.player)
        self.all_sprites.add(self.boss)

        # Player Stats
        self.player_health = PLAYER_MAX_HEALTH
        self.player_shoot_cooldown = 0

    def handle_collisions(self):
        # 1. Player Bullets hitting the Boss (Using Circle Hitbox)
        boss_hits = pygame.sprite.spritecollide(self.boss, self.player_bullets, True, pygame.sprite.collide_circle)
        for bullet in boss_hits:
            self.boss.health -= bullet.damage
        # 2. Enemy Bullets hitting the Player (Using Circle Hitbox)
        player_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_circle)
        if player_hits:
            self.player_health -= 1
            if self.player_health <= 0:
                print("Game Over!")
                pygame.quit()
                sys.exit()

    def draw_ui(self):
        # BOSS HEALTH BAR
        bar_width = 400
        bar_height = 15
        bar_x = (WIDTH - bar_width) // 2
        bar_y = 30

        # Calculate health percentage
        health_ratio = self.boss.health / self.boss.max_health
        current_bar_width = int(bar_width * health_ratio)

        # Draw Red Background, then Green Current Health
        pygame.draw.rect(self.screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        if current_bar_width > 0:
            pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, current_bar_width, bar_height))

        # Boss Label Text
        boss_text = self.font.render("BOSS", True, WHITE)
        self.screen.blit(boss_text, (bar_x, bar_y - 25))

        # ---- PLAYER LIVES (Bottom Left) ----
        player_text = self.font.render(f"LIVES: {self.player_health}", True, BLUE)
        self.screen.blit(player_text, (20, HEIGHT - 40))

    def run(self):
        while True:
            self.screen.fill(BLACK)
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Player Shooting Logic
            keys = pygame.key.get_pressed()
            if keys[pygame.K_z] and current_time > self.player_shoot_cooldown:
                # Shoot two bullets from the wings
                b1 = PlayerBullet(self.player.rect.left + 5, self.player.rect.top)
                b2 = PlayerBullet(self.player.rect.right - 5, self.player.rect.top)
                self.all_sprites.add(b1, b2)
                self.player_bullets.add(b1, b2)
                self.player_shoot_cooldown = current_time + 120 # Fires every 120 milliseconds

            if self.boss.alive():
                self.boss.shoot(self.all_sprites, self.enemy_bullets)

            # Updates
            self.map.update()
            self.all_sprites.update()
            self.handle_collisions()

            # Rendering Order
            self.map.draw(self.screen)
            self.all_sprites.draw(self.screen)
            self.player.draw_focus_dot(self.screen)  # Draw dot over the ship
            self.draw_ui()  # Draw UI last so it is on top of everything

            pygame.display.flip()
            self.clock.tick(FPS)



if __name__ == "__main__":
    Game().run()



