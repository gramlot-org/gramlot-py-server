"""Explicit Django ORM selectors, independent of the HTTP adapter."""
from dataclasses import dataclass
from django.db import models
from django.db.models import Q

_MISSING = object()


def _names(value):
    if not isinstance(value, str):
        raise TypeError('Field lists must be comma-separated names')
    return tuple(part.strip() for part in value.split(',') if part.strip())


@dataclass(frozen=True)
class SelectionTable:
    model: type
    identifier: str
    caption: str
    search: tuple[str, ...]
    columns: tuple[str, ...]
    order_by: tuple[str, ...]
    filters: tuple[str, ...]
    identity_type: type
    annotations: dict


class DjangoSelect:
    """Query only registered models and fields using the configured Django connection."""

    def __init__(self, alias='default'):
        self.alias = alias
        self.tables = {}

    def register(self, name, model, *, identifier, caption, search=None,
                 columns=(), order_by=(), filters=(), annotations=None):
        if name in self.tables:
            raise ValueError('Selection table already registered')
        annotations = dict(annotations) if annotations is not None else {}
        if any('__' in name for name in annotations):
            raise ValueError('Register simple annotation names')
        # Let Django validate native expressions and reject model-field collisions.
        model.objects.annotate(**annotations)
        search = tuple(search) if search is not None else (caption,)
        columns = tuple(dict.fromkeys((identifier, caption, *columns)))
        ordering = tuple(order_by) or (caption, identifier)
        if not search or not set(f.removeprefix('-') for f in ordering).issubset(columns):
            raise ValueError('Search is required; ordering fields must be exposed')
        for field in (*columns, *search, *filters, *(f.removeprefix('-') for f in ordering)):
            if '__' in field:
                raise ValueError('Register simple model fields')
            if field not in annotations:
                model._meta.get_field(field)
        key = model._meta.get_field(identifier)
        if isinstance(key, models.IntegerField):
            identity_type = int
        elif isinstance(key, (models.CharField, models.TextField)):
            identity_type = str
        else:
            raise TypeError('Selection identifiers require a text or integer model field')
        self.tables[name] = SelectionTable(model, identifier, caption, search, columns,
                                         ordering, tuple(filters), identity_type, annotations)
        return self

    def select(self, *, dbtable, _querystring=_MISSING, _id=_MISSING,
               columns=None, hiddenColumns=None, auxColumns=None, order_by=None, limit=10,
               ignoreCase=True, **filters):
        if dbtable not in self.tables:
            raise ValueError('Unknown selection table')
        if (_querystring is _MISSING) == (_id is _MISSING):
            raise ValueError('Supply exactly one of _querystring or _id')
        if type(limit) is not int or limit < 1:
            raise ValueError('limit must be a positive integer')
        if type(ignoreCase) is not bool:
            raise TypeError('ignoreCase must be boolean')
        definition = self.tables[dbtable]
        auxiliary = _names(auxColumns) if auxColumns is not None else ()
        projected = tuple(dict.fromkeys((definition.identifier, definition.caption,
            *(_names(columns) if columns is not None else ()),
            *(_names(hiddenColumns) if hiddenColumns is not None else ()), *auxiliary)))
        if not set(projected).issubset(definition.columns):
            raise ValueError('Requested field is not exposed by this selection')
        ordering = _names(order_by) if order_by is not None else definition.order_by
        if not ordering or not set(f.removeprefix('-') for f in ordering).issubset(definition.columns):
            raise ValueError('Ordering field is not exposed by this selection')
        if not set(filters).issubset(definition.filters):
            raise ValueError('Unknown selection filter')
        queryset = definition.model.objects.using(self.alias).annotate(
            **definition.annotations).filter(**filters).order_by(*ordering)
        if _id is not _MISSING:
            if type(_id) is not definition.identity_type or _id == '' or (type(_id) is int and abs(_id)>9007199254740991):
                raise TypeError('Selection identity does not match the registered key')
            rows = list(queryset.filter(**{definition.identifier:_id}).values(*projected)[:1])
        elif not isinstance(_querystring, str):
            raise TypeError('_querystring must be text')
        elif not _querystring:
            rows = list(queryset.values(*projected)[:limit])
        else:
            def fetch(operation):
                predicate = Q()
                for field in definition.search:
                    predicate |= Q(**{field+'__'+operation:_querystring})
                return list(queryset.filter(predicate).values(*projected)[:limit])
            rows = fetch('istartswith' if ignoreCase else 'startswith')
            if not rows:
                rows = fetch('icontains' if ignoreCase else 'contains')
        for row in rows:
            key = row[definition.identifier]
            if type(key) is not definition.identity_type or key == '' or (type(key) is int and abs(key)>9007199254740991):
                raise TypeError('Unsupported selection identity')
            if not isinstance(row[definition.caption], str):
                raise TypeError('Selection caption must be text')
        result = {'rows': rows, 'identifier':definition.identifier, 'caption':definition.caption}
        if auxColumns is not None:
            display = list(dict.fromkeys((definition.caption, *(_names(columns) if columns else ()), *auxiliary)))
            result.update(columns=display, headers=[field if field in definition.annotations else str(definition.model._meta.get_field(field).verbose_name) for field in display])
        return result
