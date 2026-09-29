# Authentication

## Creating a key

1. Sign in at [umlout.com](https://www.umlout.com).
2. Open **Profile → AI clients** and pick your client.
3. Create a key and copy it immediately — it is shown once and stored only as a hash, so it cannot
   be recovered afterwards. Lost a key? Revoke it and create a new one.

## Sending the key

Every request to `https://www.umlout.com/mcp/http` must carry the key in one of two headers:

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

## Signing in without a key (OAuth)

Some clients take only a server's address and have no field for a key: ChatGPT's connectors,
Grok's, and Claude's own **Settings → Connectors → Add custom connector**. For them, Umlout's MCP
server is an OAuth 2.1 protected resource:

1. Give the client `https://www.umlout.com/mcp/http`.
2. The client registers itself and opens an Umlout page in your browser. It shows the name the
   client gave itself, everything it will be able to do, and where you will be sent back.
3. Press **Allow**. The client receives a token and connects.

The permission appears in **Profile → AI clients** as a *Browser sign-in* and is removed with
**Disconnect**. It is not a key and does not count toward the five keys. A token opens exactly
what an MCP key opens — the MCP server, as you, with your permissions — and nothing on the REST
API.

Discovery: the `401` names `https://www.umlout.com/mcp/.well-known/oauth-protected-resource`, which
names the authorization server `https://www.umlout.com`, whose metadata is at
`/.well-known/oauth-authorization-server`. PKCE (S256) is required; clients are public.

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

Keys are listed in **Profile → AI clients** and can be revoked individually. Revocation takes
effect immediately — any client still holding the key starts failing auth on its next request.

To rotate without downtime: create the new key, update your client config, restart the client,
then revoke the old key.

## Handling the key safely

Treat it like a password. It grants full read and write access to your workspace.

- Keep it out of committed files. Client configs that hold a live key belong in your machine's
  local config directory, not in a repository.
- Where your client supports environment-variable substitution, prefer that to a literal string.
- Revoke immediately if a key ends up somewhere public.
