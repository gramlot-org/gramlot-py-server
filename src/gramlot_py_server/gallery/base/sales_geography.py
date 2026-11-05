"""Read-only geographic sales and explicit ABS SAL locality matching."""
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from genro_bag import Bag

STATES={'NSW':'New South Wales','VIC':'Victoria','QLD':'Queensland','SA':'South Australia',
        'WA':'Western Australia','TAS':'Tasmania','NT':'Northern Territory','ACT':'Australian Capital Territory'}

STATE_SUFFIX={'NSW':'NSW','VIC':'Vic.','QLD':'Qld','SA':'SA','WA':'WA','TAS':'Tas.','NT':'NT','ACT':'ACT'}

class SalesGeography:
    """Keep SQL and geographic preparation outside the chart collection."""
    def __init__(self,database,state_geojson,localities):
        self.database=database
        self.localities=Path(localities)
        self._cache={}
        codes={name:code for code,name in STATES.items()}
        self.states={'type':'FeatureCollection','features':[
            {**f,'properties':{**f['properties'],'name':codes[f['properties']['name']]}}
            for f in state_geojson['features'] if f['properties']['name'] in codes]}
        if {f['properties']['name'] for f in self.states['features']}!=set(STATES):
            raise ValueError('State GeoJSON must contain all eight Australian States and territories')

    def geography(self,state):
        if state not in STATES:raise ValueError('Unknown Australian State')
        if state not in self._cache:
            source=json.loads((self.localities/f'{state}.geojson').read_text())
            # ABS special-purpose, nonspatial records cannot be drawn as territories.
            features=[{**f,'properties':{**f['properties'],'name':f['properties']['sal_name_2021']}} for f in source['features'] if f['geometry'] is not None]
            self._cache[state]={'type':'FeatureCollection','features':features}
        return self._cache[state]

    def read(self,state,year):
        if state!='' and state not in STATES:raise ValueError('Unknown Australian State')
        if year not in ('2022','2023','2024','2025'):raise ValueError('Choose a year from 2022 to 2025')
        selected=int(year)
        with self.database.session() as session:
            if session.execute('SHOW transaction_read_only').fetchone()[0]!='on':
                raise RuntimeError('Read-only database session required')
            records=session.execute('''
                SELECT c.state,c.suburb,sum(i.total) AS revenue,count(*) AS invoices,count(DISTINCT c.id) AS customers
                FROM invc.invc_invoice i JOIN invc.invc_customer c ON c.id=i.customer_id
                WHERE i.date>=:start AND i.date<:end AND (:state='' OR c.state=:state)
                GROUP BY c.state,c.suburb ORDER BY c.state,c.suburb
            ''',dict(start=date(selected,1,1),end=date(selected+1,1,1),state=state)).fetchall()
        if any(code not in STATES for code,*_ in records):raise ValueError('Invoice references an unknown State')
        geo=self.geography(state) if state else self.states
        names=defaultdict(list)
        if state:
            for f in geo['features']:
                name=f['properties']['sal_name_2021'].removesuffix(f' ({STATE_SUFFIX[state]})')
                names[name].append(f['properties']['name'])
        totals={};unmatched=[]
        for code,suburb,revenue,invoices,customers in records:
            matches=names[suburb] if state else [code]
            matched=len(matches)==1
            key=matches[0] if matched else f'unmatched-{len(unmatched)}'
            label=suburb if state else STATES[code]
            if not matched:unmatched.append((suburb,revenue,invoices,customers))
            if key not in totals:totals[key]=[label,revenue,invoices,customers,matched]
            else:
                row=totals[key];row[1]+=revenue;row[2]+=invoices;row[3]+=customers
        rows=Bag()
        for i,(key,(label,revenue,invoices,customers,matched)) in enumerate(totals.items()):
            rows.set_item(f'r{i}',None,code=key,territory=label or '(missing locality)',map_label='' if state else label,revenue=float(revenue),
                          invoices=invoices,customers=customers,matched='Yes' if matched else 'No',
                          per_customer=float(revenue/customers))
        result=Bag(dict(rows=rows,state=state,title=STATES[state] if state else 'Australia',year=year,
                        count=len(rows),boundaries=len(geo['features']),unmatched=len(unmatched),
                        unmatched_customers=sum(r[3] for r in unmatched),
                        unmatched_revenue=float(sum(r[1] for r in unmatched)),
                        total=float(sum(r[2] for r in records))))

        result.set_item('geoJSON',geo)
        return result
