"""Explicit SQLAlchemy model of the Base gallery physical subset."""
from sqlalchemy import MetaData, Table, Column, CHAR, String, Text, Integer, Numeric, Date, ForeignKey

metadata = MetaData(schema="invc")

state = Table('invc_state', metadata,
    Column('code', String(5), primary_key=True, nullable=False),
    Column('name', String(100), primary_key=False, nullable=True),
)

customer = Table('invc_customer', metadata,
    Column('id', CHAR(22), primary_key=True, nullable=False),
    Column('account_name', Text, primary_key=False, nullable=True),
    Column('suburb', Text, primary_key=False, nullable=True),
    Column('state', String(5), ForeignKey('invc.invc_state.code', onupdate="CASCADE", ondelete="NO ACTION"), primary_key=False, nullable=True),
)

invoice = Table('invc_invoice', metadata,
    Column('id', CHAR(22), primary_key=True, nullable=False),
    Column('inv_number', CHAR(10), primary_key=False, nullable=True, unique=True),
    Column('customer_id', CHAR(22), ForeignKey('invc.invc_customer.id', onupdate="CASCADE", ondelete="NO ACTION"), primary_key=False, nullable=True),
    Column('date', Date, primary_key=False, nullable=True),
    Column('total', Numeric(14, 2), primary_key=False, nullable=True),
)

product = Table('invc_product', metadata,
    Column('id', CHAR(22), primary_key=True, nullable=False),
    Column('code', String(10), primary_key=False, nullable=True),
    Column('description', String(80), primary_key=False, nullable=True),
    Column('unit_price', Numeric(14, 2), primary_key=False, nullable=True),
)

invoice_row = Table('invc_invoice_row', metadata,
    Column('id', CHAR(22), primary_key=True, nullable=False),
    Column('invoice_id', CHAR(22), ForeignKey('invc.invc_invoice.id', onupdate="CASCADE", ondelete="NO ACTION"), primary_key=False, nullable=True),
    Column('product_id', CHAR(22), ForeignKey('invc.invc_product.id', onupdate="CASCADE", ondelete="NO ACTION"), primary_key=False, nullable=True),
    Column('quantity', Integer, primary_key=False, nullable=True),
    Column('unit_price', Numeric(14, 2), primary_key=False, nullable=True),
    Column('tot_price', Numeric(14, 2), primary_key=False, nullable=True),
)
