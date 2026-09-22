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

"""Unit tests for the Dynamic Encounter Loot Dropper."""

from unittest.mock import patch
from app.loot_dropper import generate_encounter_loot


def test_generate_encounter_loot_tier1():
    fake_items = [
        {
            "id": "potion_of_greater_healing",
            "name": "Potion of Greater Healing",
            "rarity": "Uncommon",
            "type": "Potion",
            "description": "Restores 4d4+4 HP.",
            "cost_gp": 150,
            "attunement": False,
        }
    ]

    fake_custom_item = {
        "id": "relic_of_the_goblin",
        "name": "Relic of the Goblin",
        "rarity": "Uncommon",
        "type": "Wondrous Item",
        "description": "A resonant relic.",
        "cost_gp": 50,
        "attunement": True,
    }

    with patch("app.loot_dropper.search_items_in_db", return_value=fake_items), \
         patch("app.loot_dropper.add_item_to_db", return_value=fake_custom_item):
        loot = generate_encounter_loot(challenge_rating=1, enemy_name="Goblin Patrol")

    assert "Goblin Patrol" in loot
    assert "CR 1.0" in loot
    assert "Currency Recovered" in loot
    assert "GP" in loot or "SP" in loot or "CP" in loot


def test_generate_encounter_loot_tier2():
    fake_items = [
        {
            "id": "frostbow",
            "name": "Frostbow",
            "rarity": "Rare",
            "type": "Weapon",
            "description": "Deals 1d6 cold damage.",
            "cost_gp": 2500,
            "attunement": True,
            "damage": "1d8 piercing + 1d6 cold",
        }
    ]

    with patch("app.loot_dropper.search_items_in_db", return_value=fake_items):
        loot = generate_encounter_loot(challenge_rating=7, enemy_name="Young Chimera")

    assert "Young Chimera" in loot
    assert "CR 7.0" in loot
    assert "Gemstones & Valuables" in loot
    assert "Frostbow" in loot
    assert "Requires Attunement" in loot


def test_generate_encounter_loot_tier3_and_tier4():
    fake_items = [
        {
            "id": "sunshard_amulet",
            "name": "Sunshard Amulet",
            "rarity": "Very Rare",
            "type": "Wondrous Item",
            "description": "Crystallized teardrop of solar radiance.",
            "cost_gp": 8000,
            "attunement": True,
        }
    ]

    with patch("app.loot_dropper.search_items_in_db", return_value=fake_items):
        loot_t3 = generate_encounter_loot(challenge_rating=14, enemy_name="Shadowfang Wyrm")
        loot_t4 = generate_encounter_loot(challenge_rating=20, enemy_name="Ancient Red Dragon")

    assert "Shadowfang Wyrm" in loot_t3
    assert "Ancient Red Dragon" in loot_t4
    assert "PP" in loot_t3
    assert "PP" in loot_t4


def test_generate_encounter_loot_creates_custom_item_when_none_found():
    created_item = {
        "id": "relic_of_the_beast",
        "name": "Relic of the Beast",
        "rarity": "Rare",
        "type": "Wondrous Item",
        "description": "A resonant relic.",
        "cost_gp": 500,
        "attunement": True,
    }

    with patch("app.loot_dropper.search_items_in_db", return_value=[]), \
         patch("app.loot_dropper.add_item_to_db", return_value=created_item) as mock_add:
        loot = generate_encounter_loot(challenge_rating=5, enemy_name="Beast of Chaos")

    assert "Beast of Chaos" in loot
    assert "Relic of the Beast" in loot
    mock_add.assert_called_once()
