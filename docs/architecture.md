# Integration scope

Genro ASGI hosting without a database, followed by an optional Genropy database profile.

Keep Genro ASGI hosting in this consumer repository or its host integration. Do not introduce a Genro ASGI dependency into the Gramlot core. Review the existing genro-asgi[gui] integration before designing application hosting.

The current artifact is a package scaffold. Hosting, request handling and
database integration have not been implemented here. Application examples
will use Python-authored Gramlot pages and explicit host configuration.
