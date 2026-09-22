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

"""Unit tests for the live D&D 5e SRD REST API tool."""

import pytest
from app.agent import lookup_5e_srd


def test_lookup_monster():
    """Verify live lookup of monster stat block."""
    result = lookup_5e_srd(name="Goblin")
    assert "Goblin" in result
    assert "CR:" in result
    assert "HP:" in result
    assert "AC:" in result


def test_lookup_spell():
    """Verify live lookup of spell details."""
    result = lookup_5e_srd(name="Fireball")
    assert "Fireball" in result
    assert "Casting Time:" in result
    assert "Range:" in result


def test_lookup_condition():
    """Verify live lookup of condition mechanics."""
    result = lookup_5e_srd(name="Poisoned")
    assert "Poisoned" in result
    assert "disadvantage on attack rolls" in result


def test_lookup_missing():
    """Verify missing entry handling."""
    result = lookup_5e_srd(name="NonExistentFantasyCreatureX99")
    assert "No entry found" in result
