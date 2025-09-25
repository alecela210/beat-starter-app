import streamlit as st
import json
import os

from beat_starter_core import (
    generate_beat_plan,
    save_plan_json,
    export_midi,
    HAS_MIDI
)

# ----------------------------------------------------
# 🎛️ Streamlit UI
# ----------------------------------------------------
st.set_page_config(
    page_title="🎧 Beat Starter", 
    page_icon="🎶", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# Security headers for safe sharing
st.markdown("""
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"><meta http-equiv="X-Content-Type-Options" content="nosniff"><meta http-equiv="X-Frame-Options" content="DENY"><meta http-equiv="X-XSS-Protection" content="1; mode=block">""", unsafe_allow_html=True)

st.title("🎧 Beat Starter — Beat Plan + MIDI Generator")
st.markdown("Generate an 8-bar beat plan and export a MIDI skeleton (drums + optional bass).")

st.divider()

# ----------------------------------------------------
# 🧠 User Inputs
# ----------------------------------------------------
# Categorized Genre/Subgenre selection
st.subheader("🎼 Style Selector")

genre_categories = [
    "Drum & Bass",
    "Hip-Hop",
    "House",
    "Reggaeton",
    "Pop",
    "Rock",
    "Afrobeat",
    "Jazz",
    "Techno",
    "Trance",
    "Industrial / EBM / Electro",
    "Lo-Fi",
    "Experimental",
]

category = st.selectbox("Main Genre", genre_categories, index=0)

subgenres_map = {
    "Drum & Bass": ["Classic (Amen/Think)", "Liquid", "Stepper (Chase & Status)", "Neurofunk"],
    "Hip-Hop": ["Boom Bap (DJ Premier)", "West Coast (Dr. Dre)", "Trap"],
    "House": ["Classic House", "Tech House", "Deep House", "UK Garage"],
    "Reggaeton": ["Dembow"],
    "Pop": ["Standard"],
    "Rock": ["Standard"],
    "Afrobeat": ["Modern"],
    "Jazz": ["Swing"],
    "Techno": ["Standard", "Peak", "Acid"],
    "Trance": ["Uplifting", "Standard"],
    "Industrial / EBM / Electro": ["Industrial", "EBM", "Electro"],
    "Lo-Fi": ["Standard"],
    "Experimental": ["Standard"],
}

subgenre = st.selectbox("Subgenre", subgenres_map.get(category, ["Standard"]))

# Compose internal genre key compatible with core
if category == "Drum & Bass":
    if "Classic" in subgenre:
        genre = "drum_and_bass_classic"
    elif "Liquid" in subgenre:
        genre = "drum_and_bass_liquid"
    elif "Stepper" in subgenre:
        genre = "drum_and_bass_stepper"
    else:
        genre = "drum_and_bass_neuro"
elif category == "Hip-Hop":
    if "Boom Bap" in subgenre:
        genre = "hiphop_boom_bap"
    elif "West Coast" in subgenre:
        genre = "hiphop_west_coast"
    else:
        genre = "hiphop_trap"
elif category == "House":
    if subgenre == "Tech House":
        genre = "tech_house"
    elif subgenre == "Deep House":
        genre = "deep_house"
    elif subgenre == "UK Garage":
        genre = "uk_garage"
    else:
        genre = "house"
elif category == "Reggaeton":
    genre = "reggaeton_dembow"
elif category == "Pop":
    genre = "pop"
elif category == "Rock":
    genre = "rock"
elif category == "Afrobeat":
    genre = "afrobeat"
elif category == "Jazz":
    genre = "jazz_swing"
elif category == "Techno":
    if subgenre == "Peak":
        genre = "techno_peak"
    elif subgenre == "Acid":
        genre = "techno_acid"
    else:
        genre = "techno"
elif category == "Trance":
    genre = "trance"
elif category == "Industrial / EBM / Electro":
    if subgenre == "Industrial":
        genre = "industrial"
    elif subgenre == "EBM":
        genre = "ebm"
    else:
        genre = "electro"
elif category == "Lo-Fi":
    genre = "lofi"
else:
    genre = "experimental"

mood = st.text_input("🌈 Mood (optional, e.g. dark, uplifting, chill)", "dark")
energy = st.slider("⚡ Energy (1 = low, 10 = high)", 1, 10, 7)
bpm = st.number_input("🎚️ BPM (tempo)", min_value=60, max_value=200, value=(174 if category == "Drum & Bass" else 90 if category == "Hip-Hop" else 125))

# Humanize and Seed controls
colH1, colH2 = st.columns(2)
with colH1:
    humanize_intensity = st.slider("🧬 Humanize Intensity", 0.2, 1.2, 0.6, help="Controls swing/timing/velocity variation. Lower = tighter, Higher = looser.")
with colH2:
    seed = st.number_input("🎲 Seed (0 = random)", min_value=0, max_value=999999, value=0, step=1)

# Optional Boom Bap Lo-Fi vinyl layer
lofi_vinyl = False
if genre == "hiphop_boom_bap":
    lofi_vinyl = st.checkbox("Lo‑Fi Vinyl (vinyl ticks layer)", value=False, help="Adds subtle vinyl tick accents to Boom Bap for extra grit.")

# DnB-specific controls
if "drum_and_bass" in genre.lower():
    st.subheader("🎛️ DnB Advanced Controls")
    col1, col2 = st.columns(2)
    
    with col1:
        break_preset = st.selectbox(
            "Break Preset",
            ["amen", "think", "tight"],
            help="Amen: Classic break pattern, Think: Regular kicks, Tight: Syncopated"
        )
        snare_snap = st.checkbox("Snare Snap (harder backbeat)", help="Add flam-like extra hits for harder snare sound")
    
    with col2:
        hat_layout = st.selectbox(
            "Hat Layout",
            ["standard", "break", "sparse"],
            help="Standard: Balanced, Break: Emphasized 3rd 16th, Sparse: More space"
        )
else:
    break_preset = "amen"
    snare_snap = False
    hat_layout = "standard"

midi_option = st.radio(
    "🎹 MIDI Export Option",
    ["None (JSON only)", "Drums only", "Drums + Bass (recommended)"],
    index=2
)

# Option to include melody in MIDI export
include_melody = st.checkbox("Include Melody (lead track)", value=True)

st.divider()

# ----------------------------------------------------
# 🚀 Generate Beat Plan
# ----------------------------------------------------
if st.button("🎶 Generate Beat Plan"):
    st.info("Generating your beat plan...")

    plan = generate_beat_plan(genre=genre, bpm=bpm, mood=mood, energy=energy, bars=8)

    # Display plan as JSON
    st.subheader("📊 Beat Plan (Preview)")
    st.json(plan)

    # Save JSON
    json_filename = "beat_plan.json"
    save_plan_json(plan, json_filename)
    with open(json_filename, "rb") as f:
        st.download_button("📥 Download JSON Plan", data=f, file_name=json_filename, mime="application/json")

    # ------------------------------------------------
    # 🎹 MIDI Export
    # ------------------------------------------------
    if midi_option != "None (JSON only)":
        if not HAS_MIDI:
            st.error(
                "❌ pretty_midi is not installed, so MIDI export isn't available.\n\n"
                "👉 To enable it, run this command on your server:\n\n"
                "```bash\npip install pretty_midi\n```"
            )
        else:
            st.info("Exporting MIDI...")

            include_bass = midi_option == "Drums + Bass (recommended)"
            # Build filename based on genre and BPM
            genre_key = genre.strip().lower().replace(" ", "_") if genre else "beat"
            midi_filename = f"{genre_key}_{int(bpm)}bpm.mid"
            
            # Pass DnB-specific parameters if applicable
            if "drum_and_bass" in genre.lower():
                export_midi(
                    plan, 
                    filename=midi_filename, 
                    include_bass=include_bass, 
                    include_melody=include_melody,
                    break_preset=break_preset,
                    snare_snap=snare_snap,
                    hat_layout=hat_layout,
                    humanize_intensity=humanize_intensity,
                    seed=seed,
                    lofi_vinyl=lofi_vinyl
                )
            else:
                export_midi(
                    plan,
                    filename=midi_filename,
                    include_bass=include_bass,
                    include_melody=include_melody,
                    humanize_intensity=humanize_intensity,
                    seed=seed,
                    lofi_vinyl=lofi_vinyl
                )

            # Offer MIDI download
            with open(midi_filename, "rb") as f:
                st.download_button(
                    "🎧 Download MIDI File",
                    data=f,
                    file_name=midi_filename,
                    mime="audio/midi"
                )

    st.success("✅ Done! Your beat plan and MIDI skeleton are ready.")


# ----------------------------------------------------
# 📎 Footer
# ----------------------------------------------------
st.divider()
st.caption("Made with ❤️ using Python + Streamlit • Perfect for producers & beatmakers")
