# Async API Calls Implementation Plan

## Overview

This document outlines the plan to make Rally API calls asynchronous using httpx, improving UI responsiveness in the Textual-based TUI application.

## Current State Analysis

### Architecture
- **RallyClient** (`services/rally_client.py`) - Uses `pyral` library for sync API calls
- **CachingRallyClient** (`services/caching_client.py`) - Wraps RallyClient with caching
- **MockRallyClient** (`services/mock_client.py`) - In-memory mock for testing
- **RallyClientProtocol** (`services/protocol.py`) - Protocol defining the interface

### Problem
The pyral library is **synchronous**, blocking the Textual event loop during API calls:
- `get_tickets()` - Fetches 3 entity types sequentially (slowest operation)
- `get_discussions()` - Fetches ConversationPosts
- `get_iterations()` - Fetches Iteration entities
- `get_attachments()` - Fetches Attachment metadata
- `bulk_*` operations - Sequential loops over multiple tickets
- `download_embedded_image()` - Uses `requests` (sync HTTP)

### Impact
- UI freezes during API calls
- Loading spinner cannot animate while fetching
- Poor user experience on slow networks

## Proposed Solution

### Approach: Replace pyral with httpx for async HTTP

Instead of wrapping sync calls in `run_in_executor`, we'll create a native async client using httpx to make direct Rally REST API calls. This provides:
- True async/await support
- Connection pooling
- HTTP/2 support
- Better error handling
- Concurrent requests for `get_tickets()` (fetch all entity types in parallel)

### Key Components

1. **AsyncRallyClient** - New async client using httpx
2. **AsyncRallyClientProtocol** - Protocol with async method signatures
3. **Updated CachingRallyClient** - Support async operations
4. **Updated MockRallyClient** - Async-compatible mock
5. **App integration** - Use `await` for API calls

## Implementation Plan

### Phase 1: Add httpx and Create Base Infrastructure

**Step 1.1: Add httpx dependency**
```toml
# pyproject.toml
dependencies = [
    ...
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    ...
    "pytest-asyncio>=0.23.0",  # For async test support
]
```

**Step 1.2: Create Rally REST API helper module**

Create `services/rally_api.py` with Rally WSAPI constants and helpers:
- Base URL construction
- Query string building
- Response parsing
- Error handling

```python
# services/rally_api.py
RALLY_WSAPI_VERSION = "v2.0"
ENTITY_TYPES = {
    "HierarchicalRequirement": "hierarchicalrequirement",
    "Defect": "defect",
    "Task": "task",
    "Iteration": "iteration",
    "ConversationPost": "conversationpost",
    "Attachment": "attachment",
    "User": "user",
    "PortfolioItem/Feature": "portfolioitem/feature",
}
```

### Phase 2: Create AsyncRallyClient

**Step 2.1: Create async protocol**

```python
# services/async_protocol.py
class AsyncRallyClientProtocol(Protocol):
    async def get_tickets(self, query: str | None = None) -> list[Ticket]: ...
    async def get_ticket(self, formatted_id: str) -> Ticket | None: ...
    async def get_discussions(self, ticket: Ticket) -> list[Discussion]: ...
    async def add_comment(self, ticket: Ticket, text: str) -> Discussion | None: ...
    # ... etc
```

**Step 2.2: Implement AsyncRallyClient**

Create `services/async_rally_client.py`:

```python
class AsyncRallyClient:
    def __init__(self, config: RallyConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=f"https://{config.server}/slm/webservice/{RALLY_WSAPI_VERSION}",
            headers={"ZSESSIONID": config.apikey},
            timeout=30.0,
        )

    async def __aenter__(self) -> "AsyncRallyClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit - close httpx client."""
        await self.close()

    async def close(self) -> None:
        """Close the httpx client and release resources."""
        await self._client.aclose()

    async def get_tickets(self, query: str | None = None) -> list[Ticket]:
        """Fetch tickets concurrently from multiple entity types."""
        entity_types = ["HierarchicalRequirement", "Defect", "Task"]

        # Concurrent requests for all entity types
        tasks = [
            self._fetch_entity_type(entity_type, query)
            for entity_type in entity_types
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        tickets = []
        for result in results:
            if isinstance(result, list):
                tickets.extend(result)
        return tickets
```

**Step 2.3: Error handling and retry logic**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class AsyncRallyClient:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> dict:
        """Make HTTP request with retry logic."""
        response = await self._client.request(method, url, **kwargs)
        response.raise_for_status()
        data = response.json()

        # Check for Rally API errors
        if "OperationResult" in data:
            errors = data["OperationResult"].get("Errors", [])
            if errors:
                raise RallyAPIError(errors[0])

        return data
```

**Key methods to implement:**
| Method | Rally Endpoint | Notes |
|--------|----------------|-------|
| `get_tickets()` | `GET /hierarchicalrequirement`, etc. | Concurrent requests |
| `get_ticket()` | `GET /{entity}/{id}` | Single fetch |
| `get_discussions()` | `GET /conversationpost` | Filter by artifact |
| `add_comment()` | `POST /conversationpost` | Create operation |
| `update_points()` | `POST /{entity}` | Update operation |
| `update_state()` | `POST /{entity}` | Update operation |
| `create_ticket()` | `POST /{entity}` | Create operation |
| `get_iterations()` | `GET /iteration` | Two queries (current + past) |
| `get_feature()` | `GET /portfolioitem/feature` | Single fetch |
| `set_parent()` | `POST /{entity}` | Update operation |
| `get_attachments()` | `GET /attachment` | Filter by artifact |
| `download_attachment()` | `GET /attachment/{id}/content` | Binary download |
| `upload_attachment()` | `POST /attachment` + `POST /attachmentcontent` | Multi-step |
| `download_embedded_image()` | `GET {url}` | Direct HTTP GET |

### Phase 3: Bulk Operations Optimization

**Step 3.1: Implement concurrent bulk operations**

```python
async def bulk_update_state(self, tickets: list[Ticket], state: str) -> BulkResult:
    """Update state on multiple tickets concurrently."""
    semaphore = asyncio.Semaphore(5)  # Limit concurrent requests

    async def update_one(ticket: Ticket) -> Ticket | Exception:
        async with semaphore:
            try:
                return await self.update_state(ticket, state)
            except Exception as e:
                return e

    results = await asyncio.gather(*[update_one(t) for t in tickets])
    # Process results into BulkResult...
```

**Benefits:**
- 5x faster bulk operations (concurrent vs sequential)
- Respects Rally's 12 concurrent request limit via semaphore
- Better error isolation

### Phase 4: Update CachingRallyClient

**Step 4.1: Create AsyncCachingRallyClient**

```python
# services/async_caching_client.py
class AsyncCachingRallyClient:
    def __init__(
        self,
        client: AsyncRallyClientProtocol,
        cache_manager: CacheManager,
        ...
    ) -> None:
        self._client = client
        ...

    async def get_tickets(self, query: str | None = None) -> list[Ticket]:
        # Cache logic remains similar, but async
        ...
```

### Phase 5: Update MockRallyClient

**Step 5.1: Add async methods to MockRallyClient**

```python
class MockRallyClient:
    # Keep sync methods for backward compatibility
    def get_tickets(self, query: str | None = None) -> list[Ticket]: ...

    # Add async versions
    async def get_tickets_async(self, query: str | None = None) -> list[Ticket]:
        return self.get_tickets(query)
```

Or create `AsyncMockRallyClient` that wraps the sync mock.

### Phase 6: Update App Integration

**Step 6.1: Modify app.py to use async client**

```python
# app.py
async def _load_tickets(self) -> None:
    """Load tickets asynchronously."""
    try:
        self._set_loading(True)
        tickets = await self._client.get_tickets()
        ticket_list = self.query_one(TicketList)
        ticket_list.set_tickets(tickets)
    finally:
        self._set_loading(False)

def action_refresh_cache(self) -> None:
    """Trigger async refresh."""
    self.run_worker(self._load_tickets())
```

**Step 6.2: Use Textual's `run_worker` for background tasks**

Textual provides `run_worker()` for running async tasks without blocking:
```python
self.run_worker(self._load_tickets(), exclusive=True)
```

**Step 6.3: App lifecycle management**

```python
class RallyTUI(App):
    def __init__(self, ...) -> None:
        ...
        self._async_client: AsyncRallyClient | None = None

    async def on_mount(self) -> None:
        """Initialize async client when app mounts."""
        if self._connected:
            self._async_client = AsyncRallyClient(self._config)

    async def on_unmount(self) -> None:
        """Clean up async client when app unmounts."""
        if self._async_client:
            await self._async_client.close()
```

### Phase 7: Testing

**Step 7.1: Create async test fixtures**

```python
# conftest.py
@pytest.fixture
async def async_client():
    return AsyncMockRallyClient()
```

**Step 7.2: Add async tests**

```python
# test_async_rally_client.py
@pytest.mark.asyncio
async def test_get_tickets_concurrent():
    client = AsyncRallyClient(config)
    tickets = await client.get_tickets()
    assert len(tickets) > 0
```

**Step 7.3: Test coverage targets**
- Unit tests for each async method
- Integration tests for concurrent operations
- Error handling tests (network failures, API errors)
- Cache integration tests

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `pyproject.toml` | Modify | Add httpx dependency |
| `services/rally_api.py` | New | Rally REST API helpers |
| `services/async_protocol.py` | New | Async protocol definition |
| `services/async_rally_client.py` | New | Main async client |
| `services/async_caching_client.py` | New | Async caching wrapper |
| `services/mock_client.py` | Modify | Add async support |
| `app.py` | Modify | Use async client with workers |
| `tests/conftest.py` | Modify | Add async fixtures |
| `tests/test_async_rally_client.py` | New | Async client tests |
| `tests/test_async_caching_client.py` | New | Async caching tests |

## Migration Strategy

1. **Phase 1-2**: Implement async client alongside sync client
2. **Phase 3-4**: Optimize bulk operations and caching
3. **Phase 5**: Update mock for testing
4. **Phase 6**: Switch app to use async client
5. **Phase 7**: Comprehensive testing

**Backward Compatibility:**
- Keep sync `RallyClient` for any non-async use cases
- Keep sync `RallyClientProtocol` for type checking
- Gradual migration path

## Rally WSAPI Reference

### Authentication
```
Header: ZSESSIONID: {api_key}
```

### Base URL
```
https://{server}/slm/webservice/v2.0/{entity}
```

### Query Parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `query` | Filter condition | `(State = "Open")` |
| `fetch` | Fields to return | `FormattedID,Name,State` |
| `pagesize` | Results per page | `200` (max 2000) |
| `start` | Pagination offset | `1` (1-based) |
| `order` | Sort order | `CreationDate desc` |

### Rate Limits
- 12 concurrent requests per user
- No daily limit

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rally API changes | High | Use API version in URL, add response validation |
| Rate limiting | Medium | Semaphore limiting concurrent requests |
| Network errors | Medium | Retry logic with exponential backoff |
| Data format changes | Low | Defensive parsing with fallbacks |

## Success Metrics

1. **UI Responsiveness**: Loading spinner animates during fetches
2. **Performance**: `get_tickets()` completes 3x faster (concurrent entity fetches)
3. **Bulk Operations**: 5x faster with concurrent updates
4. **Test Coverage**: 90%+ coverage on new async code
5. **No Regressions**: All existing tests pass

## Implementation Status

### Completed
- [x] Phase 1: Add httpx and tenacity dependencies
- [x] Phase 1: Create `rally_api.py` with constants and helpers
- [x] Phase 2: Create `AsyncRallyClient` with all methods
- [x] Phase 3: Implement concurrent bulk operations
- [x] Phase 4: Create `AsyncCachingRallyClient`
- [x] Phase 5: Create `AsyncMockRallyClient`
- [x] Phase 7: Add tests for rally_api and async_mock_client (56 tests)

### Pending
- [ ] Phase 6: App integration (switch app.py to use async client)
- [ ] Full integration testing with real Rally API

## Timeline Estimate

| Phase | Complexity | Dependencies |
|-------|------------|--------------|
| Phase 1 | Low | None |
| Phase 2 | High | Phase 1 |
| Phase 3 | Medium | Phase 2 |
| Phase 4 | Medium | Phase 2 |
| Phase 5 | Low | Phase 2 |
| Phase 6 | Medium | Phases 2-5 |
| Phase 7 | Medium | Phases 2-6 |

## Appendix: Rally WSAPI Endpoints

### Read Operations (GET)
```
GET /slm/webservice/v2.0/hierarchicalrequirement?query=...&fetch=...
GET /slm/webservice/v2.0/defect?query=...&fetch=...
GET /slm/webservice/v2.0/task?query=...&fetch=...
GET /slm/webservice/v2.0/iteration?query=...&fetch=...
GET /slm/webservice/v2.0/conversationpost?query=...&fetch=...
GET /slm/webservice/v2.0/attachment?query=...&fetch=...
GET /slm/webservice/v2.0/portfolioitem/feature?query=...&fetch=...
GET /slm/webservice/v2.0/user?query=...&fetch=...
```

### Write Operations (POST)
```
POST /slm/webservice/v2.0/{entity}/create
POST /slm/webservice/v2.0/{entity}/{objectId}  (update)
```

### Response Format
```json
{
  "QueryResult": {
    "Results": [...],
    "TotalResultCount": 42,
    "StartIndex": 1,
    "PageSize": 200
  }
}
```

### Error Response
```json
{
  "OperationResult": {
    "Errors": ["Error message"],
    "Warnings": []
  }
}
```
