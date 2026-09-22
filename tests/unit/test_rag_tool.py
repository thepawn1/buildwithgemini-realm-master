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

"""Unit tests for the Dungeon Master's Guide RAG tool."""

from unittest.mock import MagicMock, patch
from app.rag_tool import consult_dungeon_masters_guide


def test_consult_dungeon_masters_guide_success():
    mock_context_1 = MagicMock()
    mock_context_1.text = "Rules for madness: A character afflicted with short-term madness rolls on the table."
    mock_context_2 = MagicMock()
    mock_context_2.text = "Sanity ability score optional rule."

    mock_resp = MagicMock()
    mock_resp.contexts.contexts = [mock_context_1, mock_context_2]

    with patch("vertexai.preview.rag.retrieval_query", return_value=mock_resp), \
         patch("vertexai.init"):
        res = consult_dungeon_masters_guide("madness rules")

    assert "Rules for madness" in res
    assert "Sanity ability score" in res


def test_consult_dungeon_masters_guide_no_contexts():
    mock_resp = MagicMock()
    mock_resp.contexts.contexts = []

    with patch("vertexai.preview.rag.retrieval_query", return_value=mock_resp), \
         patch("vertexai.init"):
        res = consult_dungeon_masters_guide("nonexistent obscure rule 12345")

    assert "No relevant passages found" in res


def test_consult_dungeon_masters_guide_exception():
    with patch("vertexai.preview.rag.retrieval_query", side_effect=Exception("API connection timeout")), \
         patch("vertexai.init"):
        res = consult_dungeon_masters_guide("traps")

    assert "Retrieval failed" in res
