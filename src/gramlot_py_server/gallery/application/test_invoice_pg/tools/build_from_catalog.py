import ast, json, hashlib
from pathlib import Path

root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'catalog.json').read_text())
import argparse
parser=argparse.ArgumentParser(description='Rebuild local model files from the saved PostgreSQL catalog and native declarations.')
parser.add_argument('--native-source',type=Path,required=True)
native=parser.parse_args().native_source
metadata={}; customer_virtual=[]
for schema in ('adm','invc','sys'):
    tree=ast.parse((native/f'{schema}.py').read_text())
    for function in tree.body:
        if not isinstance(function,ast.FunctionDef): continue
        table_name=None; attrs={}; columns={}
        for node in ast.walk(function):
            if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute): continue
            if node.func.attr=='table' and node.args and isinstance(node.args[0],ast.Constant):
                table_name=node.args[0].value
                for kw in node.keywords:
                    if kw.arg in ('caption_field','rowcaption','name_long','name_plural','name_short','lookup','partition_state'):
                        try: attrs[kw.arg]=ast.literal_eval(kw.value)
                        except ValueError: pass
            if node.func.attr=='column' and node.args and isinstance(node.args[0],ast.Constant):
                entry={}
                for kw in node.keywords:
                    if kw.arg in ('name_long','name_short','name_full','group','format','print_width'):
                        try: entry[kw.arg]=ast.literal_eval(kw.value)
                        except ValueError: pass
                columns[node.args[0].value]=entry
        if table_name: metadata[(schema,table_name)]=(attrs,columns)
        if schema=='invc' and function.name=='customer':
            for stmt in function.body:
                if isinstance(stmt,ast.Expr) and any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('formulaColumn','aliasColumn','pyColumn') for n in ast.walk(stmt)):
                    customer_virtual.append(ast.unparse(stmt))

logical={(t['schema'],t['name']):t['name'].removeprefix(t['schema']+'_') for t in catalog['tables']}
dtypes={'int8':'L','int4':'I','bool':'B','bpchar':'C','varchar':'A','date':'D','numeric':'N','text':'T','time':'H','timestamptz':'DHZ','timestamp':'DH'}
actions={'a':'NO ACTION','r':'RESTRICT','c':'CASCADE','n':'SET NULL','d':'SET DEFAULT'}
report=[]; index_aliases=[]
for table in catalog['tables']:
    schema,physical=table['schema'],table['name']; name=logical[(schema,physical)]
    cols=[c for c in catalog['columns'] if (c['schema'],c['table'])==(schema,physical)]
    constraints=[c for c in catalog['constraints'] if (c['schema'],c['table'])==(schema,physical)]
    pk=next(c for c in constraints if c['type']=='p')
    attrs,labels=metadata.get((schema,name),({},{}))
    attrs={**attrs,'pkey':','.join(pk['columns']),'sqlname':physical}
    if table['comment']: attrs['comment']=table['comment']
    names={c['name'] for c in cols}
    if '__del_ts' in names: attrs['logicalDeletionField']='__del_ts'
    if '__is_draft' in names: attrs['draftField']='__is_draft'
    if '__mod_ts' in names: attrs['lastTS']='__mod_ts'
    args=', '.join(f'{k}={v!r}' for k,v in attrs.items())
    lines=['"""Read-only model of '+schema+'.'+physical+'; physical fields from PostgreSQL."""','','','class Table:','    def config_db(self, pkg):',f'        tbl = pkg.table({name!r}, {args})']
    for col in cols:
        a={'dtype':dtypes[col['udt_name']],'notnull':col['is_nullable']=='NO',**labels.get(col['name'],{})}
        if col['character_maximum_length']:
            a['size']=(':' if col['udt_name']=='varchar' else '')+str(col['character_maximum_length'])
        if col['udt_name']=='numeric' and col['numeric_precision'] is not None:
            a['size']=f"{col['numeric_precision']},{col['numeric_scale']}"
        if col['column_default'] is not None:a['sql_pg_default']=col['column_default']
        line=f"        tbl.column({col['name']!r}, "+', '.join(f'{k}={v!r}' for k,v in a.items())+')'
        fks=[f for f in constraints if f['type']=='f' and f['columns']==[col['name']]]
        if len(fks)>1: raise ValueError('Multiple physical FKs require explicit review')
        if fks:
            f=fks[0]; target=f["related_schema"]+'.'+logical[(f['related_schema'],f['related_table'])]+'.'+f['related_columns'][0]
            rel={'foreign_key':True,'constraint_name':f['name'],'onDelete_sql':actions[f['on_delete']],'onUpdate_sql':actions[f['on_update']],'deferrable':f['deferrable'],'initially_deferred':f['initially_deferred'],'indexed':False}
            line+='.relation('+repr(target)+', '+', '.join(f'{k}={v!r}' for k,v in rel.items())+')'
        lines.append(line)
    if any(c['type']=='u' for c in constraints): lines.append('        constraints = tbl.constraints()')
    for c in constraints:
        if c['type']=='u': lines.append(f"        constraints.constraint({c['name']!r}, constraint_type='UNIQUE', columns={','.join(c['columns'])!r})")
    indexes=[i for i in catalog['indexes'] if (i['schema'],i['table'])==(schema,physical) and not i['constraint_index']]
    unique_indexes={}
    for index in indexes:
        key=tuple(index['columns'])
        if key in unique_indexes:
            first=unique_indexes[key]
            if any(index[k]!=first[k] for k in ('unique','method','predicate')):
                raise ValueError('Non-equivalent index definitions need review')
            index_aliases.append({'table':schema+'.'+physical,'kept':first['name'],'equivalent':index['name']})
        else: unique_indexes[key]=index
    indexes=list(unique_indexes.values())
    if indexes: lines.append('        indexes = tbl.indexes()')
    for i in indexes:
        a={'name':i['name'],'columns':','.join(i['columns']),'unique':i['unique'],'method':i['method']}
        if i['predicate']:a['where']=i['predicate']
        lines.append('        indexes.index('+', '.join(f'{k}={v!r}' for k,v in a.items())+')')
    if schema=='invc' and name=='customer':
        lines.append('')
        lines.extend('        '+s.replace("tbl.pyColumn('customer_score', dtype='N', required_columns='$account_name,$email', name_long='Customer Score', group='e_activity.09', method='pyColumn_customer_score')", 'tbl.formulaColumn(\'customer_score\', sql_formula="10 + CASE WHEN COALESCE($email,\'\') <> \'\' THEN 5 ELSE 0 END", dtype=\'N\', name_long=\'Customer Score\', group=\'e_activity.09\')') for s in customer_virtual)

    dest=root/'packages'/schema/'model';dest.mkdir(parents=True,exist_ok=True)
    (dest/f'{name}.py').write_text('\n'.join(lines)+'\n')
    report.append({'model':schema+'.'+name,'table':schema+'.'+physical,'columns':len(cols),'foreign_keys':len([c for c in constraints if c['type']=='f']),'indexes':len(indexes)})
for schema in ('adm','invc','sys'):
    (root/'packages'/schema/'main.py').write_text('class Package:\n    def config_attributes(self):\n        return {"sqlschema": '+repr(schema)+', "sqlprefix": False}\n')
(root/'configure.py').write_text('''"""Existing PostgreSQL database: all connections are read-only, with no schema setup."""
from pathlib import Path
from asqueel import SqlDatabaseConfig

ROOT = Path(__file__).resolve().parent
CONNINFO = "dbname=test_invoice_pg options='-c default_transaction_read_only=on -c statement_timeout=15000'"


class DatabaseConfiguration(SqlDatabaseConfig):
    def main(self, root):
        db = root.db("test_invoice_pg", implementation="postgres", conninfo=CONNINFO)
        packages = db.packages()
        for schema in ("adm", "invc", "sys"):
            packages.package(schema, path=str(ROOT / "packages" / schema), sqlschema=schema, sqlprefix=False)
''')
(root/'equivalent_indexes.json').write_text(json.dumps(index_aliases,indent=2)+'\n')
(root/'model_inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print('Generated tables:',len(report),'Physical columns:',sum(t['columns'] for t in report),'Customer virtual declarations:',len(customer_virtual))
