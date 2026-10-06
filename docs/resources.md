# Resource reference

Resources are read-only URIs an MCP client can fetch without calling a tool. They cover the common
"just let me look at the board" case; anything that changes state goes through
[tools](tools.md).

All four resolve against the account that owns the API key or the OAuth sign-in, and list only the
boards of projects that account can reach. A deleted board is not listed.

| URI | Returns |
|---|---|
| `board://list` | Markdown list of every board you can reach, newest edit first, with its id |
| `board://{board_id}` | The board as JSON — shapes, connections, camera, timestamps |
| `board://{board_id}/shapes` | Just the shapes array, as JSON |
| `board://{board_id}/summary` | Short Markdown summary — name, id, shape and connection counts, last update |

Each resource read counts against the per-minute call limit, like a read tool. It does not count
against the write budgets. See [authentication.md](authentication.md#rate-limits).

## When to use which

`board://{id}` is the complete board and can be large: every shape carries its text style and
layout. When the assistant only needs to orient itself — "how big is this board?" — `summary` is far
cheaper and usually enough.

`board://list` is the natural entry point for "what am I working with?", and the ids it returns
feed straight into the other three.

## Relationship to the tools

`board://{id}` and the `get_board` tool return the same shapes and connections. The tool also takes
`fields`, `offset` and `limit`, so it can return part of a large board; prefer it when the assistant
fetches a board mid-reasoning — for example right after `find_board_by_name`. Prefer the resource
when the client supports resource attachment and the user picks the board explicitly.

A resource shows one board. The objects, relations and types behind its figures belong to the
project and are read with `get_project`, `list_elements` and `get_element`.
