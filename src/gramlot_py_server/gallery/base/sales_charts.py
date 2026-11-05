"""Read-only invoice aggregation for the reusable ChartReportPage example."""
from datetime import date
from decimal import Decimal
from time import perf_counter
from genro_bag import Bag

QUERY = '''
WITH annual AS (
 SELECT s.code,s.name,extract(year from i.date)::int AS year,
        sum(i.total) AS revenue,count(DISTINCT i.customer_id) AS customers
 FROM invc.invc_invoice i
 JOIN invc.invc_customer c ON c.id=i.customer_id
 JOIN invc.invc_state s ON s.code=c.state
 WHERE i.date >= :start_date AND i.date < :end_date
 GROUP BY s.code,s.name,extract(year from i.date)
)
SELECT current.code,current.name,current.revenue,current.customers,previous.revenue AS previous_revenue
FROM annual current LEFT JOIN annual previous ON previous.code=current.code AND previous.year=current.year-1
WHERE current.year=:year ORDER BY current.code
'''

class SalesCharts:
    """Application provider: the shared chart never knows about invoices or SQL."""
    def __init__(self,database):self.database=database

    def read(self,year):
        if not isinstance(year,str) or len(year)!=4 or not year.isascii() or not year.isdigit():
            raise ValueError('Year must contain four digits')
        selected=int(year)
        if not 1901<=selected<=9998:raise ValueError('Year outside supported date range')
        with self.database.session() as session:
            # Read-only is a connection property, not an application-side SQL convention.
            if session.execute('SHOW transaction_read_only').fetchone()[0]!='on':raise RuntimeError('Read-only database session required')
            records=session.execute(QUERY,dict(start_date=date(selected-1,1,1),end_date=date(selected+1,1,1),year=selected)).fetchall()
        rows=Bag()
        for code,name,total,customers,previous in records:
            if previous is None or previous==0 or customers<=0:
                raise ValueError('Previous-year total or distinct-customer denominator unavailable; previous data retained')
            rows.set_item(code,None,code=code,territory=name,revenue=float(total),customers=customers,
                          per_customer=float((total/customers).quantize(Decimal('0.01'))),
                          change_pct=float(((total/previous-1)*100).quantize(Decimal('0.01'))))
        return Bag(dict(rows=rows,period=f'{selected} vs {selected-1}',count=len(rows)))


    def read_timeline(self, grain):
        """Prepare complete dated territory rows; all arithmetic stays on the server."""
        if grain not in ('day', 'month'):
            raise ValueError('Choose day or month')
        started=perf_counter()
        with self.database.session() as session:
            session.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            if session.execute('SHOW transaction_read_only').fetchone()[0]!='on':
                raise RuntimeError('Read-only database session required')
            summary=session.execute('SELECT count(*),sum(total),min(date),max(date) FROM invc.invc_invoice').fetchone()
            lines=session.execute('SELECT count(*),sum(tot_price) FROM invc.invc_invoice_row').fetchone()
            records=session.execute("""
                WITH lines AS (
                    SELECT invoice_id,sum(quantity) AS units,count(*) AS line_count
                    FROM invc.invc_invoice_row GROUP BY invoice_id
                )
                SELECT date_trunc(:grain,i.date)::date AS period,s.code,s.name,
                       sum(i.total) AS revenue,count(*) AS invoices,
                       count(DISTINCT i.customer_id) AS customers,
                       sum(l.units) AS units,sum(l.line_count) AS invoice_lines
                FROM invc.invc_invoice i
                JOIN invc.invc_customer c ON c.id=i.customer_id
                JOIN invc.invc_state s ON s.code=c.state
                JOIN lines l ON l.invoice_id=i.id
                GROUP BY date_trunc(:grain,i.date),s.code,s.name
                ORDER BY period,s.code
            """,dict(grain=grain)).fetchall()
        queried=perf_counter()
        if (sum(row[3] for row in records)!=summary[1] or summary[1]!=lines[1]
                or sum(row[4] for row in records)!=summary[0]
                or sum(row[7] for row in records)!=lines[0]):
            raise ValueError('Timeline totals do not reconcile with all source invoices and lines')
        codes=sorted({row[1] for row in records})
        rows=Bag()
        for index,(period,code,name,revenue,invoices,customers,units,line_count) in enumerate(records):
            rows.set_item(f'r{index}',None,period=period,code=code,territory=name,
                          rank=codes.index(code),revenue=float(revenue),invoices=invoices,
                          customers=customers,units=int(units),invoice_lines=int(line_count))
        return Bag(dict(rows=rows,count=len(rows),grain=grain,
                        source_invoices=summary[0],source_lines=lines[0],
                        first_date=summary[2],last_date=summary[3],total=float(summary[1]),
                        query_ms=round((queried-started)*1000,2),
                        prepare_ms=round((perf_counter()-queried)*1000,2)))
