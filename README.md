# Umlout MCP Server

Let your AI assistant draw on a real whiteboard.

Umlout exposes a hosted [Model Context Protocol](https://modelcontextprotocol.io/) server, so
Claude, Cursor, VS Code Copilot and any other MCP client can create and edit diagrams in your
[Umlout](https://www.umlout.com) workspace — UML class and sequence diagrams, flowcharts, activity
diagrams, wireframes and domain models.

Nothing to install and nothing to run: the server is hosted at `https://www.umlout.com/mcp/sse`.
You only need an API key.

---

## Quick start

**1. Get an API key.** Sign in at [umlout.com](https://www.umlout.com), open **Profile → MCP API
Keys**, and create a key.

**2. Add the server to your client.**

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add --transport sse umlout https://www.umlout.com/mcp/sse --header "Authorization: Bearer YOUR_API_KEY"
```

More options, including project scope: [examples/claude-code.md](examples/claude-code.md).
</details>

<details>
<summary><b>Cursor</b> · <b>VS Code</b> — clients that speak remote SSE natively</summary>

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "umlout": {
      "url": "https://www.umlout.com/mcp/sse",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

For VS Code Copilot use [examples/vscode.json](examples/vscode.json) — it prompts for the key and
keeps it in VS Code's secret storage instead of a committed file.
</details>

<details>
<summary><b>Claude Desktop</b> — via the <code>mcp-remote</code> bridge</summary>

Claude Desktop's config file does not take a remote URL directly, so route it through
[`mcp-remote`](https://www.npmjs.com/package/mcp-remote) (needs Node.js). Edit
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "umlout": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote", "https://www.umlout.com/mcp/sse",
        "--header", "Authorization: Bearer YOUR_API_KEY"
      ]
    }
  }
}
```

Then **quit Claude Desktop completely** and reopen it — closing the window is not enough.
</details>

**3. Ask for a diagram:**

> Draw a UML sequence diagram of an OAuth2 authorization code flow on a new board called "Auth".

Verify your setup at any time:

```bash
python3 scripts/check_connection.py --api-key YOUR_API_KEY
```

---

## What it can do

**37 tools** across four areas, plus **4 read-only resources**. Full reference with every argument:
[docs/tools.md](docs/tools.md) and [docs/resources.md](docs/resources.md).

| Area | What the assistant can do |
|---|---|
| **Diagrams** | Create, list, find, rename, clear and delete boards |
| **Shapes & connections** | Add and edit shapes, draw connections with UML notation, place sequence messages, define custom anchor points, bulk-create hundreds of elements in one call |
| **Domain models** | Build nestable folders → elements → relations; create a whole model tree in a single call |
| **Comments** | Add, list, resolve and delete comments and replies on any element |

The shape vocabulary covers **70 types** — basic geometry, UML class/interface/package, sequence
(actor, lifeline, activation, fragment), activity (action, decision, fork/join, swimlanes), and a
full wireframe kit (screens, buttons, inputs, navbars, tables, cards).

### Things worth asking for

- *"Turn this OpenAPI spec into a component diagram."*
- *"Sketch the mobile onboarding flow as wireframes — three screens."*
- *"Read the board 'Checkout' and tell me which states have no outgoing transitions."*
- *"Build a domain model from these requirements: orders, invoices, customers."*

---

## Authentication and limits

Every request carries your key in `Authorization: Bearer <key>` (or `X-API-Key`). Keys are scoped
to your account — the assistant sees exactly the diagrams you can see, and nothing else.

| Limit | Value |
|---|---|
| Requests | 60 per minute |
| Write tool calls | 600 per hour |
| Bulk write calls (`bulk_*`) | 60 per hour |

Details, key rotation and revocation: [docs/authentication.md](docs/authentication.md).
Something not working? [docs/troubleshooting.md](docs/troubleshooting.md).

---

## About this repository

This repo is the public home of the Umlout MCP **connector**: documentation, client configs, the
registry manifest ([server.json](server.json)) and a connection checker. The server itself is a
hosted service — there is no local installation, so there is no server source here.

Issues and questions about the MCP integration are welcome in
[Issues](https://github.com/dmkorj/umlout-mcp/issues).

## License

[MIT](LICENSE) — documentation and examples.
