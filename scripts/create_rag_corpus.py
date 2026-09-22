#!/usr/bin/env python3
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

"""Script to create a serverless Vertex AI RAG corpus and import the Dungeon Master's Guide."""

import os
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-04-0498b22523bb"
LOCATION = "us-central1"
GCS_PATHS = [
    "gs://realm-master-assets-0498b22523bb/rag/dnd_5e_dmg_part1.pdf",
    "gs://realm-master-assets-0498b22523bb/rag/dnd_5e_dmg_part2.pdf",
    "gs://realm-master-assets-0498b22523bb/rag/dnd_5e_dmg_part3.pdf",
]
CORPUS_DISPLAY_NAME = "dnd-5e-dungeon-masters-guide"

def main():
    print(f"Initializing Vertex AI (project: {PROJECT_ID}, location: {LOCATION})...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # 1. Ensure serverless mode
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    print("Ensuring serverless mode on ragEngineConfig...")
    try:
        rag.update_rag_engine_config(
            rag_engine_config=rag.RagEngineConfig(
                name=cfg,
                rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
            )
        )
        print("✓ Serverless mode confirmed.")
    except Exception as e:
        print(f"Note on config update: {e}")

    # 2. Check for existing corpus with the same display name
    existing_corpora = rag.list_corpora()
    target_corpus = None
    for c in existing_corpora:
        if c.display_name == CORPUS_DISPLAY_NAME:
            target_corpus = c
            print(f"Found existing corpus: {c.name}")
            break

    if not target_corpus:
        print(f"Creating serverless RAG corpus '{CORPUS_DISPLAY_NAME}'...")
        target_corpus = rag.create_corpus(
            display_name=CORPUS_DISPLAY_NAME,
            embedding_model_config=rag.EmbeddingModelConfig(
                publisher_model="publishers/google/models/text-embedding-005"
            ),
        )
        print(f"✓ Created corpus: {target_corpus.name}")

    corpus_name = target_corpus.name

    # 3. Import and index the DMG PDF parts
    print(f"Importing {GCS_PATHS} into corpus {corpus_name}...")
    resp = rag.import_files(
        corpus_name=corpus_name,
        paths=GCS_PATHS,
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
    )
    print(f"✓ Import response: imported {resp.imported_rag_files_count} file(s)")
    if resp.failed_rag_files_count:
        print(f"⚠️ Failed files count: {resp.failed_rag_files_count}")

    print("\n=======================================================")
    print(f"RAG CORPUS NAME: {corpus_name}")
    print("=======================================================")
    return corpus_name

if __name__ == "__main__":
    main()
