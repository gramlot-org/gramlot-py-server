"""Build one native selector service over its dedicated read-only PostgreSQL copy."""
import atexit
from pathlib import Path
from .copy_dataset import database_name, READ_ONLY


def configure_django():
    """Configure the Django ORM before importing the concrete models."""
    import django
    from secrets import token_urlsafe
    from django.conf import settings
    settings.configure(DATABASES={'default':{
        'ENGINE':'django.db.backends.postgresql', 'NAME':database_name('django'),
        'OPTIONS':{'options':READ_ONLY}}}, INSTALLED_APPS=[],
        SECRET_KEY=token_urlsafe(32), ALLOWED_HOSTS=['127.0.0.1','localhost'],
        MIDDLEWARE=[])
    django.setup()


def create_database(backend):
    name = database_name(backend)
    if backend == 'asqueel':
        from asqueel import AsqueelDb, SqlDatabaseConfig
        from gramlot_py_server.db.asqueel import AsqueelSelect
        class DatabaseConfiguration(SqlDatabaseConfig):
            def main(self, root):
                db = root.db(name, implementation='postgres',
                    conninfo=f"dbname={name} options='{READ_ONLY}'")
                db.packages().package('invc', path=str(Path(__file__).parent/'asqueel_model/invc'),
                                      sqlschema='invc', sqlprefix=False)
        shared = AsqueelDb(DatabaseConfiguration)
        with shared.session() as session:
            if session.execute('SHOW transaction_read_only').fetchone()[0] != 'on':
                raise RuntimeError('Read-only connection required')
        atexit.register(shared.close)
        selectors = AsqueelSelect(shared).register('customers', 'invc.customer', identifier='id',
            caption='account_name', columns=('suburb','state'), order_by=('account_name','id'))
        return selectors.register('states', 'invc.state', identifier='code', caption='name',
                                  columns=('code',), order_by=('name',))
    if backend == 'sqlalchemy':
        from sqlalchemy import create_engine, text, select
        from gramlot_py_server.db.sqlalchemy import SQLAlchemySelect
        from .sqlalchemy_model import customer, state
        engine = create_engine(f'postgresql+psycopg:///{name}', connect_args={'options':READ_ONLY})
        with engine.connect() as connection:
            if connection.execute(text('SHOW transaction_read_only')).scalar() != 'on':
                raise RuntimeError('Read-only connection required')
        atexit.register(engine.dispose)
        customers = select(customer, state.c.name.label('state_name')).select_from(
            customer.outerjoin(state, customer.c.state == state.c.code)).subquery()
        return SQLAlchemySelect(engine).register('customers', customers, identifier='id',
            caption='account_name', columns=('suburb','state','state_name'), order_by=('account_name','id'))
    from django.db import connection, connections
    from django.db.models import F
    from gramlot_py_server.db.django import DjangoSelect
    from .django_model import Customer
    with connection.cursor() as cursor:
        cursor.execute('SHOW transaction_read_only')
        if cursor.fetchone()[0] != 'on':
            raise RuntimeError('Read-only connection required')
    atexit.register(connections.close_all)
    return DjangoSelect().register('customers', Customer, identifier='id', caption='account_name',
        columns=('suburb','state','state_name'), order_by=('account_name','id'),
        annotations={'state_name': F('state__name')})
