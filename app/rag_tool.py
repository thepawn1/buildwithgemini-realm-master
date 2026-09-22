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

"""Vertex AI RAG Engine retrieval tool for the D&D 5e Dungeon Master's Guide."""

from __future__ import annotations

import logging
import vertexai
from vertexai.preview import rag

logger = logging.getLogger(__name__)

PROJECT_ID = "qwiklabs-gcp-04-0498b22523bb"
LOCATION = "us-central1"
CORPUS_NAME = "projects/qwiklabs-gcp-04-0498b22523bb/locations/us-central1/ragCorpora/1777576050578948096"


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
    try:
        # Region gotcha: serverless corpus is us-central1 only; pin Vertex AI client to corpus region
        vertexai.init(project=PROJECT_ID, location=LOCATION)

        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=4),
        )
    except Exception as e:
        logger.warning("RAG retrieval query failed for '%s': %s", query, e)
        return f"Retrieval failed from Dungeon Master's Guide corpus: {e}"

    contexts = getattr(resp.contexts, "contexts", [])
    passages = []
    for c in contexts:
        text = getattr(c, "text", "").strip()
        if text:
            passages.append(text)

    if not passages:
        return f"No relevant passages found in the Dungeon Master's Guide for query: '{query}'."

    return "\n\n---\n\n".join(passages)
