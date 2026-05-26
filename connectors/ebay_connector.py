"""Small eBay Browse API connector with a deterministic fixture fallback."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import parse, request
from urllib.error import HTTPError, URLError


EBAY_SCOPE = "https://api.ebay.com/oauth/api_scope"
DEFAULT_QUERY = "Louis Vuitton handbag"
DEFAULT_MARKETPLACE_ID = "EBAY_US"


class EbayConnectorError(RuntimeError):
    """Raised when live eBay access fails before fixture fallback is applied."""


@dataclass
class EbayConnectorConfig:
    client_id: str | None = None
    client_secret: str | None = None
    marketplace_id: str = DEFAULT_MARKETPLACE_ID
    environment: str = "production"
    timeout_seconds: int = 10
    fixture_path: Path = Path(__file__).resolve().parents[1] / "fixtures" / "ebay_luxury_listings.json"

    @classmethod
    def from_env(cls) -> "EbayConnectorConfig":
        return cls(
            client_id=os.environ.get("EBAY_CLIENT_ID"),
            client_secret=os.environ.get("EBAY_CLIENT_SECRET"),
            marketplace_id=os.environ.get("EBAY_MARKETPLACE_ID", DEFAULT_MARKETPLACE_ID),
            environment=os.environ.get("EBAY_ENV", "production"),
            timeout_seconds=int(os.environ.get("EBAY_TIMEOUT_SECONDS", "10")),
        )

    @property
    def has_credentials(self) -> bool:
        return bool(self.client_id and self.client_secret)

    @property
    def api_root(self) -> str:
        if self.environment.lower() == "sandbox":
            return "https://api.sandbox.ebay.com"
        return "https://api.ebay.com"


class EbayBrowseConnector:
    def __init__(self, config: EbayConnectorConfig | None = None):
        self.config = config or EbayConnectorConfig.from_env()

    def search(
        self,
        query: str | None = None,
        limit: int = 12,
        fallback_to_fixture: bool = True,
    ) -> dict[str, Any]:
        clean_query = (query or os.environ.get("EBAY_SEARCH_QUERY") or DEFAULT_QUERY).strip()
        clean_limit = max(1, min(int(limit or 12), 50))

        if self.config.has_credentials:
            try:
                token = self._get_application_token()
                payload = self._search_live(token, clean_query, clean_limit)
                return {
                    "source": "ebay_browse",
                    "mode": "live",
                    "query": clean_query,
                    "marketplace_id": self.config.marketplace_id,
                    "items": self._normalise_items(payload.get("itemSummaries", [])),
                    "raw_total": payload.get("total", 0),
                    "error": None,
                }
            except EbayConnectorError as exc:
                if not fallback_to_fixture:
                    raise
                result = self._search_fixture(clean_query, clean_limit)
                result["mode"] = "fixture_fallback"
                result["error"] = str(exc)
                return result

        result = self._search_fixture(clean_query, clean_limit)
        result["error"] = "Missing EBAY_CLIENT_ID or EBAY_CLIENT_SECRET; using fixture data."
        return result

    def _get_application_token(self) -> str:
        credentials = f"{self.config.client_id}:{self.config.client_secret}".encode("utf-8")
        auth = base64.b64encode(credentials).decode("ascii")
        body = parse.urlencode({
            "grant_type": "client_credentials",
            "scope": EBAY_SCOPE,
        }).encode("utf-8")

        req = request.Request(
            f"{self.config.api_root}/identity/v1/oauth2/token",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )
        payload = self._read_json(req, "eBay OAuth token request failed")
        token = payload.get("access_token")
        if not token:
            raise EbayConnectorError("eBay OAuth token response did not include access_token.")
        return token

    def _search_live(self, token: str, query: str, limit: int) -> dict[str, Any]:
        params = parse.urlencode({"q": query, "limit": limit, "offset": 0})
        req = request.Request(
            f"{self.config.api_root}/buy/browse/v1/item_summary/search?{params}",
            method="GET",
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": self.config.marketplace_id,
                "Accept": "application/json",
            },
        )
        return self._read_json(req, "eBay Browse search failed")

    def _read_json(self, req: request.Request, message: str) -> dict[str, Any]:
        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise EbayConnectorError(f"{message}: HTTP {exc.code} {detail}") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EbayConnectorError(f"{message}: {exc}") from exc

    def _search_fixture(self, query: str, limit: int) -> dict[str, Any]:
        with self.config.fixture_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        items = payload.get("itemSummaries", [])
        terms = [term for term in query.lower().split() if len(term) > 2]
        matched = [
            item for item in items
            if not terms or any(term in item.get("title", "").lower() for term in terms)
        ]
        if not matched:
            matched = items

        selected = matched[:limit]
        return {
            "source": "ebay_browse",
            "mode": "fixture",
            "query": query,
            "marketplace_id": self.config.marketplace_id,
            "items": self._normalise_items(selected),
            "raw_total": len(matched),
            "error": None,
        }

    def _normalise_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalised = []
        for item in items:
            price = item.get("price") or {}
            value = price.get("value")
            try:
                price_value = float(value)
            except (TypeError, ValueError):
                continue

            seller = item.get("seller") or {}
            location = item.get("itemLocation") or {}
            image = item.get("image") or {}

            normalised.append({
                "source_item_id": item.get("itemId") or item.get("legacyItemId"),
                "title": item.get("title", "Untitled eBay listing"),
                "price_value": price_value,
                "currency": price.get("currency", "USD"),
                "seller_username": seller.get("username", "unknown_seller"),
                "seller_feedback_score": seller.get("feedbackScore"),
                "seller_feedback_pct": seller.get("feedbackPercentage"),
                "condition": item.get("condition"),
                "item_web_url": item.get("itemWebUrl"),
                "image_url": image.get("imageUrl"),
                "country": location.get("country"),
                "city": location.get("city"),
                "marketplace_id": self.config.marketplace_id,
            })
        return normalised
