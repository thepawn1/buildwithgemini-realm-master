#!/usr/bin/env python3
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

"""Seed script to populate Cloud Firestore with initial tabletop RPG compendium items.

Important: Hardcodes project ID 'qwiklabs-gcp-04-0498b22523bb' as a string to avoid
Agent Platform numeric project resolution breaking Firestore.
"""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-0498b22523bb"
COLLECTION_NAME = "items"

SEEDED_ITEMS = [
    {
        "id": "frostbow",
        "name": "Frostbow",
        "type": "Weapon",
        "rarity": "Rare",
        "cost_gp": 2500,
        "attunement": True,
        "damage": "1d8 piercing + 1d6 cold",
        "properties": [
            "Ranged (150/600)",
            "Heavy",
            "Two-handed",
            "Magical",
        ],
        "tags": ["weapon", "bow", "cold", "ranged", "ranger", "elf"],
        "description": (
            "Carved from pale glacial pine and etched with silver runes of the Winter Court. "
            "Arrows fired from this bow glow with pale blue frost and deal an additional 1d6 cold damage on impact. "
            "Favored weapon of the Wood Elf Ranger Eldrin."
        ),
    },
    {
        "id": "sunshard_amulet",
        "name": "Sunshard Amulet",
        "type": "Wondrous Item",
        "rarity": "Very Rare",
        "cost_gp": 8000,
        "attunement": True,
        "damage": "None",
        "properties": [
            "Radiant Aura",
            "Necrotic Resistance",
            "Sunlight Emission",
        ],
        "tags": ["amulet", "wondrous item", "radiant", "sunlight", "quest", "artifact"],
        "description": (
            "A golden medallion cradling a crystallized teardrop of solar radiance. "
            "Emits bright sunlight in a 30-foot radius on command, and grants the bearer advantage on saving throws "
            "against necrotic damage. Currently hidden in the Sunken Ruins guarded by the Shadowfang Wyrm."
        ),
    },
    {
        "id": "potion_of_greater_healing",
        "name": "Potion of Greater Healing",
        "type": "Potion",
        "rarity": "Uncommon",
        "cost_gp": 150,
        "attunement": False,
        "damage": "None",
        "properties": ["Consumable", "Healing"],
        "tags": ["potion", "healing", "consumable"],
        "description": (
            "A swirling red liquid that glimmers when agitated. "
            "When you drink this potion as an action or bonus action, you regain 4d4 + 4 hit points."
        ),
    },
    {
        "id": "flame_tongue_longsword",
        "name": "Flame Tongue Longsword",
        "type": "Weapon",
        "rarity": "Rare",
        "cost_gp": 2000,
        "attunement": True,
        "damage": "1d8 slashing (1d10 versatile) + 2d6 fire",
        "properties": ["Versatile", "Melee", "Fire Damage", "Illumination"],
        "tags": ["weapon", "sword", "fire", "melee"],
        "description": (
            "You can speak this magic sword's command word to cause flames to engulf the blade. "
            "While blazing, it sheds bright light in a 40-foot radius and deals an extra 2d6 fire damage to any target it hits."
        ),
    },
    {
        "id": "cloak_of_elvenkind",
        "name": "Cloak of Elvenkind",
        "type": "Wondrous Item",
        "rarity": "Uncommon",
        "cost_gp": 500,
        "attunement": True,
        "damage": "None",
        "properties": ["Stealth Advantage", "Camouflage"],
        "tags": ["wondrous item", "cloak", "stealth", "elf"],
        "description": (
            "Woven by master elven tailors with fibers that shift color to match surroundings. "
            "While wearing the cloak with its hood drawn, Wisdom (Perception) checks made to see you have disadvantage, "
            "and you have advantage on Dexterity (Stealth) checks made to hide."
        ),
    },
    {
        "id": "dwarven_thrower_greataxe",
        "name": "Dwarven Thrower Greataxe",
        "type": "Weapon",
        "rarity": "Very Rare",
        "cost_gp": 6000,
        "attunement": True,
        "damage": "1d12 slashing + 1d8 thunder (thrown)",
        "properties": ["Heavy", "Two-handed", "Thrown (range 20/60)", "Returning"],
        "tags": ["weapon", "axe", "dwarf", "barbarian", "thrown"],
        "description": (
            "Imbued with ancient dwarf runes from deep volcanic forges. When hurled at an enemy, "
            "it impacts with a thunderous shockwave dealing an additional 1d8 thunder damage, "
            "then instantly flies back to the wielder's hand. Grimlock's prized vanguard weapon."
        ),
    },
]


def seed_items() -> None:
    """Connects to Firestore using the hardcoded project ID and inserts the seeded items."""
    print(f"Connecting to Cloud Firestore (project: {PROJECT_ID})...")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection(COLLECTION_NAME)

    print(f"Seeding collection '{COLLECTION_NAME}' with {len(SEEDED_ITEMS)} items...")
    for item in SEEDED_ITEMS:
        doc_id = item["id"]
        data = {k: v for k, v in item.items() if k != "id"}
        collection.document(doc_id).set(data, merge=True)
        print(f"  ✓ Seeded item '{item['name']}' ({item['rarity']} {item['type']}) -> doc '{doc_id}'")

    print("\n✅ All items successfully seeded into Firestore!")


if __name__ == "__main__":
    seed_items()
