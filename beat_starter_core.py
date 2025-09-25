# beat_starter_core.py
# Advanced Beat Starter core with pro MIDI generation
# Drop this file in your project replacing the previous core.
# Requires: pretty_midi for MIDI export (pip install pretty_midi)

import random
import json
import math

# Try importing pretty_midi (for MIDI export)
try:
    import pretty_midi
    HAS_MIDI = True
except Exception:
    pretty_midi = None
    HAS_MIDI = False


# -------------------------
# Helper: musical utilities
# -------------------------
SCALES = {
    "minor": [0, 2, 3, 5, 7, 8, 10],   # natural minor intervals
    "major": [0, 2, 4, 5, 7, 9, 11],   # major intervals
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "aeolian": [0, 2, 3, 5, 7, 8, 10],
}

GENRE_ROOTS = {
    "techno": 36,       # C2
    "techno_acid": 36,
    "techno_peak": 36,
    "industrial": 40,   # E2-ish
    "ebm": 38,          # D2#
    "electro": 37,      # C#2
    "trance": 48,       # C3
    "house": 36,
    "tech_house": 36,
    "deep_house": 36,
    "uk_garage": 38,
    "hiphop_boom_bap": 45,
    "hiphop_west_coast": 43,
    "hiphop_trap": 40,
    "reggaeton_dembow": 46,
    "lofi": 48,
    "pop": 48,
    "rock": 40,
    "afrobeat": 48,
    "jazz_swing": 50,
    "experimental": 50,
    "default": 36
}

def pick_genre_root(genre_key):
    return GENRE_ROOTS.get(genre_key, GENRE_ROOTS["default"])

def scale_notes(root_midi, scale_name="minor", octave=0, length=8):
    """
    Return a list of MIDI note numbers following the given scale starting at root_midi.
    length = how many notes to return (repeats up octaves as needed).
    """
    intervals = SCALES.get(scale_name, SCALES["minor"])
    notes = []
    scale_len = len(intervals)
    for i in range(length):
        octave_shift = (i // scale_len) + octave
        interval = intervals[i % scale_len]
        notes.append(root_midi + interval + (12 * octave_shift))
    return notes


# -------------------------
# Drum rhythm helpers
# -------------------------
def quantize_time(t, grid):
    """Return nearest grid step for time t (not used heavily but handy)."""
    return round(t / grid) * grid

def add_note(instrument, pitch, start, duration, velocity=100):
    """Add a single note to a pretty_midi.Instrument (safeguard)."""
    instrument.notes.append(pretty_midi.Note(velocity=int(velocity),
                                             pitch=int(pitch),
                                             start=float(start),
                                             end=float(start + max(0.01, duration))))

def velocity_for(level, base=80, variation=12):
    """Return velocity based on level 0.0..1.0"""
    v = base + (variation * (level - 0.5))
    return max(25, min(127, int(v)))


# ---------------------------------
# Groove: swing & humanization helper
# ---------------------------------
def apply_swing_and_humanization(events, genre_key, energy_norm, swing_amount=0.06, humanize_intensity=0.6, bpm=120):
    """
    Apply genre-specific swing and humanization to event list (t, pitch, vel, dur).
    Enhanced for better musical cohesion and natural feel.
    """
    humanized = []
    
    # Genre-specific swing patterns
    if "drum_and_bass" in genre_key:
        # DnB typically uses less swing, more about timing precision
        swing_amount *= 0.5  # Reduce swing for DnB
        timing_humanize_range = 0.003  # Very tight timing
        vel_humanize_range = 0.03  # Subtle velocity variation
    elif "hiphop" in genre_key or "boom_bap" in genre_key:
        # Hip-hop benefits from more swing and looser timing
        swing_amount *= 1.2
        timing_humanize_range = 0.008
        vel_humanize_range = 0.06
    elif "techno" in genre_key or "industrial" in genre_key:
        # Techno needs mechanical precision
        swing_amount *= 0.3
        timing_humanize_range = 0.002
        vel_humanize_range = 0.02
    else:
        # Default settings
        timing_humanize_range = 0.005
        vel_humanize_range = 0.04
    
    # Energy affects humanization - higher energy = tighter; scaled by humanize_intensity (0..1.2)
    energy_factor = 1.0 - (energy_norm - 5) * 0.05
    energy_factor = max(0.5, min(1.0, energy_factor)) * max(0.2, min(1.2, humanize_intensity))
    
    seconds_per_beat = 60.0 / max(1, bpm)
    for t, pitch, vel, dur in events:
        # Swing: shift every other 16th note
        # Determine position within the current beat using BPM-aware timing
        beat_phase = (t / seconds_per_beat) % 1.0
        # Identify if within the "off" 16th (the second 16th within each 8th)
        # 16th boundaries at 0.0, 0.25, 0.5, 0.75 within a beat
        is_off_sixteenth = (0.25 <= beat_phase < 0.5) or (0.75 <= beat_phase < 1.0)
        if is_off_sixteenth:
            # Shift off-16ths later by swing_amount fraction of a beat
            swing_shift = swing_amount * seconds_per_beat
            new_t = t + swing_shift
        else:
            new_t = t
        
        # Velocity humanization - genre and energy dependent
        vel_variation = random.uniform(-vel_humanize_range, vel_humanize_range) * energy_factor
        new_vel = max(1, min(127, int(vel * (1 + vel_variation))))
        
        # Micro-timing humanization - very subtle and genre-dependent
        timing_humanize = random.uniform(-timing_humanize_range, timing_humanize_range) * energy_factor
        new_t += timing_humanize
        
        # Ensure we don't go negative in time
        new_t = max(0, new_t)
        
        humanized.append((new_t, pitch, new_vel, dur))
    return humanized


# -------------------------
# Pattern generation
# -------------------------
def _genre_key(genre_input):
    return genre_input.strip().lower().replace(" ", "_")

def generate_drum_events(genre, bpm, energy=5, bars=8, swing=0.06, break_preset="amen", snare_snap=False, hat_layout="standard", humanize_intensity=0.6, lofi_vinyl=False):
    """
    Generate a list of drum events (tuples): (time_seconds, midi_note, velocity, duration)
    We'll create percussive events for Kick(36), Snare(38), Hat closed(42), Hat open(46), Clap(39), Tom(48), Perc hits.
    energy: 1..10 controlling density and extra hits
    swing: fraction of a beat to swing 16th notes (positive shifts every other 16th)
    """
    beats_per_bar = 4
    seconds_per_beat = 60.0 / bpm
    seconds_per_bar = seconds_per_beat * beats_per_bar
    total_beats = bars * beats_per_bar

    events = []  # list of (time, pitch, vel, dur)

    genre_key = _genre_key(genre)
    energy_norm = max(1, min(10, energy))
    density = 0.5 + (energy_norm / 20.0)  # 0.55 .. 1.0 roughly
    aggressive = energy_norm >= 7

    # baseline patterns per genre (we'll add variations)
    if "tech_house" in genre_key:
        # Tech House: 4/4, strong offbeat open hats, claps on 2/4, extra percs
        for beat_idx in range(total_beats):
            t = beat_idx * seconds_per_beat
            events.append((t, 36, velocity_for(0.92, base=114), 0.1))  # kick
            # Offbeat open hat
            events.append((t + seconds_per_beat * 0.5, 46, velocity_for(0.78), 0.12))
            # Closed hat on quarters for drive
            events.append((t, 42, velocity_for(0.62), 0.03))
            if beat_idx % 4 in (1, 3):
                events.append((t, 39, velocity_for(0.88), 0.06))  # clap
            # Perc blips
            if random.random() < 0.25:
                events.append((t + seconds_per_beat*0.25, 49, velocity_for(0.55), 0.05))

    elif "deep_house" in genre_key:
        # Deep House: softer hats, laid-back claps, occasional rides
        for beat_idx in range(total_beats):
            t = beat_idx * seconds_per_beat
            events.append((t, 36, velocity_for(0.88, base=108), 0.1))
            events.append((t + seconds_per_beat * 0.5, 46, velocity_for(0.7), 0.1))
            if beat_idx % 4 in (1, 3):
                events.append((t, 39, velocity_for(0.78), 0.06))
            if random.random() < 0.15:
                events.append((t + seconds_per_beat*0.75, 51, velocity_for(0.55), 0.08))  # ride

    elif "uk_garage" in genre_key:
        # UK Garage (2-step): shuffled hats, syncopated kicks, claps on 2 & 4
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            # Kicks typical 1 and 2.5 with variations
            for kp in [0.0, 2.5]:
                events.append((bar_start + kp * seconds_per_beat, 36, velocity_for(0.9), 0.08))
            # Claps on 2 & 4
            for sp in [1.0, 3.0]:
                events.append((bar_start + sp * seconds_per_beat, 39, velocity_for(0.85), 0.06))
            # Shuffled 16th hats (emphasis on 3rd 16th each beat)
            step = seconds_per_bar/16.0
            for s in range(16):
                th = bar_start + s*step
                if s % 4 == 2:
                    v = velocity_for(0.72)
                elif s % 2 == 0:
                    v = velocity_for(0.6)
                else:
                    v = velocity_for(0.5)
                if random.random() < 0.9:
                    events.append((th, 42, v, 0.02))

    elif "house" in genre_key:
        # House: four-on-the-floor, offbeat open hats, claps on 2 & 4
        for beat_idx in range(total_beats):
            t = beat_idx * seconds_per_beat
            # Kick every beat
            events.append((t, 36, velocity_for(0.9, base=112), 0.1))
            # Closed hat on quarters, open hat on off-beats
            events.append((t, 42, velocity_for(0.6), 0.03))
            off = t + seconds_per_beat * 0.5
            events.append((off, 46, velocity_for(0.75), 0.12))
            # Clap on 2 & 4
            if beat_idx % 4 in (1, 3):
                events.append((t, 39, velocity_for(0.85), 0.06))
        # Small variations
        if energy_norm >= 6:
            for _ in range(bars):
                tt = random.uniform(0, seconds_per_bar * bars)
                events.append((tt, 42, velocity_for(0.6), 0.02))

    elif "reggaeton_dembow" in genre_key:
        # Reggaeton Dembow basic pattern
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            # Kicks
            for kp in [0.0, 2.5]:
                events.append((bar_start + kp * seconds_per_beat, 36, velocity_for(0.9, base=110), 0.08))
            # Snares/Claps (dembow accents)
            for sp in [1.75, 3.5]:
                events.append((bar_start + sp * seconds_per_beat, 39, velocity_for(0.9), 0.07))
            # Hats 8ths
            for i in range(8):
                th = bar_start + i * (seconds_per_bar / 8.0)
                events.append((th, 42, velocity_for(0.58), 0.03))
            # Shaker swing feel
            if random.random() < 0.5:
                for i in [1,3,5,7]:
                    ts = bar_start + i * (seconds_per_bar/8.0) + 0.01
                    events.append((ts, 82, velocity_for(0.45), 0.05))

    elif "techno" in genre_key:
        # Dark Techno family: rigid 4/4, strong offbeat open-hats, minimal swing, mechanical consistency
        is_peak = "peak" in genre_key
        is_acid = "acid" in genre_key

        for beat_idx in range(total_beats):
            t = beat_idx * seconds_per_beat
            # Kick: heavy and consistent on every beat
            events.append((t, 36, velocity_for(0.97 if is_peak else 0.95, base=116 if is_peak else 114), 0.1))

            # Closed hat on quarters (very light), strong offbeat open hat
            events.append((t, 42, velocity_for(0.5), 0.02))
            off = t + seconds_per_beat * 0.5
            events.append((off, 46, velocity_for(0.82 if is_peak else 0.78), 0.12))

            # Clap on 2 & 4 for peak techno; sparser for standard/acid
            if beat_idx % 4 in (1, 3):
                if is_peak and energy_norm >= 5:
                    events.append((t, 39, velocity_for(0.78), 0.05))
                elif random.random() < 0.35:
                    events.append((t, 39, velocity_for(0.68), 0.05))

            # Metallic ticks slightly after the kick to add grit
            if beat_idx % 2 == 0 and random.random() < (0.35 if is_peak else 0.25):
                events.append((t + seconds_per_beat * 0.25, 49, velocity_for(0.52), 0.04))  # perc
            # Short ride ping occasionally (peak)
            if is_peak and random.random() < 0.15:
                events.append((t + seconds_per_beat * 0.75, 51, velocity_for(0.5), 0.04))

            # Acid accent: extra 16th off-hat in last quarter
            if is_acid:
                q4 = t + seconds_per_beat * 0.75
                if random.random() < 0.5:
                    events.append((q4 + seconds_per_beat * 0.125, 42, velocity_for(0.58), 0.015))

        # Section marker: crash only at start when energy is high
        if energy_norm >= 7:
            events.append((0.0, 49, velocity_for(0.85), 0.4))

    elif "trance" in genre_key:
        for beat_idx in range(total_beats):
            t = beat_idx * seconds_per_beat
            # Kick on 1/beat, layered higher velocity
            events.append((t, 36, velocity_for(1.0, base=115), 0.1))
            # hats 16ths for more energy (depending on energy)
            sixteenth_count = 4 if energy_norm < 6 else 8
            step = seconds_per_beat / (sixteenth_count // 1)
            for s in range(sixteenth_count):
                st = t + s * step
                if s % 2 == 0:
                    events.append((st, 42, velocity_for(0.7 + energy_norm/30.0), 0.02))
                else:
                    if random.random() < 0.6:
                        events.append((st, 42, velocity_for(0.6), 0.02))
            # percussion + trance-style claps every 2 bars
            if beat_idx % 8 == 0 and random.random() < 0.6:
                events.append((t + seconds_per_beat * 0.5, 39, velocity_for(0.9), 0.06))

    elif "industrial" in genre_key:
        for beat_idx in range(total_beats):
            t = beat_idx * seconds_per_beat
            # heavy kick with random double hits
            events.append((t, 36, velocity_for(0.95, base=120), 0.12))
            if random.random() < 0.25 * density:
                events.append((t + seconds_per_beat * 0.25, 36, velocity_for(0.7), 0.07))
            # metallic hits: use tom/percussion notes (47,48,49)
            if random.random() < 0.6 * density:
                events.append((t + seconds_per_beat * random.random(), random.choice([47,48,49,51]), velocity_for(0.8), 0.05))
            # noisy snares/claps
            if beat_idx % 2 == 1 and random.random() < 0.8 * density:
                events.append((t + seconds_per_beat * 0.5, 38, velocity_for(0.95), 0.08))

    elif "hiphop_boom_bap" in genre_key:
        # Boom Bap (DJ Premier-style): hard snares on 2 and 4, chunky kicks, swung 8th hats, ghost snares
        swing_8th = 0.04  # laid back
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            # Occasionally use a rim-only bar (intro/break flavor)
            rim_only_bar = (bar % 8 == 4 and random.random() < 0.7)
            # Main backbeat snares on 2 and 4 (slightly late for laid-back feel)
            for sn in [1.0, 3.0]:
                t_sn = bar_start + sn * seconds_per_beat + (0.01 if energy_norm <= 6 else 0.005)
                if rim_only_bar:
                    # Rim click instead of full snare/clap
                    events.append((t_sn, 37, velocity_for(0.7), 0.06))
                else:
                    events.append((t_sn, 38, velocity_for(0.95, base=118), 0.08))
                    # Layer occasional clap
                    if random.random() < 0.4:
                        events.append((t_sn, 39, velocity_for(0.7), 0.06))
                # Ghost just before snare
                if (not rim_only_bar) and random.random() < 0.6:
                    events.append((t_sn - seconds_per_beat * 0.125, 38, velocity_for(0.45, base=85), 0.03))
            
            # Kicks: boom on 1, pickup before 2, boom on 3, occasional pickup before 4
            kick_positions = [0.0, 1.75, 3.0]
            if random.random() < 0.5:
                kick_positions.append(0.5)
            if random.random() < 0.35:
                kick_positions.append(2.5)
            for kp in kick_positions:
                events.append((bar_start + kp * seconds_per_beat, 36, velocity_for(0.92, base=115), 0.09))
            
            # Swung 8th hats with accented offbeats before snares, occasional open hat before snare
            for i in range(8):
                t_hat = bar_start + i * (seconds_per_bar / 8.0)
                if i % 2 == 1:
                    t_hat += swing_8th
                # Accents: offbeat before snares (i=1 and i=5) get more velocity
                if i in [1, 5]:
                    v_hat = velocity_for(0.68)
                elif i % 2 == 0:
                    v_hat = velocity_for(0.6)
                else:
                    v_hat = velocity_for(0.62)
                events.append((t_hat, 42, v_hat, 0.03))
                # Open hat leading into snare
                if i in [1, 5] and random.random() < 0.35:
                    events.append((t_hat + seconds_per_beat * 0.45, 46, velocity_for(0.56), 0.08))
            # Low-energy shaker to glue groove
            if energy_norm <= 4:
                for i in [1, 3, 5, 7]:
                    t_shk = bar_start + i * (seconds_per_bar / 8.0)
                    if random.random() < 0.6:
                        events.append((t_shk, 82, velocity_for(0.4), 0.05))
            # Optional vinyl ticks layer
            if lofi_vinyl:
                for i in range(16):
                    tv = bar_start + i * (seconds_per_bar / 16.0) + random.uniform(-0.003, 0.003)
                    if random.random() < 0.3:
                        events.append((tv, 42, velocity_for(0.28, base=60, variation=6), 0.01))
            
            # Occasional rim clicks and percs
            if random.random() < 0.3:
                events.append((bar_start + 2.25 * seconds_per_beat, 37, velocity_for(0.5), 0.03))

    elif "hiphop_west_coast" in genre_key:
        # West Coast (Dr. Dre-style): laid-back swing, sparse heavy kicks, clap/rim on 2 & 4, tambourine/shaker feel
        swing_8th = 0.03
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            # Occasional rim-only first backbeat for arrangement flavor
            rim_intro = (bar % 8 == 0 and random.random() < 0.5)
            # Claps/Rims on 2 and 4
            for sn in [1.0, 3.0]:
                t_sn = bar_start + sn * seconds_per_beat + 0.008
                if rim_intro and sn == 1.0:
                    events.append((t_sn, 37, velocity_for(0.75), 0.06))  # rim instead of clap/snare on first backbeat
                else:
                    # Clap flam: small pre-hit before main clap for width
                    if random.random() < 0.6:
                        events.append((t_sn - 0.012, 39, velocity_for(0.55), 0.06))
                    events.append((t_sn, 39, velocity_for(0.92, base=115), 0.08))  # clap
                    events.append((t_sn, 38, velocity_for(0.75, base=105), 0.06))  # snare layer
            
            # Kicks: 1, occasional 1.75, 3; sometimes 3.75 pickup
            kick_positions = [0.0, 3.0]
            if random.random() < 0.45:
                kick_positions.append(1.75)
            if random.random() < 0.3:
                kick_positions.append(3.75)
            for kp in kick_positions:
                events.append((bar_start + kp * seconds_per_beat, 36, velocity_for(0.95, base=118), 0.1))
            
            # Hats/Tambourine: steady 8ths with slight swing, occasional open hat
            for i in range(8):
                t_hat = bar_start + i * (seconds_per_bar / 8.0)
                if i % 2 == 1:
                    t_hat += swing_8th
                events.append((t_hat, 42, velocity_for(0.58), 0.03))
                if random.random() < 0.2 and i in [1, 5]:
                    events.append((t_hat + seconds_per_beat * 0.5, 46, velocity_for(0.5), 0.06))
            
            # Accent shaker on offbeats
            for i in [1, 3, 5, 7]:
                if random.random() < 0.5:
                    t_shk = bar_start + i * (seconds_per_bar / 8.0)
                    events.append((t_shk, 82, velocity_for(0.45), 0.05))  # High shaker

    elif "ebm" in genre_key or "electro" in genre_key:
        for beat_idx in range(total_beats):
            t = beat_idx * seconds_per_beat
            events.append((t, 36, velocity_for(0.95), 0.09))
            # syncopated hats
            if beat_idx % 2 == 0:
                events.append((t + seconds_per_beat * 0.25, 42, velocity_for(0.6), 0.02))
            if random.random() < 0.4 * density:
                events.append((t + seconds_per_beat * 0.5, 49, velocity_for(0.7), 0.04))

    elif "drum_and_bass" in genre_key:
        # DnB: Classic Jungle (Amen/Think), Liquid, Stepper, Neurofunk
        for bar in range(bars):
            bar_start = bar * seconds_per_bar

            if "classic" in genre_key:
                # 16-step grid per bar (4/4), snares on steps 4 and 12
                # Different break presets with unique kick/snare patterns
                if break_preset == "amen":
                    kick_steps = {0, 6, 8, 15}  # Classic Amen break pattern
                    snare_steps = {4, 12}
                elif break_preset == "think":
                    kick_steps = {0, 4, 8, 12}  # Think break - more regular kicks
                    snare_steps = {4, 12}
                elif break_preset == "tight":
                    kick_steps = {0, 2, 8, 10}  # Tight break - syncopated
                    snare_steps = {4, 12}
                else:
                    kick_steps = {0, 6, 8, 15}  # Default to Amen
                    snare_steps = {4, 12}
                
                # Energy variations - more subtle additions
                if energy_norm >= 7:
                    if break_preset == "think":
                        kick_steps.update({6})
                    else:
                        kick_steps.update({10})
                if energy_norm >= 9:
                    if break_preset == "tight":
                        kick_steps.update({14})
                    else:
                        kick_steps.update({14})

                step_duration = seconds_per_bar / 16.0

                # Kicks
                for s in sorted(kick_steps):
                    t = bar_start + s * step_duration
                    events.append((t, 36, velocity_for(0.92, base=118), 0.04))

                # Snares (main backbeats) - with optional snap/flam
                for s in sorted(snare_steps):
                    t = bar_start + s * step_duration
                    # Higher velocity for harder backbeat when snap is enabled
                    snare_velocity = velocity_for(0.98, base=120) if snare_snap else velocity_for(0.95, base=115)
                    events.append((t, 38, snare_velocity, 0.05))
                    
                    # Add flam-like extra hit for snap (very short, slightly before)
                    if snare_snap and random.random() < 0.7:
                        flam_t = t - 0.01  # 10ms before main hit
                        flam_velocity = snare_velocity * 0.7
                        events.append((flam_t, 38, int(flam_velocity), 0.02))

                # Ghost snares a 16th before the backbeat - energy affects probability
                ghost_probability = 0.5 + (energy_norm * 0.05)  # 0.55 to 0.95
                for s in sorted(snare_steps):
                    ghost_s = max(0, s - 1)
                    if random.random() < ghost_probability:
                        t = bar_start + ghost_s * step_duration
                        events.append((t, 38, velocity_for(0.45, base=85), 0.03))

                # Hats on all 16ths with different layout options
                hat_density = 0.85 + (energy_norm * 0.01)  # 0.9 to 0.95
                for s in range(16):
                    t = bar_start + s * step_duration
                    
                    # Different hat layouts for break feel
                    if hat_layout == "standard":
                        # Standard: quarter notes > off-quarters > other 16ths
                        if s % 4 == 0:
                            v = velocity_for(0.8)  # quarters
                        elif s % 2 == 0:
                            v = velocity_for(0.7)
                        else:
                            v = velocity_for(0.6)
                    elif hat_layout == "break":
                        # Break feel: emphasize 3rd 16th per beat for classic break
                        if s % 4 == 2:  # 3rd 16th
                            v = velocity_for(0.85)  # emphasized
                        elif s % 4 == 0:
                            v = velocity_for(0.75)
                        else:
                            v = velocity_for(0.55)
                    elif hat_layout == "sparse":
                        # Sparse: only quarters and off-quarters, more space
                        if s % 4 == 0:
                            v = velocity_for(0.8)
                        elif s % 4 == 2:
                            v = velocity_for(0.6)
                        else:
                            continue  # skip other 16ths
                    else:
                        # Default to standard
                        if s % 4 == 0:
                            v = velocity_for(0.8)
                        elif s % 2 == 0:
                            v = velocity_for(0.7)
                        else:
                            v = velocity_for(0.6)
                    
                    if random.random() < hat_density:
                        events.append((t, 42, v, 0.015))
                
                # Add shaker layer for break feel at higher energy
                if energy_norm >= 6 and hat_layout == "break":
                    for s in range(0, 16, 4):  # Every quarter note
                        t = bar_start + s * step_duration
                        events.append((t, 43, velocity_for(0.4), 0.1))  # Shaker

                # Bar-end snare fill every 4 bars
                if (bar + 1) % 4 == 0 and random.random() < 0.8:
                    for s in [13, 14, 15]:  # last three 16ths
                        t = bar_start + s * step_duration
                        events.append((t, 38, velocity_for(0.8), 0.03))
                
                # Crash/impact sounds on transitions at higher energy
                if energy_norm >= 7:
                    # Crash on bar 1 (start of pattern)
                    if bar == 0:
                        t = bar_start
                        events.append((t, 49, velocity_for(0.9), 0.5))  # Crash cymbal
                    
                    # Impact/riser on last 16th of bar 4 (transition)
                    if bar == 3 and energy_norm >= 8:
                        t = bar_start + 15 * step_duration
                        events.append((t, 57, velocity_for(0.7), 0.2))  # Impact/cymbal
                
                # Additional percussion at high energy
                if energy_norm >= 8:
                    # Random percussion hits for variation
                    for s in [1, 5, 9, 13]:  # Off-beat 16ths
                        if random.random() < 0.3:
                            t = bar_start + s * step_duration
                            events.append((t, 44, velocity_for(0.5), 0.04))  # Pedal hi-hat

            elif "stepper" in genre_key:
                # Stepper (Chase & Status style): tight two-step, heavy snares on 2 & 4, driving hats
                # Backbeats
                snare_times = [bar_start + seconds_per_beat * 1.0, bar_start + seconds_per_beat * 3.0]
                for st in snare_times:
                    events.append((st, 38, velocity_for(0.96, base=118), 0.05))
                # Kicks: 1, 1.75 pickup, 3.25 drive
                for kp in [0.0, 1.75, 3.25]:
                    events.append((bar_start + kp * seconds_per_beat, 36, velocity_for(0.94, base=118), 0.05))
                # Hats: straight 16ths with quarter accents
                step = seconds_per_bar / 16.0
                for s in range(16):
                    th = bar_start + s * step
                    if s % 4 == 0:
                        v = velocity_for(0.78)
                    elif s % 2 == 0:
                        v = velocity_for(0.68)
                    else:
                        v = velocity_for(0.58)
                    events.append((th, 42, v, 0.015))
                # Ride at offbeats occasionally
                if random.random() < 0.4:
                    for i in (1, 3):
                        events.append((bar_start + i * seconds_per_beat, 51, velocity_for(0.6), 0.04))
                # Crash at section start
                if bar == 0 and energy_norm >= 7:
                    events.append((bar_start, 49, velocity_for(0.9), 0.4))

            elif "neuro" in genre_key:
                # Neurofunk: precise snares, syncopated kicks, relentless hats, extra percs
                # Backbeats
                for st in [1.0, 3.0]:
                    events.append((bar_start + st * seconds_per_beat, 38, velocity_for(0.97, base=120), 0.05))
                # Kicks: 1, 2.25, 3.5 (common neuro syncopes)
                for kp in [0.0, 2.25, 3.5]:
                    events.append((bar_start + kp * seconds_per_beat, 36, velocity_for(0.95, base=120), 0.045))
                # 16th hats with strong off accents
                step = seconds_per_bar / 16.0
                for s in range(16):
                    th = bar_start + s * step
                    v = 0.8 if s % 4 == 2 else (0.7 if s % 2 == 0 else 0.6)
                    events.append((th, 42, velocity_for(v), 0.012))
                # Perc shots
                if energy_norm >= 7 and random.random() < 0.6:
                    for s in [3, 7, 11, 15]:
                        events.append((bar_start + s * step, 44, velocity_for(0.55), 0.03))

            else:
                # Liquid / general DnB template (rides, smoother dynamics)
                # Main snares on 2 and 4
                snare_times = [bar_start + seconds_per_beat * 1.0, bar_start + seconds_per_beat * 3.0]
                for stime in snare_times:
                    events.append((stime, 38, velocity_for(0.9, base=112), 0.05))
                # Ghost snares slightly before main
                for stime in snare_times:
                    if random.random() < 0.6:
                        events.append((stime - seconds_per_beat * 0.25, 38, velocity_for(0.45, base=85), 0.03))
                # Kicks pattern: 1.0 and 3.5 base, variations by energy
                kick_positions = [0.0, 3.5]
                if energy_norm >= 6:
                    kick_positions += [1.5]
                if energy_norm >= 8:
                    kick_positions += [2.25]
                for kp in kick_positions:
                    events.append((bar_start + kp * seconds_per_beat, 36, velocity_for(0.9, base=115), 0.04))
                # Hats: 16th grid with slight velocity shaping
                for i in range(16):
                    t_hat = bar_start + i * (seconds_per_bar / 16.0)
                    base_v = 0.65 if i % 4 != 0 else 0.75  # emphasize quarters
                    if random.random() < 0.9:
                        events.append((t_hat, 42, velocity_for(base_v), 0.015))
                # Rides on offbeats (liquid feel)
                if random.random() < 0.7:
                    for i in (1, 3):
                        events.append((bar_start + i * seconds_per_beat, 51, velocity_for(0.6), 0.05))  # ride

        # Extra ghost hits at high energy
        if energy_norm >= 8:
            for _ in range(bars):
                t = random.uniform(0, seconds_per_bar * bars)
                events.append((t, 38, velocity_for(0.4), 0.02))

    else:
        # Additional generic styles
        if "pop" in genre_key:
            for beat_idx in range(total_beats):
                t = beat_idx * seconds_per_beat
                if beat_idx % 2 == 0:
                    events.append((t, 36, velocity_for(0.88), 0.08))  # 1 & 3 kick
                else:
                    events.append((t, 38, velocity_for(0.9), 0.08))   # 2 & 4 snare
                # 8th hats
                for sub in (0, 0.5):
                    events.append((t + sub*seconds_per_beat, 42, velocity_for(0.6), 0.02))
        elif "rock" in genre_key:
            for beat_idx in range(total_beats):
                t = beat_idx * seconds_per_beat
                if beat_idx % 2 == 0:
                    events.append((t, 36, velocity_for(0.95, base=118), 0.1))
                else:
                    events.append((t, 38, velocity_for(0.92, base=116), 0.09))
                # 8th hats or ride after half
                if beat_idx < total_beats//2:
                    for sub in (0, 0.5):
                        events.append((t + sub*seconds_per_beat, 42, velocity_for(0.62), 0.03))
                else:
                    for sub in (0, 0.5):
                        events.append((t + sub*seconds_per_beat, 51, velocity_for(0.6), 0.05))
                # Crash at start of sections
                if beat_idx % 8 == 0:
                    events.append((t, 49, velocity_for(0.9), 0.5))
        elif "afrobeat" in genre_key:
            for bar in range(bars):
                bs = bar * seconds_per_bar
                # Snare/clap light on 2 & 4
                for sp in [1.0, 3.0]:
                    events.append((bs + sp*seconds_per_beat, 39, velocity_for(0.75), 0.06))
                # Syncopated kicks
                for kp in [0.0, 1.5, 2.75]:
                    events.append((bs + kp*seconds_per_beat, 36, velocity_for(0.88), 0.08))
                # Offbeat hats/shakers
                for i in range(8):
                    th = bs + i*(seconds_per_bar/8.0) + (0.0 if i%2==0 else 0.01)
                    midi = 82 if i%2==1 else 42
                    events.append((th, midi, velocity_for(0.55), 0.04))
        elif "jazz_swing" in genre_key:
            # Ride swing pattern, hihat on 2 & 4, light snare ghosts, occasional kick feather
            for bar in range(bars):
                bs = bar * seconds_per_bar
                # Ride pattern (ding-ding-da-ding) approximated on quarters and triplet skip
                for beat in range(4):
                    t = bs + beat*seconds_per_beat
                    events.append((t, 51, velocity_for(0.6), seconds_per_beat*0.1))
                    events.append((t + seconds_per_beat*2/3.0, 51, velocity_for(0.5), seconds_per_beat*0.08))
                # Hat on 2 & 4
                for sp in [1.0, 3.0]:
                    events.append((bs + sp*seconds_per_beat, 42, velocity_for(0.65), 0.04))
                # Light snare ghosts
                for g in [0.75, 2.75]:
                    events.append((bs + g*seconds_per_beat, 38, velocity_for(0.4, base=70), 0.03))
                # Feathered kick on 1 occasionally
                if random.random() < 0.5:
                    events.append((bs, 36, velocity_for(0.4, base=70), 0.05))
        else:
            # default generic 4/4
            for beat_idx in range(total_beats):
                t = beat_idx * seconds_per_beat
                events.append((t, 36, velocity_for(0.9), 0.08))
                if beat_idx % 2 == 1:
                    events.append((t, 38, velocity_for(0.85), 0.07))
                # hats on 8th
                for sub in (0, 0.5):
                    st = t + sub * seconds_per_beat
                    events.append((st, 42, velocity_for(0.6), 0.02))

    # Enhanced energy scaling
    if energy_norm >= 8:
        # High energy: lots of layers, fast hats, dense fills
        for _ in range(int(bars * 3)):
            t = random.uniform(0, seconds_per_bar * bars)
            # More ghost notes
            if random.random() < 0.8:
                events.append((t, 38, velocity_for(0.3), 0.02))
            else:
                events.append((t, random.choice([47,48,49,51]), velocity_for(0.4), 0.02))
        # Faster hi-hat patterns
        for beat_idx in range(total_beats * 2):  # Double the resolution
            t = beat_idx * (seconds_per_beat / 2)
            if random.random() < 0.9:
                events.append((t, 42, velocity_for(0.7), 0.015))
    elif energy_norm >= 5:
        # Medium energy: moderate layers
        for _ in range(int(bars * 1.5)):
            t = random.uniform(0, seconds_per_bar * bars)
            if random.random() < 0.6:
                events.append((t, 38, velocity_for(0.4), 0.025))
            else:
                events.append((t, random.choice([47,48,49]), velocity_for(0.5), 0.025))
    elif energy_norm <= 3:
        # Low energy: lots of space, minimal elements
        # Remove some events to create space
        events = [e for e in events if random.random() < 0.7]  # Remove 30% of events
        # Add more space between elements
        spaced_events = []
        for i, event in enumerate(events):
            if i > 0:
                # Add gap between similar events
                if event[1] == events[i-1][1]:  # Same instrument
                    spaced_events.append((event[0] + 0.02, event[1], event[2], event[3]))
                else:
                    spaced_events.append(event)
            else:
                spaced_events.append(event)
        events = spaced_events

    # Apply swing and humanization for better groove
    events = apply_swing_and_humanization(events, genre_key, energy_norm, humanize_intensity=humanize_intensity, bpm=bpm)
    
    # Final sort by time
    events.sort(key=lambda x: x[0])
    return events


# -------------------------
# Bassline generation (OVERHAULED)
# -------------------------
def generate_bass_events(genre, bpm, energy=5, bars=8, mood="neutral", humanize_intensity=0.6):
    """
    Generate bass events: returns list of (time, midi_note, velocity, duration)
    Enhanced for better musical cohesion with drums and genre-appropriate patterns.
    """
    beats_per_bar = 4
    seconds_per_beat = 60.0 / bpm
    seconds_per_bar = seconds_per_beat * beats_per_bar

    genre_key = _genre_key(genre)
    root = pick_genre_root(genre_key)
    energy_norm = (energy - 1) / 9.0  # normalize to 0-1
    
    # Choose scale based on mood and genre - more sophisticated mapping
    if "dark" in mood.lower() or "industrial" in genre_key or "hard" in genre_key:
        scale_name = "phrygian" if "industrial" in genre_key else "aeolian"
    elif "uplifting" in mood.lower() or "trance" in genre_key:
        scale_name = "major"
    else:
        scale_name = "minor"
    
    # Root + 5th + octave pattern (human-like variation)
    base_notes = [0, 7, 12]  # root, 5th, octave
    scale_intervals = SCALES.get(scale_name, SCALES["minor"])
    notes_pool = [root + interval for interval in base_notes]
    
    # Add some variation - occasionally use 3rd or 6th
    if random.random() < 0.3:
        variation_notes = [3, 9] if scale_name == "major" else [3, 8]
        notes_pool.extend([root + interval for interval in variation_notes])
    
    events = []
    energy_norm = max(1, min(10, energy))
    density = 0.4 + (energy_norm / 15.0)  # More controlled density
    
    # Generate kick pattern first to lock bass to it
    kick_times = []
    for bar in range(bars):
        bar_start = bar * seconds_per_bar
        # Different kick patterns per genre
        if "techno" in genre_key:
            # Techno: every beat
            kick_times.extend([bar_start + i * seconds_per_beat for i in range(4)])
        elif "hiphop_boom_bap" in genre_key:
            # Boom Bap: 1, pickup before 2 (1.75), 3 (core accents)
            for pos in [0.0, 1.75, 3.0]:
                kick_times.append(bar_start + pos * seconds_per_beat)
        elif "hiphop_west_coast" in genre_key:
            # West Coast: strong 1 and 3 with occasional pickups
            core = [0.0, 3.0]
            pickups = [1.75, 3.75] if energy_norm >= 6 else [1.75]
            for pos in core + pickups:
                kick_times.append(bar_start + pos * seconds_per_beat)
        elif "hiphop" in genre_key or "trap" in genre_key:
            # Generic Hip-hop/Trap fallback
            kick_times.extend([bar_start, bar_start + 2 * seconds_per_beat])
            if "trap" in genre_key and random.random() < 0.4:
                kick_times.append(bar_start + 2.5 * seconds_per_beat)
        elif "drum_and_bass" in genre_key:
            # DnB: syncopated, more complex
            kick_times.extend([bar_start + i * seconds_per_beat for i in [0, 1.5, 2.5, 3.5]])
        else:
            # Default: every other beat
            kick_times.extend([bar_start, bar_start + 2 * seconds_per_beat])
    
    # Lock bass to kick placement with human variation
    for kick_time in kick_times:
        # Bass hits slightly before or on kick (human feel)
        bass_offset = random.uniform(-0.02, 0.01) if energy_norm > 5 else -0.01
        t = kick_time + bass_offset
        
        # Choose note - favor root (70%), 5th (20%), octave (10%)
        note_weights = [0.7, 0.2, 0.1] + [0.025] * len(notes_pool[3:]) if len(notes_pool) > 3 else [0.7, 0.2, 0.1]
        pitch = random.choices(notes_pool, weights=note_weights[:len(notes_pool)])[0]
        
        # Duration based on energy and genre
        if genre_key in ["techno", "hardtechno"]:
            dur = seconds_per_beat * 0.25 if energy_norm > 7 else seconds_per_beat * 0.5
        elif "hiphop_boom_bap" in genre_key:
            # Punchy, shorter notes that sit with the kick
            dur = seconds_per_beat * (0.4 if energy_norm >= 6 else 0.55)
        elif "hiphop_west_coast" in genre_key:
            # More sustained, laid-back bass
            dur = seconds_per_beat * (1.0 if energy_norm <= 7 else 0.8)
        elif "hiphop" in genre_key:
            dur = seconds_per_beat * 0.75
        else:
            dur = seconds_per_beat * (0.5 if energy_norm > 6 else 1.0)
        
        # Velocity dynamics
        vel_base = 75 if "techno" in genre_key else 85
        vel_variation = 15 if energy_norm > 7 else 10
        vel = velocity_for(0.8, base=vel_base, variation=vel_variation)
        
        # Occasionally add octave jumps for energy
        if random.random() < (energy_norm / 20.0):
            pitch += 12
        
        events.append((t, pitch, vel, dur))
    
    # Add some fills and variations for higher energy
    if energy_norm >= 7:
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            # Occasional 16th note fills
            if random.random() < 0.3:
                for i in range(4):
                    t = bar_start + i * (seconds_per_beat / 4)
                    if random.random() < 0.6:  # Only 60% of potential fill notes
                        pitch = events[-1][1] if events else (root + 12)
                        events.append((t, pitch, velocity_for(0.6), seconds_per_beat / 8))

    # Apply subtle humanization to bass for natural groove
    events = apply_swing_and_humanization(events, genre_key, energy_norm, swing_amount=0.02, humanize_intensity=humanize_intensity, bpm=bpm)

    events.sort(key=lambda x: x[0])
    return events


# -------------------------
# Melody generation (NEW)
# -------------------------
def generate_melody_events(genre, bpm, energy=5, bars=8, mood="neutral", humanize_intensity=0.6):
    """
    Generate melody events list: (time, midi_note, velocity, duration)
    Enhanced for better musical cohesion with drums and bass.
    """
    beats_per_bar = 4
    seconds_per_beat = 60.0 / bpm
    seconds_per_bar = seconds_per_beat * beats_per_bar

    genre_key = _genre_key(genre)
    root = pick_genre_root(genre_key)
    energy_norm = (energy - 1) / 9.0  # normalize to 0-1
    
    # Choose scale based on mood/genre - ensure consistency with bass
    if "dark" in mood.lower() or "industrial" in genre_key or "hard" in genre_key:
        scale_name = "phrygian" if "industrial" in genre_key else "aeolian"
    elif "uplifting" in mood.lower() or "trance" in genre_key:
        scale_name = "major"
    else:
        scale_name = "minor"

    intervals = SCALES.get(scale_name, SCALES["minor"])
    events = []

    if "techno" in genre_key:
        # Repetitive stabs that complement the driving kick
        melody_root = root + 12
        # Use scale-consistent arpeggio
        scale_notes = [melody_root + i for i in intervals[:5]]
        arpeggio = [0, 2, 4, 2, 0]  # More musical arpeggio pattern
        
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            # Main stabs on downbeats - lock with kick
            for beat in (0, 2):
                t = bar_start + beat * seconds_per_beat
                arp_idx = int(beat / 2) % len(arpeggio)
                pitch = scale_notes[arp_idx % len(scale_notes)]
                events.append((t, pitch, velocity_for(0.7), seconds_per_beat * 0.25))
                
                # Offbeat accents - complement hats
                if random.random() < 0.4 and energy_norm >= 5:
                    t_off = t + seconds_per_beat * 0.5
                    pitch_off = scale_notes[(arp_idx + 2) % len(scale_notes)]
                    events.append((t_off, pitch_off, velocity_for(0.55), seconds_per_beat * 0.15))

    elif "trance" in genre_key or "uplifting" in genre_key:
        # Trance: flowing melodies that support the build
        melody_root = root + 24
        # Use consistent scale
        notes = [melody_root + i for i in intervals]
        # Create more musical motif
        motif = [0, 2, 4, 7, 4, 2, 0]  # Classic trance progression
        
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            # Evolving motif that builds energy
            for i, step in enumerate(motif):
                t = bar_start + i * (seconds_per_bar / len(motif))
                if random.random() < 0.85:
                    pitch = notes[step % len(notes)]
                    # Velocity builds through the bar
                    vel_factor = 0.7 + (i / len(motif)) * 0.2
                    events.append((t, pitch, velocity_for(vel_factor), seconds_per_beat * 0.5))
            
            # Add counter-melody at higher energy
            if energy_norm >= 7 and bar % 2 == 0:
                counter_notes = [melody_root + i for i in intervals[2:5]]  # Higher register
                for i in range(4):
                    t = bar_start + i * seconds_per_beat + seconds_per_beat * 0.25
                    pitch = counter_notes[i % len(counter_notes)]
                    events.append((t, pitch, velocity_for(0.4), seconds_per_beat * 0.25))

    elif "drum_and_bass" in genre_key:
        # DnB: chopped melodies that complement breakbeats
        melody_root = root + 12
        notes = [melody_root + d for d in intervals[:7]]
        
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            
            if "classic" in genre_key:
                # Classic DnB: sparse, rhythmic chops that work with drums
                # Place notes on off-beats to complement kick/snare pattern
                chop_positions = [1, 3, 5, 7, 9, 11, 13, 15]  # 16th note off-beats
                for pos in chop_positions:
                    if random.random() < 0.5:  # 50% chance for each position
                        t = bar_start + pos * (seconds_per_bar / 16.0)
                        # Choose notes that work with the harmony
                        if pos % 4 == 1:  # Strong off-beats
                            pitch = notes[0]  # Root
                            vel = velocity_for(0.7)
                        elif pos % 4 == 3:  # Medium off-beats
                            pitch = notes[2]  # Third
                            vel = velocity_for(0.6)
                        else:  # Weak off-beats
                            pitch = random.choice(notes[1:4])  # Scale tones
                            vel = velocity_for(0.5)
                        
                        # Short, staccato notes for classic feel
                        events.append((t, pitch, vel, seconds_per_beat * 0.15))
            else:
                # Liquid DnB: smoother, more flowing melodies
                # 8th note patterns that complement the rolling bass
                for i in range(8):
                    t = bar_start + i * (seconds_per_bar / 8.0)
                    if random.random() < 0.6:  # Higher density for liquid
                        # Create more melodic patterns
                        if i % 4 == 0:
                            pitch = notes[0]  # Root
                        elif i % 2 == 0:
                            pitch = notes[4]  # Fifth
                        else:
                            pitch = random.choice(notes[1:4])  # Scale tones
                        
                        vel = velocity_for(0.6)
                        # Longer notes for liquid feel
                        events.append((t, pitch, vel, seconds_per_beat * 0.3))

    elif "hiphop" in genre_key:
        # Hip-hop: sampled-style chops that work with the beat
        melody_root = root + 12
        notes = [melody_root + d for d in intervals[:6]]
        
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            
            if "boom_bap" in genre_key:
                # Boom bap: chopped samples that complement snare hits
                chop_positions = [0.0, 1.5, 2.5, 3.5]  # Syncopated with snare
                for pos in chop_positions:
                    t = bar_start + pos * seconds_per_beat
                    if random.random() < 0.7:
                        # Create chord-like stabs
                        base_note = notes[int(pos) % len(notes)]
                        for tri in (0, 2, 4):  # Simple chord tones
                            if tri < len(notes):
                                pitch = notes[(int(pos) + tri) % len(notes)]
                                # Short, punchy notes
                                events.append((t, pitch, velocity_for(0.5), seconds_per_beat * 0.2))
            else:
                # Modern hip-hop: sparse melodic elements
                for i in range(4):  # Quarter notes
                    t = bar_start + i * seconds_per_beat
                    if random.random() < 0.4:
                        pitch = notes[i % len(notes)]
                        # Longer, sustained notes
                        events.append((t, pitch, velocity_for(0.6), seconds_per_beat * 0.8))

    elif "industrial" in genre_key or "ebm" in genre_key:
        # Industrial/EBM: harsh, rhythmic stabs that complement the drive
        melody_root = root + 12
        # Use more dissonant intervals for industrial feel
        noisy_intervals = intervals[:4] + [intervals[0] + 1, intervals[2] + 1]  # Add some dissonance
        notes = [melody_root + i for i in noisy_intervals]
        
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            # Rhythmic stabs that lock with the kick
            for i in range(4):
                t = bar_start + i * seconds_per_beat
                if random.random() < 0.6:  # Higher hit rate for industrial
                    pitch = random.choice(notes)
                    # Hard, punchy notes
                    events.append((t, pitch, velocity_for(0.8), seconds_per_beat * 0.15))
                
                # Add noise/harsh elements at higher energy
                if energy_norm >= 7:
                    t_noise = t + random.uniform(-0.05, 0.05)
                    pitch_noise = random.choice(notes)
                    events.append((t_noise, pitch_noise, velocity_for(0.4), seconds_per_beat * 0.1))

    else:
        # Default: simple melodic patterns that complement the rhythm
        melody_root = root + 12
        notes = [melody_root + d for d in intervals[:5]]
        
        for bar in range(bars):
            bar_start = bar * seconds_per_bar
            # Simple, supportive melody
            for i in range(4):
                t = bar_start + i * seconds_per_beat
                if random.random() < 0.7:
                    pitch = notes[i % len(notes)]
                    events.append((t, pitch, velocity_for(0.6), seconds_per_beat * 0.8))

    events.sort(key=lambda x: x[0])
    return events


# -------------------------
# Main export_midi (advanced)
# -------------------------
def export_midi(plan, filename="beat_skeleton_advanced.mid", include_bass=True, include_melody=True, bars=8, break_preset="amen", snare_snap=False, hat_layout="standard", humanize_intensity=0.6, seed=None, lofi_vinyl=False):
    """
    Exports a pro-level MIDI file based on the 'plan' dict.
    plan should contain: 'genre', 'bpm', 'mood', 'energy'
    """
    if not HAS_MIDI:
        raise ImportError("pretty_midi is not installed. Run: pip install pretty_midi")

    genre = plan.get("genre", "default")
    bpm = int(plan.get("bpm", 120))
    mood = plan.get("mood", "neutral")

    # Optional reproducibility seed
    if seed is not None and seed != 0:
        try:
            random.seed(int(seed))
        except Exception:
            pass
    energy = int(plan.get("energy", 5))

    # Adjust effective BPM slightly by energy (denser & faster feeling)
    bpm_variation = int((energy - 5) * 0.6)  # energy 10 => +3 bpm approx
    eff_bpm = max(40, bpm + bpm_variation)

    pm = pretty_midi.PrettyMIDI(initial_tempo=eff_bpm)

    # Drums
    drum_instrument = pretty_midi.Instrument(program=0, is_drum=True, name="Drums")
    pm.instruments.append(drum_instrument)

    # Percussive textures
    perc_instrument = pretty_midi.Instrument(program=120, is_drum=False, name="PercTextures")
    pm.instruments.append(perc_instrument)

    # Generate drum events
    drum_events = generate_drum_events(
        plan["genre"], plan["bpm"], energy=plan["energy"], bars=bars,
        break_preset=break_preset, snare_snap=snare_snap, hat_layout=hat_layout,
        humanize_intensity=humanize_intensity, lofi_vinyl=lofi_vinyl
    )
    for t, pitch, vel, dur in drum_events:
        add_note(drum_instrument, pitch, t, dur, vel)

    # Perc textures (atmosphere)
    if energy >= 6:
        for _ in range(int(bars * 2)):
            t = random.uniform(0, (bars * 4) * (60.0 / eff_bpm))
            add_note(perc_instrument, random.choice([70, 71, 72, 73, 74]), t, 0.06, velocity_for(0.4))

    # Bass
    if include_bass:
        bass_instrument = pretty_midi.Instrument(program=34, is_drum=False, name="Bass")
        pm.instruments.append(bass_instrument)
        bass_events = generate_bass_events(genre, eff_bpm, energy=energy, bars=bars, mood=mood, humanize_intensity=humanize_intensity)
        for t, pitch, vel, dur in bass_events:
            add_note(bass_instrument, pitch, t, dur, vel)

    # Melody (optional)
    if include_melody:
        melody_inst = pretty_midi.Instrument(program=81, is_drum=False, name="Melody")  # Lead 2 (sawtooth)
        pm.instruments.append(melody_inst)
        melody_events = generate_melody_events(genre, eff_bpm, energy=energy, bars=bars, mood=mood, humanize_intensity=humanize_intensity)
        for t, pitch, vel, dur in melody_events:
            add_note(melody_inst, pitch, t, dur, vel)

    # finalize
    pm.write(filename)
    return filename


# -------------------------
# Simple plan generation (keeps previous interface)
# -------------------------
def generate_beat_plan(genre="techno", bpm=125, mood="neutral", energy=5, bars=8):
    # create a textual plan aligned with the advanced MIDI generator
    plan = {
        "genre": genre,
        "bpm": int(bpm),
        "mood": mood,
        "energy": int(energy),
        "drum_pattern_summary": f"{genre} style — density influenced by energy {energy}/10",
        "drum_template_8bars": [f"Bar {i+1}: (pattern generated for {genre})" for i in range(bars)],
        "instruments": ["Kick", "Snare", "Hi-hat", "Percussion", "Bass"],
        "structure": ["Intro", "Build", "Drop", "Breakdown", "Outro"]
    }
    # we can also populate the drum_template_8bars with textual descriptions by sampling events
    # but this keeps plan small; Streamlit UI shows MIDI and JSON downloads.
    return plan


def save_plan_json(plan, filename="beat_plan.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    return filename


# -------------------------
# If run directly for quick test (will not write MIDI if pretty_midi missing)
# -------------------------
if __name__ == "__main__":
    demo_plan = generate_beat_plan("industrial", bpm=110, mood="dark", energy=8, bars=8)
    save_plan_json(demo_plan, "example_plan.json")
    if HAS_MIDI:
        out = export_midi(demo_plan, filename="example_advanced.mid", include_bass=True, bars=8)
        print("Wrote MIDI:", out)
    else:
        print("pretty_midi not installed — example JSON saved only.")
