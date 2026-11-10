"""Regression fixtures for the user-supplied weighted prototype."""
import unittest

from tonnetz import (Chord, SAMPLE_SONGS, TonnetzChordGraph, TonnetzRecommender,
                     progression_distance, parse_chord, transform, transpose_progression,
                     transposition_invariant_distance, weighted_similarity)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.graph = TonnetzChordGraph()

    def test_known_transformations(self):
        for operation, expected in [("P", "Cm"), ("L", "Em"), ("R", "Am")]:
            with self.subTest(operation=operation):
                self.assertEqual(transform(parse_chord("C"), operation), parse_chord(expected))
                self.assertEqual(self.graph.distance(parse_chord("C"), parse_chord(expected)), 1)

    def test_transformations_are_involutions_and_keep_two_notes(self):
        self.assertEqual(len(self.graph.nodes), 24)
        for chord in self.graph.nodes:
            for operation in "PLR":
                neighbor = transform(chord, operation)
                self.assertEqual(transform(neighbor, operation), chord)
                self.assertEqual(len(chord.pcs & neighbor.pcs), 2)

    def test_shortest_routes_reach_every_chord(self):
        start = parse_chord("C")
        for goal in self.graph.nodes:
            route = self.graph.shortest_path(start, goal)
            self.assertEqual(route[0], (start, None))
            self.assertEqual(route[-1][0], goal)
            self.assertEqual(len(route) - 1, self.graph.distance(start, goal))
            for (previous, _), (chord, operation) in zip(route, route[1:]):
                self.assertEqual(transform(previous, operation), chord)

    def test_position_comparison_and_equal_length_rule(self):
        c, am = parse_chord("C"), parse_chord("Am")
        self.assertEqual(progression_distance(self.graph, [c], [am]), (1.0, [(0, 0)]))
        with self.assertRaises(ValueError):
            progression_distance(self.graph, [c], [c, c])
        with self.assertRaises(ValueError):
            progression_distance(self.graph, [], [c])
        # Disjoint single-chord sets: 0*.4 + 1*.3 + .5*.2 + 1*.1 = .5.
        self.assertAlmostEqual(weighted_similarity(self.graph, [c], [am]), .5)
        self.assertAlmostEqual(weighted_similarity(self.graph, [c], [c]), 1)

    def test_transposition_preserves_equivalence(self):
        original = SAMPLE_SONGS[0].chords
        for shift in range(12):
            distance, winning_shift, path = transposition_invariant_distance(
                self.graph, original, transpose_progression(original, shift))
            self.assertEqual(distance, 0)
            self.assertEqual(winning_shift, (-shift) % 12)
            self.assertEqual(path, [(0, 0), (1, 1), (2, 2), (3, 3)])

    def test_supported_spelling_and_rejected_extensions(self):
        self.assertEqual(parse_chord("D#m"), Chord(3, "minor"))
        self.assertEqual(parse_chord("Db major"), Chord(1, "major"))
        for symbol in ["", "C7", "Csus4", "C/G", "H"]:
            with self.subTest(symbol=symbol), self.assertRaises(ValueError):
                parse_chord(symbol)

    def test_all_sample_rankings_and_transpositions(self):
        # Intentional scoring migration: fixtures checked against the uploaded source.
        # Each tuple is (ranked title suffixes, weighted scores, semitone shifts).
        fixtures = [
            ("CDEHFBG", [1, 1, 1, 1, .675, .53333333, .31333333], [7, 6, 5, 9, 0, 0, 5]),
            ("FACDEHG", [.67, .53333333, .53333333, .53333333, .53333333, .53333333, .48], [0, 0, 7, 6, 5, 9, 0]),
            ("ADEHFBG", [1, 1, 1, 1, .675, .53333333, .31333333], [5, 11, 10, 2, 5, 5, 10]),
            ("ACEHFBG", [1, 1, 1, 1, .675, .53333333, .31333333], [6, 1, 11, 3, 6, 6, 11]),
            ("ACDHFBG", [1, 1, 1, 1, .675, .53333333, .31333333], [7, 2, 1, 4, 7, 7, 0]),
            ("ACDEHBG", [.675, .675, .675, .675, .675, .67, .29880952], [0, 7, 6, 5, 9, 0, 2]),
            ("BACDEHF", [.48, .31333333, .31333333, .31333333, .31333333, .31333333, .29880952], [0, 7, 2, 1, 0, 4, 2]),
            ("ACDEFBG", [1, 1, 1, 1, .675, .53333333, .31333333], [3, 10, 9, 8, 3, 3, 8]),
        ]
        recommender = TonnetzRecommender(SAMPLE_SONGS)
        for song, (titles, scores, shifts) in zip(SAMPLE_SONGS, fixtures):
            with self.subTest(song=song.title):
                results = recommender.recommend(song, top_k=7)
                self.assertEqual([r["song"].title for r in results], ["Song " + t for t in titles])
                self.assertEqual([r["shift"] for r in results], shifts)
                for result, score in zip(results, scores):
                    self.assertAlmostEqual(result["weighted_similarity"], score)
                    self.assertAlmostEqual(result["similarity"], 1 / (1 + result["distance"]))
                    self.assertEqual(result["path"], [(i, i) for i in range(4)])


if __name__ == "__main__":
    unittest.main()
