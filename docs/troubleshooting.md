# Troubleshooting

Start here:

```bash
python3 scripts/check_connection.py --api-key YOUR_API_KEY
```

It separates the three failures that look identical from inside a chat client: the service being
down, the key being rejected, and the SSE stream being blocked on the way.

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
        "-y", "mcp-remote", "https://www.umlout.com/mcp/sse",
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

`mcp-remote` checks for OAuth metadata before it connects, and something answered
that check with an HTML page instead of JSON — so it never got as far as sending
your API key.

Umlout authenticates with a static API key and serves no OAuth metadata, so those
probes return 404 and the bridge falls through to your key. Getting HTML back
instead means something between you and the server replied first: a corporate
proxy, a VPN portal, or a captive-portal login page on public Wi-Fi.

Confirm what you are actually reaching:

```bash
curl -i https://www.umlout.com/.well-known/oauth-authorization-server
```

A `404` is correct and expected. Anything returning HTML is the interceptor —
try the same command off the VPN or on a different network.

## `HTTP 405: Invalid OAuth error response`

Also shows up as a bare `405 Not Allowed` HTML page in the log.

```
Connection error: ServerError: HTTP 405: Invalid OAuth error response:
SyntaxError: Unexpected token '<', "<html>
<h"... is not valid JSON. Raw body: <html>
<head><title>405 Not Allowed</title></head>
    at registerClient (...)
    at SSEClientTransport._authThenStart (...)
```

**Your API key was rejected.** Nothing in that message says so, which is what makes it hard.

Here is the actual sequence. The bridge opens the stream, the server answers `401`, and `mcp-remote`
reads any `401` as "this server wants OAuth". It then tries to register itself as an OAuth client by
POSTing to `/register` — an endpoint that does not exist here, because Umlout authenticates with a
static API key and runs no OAuth server. The web server answers that POST with a plain `405` HTML
page, the bridge tries to parse it as an OAuth error object, and dies. The `405`, the HTML and the
web server's name in the output are all downstream of the original `401`.

Confirm it by asking the server directly:

```bash
curl -i --max-time 5 -H "Authorization: Bearer YOUR_API_KEY" https://www.umlout.com/mcp/sse
```

- `401` with `{"detail":"Invalid or inactive API key."}` — the key is rejected. See
  [HTTP 401](#http-401) below for why.
- `200` with `content-type: text/event-stream` — the key is fine and the problem is elsewhere.
  (The command will hang until `--max-time` cuts it off. That is the stream working.)

The cause that hides best: **a key from the wrong environment**. If you run Umlout locally as well as
using the hosted service, a key minted against your local stack is unknown to production and is
rejected exactly like a revoked one. Keys are not portable between environments — check which one
issued the key before assuming it is broken.

## HTTP 401

The key is wrong, revoked, or not being sent. Through the `mcp-remote` bridge this surfaces as a
confusing `405` instead — see [the section above](#http-405-invalid-oauth-error-response).

- Copy the key again from **Profile → MCP API Keys**. It is shown once at creation and cannot be
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

An HTTP proxy between you and the server is buffering or timing out the event stream. Corporate
proxies and some VPNs do this to `text/event-stream` by default.

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
