# Claude Code

One command, no config file:

```bash
claude mcp add --transport sse umlout https://www.umlout.com/mcp/sse --header "Authorization: Bearer YOUR_API_KEY"
```

Verify it registered:

```bash
claude mcp list
```

Then ask for a diagram in any session:

> Create a board called "Ingest pipeline" and draw the flow: S3 → Lambda → SQS → worker → Postgres.

## Scope

By default the server is added for your user account only. To share it with everyone working in a
repository, add `--scope project` — this writes `.mcp.json` at the repo root, which **is**
committed. Do not put a live key in a project-scoped config; use an environment variable instead:

```bash
claude mcp add --transport sse umlout https://www.umlout.com/mcp/sse --scope project --header "Authorization: Bearer \${UMLOUT_API_KEY}"
```

Each collaborator then exports their own `UMLOUT_API_KEY`.

## Removing it

```bash
claude mcp remove umlout
```
