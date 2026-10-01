# 005 · Architecture

Document ID: **GS-005**.

[Paired view](../docs/005-architecture.md).

<a id="gs-005-025"></a>

## 025 · Python/Uvicorn profile

Block ID: **GS-005-025**.

`gramlot_uvicorn.NativeHtmlASGI` connects a trusted Python Page directory to the
core `FileHost`, built with root-relative runtime, main, source and close URLs.
The adapter passes `mount_path` to `open_page` as `prefix`; the core adds it
once to root-relative URLs. `create_asgi_application` constructs the ASGI callable.
It serves the packaged runtime and Page main/source/close endpoints. Uvicorn is
an optional runner dependency; neither Uvicorn nor Kajenn is imported by the
adapter.

<a id="gs-005-035"></a>

## 035 · Companions and Page.css files

Block ID: **GS-005-035**.

GET and HEAD serve a file of the pages folder whose name ends in `.css` or
`_aux.js`: the `FileHost` companions `foo.css` and `foo_aux.js`, and `Page.css`
files placed in the folder. The real path of the file must stay below the pages
folder, as in `FileHost.url`. Every other file, including `.py` and `.md`,
answers 404. A `Page.css` URL outside the pages folder is an asset of the
application, which serves it itself.
