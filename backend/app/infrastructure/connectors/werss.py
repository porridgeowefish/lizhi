from __future__ import annotations

import httpx

from app.core.config import Settings


class WerssConnector:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._token: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.settings.upstream_base_url,
                timeout=30.0,
            )
        return self._client

    async def _login(self) -> str:
        client = await self._get_client()
        response = await client.post(
            "/api/v1/wx/auth/login",
            data={
                "username": self.settings.upstream_username,
                "password": self.settings.upstream_password,
            },
        )
        response.raise_for_status()
        payload = response.json()
        self._token = payload["data"]["access_token"]
        return self._token

    async def _headers(self) -> dict[str, str]:
        if not self._token:
            await self._login()
        return {"Authorization": f"Bearer {self._token}"}

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        client = await self._get_client()
        headers = kwargs.pop("headers", {})
        headers.update(await self._headers())
        response = await client.request(method, path, headers=headers, **kwargs)
        if response.status_code == 401:
            await self._login()
            headers = kwargs.pop("headers", {})
            headers.update(await self._headers())
            response = await client.request(method, path, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    async def fetch_sources(self, limit: int) -> list[dict]:
        all_items: list[dict] = []
        offset = 0
        while len(all_items) < limit:
            batch_limit = min(100, limit - len(all_items))
            response = await self._request(
                "GET",
                "/api/v1/wx/mps",
                params={"offset": offset, "limit": batch_limit, "kw": ""},
            )
            items = response.json().get("data", {}).get("list", [])
            if not items:
                break
            all_items.extend(items)
            offset += len(items)
        return all_items[:limit]

    async def fetch_articles(self, source_id: str, limit: int) -> list[dict]:
        response = await self._request(
            "GET",
            "/api/v1/wx/articles",
            params={"offset": 0, "limit": limit, "search": "", "mp_id": source_id},
        )
        return response.json().get("data", {}).get("list", [])

    async def fetch_article_detail(self, article_id: str) -> dict | None:
        response = await self._request(
            "GET",
            f"/api/v1/wx/articles/{article_id}",
        )
        payload = response.json()
        return payload.get("data") if payload.get("code") == 0 else None
