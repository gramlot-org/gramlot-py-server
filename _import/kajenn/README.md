# gramlot-kajenn

Kajenn hosts native Gramlot Pages through `genro_asgi.BaseServer`. The Python
distribution is `gramlot-kajenn`; its import package is `gramlot_kajenn`.
`KajennNativeHtmlApplication` owns the Kajenn mount and worker integration.
Generic raw ASGI hosting belongs to `gramlot-minimal` (currently a local development checkout).
The upstream server dependency is still distributed as `genro-asgi` and imported
as `genro_asgi`.

## Native Hello World

Install the locally built Gramlot, gramlot-minimal and gramlot-kajenn wheels, then
the Hello World application's Python host dependencies. The maintained launcher is:

```sh
python -m gramlot_example_app.server.kajenn
```

Open <http://127.0.0.1:8000/page/>. See [GA-010](docs/010-native-html.md)
for the supported behavior and limits. This development branch is not a new
package release or deployment.

## Historical PoC material

The older `GramlotApplication`, GenroPy `GnrApp` integration, CLI and database
examples remain as historical experiments. They require the PoC Page/recipe/RPC
APIs absent from the clean Gramlot core and are outside the native profile. Their
original documentation is retained in [GA-005](docs/005-genro-asgi-legacy.md),
with [SPECIFICATION.md](SPECIFICATION.md) recording the original scope. The old
`gramlot-genro-asgi` package and CLI names in those records refer to that
historical profile; the current distribution does not install a CLI entry point.

Maintained documentation uses the classic Read the Docs theme. Work remains on
`develop` until verified and accepted; no package publication or deployment is
implied by this change.


## Shared examples and documentation

Gramlot is the primary source of framework documentation, teaching examples,
runner and theme. This integration is a downstream consumer: it owns hosting
and setup, and must use the shared examples through its Gramlot dependency
without maintaining a copied suite. Kajenn executes the shared Python pages inside its server application; generic ASGI hosting belongs to Minimal.

Read the Gramlot manual first, then this integration's guide. Update the Gramlot
dependency and restart or regenerate exports to receive example changes.
Uniform packaging and launch commands across all integrations are still pending;
this describes the agreed model, not a completed rollout. See
[shared example ownership](docs/010-native-html.md#ga-010-020) for details.
