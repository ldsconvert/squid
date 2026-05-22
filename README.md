# Squid Mood Pet 🦑

A playful Streamlit web app where **three people** click buttons to report how they feel, and a **virtual squid** reflects the combined vibe.

## Features
- 3 named voters (set names in the sidebar)
- Mood buttons (Joyful, Calm, Focused, Excited, Stressed, Frustrated, Tired, Sad)
- Squid mood is computed from a **valence/arousal** model with **time decay** (older votes matter less)
- Mood map visualization + vote history

## Files
- `app.py`
- `requirements.txt`
- `README.md`

## Deploy (GitHub + Streamlit Community Cloud)
1. Create a GitHub repo (example: `squid-mood-pet`)
2. Upload the 3 files above to the repo root
3. In Streamlit Community Cloud, set:
   - **Repository**: your repo
   - **Branch**: `main`
   - **Main file path**: `app.py`

## Notes
- The app saves state to a local JSON file (`.squid_mood_state.json`).
- On Streamlit Cloud this usually persists between runs for the same app instance.
