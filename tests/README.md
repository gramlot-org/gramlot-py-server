# Native Django integration tests

The active suite exercises the installed native Gramlot Host protocol through
Django's test client, including page/asset delivery, Source transport, owner
isolation, close, malformed requests, capacity, and application failure mapping.
Django and native Gramlot are required; missing imports fail collection.

The extracted PoC Page/ORM suite is preserved in `historical/tests/` and is not
part of the native test gate. It awaits a separate bounded transfer and review.
