# 040 · admin-spa: concise guide

Document ID: **GD-040**.

[Expanded guide](../docs/040-admin-spa.md).

<a id="gd-040-005"></a>

## 005 · Preview status

Block ID: **GD-040-005**.

Experimental API/design preview. Intended behavior may have bugs; not a full Django/Wagtail admin replacement.

<a id="gd-040-010"></a>

## 010 · Try the Bakery example

Block ID: **GD-040-010**.

Use `/spa_admin/tables/`; active staff and model permissions required. Select breads/countries, double-click or Enter; New where allowed, Save persists, Cancel closes draft.

<a id="gd-040-015"></a>

## 015 · Declare the exposed models

Block ID: **GD-040-015**.

Subclass DjangoTablesPage, explicitly declare table_fields. Exposure does not grant permissions. Search limit: 100 rows.

<a id="gd-040-020"></a>

## 020 · How forms are generated

Block ID: **GD-040-020**.

Restricted ModelForm → Gramlot form/formlet and record Data bindings. FK/O2O: dbSelect; textarea: textBoxArea; other supported scalars: textBox. Related grids read-only.

<a id="gd-040-025"></a>

## 025 · Validation and saving

Block ID: **GD-040-025**.

validate_record_field RPC validates current draft without saving. table_forms supports custom ModelForm clean methods and Django validation. Save validates again with permissions and transaction/row lock. Clean methods must be side-effect-free; drafts may be incomplete. Current error presentation can duplicate messages.

<a id="gd-040-030"></a>

## 030 · Boundaries and permissions

Block ID: **GD-040-030**.

Relation queryset and target view permissions apply. Related fields must be exposed; parent saved and parent/target readable; 100-row limit. M2M preserved. No delete UI, full widget mapping or Wagtail workflow/tree editing. Table Inspector disabled by default.

<a id="gd-040-035"></a>

## 035 · Screenshot scope

Block ID: **GD-040-035**.

Real Bakery/core 0.1.5 screenshots, 2026-09-16. Country open, required-field error, Cancel exercised without saving; narrow evidence, not general correctness.
