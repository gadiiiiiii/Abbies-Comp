from collections import deque
from functools import lru_cache
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
#Here we are assigning integer values to our pitches, creating our pitch class
pitch_to_pc = {"C": 0, "B#": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "Fb": 4,"E#": 5, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,"Cb": 11, }
pc_to_pitch = {0: "C", 1: "C#", 2: "D", 3: "Eb", 4: "E", 5: "F", 6: "F#", 7: "G", 8: "Ab", 9: "A", 10: "Bb", 11: "B", }

@dataclass(frozen=True)
class Chord:
    root: int
    quality: str
    @property #creating our chord classes, making our chords computer readable by assigning integers in a set
    def pcs(self) -> frozenset:
        if self.quality == "major":
            intervals = (0, 4, 7)
        elif self.quality == "minor":
            intervals = (0, 3, 7)
        else:
            raise ValueError("Only major and minor triads are supported.")
        return frozenset((self.root + i) % 12 for i in intervals)
    @property
    def name(self) -> str:
        suffix = "m" if self.quality == "minor" else ""
        return pc_to_pitch[self.root] + suffix
#taking a string, such as a chord name and making them sets, includes chord names, this was taken from github and modified
def parse_chord(text: str) -> Chord:
    text = text.strip()
    if not text:
        raise ValueError("Empty chord.")
    root_name = None
    for candidate in sorted(pitch_to_pc, key=len, reverse=True):
        if text.startswith(candidate):
            root_name = candidate
            break
    if root_name is None:
        raise ValueError(f"Could not understand chord: {text}")
    remainder = text[len(root_name):].strip().lower()
    if remainder in ("", "maj", "major"):
        quality = "major"
    elif remainder in ("m", "min", "minor"):
        quality = "minor"
    else:
        raise ValueError(f"Unsupported chord '{text}'")
    return Chord(pitch_to_pc[root_name], quality)

#Here we are defining our P,L,R transformations, which will determine the connections between chords in our graph
def transform(chord: Chord, operation: str) -> Chord:
    operation = operation.upper()
    r = chord.root
    if chord.quality == "major":
        if operation == "P":
            return Chord(r, "minor")
        if operation == "L":
            return Chord((r + 4) % 12, "minor")
        if operation == "R":
            return Chord((r + 9) % 12, "minor")
    else:
        if operation == "P":
            return Chord(r, "major")
        if operation == "L":
            return Chord((r + 8) % 12, "major")
        if operation == "R":
            return Chord((r + 3) % 12, "major")
    raise ValueError(f"Unknown transformation: {operation}")
#here we are creating the nodes and connect each chord to its relative P,L,R neighbors
class Tonnetzchordgraph:
    def __init__(self) -> None:
        self.nodes: List[Chord] = [
            Chord(root, quality)
            for root in range(12)
            for quality in ("major", "minor")]
        self.adjacency: Dict[Chord, Dict[Chord, str]] = {node: {} for node in self.nodes}
        for chord in self.nodes:
            for op in ("P", "L", "R"):
                neighbor = transform(chord, op)
                self.adjacency[chord][neighbor] = op
#Calculating the shortest distance between two chords/triads using Breadth-first search algorithm
    @lru_cache(maxsize=576)
    def distance(self, start: Chord, goal: Chord) -> int:
        if start == goal:
            return 0
        queue = deque([(start, 0)])
        visited = {start}
        while queue:
            current, dist = queue.popleft()
            for neighbor in self.adjacency[current]:
                if neighbor == goal:
                    return dist + 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        raise RuntimeError("Tonnetz graph is disconnected")
#now finding the shortest path
    def shortest_path(self, start: Chord, goal: Chord) -> List[Tuple[Chord, Optional[str]]]:
        if start == goal:
            return [(start, None)]
        queue = deque([start])
        previous: Dict[Chord, Tuple[Optional[Chord], Optional[str]]] = {
            start: (None, None)}
        while queue:
            current = queue.popleft()
            for neighbor, op in self.adjacency[current].items():
                if neighbor in previous:
                    continue
                previous[neighbor] = (current, op)
                if neighbor == goal:
                    queue.clear()
                    break
                queue.append(neighbor)
        if goal not in previous:
            raise RuntimeError("No path found")
        path: List[Tuple[Chord, Optional[str]]] = []
        current = goal
        while current is not None:
            prev, op = previous[current]
            path.append((current, op))
            current = prev
        path.reverse()
        return path
#identifying which transformation connects the two directly connected chords, so where the distance between two chords is the number of P/L/R moves needed to travel between them
    def transformation_label(self, a: Chord, b: Chord) -> str:
        if b in self.adjacency[a]:
            return self.adjacency[a][b]
        return "—"
#This is where we transpose chords and chord progressions to different key signatures and organize a given song as a list of chords to find a best fit.
def transpose_chord(chord: Chord, semitones: int) -> Chord:
    return Chord((chord.root + semitones) % 12, chord.quality)
def transpose_progression(progression: Sequence[Chord], semitones: int) -> List[Chord]:
    return [transpose_chord(c, semitones) for c in progression]
#the song class stores a title and it chord progression
@dataclass
class Song:
    title: str
    chords: List[Chord]
    @classmethod
    def from_text(cls, title: str, progression: str) -> "Song":
        tokens = [x for x in progression.replace("->", " ").replace(",", " ").split() if x]
        return cls(title, [parse_chord(token) for token in tokens])
    def progression_text(self) -> str:
        return " -> ".join(chord.name for chord in self.chords)

# Calculating distance between two chords using BFS
def chord_distance(graph: Tonnetzchordgraph, a: Chord, b: Chord) -> float:
    return float(graph.distance(a, b))

# Compare two chord progressions position by position
def progression_distance(graph: Tonnetzchordgraph,a: Sequence[Chord],b: Sequence[Chord]) -> Tuple[float, List[Tuple[int, int]]]:
    if not a or not b:
        raise ValueError("Songs must contain at least one chord.")
    if len(a) != len(b):
        raise ValueError("Progressions must contain the same number of chords")
    distances = []
    comparison_path = []
    for i, (chord_a, chord_b) in enumerate(zip(a, b)):
        distances.append(chord_distance(graph, chord_a, chord_b))
        comparison_path.append((i, i))
    average_distance = sum(distances) / len(distances)
    return average_distance, comparison_path

# Compare all 12 possible transpositions of a candidate progression and select the one with the smallest average tonnetz distance
def transposition_invariant_distance(graph: Tonnetzchordgraph,a: Sequence[Chord],b: Sequence[Chord]) -> Tuple[float, int, List[Tuple[int, int]]]:
    best = (float("inf"), 0, [])
    for shift in range(12):
        shifted = transpose_progression(b, shift)
        distance, comparison_path = progression_distance(graph, a, shifted)
        if distance < best[0]:
            best = (distance, shift, comparison_path)
    return best

#converting the distance into a similarity score using S = 1/(1+D)
def similarity_from_distance(distance: float) -> float:
    return 1.0 / (1.0 + distance)

#Jaccard similarity is implemented as well
def chord_content_similarity(a: Sequence[Chord], b: Sequence[Chord]) -> float:
    chords_a = set(a)
    chords_b = set(b)
    union = chords_a | chords_b
    if not union:
        return 1.0
    return len(chords_a & chords_b) / len(union)

#This is where we include our Hamming distance
def transformation_similarity(graph: Tonnetzchordgraph,a: Sequence[Chord],b: Sequence[Chord]) -> float:
    #Compare P/L/R transformation sequences
    seq_a = transformation_sequence(graph, a)
    seq_b = transformation_sequence(graph, b)
    if len(seq_a) != len(seq_b):
        raise ValueError("Transformation sequences must have the same length.")
    #If both sequences are empty, then they are the same still
    if len(seq_a) == 0:
        return 1.0
    #Count the number of different positions
    differences = sum(x != y for x, y in zip(seq_a, seq_b))
    # Convert Hamming distance into a similarity score
    return 1.0 - differences / len(seq_a)
# Compare the overall movement of two chord progressions
# using direct chord-by-chord tonnetz distances
def trajectory_similarity(graph: Tonnetzchordgraph,a: Sequence[Chord],b: Sequence[Chord]) -> float:
    distance, _ = progression_distance(graph, a, b)
    return similarity_from_distance(distance)

def average_step_distance(graph: Tonnetzchordgraph,progression: Sequence[Chord]) -> float:
    if len(progression) < 2:
        return 0.0
    distances = [chord_distance(graph, a, b)
        for a, b in zip(progression, progression[1:])]
    return sum(distances) / len(distances)

def compactness_similarity(graph: Tonnetzchordgraph,a: Sequence[Chord],b: Sequence[Chord]) -> float:
    #Compare the average step distances of two chord progressions
    compactness_a = average_step_distance(graph, a)
    compactness_b = average_step_distance(graph, b)
    difference = abs(compactness_a - compactness_b)
    return 1.0 / (1.0 + difference)

# Initial weights: started with 25 across, then changed to run our experiments
def weighted_similarity(graph: Tonnetzchordgraph,a: Sequence[Chord],b: Sequence[Chord]) -> float:
    w_chord = 0.40
    w_transformation = 0.30
    w_trajectory = 0.20
    w_compactness = 0.10
    s_chord = chord_content_similarity(a, b)
    s_transformation = transformation_similarity(graph, a, b)
    s_trajectory = trajectory_similarity(graph, a, b)
    s_compactness = compactness_similarity(graph, a, b)
    return w_chord * s_chord+ w_transformation * s_transformation+ w_trajectory * s_trajectory+ w_compactness * s_compactness
#Here the shared chord identifies chords shared by can two progressions and the transformation sequence lists the P/L/R transformations between consecutive chords
def shared_chords(a: Sequence[Chord], b: Sequence[Chord]) -> List[str]:
    aset = {c for c in a}
    bset = {c for c in b}
    return [c.name for c in a if c in bset and c in aset]
def transformation_sequence(graph: Tonnetzchordgraph,progression: Sequence[Chord]) -> List[str]:
    result = []
    for a, b in zip(progression, progression[1:]):
        result.append(graph.transformation_label(a, b))
    return result
#note: the shared chords and transformation sequence are not separate weighted components in the similarity score, but are used to display info about the recs
#this is where we compare the target song against another song
class TonnetzRecommender:
    def __init__(self, songs: Sequence[Song]) -> None:
        self.graph = Tonnetzchordgraph()
        self.songs = list(songs)
    def recommend(self,target: Song,top_k: int = 5,transpose_invariant: bool = True) -> List[dict]:
        results = []
        for candidate in self.songs:
            if candidate.title == target.title:
                continue
            if transpose_invariant:
                distance, shift, path = transposition_invariant_distance(self.graph,target.chords, candidate.chords)
            else:
                distance, path = progression_distance(self.graph, target.chords,candidate.chords)
                shift = 0
            similarity = similarity_from_distance(distance)

            # Align the candidate to the best transposition
            aligned_candidate = transpose_progression(candidate.chords, shift)

            # Calculate the four-feature weighted similarity
            weighted_score = weighted_similarity(self.graph,target.chords,aligned_candidate)
            results.append({ "song": candidate,"distance": distance,"similarity": similarity,"weighted_similarity": weighted_score,"shift": shift,"path": path,})

        # Rank recommendations using the four-weight similarity score
        results.sort(key=lambda x: x["weighted_similarity"],reverse=True)
        return results[:top_k]

sampsongs = [Song.from_text("Song A", "C Am F G"),
                Song.from_text("Song B", "C Em F G"),
                Song.from_text("Song C", "F Dm Bb C"),
                Song.from_text("Song D", "F# D#m B C#"),
                Song.from_text("Song E", "G Em C D"),
                Song.from_text("Song F", "Am F C G"),
                Song.from_text("Song G", "C G Am F"),
                Song.from_text("Song H", "Eb Cm Ab Bb")]

#everything below is to display the results/outputs
def print_song_list(songs: Sequence[Song]) -> None:
    print("\n Chord progression library")
    print("-" * 60)
    for i, song in enumerate(songs, start=1):
        print(f"{i:2}. {song.title:15} {song.progression_text()}")

def print_result(target: Song, result: dict, recommender: TonnetzRecommender) -> None:
    song = result["song"]
    distance = result["distance"]
    similarity = result["similarity"]
    shift = result["shift"]
    path = result["path"]

    print(f"\n{song.title}")
    print(f"  Progression: {song.progression_text()}")
    print(f"  Tonnetz distance: {distance:.3f}")
    print(f"  Harmonic similarity: {similarity * 100:.1f}%")
    print(f"  Four-weight similarity: " f"{result['weighted_similarity'] * 100:.1f}%")
    if shift:
        print(f"Best transposition alignment: +{shift} semitones")
    else:
        print("Best transposition alignment: 0 semitones")

    shared = shared_chords(target.chords, song.chords)
    if shared:
        print(f"Shared chords: {', '.join(shared)}")
    else:
        print("Shared chords: none")

    target_transforms = transformation_sequence(recommender.graph, target.chords)
    candidate_transforms = transformation_sequence(recommender.graph, song.chords)
    print(f"  Target P/L/R path:     {' -> '.join(target_transforms) or 'single chord'}")
    print(f"  Candidate P/L/R path:  {' -> '.join(candidate_transforms) or 'single chord'}")

    print("Direct chord comparison:")
    for i, j in path[:8]:
        print(f"{target.chords[i].name:4}  <->  "f"{transpose_progression(song.chords, shift)[j].name:4}")
    if len(path) > 8:
        print("...")
#this just runs the demo pretty much
def run_demo() -> None:
    recommender = TonnetzRecommender(sampsongs)
    print("Tonnetz Music Recommendation System")
    print("Mathematical model: Z_12 -> triads -> P/L/R graph -> BFS -> weighted similarity")
    print_song_list(sampsongs)
    print("\nChoose a song number or type a custom progression.")
    choice = input("Your choice: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(sampsongs):
        target = sampsongs[int(choice) - 1]
    else:
        progression = choice
        target = Song.from_text("Your Song", progression)
    print("\nSelected:")
    print(f"  {target.title}: {target.progression_text()}")
    results = recommender.recommend(target, top_k=5, transpose_invariant=True)
    print("\n" + "=" * 60)
    print("Recommendations")
    print("=" * 60)
    for rank, result in enumerate(results, start=1):
        print(f"\n#{rank}")
        print_result(target, result, recommender)
    print("\n" + "=" * 60)
    print("NOTE:")
    print("This prototype measures harmonic similarity using a tonnetz")
    print("chicken-wire graph. It does not measure timbre,")
    print("lyrics, production, or other dimensions of music preference and does not claim to provide full user satisfaction.")
# Compatibility names for the browser application.
TonnetzChordGraph = Tonnetzchordgraph
SAMPLE_SONGS = sampsongs
PITCH_TO_PC = pitch_to_pc
PC_TO_PITCH = pc_to_pitch

if __name__ == "__main__":
    run_demo()