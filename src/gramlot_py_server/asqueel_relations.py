"""Expose allowed Asqueel relation-model levels to a Gramlot tree store."""

import re

from genro_bag import Bag
from gramlot.page import endpoint
from gramlot.tree_store import TreeStoreResolver


def _display_caption(value):
    """Temporarily hide the legacy translation marker in displayed captions."""
    return re.sub(r'^!!(?:\[[^\]]+\])?', '', value)


def _relation_table(node):
    joiner = node.attr['joiner']
    relation = {'O': 'one_relation', 'M': 'many_relation'}[joiner['mode']]
    return joiner[relation].rsplit('.', 1)[0]


_COLUMN_KINDS = {
    'formulaColumn': 'formula', 'aliasColumn': 'alias', 'subQueryColumn': 'subquery',
    'bagItemColumn': 'virtual', 'pyColumn': 'python', 'compositeColumn': 'composite',
}


def _group_names(table):
    groups = {key[6:]: value for key, value in table.attributes.items() if key.startswith('group_')}
    groups.update({item.attributes['name']: item.name_long for item in table.values() if item.tag == 'colgroup'})
    return groups


def _group_path(attributes, groups):
    if 'joiner' in attributes:
        joiner = attributes['joiner']
        group = joiner.get({'O': 'one_group', 'M': 'many_group'}[joiner['mode']])
    else:
        group = attributes.get('group')
    if not group:
        return []
    parts = group.lstrip('*_').split('.')
    if parts[-1].isdigit():
        parts.pop()
    return parts if parts and parts[0] in groups else []


class AsqueelRelations:
    """Opt in to relation metadata by declaring allowed root tables on the page."""

    relation_roots = ()
    relation_database = None

    @endpoint
    def relation_tree(self, table, path='', label=None, attributes=None):
        if not isinstance(self.relation_roots, tuple):
            raise TypeError('relation_roots must be a tuple')
        if table not in self.relation_roots:
            raise ValueError('Relation root is not exposed')
        if not isinstance(path, str):
            raise TypeError('Relation path must be a string')
        steps = path.split('.') if path else []
        if any(not step for step in steps):
            raise ValueError('Invalid relation path')
        model = self.async_db(self.relation_database).model
        root_table = model.table(table)
        current_table = root_table
        current = root_table.newRelationResolver(cacheTime=-1)()
        visited = {table}
        captions = []
        relation_steps = []
        group_steps = []
        for step in steps:
            if not step.startswith('@'):
                group_steps.append(step)
                continue
            node = current.get_node(step)
            if node is None or node.resolver is None:
                raise ValueError('Unknown relation path')
            if group_steps != _group_path(node.attr, _group_names(current_table)):
                raise ValueError('Invalid relation path')
            group_steps = []
            relation_steps.append(step)
            destination = _relation_table(node)
            current_table = model.table(destination)
            captions.append(_display_caption(current_table.name_long))
            visited.add(destination)
            current = node.get_value()
        if group_steps:
            raise ValueError('Invalid relation path')
        result = Bag()
        for node in current.get_nodes():
            value = TreeStoreResolver() if node.resolver is not None else None
            attributes = dict(node.attr)
            if node.resolver is not None:
                destination = _relation_table(node)
                caption = _display_caption(model.table(destination).name_long)
                attributes['node_kind'] = 'relation'
                attributes['dtype'] = {'O': 'RO', 'M': 'RM'}[attributes['joiner']['mode']]
                attributes['relation_direction'] = {'O': 'ascending', 'M': 'descending'}[attributes['joiner']['mode']]
                attributes['badge_color'] = {'O': '#218544', 'M': '#246ed4'}[attributes['joiner']['mode']]
                group = attributes['joiner'].get({'O': 'one_group', 'M': 'many_group'}[attributes['joiner']['mode']])
                if group is not None:
                    attributes['group'] = group
                if destination in visited:
                    attributes['loop'] = True
            else:
                caption = _display_caption(current_table.columns[node.label].name_long)
                attributes['node_kind'] = 'column'
            attributes.update(caption=caption, fullcaption='.'.join([*captions, caption]),
                              fieldpath='.'.join([*relation_steps, node.label]), root_table_caption=_display_caption(root_table.name_long),
                              badge=attributes['dtype'])
            result.set_item(node.label, value, _attributes=attributes)
        for column in [*current_table.virtual_columns.values(), *current_table.composites.values()]:
            caption = _display_caption(column.name_long)
            attributes = dict(column.attributes, dtype=column.dtype, caption=caption,
                              fullcaption='.'.join([*captions, caption]),
                              fieldpath='.'.join([*relation_steps, column.name]), node_kind='column',
                              column_kind=_COLUMN_KINDS[column.tag], root_table_caption=_display_caption(root_table.name_long),
                              badge=column.dtype)
            result.set_item(column.name, None, _attributes=attributes)
        groups = _group_names(current_table)
        grouped = Bag()
        for node in sorted(result.get_nodes(), key=lambda item: (item.attr.get('group') or '').split('.')):
            target = grouped
            parts = _group_path(node.attr, groups)
            for index, part in enumerate(parts):
                group_node = target.get_node(part)
                if group_node is None:
                    name = groups.get('.'.join(parts[:index + 1]), part)
                    target.set_item(part, Bag(), caption=_display_caption(name), node_kind='group')
                    group_node = target.get_node(part)
                target = group_node.get_value(static=True)
                if not isinstance(target, Bag):
                    raise ValueError('Field and group names collide')
            if target.get_node(node.label) is not None:
                raise ValueError('Field and group names collide')
            target.set_item(node.label, node.resolver if node.resolver is not None else node.get_value(static=True),
                            _attributes=dict(node.attr))
        return grouped


def relation_tree(parent, *, datapath, table, tree_attributes=None, **attributes):
    """Declare an Asqueel relation tree using the page's relation_tree endpoint."""
    from genro_bag import Bag
    from gramlot.page import tree_store

    pane = tree_store(parent, datapath=datapath, method='relation_tree', params={'table': table},
                      tree_attributes={'labelAttribute': 'caption', 'selectedPath': '^.selection',
                                       **(tree_attributes or {}), 'internalNames': '^.internalNames',
                                       'favorites': '^.favorites', 'favoritesLabel': 'Favorites'}, **attributes)
    pane.dataSetter('.internalNames', False)
    label = pane.html_label()
    label.input(type='checkbox', value='^.internalNames')
    label.span('Internal names')
    pane.value.move(len(pane.value.get_nodes()) - 1, 0)
    [tree] = [node for node in pane.value.get_nodes() if node.node_tag == 'tree']
    favorite_key = f'gramlot.relationTree.favorites.v1:{table}'
    pane.dataSetter('.favorites', Bag())
    pane.dataController(func='treeFavoritesMount', favoriteKey=favorite_key, _onBuilt=True)
    actions = tree.rowActions(position='end', actionState='treeFavoriteActionState', state='^.favorites')
    actions.button(rowAction='favorite', icon='♡', title='Add favorite').dataController(
        func='treeFavoriteToggle', favoriteKey=favorite_key)
    actions.button(icon='ⓘ', title='Inspect attributes').dataController(func='treeInspect')
    return pane
