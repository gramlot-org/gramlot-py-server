# 005 · Architecture

Document ID: **GS-005**.

<a id="gs-005-025"></a>
## 025 · Python/Uvicorn profile

`gramlot_uvicorn.NativeHtmlASGI` connects a trusted Python Page directory to the
core `FileHost`, built with root-relative runtime, main, source and close URLs.
The adapter passes `mount_path` to `open_page` as `prefix`; the core adds it
once to root-relative URLs. `create_asgi_application` constructs the ASGI callable.
It serves the packaged runtime and Page main/source/close endpoints. Uvicorn is
an optional runner dependency; neither Uvicorn nor Kajenn is imported by the
adapter.
