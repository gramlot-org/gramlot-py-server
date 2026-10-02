# 045 · inspector: concise guide

Document ID: **GD-045**.

[Expanded guide](../docs/045-inspector.md).

<a id="gd-045-005"></a>

## 005 · Preview status

Block ID: **GD-045-005**.

Experimental API/design tool; behavior described is intended and may have bugs.

<a id="gd-045-010"></a>

## 010 · Open the Inspector

Block ID: **GD-045-010**.

Bakery `/products/explore/` → magnifier Open inspector. Data/Source trees and Properties, movable/resizable panel.

<a id="gd-045-015"></a>

## 015 · Three different views

Block ID: **GD-045-015**.

Data: runtime Bag. Source: runtime UI declaration tree. Separate Python CodeMirror viewer: read-only file. Inspector is not the IDE or a Python file editor.

<a id="gd-045-020"></a>

## 020 · Try a Data edit

Block ID: **GD-045-020**.

Data/detail/title → edit value → leave property row. Bound bread title updates; later service data can replace it.

<a id="gd-045-025"></a>

## 025 · Try a Source edit

Block ID: **GD-045-025**.

Source/h1_0 → edit value → leave property row. Heading updates. Typed scalar/attribute editors, add/delete attributes. Complex values read-only as a whole; expand to scalar children.

<a id="gd-045-030"></a>

## 030 · Lifetime and effects

Block ID: **GD-045-030**.

Runtime edits do not write Python files. Reload restores server/declaration state. Changes may trigger bindings/controllers/RPCs; persistence uses services and permissions. source_inspection controls availability; table admin disables it by default.

<a id="gd-045-035"></a>

## 035 · Screenshot scope

Block ID: **GD-045-035**.

Real Bakery/core 0.1.5 screenshots, 2026-09-16. Chromium Data/Source changes and reload restoration exercised; no guarantee of general correctness.
