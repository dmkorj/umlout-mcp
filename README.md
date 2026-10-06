# Umlout MCP Server

Let your AI assistant draw on a real whiteboard.

Umlout exposes a hosted [Model Context Protocol](https://modelcontextprotocol.io/) server, so
Claude, Cursor, VS Code Copilot and any other MCP client can build and edit projects in your
[Umlout](https://www.umlout.com) workspace — UML class, sequence, activity and state boards,
flowcharts, wireframes, agile and planning boards, floor plans, dashboards and cloud architecture
drawn with the AWS, Azure and Kubernetes icon sets.

Nothing to install and nothing to run: the server is hosted at `https://www.umlout.com/mcp/http`
(Streamable HTTP). The older SSE address, `/mcp/sse`, still answers, but an SSE session does not
survive a restart of the service, so a client pointed at it fails after every deploy until it is
reconnected by hand. Use `/mcp/http`.
You only need an API key.

---

## Quick start

**1. Get an API key.** Sign in at [umlout.com](https://www.umlout.com), open **Profile → AI clients**,
pick your client and create a key. The profile page gives the exact text for your client with
the key already in it.

**2. Add the server to your client.**

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add --transport http umlout https://www.umlout.com/mcp/http --header "Authorization: Bearer YOUR_API_KEY"
```

More options, including project scope: [examples/claude-code.md](examples/claude-code.md).
</details>

<details>
<summary><b>Cursor</b> · <b>VS Code</b></summary>

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "umlout": {
      "url": "https://www.umlout.com/mcp/http",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

VS Code reads a different shape — `servers`, not `mcpServers`, and `"type": "http"` — so use
[examples/vscode.json](examples/vscode.json) in `.vscode/mcp.json`. It prompts for the key and
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
        "-y", "mcp-remote", "https://www.umlout.com/mcp/http",
        "--header", "Authorization: Bearer YOUR_API_KEY"
      ]
    }
  }
}
```

Then **quit Claude Desktop completely** and reopen it — closing the window is not enough.
</details>

<details>
<summary><b>Codex</b> · <b>Gemini CLI</b> · <b>Antigravity</b> · <b>Devin Desktop</b> · other clients</summary>

Codex keeps the key out of its config and reads it from an environment variable — see
[examples/codex.md](examples/codex.md).

Every other client takes a JSON file with an address and a `headers` object; only the name of the
address field differs:

| client | file | address field |
|---|---|---|
| Cursor | `~/.cursor/mcp.json` | `url` |
| Gemini CLI | `~/.gemini/settings.json` | `httpUrl` |
| Antigravity | `~/.gemini/config/mcp_config.json` | `serverUrl` |
| Devin Desktop (formerly Windsurf) | its `mcp_config.json` (MCPs → View raw config) | `serverUrl` |

```json
{
  "mcpServers": {
    "umlout": {
      "serverUrl": "https://www.umlout.com/mcp/http",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```
</details>

<details>
<summary><b>ChatGPT</b> · <b>Claude connectors</b> · <b>Grok</b> — clients that take only an address</summary>

No key: give the client `https://www.umlout.com/mcp/http`. It opens an Umlout page where you
sign in and allow it. See [docs/authentication.md](docs/authentication.md#signing-in-without-a-key-oauth).
</details>

**3. Ask for a board:**

> Create a project "Auth" and draw a UML sequence diagram of the OAuth2 authorization code flow
> on a board in it.

Verify your setup at any time:

```bash
python3 scripts/check_connection.py --api-key YOUR_API_KEY
```

---

## What it can do

**95 tools** across twelve areas, plus **4 read-only resources**. Full reference with every argument:
[docs/tools.md](docs/tools.md) and [docs/resources.md](docs/resources.md).

Umlout stores a **project**, and a board is one view of it. A project holds **objects** — each with
a name, exactly one **type**, its own properties and a description — and the **relations** between
them. A **figure** on a board is one drawing of an object, so the same object can be drawn on five
boards and is still one object; a line on a board is one drawing of a relation.

| Area | What the assistant can do |
|---|---|
| **Projects** | Create, list, read, rename, share publicly and delete projects |
| **Boards** | Create boards in a project, find them by name, rename, point the camera, clear, delete and restore |
| **Objects and folders** | Create objects, folders and relations in one call; update, merge duplicates, give an object its own detail board |
| **Relations** | Create and update relations with UML detail; reverse a relation's direction |
| **Types and fields** | Browse the catalogue's types; declare the project's own types; describe each type's fields — text, number, yes/no, choice, markdown, reference, counter, computed, file, list of pairs — and the template an object of the type is drawn with |
| **Shared fields** | Describe a field once and use it in several types |
| **Shapes and connections** | Draw figures of objects and free figures, UML classes with their compartments, connections with UML notation, sequence messages, custom anchor points; update and delete one at a time or hundreds per call |
| **Composite figures and palettes** | Save a set of figures as one card and place it again; redraw older copies; arrange the toolbar's palettes |
| **Files** | Upload files into a project, rename, delete and restore them; show an image in an Image figure |
| **Comments** | Add, list, resolve and delete comments and replies on any figure or line |
| **Deleted items** | List what was deleted in a project and restore it — a board, an object, a relation, a type, a shared field or a file |
| **Plan and limits** | Read the plan's quotas and what is left of the rate-limit budgets |

The figure vocabulary covers **205 figures** — basic geometry, UML (class, use case, state,
activity, sequence, component, deployment, timing), flowchart, charts and dashboard figures,
agile and retrospective cards, plans with stages and tasks, floor plans, and a full wireframe kit —
plus the AWS, Azure and Kubernetes icon libraries.

### Things worth asking for

- *"Turn this OpenAPI spec into a component diagram."*
- *"Sketch the mobile onboarding flow as wireframes — three screens."*
- *"Read the board 'Checkout' and tell me which states have no outgoing transitions."*
- *"Build a project from these requirements: orders, invoices, customers — one type per noun,
  with their fields — and draw a class board of it."*
- *"Add a `status` field to every Task and count the done ones on each Stage."*

---

## Authentication and limits

Every request carries your key in `Authorization: Bearer <key>` (or `X-API-Key`), or an OAuth
token for a client that signs in through the browser. Both are scoped to your account — the
assistant sees exactly the projects you can see, with the role you have in each, and nothing else.

| Limit | Value |
|---|---|
| Tool calls | 300 per minute |
| Write tool calls | 600 per hour |
| Bulk write calls (`bulk_*`) | 600 per hour, in addition to the write budget |

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
