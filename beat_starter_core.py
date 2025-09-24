# Enhanced Beat Starter Core with MIDI export (requires 'pretty_midi' to write MIDI files)
# Save this file as beat_starter_core.py and run locally.
import json, random, datetime
from pathlib import Path

# NOTE: The MIDI export functions require 'pretty_midi' (pip install pretty_midi).
try:
    import pretty_midi
except Exception:
    pretty_midi = None

GENRE_KB = {
  "techno": {
    "bpm_range": [
      120,
      140
    ],
    "pattern": "4x4 kick | steady closed hi-hat on 8th notes | clap on 2 and 4",
    "instruments": [
      "Acid bass",
      "Analog lead",
      "White noise riser",
      "Perc loop"
    ],
    "structure": [
      "Intro",
      "Build",
      "Drop",
      "Breakdown",
      "Outro"
    ]
  },
  "techno_acid": {
    "bpm_range": [
      125,
      135
    ],
    "pattern": "4x4 kick | 16th acid bassline | hi-hat variation",
    "instruments": [
      "TB-303 acid bass",
      "Roland stab",
      "Closed hat",
      "Noise riser"
    ],
    "structure": [
      "Intro",
      "Acid groove",
      "Peak",
      "Breakdown",
      "Outro"
    ]
  },
  "techno_peak": {
    "bpm_range": [
      128,
      140
    ],
    "pattern": "Driving 4x4 kick | open hat on off-beats | percussive loops",
    "instruments": [
      "Punchy kick",
      "Sub bass",
      "Lead stab",
      "Perc loop"
    ],
    "structure": [
      "Intro",
      "Rise",
      "Peak",
      "Breakdown",
      "Peak 2",
      "Outro"
    ]
  },
  "industrial": {
    "bpm_range": [
      110,
      140
    ],
    "pattern": "Distorted kick | metallic hits | industrial percussion patterns",
    "instruments": [
      "Distorted kick",
      "Metallic percussion",
      "Harsh synth",
      "Noise"
    ],
    "structure": [
      "Intro (noise)",
      "Riff",
      "Aggressive section",
      "Break",
      "Outro"
    ]
  },
  "ebm": {
    "bpm_range": [
      120,
      135
    ],
    "pattern": "4x4 kick with driving bassline | stompy snare | minimal hats",
    "instruments": [
      "Synth bass",
      "Cold lead",
      "Punchy kick",
      "Perc hits"
    ],
    "structure": [
      "Intro",
      "Verse",
      "Chorus",
      "Verse",
      "Instrumental",
      "Outro"
    ]
  },
  "electro": {
    "bpm_range": [
      110,
      128
    ],
    "pattern": "Syncopated kicks | crisp hats | retro electric percussion",
    "instruments": [
      "FM bass",
      "Retro lead",
      "808-style kick",
      "Perc loops"
    ],
    "structure": [
      "Intro",
      "Build",
      "Drop",
      "Break",
      "Drop 2",
      "Outro"
    ]
  },
  "hiphop_boom_bap": {
    "bpm_range": [
      80,
      95
    ],
    "pattern": "Boom-bap kick/snare | swung hi-hat | chopped sample loop",
    "instruments": [
      "Boom-bap kick",
      "Snappy snare",
      "Warm bass",
      "Vocal sample"
    ],
    "structure": [
      "Intro",
      "Verse",
      "Chorus",
      "Verse",
      "Outro"
    ]
  },
  "hiphop_trap": {
    "bpm_range": [
      130,
      160
    ],
    "pattern": "Trap hi-hat rolls | deep 808 | punchy snare on 3",
    "instruments": [
      "808 sub",
      "Snare clap",
      "Pluck lead",
      "Hi-hat loop"
    ],
    "structure": [
      "Intro",
      "Verse",
      "Hook",
      "Verse",
      "Hook",
      "Outro"
    ]
  },
  "lofi": {
    "bpm_range": [
      60,
      90
    ],
    "pattern": "Soft kick | chopped samples | dusty percussion",
    "instruments": [
      "Crate-sampled piano",
      "Soft bass",
      "Brush snare",
      "Tape hiss"
    ],
    "structure": [
      "Intro",
      "Looped verse",
      "Short break",
      "Looped verse",
      "Outro"
    ]
  },
  "experimental": {
    "bpm_range": [
      60,
      150
    ],
    "pattern": "Non-linear percussion | irregular accents | noise textures",
    "instruments": [
      "Found sound samples",
      "Granular synth",
      "Textural pads",
      "Perc objects"
    ],
    "structure": [
      "Freeform",
      "Improvisation slots",
      "Noise bridge",
      "Outro"
    ]
  }
}

DEFAULT_GENRE = "techno"

def _choose_genre_key(genre_input):
    g = genre_input.strip().lower().replace(" ", "_")
    if g in GENRE_KB:
        return g
    for key in GENRE_KB:
        if key in g or g in key:
            return key
    return DEFAULT_GENRE

def generate_beat_plan(genre_input: str, mood: str=None, energy: int=None, seed: int=None):
    if seed is not None:
        random.seed(seed)
    genre_key = _choose_genre_key(genre_input)
    kb = GENRE_KB[genre_key]
    bpm = random.randint(kb["bpm_range"][0], kb["bpm_range"][1])
    if energy is not None:
        shift = int((energy - 5) * 0.8)
        bpm = max(kb["bpm_range"][0], min(kb["bpm_range"][1], bpm + shift))
    instruments = random.sample(kb["instruments"], k=min(3, len(kb["instruments"])))
    structure = kb["structure"].copy()
    if random.random() < 0.4:
        insert_pos = random.randint(1, max(1, len(structure)-2))
        structure.insert(insert_pos, "Short Fill / Transition")
    drum_template = []
    for bar in range(1,9):
        fill = ""
        if bar % 4 == 0 and random.random() < 0.5:
            fill = " + small fill"
        drum_template.append(f"Bar {{bar}}: Kick on 1, hat on 8th notes{{fill}}")
    plan = {
        "genre": genre_key,
        "requested_genre": genre_input,
        "bpm": bpm,
        "mood": mood or "neutral",
        "energy": energy or 5,
        "drum_pattern_summary": kb["pattern"],
        "drum_template_8bars": drum_template,
        "instruments": instruments,
        "structure": structure,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "notes": "MIDI export available: drums + simple bassline. To export MIDI, install 'pretty_midi'."
    }
    return plan

def save_plan_json(plan: dict, filename: str=None):
    p = Path("/mnt/data")
    p.mkdir(parents=True, exist_ok=True)
    if filename is None:
        filename = f"beat_plan_{plan['genre']}_{int(datetime.datetime.utcnow().timestamp())}.json"
    path = p / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    return str(path)

def export_midi(plan: dict, filename: str=None, drums=True, bass=True, bars=8):
    """Export a simple MIDI file based on the plan.
    This function requires 'pretty_midi'. If 'pretty_midi' is not installed, it will raise an Exception.
    - drums: include kick/snare/hihat on percussion channel
    - bass: include a simple bassline on a bass instrument
    - bars: number of bars to generate (4/4)
    """
    if pretty_midi is None:
        raise RuntimeError("pretty_midi is not installed. Run: pip install pretty_midi")
    if filename is None:
        filename = f"beat_{plan['genre']}_{int(datetime.datetime.utcnow().timestamp())}.mid"
    out_dir = Path("/mnt/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    bpm = plan.get("bpm", 120)
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    # Drums
    if drums:
        drum = pretty_midi.Instrument(program=0, is_drum=True, name="Drum Kit")
        seconds_per_beat = 60.0 / bpm
        beats_per_bar = 4
        total_beats = bars * beats_per_bar
        for beat_idx in range(total_beats):
            t = beat_idx * seconds_per_beat
            kick_note = pretty_midi.Note(velocity=100, pitch=36, start=t, end=t+0.05)
            drum.notes.append(kick_note)
            if (beat_idx % 4) in (1, 3):
                snare = pretty_midi.Note(velocity=90, pitch=38, start=t, end=t+0.05)
                drum.notes.append(snare)
            hh_t1 = t
            hh_t2 = t + seconds_per_beat * 0.5
            hh1 = pretty_midi.Note(velocity=70, pitch=42, start=hh_t1, end=hh_t1+0.02)
            hh2 = pretty_midi.Note(velocity=65, pitch=42, start=hh_t2, end=hh_t2+0.02)
            drum.notes.extend([hh1, hh2])
        pm.instruments.append(drum)
    # Bass
    if bass:
        bass_inst = pretty_midi.Instrument(program=34, is_drum=False, name="Electric Bass")
        genre = plan.get("genre", "techno")
        root_map = { "techno": 36, "industrial": 40, "ebm": 38, "electro": 37, "hiphop_boom_bap": 45, "hiphop_trap": 40, "lofi": 48, "experimental": 50 }
        root = root_map.get(genre, 36)
        seconds_per_beat = 60.0 / bpm
        beats_per_bar = 4
        for beat_idx in range(bars * beats_per_bar):
            t = beat_idx * seconds_per_beat
            if beat_idx % 2 == 0:
                end = t + seconds_per_beat * 1.9
            else:
                end = t + seconds_per_beat * 0.9
            note = pretty_midi.Note(velocity=80, pitch=root, start=t, end=end)
            bass_inst.notes.append(note)
        pm.instruments.append(bass_inst)
    pm.write(str(path))
    return str(path)
