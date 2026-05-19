import pygame
import sys
import json
import os

# Allow running standalone too
sys.path.insert(0, os.path.dirname(__file__))

from settings import *
from player import *
from bullets import *
from map import *
from boss import *


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SUPER MEGA IMBA BULLET HELL")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)

        self.state = "START_MENU"
        self.score = 0
        self.high_score = self.load_high_score()
        self.reset_game()

    def reset_game(self):
        self.map = Map()
        self.player = Player()
        self.boss = Boss()

        self.all_sprites = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()

        self.all_sprites.add(self.player)
        self.all_sprites.add(self.boss)

        self.player_health = PLAYER_MAX_HEALTH
        self.player_shoot_cooldown = 0
        self.score = 0

    def load_high_score(self):
        try:
            with open(SCORE_FILE, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open(SCORE_FILE, "w") as f:
                    json.dump({"high_score": self.high_score}, f)
            except IOError:
                pass

    def handle_collisions(self):
        boss_hits = pygame.sprite.spritecollide(self.boss, self.player_bullets, True, pygame.sprite.collide_circle)
        for bullet in boss_hits:
            self.boss.health -= bullet.damage
            self.score += 10
        player_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_circle)
        if player_hits:
            self.player_health -= 1
            if self.player_health <= 0:
                self.save_high_score()
                self.state = "GAME_OVER"

    def draw_ui(self):
        bar_width = 400
        bar_height = 15
        bar_x = (WIDTH - bar_width) // 2
        bar_y = 30
        health_ratio = self.boss.health / self.boss.max_health
        current_bar_width = int(bar_width * health_ratio)
        pygame.draw.rect(self.screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        if current_bar_width > 0:
            pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, current_bar_width, bar_height))
        self.screen.blit(self.font.render("BOSS", True, WHITE), (bar_x, bar_y - 25))
        self.screen.blit(self.font.render(f"LIVES: {self.player_health}", True, BLUE), (20, HEIGHT - 40))
        self.screen.blit(self.font.render(f"SCORE: {self.score}", True, WHITE), (20, 60))

    def draw_menus(self):
        self.screen.fill(BLACK)
        if self.state == "START_MENU":
            title = self.font.render("SUPER MEGA IMBA BULLET HELL", True, BLUE)
            instruction = self.font.render("Press SPACEBAR to Start", True, WHITE)
            hi_score = self.font.render(f"All-Time High Score: {self.high_score}", True, RED)
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
            self.screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2))
            self.screen.blit(hi_score, (WIDTH // 2 - hi_score.get_width() // 2, HEIGHT // 2 + 50))
        elif self.state == "GAME_OVER":
            title = self.font.render("GAME OVER", True, RED)
            final_score = self.font.render(f"Your Score: {self.score}", True, WHITE)
            instruction = self.font.render("Press R to Restart  |  Q to Quit  |  N for Next Game", True, BLUE)
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
            self.screen.blit(final_score, (WIDTH // 2 - final_score.get_width() // 2, HEIGHT // 2))
            self.screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2 + 50))

    def run(self):
        """Returns True to continue to next game, False to quit."""
        while True:
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if self.state == "START_MENU" and event.key == pygame.K_SPACE:
                        self.state = "PLAYING"
                    elif self.state == "GAME_OVER":
                        if event.key == pygame.K_r:
                            self.reset_game()
                            self.state = "PLAYING"
                        elif event.key == pygame.K_q:
                            return False
                        elif event.key == pygame.K_n:
                            return True  # advance to next game

            if self.state == "PLAYING":
                keys = pygame.key.get_pressed()
                if keys[pygame.K_z] and current_time > self.player_shoot_cooldown:
                    b1 = PlayerBullet(self.player.rect.left + 5, self.player.rect.top)
                    b2 = PlayerBullet(self.player.rect.right - 5, self.player.rect.top)
                    self.all_sprites.add(b1, b2)
                    self.player_bullets.add(b1, b2)
                    self.player_shoot_cooldown = current_time + 120

                if self.boss.alive():
                    self.boss.shoot(self.all_sprites, self.enemy_bullets)
                elif self.state == "PLAYING":
                    self.save_high_score()
                    self.state = "GAME_OVER"

                self.map.update()
                self.all_sprites.update()
                self.handle_collisions()

                self.map.draw(self.screen)
                self.all_sprites.draw(self.screen)
                self.player.draw_focus_dot(self.screen)
                self.draw_ui()
            else:
                self.draw_menus()

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    pygame.init()
    Game().run()
    pygame.quit()
