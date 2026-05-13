<<<<<<< HEAD
# uni-pygame
=======
# Boss Rush — Terraria-Inspired 2D RPG Prototype

A pixel-art style boss-fight game built with **pure Python + Pygame**.
Fight **Malvortex the Dread Titan** across a multi-phase encounter in a
dark-fantasy side-scrolling arena.

---

## Folder Structure

```
boss_rush/
├── main.py              ← Entry point; game loop, collision resolution
├── src/
│   ├── __init__.py
│   ├── settings.py      ← ALL constants (tweak here first!)
│   ├── world.py         ← Arena geometry, platforms, camera, parallax BG
│   ├── player.py        ← Player entity: movement, dash, melee, ranged, leveling
│   ├── boss.py          ← Boss entity: multi-phase AI FSM, attack patterns
│   ├── attacks.py       ← Projectile & MeleeHitbox objects + AttackManager
│   ├── particles.py     ← Particle emitters, damage numbers, screen shake
│   └── ui.py            ← HUD, boss bar, pause/game-over/victory screens
└── README.md
```

---

## Quick Start

```bash
pip install pygame
python main.py
```

---

## Controls

| Key           | Action           |
|---------------|------------------|
| A / ←         | Move left        |
| D / →         | Move right       |
| Space / W / ↑ | Jump             |
| Shift         | Dash (invincible)|
| Z / J         | Melee swing      |
| X / K         | Magic bolt       |
| Esc           | Pause            |
| R             | Restart          |
| Q             | Quit             |

---

## Systems Overview

### Physics (`world.py`, `player.py`, `boss.py`)
All entities use AABB collision against platform rects.  
`resolve_vertical()` handles landing and ceiling hits.  
`resolve_horizontal()` clamps to arena bounds.  
Gravity is applied every frame scaled by delta-time.  
Terminal velocity caps falling speed.

### Combat (`main.py → resolve_attacks()`)
```
final_damage = max(1, base_attack - target_defense)
crit_damage  = final_damage × crit_multiplier  (15% chance for player)
```
All `Projectile` and `MeleeHitbox` objects carry `owner` tags ('player'/'boss')
so a single loop handles bidirectional damage without duplication.

### Boss AI (`boss.py`)
A lightweight FSM with four states:
```
idle → telegraph (0.9s warning) → attack → cooldown → idle
```
Phase 1 attacks: Projectile Volley, Ground Slam  
Phase 2 attacks (≤35% HP): + Charge Rush, Fireball Arc  
Enrage accelerates cooldowns by 35% and adds visual effects.

### Particle System (`particles.py`)
- Pooled up to `MAX_PARTICLES` active particles  
- Emitter helpers: `emit_hit`, `emit_blood`, `emit_fire`, `emit_magic`, `emit_dust`  
- Damage numbers rise, fade, and display CRIT in a different font size  
- `ScreenShake` uses trauma²-based displacement

### Camera (`world.py → Camera`)
Lerp-based smooth follow clamped to arena bounds.  
Screen-shake offset is composed on top of camera position each frame.

### Leveling (`player.py → gain_xp`)
XP thresholds scale by ×1.4 per level.  
Level-up grants: +15 max HP (full heal), +3 attack, +1 defense, +10 mana.  
TODO: Show a perk-selection popup on level-up.

---

## Extending the Game

### Add a new boss attack
1. Add a key to `ATKS` dict in `boss.py`
2. Add a cooldown entry to `self._cooldowns`
3. Add a branch in `_execute_attack()`
4. Include it in `_pick_next_attack()` for the appropriate phase

### Add a new player ability
1. Add constants to `settings.py`
2. Add timer + input check in `player.handle_input()`
3. Create appropriate `Projectile` or `MeleeHitbox` and push to `AttackManager`

### Add a new arena
1. Create a new `World` subclass with a different `_build_arena()` layout
2. Swap it in `make_game()` in `main.py`

### Replace placeholder graphics
Swap colored `pygame.draw` calls for `pygame.image.load()` sprite sheets.
The draw methods in each class are self-contained and easy to replace.

---

## TODO (Future Roadmap)

- [ ] Sprite sheet animation FSM for player and boss
- [ ] Title screen + boss intro cutscene
- [ ] Multiple boss arenas (load from Tiled JSON)
- [ ] Equipment system (weapons, armor with stats)
- [ ] Perk selection UI on level-up
- [ ] Sound effects and music (pygame.mixer)
- [ ] Particle pooling for zero-allocation recycling
- [ ] Save/load via JSON
- [ ] Minion spawning boss phase
- [ ] Homing and piercing projectile variants
- [ ] Destructible terrain
- [ ] Controller support (pygame.joystick)
>>>>>>> 4e767c9 (Main Gamet)
