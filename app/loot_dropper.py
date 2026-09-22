# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Dynamic Encounter Loot Dropper for tabletop RPG encounters."""

from __future__ import annotations

import logging
import random
from typing import Any

from app.firestore_db import add_item_to_db, search_items_in_db

logger = logging.getLogger(__name__)

GEM_TABLE_TIER1 = ["Banded Agate (10 GP)", "Lapis Lazuli (10 GP)", "Malachite (10 GP)", "Tiger Eye (10 GP)", "Carnelian (25 GP)"]
GEM_TABLE_TIER2 = ["Bloodstone (50 GP)", "Moonstone (50 GP)", "Onyx (50 GP)", "Amber (100 GP)", "Jade (100 GP)", "Pearl (100 GP)"]
GEM_TABLE_TIER3 = ["Black Pearl (500 GP)", "Alexandrite (500 GP)", "Aquamarine (500 GP)", "Blue Sapphire (1000 GP)", "Fire Opal (1000 GP)"]
GEM_TABLE_TIER4 = ["Star Ruby (1000 GP)", "Diamond (2500 GP)", "Star Sapphire (5000 GP)", "Jacinth (5000 GP)"]


def _roll_dice(num: int, sides: int) -> int:
    """Helper to simulate rolling dice."""
    return sum(random.randint(1, sides) for _ in range(num))


def generate_encounter_loot(
    challenge_rating: float,
    enemy_name: str = "",
    include_magic_items: bool = True,
) -> str:
    """Rolls dynamic encounter loot based on Challenge Rating (CR) and fetches matched rewards from Cloud Firestore.

    Args:
        challenge_rating: Challenge rating of the defeated foe or encounter (e.g. 0.25, 1, 3, 7, 14, 20).
        enemy_name: Optional name of the enemy or encounter (e.g. 'Owlbear', 'Shadowfang Wyrm', 'Goblin Patrol').
        include_magic_items: Whether to roll and pick magical items from the Firestore compendium.

    Returns:
        A formatted markdown loot summary including coins, gemstones, and magical items.
    """
    cr = float(challenge_rating)
    target_name = enemy_name.strip() or f"CR {cr} Encounter"

    pp, gp, sp, cp = 0, 0, 0, 0
    gems: list[str] = []
    eligible_rarities: list[str] = []

    if cr <= 4:
        # Tier 1 (CR 0–4)
        cp = _roll_dice(3, 6) * 10
        sp = _roll_dice(2, 6) * 10
        gp = _roll_dice(1, 6) * 10
        eligible_rarities = ["Common", "Uncommon"]
        if random.random() < 0.45:
            num_gems = random.randint(1, 3)
            gems = random.choices(GEM_TABLE_TIER1, k=num_gems)

    elif cr <= 10:
        # Tier 2 (CR 5–10)
        sp = _roll_dice(2, 6) * 100
        gp = _roll_dice(4, 6) * 100
        pp = _roll_dice(1, 4) * 10
        eligible_rarities = ["Uncommon", "Rare"]
        num_gems = random.randint(2, 5)
        gems = random.choices(GEM_TABLE_TIER2, k=num_gems)

    elif cr <= 16:
        # Tier 3 (CR 11–16)
        gp = _roll_dice(4, 8) * 1000
        pp = _roll_dice(3, 6) * 100
        eligible_rarities = ["Rare", "Very Rare"]
        num_gems = random.randint(3, 6)
        gems = random.choices(GEM_TABLE_TIER3, k=num_gems)

    else:
        # Tier 4 (CR 17+)
        gp = _roll_dice(10, 10) * 1000
        pp = _roll_dice(5, 10) * 1000
        eligible_rarities = ["Very Rare", "Legendary"]
        num_gems = random.randint(4, 8)
        gems = random.choices(GEM_TABLE_TIER4, k=num_gems)

    # Calculate total gold equivalent (100 CP = 1 GP, 10 SP = 1 GP, 1 PP = 10 GP)
    total_gp_equiv = round(gp + (pp * 10) + (sp / 10) + (cp / 100), 2)

    # Magic items selection from Firestore
    dropped_items: list[dict[str, Any]] = []
    if include_magic_items:
        firestore_items: list[dict[str, Any]] = []
        for rarity in eligible_rarities:
            found = search_items_in_db(rarity=rarity)
            firestore_items.extend(found)

        # Decide how many items drop based on tier
        if cr <= 4 and random.random() < 0.60 and firestore_items:
            dropped_items.append(random.choice(firestore_items))
        elif 4 < cr <= 10 and firestore_items:
            k = min(len(firestore_items), random.randint(1, 2))
            dropped_items.extend(random.sample(firestore_items, k=k))
        elif 10 < cr and firestore_items:
            k = min(len(firestore_items), random.randint(1, 3))
            dropped_items.extend(random.sample(firestore_items, k=k))

        # If high CR or no items were found in Firestore, create a tailored reward in DB
        if not dropped_items and include_magic_items:
            fallback_rarity = eligible_rarities[-1]
            custom_item = add_item_to_db(
                name=f"Relic of the {target_name.split()[0]}",
                item_type="Wondrous Item",
                rarity=fallback_rarity,
                description=f"A resonant relic recovered from defeating {target_name}. Radiates latent magic.",
                cost_gp=int(total_gp_equiv // 2) or 100,
                attunement=True,
                damage="None",
                properties=["Arcane Focus", "Enchanted"],
                tags=["loot", "relic", fallback_rarity.lower()],
            )
            dropped_items.append(custom_item)

    # Build output report
    lines = [
        f"### ⚔️ Victory Loot: Defeated {target_name} (CR {cr})",
        "",
        "#### 💰 Currency Recovered:",
    ]

    coin_parts = []
    if pp:
        coin_parts.append(f"**{pp:,} PP**")
    if gp:
        coin_parts.append(f"**{gp:,} GP**")
    if sp:
        coin_parts.append(f"**{sp:,} SP**")
    if cp:
        coin_parts.append(f"**{cp:,} CP**")

    if coin_parts:
        lines.append(f"- Coins: {', '.join(coin_parts)} *(Approx. **{total_gp_equiv:,} GP** equivalent)*")
    else:
        lines.append("- Coins: None")

    if gems:
        lines.append("")
        lines.append("#### 💎 Gemstones & Valuables:")
        for g in gems:
            lines.append(f"- {g}")

    if dropped_items:
        lines.append("")
        lines.append("#### 🎁 Magical Treasures (From Cloud Firestore Catalog):")
        for it in dropped_items:
            attune = " *(Requires Attunement)*" if it.get("attunement") else ""
            dmg = f" | Damage: `{it.get('damage')}`" if it.get("damage") and it.get("damage") != "None" else ""
            cost = f" | Value: {it.get('cost_gp', 0):,} GP" if it.get("cost_gp") else ""
            lines.append(f"- **{it.get('name')}** [{it.get('rarity')} {it.get('type')}{attune}{dmg}{cost}]:")
            lines.append(f"  *{it.get('description')}* (Firestore doc: `{it.get('id')}`)")
    else:
        lines.append("")
        lines.append("#### 🎁 Magical Treasures:")
        lines.append("- No magical items found in this hoard.")

    lines.append("")
    lines.append("*(Remember to record any equipped items or coins in your Active Inventory!)*")
    return "\n".join(lines)
