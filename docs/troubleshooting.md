# Troubleshooting

Start here:

```bash
python3 scripts/check_connection.py --api-key YOUR_API_KEY
```

It separates the three failures that look identical from inside a chat client: the service being
down, the key being rejected, and the response stream being blocked on the way.

---

## The client shows no Umlout tools at all

The server never connected, and most clients fail quietly.

- **Restart fully.** Claude Desktop reloads MCP servers only on a real quit — closing the window is
  not enough.
- **Check the config file is the one the client actually reads.** Path typos here are the single
  most common cause. macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`.
  Windows: `%APPDATA%\Claude\claude_desktop_config.json`. Cursor: `~/.cursor/mcp.json`. VS Code:
  `.vscode/mcp.json` in the workspace.
- **Validate the JSON.** A trailing comma silently disables the whole file:
  `python3 -m json.tool < your_config.json`.
- **Remove the `_comment` field** if you copied a file from [../examples/](../examples/) into a
  client that rejects unknown keys.
- **Claude Desktop needs Node.js** for the `npx mcp-remote` bridge. Check with `node --version`; if
  the log says `Failed to spawn process`, see [that section below](#failed-to-spawn-process-no-such-file-or-directory).

## `Failed to spawn process: No such file or directory`

In the Claude Desktop log, a few milliseconds after startup:

```
[info] Using MCP server command: npx with path: { ... }
Failed to spawn process: No such file or directory
[info] Server transport closed unexpectedly
```

There is no `npx` on the PATH Claude Desktop uses. The log names the command but
not what is missing, which makes this look like a server problem when it is not.

Check in a terminal:

```bash
node --version
```

**If that says "command not found"**, Node.js is not installed. The `mcp-remote`
bridge runs through `npx`, so it cannot start. On macOS:

```bash
brew install node
```

Then **fully quit Claude Desktop** (⌘Q — closing the window is not enough) and reopen it.
Homebrew installs to `/opt/homebrew/bin`, which is already on Claude Desktop's PATH.

**If `node --version` works but Claude Desktop still cannot spawn it**, your Node
lives somewhere Claude Desktop does not look. This is the normal case for
[nvm](https://github.com/nvm-sh/nvm), which puts Node under `~/.nvm/versions/...`
and adds it to the PATH from your shell profile — a GUI app never reads that. The
PATH Claude Desktop actually uses is printed in the log line above; nvm's directory
will not be in it.

Find the real path and hardcode it:

```bash
which npx
```

```json
{
  "mcpServers": {
    "umlout": {
      "command": "/Users/you/.nvm/versions/node/v22.11.0/bin/npx",
      "args": [
        "-y", "mcp-remote", "https://www.umlout.com/mcp/http",
        "--header", "Authorization: Bearer YOUR_API_KEY"
      ]
    }
  }
}
```

Note that an nvm path pins a specific Node version, so it breaks when you remove
that version. A Homebrew install avoids the problem entirely.

## `Unexpected token '<', "<!doctype "... is not valid JSON`

```
[pid] Discovering OAuth server configuration...
[pid] Connection error: SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
```

`mcp-remote` looks up OAuth metadata, and something answered that lookup with an HTML page
instead of JSON — so it never got as far as sending your API key.

Umlout serves that metadata as JSON: the MCP server names it in its `401`, and it names the
authorization server where a client without a key can sign in. Getting HTML back means something
between you and the server replied first: a corporate proxy, a VPN portal, or a captive-portal
login page on public Wi-Fi.

Confirm what you are actually reaching:

```bash
curl -i https://www.umlout.com/.well-known/oauth-authorization-server
```

JSON starting with `"issuer"` is correct. Anything returning HTML is the interceptor — try the same
command off the VPN or on a different network.

## A browser opens asking you to allow a client, though you set a key

Or, with an older `mcp-remote`, `HTTP 405: Invalid OAuth error response` in the log.

**Your API key was rejected.** When the server answers `401`, a client reads it as «sign in
through OAuth»: it registers itself with Umlout and opens the Umlout page where you allow it. That
is the right path for a client with no key — ChatGPT's connector, Claude's own connector dialog —
but a client you gave a key reaches it only because the key was refused. Allowing it there works,
and the client then connects without the key; fixing the key avoids the detour.

Confirm it by asking the server directly:

```bash
curl -i --max-time 5 -X POST https://www.umlout.com/mcp/http \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

- `401` with `{"detail":"Invalid or inactive API key."}` — the key is rejected. See
  [HTTP 401](#http-401) below for why.
- `401` saying the key *is not issued for the MCP server* — it is a key for scripts, which works
  over REST only. Create a key for your client in **Profile → AI clients**.
- `200` with an `mcp-session-id` header — the key is fine and the problem is elsewhere.

The cause that hides best: **a key from the wrong environment**. If you run Umlout locally as well as
using the hosted service, a key minted against your local stack is unknown to production and is
rejected exactly like a revoked one. Keys are not portable between environments — check which one
issued the key before assuming it is broken.

## HTTP 401

The key is wrong, revoked, or not being sent. Through a client that supports OAuth this surfaces as a browser
opening to allow the client instead — see [the section above](#a-browser-opens-asking-you-to-allow-a-client-though-you-set-a-key).

- Copy the key again from **Profile → AI clients**. It is shown once at creation and cannot be
  recovered later — if you did not save it, revoke it and make a new one.
- The header value is `Bearer YOUR_KEY` — the word `Bearer`, one space, then the key. A common slip
  is pasting the key alone, or leaving the angle brackets from `<YOUR_API_KEY>`.
- Watch for whitespace: a newline or trailing space picked up when copying will fail auth.
- If you use `X-API-Key` instead, send the bare key with no `Bearer` prefix.

After 20 failed attempts from one IP in 15 minutes, further attempts are blocked for the rest of
that window — fix the key, then wait it out.

## "rate_limited", or HTTP 429

A tool call over its budget comes back as an error whose text starts with
`{"error":"rate_limited"`. Nothing was written. The object names the budget (`scope`) and the seconds
to wait (`retry_after`); `get_rate_limit_status` shows every budget at once. The limits are 300 tool
calls a minute, 600 writes an hour and 600 `bulk_*` calls an hour —
[authentication.md](authentication.md#rate-limits) has the full table.

HTTP `429` is the per-request limit, 600 requests a minute, which sits above the tool-call limit and
is reached only by a client that ignores `retry_after`.

If you hit a limit while drawing a large board, have the assistant use `bulk_add_shapes`,
`bulk_add_connections` and `bulk_create_project_items` instead of one call per item: a bulk call
costs one write however many items it carries.

## The connection opens, then drops after ~30–60 seconds

An HTTP proxy between you and the server is buffering or timing out the event stream the server
answers with. Corporate proxies and some VPNs do this to `text/event-stream` by default.

If your client is still pointed at the old address, `/mcp/sse`, a drop after every Umlout deploy is
expected: an SSE session does not survive a restart of the service. Point it at `/mcp/http`.

The checker reports this as a timeout while the health check still passes. Try the same command off
the VPN to confirm, then ask whoever runs the proxy to pass `text/event-stream` through unbuffered.

## The assistant says a board or a project does not exist

A key only reaches the projects of the account that created it and the projects shared with that
account. If the board is in someone else's project, the project has to be shared with you first
(**Project → Access**) — the key does not widen access. A deleted board is not found either;
`list_deleted` on its project shows it, and `restore_board` brings it back.

Also check the assistant is not inventing an id. `find_board_by_name` matches the whole name,
ignoring case; `list_projects` and `list_project_boards` are the reliable way to get real ids.

## Writes fail with a permissions error

Roles are set on the project and are the same as in the web app. An editor may change everything
inside the project, including renaming and deleting its boards; only the owner may delete the
project itself. A commenter may read and comment, and a viewer may only read. The table is in
[authentication.md](authentication.md#what-a-key-can-reach).

## Something else

Open an [issue](https://github.com/dmkorj/umlout-mcp/issues) with the output of
`check_connection.py`, your client and its version, and the config with the key redacted.
