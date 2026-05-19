#!/usr/bin/env python3
# =============================================================================
# main.py — Top-level launcher
#
# Runs the three games in sequence:
#   1. Bullet Hell  (bullet_hell/game/)
#   2. Maze FPS     (maze/)
#   3. Boss Rush    (src/ + scene_manager)
#
# Each game returns True  → advance to the next one
#                  False → quit immediately
# =============================================================================

import sys
import os
import pygame

ROOT = os.path.dirname(__file__)


def run_bullet_hell():
    """Launch bullet_hell. Returns True to continue, False to quit."""
    game_dir = os.path.join(ROOT, "bullet_hell", "game")
    sys.path.insert(0, game_dir)

    # Import lazily so path is set first
    from bullet_hell.game.main import Game as BulletHellGame

    pygame.display.set_caption("Game 1 — Bullet Hell")
    result = BulletHellGame().run()

    # Clean up bullet_hell modules so they don't clash with later imports
    _purge_modules(["settings", "player", "bullets", "map", "boss"])
    sys.path.pop(0)
    return result


def run_maze():
    """Launch maze. Returns True to continue, False to quit."""
    game_dir = os.path.join(ROOT, "maze")
    sys.path.insert(0, game_dir)

    from maze.main import Game as MazeGame

    pygame.display.set_caption("Game 2 — Maze FPS")
    result = MazeGame().run()

    _purge_modules(["settings", "map", "player", "raycasting",
                    "object_renderer", "sprite_object", "object_handler",
                    "weapon", "sound", "pathfinding", "npc"])
    sys.path.pop(0)
    return result


def run_boss_rush():
    """Launch boss rush. Returns True when done, False to quit."""
    sys.path.insert(0, ROOT)

    from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS
    from src.scene_manager import SceneManager
    from src.ui import UI

    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Game 3 — " + TITLE)
    clock = pygame.time.Clock()

    scene_mgr = SceneManager()
    ui = UI()

    running = True
    while running:
        raw_dt = clock.tick(FPS) / 1000.0
        dt = min(raw_dt, 0.05)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return False

        keys = pygame.key.get_pressed()
        scene_mgr.update(dt, keys, events)

        screen = pygame.display.get_surface()
        scene_mgr.draw(screen, ui)
        pygame.display.flip()

        # End condition: player won or game over → show screen, then exit
        if scene_mgr.victory or scene_mgr.game_over:
            # Let the UI show the end screen for a moment, then exit on keypress
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    scene_mgr._restart()

    sys.path.pop(0)
    return True


def _purge_modules(names):
    """Remove named modules from sys.modules to avoid import conflicts."""
    for name in names:
        sys.modules.pop(name, None)


def main():
    pygame.init()

    # ── Game 1: Bullet Hell ───────────────────────────────────────────────
    print("[Launcher] Starting Game 1: Bullet Hell")
    if not run_bullet_hell():
        pygame.quit()
        sys.exit()

    # ── Game 2: Maze FPS ──────────────────────────────────────────────────
    print("[Launcher] Starting Game 2: Maze FPS")
    if not run_maze():
        pygame.quit()
        sys.exit()

    # ── Game 3: Boss Rush ─────────────────────────────────────────────────
    print("[Launcher] Starting Game 3: Boss Rush")
    run_boss_rush()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
