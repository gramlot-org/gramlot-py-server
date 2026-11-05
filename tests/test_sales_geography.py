"""Geographic matching must not assign unknown or ambiguous localities."""
import json,unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from gramlot_py_server.gallery.base.sales_geography import SalesGeography,STATES

class Cursor:
    def __init__(self,rows):self.rows=rows
    def fetchone(self):return self.rows[0]
    def fetchall(self):return self.rows
class Database:
    def __init__(self,readonly=True):self.readonly=readonly
    def session(self):return self
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def execute(self,sql,args=None):
        if sql.startswith('SHOW'):return Cursor([('on' if self.readonly else 'off',)])
        return Cursor([('ACT','Canberra',Decimal('10'),2,1),('ACT','Unknown',Decimal('20'),3,2)])

def feature(name):
    return dict(type='Feature',properties=dict(name=name,sal_name_2021=name),geometry=dict(type='Polygon',coordinates=[[[0,0],[1,0],[1,1],[0,0]]]))

class GeographyTest(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.states=dict(type='FeatureCollection',features=[feature(name) for name in STATES.values()])
        self.path=Path(self.folder.name)
        self.localities=[feature('Canberra'),dict(type='Feature',properties=dict(sal_name_2021='No usual address'),geometry=None)]
        self.write()
    def write(self):
        (self.path/'ACT.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=self.localities)))
    def provider(self,readonly=True):return SalesGeography(Database(readonly),self.states,self.path)
    def test_national_totals_do_not_load_localities(self):
        (self.path/'ACT.geojson').unlink()
        result=self.provider().read('','2025')
        self.assertEqual(result.get_item('count'),1);self.assertEqual(result.get_item('total'),30)
        row=result.get_item('rows').nodes[0].attr
        self.assertEqual(row['customers'],3);self.assertEqual(row['per_customer'],10)
    def test_unmatched_remains_in_rows_and_totals(self):
        result=self.provider().read('ACT','2025')
        self.assertEqual(result.get_item('boundaries'),1);self.assertEqual(result.get_item('unmatched'),1)
        self.assertEqual(result.get_item('unmatched_revenue'),20);self.assertEqual(result.get_item('total'),30)
        self.assertEqual(result.get_item('rows').nodes[1].attr['matched'],'No')
        self.assertIsInstance(result.get_item('geoJSON'),dict)
    def test_ambiguous_names_are_not_guessed(self):
        self.localities.append(feature('Canberra (ACT)'));self.write()
        self.assertEqual(self.provider().read('ACT','2025').get_item('unmatched'),2)
    def test_only_current_state_suffix_is_removed(self):
        self.localities=[feature('Canberra (ACT)'),feature('Unknown (NSW)')];self.write()
        result=self.provider().read('ACT','2025')
        self.assertEqual(result.get_item('unmatched'),1)
        self.assertEqual(result.get_item('rows').nodes[0].attr['code'],'Canberra (ACT)')
        self.localities=[feature('Canberra (District - ACT)')];self.write()
        self.assertEqual(self.provider().read('ACT','2025').get_item('unmatched'),2)
    def test_invalid_parameters_and_readonly(self):
        with self.assertRaises(ValueError):self.provider().read('../ACT','2025')
        with self.assertRaises(ValueError):self.provider().read('ACT','2026')
        with self.assertRaises(RuntimeError):self.provider(False).read('ACT','2025')
