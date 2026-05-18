# Maze — A Doom-like FPS in Python

A first-person shooter built with Python and Pygame, inspired by classic 90s ray-casting games like Doom and Wolfenstein 3D. Navigate a multi-room maze, hunt down enemies, and survive.

---

## Overview

Maze uses a raycasting engine to render a 3D perspective from a 2D grid map — the same technique used in the original Doom engine. Enemy NPCs actively hunt the player using a BFS pathfinding algorithm, making them a real threat in tight corridors.

The game features a full gameplay loop: roam the map, fight enemies, take damage, recover health, and either survive or face a game over screen.

---

## Features

- **Raycasting renderer** — textured walls, floor, and a sky rendered in real time
- **Enemy AI** — NPCs navigate toward the player using BFS pathfinding with 8-directional movement
- **Animated sprites** — enemies cycle through idle, walk, attack, pain, and death animations
- **Weapon system** — animated finger weapon with a fire and reload cycle; deals 25 damage per hit
- **Health system** — player starts with 100 HP, takes damage from enemy attacks, and slowly regenerates over time
- **Sound effects** — weapon fire, enemy pain/death/attack sounds, and a background theme track
- **Game Over & Win screens** — full-screen overlays on death or level completion
- **Multi-texture walls** — 5 distinct wall textures mapped across a hand-crafted 16×28 grid map

---

## Requirements

- Python 3.8+
- Pygame

Install dependencies:

```bash
pip install pygame
```

---

## Installation & Running

```bash
# Clone the repository
git clone https://github.com/kyrusoo/uni-pygame.git
cd uni-pygame

# Run the game
python3 maze/main.py
```

> Make sure you run the command from the `uni-pygame/` root directory — the game resolves the `resources/` path relative to there.

---

## Controls

| Input | Action |
|---|---|
| `W` | Move forward |
| `S` | Move backward |
| `A` | Strafe left |
| `D` | Strafe right |
| Mouse move | Look left / right |
| Left click | Shoot |
| `Escape` | Quit |

---

## Project Structure

```
uni-pygame/
├── maze/
│   ├── main.py            # Game loop and entry point
│   ├── settings.py        # Resolution, FOV, player stats, constants
│   ├── map.py             # 2D grid map definition
│   ├── player.py          # Player movement, mouse look, health
│   ├── raycasting.py      # Ray-casting engine
│   ├── object_renderer.py # Wall/floor/sky rendering, HUD overlays
│   ├── sprite_object.py   # Base sprite and animated sprite classes
│   ├── object_handler.py  # Manages all sprites and NPCs in the scene
│   ├── npc.py             # Enemy AI: states, pathfinding, combat
│   ├── pathfinding.py     # BFS pathfinding on the world grid
│   ├── weapon.py          # Weapon sprite and shoot/reload animation
│   └── sound.py           # Sound effect and music loading
└── resources/
    ├── textures/           # Wall textures, sky, HUD overlays, digit sprites
    ├── sprites/
    │   ├── npc/expeditor/  # Enemy animation frames (idle/walk/attack/pain/death)
    │   ├── weapon/finger/  # Weapon animation frames
    │   └── animated_sprites/ # Other animated world sprites (eye)
    └── sound/              # .wav and .mp3 audio files
```

---

## Settings

Key values in `settings.py` you can tweak:

| Setting | Default | Description |
|---|---|---|
| `RES` | 1600 × 900 | Window resolution |
| `FOV` | π / 2 (90°) | Field of view |
| `PLAYER_SPEED` | 0.004 | Movement speed |
| `PLAYER_MAX_HEALTH` | 100 | Starting health |
| `MOUSE_SENSITIVITY` | 0.0003 | Mouse look sensitivity |
| `MAX_DEPTH` | 20 | Maximum ray travel distance |

---

## Authors

Whole project was developed as a university project. Contributors on separate Git branches: `dev_kyrusoo`, `dev_tashlyg`, `dev_xolonvr`.
Maze part was merged from `dev_kyrusoo`
