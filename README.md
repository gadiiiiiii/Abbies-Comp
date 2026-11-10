# Tonnetz Explorer

A local chord explorer and comparison lab with an interactive hexagonal Tonnetz
map, synthesized playback, weighted similarity scores, and reproducible exports.

## Run locally

Requires Python 3; no third-party Python packages are needed.

```powershell
python app.py --explore
```

Open http://127.0.0.1:8765/explore, or double-click **Open Tonnetz Explorer.cmd**
on Windows. The study lab is at http://127.0.0.1:8765/. Keep the server running.
Add `--no-browser` to start without opening a browser.

## Scoring model

`tonnetz.py` uses the user-supplied weighted prototype, with compatibility aliases
for existing browser imports. This intentionally replaces DTW and changes rankings.

- Major/minor triads form a 24-chord P/L/R graph. Breadth-first search finds chord
  distances as the shortest number of transformations.
- Progressions must have **the same number of chords**. Compare matching positions,
  without warping, padding, truncation, or repeated alignment positions.
- Across-key mode chooses the first of 12 transpositions with the lowest average
  position-by-position distance. It does not optimize the weighted score.
- Recommendations rank by **40% chord content + 30% transformation sequence +
  20% trajectory + 10% compactness**, descending with stable ties.

Chord content is set Jaccard similarity. Transformation similarity is one minus
normalized Hamming distance between direct P/L/R-label sequences. Non-neighbor
transitions share a dash label, exactly as in the supplied code. Trajectory is
`1 / (1 + average distance)`. Compactness is `1 / (1 + absolute difference between
average step distances)`. UI details and readable reports show all four components.
Scores describe harmonic structure, not a probability of liking a song.

All eight examples have four chords. Other lengths can be entered and played;
Explore shows no matches when no example has that chord count. Use Study to compare
2–5 custom or catalog progressions of the same length. The two attributed catalog
excerpts have different lengths and cannot be directly compared with each other
under this model; they are never silently cropped.

## Studies and reports

Custom entries stay in browser local storage. Download study JSON for inputs,
calculations, source fingerprints and provenance, or a readable HTML report to
read/print offline. Downloads include entered titles/chords; review before sharing.
The app does not extract chords from audio or connect to streaming accounts.

```powershell
python replay_study.py "C:/path/to/tonnetz-study-file.json"
```

Imports validate inputs and recalculate with the current engine. Old DTW exports
with equal-length inputs can be reopened, with changed scores and source hashes
reported. Unequal-length studies are rejected with a clear message. Fingerprints
support reproducibility, not authenticity.

Catalog excerpts retain original symbols, reductions, attribution and source
licensing; see [CATALOG_SOURCES.md](CATALOG_SOURCES.md). They are short excerpts,
not independently audio-verified full-song analyses.

## Local use and privacy

The server binds only to `127.0.0.1`, checks local Host/Origin values, and serves
an explicit list of app files. Keep it on your own device; it is not designed as
a public/shared web server. Browser-saved entries and downloaded studies are not
part of this repository.

## Verification

```powershell
python -m unittest discover -s tests -v
node tests/analysis_request_test.cjs
```

Tests cover weighted rankings, equal-length validation, P/L/R properties, API
protections, explanations, provenance, replay and escaped HTML. Historical notes
in UPGRADE_PLAN.md and RESEARCH_REVIEW.md describe earlier versions; this README
documents current scoring.
