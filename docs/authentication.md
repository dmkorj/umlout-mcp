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
The assistant sees the projects you own plus those shared with you, and every board, object,
relation, type and file inside them.

Permission is set on the **project**, never on a board or an object, and the roles are the web
app's (**Project → Access**):

| role | what the assistant may do in the project |
|---|---|
| owner | everything, including `delete_project` |
| editor | create, change, delete and restore boards, objects, relations, types, fields, figures and files; rename and delete boards; make the project public; resolve any comment and delete any comment |
| commenter | read everything; list and add comments; delete their own comments |
| viewer | read everything except comments |

A tool marked **Editors only** in [tools.md](tools.md) refuses a commenter and a viewer. A deleted board,
object, relation, declared type, shared field or file is kept: `list_deleted` shows it and the
`restore_*` tools bring it back. Deleting a project or a comment cannot be undone.

There is no organisation-wide or admin-scoped key. If two people should each drive their own
workspace, they each create their own key. An account may hold up to five active keys.

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

| Scope | Limit | Window | What counts |
|---|---|---|---|
| Tool calls per account | 300 | 1 minute | every tool call and resource read, except `get_rate_limit_status` |
| Write tool calls per account | 600 | 1 hour | every tool whose name does not start with `get_`, `list_` or `find_` |
| Bulk write calls per account | 600 | 1 hour | every `bulk_*` tool — **in addition to** the write budget |
| HTTP requests per account | 600 | 1 minute | every request to the server, before any tool runs |
| Failed auth attempts per IP | 20 | 15 minutes | requests with a missing, revoked or mistyped key |

A `bulk_*` call costs one write and one bulk write, however many items it carries, so batching is
always the cheaper way to write many items. Reads cost a tool call and nothing else, so a client
that only reads never uses up the write budgets.

A tool call over its budget is refused before anything is written. The refusal comes back as the
tool's error result, and its text is a JSON object the client can act on:

```json
{"error":"rate_limited","scope":"mcp:tool-write","retry_after":412,"limit":600,"window_seconds":3600}
```

`retry_after` is the number of seconds until the call would succeed. `get_rate_limit_status`
reports what is left of every budget and costs nothing. Only the HTTP request limit answers with
HTTP `429` instead; it is set well above the tool-call limit, so a client that respects
`retry_after` does not reach it.

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
