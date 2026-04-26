# Complete Audit Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix critical correctness bugs, add missing Splitwise API endpoints, and clean up design issues identified in the audit.

**Architecture:** Modify the existing 4 core files (`client.py`, `server.py`, `errors.py`, `config.py`) to fix bugs and add features. Add comprehensive test coverage. Remove arithmetic tools and dead code.

**Tech Stack:** Python 3.10+, FastMCP, httpx, rapidfuzz, pytest, pytest-asyncio

---

### Task 1: Add response validation for write operations in client.py

**Files:**
- Modify: `src/splitwise_mcp_server/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Create test file with response validation tests**

```python
"""Tests for SplitwiseClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from splitwise_mcp_server.client import SplitwiseClient
from splitwise_mcp_server.auth import OAuth2Handler


@pytest.fixture
def auth_handler():
    return OAuth2Handler(
        consumer_key="test_key",
        consumer_secret="test_secret",
        access_token="test_token",
    )


@pytest.fixture
def sw_client(auth_handler):
    return SplitwiseClient(auth_handler, cache_ttl=3600)


class TestValidateWriteResponse:
    def test_create_expense_with_errors_raises(self, sw_client):
        response_data = {
            "expenses": [],
            "errors": {"base": ["The shares don't add up to the total cost"]},
        }
        with pytest.raises(Exception, match="shares don't add up"):
            sw_client._validate_write_response(response_data)

    def test_create_expense_success_passes(self, sw_client):
        response_data = {
            "expenses": [{"id": 1, "cost": "25.00"}],
            "errors": {},
        }
        sw_client._validate_write_response(response_data)

    def test_delete_with_success_false_raises(self, sw_client):
        response_data = {"success": False}
        with pytest.raises(Exception, match="did not succeed"):
            sw_client._validate_write_response(response_data)

    def test_delete_with_success_true_passes(self, sw_client):
        response_data = {"success": True}
        sw_client._validate_write_response(response_data)

    def test_errors_as_list_raises(self, sw_client):
        response_data = {"errors": ["Invalid input"]}
        with pytest.raises(Exception, match="Invalid input"):
            sw_client._validate_write_response(response_data)

    def test_empty_errors_dict_passes(self, sw_client):
        response_data = {"errors": {}}
        sw_client._validate_write_response(response_data)

    def test_no_errors_key_passes(self, sw_client):
        response_data = {"id": 1, "cost": "25.00"}
        sw_client._validate_write_response(response_data)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/tarunnv/projects/tarunnv/splitwise-mcp && python -m pytest tests/test_client.py -v`
Expected: FAIL — `_validate_write_response` does not exist yet

- [ ] **Step 3: Implement `_validate_write_response` in client.py**

Add after `_log_response` method (~line 86):

```python
def _validate_write_response(self, data: Dict[str, Any]) -> None:
    """Check Splitwise write-operation response for logical errors.

    Splitwise returns 200 OK even for failed writes. Success is determined
    by the response body: 'errors' must be empty, 'success' must be True.
    """
    errors = data.get("errors")
    if errors:
        if isinstance(errors, dict) and errors:
            parts = []
            for key, value in errors.items():
                if isinstance(value, list):
                    parts.append(f"{key}: {', '.join(str(v) for v in value)}")
                else:
                    parts.append(f"{key}: {value}")
            raise Exception(f"Splitwise API error: {'; '.join(parts)}")
        elif isinstance(errors, list) and errors:
            raise Exception(f"Splitwise API error: {'; '.join(str(e) for e in errors)}")
        elif isinstance(errors, str) and errors:
            raise Exception(f"Splitwise API error: {errors}")

    if "success" in data and data["success"] is not True:
        raise Exception("Operation did not succeed. The resource may not exist or you may lack permission.")
```

Then apply it in the `post` method. After `return response.json()` on line 317, change to:

```python
result = response.json()
self._validate_write_response(result)
return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_client.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_client.py src/splitwise_mcp_server/client.py
git commit -m "fix: validate write-operation responses for logical errors

Splitwise returns 200 OK even when operations fail. Now checks
'errors' and 'success' fields in response body."
```

---

### Task 2: Fix user split validation to accept email+name

**Files:**
- Modify: `src/splitwise_mcp_server/errors.py`
- Create: `tests/test_errors.py`

- [ ] **Step 1: Create test file**

```python
"""Tests for validation functions."""

import pytest
from splitwise_mcp_server.errors import validate_user_split, ValidationError


class TestValidateUserSplit:
    def test_valid_with_user_id(self):
        users = [{"user_id": 123, "paid_share": "25.00", "owed_share": "12.50"}]
        validate_user_split(users)

    def test_valid_with_email_and_name(self):
        users = [
            {
                "email": "jane@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "paid_share": "0.00",
                "owed_share": "12.50",
            }
        ]
        validate_user_split(users)

    def test_invalid_no_identification(self):
        users = [{"paid_share": "25.00", "owed_share": "12.50"}]
        with pytest.raises(ValidationError, match="user_id.*or.*email"):
            validate_user_split(users)

    def test_invalid_email_without_name(self):
        users = [{"email": "jane@example.com", "paid_share": "0", "owed_share": "10"}]
        with pytest.raises(ValidationError, match="first_name.*last_name"):
            validate_user_split(users)

    def test_negative_share_raises(self):
        users = [{"user_id": 1, "paid_share": "-5.00", "owed_share": "10.00"}]
        with pytest.raises(ValidationError, match="non-negative"):
            validate_user_split(users)

    def test_empty_list_raises(self):
        with pytest.raises(ValidationError):
            validate_user_split([])
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_errors.py -v`
Expected: `test_valid_with_email_and_name` and `test_invalid_no_identification` FAIL

- [ ] **Step 3: Fix validate_user_split in errors.py**

Replace the `user_id` check block (lines 272-277) with:

```python
has_user_id = "user_id" in user
has_email_ident = all(k in user for k in ("email", "first_name", "last_name"))

if not has_user_id and not has_email_ident:
    raise ValidationError(
        f"users[{i}] must include user_id or (email, first_name, and last_name)",
        field="users",
        details={"validation": "required_field", "index": i},
    )

if "email" in user and not has_email_ident:
    raise ValidationError(
        f"users[{i}] with email must also include first_name and last_name",
        field="users",
        details={"validation": "required_field", "index": i},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_errors.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/splitwise_mcp_server/errors.py tests/test_errors.py
git commit -m "fix: accept email+name as alternative to user_id in splits

Splitwise API allows identifying users by email+first_name+last_name
instead of user_id."
```

---

### Task 3: Fix split_equally conflict and datetime deprecation

**Files:**
- Modify: `src/splitwise_mcp_server/server.py`

- [ ] **Step 1: Fix split_equally auto-detection in create_expense**

In `create_expense` in server.py, replace the expense_data construction (lines 282-288):

```python
expense_data = {
    "cost": cost,
    "description": description,
    "currency_code": currency_code,
    "group_id": group_id,
}

if users:
    expense_data["split_equally"] = False
    expense_data["users"] = users
elif split_equally:
    expense_data["split_equally"] = True
```

- [ ] **Step 2: Fix datetime deprecation**

Replace line 294:
```python
expense_data["date"] = datetime.utcnow().isoformat() + "Z"
```
With:
```python
from datetime import timezone
expense_data["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

Also add `timezone` to the import at top of file (line 6):
```python
from datetime import datetime, timezone
```

- [ ] **Step 3: Run existing tests to verify no regressions**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/splitwise_mcp_server/server.py
git commit -m "fix: auto-detect split_equally and replace deprecated utcnow

When custom user splits are provided, split_equally is now set to False
automatically. Replaced datetime.utcnow() with datetime.now(timezone.utc)."
```

---

### Task 4: Add missing expense fields and update_expense params

**Files:**
- Modify: `src/splitwise_mcp_server/server.py`

- [ ] **Step 1: Add details and repeat_interval to create_expense**

Add parameters to `create_expense` signature:
```python
async def create_expense(
    cost: str,
    description: str,
    group_id: int = 0,
    currency_code: str = "USD",
    date: Optional[str] = None,
    category_id: Optional[int] = None,
    details: Optional[str] = None,
    repeat_interval: Optional[str] = None,
    users: Optional[List[Dict[str, Any]]] = None,
    split_equally: bool = True
) -> Dict[str, Any]:
```

Add validation after category_id validation:
```python
if repeat_interval is not None:
    valid_intervals = ["never", "weekly", "fortnightly", "monthly", "yearly"]
    validate_choice(repeat_interval, "repeat_interval", valid_intervals)
```

Add to expense_data construction:
```python
if details is not None:
    expense_data["details"] = details
if repeat_interval is not None:
    expense_data["repeat_interval"] = repeat_interval
```

- [ ] **Step 2: Add missing params to update_expense**

Update signature:
```python
async def update_expense(
    expense_id: int,
    cost: Optional[str] = None,
    description: Optional[str] = None,
    date: Optional[str] = None,
    category_id: Optional[int] = None,
    currency_code: Optional[str] = None,
    group_id: Optional[int] = None,
    details: Optional[str] = None,
    repeat_interval: Optional[str] = None,
    users: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
```

Add validation for new fields (after existing validations):
```python
if currency_code is not None:
    validate_currency_code(currency_code)
if group_id is not None and group_id < 0:
    raise ValidationError("group_id must be non-negative", field="group_id")
if repeat_interval is not None:
    valid_intervals = ["never", "weekly", "fortnightly", "monthly", "yearly"]
    validate_choice(repeat_interval, "repeat_interval", valid_intervals)
```

Add to expense_data dict building:
```python
if currency_code is not None:
    expense_data["currency_code"] = currency_code
if group_id is not None:
    expense_data["group_id"] = group_id
if details is not None:
    expense_data["details"] = details
if repeat_interval is not None:
    expense_data["repeat_interval"] = repeat_interval
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/splitwise_mcp_server/server.py
git commit -m "feat: add details, repeat_interval, currency_code, group_id params

create_expense now supports notes and recurring schedules.
update_expense now supports changing currency, group, notes, recurrence."
```

---

### Task 5: Clean up client.py — dead code, headers, f-strings, retry logic

**Files:**
- Modify: `src/splitwise_mcp_server/client.py`
- Modify: `tests/test_client.py`

- [ ] **Step 1: Add retry test to test_client.py**

```python
class TestRetryLogic:
    @pytest.mark.asyncio
    async def test_retries_on_500(self, sw_client):
        """Verify the client retries once on server errors."""
        import httpx

        call_count = 0
        original_send = sw_client.client.send

        async def mock_send(request, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(500, json={"error": "Internal Server Error"})
            return httpx.Response(200, json={"user": {"id": 1}})

        sw_client.client.send = mock_send
        result = await sw_client.get("/get_current_user")
        assert result == {"user": {"id": 1}}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_400(self, sw_client):
        """Verify 4xx errors are NOT retried."""
        import httpx

        call_count = 0
        original_send = sw_client.client.send

        async def mock_send(request, **kwargs):
            nonlocal call_count
            call_count += 1
            return httpx.Response(400, json={"errors": {"base": ["bad request"]}})

        sw_client.client.send = mock_send
        with pytest.raises(Exception):
            await sw_client.get("/get_current_user")
        assert call_count == 1
```

- [ ] **Step 2: Remove dead `put()` and `delete()` methods from client.py**

Delete the `put()` method (lines 325-363) and `delete()` method (lines 365-401).

- [ ] **Step 3: Fix Content-Type header**

Replace `_get_headers` method:
```python
def _get_headers(self) -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    headers.update(self.auth_handler.get_auth_headers())
    return headers
```

- [ ] **Step 4: Fix f-strings without interpolation**

In `add_user_to_group`: change `f"/add_user_to_group"` to `"/add_user_to_group"`
In `remove_user_from_group`: change `f"/remove_user_from_group"` to `"/remove_user_from_group"`

- [ ] **Step 5: Add retry logic to `get()` and `post()` methods**

Add at top of client.py:
```python
import asyncio

RETRYABLE_STATUS_CODES = {500, 502, 503}
MAX_RETRIES = 1
RETRY_DELAY = 2.0
```

Wrap the request in both `get()` and `post()` with retry:
```python
async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{self.BASE_URL}{endpoint}"
    headers = self._get_headers()
    self._log_request("GET", url, params)

    last_exception = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await self.client.get(url, headers=headers, params=params)
            self._log_response(response)

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                logger.warning(f"Retryable error {response.status_code}, retrying in {RETRY_DELAY}s...")
                await asyncio.sleep(RETRY_DELAY)
                continue

            if response.status_code >= 400:
                error = self.handle_api_error(response)
                raise Exception(f"{error.message} (Status: {error.status_code})")

            return response.json()
        except RateLimitError:
            raise
        except httpx.RequestError as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"Network error, retrying in {RETRY_DELAY}s: {e}")
                await asyncio.sleep(RETRY_DELAY)
                last_exception = e
                continue
            raise Exception(f"Network error: Could not connect to Splitwise API.\nDetails: {e}")

    raise last_exception or Exception("Request failed after retries")
```

Same pattern for `post()`, but keeping `_validate_write_response` call.

- [ ] **Step 6: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add src/splitwise_mcp_server/client.py tests/test_client.py
git commit -m "refactor: clean up client — retry logic, remove dead code, fix headers

Add 1-retry with 2s backoff for 5xx/network errors.
Remove unused put() and delete() methods.
Remove redundant Content-Type header.
Fix f-strings without interpolation."
```

---

### Task 6: Add missing API endpoints (create_friend, delete_friend, get_notifications, restore_expense)

**Files:**
- Modify: `src/splitwise_mcp_server/client.py`
- Modify: `src/splitwise_mcp_server/server.py`

- [ ] **Step 1: Add client methods**

Add to client.py after the friend endpoints section:

```python
async def create_friend(self, user_email: str, user_first_name: str = "", user_last_name: str = "") -> Dict[str, Any]:
    data = {"user_email": user_email}
    if user_first_name:
        data["user_first_name"] = user_first_name
    if user_last_name:
        data["user_last_name"] = user_last_name
    return await self.post("/create_friend", data=data)

async def delete_friend(self, friend_id: int) -> Dict[str, Any]:
    return await self.post(f"/delete_friend/{friend_id}")

async def get_notifications(self) -> Dict[str, Any]:
    return await self.get("/get_notifications")

async def restore_expense(self, expense_id: int) -> Dict[str, Any]:
    return await self.post(f"/restore_expense/{expense_id}")
```

- [ ] **Step 2: Add server tools — register_friend_tools additions**

In `register_friend_tools`, add after `get_friend`:

```python
@mcp.tool()
async def create_friend(user_email: str, user_first_name: str = "", user_last_name: str = "") -> Dict[str, Any]:
    """Add a friend by email. Optionally provide their name."""
    try:
        validate_required(user_email, "user_email")
        validate_email(user_email)
        result = await client.create_friend(user_email, user_first_name, user_last_name)
        resolver.clear_cache()
        return result
    except (ValidationError, RateLimitError):
        raise
    except Exception as e:
        logger.error(f"Error creating friend: {e}")
        raise

@mcp.tool()
async def delete_friend(friend_id: int) -> Dict[str, Any]:
    """Remove a friendship. Does not affect shared expenses."""
    try:
        result = await client.delete_friend(friend_id)
        resolver.clear_cache()
        return result
    except Exception as e:
        logger.error(f"Error deleting friend {friend_id}: {e}")
        raise
```

- [ ] **Step 3: Add notification tool — new register_notification_tools function**

```python
def register_notification_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_notifications() -> Dict[str, Any]:
        """Get recent notifications for the current user (new expenses, payments, comments)."""
        try:
            result = await client.get_notifications()
            return result
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            raise
```

Register in `create_server()`:
```python
register_notification_tools(mcp)
```

- [ ] **Step 4: Add restore_expense to expense tools**

In `register_expense_tools`, add after `delete_expense`:

```python
@mcp.tool()
async def restore_expense(expense_id: int) -> Dict[str, Any]:
    """Restore a previously deleted expense."""
    try:
        result = await client.restore_expense(expense_id)
        return result
    except Exception as e:
        logger.error(f"Error restoring expense {expense_id}: {e}")
        raise
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/splitwise_mcp_server/client.py src/splitwise_mcp_server/server.py
git commit -m "feat: add create_friend, delete_friend, get_notifications, restore_expense

Covers previously missing Splitwise API endpoints for core UX scenarios."
```

---

### Task 7: Remove arithmetic tools and trim docstrings

**Files:**
- Modify: `src/splitwise_mcp_server/server.py`

- [ ] **Step 1: Remove register_arithmetic_tools function and its call**

Delete the entire `register_arithmetic_tools` function (lines 1173-1383).
Remove `register_arithmetic_tools(mcp)` from `create_server()`.

- [ ] **Step 2: Trim all tool docstrings**

Replace verbose multi-section docstrings with 2-5 line focused descriptions. Example:

Before (get_current_user):
```python
"""Get information about the currently authenticated user.

Returns detailed profile information for the authenticated user including
their ID, name, email, registration status, and profile picture.

Returns:
    Dictionary containing user profile information:
    - id: User ID
    ...
Raises:
    Exception: ...
"""
```

After:
```python
"""Get the current authenticated user's profile (id, name, email, picture)."""
```

Apply this trimming pattern to ALL tools.

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/splitwise_mcp_server/server.py
git commit -m "refactor: remove arithmetic tools, trim docstrings

Arithmetic tools added noise to tool discovery. LLMs handle basic math.
Shorter docstrings reduce token overhead in tool descriptions sent to LLM."
```

---

### Task 8: Wire config default_match_threshold

**Files:**
- Modify: `src/splitwise_mcp_server/server.py`

- [ ] **Step 1: Store config reference and use threshold**

In lifespan, after creating resolver, store config:
```python
server._splitwise_config = config
```

Actually, simpler: just store threshold on the resolver:
```python
resolver = EntityResolver(client)
resolver.default_threshold = config.default_match_threshold
```

Then in each resolve tool, change default:
```python
async def resolve_friend(query: str, threshold: Optional[int] = None) -> List[Dict[str, Any]]:
    ...
    effective_threshold = threshold if threshold is not None else resolver.default_threshold
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest tests/ -v`

- [ ] **Step 3: Commit**

```bash
git add src/splitwise_mcp_server/server.py
git commit -m "fix: wire config default_match_threshold to resolver tools"
```

---

### Task 9: Final validation

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`

- [ ] **Step 2: Verify the server starts**

Run: `cd /Users/tarunnv/projects/tarunnv/splitwise-mcp && timeout 5 python -c "from splitwise_mcp_server.server import create_server; print('Server creation OK')" 2>&1 || true`

- [ ] **Step 3: Verify tool count**

Run: `python -c "
from splitwise_mcp_server.server import create_server
s = create_server()
print(f'Tools registered: {len(s._tool_manager._tools)}')
for name in sorted(s._tool_manager._tools.keys()):
    print(f'  - {name}')
"`

Expected: ~27 tools (28 original - 5 arithmetic + 4 new endpoints)
