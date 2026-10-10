"""Download the raw dataset from data.gov.sg into data/raw/.

Flow: initiate-download -> poll-download -> signed URL (v1 public API).
Run: python src/download.py [--force]   (skips if the file already exists)

On success writes data/raw/pull_manifest.json: dataset id, source URLs, retrieval time,
byte size, SHA-256, row count and month coverage. Downloads land in a .part file and are
validated (expected header + non-empty) before replacing any existing CSV.
"""
import argparse
import hashlib
import json
import time
import urllib.request as u
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/raw/hdb-resale-prices-2017-onwards.csv"
MANIFEST = ROOT / "data/raw/pull_manifest.json"
DATASET = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
DATASET_URL = f"https://data.gov.sg/datasets/{DATASET}/view"
EXPECTED_HEADER = ("month,town,flat_type,block,street_name,storey_range,floor_area_sqm,"
                   "flat_model,lease_commence_date,remaining_lease,resale_price")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def get(url, ref="https://data.gov.sg/"):
    r = u.Request(url, headers={"User-Agent": UA, "Accept": "*/*", "Referer": ref})
    with u.urlopen(r, timeout=180) as resp:
        return resp.read()


def inspect_csv(path, manifest=None):
    """Structure + content summary for the raw CSV: header, bytes, SHA-256, rows, month coverage."""
    import csv
    import io
    data = Path(path).read_bytes()
    reader = csv.reader(io.StringIO(data.decode('utf-8'), newline=''), strict=True)
    header = next(reader, [])
    if header != EXPECTED_HEADER.split(','):
        raise ValueError('invalid or duplicate CSV schema')
    months = []
    for row in reader:
        if len(row) != len(header):
            raise ValueError('invalid CSV record width')
        import math
        for index in (6, 10):
            if row[index] and not math.isfinite(float(row[index])):
                raise ValueError('nonfinite CSV numeric value')
        months.append(row[0])
    if not months:
        raise ValueError('empty CSV')
    info = {
        "header_ok": True,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "rows": len(months),
        "month_min": min(months),
        "month_max": max(months),
    }
    if manifest is not None and Path(manifest).exists():
        saved = json.loads(Path(manifest).read_text(encoding='utf-8'))
        if any(saved.get(key) != value for key, value in info.items()):
            raise ValueError('cache manifest integrity mismatch')
    return info


def write_manifest(info, retrieved_at, source):
    m = {
        "dataset_id": DATASET,
        "dataset_url": DATASET_URL,
        "file": OUT.name,
        "retrieved_at": retrieved_at,
        "retrieved_at_source": source,
        **info,
    }
    MANIFEST.write_text(json.dumps(m, indent=2), encoding="utf-8")
    print("manifest:", MANIFEST)
    for k in ("retrieved_at", "rows", "month_min", "month_max", "sha256"):
        print(f"    {k}: {m[k]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download even if the file exists")
    args = ap.parse_args()

    if OUT.exists() and not args.force:
        info = inspect_csv(OUT, MANIFEST)
        print(f"raw file already present ({OUT.stat().st_size} bytes) — use --force to refresh")
        print("path:", OUT)
        if not MANIFEST.exists():
            mtime = datetime.fromtimestamp(OUT.stat().st_mtime, tz=timezone.utc).isoformat()
            write_manifest(inspect_csv(OUT), mtime, "file_mtime")
        return

    base = f"https://api-open.data.gov.sg/v1/public/api/datasets/{DATASET}"
    url = ""
    try:
        j = json.loads(get(base + "/poll-download"))
        url = (j.get("data") or {}).get("url") or ""
    except Exception:
        pass
    if not url:
        get(base + "/initiate-download")
        for _ in range(15):
            time.sleep(1.5)
            try:
                j = json.loads(get(base + "/poll-download"))
                url = (j.get("data") or {}).get("url") or ""
            except Exception:
                continue
            if url:
                break
    if not url:
        raise SystemExit("no signed URL returned — try again in a minute")

    data = get(url)
    part = OUT.parent / (OUT.name + ".part")
    part.parent.mkdir(parents=True, exist_ok=True)
    part.write_bytes(data)
    info = inspect_csv(part)
    if not info["header_ok"] or info["rows"] == 0:
        part.unlink(missing_ok=True)
        raise SystemExit(f"downloaded file failed structure validation (header_ok={info['header_ok']}, "
                         f"rows={info['rows']}) — kept existing file")
    if __package__:
        from .promotion import promote
    else:
        from promotion import promote
    manifest_part = MANIFEST.with_suffix('.json.part')
    receipt = dict(dataset_id=DATASET, dataset_url=DATASET_URL, file=OUT.name,
                   retrieved_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                   retrieved_at_source='download', **info)
    manifest_part.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    promote([(part, OUT), (manifest_part, MANIFEST)])
    print(f"downloaded {info['bytes']} bytes · {info['rows']} rows · {info['month_min']} → {info['month_max']}")
    print("path:", OUT)


if __name__ == "__main__":
    main()
