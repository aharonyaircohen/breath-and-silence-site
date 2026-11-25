import json
import tempfile
import unittest
from pathlib import Path
from test_build import builder


class StaticSiteTests(unittest.TestCase):
    def test_builds_readable_rtl_pages_and_escaped_research_details(self):
        mod = builder()
        self.assertTrue(hasattr(mod, 'build_site'), 'Static site generation is not implemented')
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            content = root / 'content'
            content.mkdir()
            (content / 'model.md').write_text('# דממה חיה\n\nהמוח מתמכר לרעש [7].\n\n<a id="process"></a>\n## התהליך\nבחירה חופשית.\n\n<a id="conclusion"></a>\n# ד. מסקנה\nמודל עבודה.')
            (content / 'homepage.md').write_text('# דממה חיה\n## אימון לשקט נפשי\n\nדף ההסבר.')
            (content / 'preparation.md').write_text('מרווח לפני התרגול.')
            record = {'id': 7, 'title': '<script>test</script> Study', 'url': 'https://example.org/study',
                      'principles': ['P1'], 'identifiers': {}, 'year': '2024', 'journal': '',
                      'summary_he': 'ממצא ניסויי', 'relevance_he': 'למידת הרגל',
                      'limitation_he': 'לא אבחנה קלינית', 'kind': 'trial', 'evidence_status': 'mixed'}
            (content / 'research.json').write_text(json.dumps([record], ensure_ascii=False))
            output = root / 'site'
            mod.build_site(content, output, '/course/')
            for name in ['index.html', 'model/index.html', 'research/index.html',
                         'research/s007/index.html', 'process/index.html',
                         'preparation/index.html', 'about/index.html', '404.html']:
                self.assertTrue((output / name).is_file(), name)
                html = (output / name).read_text()
                self.assertIn('lang="he"', html)
                self.assertIn('dir="rtl"', html)
                self.assertIn('| דממה חיה</title>', html)
                self.assertIn('>דממה חיה<span>', html)
                self.assertIn('content="דממה חיה: המודל', html)
            detail = (output / 'research/s007/index.html').read_text()
            self.assertNotIn('<script>test</script>', detail)
            self.assertIn('&lt;script&gt;', detail)
            model = (output / 'model/index.html').read_text()
            self.assertIn('/course/research/s007/', model)
            self.assertNotIn('<div class="toc">', model)
            self.assertIn('class="toc-links"', model)
            self.assertTrue((output / 'assets/site.css').is_file())
            self.assertTrue((output / 'assets/site.js').is_file())
            self.assertIn('source-filter', (output / 'research/index.html').read_text())
            self.assertIn('בחירה חופשית.', (output / 'process/index.html').read_text())
            self.assertNotIn('מודל עבודה.', (output / 'process/index.html').read_text())


class RebuildAndPublicationTests(unittest.TestCase):
    @staticmethod
    def fixture(root):
        content = root / 'content'
        content.mkdir()
        (content / 'model.md').write_text('# המודל\n\nתיאור [7].')
        (content / 'homepage.md').write_text('# דממה חיה\n## אימון לשקט נפשי\n\nדף ההסבר.')
        (content / 'preparation.md').write_text('מרווח לפני התרגול.')
        record = {'id': 7, 'title': 'Study', 'url': 'https://example.org/study',
                  'principles': ['P1'], 'identifiers': {}, 'year': '', 'journal': '',
                  'summary_he': 'סיכום מדידה', 'relevance_he': 'רלוונטיות למודל',
                  'limitation_he': 'מגבלה חשובה', 'kind': 'trial', 'evidence_status': 'mixed'}
        (content / 'research.json').write_text(json.dumps([record], ensure_ascii=False))
        return content, record

    def test_homepage_publishes_full_explanation_with_inline_source_links(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            content, record = self.fixture(root)
            text = ('# דממה חיה\n## אימון לשקט נפשי\n\n'
                    'מה נדרש כדי ששקט עמוק יהפוך לשגרה?\n\n'
                    '## איך רעש נעשה הרגל\n\n'
                    'הסבר עם [המחקר המקורי](https://example.org/study).\n\n'
                    '## איך המרכיבים מתחברים לדממה חיה\n\n'
                    'סיום מלא של ההסבר.')
            (content / 'homepage.md').write_text(text)
            output = root / 'site'
            builder().build_site(content, output, '/course/')
            html = (output / 'index.html').read_text()
            self.assertIn('מה נדרש כדי ששקט עמוק יהפוך לשגרה?', html)
            self.assertIn('איך המרכיבים מתחברים לדממה חיה', html)
            self.assertIn('href="https://example.org/study"', html)
            self.assertIn('class="toc-links"', html)
            self.assertIn('סיום מלא של ההסבר.', html)
            self.assertEqual(html.count('<h1'), 1)
            self.assertNotIn('להכיר שקט.', html)
            self.assertIn('<title>אימון לשקט נפשי | דממה חיה</title>', html)

    def test_rejects_private_archive_fields_in_public_input(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            content, record = self.fixture(root)
            record['origins'] = [{'path': '/private/evidence'}]
            (content / 'research.json').write_text(json.dumps([record]))
            with self.assertRaises(ValueError):
                builder().build_site(content, root / 'site', '/course/')

    def test_rebuild_removes_withdrawn_generated_source_not_unmanaged_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            content, record = self.fixture(root)
            output = root / 'site'
            mod = builder()
            mod.build_site(content, output, '/course/')
            (output / 'keep.txt').write_text('not generated by the site builder')
            record['id'] = 8
            (content / 'research.json').write_text(json.dumps([record]))
            (content / 'model.md').write_text('# המודל\n\nתיאור [8].')
            mod.build_site(content, output, '/course/')
            self.assertFalse((output / 'research/s007/index.html').exists())
            self.assertTrue((output / 'research/s008/index.html').is_file())
            self.assertTrue((output / 'keep.txt').is_file())

    def test_rejects_source_url_without_hostname(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            content, record = self.fixture(root)
            record['url'] = 'https:example.org/study'
            (content / 'research.json').write_text(json.dumps([record]))
            with self.assertRaises(ValueError):
                builder().build_site(content, root / 'site', '/course/')


if __name__ == '__main__':
    unittest.main()
