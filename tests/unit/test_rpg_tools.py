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

from app.agent import roll_dice, lookup_dnd_rules


def test_roll_dice_valid():
    res = roll_dice("1d20+5")
    assert "Rolled 1d20+5" in res
    assert "Total:" in res


def test_roll_dice_invalid():
    res = roll_dice("invalid_dice")
    assert "Invalid dice expression" in res


def test_lookup_dnd_rules():
    magic_missile = lookup_dnd_rules("magic missile")
    assert "automatically hits" in magic_missile
    assert "1d4 + 1" in magic_missile

    unknown = lookup_dnd_rules("unknown_topic_xyz")
    assert "Rules reference" in unknown
