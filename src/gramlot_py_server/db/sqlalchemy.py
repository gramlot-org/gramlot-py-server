"""Registered SQLAlchemy selectors, independent of the HTTP adapter."""

from dataclasses import dataclass

from sqlalchemy import String, cast, func, or_, select

_MISSING = object()


@dataclass(frozen=True)
class SelectionTable:
    table: object
    identifier: str
    caption: str
    search: tuple[str, ...]
    columns: tuple[str, ...]
    order_by: tuple[str, ...]
    filters: tuple[str, ...]


def _names(value):
    if not isinstance(value, str):
        raise TypeError("Field lists must be comma-separated names")
    return tuple(part.strip() for part in value.split(",") if part.strip())


class SQLAlchemySelect:
    """Expose only explicitly registered tables and fields through data RPC.

    The application owns the Engine and its disposal. Each call owns one connection.
    Dedicated endpoints may add SQLAlchemy predicates with ``where``.
    """

    def __init__(self, engine):
        self.engine = engine
        self.tables = {}

    def register(self, name, table, *, identifier, caption, search=None,
                 columns=(), order_by=(), filters=()):
        if name in self.tables:
            raise ValueError(f"Selection table already registered: {name}")
        search = tuple(search) if search is not None else (caption,)
        columns = tuple(dict.fromkeys((identifier, caption, *columns)))
        order_by = tuple(order_by) or (caption, identifier)
        if not search or not set(field.removeprefix("-") for field in order_by).issubset(columns):
            raise ValueError("Search is required; ordering fields must be exposed")
        for field in (*columns, *search, *(field.removeprefix("-") for field in order_by), *filters):
            if field not in table.c:
                raise ValueError(f"Unknown registered field: {field}")
        self.tables[name] = SelectionTable(table, identifier, caption, search,
                                           columns, order_by, tuple(filters))
        return self

    def select(self, *, dbtable, _querystring=_MISSING, _id=_MISSING,
               columns=None, hiddenColumns=None, auxColumns=None, order_by=None, limit=10,
               ignoreCase=True, where=(), condition=None, weakCondition=False, **filters):
        if condition is not None or weakCondition is not False:
            raise ValueError("condition and weakCondition are Asqueel-only capabilities")
        if dbtable not in self.tables:
            raise ValueError("Unknown selection table")
        if (_querystring is _MISSING) == (_id is _MISSING):
            raise ValueError("Supply exactly one of _querystring or _id")
        if type(limit) is not int or limit < 1:
            raise ValueError("limit must be a positive integer")
        if type(ignoreCase) is not bool:
            raise TypeError("ignoreCase must be boolean")
        definition = self.tables[dbtable]
        table = definition.table
        auxiliary = _names(auxColumns) if auxColumns is not None else ()
        projected = tuple(dict.fromkeys((definition.identifier, definition.caption,
                          *(_names(columns) if columns is not None else ()),
                          *(_names(hiddenColumns) if hiddenColumns is not None else ()), *auxiliary)))
        if not set(projected).issubset(definition.columns):
            raise ValueError("Requested field is not exposed by this selection")
        ordering = _names(order_by) if order_by is not None else definition.order_by
        if not ordering or not set(field.removeprefix("-") for field in ordering).issubset(definition.columns):
            raise ValueError("Ordering field is not exposed by this selection")
        if not set(filters).issubset(definition.filters):
            raise ValueError("Unknown selection filter")
        predicates = list(where)
        predicates.extend(table.c[field] == value for field, value in filters.items())
        if _id is not _MISSING:
            if not ((type(_id) is int and abs(_id) <= 9007199254740991)
                    or (isinstance(_id, str) and _id)):
                raise TypeError("Selection identity must be a non-empty string or safe integer")
            # SQL engines may coerce '0' to 0. Enforce the wire identity type first.
            expected = table.c[definition.identifier].type.python_type
            if type(_id) is not expected:
                raise TypeError("Selection identity type does not match the registered key")
            predicates.append(table.c[definition.identifier] == _id)
        else:
            if not isinstance(_querystring, str):
                raise TypeError("_querystring must be text")
            query = _querystring.lower() if ignoreCase else _querystring
        statement = select(*(table.c[field] for field in projected)).where(*predicates)
        statement = statement.order_by(*(table.c[field[1:]].desc() if field.startswith("-")
                                          else table.c[field] for field in ordering))
        statement = statement.limit(1 if _id is not _MISSING else limit)
        with self.engine.connect() as connection:
            def fetch(predicate=None):
                selected = statement if predicate is None else statement.where(predicate)
                return [dict(row) for row in connection.execute(selected).mappings()]
            if _id is not _MISSING or _querystring == "":
                rows = fetch()
            else:
                expressions = [func.coalesce(cast(table.c[field], String), "") for field in definition.search]
                if ignoreCase:
                    expressions = [func.lower(expression) for expression in expressions]
                # Literal SQL operations supported by both PostgreSQL and SQLite;
                # wildcard characters are never interpreted as patterns.
                rows = fetch(or_(*(func.substr(expr, 1, func.length(query)) == query for expr in expressions)))
                if not rows:
                    rows = fetch(or_(*(func.replace(expr, query, "") != expr for expr in expressions)))
        for row in rows:
            key = row[definition.identifier]
            if not ((type(key) is int and abs(key) <= 9007199254740991)
                    or (isinstance(key, str) and key)):
                raise TypeError("Unsupported selection identity")
            if not isinstance(row[definition.caption], str):
                raise TypeError("Selection caption must be text")
        result = {"rows": rows, "identifier": definition.identifier, "caption": definition.caption}
        if auxColumns is not None:
            display = list(dict.fromkeys((definition.caption, *(_names(columns) if columns else ()), *auxiliary)))
            result.update(columns=display, headers=[definition.table.c[field].info.get('label', field) for field in display])
        return result
