#!/usr/bin/env python3
# =============================================================================
# main.py — Entry point with scene manager integration
#
# This version delegates ALL game logic to SceneManager.
# Main loop only handles:
#   - Window/clock setup
#   - Event collection
#   - scene_manager.update() + scene_manager.draw()
#
# The old boss-only logic is now inside scene_manager.py as one of 4 zones.
# =============================================================================

import sys
import os
import pygame

# Ensure src package is importable when run from project root
sys.path.insert(0, os.path.dirname(__file__))

from src.settings import *
from src.scene_manager import SceneManager
from src.ui import UI


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # ── Initialize scene manager (handles everything) ─────────────────────
    scene_mgr = SceneManager()
    ui = UI()

    running = True
    while running:
        # ── Delta time ────────────────────────────────────────────────────
        raw_dt = clock.tick(FPS) / 1000.0
        dt = min(raw_dt, 0.05)  # clamp to avoid spiral of death

        # ── Collect events ────────────────────────────────────────────────
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # ── Update (scene manager does everything) ────────────────────────
        scene_mgr.update(dt, keys, events)

        # ── Draw ──────────────────────────────────────────────────────────
        scene_mgr.draw(screen, ui)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
