# 005 · Architecture

Document ID: **GS-005**.

<a id="gs-005-025"></a>
## 025 · Python/Uvicorn profile

`gramlot_uvicorn.NativeHtmlASGI` connects a trusted Python Page directory to the
neutral core `Host`. `create_asgi_application` constructs the ASGI callable.
It serves the packaged runtime and Page main/source/close endpoints. Uvicorn is
an optional runner dependency; neither Uvicorn nor Kajenn is imported by the
adapter.
