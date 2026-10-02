# data/raw — raw files are never edited or committed

**Source:** HDB resale flat prices (registration date, Jan-2017 onwards)
**Dataset:** data.gov.sg `d_8b84c4ee58e3cfc0ece0d773c8ca6abc` — https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view
**Licence:** Singapore Open Data Licence (© Housing & Development Board)
**Size:** 241,822 rows (~22.8 MB) at the 2026-10-02 pull — fetched by `src/download.py` (data.gov.sg v1 flow: initiate → poll → signed URL; browser user-agent header required); excluded from git.
**Pulls:** 2026-10-02 — `hdb-resale-prices-2017-onwards.csv` (241,823 lines incl. header) + `dataset-metadata.json` (local; gitignored). Re-pull any time with `python src/download.py`.
