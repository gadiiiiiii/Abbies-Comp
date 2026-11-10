import json
import unittest
from analysis import parse_study, study_data
from curated_catalog import catalog_songs
from replay_study import verify
from tonnetz import SAMPLE_SONGS, TonnetzRecommender


class CuratedStudyTests(unittest.TestCase):
    def inputs(self):
        source = catalog_songs()[0]
        return {'songs': [{'catalog_id': source['id'], 'title': source['title'] + ' — ' + source['artist'],
                           'progression': ' '.join(source['chords'])},
                          {'title': 'Comparison', 'progression': ' '.join(source['chords'])}]}

    def test_provenance_survives_export_and_replay(self):
        songs, mode = parse_study(self.inputs())
        report = study_data(TonnetzRecommender(SAMPLE_SONGS), songs, mode)
        saved = json.loads(json.dumps(report))
        for song in saved['songs']:
            if 'provenance' not in song:
                continue
            self.assertIn('original_chords', song['provenance'])
            self.assertEqual(len(song['chords']), len(song['provenance']['original_chords']))
        self.assertIn('data/curated-input.json', saved['reproducibility']['source_sha256'])
        self.assertTrue(verify(saved)['results_match'])
        saved['songs'][0]['provenance']['license'] = 'altered'
        self.assertFalse(verify(saved)['results_match'])

    def test_source_identity_cannot_label_changed_chords(self):
        for key, value in [('progression', 'C'), ('title', 'Wrong title'), ('catalog_id', 'unknown')]:
            payload = self.inputs()
            payload['songs'][0][key] = value
            with self.assertRaises(ValueError):
                parse_study(payload)
