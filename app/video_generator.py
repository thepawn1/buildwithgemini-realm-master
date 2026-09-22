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

"""Vertex AI Omni Video Generation and Cloud Storage public uploader for RealmMaster."""

from __future__ import annotations

import base64
import datetime
import logging
import re
import uuid

from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

logger = logging.getLogger(__name__)

PROJECT_ID = "qwiklabs-gcp-04-0498b22523bb"
LOCATION = "global"
BUCKET_NAME = "realm-master-assets-0498b22523bb"
VIDEO_MODEL = "gemini-omni-flash-preview"


def generate_item_video(
    item_name: str,
    visual_description: str,
    tool_context: ToolContext,
) -> str:
    """Generates a short showcase video for a fantasy tabletop RPG item using Google's Omni model.

    Saves the generated video artifact to the playground/session artifacts panel and uploads
    the video bytes directly to the public Cloud Storage bucket.

    Args:
        item_name: Name of the magical item, weapon, armor, artifact, or relic (e.g. 'Sunshard Amulet', 'Moonblade').
        visual_description: Visual prompt detailing the item, magical effects, lighting, and movement.
        tool_context: The ADK tool execution context used to persist the artifact.

    Returns:
        The public HTTPS URL of the video hosted on Cloud Storage.
    """
    enhanced_prompt = (
        f"A cinematic high-detail video showcase of the fantasy tabletop RPG item '{item_name}': "
        f"{visual_description}. Glowing magical aura, smooth camera motion, epic fantasy lighting."
    )

    try:
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )
        interaction = genai_client.interactions.create(
            model=VIDEO_MODEL,
            input=enhanced_prompt,
        )
    except Exception as e:
        logger.exception("Failed to generate video with Omni model: %s", e)
        return f"Video generation failed for item '{item_name}': {e}"

    output_video = getattr(interaction, "output_video", None)
    if not output_video or not getattr(output_video, "data", None):
        return f"Failed to generate video: No video data returned by model for '{item_name}'."

    raw_data = output_video.data
    if isinstance(raw_data, str):
        video_bytes = base64.b64decode(raw_data)
    elif isinstance(raw_data, bytes):
        video_bytes = raw_data
    else:
        return f"Unexpected video data format returned for '{item_name}'."

    # Generate clean filename and storage path
    clean_slug = re.sub(r"[^a-zA-Z0-9]+", "_", item_name[:30]).strip("_").lower() or "item"
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid.uuid4().hex[:6]
    artifact_filename = f"{clean_slug}_{unique_suffix}.mp4"
    blob_path = f"videos/{timestamp}_{artifact_filename}"

    # (1) Save video as an artifact using tool_context.save_artifact
    try:
        video_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        tool_context.save_artifact(
            filename=artifact_filename,
            artifact=video_part,
            custom_metadata={"item_name": item_name, "model": VIDEO_MODEL},
        )
    except Exception as e:
        logger.warning("Could not save video artifact to tool_context: %s", e)

    # (2) Upload video bytes directly to public Cloud Storage bucket
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(video_bytes, content_type="video/mp4")
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
    except Exception as e:
        logger.exception("Failed to upload video to Cloud Storage: %s", e)
        return f"Generated video but failed to upload to Cloud Storage: {e}"

    return public_url
