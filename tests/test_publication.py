"""Acceptance checks against the actual approved public content, not private archives."""
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

from test_build import builder

ROOT = Path(__file__).resolve().parents[1]
BASE = '/breath-and-silence-site/'


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.unsafe_scripts = []
        self.inline_handlers = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if 'id' in data:
            self.ids.add(data['id'])
        if tag in ['a', 'link', 'script', 'img']:
            value = data.get('href') if tag in ['a', 'link'] else data.get('src')
            if value:
                self.links.append(value)
        if tag == 'script' and data.get('src') != BASE + 'assets/site.js':
            self.unsafe_scripts.append(data)
        self.inline_handlers.extend(k for k in data if k.lower().startswith('on'))


class ApprovedPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / 'site'
        cls.records = json.loads((ROOT / 'content/research.json').read_text())
        cls.mod = builder()
        cls.result = cls.mod.build_site(ROOT / 'content', cls.output, BASE)
        cls.pages = {}
        for file in cls.output.rglob('*.html'):
            parsed = Page()
            parsed.feed(file.read_text())
            cls.pages[file] = parsed

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_complete_catalog_and_public_fields(self):
        self.assertEqual(self.result['sources'], len(self.records))
        self.assertEqual(len({r['id'] for r in self.records}), len(self.records))
        self.assertEqual(json.loads((self.output / 'assets/research.json').read_text()), self.records)
        for r in self.records:
            self.assertEqual(set(r), self.mod.PUBLIC_KEYS)
            self.assertIn(r['kind'], self.mod.KINDS)
            self.assertIn(r['evidence_status'], self.mod.STATUSES)
            for key in ['summary_he', 'relevance_he', 'limitation_he']:
                self.assertTrue(r[key].strip(), (r['id'], key))
            self.assertTrue((self.output / f'research/s{r["id"]:03d}/index.html').is_file())

    def test_dispenza_sources_are_discoverable_in_both_languages(self):
        by_id = {r['id']: r for r in self.records}
        for source_id in [28, 39, 79, 80]:
            record = by_id[source_id]
            searchable = ' '.join(record[k] for k in ['title', 'summary_he', 'relevance_he', 'limitation_he']).casefold()
            self.assertIn('dispenza', searchable, source_id)
            self.assertIn('דיספנזה', searchable, source_id)

    def test_local_links_assets_and_anchors(self):
        problems = []
        for file, parsed in self.pages.items():
            for link in parsed.links:
                u = urlsplit(link)
                if u.scheme or u.netloc:
                    continue
                if u.path.startswith(BASE):
                    target = self.output / unquote(u.path[len(BASE):])
                elif u.path.startswith('/'):
                    problems.append((str(file), link, 'outside project base'))
                    continue
                else:
                    target = file.parent / unquote(u.path) if u.path else file
                if target.is_dir():
                    target /= 'index.html'
                if not target.is_file():
                    problems.append((str(file), link, 'missing file'))
                elif u.fragment and target in self.pages and unquote(u.fragment) not in self.pages[target].ids:
                    problems.append((str(file), link, 'missing anchor'))
        self.assertEqual(problems, [])

    def test_no_private_archive_or_unexpected_executable_html(self):
        for file in self.output.rglob('*'):
            if not file.is_file() or file.suffix not in ['.json', '.html']:
                continue
            text = file.read_text()
            for token in ['/root/', 'cache/scratch', 'source_text_path', 'original_source_text_path',
                          '"verified_quotes"', '"origins"', '"cards"']:
                self.assertNotIn(token, text, (str(file), token))
        for file, page in self.pages.items():
            text = file.read_text()
            self.assertIn('lang="he"', text)
            self.assertIn('dir="rtl"', text)
            self.assertEqual(page.unsafe_scripts, [], str(file))
            self.assertEqual(page.inline_handlers, [], str(file))


if __name__ == '__main__':
    unittest.main()
