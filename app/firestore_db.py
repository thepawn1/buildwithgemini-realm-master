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

"""Firestore database client and helper functions for RealmMaster items catalog."""

from __future__ import annotations

import re
from typing import Any
from google.cloud import firestore

# Hardcoded GCP project ID as required to avoid Agent Platform numeric project resolution
PROJECT_ID = "qwiklabs-gcp-04-0498b22523bb"
COLLECTION_NAME = "items"

_db_client: firestore.Client | None = None


def get_firestore_client() -> firestore.Client:
    """Returns a singleton Firestore client using the hardcoded project ID."""
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=PROJECT_ID)
    return _db_client


def _slugify(name: str) -> str:
    """Normalize item name to a consistent document ID."""
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    return clean.strip("_")


def get_item_from_db(name: str) -> dict[str, Any] | None:
    """Retrieve an item by name or document id."""
    db = get_firestore_client()
    doc_id = _slugify(name)
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return data

    # Fallback to search by exact name case-insensitively across collection
    coll_ref = db.collection(COLLECTION_NAME)
    for doc in coll_ref.stream():
        data = doc.to_dict() or {}
        if data.get("name", "").lower() == name.strip().lower():
            data["id"] = doc.id
            return data
    return None


def search_items_in_db(
    query: str = "", item_type: str = "", rarity: str = ""
) -> list[dict[str, Any]]:
    """Search items in the catalog matching query string, item type, or rarity."""
    db = get_firestore_client()
    coll_ref = db.collection(COLLECTION_NAME)

    results: list[dict[str, Any]] = []
    q_lower = query.strip().lower()
    type_lower = item_type.strip().lower()
    rarity_lower = rarity.strip().lower()

    for doc in coll_ref.stream():
        data = doc.to_dict() or {}
        data["id"] = doc.id

        # Type filter
        if type_lower and data.get("type", "").lower() != type_lower:
            continue

        # Rarity filter
        if rarity_lower and data.get("rarity", "").lower() != rarity_lower:
            continue

        # Search term filter (check name, description, properties, tags)
        if q_lower:
            name = data.get("name", "").lower()
            desc = data.get("description", "").lower()
            tags = [t.lower() for t in data.get("tags", [])]
            props = [p.lower() for p in data.get("properties", [])]

            if not (
                q_lower in name
                or q_lower in desc
                or any(q_lower in t for t in tags)
                or any(q_lower in p for p in props)
            ):
                continue

        results.append(data)

    return results


def add_item_to_db(
    name: str,
    item_type: str,
    rarity: str,
    description: str,
    cost_gp: int = 0,
    attunement: bool = False,
    damage: str = "None",
    properties: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Create or update an item in the Firestore collection."""
    db = get_firestore_client()
    doc_id = _slugify(name)
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)

    item_data: dict[str, Any] = {
        "name": name.strip(),
        "type": item_type.strip(),
        "rarity": rarity.strip(),
        "description": description.strip(),
        "cost_gp": cost_gp,
        "attunement": attunement,
        "damage": (damage or "None").strip(),
        "properties": properties or [],
        "tags": tags or [],
    }

    doc_ref.set(item_data, merge=True)
    item_data["id"] = doc_id
    return item_data
