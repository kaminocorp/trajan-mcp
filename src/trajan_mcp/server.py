"""Trajan MCP Server — exposes Trajan product data as MCP tools and resources.

Environment variables:
    TRAJAN_API_KEY  — Product-scoped API key (trj_pk_...) with mcp:read/write scopes
    TRAJAN_API_URL  — Base URL of the Trajan API (default: https://api.trajancloud.com)
"""

import json
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

import httpx
from mcp.server.fastmcp import Context, FastMCP

from trajan_mcp.client import TrajanClient

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

_api_key = os.environ.get("TRAJAN_API_KEY", "")
_api_url = os.environ.get("TRAJAN_API_URL", "https://api.trajancloud.com")

_client: TrajanClient | None = None


def _get_client() -> TrajanClient:
    """Lazy-init the HTTP client so env vars can be set before import."""
    global _client
    if _client is None:
        key = os.environ.get("TRAJAN_API_KEY", _api_key)
        url = os.environ.get("TRAJAN_API_URL", _api_url)
        if not key:
            print(
                "Error: TRAJAN_API_KEY environment variable is required.\n"
                "Create an API key at https://www.trajancloud.com with mcp:read and mcp:write scopes.",
                file=sys.stderr,
            )
            sys.exit(1)
        _client = TrajanClient(base_url=url, api_key=key)
    return _client


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Startup / shutdown lifecycle."""
    yield
    if _client is not None:
        await _client.close()


mcp = FastMCP(
    "Trajan",
    instructions=(
        "Trajan is a developer workspace for managing software products. "
        "Use these tools to read project context, documentation, and work items, "
        "or to create new documents and tasks. "
        "The API key is scoped to a single product — all data is for that product."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_json(data: Any) -> str:
    """Format data as indented JSON for readable MCP responses."""
    return json.dumps(data, indent=2, default=str)


def _error_message(exc: httpx.HTTPStatusError) -> str:
    """Extract a human-readable error from an API error response."""
    try:
        detail = exc.response.json().get("detail", str(exc))
    except Exception:
        detail = exc.response.text or str(exc)
    return f"Error {exc.response.status_code}: {detail}"


# ---------------------------------------------------------------------------
# Resources — browsable data URIs
# ---------------------------------------------------------------------------


@mcp.resource(
    "product://overview", description="Product metadata, linked repositories, and entity counts"
)
async def resource_product_overview() -> str:
    """Product overview including name, description, repos, and counts."""
    client = _get_client()
    data = await client.get_product()
    return _fmt_json(data)


@mcp.resource("docs://list", description="All documents in the product (titles only, no content)")
async def resource_docs_list() -> str:
    """List of all documents with id, title, type, section, and updated_at."""
    client = _get_client()
    data = await client.list_documents(limit=500)
    return _fmt_json(data)


@mcp.resource(
    "docs://{document_id}",
    description="Full document with markdown content",
    mime_type="application/json",
)
async def resource_document(document_id: str) -> str:
    """Single document with full markdown content, type, section, and sync status."""
    client = _get_client()
    data = await client.get_document(document_id)
    return _fmt_json(data)


@mcp.resource("workitems://list", description="All work items in the product")
async def resource_work_items_list() -> str:
    """List of work items with id, title, type, status, priority, and tags."""
    client = _get_client()
    data = await client.list_work_items(limit=500)
    return _fmt_json(data)


@mcp.resource(
    "workitems://{item_id}",
    description="Full work item detail",
    mime_type="application/json",
)
async def resource_work_item(item_id: str) -> str:
    """Single work item with full description, status, priority, tags, and timestamps."""
    client = _get_client()
    data = await client.get_work_item(item_id)
    return _fmt_json(data)


@mcp.resource("repos://list", description="Repositories linked to the product")
async def resource_repos_list() -> str:
    """List of repositories with id, name, full_name, language, and default branch."""
    client = _get_client()
    data = await client.list_repositories()
    return _fmt_json(data)


@mcp.resource(
    "repo://{repository_id}/tree",
    description="File tree of a linked repository",
    mime_type="application/json",
)
async def resource_repo_tree(repository_id: str) -> str:
    """Complete file tree of a repository from GitHub (default branch)."""
    client = _get_client()
    data = await client.get_repository_tree(repository_id)
    return _fmt_json(data)


@mcp.resource(
    "codebase://context",
    description="AI-generated codebase analysis: tech stack, architecture, endpoints, models",
)
async def resource_codebase_context() -> str:
    """Deep codebase analysis including tech stack, architecture patterns, API endpoints,
    database models, services, and frontend pages. Null if analysis hasn't been run."""
    client = _get_client()
    data = await client.get_codebase_context()
    return _fmt_json(data)


# ---------------------------------------------------------------------------
# Tools — Read
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_product_overview(ctx: Context) -> str:
    """Get an overview of the product: name, description, repositories, and counts.

    Returns the product's metadata, linked repositories, and counts of
    documents and work items. Use this first to understand the project.
    """
    client = _get_client()
    try:
        data = await client.get_product()
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def list_documents(
    ctx: Context,
    type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """List documents in the product (titles only, no content).

    Args:
        type: Filter by document type (blueprint, plan, note, changelog, etc.)
        limit: Max results (1-500, default 50)
        offset: Pagination offset

    Returns a list of documents with id, title, type, section, and updated_at.
    To read full content, use get_document with a specific document ID.
    """
    client = _get_client()
    try:
        data = await client.list_documents(type=type, limit=limit, offset=offset)
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def get_document(ctx: Context, document_id: str) -> str:
    """Get a single document with its full markdown content.

    Args:
        document_id: UUID of the document to retrieve

    Returns the document's title, content, type, section, sync status, etc.
    """
    client = _get_client()
    try:
        data = await client.get_document(document_id)
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def search_documents(
    ctx: Context,
    query: str,
    type: str | None = None,
    limit: int = 10,
) -> str:
    """Search documents by title and content.

    Args:
        query: Search text (matched against title and content)
        type: Optional filter by document type
        limit: Max results (1-100, default 10)

    Returns matching documents with a text snippet around the match.
    """
    client = _get_client()
    try:
        data = await client.search_documents(query=query, type=type, limit=limit)
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def list_work_items(
    ctx: Context,
    status: str | None = None,
    type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    """List work items (tasks, features, bugs) in the product.

    Args:
        status: Filter by status (reported, in_progress, completed, etc.)
        type: Filter by type (feature, fix, refactor, investigation, bug, task)
        limit: Max results (1-500, default 50)
        offset: Pagination offset

    Returns a list of work items with id, title, type, status, priority, tags.
    """
    client = _get_client()
    try:
        data = await client.list_work_items(
            status=status, type=type, limit=limit, offset=offset
        )
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def get_work_item(ctx: Context, work_item_id: str) -> str:
    """Get a single work item with full details.

    Args:
        work_item_id: UUID of the work item to retrieve

    Returns the work item's title, description, type, status, priority, tags, etc.
    """
    client = _get_client()
    try:
        data = await client.get_work_item(work_item_id)
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


# ---------------------------------------------------------------------------
# Tools — Repositories
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_repositories(ctx: Context) -> str:
    """List repositories linked to the product.

    Returns a list of repositories with id, name, full_name, language, and URL.
    Use the repository ID with get_repository_tree or get_repository_file.
    """
    client = _get_client()
    try:
        data = await client.list_repositories()
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def get_repository_tree(
    ctx: Context,
    repository_id: str,
    branch: str | None = None,
) -> str:
    """Get the file tree of a linked GitHub repository.

    Args:
        repository_id: UUID of the repository
        branch: Branch name (defaults to the repository's default branch)

    Returns the full file tree with paths, types (file/directory), and sizes.
    """
    client = _get_client()
    try:
        data = await client.get_repository_tree(repository_id, branch=branch)
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def get_repository_file(
    ctx: Context,
    repository_id: str,
    path: str,
    branch: str | None = None,
) -> str:
    """Get the content of a single file from a linked GitHub repository.

    Args:
        repository_id: UUID of the repository
        path: File path within the repository (e.g. "src/main.py")
        branch: Branch name (defaults to the repository's default branch)

    Returns the file content as text. Binary files and files exceeding the
    size limit will return an error.
    """
    client = _get_client()
    try:
        data = await client.get_repository_file(repository_id, path=path, branch=branch)
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


# ---------------------------------------------------------------------------
# Tools — Write
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_document(
    ctx: Context,
    title: str,
    content: str | None = None,
    type: str = "note",
    section: str | None = None,
    subsection: str | None = None,
) -> str:
    """Create a new document in the product.

    Args:
        title: Document title
        content: Markdown content (optional)
        type: Document type — one of: blueprint, plan, note, changelog (default: note)
        section: Top-level section (e.g. "technical", "conceptual")
        subsection: Subsection (e.g. "backend", "frontend")

    Returns the created document with its ID.
    """
    client = _get_client()
    try:
        data = await client.create_document(
            title=title, content=content, type=type, section=section, subsection=subsection
        )
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def update_document(
    ctx: Context,
    document_id: str,
    title: str | None = None,
    content: str | None = None,
    type: str | None = None,
    section: str | None = None,
    subsection: str | None = None,
) -> str:
    """Update an existing document.

    Args:
        document_id: UUID of the document to update
        title: New title (optional)
        content: New markdown content (optional)
        type: New document type (optional)
        section: New section, e.g. "technical", "conceptual" (optional)
        subsection: New subsection, e.g. "backend", "frontend" (optional)

    Only provided fields are updated; omitted fields are unchanged.
    """
    client = _get_client()
    try:
        data = await client.update_document(
            document_id=document_id,
            title=title,
            content=content,
            type=type,
            section=section,
            subsection=subsection,
        )
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def create_work_item(
    ctx: Context,
    title: str,
    description: str | None = None,
    type: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
) -> str:
    """Create a new work item (task, feature request, bug report).

    Args:
        title: Work item title
        description: Detailed description (optional)
        type: Type — one of: feature, fix, refactor, investigation, bug, task, question
        priority: Priority level 1-4 (1=low, 2=medium, 3=high, 4=critical)
        tags: List of tags (optional)

    Returns the created work item with its ID and status.
    """
    client = _get_client()
    try:
        data = await client.create_work_item(
            title=title, description=description, type=type, priority=priority, tags=tags
        )
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def update_work_item(
    ctx: Context,
    work_item_id: str,
    title: str | None = None,
    description: str | None = None,
    type: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
) -> str:
    """Update an existing work item.

    Args:
        work_item_id: UUID of the work item to update
        title: New title (optional)
        description: New description (optional)
        type: New type (optional)
        status: New status — e.g. reported, in_progress, completed (optional)
        priority: New priority 1-4 (optional)
        tags: New tags list (optional)

    Only provided fields are updated; omitted fields are unchanged.
    """
    client = _get_client()
    try:
        data = await client.update_work_item(
            work_item_id=work_item_id,
            title=title,
            description=description,
            type=type,
            status=status,
            priority=priority,
            tags=tags,
        )
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


# ---------------------------------------------------------------------------
# Tools — Admin
# ---------------------------------------------------------------------------


@mcp.tool()
async def generate_docs(ctx: Context, mode: str = "full") -> str:
    """Trigger AI documentation generation for the product.

    Args:
        mode: Generation mode — "full" (regenerate all from scratch) or
              "additive" (only add new docs, preserve existing). Default: "full".

    Starts a background task. Use get_docs_generation_status to poll progress.
    Requires mcp:admin scope on the API key.
    """
    client = _get_client()
    try:
        data = await client.generate_docs(mode=mode)
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def get_docs_generation_status(ctx: Context) -> str:
    """Get current documentation generation status.

    Returns the status (idle, generating, completed, failed), progress details,
    any error message, and the timestamp of the last successful generation.
    Use this to poll after calling generate_docs.
    """
    client = _get_client()
    try:
        data = await client.get_docs_status()
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def get_codebase_context(ctx: Context) -> str:
    """Get the deep codebase analysis for the product.

    Returns the AI-generated product overview including tech stack, architecture,
    API endpoints, database models, services, and frontend pages. This is the
    same data that powers documentation generation.

    Returns null if analysis hasn't been run yet — trigger it from the Trajan UI.
    """
    client = _get_client()
    try:
        data = await client.get_codebase_context()
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


@mcp.tool()
async def sync_docs_to_repo(
    ctx: Context,
    document_ids: list[str] | None = None,
    message: str = "Sync documentation from Trajan (via MCP)",
) -> str:
    """Push documents to the linked GitHub repository.

    Args:
        document_ids: List of document UUIDs to sync (optional — if omitted,
                      syncs all documents with local changes)
        message: Git commit message (default: "Sync documentation from Trajan (via MCP)")

    Uses the repository's sync configuration (branch, path prefix, PR mode).
    Sync must be enabled on the repository first. Requires mcp:admin scope.
    """
    client = _get_client()
    try:
        data = await client.sync_docs(document_ids=document_ids, message=message)
    except httpx.HTTPStatusError as exc:
        return _error_message(exc)
    return _fmt_json(data)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server over stdio."""
    import asyncio

    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
