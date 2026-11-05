"""Read-only temporal report reconciliation and parameter contract."""
import unittest
from datetime import date
from decimal import Decimal
from gramlot_py_server.gallery.base.sales_charts import SalesCharts

class Cursor:
    def __init__(self,rows):self.rows=rows
    def fetchone(self):return self.rows[0]
    def fetchall(self):return self.rows
class Database:
    def __init__(self,readonly=True,total=Decimal('30')):self.readonly=readonly;self.total=total;self.grain=None
    def session(self):return self
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def execute(self,sql,args=None):
        if sql.startswith('SET'):return Cursor([])
        if sql.startswith('SHOW'):return Cursor([('on' if self.readonly else 'off',)])
        if 'sum(total)' in sql:return Cursor([(2,self.total,date(2022,1,1),date(2022,2,1))])
        if 'sum(tot_price)' in sql:return Cursor([(3,Decimal('30'))])
        self.grain=args['grain']
        return Cursor([(date(2022,1,1),'ACT','Australian Capital Territory',Decimal('10'),1,1,2,1),
                       (date(2022,2,1),'TAS','Tasmania',Decimal('20'),1,1,4,2)])

class TimelineTest(unittest.TestCase):
    def test_prepared_rows_and_totals(self):
        for grain in ('day','month'):
            db=Database();result=SalesCharts(db).read_timeline(grain)
            self.assertEqual(db.grain,grain);self.assertEqual(result.get_item('count'),2)
            self.assertEqual(result.get_item('source_lines'),3)
            row=result.get_item('rows').nodes[1]
            self.assertEqual(row.attr['period'],date(2022,2,1));self.assertEqual(row.attr['units'],4)
            self.assertEqual(row.attr['rank'],1);self.assertEqual(result.get_item('total'),30)
    def test_rejects_non_readonly_and_unreconciled_data(self):
        with self.assertRaises(RuntimeError):SalesCharts(Database(False)).read_timeline('day')
        with self.assertRaises(ValueError):SalesCharts(Database(total=Decimal('31'))).read_timeline('month')
    def test_invalid_grain_does_not_open_session(self):
        with self.assertRaises(ValueError):SalesCharts(None).read_timeline('week; DROP')
