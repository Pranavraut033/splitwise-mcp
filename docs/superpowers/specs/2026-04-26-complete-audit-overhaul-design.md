# Splitwise MCP Server — Complete Audit Overhaul

**Date:** 2026-04-26
**Branch:** `fix/complete-audit-overhaul`

## Problem

The MCP server has critical correctness bugs, missing API coverage, and design issues identified during a full audit against the official Splitwise API documentation.

## Phase 1 — Critical Bug Fixes

### 1.1 Response validation for write operations

**Problem:** Splitwise returns 200 OK for failed operations. Success is determined by checking `errors` (empty = success) or `success` (true = success) in the response body. The server currently treats any 2xx as success.

**Fix:** Add `_validate_write_response(response_data, endpoint)` in `client.py`:
- For create/update endpoints: raise if `response_data.get("errors")` is non-empty
- For delete endpoints: raise if `response_data.get("success")` is not `True`
- Apply to: `create_expense`, `update_expense`, `delete_expense`, `create_group`, `delete_group`, `add_user_to_group`, `remove_user_from_group`, `create_comment`, `delete_comment`

### 1.2 Fix user split validation

**Problem:** `validate_user_split()` requires `user_id` in every split dict. The API accepts either `user_id` OR `email` + `first_name` + `last_name`.

**Fix:** Change validation to accept either identification method.

### 1.3 Fix `split_equally` conflict

**Problem:** Default `split_equally=True` is sent even when custom `users` splits are provided.

**Fix:** In `create_expense`, if `users` is provided with shares, force `split_equally=False`.

## Phase 2 — Moderate Fixes

### 2.1 Deprecation fix
Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`.

### 2.2 Missing expense fields
Add to `create_expense`: `details` (str, optional), `repeat_interval` (enum, optional).
Add to `update_expense`: `currency_code`, `group_id`, `details`, `repeat_interval`.

### 2.3 Dead code removal
Remove unused `put()` and `delete()` HTTP methods from `client.py`.

### 2.4 Fix f-string without interpolation
Remove pointless `f` prefix on static strings in `client.py`.

### 2.5 Wire config threshold
Pass `config.default_match_threshold` through to resolver tools as default.

### 2.6 Remove redundant Content-Type header
Let httpx manage `Content-Type` when using `json=` parameter. Only set `Accept` header explicitly.

## Phase 3 — Missing API Coverage

### 3.1 `create-friend` tool
- Endpoint: `POST /create_friend`
- Params: `user_email` (str, required), `user_first_name` (str, optional), `user_last_name` (str, optional)
- Clears resolver friend cache after success

### 3.2 `delete-friend` tool
- Endpoint: `POST /delete_friend/{id}`
- Params: `friend_id` (int, required)
- Clears resolver friend cache after success

### 3.3 `get-notifications` tool
- Endpoint: `GET /get_notifications`
- Returns list of notifications for the current user

### 3.4 `restore-expense` tool
- Endpoint: `POST /restore_expense/{id}`
- Params: `expense_id` (int, required)
- Safety net for accidental deletions

## Phase 4 — Design Improvements

### 4.1 Remove arithmetic tools
Remove all 5 arithmetic tools (`add`, `subtract`, `multiply`, `divide`, `modulo`). LLMs handle basic math natively. These consume 18% of tool surface area and add noise.

### 4.2 Trim docstrings
Reduce tool docstrings to 3-5 lines focused on: what it does, key constraints, non-obvious behavior. Remove verbose Args/Returns/Raises sections — FastMCP sends these to the LLM as tool descriptions.

### 4.3 Add retry for transient failures
Add 1 retry with 2s delay for 5xx and `httpx.RequestError` only. No retry for 4xx.

## Files Modified

| File | Changes |
|---|---|
| `client.py` | Response validation, retry logic, remove dead code, fix headers, fix f-strings, add new endpoints |
| `server.py` | Fix split_equally, add missing params, add new tools, remove arithmetic tools, trim docstrings, wire config threshold |
| `errors.py` | Fix validate_user_split to accept email+name |
| `config.py` | No changes needed (threshold already loaded) |

## Out of Scope

- `restore_group` — rarely needed
- `update_user` — rarely needed
- `create_friends` (batch) — rarely needed
- Form encoding change — current JSON approach works
- OAuth token refresh — separate concern
