"""Stdlib checks for resale-card #10; optional --pbix checks the release report.

Run: python bi/check_report.py [--pbix path/to/hdb-resale-mart.pbix]
This checks authoring contracts, not a substitute for a Desktop render.
"""
import argparse
import csv
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'bi/source'
CARD = 'definition/pages/6ff4b9bc65dc02ac5d29/visuals/e86b30c19a4d7522f0bb/visual.json'


def check_visuals(read, files):
    card = json.loads(read(CARD))['visual']
    data = card['query']['queryState']['Data']['projections']
    assert len(data) == 1
    assert data[0]['field']['Measure'] == {
        'Expression': {'SourceRef': {'Entity': 'town_4room_yoy'}},
        'Property': 'Resales KPI',
    }
    caption = card['objects']['label'][0]['properties']['text']['expr']['Literal']['Value']
    assert caption == "'Resales, Q3 2026 vs Q3 2025'"
    alt = card['visualContainerObjects']['general'][0]['properties']['altText']['expr']['Measure']
    assert alt['Property'] == 'Resales Alt Text'
    assert alt['Expression']['SourceRef']['Entity'] == 'town_4room_yoy'
    tables = [json.loads(read(f))['visual'] for f in files if f.endswith('/visual.json')]
    tables = [v for v in tables if v['visualType'] == 'tableEx']
    assert len(tables) == 1
    assert tables[0]['objects']['total'][0]['properties']['totals']['expr']['Literal']['Value'] == 'false'
    text = read(CARD)
    assert 'latest 12 months' not in text and '+7%' not in text and '+7.0%' not in text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pbix', type=Path)
    args = parser.parse_args()
    report = SOURCE / 'hdb-resale-mart.Report'
    files = [str(f.relative_to(report)).replace('\\', '/') for f in report.rglob('*.json')]
    check_visuals(lambda f: (report / f).read_text(encoding='utf-8'), files)
    model = (SOURCE / 'hdb-resale-mart.SemanticModel/definition/tables/town_4room_yoy.tmdl').read_text(encoding='utf-8')
    for required in ['SUM(town_4room_yoy[n_t1])', 'SUM(town_4room_yoy[n_t0])',
                     'DIVIDE(CurrentSales - PriorSales, PriorSales)', 'ISBLANK(Change)',
                     'FORMAT(Change, "+0.0%;-0.0%;0.0%")', '[Resales KPI]',
                     'Q3 2026 vs Q3 2025', 'Percentage is change in sales count, not price.']:
        assert required in model, required
    assert 'latest 12 months' not in model and '+7%' not in model
    assert 'Data Portfolio' not in model and 'Users\\' not in model
    with (ROOT / 'outputs/town_4room_yoy.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    prior = sum(int(row['n_t0']) for row in rows)
    current = sum(int(row['n_t1']) for row in rows)
    assert prior > 0 and current >= 0
    print(f'PASS source: data-bound count/YoY and alt text; Q3 windows; table totals off; {len(rows)} towns; {current:,} / {prior:,} - 1 = {(current/prior-1):+.1%}')
    if args.pbix:
        with zipfile.ZipFile(args.pbix) as z:
            assert z.testzip() is None
            assert len(z.read('DataModel')) > 0
            def read(f):
                return z.read('Report/' + f).decode('utf-8')
            check_visuals(read, [f.removeprefix('Report/') for f in z.namelist() if f.startswith('Report/')])
        print('PASS PBIX: packaged bindings/windows/totals off; imported DataModel present; ZIP CRC clean')


if __name__ == '__main__':
    main()
