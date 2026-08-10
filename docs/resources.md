# Resource reference

Resources are read-only URIs an MCP client can fetch without calling a tool. They cover the common
"just let me look at the board" case; anything that changes state goes through
[tools](tools.md).

All four resolve against the account that owns the API key.

| URI | Returns |
|---|---|
| `diagram://list` | Markdown list of every diagram accessible to you (owned or shared) |
| `diagram://{diagram_id}` | The full diagram document as JSON — shapes, connections, metadata |
| `diagram://{diagram_id}/shapes` | Just the shapes array, as JSON |
| `diagram://{diagram_id}/summary` | Short Markdown summary — name, counts, shape-type breakdown |

## When to use which

`diagram://{id}` is the complete picture and can be large on a busy board. When the assistant only
needs to orient itself — "how big is this diagram, what kind of thing is it?" — `summary` is far
cheaper and usually enough.

`diagram://list` is the natural entry point for "what am I working with?", and the ids it returns
feed straight into the other three.

## Relationship to the tools

`diagram://{id}` and the `get_diagram` tool return the same document. Prefer the resource when the
client supports resource attachment (the user picks the board explicitly), and the tool when the
assistant needs to fetch a board mid-reasoning — for example right after `find_diagram_by_name`.
