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

## HTTP 429

You hit a rate limit: 60 requests/minute, 600 write calls/hour, or 60 `bulk_*` calls/hour. Nothing
was partially written. Wait for the window to roll over.

If you hit this while generating a large diagram, have the assistant use `bulk_add_shapes` and
`bulk_add_connections` instead of one call per element — that is what they exist for.

## The connection opens, then drops after ~30–60 seconds

An HTTP proxy between you and the server is buffering or timing out the event stream the server
answers with. Corporate proxies and some VPNs do this to `text/event-stream` by default.

If your client is still pointed at the old address, `/mcp/sse`, a drop after every Umlout deploy is
expected: an SSE session does not survive a restart of the service. Point it at `/mcp/http`.

The checker reports this as a timeout while the health check still passes. Try the same command off
the VPN to confirm, then ask whoever runs the proxy to pass `text/event-stream` through unbuffered.

## The assistant says a diagram does not exist

A key only reaches the workspace of the account that created it. If the board lives in someone
else's account, it has to be shared with you first — the key does not widen access.

Also check the assistant is not inventing an id. `find_diagram_by_name` matches the name
**exactly**, including case and spacing; `list_diagrams` is the reliable way to get real ids.

## Writes fail with a permissions error

Roles are the same as in the web app. Editors can change a model's contents, but renaming or
deleting a diagram, and deleting a model, require ownership.

## Something else

Open an [issue](https://github.com/dmkorj/umlout-mcp/issues) with the output of
`check_connection.py`, your client and its version, and the config with the key redacted.
