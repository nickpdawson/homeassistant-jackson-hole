"""Fetch the Jackson Hole all.json feed and read values out of it.

The feed wraps most numbers as {"value": "10,000", "unitSymbol": "ft"},
sends {} when a value is missing, and formats some numbers with commas.
The helpers here return None for anything missing or unparseable so the
entities never raise on a sparse or off-season feed.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime
import json
from typing import Any

import aiohttp

from .const import FETCH_TIMEOUT, MAX_RESPONSE_BYTES


class ApiError(Exception):
    """The feed could not be fetched or is not the resort feed."""


class ResponseTooLarge(ApiError):
    """The response was larger than the allowed limit."""


def child(node: Any, *path: str) -> Any:
    """Walk nested dict keys, returning None at the first missing step."""
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def section(data: Any, *path: str) -> dict[str, Any]:
    """Return a nested dict, or {} if it is missing or not a dict."""
    node = child(data, *path)
    return node if isinstance(node, dict) else {}


def to_number(value: Any) -> float | None:
    """Parse '10,000', '7' or 7 to a float. None if it is not a number."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return None
    return None


def measure(data: Any, *path: str) -> float | None:
    """Read the numeric 'value' of a measurement dict at path."""
    node = child(data, *path)
    if isinstance(node, dict):
        return to_number(node.get("value"))
    return None


def to_int(value: Any) -> int | None:
    number = to_number(value)
    return None if number is None else int(number)


def parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else None


def is_open(status: Any) -> bool:
    return isinstance(status, str) and status.strip().upper() == "OPEN"


async def read_limited(response: aiohttp.ClientResponse, limit: int) -> bytes:
    """Read the body, stopping once it passes limit bytes."""
    declared = to_int(response.headers.get(aiohttp.hdrs.CONTENT_LENGTH))
    if declared is not None and declared > limit:
        raise ResponseTooLarge(f"Response is {declared} bytes, limit {limit}")
    body = bytearray()
    async for chunk in response.content.iter_chunked(65536):
        body.extend(chunk)
        if len(body) > limit:
            raise ResponseTooLarge(f"Response exceeds {limit} bytes")
    return bytes(body)


async def fetch_data(session: aiohttp.ClientSession, url: str) -> dict[str, Any]:
    """Download and decode all.json. Raises ApiError on any failure."""
    try:
        async with asyncio.timeout(FETCH_TIMEOUT):
            async with session.get(url) as response:
                if response.status != 200:
                    raise ApiError(f"API returned HTTP {response.status}")
                body = await read_limited(response, MAX_RESPONSE_BYTES)
    except TimeoutError as err:
        raise ApiError(f"Timed out after {FETCH_TIMEOUT}s fetching {url}") from err
    except aiohttp.ClientError as err:
        raise ApiError(f"Error fetching {url}: {err}") from err

    try:
        data = json.loads(body)
    except ValueError as err:
        raise ApiError(f"Response is not JSON: {err}") from err
    if not isinstance(data, dict) or "respTimestamp" not in data:
        raise ApiError("Response is not the resort feed (no respTimestamp)")
    return data
