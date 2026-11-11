"""HTTP client for the XCC controller."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientError, ClientSession


class XCCApiError(Exception):
    """Raised when the XCC controller returns an error."""


class XCCApi:
    """Small async client for the controller's JSON API."""

    def __init__(self, host: str, username: str, password: str, session: ClientSession) -> None:
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.session = session

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            async with self.session.request(
                method,
                f"{self.host}{path}",
                headers={"Accept": "application/json"},
                timeout=15,
                **kwargs,
            ) as response:
                if response.status == 401:
                    raise XCCApiError("invalid_auth")
                if response.status >= 400:
                    raise XCCApiError(f"http_{response.status}")
                try:
                    return await response.json(content_type=None)
                except (json.JSONDecodeError, ClientError) as err:
                    raise XCCApiError("invalid_response") from err
        except XCCApiError:
            raise
        except (ClientError, TimeoutError) as err:
            raise XCCApiError("cannot_connect") from err

    async def async_login(self) -> Any:
        """Authenticate and retain the controller session cookie."""
        query = urlencode({"login": self.username, "pass": self.password})
        return await self._request("POST", f"/login.json?{query}")

    async def async_get_functions(self) -> dict[str, dict[str, Any]]:
        """Fetch current component state and normalize it to an ID map."""
        data = await self._request("GET", "/functions.json?status&extended")
        if isinstance(data, list):
            return {
                str(item["id"]): item
                for item in data
                if isinstance(item, dict) and item.get("id") is not None
            }
        if isinstance(data, dict):
            return {str(key): value for key, value in data.items() if isinstance(value, dict)}
        raise XCCApiError("invalid_response")

    async def async_get_extended_data(self) -> dict[str, Any]:
        """Fetch the global status and heat-pump unit projection."""
        unit_mask = {
            key: 1
            for key in (
                "pump",
                "power",
                "tcj",
                "mototime",
                "fanUp",
                "fanLo",
                "ts",
                "td",
                "te",
                "curr",
            )
        }
        mask = {
            "null": {
                key: 1
                for key in (
                    "tempOut",
                    "powerAct",
                    "tempAct",
                    "tempReq",
                    "hdo",
                    "hdoIgnore",
                    "hdoIgnoreTemp",
                    "on",
                    "error",
                )
            }
        }
        mask["null"]["units"] = [unit_mask]
        data = await self._request(
            "POST",
            "/getData.json?status&extended",
            json=mask,
        )
        if not isinstance(data, dict):
            raise XCCApiError("invalid_response")
        return data
