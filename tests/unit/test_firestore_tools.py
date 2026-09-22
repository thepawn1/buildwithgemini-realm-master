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

"""Unit tests for Cloud Firestore RPG item catalog functions and tools."""

import pytest
from app.agent import add_item_to_catalog, get_item_details, search_item_catalog
from app.firestore_db import PROJECT_ID, get_item_from_db, search_items_in_db


def test_hardcoded_project_id():
    """Verify that the project ID is hardcoded as required."""
    assert PROJECT_ID == "qwiklabs-gcp-04-0498b22523bb"


def test_search_seeded_items():
    """Verify seeded items are searchable via search_item_catalog."""
    res = search_item_catalog(query="bow")
    assert "Frostbow" in res
    assert "Rare Weapon" in res

    res_amulet = search_item_catalog(query="Sunshard")
    assert "Sunshard Amulet" in res_amulet


def test_get_item_details():
    """Verify get_item_details retrieves full metadata from Firestore."""
    details = get_item_details("Sunshard Amulet")
    assert "Sunshard Amulet" in details
    assert "Very Rare" in details
    assert "8000 GP" in details
    assert "Radiant Aura" in details


def test_add_and_retrieve_custom_item():
    """Verify writing a new item to Firestore and reading it back."""
    result = add_item_to_catalog(
        name="Elven Moonsilver Dagger",
        item_type="Weapon",
        rarity="Uncommon",
        description="A slender dagger that glows faintly when magical beasts are within 100 feet.",
        cost_gp=350,
        damage="1d4 + 1 piercing",
        properties=["Finesse", "Light", "Thrown"],
        tags=["dagger", "elf", "moonsilver"],
    )
    assert "Successfully saved item 'Elven Moonsilver Dagger'" in result

    # Read back
    details = get_item_details("Elven Moonsilver Dagger")
    assert "Elven Moonsilver Dagger" in details
    assert "350 GP" in details
    assert "1d4 + 1 piercing" in details
