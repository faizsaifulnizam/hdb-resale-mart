"""Download the raw dataset from data.gov.sg into data/raw/.

Flow: initiate-download -> poll-download -> signed URL (v1 public API).
Run: python src/download.py [--force]   (skips if the file already exists)
"""
import argparse
import json
import time
import urllib.request as u
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/raw/hdb-resale-prices-2017-onwards.csv"
DATASET = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def get(url, ref="https://data.gov.sg/"):
    r = u.Request(url, headers={"User-Agent": UA, "Accept": "*/*", "Referer": ref})
    with u.urlopen(r, timeout=180) as resp:
        return resp.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download even if the file exists")
    args = ap.parse_args()

    if OUT.exists() and not args.force:
        print(f"raw file already present ({OUT.stat().st_size} bytes) — use --force to refresh")
        print("path:", OUT)
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"downloaded {len(data)} bytes, ~{data.count(chr(10))} lines")
    print("path:", OUT)


if __name__ == "__main__":
    main()
