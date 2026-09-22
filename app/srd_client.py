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

"""Live D&D 5e SRD REST API client for RealmMaster."""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

BASE_URL = "https://www.dnd5eapi.co/api"
DEFAULT_TIMEOUT = 5


def _slugify(text: str) -> str:
    """Normalize names to D&D 5e API index slugs (e.g. 'Adult Red Dragon' -> 'adult-red-dragon')."""
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")


def _get_json(url: str) -> dict[str, Any] | None:
    """Make HTTP GET request to D&D 5e API with timeout and headers."""
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "RealmMaster-Agent/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.debug("D&D 5e API request failed for %s: %s", url, e)
        return None


def _format_monster(data: dict[str, Any]) -> str:
    name = data.get("name", "Unknown Monster")
    cr = data.get("challenge_rating", "?")
    hp = data.get("hit_points", "?")
    size = data.get("size", "")
    type_str = data.get("type", "")
    alignment = data.get("alignment", "")

    # AC
    ac_field = data.get("armor_class")
    if isinstance(ac_field, list) and ac_field and isinstance(ac_field[0], dict):
        ac_val = ac_field[0].get("value", "?")
    else:
        ac_val = ac_field or "?"

    speed_dict = data.get("speed", {})
    speed_str = ", ".join(f"{k} {v}" for k, v in speed_dict.items()) if isinstance(speed_dict, dict) else str(speed_dict)

    stats = (
        f"STR {data.get('strength')} | DEX {data.get('dexterity')} | CON {data.get('constitution')} | "
        f"INT {data.get('intelligence')} | WIS {data.get('wisdom')} | CHA {data.get('charisma')}"
    )

    actions = []
    for action in data.get("actions", [])[:3]:
        actions.append(f"- **{action.get('name')}**: {action.get('desc')}")
    actions_str = "\n".join(actions) if actions else "None"

    special_abilities = []
    for trait in data.get("special_abilities", [])[:2]:
        special_abilities.append(f"- **{trait.get('name')}**: {trait.get('desc')}")
    traits_str = "\n" + "\n".join(special_abilities) if special_abilities else ""

    return (
        f"### 🐉 {name} ({size} {type_str}, {alignment})\n"
        f"- **CR:** {cr} | **HP:** {hp} | **AC:** {ac_val}\n"
        f"- **Speed:** {speed_str}\n"
        f"- **Ability Scores:** {stats}\n"
        f"{f'- **Traits:**{traits_str}\n' if traits_str else ''}"
        f"- **Key Actions:**\n{actions_str}"
    )


def _format_spell(data: dict[str, Any]) -> str:
    name = data.get("name", "Unknown Spell")
    level = data.get("level", 0)
    level_str = "Cantrip" if level == 0 else f"Level {level}"
    school = data.get("school", {}).get("name", "Magic")
    casting_time = data.get("casting_time", "1 action")
    range_dist = data.get("range", "Self")
    duration = data.get("duration", "Instantaneous")
    components = ", ".join(data.get("components", []))

    desc_lines = data.get("desc", [])
    desc_str = "\n".join(desc_lines) if isinstance(desc_lines, list) else str(desc_lines)

    higher = data.get("higher_level", [])
    higher_str = f"\n\n**At Higher Levels:** {' '.join(higher)}" if higher else ""

    return (
        f"### ✨ {name} ({level_str} {school})\n"
        f"- **Casting Time:** {casting_time} | **Range:** {range_dist} | **Duration:** {duration}\n"
        f"- **Components:** {components}\n"
        f"- **Description:** {desc_str}{higher_str}"
    )


def _format_condition(data: dict[str, Any]) -> str:
    name = data.get("name", "Condition")
    desc_lines = data.get("desc", [])
    desc_str = "\n".join(desc_lines) if isinstance(desc_lines, list) else str(desc_lines)
    return f"### ⚠️ {name} (Condition)\n{desc_str}"


def lookup_srd_data(name: str, category: str = "") -> str:
    """Queries the live D&D 5e SRD REST API for monsters, spells, conditions, or equipment.

    Args:
        name: Name or search term (e.g. 'Goblin', 'Fireball', 'Paralyzed', 'Owlbear').
        category: Optional category filter ('monsters', 'spells', 'conditions', 'equipment').

    Returns:
        Formatted markdown documentation from the official SRD.
    """
    category_slug = category.strip().lower()
    valid_categories = ["monsters", "spells", "conditions", "equipment"]

    if category_slug and category_slug in valid_categories:
        search_categories = [category_slug]
    else:
        search_categories = valid_categories

    slug = _slugify(name)

    # 1. Try direct exact match on each category
    for cat in search_categories:
        data = _get_json(f"{BASE_URL}/{cat}/{slug}")
        if data and "name" in data:
            if cat == "monsters":
                return _format_monster(data)
            elif cat == "spells":
                return _format_spell(data)
            elif cat == "conditions":
                return _format_condition(data)
            else:
                desc = " ".join(data.get("desc", [])) if "desc" in data else str(data)
                return f"### {data.get('name')}\n{desc}"

    # 2. Try search by name parameter fallback
    for cat in search_categories:
        search_url = f"{BASE_URL}/{cat}/?name={urllib.parse.quote(name.strip())}"
        results = _get_json(search_url)
        if results and results.get("count", 0) > 0:
            first_idx = results["results"][0]["index"]
            item_data = _get_json(f"{BASE_URL}/{cat}/{first_idx}")
            if item_data:
                if cat == "monsters":
                    return _format_monster(item_data)
                elif cat == "spells":
                    return _format_spell(item_data)
                elif cat == "conditions":
                    return _format_condition(item_data)
                else:
                    return f"### {item_data.get('name')}\n{item_data.get('desc', '')}"

    return (
        f"No entry found in the official D&D 5e SRD for '{name}'. "
        f"Searched categories: {', '.join(search_categories)}. "
        f"You may adjudicate the rule directly or check the custom Firestore catalog."
    )
