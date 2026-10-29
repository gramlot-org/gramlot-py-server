# Hosting a separate gallery module

Document ID: **GP-025**. Updated: **2026-10-29**.

Block ID: **GP-025-005**.
<a id="gp-025-005"></a>
## 005 · Python host integration

The host owns the mount and resource mapping. `stage(..., modules=...)` passes
trusted catalogue metadata to the gallery; `stage_module` creates launch wrappers
from the separately distributed Python module and returns its asset mapping.

```python
from mobile_application import ROOT, PAGES, ASSETS, CATALOG
from gramlot_py_server.gallery import stage
from gramlot_py_server.gallery.modules import stage_module

mount = '/mobile-application'
registration = dict(catalog=CATALOG, mount=mount,
                    integration=mount + '/device-provider.js', prerequisites=[])
resources = stage(folder, [], '', remote_edit=False, modules=[registration])
module = stage_module(folder / 'mobile-application', pages=PAGES, assets=ASSETS,
                      catalog_file=ROOT / 'catalog.json', prefix=mount,
                      frame_script_url='/gallery/dist/frame.js')
resources.update({mount + path: item for path, item in module.items()})
```

Pass `resources` to the existing Uvicorn `serve(..., assets=resources)` call.
The deployed reverse proxy provides the common HTTPS origin. Pages use the normal
host bootstrap, collection registry, page session and RPC lifecycle. Python
wrappers retain their companion Logic and install the gallery theme bridge.

Block ID: **GP-025-010**.
<a id="gp-025-010"></a>
## 010 · Prerequisites and public resources

`catalog_file` is the original authoritative JSON, served byte-for-byte at
`/mobile-application/catalog.json`. Only catalogue entries whose `requires` are
included in `prerequisites` get page wrappers. Use the identical prerequisites
for `stage` registration and `stage_module`. The module index, available at
`/mobile-application/index`, links directly to eligible pages and explains missing
host prerequisites. Its page list is generated from the same catalogue.

This staging helper follows GCP-110's module layout: Python pages with JS
companions, shared `index.css`, `device-provider.js` and the two synthetic barcode
images. It does not mount an arbitrary repository directory. It must not expose
private APNs keys, local push registrations, user files or Mac configuration.
No push registration callback is inferred. The beta host supplies no
`pushRegistration` or `topLevelEntry`, and keeps Remote Edit disabled.

Block ID: **GP-025-015**.
<a id="gp-025-015"></a>
## 015 · Qualification and deployment

The examples repository contains an opt-in public-artifact preparation script,
Uvicorn entry point and Docker recipe under `deploy/galleries`. The recipe does
not replace the public updater. The owner authorized deployment on 2026-10-25: the public Python gallery now
uses the verified local wheel set and allowlisted module artifact, without a
registry release. Its demo IDE remains read-only at the server boundary. Further
deployments still require explicit authorization. Native hardware,
public TLS and Universal Link association require their own acceptance checks.

Block ID: **GP-025-020**.
<a id="gp-025-020"></a>
## 020 · Common local release preview — 2026-10-29

Use the checked-out core, examples and server together in the Python environment.
Prepare the public mobile artifact with the examples repository's
`deploy/galleries/prepare-mobile.py`; build its provider against the same core
DeviceFrameHost first. The existing Base/Asqueel service database and the Kajenn
SQLite demonstration prerequisites are the same as the database preview.

From this repository:

```sh
python scripts/serve_release_gallery.py \
  --database /tmp/gramlot-preview.sqlite \
  --modules /path/to/prepared-modules \
  --port 61508
```

`--modules` points to the parent of `mobile_application/`; omit it for the ordinary
common preview. The runner uses existing `stage` and `stage_module` contracts,
reads the external catalogue once, mounts its resources at `/mobile-application/`
and registers the same eligible entries with the gallery. It retains Base,
Asqueel selectors, PageStore/WebSocket and chat. Invoice is excluded. Remote Edit
is disabled, including the synthetic-document IDE.

HTTP loopback is sufficient for ordinary browser checks. Native module activation
still requires the same-origin HTTPS frontend and the Capacitor app; this runner
does not bypass that check or install certificates. Production push and top-level
shortcut prerequisites are not supplied. There is no automatic deployment.
