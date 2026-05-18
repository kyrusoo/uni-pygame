import pygame
import sys
import json
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

        self.state = "START_MENU"

        self.score = 0
        self.high_score = self.load_high_score()  # Core Feature: Data Persistence

        self.reset_game()

    def reset_game(self):
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
        self.score = 0

    def load_high_score(self):
        try:
            with open(SCORE_FILE, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            print("bruh")
            return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open(SCORE_FILE, "w") as f:
                    json.dump({"high_score": self.high_score}, f)
            except IOError:
                print("Error: Could not save high score to file.")

    def handle_collisions(self):
        # 1. Player Bullets hitting the Boss (Using Circle Hitbox)
        boss_hits = pygame.sprite.spritecollide(self.boss, self.player_bullets, True, pygame.sprite.collide_circle)
        for bullet in boss_hits:
            self.boss.health -= bullet.damage
            self.score += 10
        # 2. Enemy Bullets hitting the Player (Using Circle Hitbox)
        player_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_circle)
        if player_hits:
            self.player_health -= 1
            if self.player_health <= 0:
                print("Game Over!")
                self.save_high_score()
                self.state = "GAME_OVER"

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

        boss_text = self.font.render("BOSS", True, WHITE)
        self.screen.blit(boss_text, (bar_x, bar_y - 25))

        player_text = self.font.render(f"LIVES: {self.player_health}", True, BLUE)
        self.screen.blit(player_text, (20, HEIGHT - 40))

        score_txt = self.font.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_txt, (20, 60))

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
            instruction = self.font.render("Press R to Restart or Q to Quit", True, BLUE)

            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
            self.screen.blit(final_score, (WIDTH // 2 - final_score.get_width() // 2, HEIGHT // 2))
            self.screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2 + 50))

    def run(self):
        while True:
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.state == "START_MENU" and event.key == pygame.K_SPACE:
                        self.state = "PLAYING"
                    elif self.state == "GAME_OVER":
                        if event.key == pygame.K_r:
                            self.reset_game()
                            self.state = "PLAYING"
                        elif event.key == pygame.K_q:
                            pygame.quit()
                            sys.exit()


            if self.state == "PLAYING":
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
            else:
                self.draw_menus()

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()