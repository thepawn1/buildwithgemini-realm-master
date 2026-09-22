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

"""Vertex AI Image Generation and Cloud Storage public uploader for RealmMaster."""

from __future__ import annotations

import datetime
import logging
import re
import uuid
from google import genai
from google.cloud import storage

logger = logging.getLogger(__name__)

PROJECT_ID = "qwiklabs-gcp-04-0498b22523bb"
LOCATION = "us-central1"
BUCKET_NAME = "realm-master-assets-0498b22523bb"
IMAGE_MODEL = "gemini-2.5-flash-image"


def generate_and_upload_scene_art(prompt: str, subject_type: str = "scene") -> str:
    """Generates an illustration using Vertex AI and uploads it to the public Cloud Storage bucket.

    Args:
        prompt: Visual description for the image (e.g. 'Wood Elf Ranger Eldrin aiming a frostbow').
        subject_type: Optional type of art ('scene', 'portrait', 'item', 'monster').

    Returns:
        A markdown-formatted string with the embedded image and public URL.
    """
    enhanced_prompt = (
        f"A detailed fantasy tabletop RPG digital illustration of: {prompt}. "
        f"Epic fantasy art style, atmospheric lighting, rich colors, high detail."
    )

    try:
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        response = genai_client.models.generate_content(
            model=IMAGE_MODEL,
            contents=enhanced_prompt,
        )
    except Exception as e:
        logger.exception("Failed to generate image with Vertex AI: %s", e)
        return f"Image generation failed for prompt '{prompt}': {e}"

    image_bytes = None
    for candidate in getattr(response, "candidates", []):
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []):
            inline_data = getattr(part, "inline_data", None)
            if inline_data and getattr(inline_data, "data", None):
                image_bytes = inline_data.data
                break
        if image_bytes:
            break

    if not image_bytes:
        return f"Failed to generate image: No image data returned from model for prompt '{prompt}'."

    # Generate a clean filename slug
    clean_slug = re.sub(r"[^a-zA-Z0-9]+", "_", prompt[:30]).strip("_").lower() or "scene"
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid.uuid4().hex[:6]
    blob_path = f"scenes/{timestamp}_{clean_slug}_{unique_suffix}.png"

    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type="image/png")
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
    except Exception as e:
        logger.exception("Failed to upload image to GCS: %s", e)
        return f"Generated image but failed to upload to Cloud Storage: {e}"

    return (
        f"![{prompt}]({public_url})\n\n"
        f"**Public Image URL:** {public_url}\n"
        f"*(Generated with Vertex AI Imagen / {IMAGE_MODEL} and hosted on Cloud Storage)*"
    )
