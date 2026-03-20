"""HTTP client for the Trajan MCP API endpoints."""

from typing import Any

import httpx


class TrajanClient:
    """Typed HTTP client for the Trajan API's MCP endpoints.

    All methods target /api/v1/mcp/* and authenticate via Bearer API key.
    The API key is product-scoped — all data returned is for that product.
    """

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=f"{self._base}/api/v1/mcp",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    # --- helpers ---

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    async def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self._client.post(path, json=json)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    async def _patch(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self._client.patch(path, json=json)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    # --- read ---

    async def get_product(self) -> dict[str, Any]:
        return await self._get("/product")

    async def list_documents(
        self,
        type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if type:
            params["type"] = type
        return await self._get("/documents", params=params)

    async def get_document(self, document_id: str) -> dict[str, Any]:
        return await self._get(f"/documents/{document_id}")

    async def list_work_items(
        self,
        status: str | None = None,
        type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if type:
            params["type"] = type
        return await self._get("/work-items", params=params)

    async def get_work_item(self, work_item_id: str) -> dict[str, Any]:
        return await self._get(f"/work-items/{work_item_id}")

    async def search_documents(
        self,
        query: str,
        type: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"q": query, "limit": limit}
        if type:
            params["type"] = type
        return await self._get("/documents/search", params=params)

    # --- repositories ---

    async def list_repositories(self) -> dict[str, Any]:
        return await self._get("/repositories")

    async def get_repository_tree(
        self,
        repository_id: str,
        branch: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if branch:
            params["branch"] = branch
        return await self._get(f"/repositories/{repository_id}/tree", params=params or None)

    async def get_repository_file(
        self,
        repository_id: str,
        path: str,
        branch: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"path": path}
        if branch:
            params["branch"] = branch
        return await self._get(f"/repositories/{repository_id}/file", params=params)

    # --- write ---

    async def create_document(
        self,
        title: str,
        content: str | None = None,
        type: str = "note",
        section: str | None = None,
        subsection: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"title": title, "type": type}
        if content is not None:
            body["content"] = content
        if section is not None:
            body["section"] = section
        if subsection is not None:
            body["subsection"] = subsection
        return await self._post("/documents", json=body)

    async def update_document(
        self,
        document_id: str,
        title: str | None = None,
        content: str | None = None,
        type: str | None = None,
        section: str | None = None,
        subsection: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if content is not None:
            body["content"] = content
        if type is not None:
            body["type"] = type
        if section is not None:
            body["section"] = section
        if subsection is not None:
            body["subsection"] = subsection
        return await self._patch(f"/documents/{document_id}", json=body)

    async def create_work_item(
        self,
        title: str,
        description: str | None = None,
        type: str | None = None,
        priority: int | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"title": title}
        if description is not None:
            body["description"] = description
        if type is not None:
            body["type"] = type
        if priority is not None:
            body["priority"] = priority
        if tags is not None:
            body["tags"] = tags
        return await self._post("/work-items", json=body)

    async def update_work_item(
        self,
        work_item_id: str,
        title: str | None = None,
        description: str | None = None,
        type: str | None = None,
        status: str | None = None,
        priority: int | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if title is not None:
            body["title"] = title
        if description is not None:
            body["description"] = description
        if type is not None:
            body["type"] = type
        if status is not None:
            body["status"] = status
        if priority is not None:
            body["priority"] = priority
        if tags is not None:
            body["tags"] = tags
        return await self._patch(f"/work-items/{work_item_id}", json=body)

    # --- admin ---

    async def generate_docs(self, mode: str = "full") -> dict[str, Any]:
        return await self._post("/generate-docs", json={"mode": mode})

    async def get_docs_status(self) -> dict[str, Any]:
        return await self._get("/docs-status")

    async def get_codebase_context(self) -> dict[str, Any]:
        return await self._get("/codebase-context")

    async def sync_docs(
        self,
        document_ids: list[str] | None = None,
        message: str = "Sync documentation from Trajan (via MCP)",
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"message": message}
        if document_ids is not None:
            body["document_ids"] = document_ids
        return await self._post("/sync-docs", json=body)
