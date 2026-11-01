# 915 · Asqueel relation tree

Document ID: **GP-915**. Status: implemented in an isolated development clone;
owner acceptance pending. [Compact counterpart](../../docs_llm/internal/915-asqueel-relation-tree.md).

<a id="gp-915-005"></a>
## 005 · Kajenn integration

Block ID: **GP-915-005**.

`gramlot_py_server.asqueel_relations.AsqueelRelations` is an opt-in page mixin.
A page declares the permitted Asqueel root table names in the `relation_roots`
tuple; its default is empty. Optional `relation_database` selects the Kajenn
database; the default uses Kajenn's default. The endpoint `relation_tree` uses
the request-scoped `async_db` model, rejects unlisted roots, and follows only
actual relation resolvers without a fixed path-depth limit. It returns the current
level in a Bag, replacing Asqueel's server-side relation resolvers with inert
Gramlot `TreeStoreResolver` descriptions. Request-supplied attributes and label
are accepted for the generic store contract but do not authorize traversal.

`relation_tree(parent, datapath=..., table=...)` composes the generic tree store.
The page's Logic must supply `treeStoreMount`, `treeInspect` and
`treeInspectClose` from `TreeStoreLogic`; the
tree collection must be installed. For example, with the tree collection installed on the Gramlot server:

```python
from gramlot import Page as BasePage
from gramlot_py_server.asqueel_relations import AsqueelRelations, relation_tree

class Page(AsqueelRelations, BasePage):
    relation_roots = ("app.customer",)

    def main(self, root):
        relation_tree(root, datapath="model", table="app.customer")
```

The companion `_aux.js` exports the page Logic:

```javascript
export {TreeStoreLogic as Logic} from '@gramlot/gramlot/page';
```

The optional `kajenn-asqueel` extra supplies
the Kajenn database integration. The application must set suitable endpoint
authorization and root exposure: permitted roots expose metadata reachable through
relations, not data records. `relation_tree`'s inherited endpoint is not itself an
authentication rule.

For each relation, Asqueel marks the node with `loop=true` when its destination
table is already on that request's path, including its root. Opening or selecting
a marked node does not prompt; automatic search stops at marked loops.

Under GC-000 amendment 11.105, the adapter enriches the resolver's level with
model virtual/composite columns, readable captions, relation direction, type,
logical `fieldpath` and defined field groups. A relation inside a group remains
lazy. A request path includes its visible group names; the adapter validates them
against model metadata before following a relation. A field/group name collision
is rejected. Model metadata, including virtual-column attributes, is exposed to
the application subject to its authorization policy; this is not a permission
filter. Field and relation type codes are supplied as generic tree `badge`
metadata; RO/RM relationship directions supply `badge_color`. A Source-composed
row action opens a dialog showing the node's attributes. Favorites use the PoC's
browser localStorage key per table and a Source/Data Bag view inside the same tree.
Selecting a favorite loads its original path, including missing ancestors. The favorite
action appears on leaf fields only, with a filled heart
and accessible removal label when saved.

The `Internal names` checkbox switches between descriptive captions and technical
node labels; favorites switch to their original field paths. Restored favorite
captions receive the same temporary display filter.

<a id="gp-915-010"></a>
## 010 · Verification and limits

Block ID: **GP-915-010**.

The adapter is integrated into the local common base with the corresponding core;
original working copies remain intact. The complete Python adapter suite passes
337 tests (one skipped), including real SQLite relation metadata and RPC checks.
Core Tree and dbSelect qualification passes Chromium and WebKit; Tree also runs
from file without network requests. Earlier isolated browser checks used the
read-only test_invoice_pg metadata model; this is not integration of the Invoice
application. Public deployment and owner visual acceptance are separate.
Search stops at marked loops. Checkbox state propagates to descendants as they
load; a checked unresolved branch remains in `checkedPaths` until its descendants
are available. As a temporary presentation filter, the adapter removes a leading
`!!` and its optional `[language]` tag from captions; original metadata remains.
Localization design remains open.
Full PoC parity and owner acceptance remain pending; no release or deployment.
