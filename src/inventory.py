# =============================================================================
# inventory.py — Inventory grid, equipment slots, crafting UI
# The Inventory is purely a data container; UI rendering is kept here too
# so the main ui.py stays focused on HUD.
# TODO: Drag-and-drop, item tooltips on hover, hotbar quick-select.
# =============================================================================

# =============================================================================
# inventory.py — Inventory grid, equipment slots, crafting UI
# =============================================================================

from __future__ import annotations

import pygame

from src.settings import *
from src.items import (
    Item, ITEMS, RECIPES,
    CATEGORY_WEAPON, CATEGORY_ARMOR,
    CATEGORY_CONSUMABLE, CATEGORY_RESOURCE,
    SLOT_HEAD, SLOT_BODY, SLOT_LEGS,
    WTYPE_MELEE
)


# ── Inventory slot ────────────────────────────────────────────────────────────

class InvSlot:
    """One cell in the inventory grid."""

    def __init__(self):
        self.item_id: str = ""
        self.qty: int = 0

    @property
    def empty(self) -> bool:
        return self.item_id == "" or self.qty <= 0

    @property
    def item(self) -> Item | None:
        return ITEMS.get(self.item_id)

    def clear(self):
        self.item_id = ""
        self.qty = 0


# ── Inventory ─────────────────────────────────────────────────────────────────

class Inventory:
    """
    Fixed-size grid inventory + equipment slots.
    Provides add / remove / craft helpers used by the world scene.
    """

    COLS = 8
    ROWS = 5

    def __init__(self):
        self.slots: list[InvSlot] = [InvSlot() for _ in range(self.COLS * self.ROWS)]

        # Equipment slots
        self.equipped: dict[str, str] = {
            "weapon": "",
            SLOT_HEAD: "",
            SLOT_BODY: "",
            SLOT_LEGS: "",
        }

        # Give starter items
        self._give_starters()

        # UI state
        self.open = False
        self.selected_slot = -1  # highlighted slot index
        self.craft_scroll = 0  # recipe list scroll offset
        self.craft_selected = -1  # highlighted recipe index
        self._recipe_keys = list(RECIPES.keys())

        # Fonts
        pygame.font.init()
        self._font_sm = pygame.font.SysFont("monospace", 12, bold=True)
        self._font_md = pygame.font.SysFont("monospace", 15, bold=True)
        self._font_lg = pygame.font.SysFont("monospace", 19, bold=True)

    # ── Starter kit ───────────────────────────────────────────────────────────

    def _give_starters(self):
        """Player starts with sticks, a wooden sword, and a stone sword."""
        self.add("stick", 10)
        self.add("wood", 5)
        self.add("stick_weapon", 1)
        self.add("wooden_sword", 1)
        self.add("stone_sword", 1)

    # ── Core helpers ──────────────────────────────────────────────────────────

    def add(self, item_id: str, qty: int = 1) -> bool:
        """Add qty of item. Returns True if all qty fit."""
        item = ITEMS.get(item_id)
        if not item:
            return False

        remaining = qty
        # Try stacking onto existing slots first
        for slot in self.slots:
            if slot.item_id == item_id and item.stackable:
                space = item.max_stack - slot.qty
                add = min(space, remaining)
                slot.qty += add
                remaining -= add
                if remaining == 0:
                    return True

        # Fill empty slots
        for slot in self.slots:
            if slot.empty:
                add = min(item.max_stack, remaining)
                slot.item_id = item_id
                slot.qty = add
                remaining -= add
                if remaining == 0:
                    return True

        return remaining == 0  # False if some items didn't fit

    def remove(self, item_id: str, qty: int = 1) -> bool:
        """Remove qty of item. Returns True on success, False if not enough."""
        count = self.count(item_id)
        if count < qty:
            return False
        remaining = qty
        for slot in self.slots:
            if slot.item_id == item_id and remaining > 0:
                take = min(slot.qty, remaining)
                slot.qty -= take
                remaining -= take
                if slot.qty <= 0:
                    slot.clear()
        return True

    def count(self, item_id: str) -> int:
        return sum(s.qty for s in self.slots if s.item_id == item_id)

    def has(self, item_id: str, qty: int = 1) -> bool:
        return self.count(item_id) >= qty

    # ── Crafting ──────────────────────────────────────────────────────────────

    def can_craft(self, result_id: str) -> bool:
        recipe = RECIPES.get(result_id)
        if not recipe:
            return False
        return all(self.has(iid, q) for iid, q in recipe)

    def craft(self, result_id: str) -> bool:
        if not self.can_craft(result_id):
            return False
        recipe = RECIPES[result_id]
        for iid, q in recipe:
            self.remove(iid, q)
        self.add(result_id, 1)
        return True

    # ── Equipment ─────────────────────────────────────────────────────────────

    def equip_from_slot(self, slot_idx: int) -> bool:
        """Equip the item in inventory slot_idx. Returns True on success."""
        if slot_idx < 0 or slot_idx >= len(self.slots):
            return False
        slot = self.slots[slot_idx]
        if slot.empty:
            return False
        item = slot.item
        if not item:
            return False

        if item.category == CATEGORY_WEAPON:
            old = self.equipped["weapon"]
            self.equipped["weapon"] = item.id
            slot.clear()
            if old:
                self.add(old, 1)
            return True

        elif item.category == CATEGORY_ARMOR and item.armor_slot:
            old = self.equipped[item.armor_slot]
            self.equipped[item.armor_slot] = item.id
            slot.clear()
            if old:
                self.add(old, 1)
            return True

        return False

    def unequip(self, slot_key: str) -> bool:
        item_id = self.equipped.get(slot_key, "")
        if not item_id:
            return False
        if self.add(item_id, 1):
            self.equipped[slot_key] = ""
            return True
        return False

    # ── Stat helpers (read by Player) ─────────────────────────────────────────

    @property
    def weapon_item(self) -> Item | None:
        return ITEMS.get(self.equipped.get("weapon", ""))

    @property
    def total_defense(self) -> int:
        total = 0
        for slot_key in (SLOT_HEAD, SLOT_BODY, SLOT_LEGS):
            iid = self.equipped.get(slot_key, "")
            if iid:
                item = ITEMS.get(iid)
                if item:
                    total += item.defense
        return total

    @property
    def weapon_damage(self) -> int:
        w = self.weapon_item
        return w.damage if w else 8  # bare-fist fallback

    @property
    def weapon_range(self) -> int:
        w = self.weapon_item
        return w.attack_range if w else 40

    @property
    def weapon_rate(self) -> float:
        w = self.weapon_item
        return w.attack_rate if w else 0.55

    # ── Consumable use ────────────────────────────────────────────────────────

    def use_consumable(self, item_id: str, player) -> bool:
        """Use one consumable from inventory; apply effect to player."""
        item = ITEMS.get(item_id)
        if not item or item.category != CATEGORY_CONSUMABLE:
            return False
        if not self.has(item_id, 1):
            return False
        self.remove(item_id, 1)
        if item.heal_hp > 0:
            player.hp = min(player.max_hp, player.hp + item.heal_hp)
        if item.heal_mana > 0:
            player.mana = min(player.max_mana, player.mana + item.heal_mana)
        return True

    # ── UI draw ───────────────────────────────────────────────────────────────

    CELL = 48  # pixel size of each inventory cell
    PAD = 8

    def draw(self, surface: pygame.Surface):
        if not self.open:
            return

        sw, sh = surface.get_size()

        # ── Backdrop ──────────────────────────────────────────────────────
        panel_w = 700
        panel_h = 480
        px = sw // 2 - panel_w // 2
        py = sh // 2 - panel_h // 2

        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill((10, 10, 25, 215))
        surface.blit(bg, (px, py))
        pygame.draw.rect(surface, (80, 60, 120), (px, py, panel_w, panel_h), 2)

        # Title
        title = self._font_lg.render("INVENTORY  [I / TAB = close]",
                                     True, (200, 200, 255))
        surface.blit(title, (px + 10, py + 8))

        # ── Inventory grid ────────────────────────────────────────────────
        gx = px + 10
        gy = py + 36
        C = self.CELL
        P = 4

        for idx, slot in enumerate(self.slots):
            col = idx % self.COLS
            row = idx // self.COLS
            rx = gx + col * (C + P)
            ry = gy + row * (C + P)

            # Cell background
            bg_col = (40, 35, 60) if idx != self.selected_slot else (80, 60, 120)
            pygame.draw.rect(surface, bg_col, (rx, ry, C, C))
            pygame.draw.rect(surface, (70, 55, 90), (rx, ry, C, C), 1)

            if not slot.empty and slot.item:
                self._draw_item_icon(surface, slot.item, rx + 4, ry + 4, C - 8)
                if slot.item.stackable and slot.qty > 1:
                    qty_s = self._font_sm.render(str(slot.qty), True, C_WHITE)
                    surface.blit(qty_s, (rx + C - qty_s.get_width() - 2,
                                         ry + C - qty_s.get_height() - 1))

        # ── Equipment panel ───────────────────────────────────────────────
        eq_x = gx + self.COLS * (C + P) + 12
        eq_y = gy
        self._font_md.render("EQUIPPED", True, (200, 200, 255))
        eq_title = self._font_md.render("EQUIPPED", True, (180, 160, 220))
        surface.blit(eq_title, (eq_x, eq_y - 2))

        slots_order = [
            ("weapon", "Weapon"),
            (SLOT_HEAD, "Head"),
            (SLOT_BODY, "Body"),
            (SLOT_LEGS, "Legs"),
        ]
        for i, (key, label) in enumerate(slots_order):
            ex = eq_x
            ey = eq_y + 22 + i * (C + P)
            lbl = self._font_sm.render(label, True, (150, 150, 190))
            surface.blit(lbl, (ex, ey - 14))
            pygame.draw.rect(surface, (30, 25, 45), (ex, ey, C, C))
            pygame.draw.rect(surface, (100, 80, 140), (ex, ey, C, C), 2)
            iid = self.equipped.get(key, "")
            if iid and iid in ITEMS:
                self._draw_item_icon(surface, ITEMS[iid], ex + 4, ey + 4, C - 8)

        # Stats summary
        sy = eq_y + 22 + 4 * (C + P) + 8
        def_total = PLAYER_DEFENSE + self.total_defense
        wdmg = self.weapon_damage
        for line, col in [
            (f"ATK  {wdmg}", (220, 180, 80)),
            (f"DEF  {def_total}", (80, 180, 220)),
        ]:
            s = self._font_md.render(line, True, col)
            surface.blit(s, (eq_x, sy))
            sy += 22

        # ── Crafting panel ────────────────────────────────────────────────
        cr_x = px + 10
        cr_y = gy + self.ROWS * (C + P) + 12
        cr_title = self._font_md.render("CRAFTING  [C = craft selected]",
                                        True, (180, 220, 180))
        surface.blit(cr_title, (cr_x, cr_y))
        cr_y += 22

        visible = 4
        for vi in range(visible):
            ri = self.craft_scroll + vi
            if ri >= len(self._recipe_keys):
                break
            rkey = self._recipe_keys[ri]
            ritem = ITEMS.get(rkey)
            if not ritem:
                continue

            craftable = self.can_craft(rkey)
            row_col = (40, 55, 40) if craftable else (45, 35, 35)
            if ri == self.craft_selected:
                row_col = (60, 90, 60) if craftable else (70, 45, 45)

            pygame.draw.rect(surface, row_col,
                             (cr_x, cr_y + vi * 26, panel_w - 20, 24))

            # Item name + ingredients
            name_col = (140, 220, 140) if craftable else (180, 120, 120)
            name_s = self._font_sm.render(ritem.name, True, name_col)
            surface.blit(name_s, (cr_x + 4, cr_y + vi * 26 + 5))

            recipe = RECIPES[rkey]
            ing_parts = []
            for iid, qty in recipe:
                have = self.count(iid)
                iname = ITEMS[iid].name if iid in ITEMS else iid
                ing_parts.append(f"{iname}×{qty}({have})")
            ing_str = "  ".join(ing_parts)
            ing_s = self._font_sm.render(ing_str, True, (150, 150, 150))
            surface.blit(ing_s, (cr_x + 150, cr_y + vi * 26 + 5))

        # scroll hint
        hint = self._font_sm.render("↑↓ scroll  E=equip  U=unequip-weapon",
                                    True, (100, 100, 130))
        surface.blit(hint, (cr_x, py + panel_h - 18))

    # ── Item icon renderer ────────────────────────────────────────────────────

    def _draw_item_icon(self, surface, item: Item, x, y, size):
        """Minimal geometric icon for each item type."""
        c1 = item.color
        c2 = item.color2

        cat = item.category
        if cat == CATEGORY_WEAPON:
            # Sword shape: hilt + blade
            mid = size // 2
            # blade
            pygame.draw.line(surface, c2, (x + mid, y + size),
                             (x + size, y), 3)
            # hilt
            pygame.draw.line(surface, c1,
                             (x + mid - 4, y + size // 2 + 4),
                             (x + mid + 6, y + size // 2 - 4), 4)

        elif cat == CATEGORY_ARMOR:
            # Shield/armor shape
            pts = [
                (x + size // 2, y),
                (x + size, y + size // 3),
                (x + size, y + size * 2 // 3),
                (x + size // 2, y + size),
                (x, y + size * 2 // 3),
                (x, y + size // 3),
            ]
            pygame.draw.polygon(surface, c1, pts)
            pygame.draw.polygon(surface, c2, pts, 2)

        elif cat == CATEGORY_RESOURCE:
            pygame.draw.rect(surface, c1, (x + 2, y + 2, size - 4, size - 4))
            pygame.draw.rect(surface, c2, (x + 2, y + 2, size - 4, size - 4), 2)

        elif cat == CATEGORY_CONSUMABLE:
            # Potion bottle
            bx = x + size // 4
            pygame.draw.rect(surface, c1, (bx, y + size // 3, size // 2, size * 2 // 3))
            pygame.draw.rect(surface, c2, (bx + size // 8, y + size // 6,
                                           size // 4, size // 3))
        else:
            pygame.draw.rect(surface, c1, (x, y, size, size))

    # ── Input handling ────────────────────────────────────────────────────────

    def handle_key(self, key, player) -> bool:
        """Returns True if key was consumed by inventory UI."""
        if not self.open:
            return False

        if key == pygame.K_UP:
            if self.craft_selected > 0:
                self.craft_selected -= 1
            elif self.craft_scroll > 0:
                self.craft_scroll -= 1
            return True

        if key == pygame.K_DOWN:
            max_idx = len(self._recipe_keys) - 1
            if self.craft_selected < min(3, max_idx - self.craft_scroll):
                self.craft_selected += 1
            elif self.craft_scroll + 4 <= max_idx:
                self.craft_scroll += 1
            return True

        if key == pygame.K_c:
            ri = self.craft_scroll + self.craft_selected
            if 0 <= ri < len(self._recipe_keys):
                rkey = self._recipe_keys[ri]
                self.craft(rkey)
            return True

        if key == pygame.K_e and self.selected_slot >= 0:
            self.equip_from_slot(self.selected_slot)
            return True

        if key == pygame.K_u:
            self.unequip("weapon")
            return True

        # Number keys 1-5 for consumable quick-use from first row
        num_map = {
            pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
            pygame.K_4: 3, pygame.K_5: 4,
        }
        if key in num_map:
            self.use_consumable(self.slots[num_map[key]].item_id, player)
            return True

        return False

    def handle_click(self, mx, my, surface_size) -> bool:
        """Mouse click on inventory grid — select slot."""
        if not self.open:
            return False
        sw, sh = surface_size
        panel_w, panel_h = 700, 480
        px = sw // 2 - panel_w // 2
        py = sh // 2 - panel_h // 2
        gx, gy = px + 10, py + 36
        C, P = self.CELL, 4

        for idx in range(len(self.slots)):
            col = idx % self.COLS
            row = idx // self.COLS
            rx = gx + col * (C + P)
            ry = gy + row * (C + P)
            if rx <= mx < rx + C and ry <= my < ry + C:
                self.selected_slot = idx
                return True
        return False
