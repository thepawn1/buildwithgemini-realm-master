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

"""Unit tests for the Vertex AI Image Generator and GCS uploader."""

from unittest.mock import MagicMock, patch
from app.image_generator import generate_and_upload_scene_art


def test_generate_and_upload_scene_art_success():
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake-png-bytes"
    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part]
    mock_genai_response = MagicMock()
    mock_genai_response.candidates = [mock_candidate]

    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.return_value = mock_genai_response

    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_storage_client = MagicMock()
    mock_storage_client.bucket.return_value = mock_bucket

    with patch("google.genai.Client", return_value=mock_genai_client), \
         patch("google.cloud.storage.Client", return_value=mock_storage_client):
        result = generate_and_upload_scene_art("Eldrin in the Whispering Woods")

    assert "![" in result
    assert "https://storage.googleapis.com/realm-master-assets-0498b22523bb/scenes/" in result
    mock_blob.upload_from_string.assert_called_once_with(b"fake-png-bytes", content_type="image/png")


def test_generate_and_upload_scene_art_model_failure():
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.side_effect = Exception("Model quota exceeded")

    with patch("google.genai.Client", return_value=mock_genai_client):
        result = generate_and_upload_scene_art("Sunken Ruins")

    assert "Image generation failed" in result
    assert "Model quota exceeded" in result


def test_generate_and_upload_scene_art_upload_failure():
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake-png-bytes"
    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part]
    mock_genai_response = MagicMock()
    mock_genai_response.candidates = [mock_candidate]

    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.return_value = mock_genai_response

    mock_storage_client = MagicMock()
    mock_storage_client.bucket.side_effect = Exception("GCS write permission denied")

    with patch("google.genai.Client", return_value=mock_genai_client), \
         patch("google.cloud.storage.Client", return_value=mock_storage_client):
        result = generate_and_upload_scene_art("Dragon Den")

    assert "failed to upload to Cloud Storage" in result
