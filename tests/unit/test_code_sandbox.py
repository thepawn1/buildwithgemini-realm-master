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

"""Unit tests for the Agent Platform Code Sandbox integration."""

import os
from unittest.mock import MagicMock, patch

from google.adk.code_executors import AgentEngineSandboxCodeExecutor

from app.code_sandbox import (
    DEFAULT_AGENT_ENGINE_RESOURCE,
    DEFAULT_SANDBOX_RESOURCE,
    get_agent_engine_resource_name,
    get_or_create_sandbox,
    get_sandbox_code_executor,
)


def test_get_agent_engine_resource_name():
    """Tests resolving agent engine resource name."""
    with patch.dict(os.environ, {}, clear=True):
        assert get_agent_engine_resource_name() == DEFAULT_AGENT_ENGINE_RESOURCE

    with patch.dict(os.environ, {"AGENT_ENGINE_RESOURCE_NAME": "projects/test/locations/us-central1/reasoningEngines/123"}):
        assert get_agent_engine_resource_name() == "projects/test/locations/us-central1/reasoningEngines/123"


def test_get_or_create_sandbox_from_env():
    """Tests sandbox resolution from environment variable."""
    custom_sb = "projects/test/locations/us-central1/reasoningEngines/123/sandboxEnvironments/456"
    with patch.dict(os.environ, {"SANDBOX_RESOURCE_NAME": custom_sb}):
        result = get_or_create_sandbox()
        assert result == custom_sb


def test_get_or_create_sandbox_existing():
    """Tests reusing an existing running sandbox from client.agent_engines.sandboxes.list."""
    mock_sb = MagicMock()
    mock_sb.name = "projects/test/locations/us-central1/reasoningEngines/123/sandboxEnvironments/existing-999"
    mock_sb.state = "STATE_RUNNING"

    mock_client = MagicMock()
    mock_client.agent_engines.sandboxes.list.return_value = [mock_sb]

    with patch.dict(os.environ, {}, clear=True):
        with patch("vertexai.Client", return_value=mock_client):
            result = get_or_create_sandbox(
                project_id="test-proj",
                location="us-central1",
                agent_engine_resource_name="projects/test/locations/us-central1/reasoningEngines/123",
            )
            assert result == mock_sb.name


def test_get_or_create_sandbox_create_new():
    """Tests creating a new sandbox when no existing one is found."""
    mock_op = MagicMock()
    mock_op.response.name = "projects/test/locations/us-central1/reasoningEngines/123/sandboxEnvironments/new-111"

    mock_client = MagicMock()
    mock_client.agent_engines.sandboxes.list.return_value = []
    mock_client.agent_engines.sandboxes.create.return_value = mock_op

    with patch.dict(os.environ, {}, clear=True):
        with patch("vertexai.Client", return_value=mock_client):
            result = get_or_create_sandbox(
                project_id="test-proj",
                location="us-central1",
                agent_engine_resource_name="projects/test/locations/us-central1/reasoningEngines/123",
            )
            assert result == "projects/test/locations/us-central1/reasoningEngines/123/sandboxEnvironments/new-111"
            mock_client.agent_engines.sandboxes.create.assert_called_once()


def test_get_or_create_sandbox_fallback_on_error():
    """Tests graceful fallback if vertexai.Client raises an exception."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("vertexai.Client", side_effect=RuntimeError("API error")):
            result = get_or_create_sandbox()
            assert result == DEFAULT_SANDBOX_RESOURCE


def test_get_sandbox_code_executor():
    """Tests constructing the AgentEngineSandboxCodeExecutor."""
    executor = get_sandbox_code_executor(
        sandbox_resource_name="projects/test/locations/us-central1/reasoningEngines/123/sandboxEnvironments/456"
    )
    assert isinstance(executor, AgentEngineSandboxCodeExecutor)
    assert executor.sandbox_resource_name == "projects/test/locations/us-central1/reasoningEngines/123/sandboxEnvironments/456"
