"""Copy every row of the Base physical subset from a read-only PostgreSQL snapshot.

Run with --backend asqueel|sqlalchemy|django. Existing target databases are refused.
Only schema metadata and aggregate verification statuses are emitted.
"""
import argparse
import hashlib
import json
from importlib.resources import files

import psycopg
from psycopg import sql

BACKENDS = ('asqueel', 'sqlalchemy', 'django')
SOURCE = 'test_invoice_pg_xl'
READ_ONLY = '-c default_transaction_read_only=on -c statement_timeout=120000'


def specification():
    return json.loads(files('gramlot_examples').joinpath('base/model.json').read_text())


def database_name(backend):
    if backend not in BACKENDS:
        raise ValueError('Unsupported Base database adapter')
    return f'gramlot_base_{backend}'


def table_name(table):
    return sql.Identifier('invc', table['physical'])


def selected_columns(table):
    return sql.SQL(', ').join(sql.Identifier(c['name']) for c in table['columns'])


def source_metadata(connection, specification):
    """Refuse drift before creating a copy; never run DDL on the source."""
    for table in specification['tables'].values():
        rows = connection.execute('''SELECT column_name, udt_name, is_nullable,
            character_maximum_length, numeric_precision, numeric_scale
            FROM information_schema.columns WHERE table_schema='invc' AND table_name=%s''',
            (table['physical'],)).fetchall()
        actual = {r[0]: r[1:] for r in rows}
        for column in table['columns']:
            expected = tuple(column[k] for k in ('udt_name','is_nullable',
                'character_maximum_length','numeric_precision','numeric_scale'))
            if actual.get(column['name']) != expected:
                raise ValueError(f"Source schema changed: {table['physical']}.{column['name']}")


def create_schema(target, specification):
    target.execute('CREATE SCHEMA invc')
    types = {'varchar':'varchar', 'bpchar':'char', 'text':'text', 'int4':'integer',
             'numeric':'numeric', 'date':'date'}
    for table in specification['tables'].values():
        declarations = []
        for c in table['columns']:
            dtype = types[c['udt_name']]
            if c['character_maximum_length']:
                dtype += f"({c['character_maximum_length']})"
            if c['udt_name'] == 'numeric':
                dtype += f"({c['numeric_precision']},{c['numeric_scale']})"
            declarations.append(sql.SQL('{} {}{}').format(sql.Identifier(c['name']),
                sql.SQL(dtype), sql.SQL(' NOT NULL' if c['is_nullable']=='NO' else '')))
        target.execute(sql.SQL('CREATE TABLE {} ({})').format(table_name(table), sql.SQL(', ').join(declarations)))


def digest(connection, table):
    """Hash COPY's ordered text stream; row values never reach logs or files."""
    key = next(c['columns'][0] for c in table['constraints'] if c['type']=='p')
    query = sql.SQL('COPY (SELECT {} FROM {} ORDER BY {}) TO STDOUT').format(
        selected_columns(table), table_name(table), sql.Identifier(key))
    value = hashlib.sha256()
    with connection.cursor().copy(query) as stream:
        for chunk in stream:
            value.update(chunk)
    return value.hexdigest()


def verify(source, target, specification):
    report = {'source_read_only': source.execute('SHOW transaction_read_only').fetchone()[0],
              'tables': {}, 'relations': {}}
    if report['source_read_only'] != 'on':
        raise RuntimeError('Source must remain read-only')
    for name, table in specification['tables'].items():
        count = sql.SQL('SELECT count(*) FROM {}').format(table_name(table))
        a = source.execute(count).fetchone()[0]
        b = target.execute(count).fetchone()[0]
        equal = digest(source, table) == digest(target, table)
        if a != b or not equal:
            raise RuntimeError(f'Copy verification failed for {name}')
        report['tables'][name] = {'source_rows':a, 'copy_rows':b, 'all_values_equal':equal}
        for constraint in table['constraints']:
            if constraint['type'] != 'f':
                continue
            field = sql.Identifier(constraint['columns'][0])
            referenced = sql.Identifier('invc', constraint['related_table'])
            refkey = sql.Identifier(constraint['related_columns'][0])
            query = sql.SQL('SELECT count(*) FROM {} c LEFT JOIN {} p ON c.{}=p.{} '
                            'WHERE c.{} IS NOT NULL AND p.{} IS NULL').format(
                                table_name(table), referenced, field, refkey, field, refkey)
            orphans = target.execute(query).fetchone()[0]
            if orphans:
                raise RuntimeError(f'Orphan references in {name}')
            report['relations'][name+'.'+constraint['columns'][0]] = {'orphans':orphans}
    return report


def copy_dataset(backend):
    name = database_name(backend)
    spec = specification()
    # PostgreSQL enforces read-only for every source transaction. All queries share
    # one repeatable snapshot, including counts and the equality verification.
    with psycopg.connect(dbname=SOURCE, options=READ_ONLY) as source:
        source.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        source_metadata(source, spec)
        with psycopg.connect(dbname='postgres', autocommit=True) as admin:
            if admin.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone():
                raise ValueError(f'Target {name} already exists; no changes made')
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
        # No cleanup/drop path: a failed attempt leaves a dedicated database for inspection.
        with psycopg.connect(dbname=name) as target:
            if target.execute('SELECT current_database()').fetchone()[0] != name or name == SOURCE:
                raise RuntimeError('Refusing an unexpected destination')
            create_schema(target, spec)
            for table in spec['tables'].values():
                out = sql.SQL('COPY {} ({}) TO STDOUT').format(table_name(table), selected_columns(table))
                into = sql.SQL('COPY {} ({}) FROM STDIN').format(table_name(table), selected_columns(table))
                with source.cursor().copy(out) as reader, target.cursor().copy(into) as writer:
                    for chunk in reader:
                        writer.write(chunk)
            for table in spec['tables'].values():
                for constraint in table['constraints']:
                    target.execute(sql.SQL('ALTER TABLE {} ADD CONSTRAINT {} {}').format(
                        table_name(table),sql.Identifier(constraint['name']),sql.SQL(constraint['definition'])))
            report = verify(source, target, spec)
            report['database'] = name
            return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=BACKENDS, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        with psycopg.connect(dbname=SOURCE, options=READ_ONLY) as source, psycopg.connect(
                dbname=database_name(args.backend), options=READ_ONLY) as target:
            source.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            print(json.dumps(verify(source, target, specification()), indent=2))
    else:
        print(json.dumps(copy_dataset(args.backend), indent=2))


if __name__ == '__main__':
    main()
