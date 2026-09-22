# ruff: noqa
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

import datetime
import random
import re
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


MODEL = "gemini-3.6-flash"


async def generate_memories_callback(callback_context: CallbackContext):
    """Saves session events to Vertex AI Memory Bank after each turn."""
    try:
        await callback_context.add_session_to_memory()
    except (ValueError, Exception):
        # Gracefully skip if running in environments without a configured memory service
        pass
    return None


def roll_dice(expression: str) -> str:
    """Roll tabletop RPG dice using standard notation (e.g., '1d20+5', '2d6', '1d8+2').

    Args:
        expression: The dice expression to roll, such as '1d20', '2d6+3', or '1d100'.

    Returns:
        A string detailing each individual die roll and the final total result.
    """
    clean_expr = expression.strip().lower().replace(" ", "")
    match = re.match(r"^(\d+)?d(\d+)([+-]\d+)?$", clean_expr)
    if not match:
        return f"Invalid dice expression '{expression}'. Please use standard format like '1d20', '2d6+3', or '1d8-1'."

    num_dice = int(match.group(1)) if match.group(1) else 1
    die_sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    if num_dice > 100 or die_sides > 1000:
        return "Dice limits exceeded (maximum 100 dice with up to 1000 sides)."

    rolls = [random.randint(1, die_sides) for _ in range(num_dice)]
    total = sum(rolls) + modifier
    mod_str = f" {match.group(3)}" if modifier != 0 else ""
    return f"Rolled {clean_expr}: rolls={rolls}{mod_str} => Total: {total}"


def lookup_dnd_rules(topic: str) -> str:
    """Look up official rules, spell mechanics, condition descriptions, or monster details for 5e / tabletop RPGs.

    Args:
        topic: The spell, rule, condition, or monster name to look up (e.g., 'magic missile', 'rest', 'sneak attack').

    Returns:
        A concise reference summary of the official rules or mechanics.
    """
    topic_clean = topic.strip().lower()
    knowledge_base = {
        "magic missile": (
            "Magic Missile (1st-level Evocation, 1 action, 120 ft range, V/S): "
            "You create three glowing darts of magical force. Each dart hits a creature of your choice that you can see within range. "
            "A dart deals 1d4 + 1 force damage to its target. The darts all strike simultaneously, and you can direct them to hit one creature or several. "
            "Higher Levels: When cast using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st "
            "(e.g., 4 darts at 2nd level). Note: No attack roll or saving throw is required—it automatically hits."
        ),
        "fireball": (
            "Fireball (3rd-level Evocation, 1 action, 150 ft range, 20-ft radius sphere): "
            "Each creature in area must make a Dexterity saving throw. Takes 8d6 fire damage on failed save, half on successful. "
            "Scales +1d6 per slot level above 3rd."
        ),
        "sneak attack": (
            "Sneak Attack (Rogue feature): Once per turn, you can deal an extra 1d6 damage (scaling with rogue level) to one creature you hit "
            "with an attack if you have advantage on the attack roll, or if another enemy of the target is within 5 feet of it and you don't have disadvantage. "
            "The attack must use a finesse or ranged weapon."
        ),
        "rest": (
            "Short Rest: At least 1 hour of downtime; spend Hit Dice to regain HP. "
            "Long Rest: At least 8 hours of downtime (sleep/light activity); regain all HP and up to half your total Hit Dice."
        ),
    }
    for key, text in knowledge_base.items():
        if key in topic_clean:
            return text
    return f"Rules reference for '{topic}': Consult the standard tabletop 5e reference. Adjudicate in favor of fun and game balance."


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def search_item_catalog(query: str = "", item_type: str = "", rarity: str = "") -> str:
    """Searches the tabletop RPG item and equipment catalog in Cloud Firestore.

    Args:
        query: Optional keywords to search in item names, descriptions, properties, or tags (e.g. 'bow', 'healing', 'fire', 'frost').
        item_type: Optional item type filter (e.g. 'Weapon', 'Wondrous Item', 'Potion', 'Armor').
        rarity: Optional rarity filter (e.g. 'Common', 'Uncommon', 'Rare', 'Very Rare', 'Legendary').

    Returns:
        A formatted list of matching items with summary details.
    """
    from app.firestore_db import search_items_in_db

    items = search_items_in_db(query=query, item_type=item_type, rarity=rarity)
    if not items:
        return f"No items found matching query='{query}', type='{item_type}', rarity='{rarity}' in the Firestore catalog."

    output_lines = [f"Found {len(items)} item(s) in Firestore catalog:"]
    for it in items:
        attune_str = " (Requires Attunement)" if it.get("attunement") else ""
        cost_str = f" | Cost: {it.get('cost_gp', 0)} GP"
        damage_str = f" | Damage: {it.get('damage')}" if it.get("damage") and it.get("damage") != "None" else ""
        output_lines.append(
            f"- **{it.get('name')}** [{it.get('rarity')} {it.get('type')}{attune_str}{damage_str}{cost_str}]: {it.get('description')}"
        )
    return "\n".join(output_lines)


def get_item_details(item_name: str) -> str:
    """Retrieves full stats, mechanics, lore, and pricing for a specific item from the Firestore catalog.

    Args:
        item_name: The name of the item to retrieve (e.g. 'Frostbow', 'Sunshard Amulet', 'Potion of Greater Healing').

    Returns:
        Full detailed breakdown of the item from Firestore, or a not found message.
    """
    from app.firestore_db import get_item_from_db

    item = get_item_from_db(item_name)
    if not item:
        return f"Item '{item_name}' was not found in the Firestore catalog. You can add it using `add_item_to_catalog`."

    attune_str = "Yes" if item.get("attunement") else "No"
    props_str = ", ".join(item.get("properties", [])) or "None"
    tags_str = ", ".join(item.get("tags", [])) or "None"

    return (
        f"**{item.get('name')}**\n"
        f"- **Type:** {item.get('type')}\n"
        f"- **Rarity:** {item.get('rarity')}\n"
        f"- **Cost:** {item.get('cost_gp', 0)} GP\n"
        f"- **Requires Attunement:** {attune_str}\n"
        f"- **Damage / Effect:** {item.get('damage', 'None')}\n"
        f"- **Properties:** {props_str}\n"
        f"- **Tags:** {tags_str}\n"
        f"- **Description:** {item.get('description', '')}"
    )


def add_item_to_catalog(
    name: str,
    item_type: str,
    rarity: str,
    description: str,
    cost_gp: int = 0,
    attunement: bool = False,
    damage: str = "None",
    properties: list[str] | None = None,
    tags: list[str] | None = None,
) -> str:
    """Adds a new item or updates an existing item in the Cloud Firestore RPG catalog.

    Args:
        name: Name of the item (e.g. 'Moonblade', 'Dragon Scale Mail').
        item_type: Category (e.g. 'Weapon', 'Armor', 'Potion', 'Wondrous Item', 'Ring', 'Scroll').
        rarity: Rarity tier ('Common', 'Uncommon', 'Rare', 'Very Rare', 'Legendary', 'Artifact').
        description: Lore description and mechanical effects.
        cost_gp: Estimated value in gold pieces (GP).
        attunement: Whether the item requires attunement.
        damage: Damage roll expression or dice if applicable (e.g. '1d8 radiant').
        properties: List of weapon/armor/item properties (e.g. ['Finesse', 'Light']).
        tags: List of keywords for search indexing (e.g. ['sword', 'elf', 'radiant']).

    Returns:
        Confirmation message that the item was saved in Firestore.
    """
    from app.firestore_db import add_item_to_db

    item = add_item_to_db(
        name=name,
        item_type=item_type,
        rarity=rarity,
        description=description,
        cost_gp=cost_gp,
        attunement=attunement,
        damage=damage,
        properties=properties,
        tags=tags,
    )
    return (
        f"Successfully saved item '{item['name']}' ({item['rarity']} {item['type']}) "
        f"into Cloud Firestore catalog under document '{item['id']}'."
    )


def lookup_5e_srd(name: str, category: str = "") -> str:
    """Queries the live D&D 5e SRD REST API for official monster stat blocks, spells, conditions, or equipment.

    Args:
        name: Name of the creature, spell, or condition to look up (e.g. 'Goblin', 'Owlbear', 'Adult Red Dragon', 'Fireball', 'Paralyzed').
        category: Optional category filter ('monsters', 'spells', 'conditions', 'equipment'). If omitted, searches across all categories.

    Returns:
        Authoritative 5e rules, stats (HP, AC, CR, abilities, actions), or spell descriptions fetched live from the official SRD.
    """
    from app.srd_client import lookup_srd_data

    return lookup_srd_data(name=name, category=category)


def consult_dungeon_masters_guide(query: str) -> str:
    """Searches the official D&D 5e Dungeon Master's Guide (DMG) RAG corpus and returns relevant rules and passages.

    Use this tool whenever you or the adventurer need authoritative Dungeon Master guidance, dungeon hazard mechanics,
    madness and sanity rules, environmental hazards, downtime activities, planar lore, encounter balance guidelines,
    or magic item creation and identification rules.

    Args:
        query: What to look up in the Dungeon Master's Guide (e.g. 'madness rules', 'attunement', 'extreme heat hazard').

    Returns:
        The matched passages from the Dungeon Master's Guide vector corpus, or a message if none was found.
    """
    from app.rag_tool import consult_dungeon_masters_guide as _consult_dmg

    return _consult_dmg(query=query)


def generate_scene_art(prompt: str, subject_type: str = "scene") -> str:
    """Generates a fantasy RPG illustration, character portrait, or scene using Vertex AI and uploads it to Cloud Storage.

    Args:
        prompt: Visual description for the artwork (e.g. 'Wood Elf Ranger Eldrin aiming a frosty glowing recurve bow in a sunken cavern').
        subject_type: Optional category of art ('scene', 'portrait', 'item', 'monster').

    Returns:
        A markdown-formatted string with the embedded image and public Cloud Storage URL.
    """
    from app.image_generator import generate_and_upload_scene_art

    return generate_and_upload_scene_art(prompt=prompt, subject_type=subject_type)


def generate_item_video(
    item_name: str,
    visual_description: str,
    tool_context: ToolContext,
) -> str:
    """Generates a short showcase video for a fantasy RPG item using Google's Omni model (gemini-omni-flash-preview).

    Saves the video artifact in the session artifact registry and uploads the video bytes to the public Cloud Storage bucket.

    Args:
        item_name: Name of the magical item, relic, weapon, or armor (e.g. 'Sunshard Amulet', 'Moonblade', 'Dragon Scale Mail').
        visual_description: Detailed visual description of the item, magical particles, lighting, and movement.
        tool_context: Tool execution context injected by ADK.

    Returns:
        The public HTTPS URL of the video hosted on Cloud Storage (https://storage.googleapis.com/<bucket>/<object>).
    """
    from app.video_generator import generate_item_video as _gen_video

    return _gen_video(
        item_name=item_name,
        visual_description=visual_description,
        tool_context=tool_context,
    )


def generate_encounter_loot(
    challenge_rating: float,
    enemy_name: str = "",
    include_magic_items: bool = True,
) -> str:
    """Rolls dynamic encounter loot (currency, gemstones, and magic items) based on Challenge Rating (CR) and Cloud Firestore.

    Args:
        challenge_rating: The Challenge Rating (CR) of the defeated foe or encounter (e.g. 0.25, 1, 3, 5, 10, 15, 20).
        enemy_name: Optional name of the monster, boss, or encounter defeated (e.g. 'Owlbear', 'Shadowfang Wyrm').
        include_magic_items: Whether to roll and pick magical items from the Cloud Firestore compendium.

    Returns:
        A comprehensive formatted loot manifest with coins, gems, and magical items.
    """
    from app.loot_dropper import generate_encounter_loot as _gen_loot

    return _gen_loot(
        challenge_rating=challenge_rating,
        enemy_name=enemy_name,
        include_magic_items=include_magic_items,
    )


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

INSTRUCTION = schema_manager.generate_system_prompt(
    role_description="You are RealmMaster, an omniscient, deeply immersive Fantasy RPG Dungeon Master, rule keeper, and tabletop companion.",
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects. "
        "Use your memory to track Character Profile, Active Inventory, Party Members, and Ongoing Campaign Quest Notes."
    ),
    include_schema=True,
    include_examples=True,
)

from app.code_sandbox import get_sandbox_code_executor

sandbox_code_executor = get_sandbox_code_executor()

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    tools=[
        PreloadMemoryTool(),
        roll_dice,
        lookup_dnd_rules,
        lookup_5e_srd,
        consult_dungeon_masters_guide,
        generate_scene_art,
        generate_item_video,
        generate_encounter_loot,
        search_item_catalog,
        get_item_details,
        add_item_to_catalog,
        get_weather,
        get_current_time,
    ],
    code_executor=sandbox_code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
