"""Provider contract independent of the live PostgreSQL fixture."""
import unittest
from decimal import Decimal
from gramlot_py_server.gallery.base.sales_charts import SalesCharts

class Cursor:
    def __init__(self,rows):self.rows=rows
    def fetchone(self):return self.rows[0]
    def fetchall(self):return self.rows
class Session:
    def __init__(self,rows,read_only=True):self.rows=rows;self.read_only=read_only
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def execute(self,sql,args=None):
        if sql.startswith('SHOW'):return Cursor([('on' if self.read_only else 'off',)])
        assert args['start_date'].year==args['year']-1 and args['end_date'].year==args['year']+1
        assert 'previous.revenue AS previous_revenue' in sql
        return Cursor(self.rows)
class Database:
    def __init__(self,rows,read_only=True):self.rows=rows;self.read_only=read_only
    def session(self):return Session(self.rows,self.read_only)

class SalesChartsTest(unittest.TestCase):
    def test_metrics_and_empty(self):
        row=SalesCharts(Database([('A','Alpha',Decimal('80'),2,Decimal('100'))])).read('2025').get_item('rows').nodes[0]
        self.assertEqual(row.attr['per_customer'],40)
        self.assertEqual(row.attr['change_pct'],-20)
        self.assertEqual(SalesCharts(Database([])).read('2030').get_item('count'),0)
    def test_errors_are_explicit(self):
        for previous,customers in [(None,2),(Decimal(0),2),(Decimal(100),0)]:
            with self.assertRaises(ValueError):SalesCharts(Database([('A','Alpha',Decimal(80),customers,previous)])).read('2025')
        with self.assertRaises(RuntimeError):SalesCharts(Database([],False)).read('2025')
        for year in ('2025;DROP','0000',2025):
            with self.assertRaises(ValueError):SalesCharts(Database([])).read(year)
