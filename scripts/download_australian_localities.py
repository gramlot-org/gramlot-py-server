"""Download public ABS SAL 2021 boundaries, one simplified GeoJSON per State."""
import argparse,json,urllib.request,urllib.parse
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output',type=Path)
root=parser.parse_args().output;root.mkdir(parents=True,exist_ok=True)
url='https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SAL/MapServer/0/query'
for code,abbr in enumerate(['NSW','VIC','QLD','SA','WA','TAS','NT','ACT'],1):
 path=root/f'{abbr}.geojson'
 if path.exists():continue
 features=[];offset=0
 while True:
  params=dict(where=f"state_code_2021='{code}'",outFields='sal_code_2021,sal_name_2021,state_code_2021,state_name_2021',outSR=4326,returnGeometry='true',f='geojson',resultRecordCount=1000,resultOffset=offset,orderByFields='sal_code_2021',geometryPrecision=4,maxAllowableOffset=0.001)
  with urllib.request.urlopen(url+'?'+urllib.parse.urlencode(params),timeout=90) as response:d=json.load(response)
  if 'error' in d:raise RuntimeError(d['error'])
  batch=d['features'];features.extend(batch)
  if len(batch)<1000:break
  offset+=len(batch)
 for feature in features:
  feature['properties']['name']=feature['properties']['sal_code_2021']
 path.write_text(json.dumps(dict(type='FeatureCollection',features=features),separators=(',',':')))
 print(abbr,len(features),path.stat().st_size,flush=True)
