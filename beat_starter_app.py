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
st.set_page_config(page_title="🎧 Beat Starter", page_icon="🎶", layout="centered")

st.title("🎧 Beat Starter — Beat Plan + MIDI Generator")
st.markdown("Generate an 8-bar beat plan and export a MIDI skeleton (drums + optional bass).")

st.divider()

# ----------------------------------------------------
# 🧠 User Inputs
# ----------------------------------------------------
genre = st.text_input("🎼 Genre (e.g. Techno, Industrial, EBM, Electro, HipHop, LoFi)", "HipHop")
mood = st.text_input("🌈 Mood (optional, e.g. dark, uplifting, chill)", "dark")
energy = st.slider("⚡ Energy (1 = low, 10 = high)", 1, 10, 7)
bpm = st.number_input("🎚️ BPM (tempo)", min_value=60, max_value=200, value=120)

midi_option = st.radio(
    "🎹 MIDI Export Option",
    ["None (JSON only)", "Drums only", "Drums + Bass (recommended)"],
    index=2
)

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
            midi_filename = "beat_skeleton.mid"
            export_midi(plan, filename=midi_filename, include_bass=include_bass)

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
