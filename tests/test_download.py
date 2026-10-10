import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src import download
from tests.test_pipeline import FIELDS, sale
import csv


class DownloadChecks(unittest.TestCase):
    def test_short_record_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'raw.csv'
            path.write_text(download.EXPECTED_HEADER + '\n2026-09,bad\n')
            with self.assertRaises(ValueError):
                download.inspect_csv(path)

    def test_late_download_manifest_promotion_preserves_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'raw.csv'
            manifest = Path(directory) / 'manifest.json'
            path.write_bytes(b'previous raw')
            manifest.write_bytes(b'previous manifest')
            import io, os
            stream = io.StringIO(newline='')
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerow(sale())
            data = stream.getvalue().encode()
            original = os.replace
            failed = False
            def fail_manifest(source, target):
                nonlocal failed
                if Path(target) == manifest and not failed:
                    failed = True
                    raise OSError('late manifest promotion')
                return original(source, target)
            with patch.object(download, 'OUT', path), patch.object(download, 'MANIFEST', manifest), patch('sys.argv', ['download', '--force']), patch.object(download, 'get', side_effect=[b'{"data":{"url":"https://offline.invalid/raw"}}', data]), patch('os.replace', fail_manifest):
                with self.assertRaises(OSError):
                    download.main()
            self.assertEqual(path.read_bytes(), b'previous raw')
            self.assertEqual(manifest.read_bytes(), b'previous manifest')

    def test_nonfinite_download_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'raw.csv'
            with path.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerow(sale(resale_price='NaN'))
            with self.assertRaises(ValueError):
                download.inspect_csv(path)

    def test_stale_cache_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'raw.csv'
            manifest = Path(directory) / 'manifest.json'
            with path.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerow(sale())
            manifest.write_text(json.dumps({'sha256': '0' * 64}))
            with patch.object(download, 'OUT', path), patch.object(download, 'MANIFEST', manifest), patch('sys.argv', ['download']):
                with self.assertRaises(ValueError):
                    download.main()


if __name__ == '__main__':
    unittest.main()
