# Authentication

## Creating a key

1. Sign in at [umlout.com](https://www.umlout.com).
2. Open **Profile → MCP API Keys**.
3. Create a key and copy it immediately — it is shown once and stored only as a hash, so it cannot
   be recovered afterwards. Lost a key? Revoke it and create a new one.

## Sending the key

Every request to `https://www.umlout.com/mcp/sse` must carry the key in one of two headers:

```http
Authorization: Bearer YOUR_API_KEY
```

```http
X-API-Key: YOUR_API_KEY
```

Use whichever your client supports; they are equivalent. Most MCP clients express this as a
`headers` object in the server config — see [../examples/](../examples/).

`GET /mcp/health` is the one unauthenticated endpoint. It returns `{"status": "ok"}` and is what
[check_connection.py](../scripts/check_connection.py) probes first.

## What a key can reach

A key is bound to the account that created it and carries that account's permissions — no more.
The assistant sees the diagrams and models you own plus those explicitly shared with you. Write
operations respect the same roles as the web app: editors can change a model's contents, but only
an owner can delete a model or rename and delete a diagram.

There is no organisation-wide or admin-scoped key. If two people should each drive their own
workspace, they each create their own key.

## Rate limits

| Scope | Limit | Window |
|---|---|---|
| Requests per account | 60 | 1 minute |
| Write tool calls per account | 600 | 1 hour |
| Bulk write calls (`bulk_*`) per account | 60 | 1 hour |
| Failed auth attempts per IP | 20 | 15 minutes |

Reads (`get_*`, `list_*`, `find_*`) count toward the request limit but not the write budgets.

The bulk budget is deliberately tighter than the write budget: a single `bulk_add_shapes` or
`bulk_create_model_items` call can write hundreds of items, so 60 of them per hour is a larger
allowance than it looks.

Exceeding a limit returns an error to the client; nothing is partially written.

## Rotating and revoking

Keys are listed in **Profile → MCP API Keys** and can be revoked individually. Revocation takes
effect immediately — any client still holding the key starts failing auth on its next request.

To rotate without downtime: create the new key, update your client config, restart the client,
then revoke the old key.

## Handling the key safely

Treat it like a password. It grants full read and write access to your workspace.

- Keep it out of committed files. Client configs that hold a live key belong in your machine's
  local config directory, not in a repository.
- Where your client supports environment-variable substitution, prefer that to a literal string.
- Revoke immediately if a key ends up somewhere public.
