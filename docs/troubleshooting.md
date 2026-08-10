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
- **Claude Desktop needs Node.js** for the `npx mcp-remote` bridge. Check with `node --version`.

## HTTP 401

The key is wrong, revoked, or not being sent.

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
