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

"""Agent Platform Code Execution Sandbox integration using AgentEngineSandboxCodeExecutor."""

import logging
import os
from typing import Optional
import vertexai
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from vertexai import types

logger = logging.getLogger(__name__)

PROJECT_ID = "qwiklabs-gcp-04-0498b22523bb"
LOCATION = "us-central1"
DEFAULT_AGENT_ENGINE_RESOURCE = "projects/809099885048/locations/us-central1/reasoningEngines/4285231670291857408"
DEFAULT_SANDBOX_RESOURCE = (
    "projects/809099885048/locations/us-central1/reasoningEngines/4285231670291857408/sandboxEnvironments/3650335173507022848"
)


def get_agent_engine_resource_name() -> str:
    """Returns the agent engine resource name from environment or default."""
    return os.environ.get("AGENT_ENGINE_RESOURCE_NAME", DEFAULT_AGENT_ENGINE_RESOURCE)


def get_or_create_sandbox(
    project_id: str = PROJECT_ID,
    location: str = LOCATION,
    agent_engine_resource_name: Optional[str] = None,
) -> str:
    """Finds an active sandbox environment or creates a new one from the agent engine resource.

    Args:
        project_id: GCP project ID.
        location: GCP region.
        agent_engine_resource_name: Resource name of the parent ReasoningEngine.

    Returns:
        The full resource name of the active sandbox environment.
    """
    # 1. Check if explicitly configured in environment
    env_sandbox = os.environ.get("SANDBOX_RESOURCE_NAME")
    if env_sandbox:
        logger.info("Using configured sandbox resource from environment: %s", env_sandbox)
        return env_sandbox

    engine_name = agent_engine_resource_name or get_agent_engine_resource_name()

    try:
        client = vertexai.Client(project=project_id, location=location)
        # Check existing sandboxes
        existing_sandboxes = list(client.agent_engines.sandboxes.list(name=engine_name))
        for sb in existing_sandboxes:
            state_str = str(getattr(sb, "state", ""))
            if "RUNNING" in state_str or getattr(sb, "name", None):
                logger.info("Found existing running sandbox: %s", sb.name)
                return sb.name

        # If none exist, create one
        logger.info("No active sandbox found for %s. Creating a new sandbox environment...", engine_name)
        operation = client.agent_engines.sandboxes.create(
            spec={"code_execution_environment": {}},
            name=engine_name,
            config=types.CreateAgentEngineSandboxConfig(
                display_name="realm_master_sandbox",
                ttl="31536000s",
            ),
        )
        sandbox_name = operation.response.name
        logger.info("Successfully created sandbox environment: %s", sandbox_name)
        return sandbox_name
    except Exception as e:
        logger.warning("Error inspecting or creating sandbox dynamically (%s), falling back to %s", e, DEFAULT_SANDBOX_RESOURCE)
        return DEFAULT_SANDBOX_RESOURCE


def get_sandbox_code_executor(
    sandbox_resource_name: Optional[str] = None,
    agent_engine_resource_name: Optional[str] = None,
) -> AgentEngineSandboxCodeExecutor:
    """Constructs and returns an AgentEngineSandboxCodeExecutor.

    Args:
        sandbox_resource_name: Optional specific sandbox resource name.
        agent_engine_resource_name: Optional parent agent engine resource name.

    Returns:
        An initialized AgentEngineSandboxCodeExecutor.
    """
    engine_name = agent_engine_resource_name or get_agent_engine_resource_name()
    sandbox_name = sandbox_resource_name or get_or_create_sandbox(
        agent_engine_resource_name=engine_name
    )

    return AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=sandbox_name,
        agent_engine_resource_name=engine_name,
    )
