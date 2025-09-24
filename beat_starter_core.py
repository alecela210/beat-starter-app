import random
import json

# Try importing pretty_midi (for MIDI export)
try:
    import pretty_midi
    HAS_MIDI = True
except ImportError:
    HAS_MIDI = False


# ----------------------------------------------------
# 🥁 Drum Template Generator
# ----------------------------------------------------
def generate_drum_template(genre, bars=8, mood="neutral", energy=5):
    patterns = {
        "techno": [
            "4/4 kick with offbeat open hat",
            "Kick on every beat, snare/clap on 2 and 4",
            "Driving groove with layered percussion",
        ],
        "hiphop": [
            "Boom-bap kick/snare, swung hi-hats",
            "Trap-style 808 kick with rapid hi-hats",
            "Lo-fi groove with dusty clap",
        ],
        "industrial": [
            "Distorted kick and snare with machine-gun hats",
            "Broken beat with metallic percussion",
            "Layered noise hits and syncopated groove",
        ],
        "ebm": [
            "Pulsing kick, clap every 4 bars",
            "Kick on 1, tom fills on 3",
            "Kick/snare syncopation with aggressive hats",
        ],
        "electro": [
            "Kick on 1 and 3, snare on 2 and 4",
            "Classic 808 groove with rimshots",
            "Funky syncopated beat with 16th hats",
        ],
    }

    genre_key = genre.lower().split("_")[0]
    genre_patterns = patterns.get(genre_key, patterns["techno"])

    drum_template = []
    for bar in range(1, bars + 1):
        base = random.choice(genre_patterns)
        fill = ""

        # Variation logic
        if bar % 4 == 0:
            fill += " + short fill"
        if bar % 8 == 0:
            fill += " + transition"

        # Mood and energy adjustments
        if energy > 7:
            fill += " + extra percussion"
        elif energy < 4:
            fill += " + stripped-down feel"
        if "dark" in mood.lower():
            fill += " + darker timbre"
        if "uplifting" in mood.lower():
            fill += " + brighter groove"

        drum_template.append(f"Bar {bar}: {base}{fill}")
    return drum_template


# ----------------------------------------------------
# 🎛️ Beat Plan Generator
# ----------------------------------------------------
def generate_beat_plan(genre="techno", bpm=125, mood="neutral", energy=5, bars=8):
    plan = {
        "genre": genre,
        "bpm": bpm,
        "mood": mood,
        "energy": energy,
        "drum_pattern_summary": f"{genre.title()} groove with {mood} mood at {energy}/10 energy",
        "drum_template_8bars": generate_drum_template(genre, bars, mood, energy),
        "instruments": ["Kick", "Snare", "Hi-hat", "Bass"],
        "structure": ["Intro", "Verse", "Chorus", "Verse", "Outro"],
    }
    return plan


# ----------------------------------------------------
# 💾 Save JSON Plan
# ----------------------------------------------------
def save_plan_json(plan, filename="beat_plan.json"):
    with open(filename, "w") as f:
        json.dump(plan, f, indent=4)
    return filename


# ----------------------------------------------------
# 🎹 MIDI Export
# ----------------------------------------------------
def export_midi(plan, filename="beat_skeleton.mid", include_bass=False):
    if not HAS_MIDI:
        raise ImportError("pretty_midi is not installed. Run: pip install pretty_midi")

    bpm = plan.get("bpm", 120)
    beats_per_second = bpm / 60.0
    seconds_per_bar = 4 / beats_per_second  # 4/4 time

    midi = pretty_midi.PrettyMIDI()

    # Drums
    drums = pretty_midi.Instrument(program=0, is_drum=True)
    midi.instruments.append(drums)

    for bar_index, bar in enumerate(plan["drum_template_8bars"]):
        start_time = bar_index * seconds_per_bar

        # Kick (note 36)
        kick = pretty_midi.Note(
            velocity=100,
            pitch=36,
            start=start_time,
            end=start_time + 0.1,
        )
        drums.notes.append(kick)

        # Snare (note 38)
        snare_time = start_time + seconds_per_bar / 2
        snare = pretty_midi.Note(
            velocity=95,
            pitch=38,
            start=snare_time,
            end=snare_time + 0.1,
        )
        drums.notes.append(snare)

        # Hi-hats (note 42) - 8th notes
        for i in range(8):
            hat_time = start_time + i * (seconds_per_bar / 8)
            hat = pretty_midi.Note(
                velocity=70,
                pitch=42,
                start=hat_time,
                end=hat_time + 0.05,
            )
            drums.notes.append(hat)

    # Optional bassline
    if include_bass:
        bass = pretty_midi.Instrument(program=32)  # Fingered bass
        midi.instruments.append(bass)
        root_notes = [36, 38, 41, 43]  # Basic bass pattern (C, D, F, G)
        for bar_index in range(len(plan["drum_template_8bars"])):
            start_time = bar_index * seconds_per_bar
            pitch = random.choice(root_notes)
            note = pretty_midi.Note(
                velocity=100,
                pitch=pitch,
                start=start_time,
                end=start_time + seconds_per_bar,
            )
            bass.notes.append(note)

    midi.write(filename)
    return filename


# ----------------------------------------------------
# 🧪 Test (if run directly)
# ----------------------------------------------------
if __name__ == "__main__":
    plan = generate_beat_plan("hiphop", bpm=90, mood="dark", energy=7)
    save_plan_json(plan)
    if HAS_MIDI:
        export_midi(plan, "demo.mid", include_bass=True)
        print("✅ MIDI exported as demo.mid")
    else:
        print("⚠️ pretty_midi not installed — JSON only")
