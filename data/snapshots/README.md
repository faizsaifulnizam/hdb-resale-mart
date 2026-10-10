# Frozen HDB input

`hdb-20261002.zip` contains the authentic historical CSV and its original metadata and manifest, unchanged. Data © Housing & Development Board, distributed under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence). No model or private audit evidence is included.

CSV SHA-256: `bd13d9cf3c1452d780f877e211c67d54e22eff63c4958a62150390f2ee90c11b` — 23,919,062 bytes; 241,822 records. The historical 2026-10-02 retrieval date is a **file-mtime proxy**, not authenticated acquisition time. This archive preserves the historical vintage, not current publisher data.

From the repo root, restore with stdlib Python (only the three named members are written):

```bash
python -c "import zipfile,hashlib,pathlib; z=zipfile.ZipFile('data/snapshots/hdb-20261002.zip'); names=['hdb-resale-prices-2017-onwards.csv','pull_manifest.json','dataset-metadata.json']; data={n:z.read(n) for n in names}; assert z.testzip() is None; assert hashlib.sha256(data[names[0]]).hexdigest()=='bd13d9cf3c1452d780f877e211c67d54e22eff63c4958a62150390f2ee90c11b'; p=pathlib.Path('data/raw'); p.mkdir(parents=True,exist_ok=True); [ (p/n).write_bytes(data[n]) for n in names ]"
```

Run the README analysis stages afterward. `download.py` validates the cache receipt; `download.py --force` instead obtains live publisher data. Do not expect a live refresh to reproduce a frozen historical headline. Local packaging is verified; anonymous public delivery is not established until this repair is published.
