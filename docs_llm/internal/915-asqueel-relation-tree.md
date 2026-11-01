# 915 · Asqueel relation tree

Document ID: **GP-915**. Status: implemented in isolated development clone; owner acceptance pending.
[Full counterpart](../../docs/internal/915-asqueel-relation-tree.md).

<a id="gp-915-005"></a>
## 005 · Kajenn integration

Block ID: **GP-915-005**.

`AsqueelRelations` opt-in page mixin exposes `relation_tree` only for the
`relation_roots` tuple (empty by default); `relation_database` selects the Kajenn
DB. A request-scoped `async_db` model supplies one relation level per call; paths
follow actual resolver edges with no fixed depth limit. The response replaces Asqueel's server
resolvers with inert Gramlot TreeStoreResolver wire descriptions. Incoming label
and attributes do not authorize anything. The Python `relation_tree` composition
uses TreeStoreLogic and the tree collection; optional `kajenn-asqueel` installs
integration requirements. Applications must authorize access to roots and
reachable metadata; endpoint has no authentication rule of its own.
Re-export `TreeStoreLogic` as `Logic` or delegate `treeStoreMount`, `treeInspect`
and `treeInspectClose`; do not extend it.
Asqueel marks a relation node `loop=true` when its destination table is already
on the same path, including the root. Opening it does not prompt; automatic
search stops at loops.
Under GC-000 amendment 11.105 the adapter adds virtual/composite columns,
captions, type/direction, logical field paths and defined groups. Grouped
relations stay lazy; request group paths are validated against model metadata,
and group/field name collisions fail. Model metadata exposure requires application
authorization. Field/relation type codes use generic `badge` metadata; RO/RM
directions supply `badge_color`. A Source row action opens an attribute-inspection
dialog. Favorites persist per table in browser localStorage and appear inside the
same tree using a Source/Data Bag; selection loads the original path's ancestors.
The favorite action appears only on leaves, with a filled heart and accessible
removal label for saved fields.

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
Search stops at marked loops. Checkbox state propagates when descendants load;
`checkedPaths` holds the unresolved branch until descendants are available.
The adapter temporarily removes a leading `!!` and optional `[language]` tag
from display captions; original metadata remains until localization is designed.
Full PoC parity and owner acceptance remain pending; no release or deployment.
