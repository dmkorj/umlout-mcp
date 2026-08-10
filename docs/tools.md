# Tool reference

37 tools, grouped by area. Every tool acts as the account that owns the API key — there is
no user or owner argument to pass, and nothing outside your workspace is reachable.

Tools whose name starts with `get_`, `list_` or `find_` are reads and are not metered against
the write budget. See [authentication.md](authentication.md) for the limits.

## Contents

- [Diagrams](#diagrams) — 6 tools
- [Shapes & connections](#shapes--connections) — 12 tools
- [Domain models](#domain-models) — 15 tools
- [Comments](#comments) — 4 tools

---

## Diagrams

Boards are owned by the account the API key belongs to.

### `list_diagrams`

List all diagrams belonging to the authenticated user.

```python
list_diagrams()
```

**Returns** — JSON array of diagram summaries (id, name, created_at, updated_at).

### `get_diagram`

Fetch a full diagram including all shapes and connections.

```python
get_diagram(diagram_id)
```

**Parameters**

- `diagram_id` — MongoDB _id string of the diagram.

**Returns** — Full diagram JSON including shapes, connections, camera, and metadata.

### `find_diagram_by_name`

Find a diagram by its exact name for the authenticated user.

```python
find_diagram_by_name(name)
```

**Parameters**

- `name` — Exact diagram name to search for.

**Returns** — DiagramSummary JSON, or null if not found.

### `create_diagram`

Create a new empty diagram owned by the authenticated user.

```python
create_diagram(name)
```

**Parameters**

- `name` — Human-readable name for the new diagram.

**Returns** — Full diagram JSON of the newly created diagram.

### `rename_diagram`

Rename an existing diagram. Only the owner may rename.

```python
rename_diagram(diagram_id, name)
```

**Parameters**

- `diagram_id` — MongoDB _id string of the diagram.
- `name` — New name for the diagram.

**Returns** — Updated diagram summary JSON.

### `delete_diagram`

Delete a diagram permanently. Only the owner may delete.

```python
delete_diagram(diagram_id)
```

**Parameters**

- `diagram_id` — MongoDB _id string of the diagram.

**Returns** — Success message string.

---

## Shapes & connections

Everything drawn on a board. Prefer the `bulk_*` tools when generating a whole diagram — one call instead of dozens.

### `add_shape`

Add a single shape to a diagram.

```python
add_shape(
    diagram_id,
    type,
    x,
    y,
    width,
    height,
    rotation,
    label,
    style,
    container_id,
    seq_operator,
    seq_operands,
    act_lanes,
    act_lane_orientation,
)
```

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `type` — Shape type. Basic: rect, roundedRect, circle, diamond, text, image, triangle, callout, parallelogram, star, arrowRight, arrowLeft, doubleArrow, pentagon, octagon, hexagon, frame, trapezoid, cloud, cross, cylinder, bracketLeft, bracketRight, chevron, label. UML: umlClass, umlInterface, umlPackage, umlComment, umlNote. Kanban: ticketColumn, ticketSticky. Sequence diagram: umlSeqActor, umlSeqLifeline (participant), umlSeqActivation, umlSeqFragment. Activity diagram: umlActAction (rounded rect), umlActInitial (filled circle, ~24 px square), umlActFinal (bullseye, ~32 px square), umlActFlowFinal (circle with X, ~32 px square), umlActDecision (diamond; also used for merge), umlActBar (fork/join bar — keep one side ~8 px thick; width >= height renders horizontal, otherwise vertical), umlActSignalSend, umlActAcceptEvent, umlActObject, umlActPartition (swimlanes; see act_lanes). Control-flow edges are plain connections; put guards in the connection label, e.g. "[x > 0]". Wireframe: wfMobileScreen (~320x640) and wfDesktopScreen (~640x420) are device frames that act as containers — place widgets inside them via container_id; content starts below the chrome (mobile: y+48, desktop: y+36). Widgets: wfButton, wfInput, wfTextarea, wfDropdown, wfCheckbox, wfRadio, wfSwitch, wfLabel, wfHeading, wfImage, wfTextBlock, wfDivider, wfAvatar, wfSlider, wfProgress, wfSearch, wfNavbar, wfTabBar, wfCard, wfTable, wfBadge. Control state lives in wfChecked (checkbox/ radio/switch) and wfValue 0-100 (slider/progress) — set them via bulk_add_shapes raw dicts or update_shape fields.
- `x` — Left edge X position in world space.
- `y` — Top edge Y position in world space.
- `width` — Shape width in pixels.
- `height` — Shape height in pixels. For lifelines (umlSeqLifeline / umlSeqActor) this is the TOTAL height: the head box occupies the top 40 px (participant) or 60 px (actor) and the dashed line fills the rest. Messages attach to the vertical center line at x + width/2.
- `rotation` — Rotation in radians (0 = unrotated, positive = clockwise).
- `label` — Text label displayed inside the shape (lifelines: the participant name, e.g. "user : User").
- `style` — Optional ShapeStyle overrides (strokeColor, fillColor, etc.).
- `container_id` — Structural parent shape id. Required for umlSeqActivation (its lifeline id — also center the bar on the lifeline: x = lifeline.x + lifeline.width/2 - width/2).
- `seq_operator` — umlSeqFragment only — alt, opt, loop, par, or break.
- `seq_operands` — umlSeqFragment only — list of {"guard": str, "height": float}, top to bottom. Heights should sum to height - 22 (the operator tab band).
- `act_lanes` — umlActPartition only — list of {"label": str, "size": float}, left to right (vertical) or top to bottom (horizontal). Sizes must sum to the shape width (vertical) or height - 28 (horizontal; the title bar band). Omit to get two equal lanes.
- `act_lane_orientation` — umlActPartition only — "vertical" (lanes side by side, the default) or "horizontal" (stacked rows).

**Returns** — JSON of the newly created shape (including its generated id).

### `bulk_add_shapes`

Add multiple shapes to a diagram in a single operation.

```python
bulk_add_shapes(diagram_id, shapes)
```

Ideal for generating an entire UML diagram at once.

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `shapes` — List of shape descriptors. Each must have x, y and may include type, width, height, label, style, containerId, seqOperator, seqOperands, actLanes, actLaneOrientation (see add_shape for per-type semantics).

**Returns** — JSON array of all created shapes (each with its generated id).

### `update_shape`

Update fields of an existing shape.

```python
update_shape(diagram_id, shape_id, fields)
```

Pass only the fields you want to change; all others are preserved.
Nested fields like 'style' are merged (not replaced) if provided as a dict.

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `shape_id` — id of the shape to update.
- `fields` — Dict of fields to update (e.g. {"label": "New Name", "x": 200}).

**Returns** — JSON of the updated shape.

### `delete_shape`

Delete a shape and all connections that reference it.

```python
delete_shape(diagram_id, shape_id)
```

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `shape_id` — id of the shape to delete.

**Returns** — Success message indicating how many connections were also removed.

### `add_custom_anchor`

Add a custom anchor point to a shape's border.

```python
add_custom_anchor(diagram_id, shape_id, side, t, anchor_id)
```

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `shape_id` — id of the target shape.
- `side` — Which border edge — top, right, bottom, or left.
- `t` — Position along the edge from 0.0 to 1.0, CLOCKWISE: top:    0 = left corner,  1 = right corner. right:  0 = top corner,   1 = bottom corner. bottom: 0 = right corner, 1 = left corner. left:   0 = bottom corner, 1 = top corner. On lifelines (umlSeqLifeline/umlSeqActor), left/right anchors below the head band resolve to the dashed center line.
- `anchor_id` — Optional id for the anchor.  Auto-generated when omitted.

**Returns** — JSON of the new anchor {id, side, t}.

### `remove_custom_anchor`

Remove a custom anchor point from a shape.

```python
remove_custom_anchor(diagram_id, shape_id, anchor_id)
```

Any connections whose endpoints reference this anchor will have their
customAnchorId cleared (they fall back to the shape's regular anchor).

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `shape_id` — id of the shape that owns the anchor.
- `anchor_id` — id of the custom anchor to remove.

**Returns** — Success message string.

### `add_connection`

Draw a connection between two shapes.

```python
add_connection(
    diagram_id,
    from_shape_id,
    to_shape_id,
    from_anchor,
    to_anchor,
    from_custom_anchor_id,
    to_custom_anchor_id,
    label,
    style,
    seq_kind,
    relation_kind,
    start_multiplicity,
    start_role,
    end_multiplicity,
    end_role,
)
```

For most use-cases supply just from_shape_id and to_shape_id and leave
the anchors unset: each end then picks the side facing the other shape,
and keeps doing so as either shape is moved. Only set from_anchor /
to_anchor when a specific side is required by the diagram's semantics.
For free-point connections, omit the shape IDs.

For UML sequence-diagram messages between lifelines, prefer
add_sequence_message — it creates the lifeline anchors for you.

For UML class-diagram relations, set relation_kind to apply the standard
notation preset. Direction convention (from → to):
  - association:         plain line, no heads.
  - directedAssociation: open arrow at the `to` end.
  - aggregation:         hollow diamond at the `from` (whole) end; draw
                         from the whole/aggregate to the part.
  - composition:         filled diamond at the `from` (whole) end.
  - generalization:      hollow triangle at the `to` end; draw from the
                         subclass to the superclass.
  - realization:         dashed line + hollow triangle at `to`; draw from
                         the implementing class to the interface.
  - dependency:          dashed line + open arrow at the `to` end.

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `from_shape_id` — id of the source shape (or None for free point).
- `to_shape_id` — id of the target shape (or None for free point).
- `from_anchor` — Pins the edge the connection leaves from (top/right/bottom/left). Omit for an auto anchor that always faces the other end.
- `to_anchor` — Pins the edge the connection arrives at. Omit for auto.
- `from_custom_anchor_id` — If set, the connection originates from this custom anchor id on from_shape_id instead of the named edge.
- `to_custom_anchor_id` — If set, the connection terminates at this custom anchor id on to_shape_id instead of the named edge.
- `label` — Optional text label on the connection.
- `style` — Optional ConnectionStyle overrides (win over any preset).
- `seq_kind` — Marks a sequence-diagram message (sync, async, reply, create, destroy) and applies its UML 2.5.1 notation preset.
- `relation_kind` — Marks a UML class-diagram relation (association, directedAssociation, aggregation, composition, generalization, realization, dependency) and applies its notation preset. Mutually exclusive with seq_kind.
- `start_multiplicity` — UML multiplicity at the `from` end (e.g. "1", "0..*").
- `start_role` — Role name at the `from` end.
- `end_multiplicity` — UML multiplicity at the `to` end.
- `end_role` — Role name at the `to` end.

**Returns** — JSON of the newly created connection (including its generated id).

### `add_sequence_message`

Add a UML sequence-diagram message between two lifelines at height y.

```python
add_sequence_message(
    diagram_id,
    from_lifeline_id,
    to_lifeline_id,
    y,
    kind,
    label,
)
```

Creates the custom anchors on both lifelines' dashed center lines
(sides facing each other, derived from the lifelines' positions),
applies the UML 2.5.1 notation preset for the kind (sync = solid line
+ filled arrowhead, async = solid + open, reply/create = dashed +
open, destroy = solid + filled ending at an X), and creates the
connection. Self-messages (from == to) become a small rectangular
loop. For 'destroy', the target lifeline's destruction X is placed at
y. For 'create', place the target lifeline's head center at y first
(head height: 40 participant / 60 actor) — the message attaches to
the head's facing edge.

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `from_lifeline_id` — id of the source lifeline (umlSeqLifeline or umlSeqActor).
- `to_lifeline_id` — id of the target lifeline (may equal the source).
- `y` — World-space y of the message. Must be below both heads and above both lifeline bottoms. When the diagram has snapToGrid on, y (and the self-message return y) is snapped to the nearest half-grid step before validation and placement.
- `kind` — sync | async | reply | create | destroy.
- `label` — Message label. Defaults per kind (e.g. "message()").

**Returns** — JSON of the created connection (including generated anchor ids).

### `bulk_add_connections`

Add multiple connections to a diagram in a single operation.

```python
bulk_add_connections(diagram_id, connections)
```

Each connection dict must contain 'from' and 'to' keys with ConnectionEndpoint
objects (shapeId, and optionally anchor — omit it for an auto anchor that
always faces the other end). Optionally include 'label', 'style', 'seqKind',
'relationKind' (UML class relation — see add_connection for the kinds and
direction convention), and 'endLabels' ({"start"/"end": {"multiplicity",
"role"}}). seqKind and relationKind are mutually exclusive.

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `connections` — List of connection descriptors.

**Returns** — JSON array of all created connections (each with its generated id).

### `update_connection`

Update fields of an existing connection.

```python
update_connection(diagram_id, connection_id, fields)
```

Pass only the fields to change; all others are preserved.

Passing "relationKind" retypes a UML class relation: it validates the
kind, sets classRelation, and merges that kind's notation preset into the
style (rejected on sequence-message connections). Dict fields are merged
one level deep, so {"endLabels": {"end": {...}}} replaces the whole "end"
sub-dict but leaves "start" untouched.

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `connection_id` — id of the connection to update.
- `fields` — Dict of fields to update (e.g. {"label": "uses", "style": {"strokeColor": "#ff0000"}}).

**Returns** — JSON of the updated connection.

### `delete_connection`

Remove a connection from a diagram.

```python
delete_connection(diagram_id, connection_id)
```

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `connection_id` — id of the connection to delete.

**Returns** — Success message string.

### `clear_diagram`

Remove ALL shapes and connections from a diagram.

```python
clear_diagram(diagram_id)
```

The diagram itself (name, metadata) is preserved.

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.

**Returns** — Success message string.

---

## Domain models

A model holds nestable folders → elements → relations. Editor rights are required for writes; deleting a model requires ownership.

### `list_models`

List all domain models owned by the authenticated user.

```python
list_models()
```

**Returns** — JSON array of model summaries (id, name, description, timestamps).

### `get_model`

Fetch a model with its full contents (folders, elements, relations).

```python
get_model(model_id)
```

**Parameters**

- `model_id` — MongoDB _id string of the model.

**Returns** — JSON object: model summary plus `folders`, `elements`, `relations` arrays.

### `create_model`

Create a new empty domain model owned by the authenticated user.

```python
create_model(name, description)
```

**Parameters**

- `name` — Human-readable model name.
- `description` — Optional description.

**Returns** — JSON summary of the created model.

### `update_model`

Update a model's name and/or description. Editors only.

```python
update_model(model_id, name, description)
```

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `name` — New name (omit or empty to leave unchanged).
- `description` — New description (omit or empty to leave unchanged).

**Returns** — JSON summary of the updated model.

### `delete_model`

Delete a model and all its folders, elements, and relations. Owner only.

```python
delete_model(model_id)
```

Linked diagrams are unlinked and their model-originated shapes/connections removed.

**Parameters**

- `model_id` — MongoDB _id string of the model.

**Returns** — Success message string.

### `create_folder`

Create a folder in a model. Editors only.

```python
create_folder(model_id, name, parent_folder_id)
```

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `name` — Folder name.
- `parent_folder_id` — Optional parent folder id (empty for root level).

**Returns** — JSON of the created folder.

### `bulk_create_model_items`

Create folders, elements, and relations in a model in one operation. Editors only.

```python
bulk_create_model_items(model_id, items)
```

Ideal for building a whole model tree at once. Items may reference each
other by a local `ref` name, so you can point an element at a folder — or
a relation at two elements — that this same call is creating, without
knowing their generated ids.

`items` is an object with any of these keys, each a list:
  folders:   {"ref": optional local name, "name": required,
              "parent_folder_id": optional folder id or local folder ref}
  elements:  {"ref": optional local name, "name": required,
              "folder_id": optional folder id or local folder ref,
              "description": optional, "element_type": defaults to "rectangle"}
  relations: {"source_element_id": required element id or local element ref,
              "target_element_id": required element id or local element ref,
              "label": optional, "relation_type": defaults to "association"}

An id-or-ref field matching a `ref` declared in this same call resolves to
that new item; otherwise it must be an id already in the model. Folders may
be listed in any order — parents are inserted before their children.

Validation is all-or-nothing: the same guards as the single-item tools
(folder cycles, folder/element ownership, relation self-loops and
duplicates) run over the whole payload before anything is written, so a
rejected item leaves the model completely untouched.

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `items` — Object with optional `folders`, `elements`, `relations` lists (at most 100 each).

**Returns** — JSON object with `folders`, `elements`, `relations` arrays of the created items, each with its generated id; folders and elements echo back the `ref` you supplied so you can map refs to real ids.

### `update_folder`

Rename and/or move a folder. Editors only.

```python
update_folder(model_id, folder_id, name, parent_folder_id)
```

Moving into the folder itself or one of its descendants is rejected.

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `folder_id` — Folder to update.
- `name` — New name (empty to leave unchanged).
- `parent_folder_id` — New parent id to move under (empty string leaves it unchanged).

**Returns** — JSON of the updated folder.

### `delete_folder`

Delete a folder and its descendant folders. Editors only.

```python
delete_folder(model_id, folder_id)
```

Elements inside the deleted folders are preserved and moved to the model root.

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `folder_id` — Folder to delete.

**Returns** — Success message string.

### `create_element`

Create an element in a model. Editors only.

```python
create_element(model_id, name, folder_id, description, element_type)
```

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `name` — Element name.
- `folder_id` — Optional folder id (empty for root level). Must belong to the model.
- `description` — Optional description.
- `element_type` — Element kind (default "rectangle").

**Returns** — JSON of the created element.

### `update_element`

Update an element's fields and/or move it to another folder. Editors only.

```python
update_element(
    model_id,
    element_id,
    name,
    folder_id,
    description,
    element_type,
)
```

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `element_id` — Element to update.
- `name` — New name (empty leaves unchanged).
- `folder_id` — New folder id to move under (empty leaves unchanged; must belong to the model).
- `description` — New description (empty leaves unchanged).
- `element_type` — New element type (empty leaves unchanged).

**Returns** — JSON of the updated element.

### `delete_element`

Delete an element and any relations touching it. Editors only.

```python
delete_element(model_id, element_id)
```

Also removes the element's shapes (and their connections) from all diagrams.

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `element_id` — Element to delete.

**Returns** — Success message string.

### `create_relation`

Create a relation between two elements in a model. Editors only.

```python
create_relation(
    model_id,
    source_element_id,
    target_element_id,
    label,
    relation_type,
)
```

Self-loops and duplicate (same source/target/type) relations are rejected.

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `source_element_id` — Source element id (must belong to the model).
- `target_element_id` — Target element id (must belong to the model).
- `label` — Optional relation label.
- `relation_type` — Relation kind (default "association").

**Returns** — JSON of the created relation.

### `update_relation`

Update a relation's label and/or type. Editors only.

```python
update_relation(model_id, relation_id, label, relation_type)
```

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `relation_id` — Relation to update.
- `label` — New label (empty leaves unchanged).
- `relation_type` — New type (empty leaves unchanged).

**Returns** — JSON of the updated relation.

### `delete_relation`

Delete a relation and remove its connections from all diagrams. Editors only.

```python
delete_relation(model_id, relation_id)
```

**Parameters**

- `model_id` — MongoDB _id string of the model.
- `relation_id` — Relation to delete.

**Returns** — Success message string.

---

## Comments

Threaded comments anchored to a shape or connection.

### `list_comments`

List root-level comments for a diagram, optionally filtered by target element.

```python
list_comments(diagram_id, target_id, include_resolved)
```

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `target_id` — If provided, only return comments attached to this shape/connection id.
- `include_resolved` — When False, only return unresolved comments (default True).

**Returns** — List of root comment objects with reply_count populated.

### `add_comment`

Add a comment or reply to a diagram element.

```python
add_comment(diagram_id, target_type, target_id, body, author_name, parent_id)
```

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `target_type` — "shape" or "connection".
- `target_id` — Id of the shape or connection to attach to.
- `body` — Comment text (1-2000 chars).
- `author_name` — Display name to attribute the comment to.
- `parent_id` — If provided, this is a reply to that root comment id.

**Returns** — The created comment object.

### `resolve_comment`

Mark a root comment as resolved or unresolved.

```python
resolve_comment(diagram_id, comment_id, resolved)
```

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `comment_id` — MongoDB _id of the root comment to update.
- `resolved` — True to resolve, False to reopen (default True).

**Returns** — The updated comment object.

### `delete_comment`

Delete a comment and all its replies.

```python
delete_comment(diagram_id, comment_id)
```

**Parameters**

- `diagram_id` — MongoDB _id of the diagram.
- `comment_id` — MongoDB _id of the comment to delete.

**Returns** — {"deleted_count": N} indicating how many documents were removed.
