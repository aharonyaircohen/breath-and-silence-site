import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def builder():
    path = ROOT / 'scripts' / 'build.py'
    if not path.is_file():
        raise AssertionError('Public projection builder has not been implemented')
    spec = importlib.util.spec_from_file_location('site_build', path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectionTests(unittest.TestCase):
    def test_public_record_does_not_export_private_evidence(self):
        item = {'id': 7, 'title': 'A study', 'url': 'https://example.org/study',
                'principles': ['P1'], 'identifiers': {'doi': ['10.1000/test']},
                'quotes': ['copyrighted source paragraph'],
                'verified_quotes': ['source passage'],
                'origins': [{'path': '/private/course/archive'}],
                'cards': [{'source_text_path': '/private/source.txt'}],
                'metadata': [{'pubYear': '2024', 'journalTitle': 'Example Journal'}]}
        summary = {'id': 7, 'summary_he': 'ממצא שנמדד', 'relevance_he': 'רלוונטיות למודל',
                   'limitation_he': 'מגבלה', 'kind': 'trial', 'evidence_status': 'mixed'}
        result = builder().public_record(item, summary)
        self.assertEqual(result['id'], 7)
        self.assertEqual(result['summary_he'], 'ממצא שנמדד')
        self.assertEqual(result['year'], '2024')
        self.assertEqual(set(result), {'id', 'title', 'url', 'principles', 'identifiers',
                                      'year', 'journal', 'summary_he', 'relevance_he',
                                      'limitation_he', 'kind', 'evidence_status'})
        serialized = json.dumps(result)
        for private in ['source_text_path', 'origins', 'verified_quotes', 'copyrighted', '/private/']:
            self.assertNotIn(private, serialized)


class PublicationTests(unittest.TestCase):
    def test_public_model_preserves_claims_but_rewrites_internal_links(self):
        original = ('# נשימה ושקט\n\nהמוח מתמכר לרעש [7].\n\n'
                    '[מפה](research/evidence-map.md)\n'
                    '[נתונים](research/library.json)\n\n'
                    '## Sources\n\n[7] https://example.org/study\n')
        mod = builder()
        self.assertTrue(hasattr(mod, 'public_model'), 'Public model conversion is not implemented')
        result = mod.public_model(original, '/course/')
        self.assertIn('המוח מתמכר לרעש', result)
        self.assertIn('/course/research/s007/', result)
        self.assertIn('/course/research/', result)
        self.assertIn('/course/assets/research.json', result)
        self.assertNotIn('research/library.json', result)
        self.assertNotIn('## Sources', result)


if __name__ == '__main__':
    unittest.main()
