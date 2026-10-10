import json
import unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT = Path(__file__).resolve().parents[1]
VISUALS = ROOT / 'bi/source/hdb-resale-mart.Report/definition/pages/6ff4b9bc65dc02ac5d29/visuals'

class DocumentationChecks(unittest.TestCase):
    def test_bi_caption_respects_selection_and_footer_is_frozen(self):
        caption = json.loads((VISUALS / '17d9f4a60b3e5c8291cc/visual.json').read_text())['visual']['objects']['label'][0]['properties']['text']['expr']['Literal']['Value']
        self.assertIn('selected towns', caption)
        footer = (VISUALS / 'b2c8e51f7a93460d8e3d/visual.json').read_text()
        self.assertIn('Frozen benchmark', footer)
        self.assertIn('mtime proxy', footer)

    def test_page_has_heading_and_primary_landmark(self):
        class Parser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.h1 = self.main = 0
                self.in_main = False
            def handle_starttag(self, tag, attrs):
                if tag == 'main':
                    self.main += 1
                    self.in_main = True
                if tag == 'h1': self.h1 += 1
                if tag == 'footer': assert not self.in_main
            def handle_endtag(self, tag):
                if tag == 'main': self.in_main = False
        parser = Parser()
        parser.feed((ROOT / 'docs/index.html').read_text(encoding='utf-8'))
        self.assertEqual((parser.h1, parser.main), (1, 1))
