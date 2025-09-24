# Streamlit app for Beat Starter (uses beat_starter_core.py)
import streamlit as st
from beat_starter_core import generate_beat_plan, save_plan_json, export_midi

st.set_page_config(page_title="Beat Starter Generator", layout="centered", page_icon="🎛️")

st.title("Beat Starter — Beat Plan + MIDI Export (MVP)")
st.write("Generate a beat plan and export a simple MIDI skeleton (drums + bass). Note: MIDI export requires installing 'pretty_midi'.")

genre = st.text_input("Genre (e.g. Techno, Industrial, EBM, Electro, HipHop_Trap)", value="Techno")
mood = st.text_input("Mood (optional, e.g. dark, uplifting)", value="dark")
energy = st.slider("Energy (1 = low, 10 = high)", min_value=1, max_value=10, value=6)

midi_option = st.radio("MIDI export option", ("None (JSON only)", "Drums only", "Drums + Bass (recommended)"))

if st.button("Generate Beat Plan"):
    plan = generate_beat_plan(genre, mood=mood, energy=energy, seed=None)
    st.markdown("### Result")
    st.json(plan)
    if st.button("Save JSON"):
        path = save_plan_json(plan)
        st.success(f"Saved JSON to {path}")
    if midi_option != "None (JSON only)":
        drums = midi_option != ""
        bass = midi_option == "Drums + Bass (recommended)"
        try:
            midi_path = export_midi(plan, drums=True, bass=(midi_option=="Drums + Bass (recommended)"))
            st.success(f"MIDI exported to: {midi_path}")
            st.audio(midi_path)
        except Exception as e:
            st.error(f"Could not export MIDI: {e}. To enable MIDI export, run: pip install pretty_midi")