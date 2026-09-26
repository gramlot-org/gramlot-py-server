# 010 · Usage

Document ID: **GS-010**.

<a id="gs-010-025"></a>
## 025 · Run Python pages with Uvicorn

Install the Gramlot core, then `python -m pip install ".[uvicorn]"` from the
Uvicorn checkout and a Gramlot Python page package. Expose the ASGI application from a Python module:

```python
from gramlot_uvicorn import create_asgi_application
application = create_asgi_application("pages")
```

Run `uvicorn your_module:application`. The pages directory is trusted application
source. The Hello World package provides
`python -m gramlot_example_app.server.uvicorn` as a ready-to-run example.
No Kajenn dependency is required for this profile.
