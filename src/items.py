# =============================================================================
# items.py — All item definitions: weapons, armor, resources, consumables
# Items are pure data; no pygame or game-state dependencies here.
# TODO: Add enchantments, item rarity tiers, ranged weapons (bow/staff).
# =============================================================================

from dataclasses import dataclass, field
from typing import Optional


# ── Item categories ───────────────────────────────────────────────────────────
CATEGORY_WEAPON   = "weapon"
CATEGORY_ARMOR    = "armor"
CATEGORY_RESOURCE = "resource"
CATEGORY_CONSUMABLE = "consumable"

# ── Weapon sub-types ──────────────────────────────────────────────────────────
WTYPE_MELEE  = "melee"
WTYPE_RANGED = "ranged"

# ── Armor slots ───────────────────────────────────────────────────────────────
SLOT_HEAD  = "head"
SLOT_BODY  = "body"
SLOT_LEGS  = "legs"


@dataclass
class Item:
    """Base item record. All fields are plain data — no game logic."""
    id:          str
    name:        str
    category:    str
    description: str   = ""
    stackable:   bool  = True
    max_stack:   int   = 99

    # Weapon stats (if category == CATEGORY_WEAPON)
    weapon_type: Optional[str] = None
    damage:      int  = 0
    attack_rate: float = 0.35   # seconds between swings
    attack_range:int  = 70      # px reach (melee) / irrelevant for ranged
    mana_cost:   int  = 0       # ranged: mana per shot
    proj_speed:  float = 0.0    # ranged: projectile speed
    knockback:   float = 300.0

    # Armor stats (if category == CATEGORY_ARMOR)
    armor_slot:  Optional[str] = None
    defense:     int  = 0

    # Visual — simple color used for pixel-art placeholder sprite
    color:       tuple = (180, 180, 180)
    color2:      tuple = (120, 120, 120)   # accent / blade color

    # Consumable
    heal_hp:    int = 0
    heal_mana:  int = 0


# =============================================================================
# ── Item Registry ─────────────────────────────────────────────────────────────
# Single source of truth.  Access via ITEMS["item_id"].
# =============================================================================

ITEMS: dict[str, Item] = {}

def _reg(item: Item) -> Item:
    ITEMS[item.id] = item
    return item


# ── Resources ─────────────────────────────────────────────────────────────────
_reg(Item("wood",  "Wood",  CATEGORY_RESOURCE,
          "Basic crafting material. Dropped by trees.",
          color=(139, 90, 43)))
_reg(Item("stone", "Stone", CATEGORY_RESOURCE,
          "Solid rock. Dropped by stone deposits.",
          color=(130, 130, 130)))
_reg(Item("stick", "Stick", CATEGORY_RESOURCE,
          "A thin wooden stick. Used in basic recipes.",
          color=(160, 110, 60)))
_reg(Item("mob_fang", "Mob Fang", CATEGORY_RESOURCE,
          "Dropped by Goblins. Used in upgrades.",
          color=(220, 200, 80), max_stack=50))
_reg(Item("mob_eye",  "Mob Eye",  CATEGORY_RESOURCE,
          "Dropped by Eyebats. Used in upgrades.",
          color=(180, 40, 40), max_stack=50))
_reg(Item("mid_boss_core", "Guardian Core", CATEGORY_RESOURCE,
          "Dropped by medium bosses. Rare crafting material.",
          color=(120, 60, 200), max_stack=10))

# ── Consumables ───────────────────────────────────────────────────────────────
_reg(Item("health_potion", "Health Potion", CATEGORY_CONSUMABLE,
          "Restores 40 HP.", stackable=True, max_stack=20,
          heal_hp=40, color=(220, 50, 80)))
_reg(Item("mana_potion", "Mana Potion", CATEGORY_CONSUMABLE,
          "Restores 30 Mana.", stackable=True, max_stack=20,
          heal_mana=30, color=(60, 80, 220)))

# ── Weapons ───────────────────────────────────────────────────────────────────
_reg(Item("stick_weapon", "Fighting Stick", CATEGORY_WEAPON,
          "A stick. Better than nothing.",
          stackable=False, max_stack=1,
          weapon_type=WTYPE_MELEE,
          damage=6, attack_rate=0.4, attack_range=55, knockback=180,
          color=(160, 110, 60), color2=(140, 90, 40)))

_reg(Item("wooden_sword", "Wooden Sword", CATEGORY_WEAPON,
          "Carved from sturdy oak. A classic beginner weapon.",
          stackable=False, max_stack=1,
          weapon_type=WTYPE_MELEE,
          damage=14, attack_rate=0.35, attack_range=65, knockback=260,
          color=(139, 90, 43), color2=(200, 160, 80)))

_reg(Item("stone_sword", "Stone Sword", CATEGORY_WEAPON,
          "Heavy but hits hard. Requires stone + wood.",
          stackable=False, max_stack=1,
          weapon_type=WTYPE_MELEE,
          damage=24, attack_rate=0.42, attack_range=70, knockback=340,
          color=(130, 130, 130), color2=(80, 80, 80)))

_reg(Item("bone_sword", "Bone Sword", CATEGORY_WEAPON,
          "Crafted from monster fangs. Drops from mid-boss.",
          stackable=False, max_stack=1,
          weapon_type=WTYPE_MELEE,
          damage=35, attack_rate=0.32, attack_range=75, knockback=380,
          color=(230, 220, 190), color2=(255, 255, 220)))

# ── Armor ─────────────────────────────────────────────────────────────────────
_reg(Item("wooden_helmet", "Wooden Helmet", CATEGORY_ARMOR,
          "Carved wood headguard. +2 defense.",
          stackable=False, max_stack=1,
          armor_slot=SLOT_HEAD, defense=2,
          color=(139, 90, 43), color2=(110, 70, 30)))

_reg(Item("wooden_chestplate", "Wooden Chestplate", CATEGORY_ARMOR,
          "Wooden body armor. +4 defense.",
          stackable=False, max_stack=1,
          armor_slot=SLOT_BODY, defense=4,
          color=(139, 90, 43), color2=(110, 70, 30)))

_reg(Item("wooden_leggings", "Wooden Leggings", CATEGORY_ARMOR,
          "Wooden leg guards. +2 defense.",
          stackable=False, max_stack=1,
          armor_slot=SLOT_LEGS, defense=2,
          color=(139, 90, 43), color2=(110, 70, 30)))

_reg(Item("stone_helmet", "Stone Helmet", CATEGORY_ARMOR,
          "Heavy stone helm. +4 defense.",
          stackable=False, max_stack=1,
          armor_slot=SLOT_HEAD, defense=4,
          color=(130, 130, 130), color2=(90, 90, 90)))

_reg(Item("stone_chestplate", "Stone Chestplate", CATEGORY_ARMOR,
          "Stone body armor. +7 defense.",
          stackable=False, max_stack=1,
          armor_slot=SLOT_BODY, defense=7,
          color=(130, 130, 130), color2=(90, 90, 90)))

_reg(Item("stone_leggings", "Stone Leggings", CATEGORY_ARMOR,
          "Stone leg guards. +4 defense.",
          stackable=False, max_stack=1,
          armor_slot=SLOT_LEGS, defense=4,
          color=(130, 130, 130), color2=(90, 90, 90)))


# =============================================================================
# ── Crafting Recipes ──────────────────────────────────────────────────────────
# recipe: { result_id: [(ingredient_id, qty), ...] }
# TODO: Add crafting stations that gate which recipes are available.
# =============================================================================

RECIPES: dict[str, list[tuple[str, int]]] = {
    # Sticks
    "stick":              [("wood", 1)],

    # Weapons
    "stick_weapon":       [("stick", 2)],
    "wooden_sword":       [("wood", 8), ("stick", 2)],
    "stone_sword":        [("stone", 12), ("wood", 4), ("stick", 2)],
    "bone_sword":         [("mob_fang", 8), ("stick", 4)],

    # Wooden armor
    "wooden_helmet":      [("wood", 10)],
    "wooden_chestplate":  [("wood", 18)],
    "wooden_leggings":    [("wood", 12)],

    # Stone armor
    "stone_helmet":       [("stone", 14), ("wood", 4)],
    "stone_chestplate":   [("stone", 22), ("wood", 8)],
    "stone_leggings":     [("stone", 16), ("wood", 4)],

    # Potions
    "health_potion":      [("wood", 2), ("mob_eye", 1)],
    "mana_potion":        [("wood", 2), ("mob_fang", 1)],
}