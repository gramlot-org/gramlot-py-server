"""Verified collection resources shared by Python hosting integrations."""

from importlib.resources.abc import Traversable
from io import BytesIO, TextIOWrapper
import json
from urllib.parse import quote
from gramlot.collection import collection_graph, _path
from gramlot.server import GramlotFileServer


class _Resource(Traversable):
    """An immutable verified file snapshot, independent of package storage type."""

    def __init__(self, name, content):
        self._name, self._content = name, content

    @property
    def name(self):
        return self._name

    def is_file(self):
        return True

    def is_dir(self):
        return False

    def iterdir(self):
        raise NotADirectoryError(self.name)

    def joinpath(self, *descendants):
        raise NotADirectoryError(self.name)

    def open(self, mode="r", *args, **kwargs):
        if mode == "rb":
            return BytesIO(self._content)
        if mode == "r":
            return TextIOWrapper(BytesIO(self._content), *args, **kwargs)
        raise ValueError("Collection resources are read-only")


class GramlotCollectionResources:
    def __init__(self, *, base_url):
        if (
            not isinstance(base_url, str)
            or not base_url.startswith("/")
            or base_url.startswith("//")
            or base_url.endswith("/")
        ):
            raise ValueError("Collection base_url must be root-relative without a trailing slash")
        self.base_url = base_url
        self._collections = {}
        self._content = {}
        self._registered = False

    def register(self, collections):
        ordered = collection_graph(collections)
        incoming = {collection.name: collection for collection in ordered}
        if self._registered:
            if any(
                name not in self._collections or self._collections[name] != collection
                for name, collection in incoming.items()
            ):
                raise ValueError("Collection registry is fixed; restart to change it")
            return
        namespaces = set()
        verified = {}
        for collection in ordered:
            content = collection.verify()
            verified[collection.name] = content
            for namespace in json.loads(content[collection.commands])["groups"]:
                if namespace in namespaces:
                    raise ValueError(f"Duplicate command namespace: {namespace}")
                namespaces.add(namespace)
        self._content = verified
        self._collections = incoming
        self._registered = True

    def url(self, collection, path):
        if self._collections.get(collection.name) != collection:
            raise ValueError(f"Unregistered collection: {collection.name}; restart the server")
        if self.asset(collection.name, collection.build_id, path) is None:
            raise ValueError(f"Invalid collection browser resource: {collection.name}/{path}")
        return (
            f"{self.base_url}/{quote(collection.name, safe='')}/{collection.build_id[7:]}/"
            + "/".join(quote(p, safe="") for p in path.split("/"))
        )

    def asset(self, name, build_id, path):
        collection = self._collections.get(name)
        if collection is None or collection.build_id != build_id:
            return None
        try:
            _path(path)
        except (ValueError, TypeError):
            return None
        if not path.startswith("assets/") or path not in collection.files:
            return None
        return _Resource(path.rsplit("/", 1)[-1], self._content[name][path])


class _CollectionFileServer(GramlotFileServer):
    def __init__(self, pages, *, collection_resources, **options):
        self.collection_resources = collection_resources
        super().__init__(pages, **options)

    def collection_url(self, collection, path):
        return self.collection_resources.url(collection, path)

    def initialize_collections(self):
        declarations = list(self.collections)
        for page in self.iter_page_classes():
            declarations.extend(self.page_collections(page))
        self.collection_resources.register(collection_graph(declarations))

