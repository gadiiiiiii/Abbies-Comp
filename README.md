# Tonnetz Explorer

A local chord explorer with an interactive hexagonal Tonnetz map, synthesized
playback and weighted harmonic matches. The app has one explorer interface;
the Study feature, exports and study endpoints have been removed.

## Run locally

Requires Python 3; no third-party Python packages are needed.

```powershell
python app.py
```

Open http://127.0.0.1:8765, or double-click **Open Tonnetz Explorer.cmd** on
Windows. The previous `/explore` address still works. Keep the server running.
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
average step distances)`. Expand Details on a match to see all four components.
Scores describe harmonic structure, not a probability of liking a song.

All eight examples have four chords. Other lengths can be entered and played;
they show no matches when no example has that chord count. Progressions are never
silently padded or cropped. The app does not extract chords from audio or connect
to streaming accounts. Examples are chord sequences, not recordings.

## Performance

The graph is built once and updated in place. Match details are created only when
opened. Playback wakes at chord boundaries rather than polling every frame, and
suspends its audio context when idle. Request cancellation prevents old results
from replacing newer input. Repeated comparisons reuse bounded client/server
caches, and pure graph distances are cached without changing the scoring rules.
Static assets support ETag revalidation while refreshing after file edits.
The glass background is stationary to avoid continuous repainting.

The attributed catalog data and import tooling remain as offline developer
resources; they are not loaded by the explorer. Source licensing and attribution
are documented in [CATALOG_SOURCES.md](CATALOG_SOURCES.md).

## Local use and privacy

The server binds only to `127.0.0.1`, checks local Host/Origin values, and serves
an explicit list of app files. Keep it on your own device; it is not designed as
a public/shared web server. Chord entries are kept in memory for the current page. No accounts, telemetry,
or saved-study browser storage are used by the explorer.

## Verification

```powershell
python -m unittest discover -s tests -v
node tests/explorer_request_test.cjs
```

Tests cover weighted rankings, equal-length validation, P/L/R properties, API
protections, explanations, retired Study routes, static revalidation, immutable
cached responses, request cancellation and stale-response handling. Historical notes
in UPGRADE_PLAN.md and RESEARCH_REVIEW.md describe earlier versions; this README
documents current scoring.
