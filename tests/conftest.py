"""Shared fixtures for Jackson Hole Mountain Resort tests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.jackson_hole.const import DEFAULT_API_URL, DEFAULTS, DOMAIN

# Trimmed copy of all.json fetched 2026-10-26 (off season, all closed).
FIXTURE = Path(__file__).parent / "fixtures" / "all.json"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load custom_components/ in every test."""
    return


@pytest.fixture(autouse=True)
def us_units(hass):
    """The feed is in US units; keep test states in the same units."""
    hass.config.units = US_CUSTOMARY_SYSTEM


@pytest.fixture
def feed() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text())


@pytest.fixture
def mock_api(aioclient_mock: AiohttpClientMocker, feed) -> AiohttpClientMocker:
    aioclient_mock.get(DEFAULT_API_URL, json=feed)
    return aioclient_mock


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """An entry as 1.0.0 created it: every setting in data, no options."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Jackson Hole Mountain Resort",
        version=1,
        unique_id=DOMAIN,
        data={**DEFAULTS, "create_trail_entities": True},
    )
