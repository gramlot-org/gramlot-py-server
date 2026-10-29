"""Explicitly registered database selectors using public Asqueel query/session APIs."""

from dataclasses import dataclass
import re

_MISSING = object()
_FIELD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_REFERENCE = re.compile(r"(?:[A-Za-z_][A-Za-z0-9_]*|(?:@[A-Za-z_][A-Za-z0-9_]*\.)+[A-Za-z_][A-Za-z0-9_]*)\Z")
_INTEGER_DTYPES = {"I", "L", "serial", "serial4", "serial8"}
_TEXT_DTYPES = {"T", "A", "C"}


def _names(value):
    if not isinstance(value, str):
        raise TypeError("Field lists must be comma-separated names")
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _identity(value, expected):
    if type(value) is not expected or (expected is int and abs(value) > 9007199254740991) or value == "":
        raise TypeError("Selection identity must match the registered string or safe integer key")


@dataclass(frozen=True)
class _SelectionTable:
    table: str
    identifier: str
    caption: str
    search: tuple[str, ...]
    columns: tuple[str, ...]
    order_by: tuple[str, ...]
    filters: tuple[str, ...]
    where: str | None
    sqlparams: dict
    identity_type: type
    expressions: dict
    headers: dict


class AsqueelSelect:
    """Adapt configured model fields to the existing Gramlot selector response.

    The application supplies a shared AsqueelDb, not a live SessionDb. Each call
    opens/closes its own session. Registration is trusted application code;
    requests use declared equality filters and registered ordinary projections.
    Auxiliary model fields and relation paths are resolved by Asqueel on demand.
    """

    def __init__(self, database):
        self.database = database
        self.tables = {}

    def register(self, name, table, *, identifier, caption, search=None,
                 columns=(), order_by=(), filters=(), where=None, sqlparams=None):
        if name in self.tables:
            raise ValueError(f"Selection table already registered: {name}")
        search = tuple(search) if search is not None else (caption,)
        columns = tuple(dict.fromkeys((identifier, caption, *columns)))
        ordering = tuple(order_by) or (caption, identifier)
        fields = (identifier, caption, *search, *filters,
                  *(field.removeprefix("-") for field in ordering))
        if not search or any(not isinstance(field, str) or not _FIELD.fullmatch(field) for field in fields):
            raise ValueError("Register simple key, caption, search, filter and ordering fields")
        if any(not isinstance(field, str) or not _REFERENCE.fullmatch(field) for field in columns):
            raise ValueError("Register model fields or relation paths")
        if not set(field.removeprefix("-") for field in ordering).issubset(columns):
            raise ValueError("Ordering fields must be exposed")
        parameters = dict(sqlparams or {})
        if any(name.startswith("selector_") for name in parameters):
            raise ValueError("selector_ parameters are reserved")
        with self.database.session() as session:
            model_table = session.table(table)
            for field in (*fields, *columns):
                if model_table.column(field) is None:
                    raise ValueError(f"Unknown registered field: {field}")
            expressions = tuple(field if field.startswith('@') else '$'+field for field in columns)
            compiled = model_table.query(columns=','.join(expressions), limit=1).compiled.columns
            if len(compiled) != len(columns) or len({col.name for col in compiled}) != len(columns):
                raise ValueError('Ambiguous selector projection')
            projections = {col.name:expr for col,expr in zip(compiled,expressions)}
            headers = {col.name: (model_table.column(field).attributes.get('name_short')
                or model_table.column(field).attributes.get('name_long')
                or model_table.column(field).name) for field,col in zip(columns,compiled)}
            dtype = model_table.column(identifier).dtype
            if dtype not in _INTEGER_DTYPES | _TEXT_DTYPES:
                raise TypeError("Selection identifiers require a text or integer model field")
            identity_type = int if dtype in _INTEGER_DTYPES else str
        self.tables[name] = _SelectionTable(table, identifier, caption, search,
            tuple(projections), ordering, tuple(filters), where, parameters, identity_type,
            projections, headers)
        return self

    def select(self, *, dbtable, _querystring=_MISSING, _id=_MISSING,
               columns=None, hiddenColumns=None, auxColumns=None, order_by=None, limit=10,
               ignoreCase=True, condition=None, weakCondition=False, **filters):
        if dbtable not in self.tables:
            raise ValueError("Unknown selection table")
        if (_querystring is _MISSING) == (_id is _MISSING):
            raise ValueError("Supply exactly one of _querystring or _id")
        if type(limit) is not int or limit < 1:
            raise ValueError("limit must be a positive integer")
        if type(ignoreCase) is not bool:
            raise TypeError("ignoreCase must be boolean")
        definition = self.tables[dbtable]
        auxiliary = tuple(dict.fromkeys(field.removeprefix('$') for field in _names(auxColumns))) if auxColumns is not None else ()
        if any(not _REFERENCE.fullmatch(field) for field in auxiliary):
            raise ValueError('Auxiliary columns must be model fields or relation paths')
        ordering = _names(order_by) if order_by is not None else definition.order_by
        if not ordering or not set(field.removeprefix("-") for field in ordering).issubset(definition.columns):
            raise ValueError("Ordering field is not exposed by this selection")
        if condition is not None and (not isinstance(condition, str) or not condition.strip()):
            raise TypeError("condition must be a nonempty Asqueel expression")
        if type(weakCondition) is not bool and (not isinstance(weakCondition, str) or not weakCondition.strip()):
            raise TypeError("weakCondition must be boolean or an Asqueel expression")
        # As in legacy dbSelect, a weak condition accompanies an explicit condition.
        if condition is None:
            weakCondition = False
            if not set(filters).issubset(definition.filters):
                raise ValueError("Unknown selection filter")
        if any(name.startswith('selector_') or name in definition.sqlparams for name in filters):
            raise ValueError("Selection parameters cannot replace server-owned bindings")
        predicates = [definition.where] if definition.where else []
        parameters = dict(definition.sqlparams)
        for index, (field, value) in enumerate(filters.items()):
            if condition is not None:
                parameters[field] = value
            elif value is None:
                predicates.append(f"${field} IS NULL")
            else:
                name = f"selector_filter_{index}"
                predicates.append(f"${field} = :{name}")
                parameters[name] = value
        if _id is not _MISSING:
            _identity(_id, definition.identity_type)
            predicates.append(f"${definition.identifier} = :selector_id")
            parameters["selector_id"] = _id
        elif not isinstance(_querystring, str):
            raise TypeError("_querystring must be text")

        with self.database.session() as session:
            table = session.table(definition.table)
            projections = dict(definition.expressions)
            headers = dict(definition.headers)
            visible = ()
            if auxiliary:
                expressions = tuple(field if field.startswith('@') else '$'+field for field in auxiliary)
                compiled = table.query(columns=','.join(expressions), limit=1).compiled.columns
                visible = tuple(col.name for col in compiled)
                if len(visible) != len(auxiliary) or len(set(visible)) != len(visible):
                    raise ValueError('Ambiguous selector projection')
                for field, expression, name in zip(auxiliary, expressions, visible):
                    if name in projections and projections[name] != expression:
                        raise ValueError('Ambiguous selector projection')
                    projections[name] = expression
                    column = table.column(field)
                    headers[name] = (column.attributes.get('name_short')
                                     or column.attributes.get('name_long') or column.name)
            projected = tuple(dict.fromkeys((definition.identifier, definition.caption,
                *(_names(columns) if columns is not None else ()),
                *(_names(hiddenColumns) if hiddenColumns is not None else ()), *visible)))
            if not set(projected).issubset(projections):
                raise ValueError("Requested field is not exposed by this selection")

            hard = condition if weakCondition is not True else None
            soft = weakCondition if isinstance(weakCondition, str) else condition if weakCondition is True else None
            errors = None
            def fetch(search=None, *, eligibility=()):
                conditions = [*predicates, *[item for item in eligibility if item], *([search] if search else [])]
                result = table.query(
                    columns=",".join(projections[field] for field in projected),
                    where=" AND ".join(f"({item})" for item in conditions) or None,
                    order_by=",".join(f"${field[1:]} DESC" if field.startswith("-") else f"${field}"
                                      for field in ordering),
                    limit=1 if _id is not _MISSING else limit, sqlparams=parameters,
                ).fetch()
                return [{field: row[field] for field in projected} for row in result]

            if _id is not _MISSING:
                rows = fetch(eligibility=(hard,))
                if not rows and hard:
                    rows = fetch()
                    if rows:
                        errors = "Current value does not fit condition."
            else:
                parameters["selector_query"] = _querystring
                needle = "LOWER(:selector_query)" if ignoreCase else ":selector_query"
                expressions = [f"COALESCE(CAST(${field} AS TEXT),'')" for field in definition.search]
                if ignoreCase:
                    expressions = [f"LOWER({expression})" for expression in expressions]
                prefix = " OR ".join(f"SUBSTR({expr},1,LENGTH({needle})) = {needle}" for expr in expressions)
                contains = " OR ".join(f"REPLACE({expr},{needle},'') <> {expr}" for expr in expressions)
                def search(eligibility):
                    if _querystring == "":
                        return fetch(eligibility=eligibility)
                    return (fetch(prefix, eligibility=eligibility)
                            or fetch(contains, eligibility=eligibility))
                rows = search((hard, soft))
                if not rows and soft:
                    rows = search((hard,))
        for row in rows:
            _identity(row[definition.identifier], definition.identity_type)
            if not isinstance(row[definition.caption], str):
                raise TypeError("Selection caption must be text")
        result = {"rows": rows, "identifier": definition.identifier, "caption": definition.caption}
        if errors:
            result['errors'] = errors
        if auxColumns is not None:
            display = list(dict.fromkeys((definition.caption, *(_names(columns) if columns else ()), *visible)))
            result.update(columns=display, headers=[headers[field] for field in display])
        return result
