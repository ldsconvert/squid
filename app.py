import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
import plotly.express as px

# ======================================================
# Squid Mood Pet 🦑
# Three people click mood buttons; squid reflects combined mood.
# Deploy via GitHub + Streamlit Community Cloud.
# ======================================================

STATE_FILE = Path('.squid_mood_state.json')

# --- Mood model (valence, arousal) on [-1..1]
MOODS = {
    "Joyful":      ( 0.9,  0.6, "😄"),
    "Calm":        ( 0.6, -0.4, "😌"),
    "Focused":     ( 0.4,  0.3, "🎯"),
    "Stressed":    (-0.6,  0.7, "😬"),
    "Frustrated":  (-0.7,  0.6, "😠"),
    "Tired":       (-0.4, -0.6, "🥱"),
    "Sad":         (-0.8, -0.5, "😢"),
    "Excited":     ( 0.8,  0.9, "🤩"),
}

# --- Visual palette by mood quadrant
# (valence high/low) x (arousal high/low)
PALETTE = {
    "upbeat":   {"bg": "#0B1220", "accent": "#22C55E", "glow": "rgba(34,197,94,0.35)", "label": "Upbeat"},
    "wired":    {"bg": "#0B1220", "accent": "#F59E0B", "glow": "rgba(245,158,11,0.35)", "label": "Wired"},
    "low":      {"bg": "#0B1220", "accent": "#60A5FA", "glow": "rgba(96,165,250,0.35)", "label": "Low"},
    "rough":    {"bg": "#0B1220", "accent": "#EF4444", "glow": "rgba(239,68,68,0.35)", "label": "Rough"},
}

SQUID_FACES = {
    "Upbeat": ["(•‿•)", "(ᵔᴥᵔ)", "(✿◕‿◕)", "(ง'̀-'́)ง"],
    "Wired":  ["(⊙_⊙)", "(ʘ‿ʘ)", "(ง •̀_•́)ง", "(☉_☉)"],
    "Low":    ["(－‸ლ)", "(._.)", "(•︵•)", "(︶︹︶)"],
    "Rough":  ["(ಠ_ಠ)", "(>_<)", "(ノಠ益ಠ)ノ", "(；￣Д￣)"],
}

SQUID_ART = r"""
            _
        _.-""""-._
      .'  _   _   '.
     /   (o) (o)    \
    |  .-.  ^  .-.   |
    |  \  \___/  /   |
     \  '._   _.'   /
      '._  """  _.'
         '-.__.-'
       _/ /|\ \_
      /_ /_|_\ _\
        /_/ \_\
"""

@dataclass
class Vote:
    person: str
    mood: str
    valence: float
    arousal: float
    timestamp_utc: str  # ISO

@dataclass
class AppState:
    people: List[str]
    last_votes: Dict[str, Vote]
    history: List[Vote]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> AppState:
    if STATE_FILE.exists():
        try:
            raw = json.loads(STATE_FILE.read_text())
            people = raw.get("people", ["Person 1", "Person 2", "Person 3"])
            last_votes = {}
            for k, v in (raw.get("last_votes", {}) or {}).items():
                last_votes[k] = Vote(**v)
            history = [Vote(**x) for x in (raw.get("history", []) or [])]
            return AppState(people=people, last_votes=last_votes, history=history)
        except Exception:
            pass
    return AppState(people=["Person 1", "Person 2", "Person 3"], last_votes={}, history=[])


def save_state(state: AppState):
    raw = {
        "people": state.people,
        "last_votes": {k: asdict(v) for k, v in state.last_votes.items()},
        "history": [asdict(v) for v in state.history[-500:]],  # cap history
    }
    STATE_FILE.write_text(json.dumps(raw, indent=2))


def time_decay_weight(iso_ts: str, half_life_hours: float = 12.0) -> float:
    """Exponential decay weight; 1.0 now, 0.5 after half-life."""
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except Exception:
        return 1.0

    age_seconds = (datetime.now(timezone.utc) - ts).total_seconds()
    age_hours = max(0.0, age_seconds / 3600.0)
    return 0.5 ** (age_hours / max(0.1, half_life_hours))


def combined_mood(state: AppState) -> Tuple[float, float, Dict[str, float]]:
    """Return (valence, arousal, weights_by_person)."""
    vals = []
    ars = []
    wts = []
    weights_by_person = {}

    for p in state.people:
        v = state.last_votes.get(p)
        if not v:
            continue
        w = time_decay_weight(v.timestamp_utc)
        weights_by_person[p] = w
        vals.append(v.valence)
        ars.append(v.arousal)
        wts.append(w)

    if not wts:
        return 0.0, 0.0, {}

    total = sum(wts)
    val = sum(v * w for v, w in zip(vals, wts)) / total
    aro = sum(a * w for a, w in zip(ars, wts)) / total
    return float(val), float(aro), weights_by_person


def quadrant_label(val: float, aro: float) -> str:
    # valence positive/negative; arousal positive/negative
    if val >= 0 and aro >= 0:
        return "Upbeat"
    if val >= 0 and aro < 0:
        return "Low"
    if val < 0 and aro >= 0:
        return "Wired"
    return "Rough"


def palette_for(label: str) -> dict:
    if label == "Upbeat":
        return PALETTE["upbeat"]
    if label == "Wired":
        return PALETTE["wired"]
    if label == "Low":
        return PALETTE["low"]
    return PALETTE["rough"]


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def ink_level(val: float, aro: float) -> float:
    """0..1 where 1 = lots of ink (stress/rough), 0 = clear water."""
    # ink rises as valence drops and arousal rises
    return clamp01(((-val) * 0.65) + (max(0, aro) * 0.35))


def glow_level(val: float, aro: float) -> float:
    """0..1 where 1 = happy bioluminescent squid."""
    return clamp01((max(0, val) * 0.7) + (max(0, aro) * 0.3))


def add_vote(state: AppState, person: str, mood: str):
    val, aro, _emoji = MOODS[mood]
    v = Vote(person=person, mood=mood, valence=val, arousal=aro, timestamp_utc=now_iso())
    state.last_votes[person] = v
    state.history.append(v)


# -----------------------------
# UI
# -----------------------------

st.set_page_config(page_title="Squid Mood Pet", page_icon="🦑", layout="wide")
state = load_state()

# Sidebar: configure names (no code edits needed)
with st.sidebar:
    st.header("🧑‍🤝‍🧑 People")
    st.caption("Set the 3 names here. These are the only people who can steer the squid.")

    names = []
    for i in range(3):
        default = state.people[i] if i < len(state.people) else f"Person {i+1}"
        names.append(st.text_input(f"Name {i+1}", value=default, key=f"name_{i}"))

    # Normalize and update
    cleaned = [n.strip() if n.strip() else f"Person {i+1}" for i, n in enumerate(names)]
    state.people = cleaned

    st.divider()
    st.header("⚙️ Controls")
    half_life = st.slider("Mood memory half-life (hours)", min_value=1, max_value=48, value=12)
    st.caption("Short half-life = squid changes quickly. Long half-life = squid holds grudges.")

    if st.button("Reset squid (clear votes)"):
        state.last_votes = {}
        state.history = []
        save_state(state)
        st.success("Reset complete.")

# Override decay function half-life with slider

def time_decay_weight_local(iso_ts: str) -> float:
    return time_decay_weight(iso_ts, half_life_hours=float(half_life))

# Monkey patch used in combined_mood

def combined_mood_local(state: AppState) -> Tuple[float, float, Dict[str, float]]:
    vals, ars, wts = [], [], []
    weights_by_person = {}
    for p in state.people:
        v = state.last_votes.get(p)
        if not v:
            continue
        w = time_decay_weight_local(v.timestamp_utc)
        weights_by_person[p] = w
        vals.append(v.valence)
        ars.append(v.arousal)
        wts.append(w)
    if not wts:
        return 0.0, 0.0, {}
    total = sum(wts)
    val = sum(v * w for v, w in zip(vals, wts)) / total
    aro = sum(a * w for a, w in zip(ars, wts)) / total
    return float(val), float(aro), weights_by_person


# Header
st.title("🦑 Squid Mood Pet")
st.write(
    "- Three people vote how they feel.\n"
    "- The squid shows the **combined vibe** (with time decay).\n"
    "- Go wild: try making it ‘Upbeat’ vs ‘Rough’ and watch ink/glow change."
)

# Voting panels
st.subheader("Vote your feeling")
cols = st.columns(3)

for i, person in enumerate(state.people):
    with cols[i]:
        st.markdown(f"### {person}")
        last = state.last_votes.get(person)
        if last:
            st.caption(f"Last: **{last.mood}** at {last.timestamp_utc.replace('T',' ').split('.')[0]} UTC")
        else:
            st.caption("Last: —")

        # Mood buttons
        for mood in ["Joyful", "Calm", "Focused", "Excited", "Stressed", "Frustrated", "Tired", "Sad"]:
            emoji = MOODS[mood][2]
            if st.button(f"{emoji} {mood}", key=f"btn_{person}_{mood}"):
                add_vote(state, person, mood)
                save_state(state)
                st.experimental_rerun()

# Compute combined
val, aro, weights = combined_mood_local(state)
label = quadrant_label(val, aro)
pal = palette_for(label)

ink = ink_level(val, aro)
glow = glow_level(val, aro)

# Squid display
st.divider()
st.subheader("The Squid’s Current Mood")

left, mid, right = st.columns([1.2, 1.6, 1.2])

with left:
    face = SQUID_FACES[label][int((ink * 10) % len(SQUID_FACES[label]))]
    st.markdown(
        f"""
<div style="background:{pal['bg']}; border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:18px; box-shadow: 0 0 40px {pal['glow']};">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <div style="font-size:28px; font-weight:700; color:{pal['accent']};">{label} Squid</div>
    <div style="font-size:18px; color:rgba(255,255,255,0.7);">Valence {val:+.2f} • Arousal {aro:+.2f}</div>
  </div>
  <div style="margin-top:12px; font-size:42px;">🦑</div>
  <div style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono','Courier New', monospace; font-size:22px; color:rgba(255,255,255,0.85);">{face}</div>
  <div style="margin-top:12px; height:10px; border-radius:999px; background:rgba(255,255,255,0.08); overflow:hidden;">
    <div style="width:{int(ink*100)}%; height:100%; background:{pal['accent']};"></div>
  </div>
  <div style="margin-top:8px; color:rgba(255,255,255,0.7);">Ink level: {int(ink*100)}% • Glow: {int(glow*100)}%</div>
</div>
""",
        unsafe_allow_html=True,
    )

with mid:
    st.markdown("#### 🧭 Mood Map (Valence vs Arousal)")
    # Point for squid + points for each person
    rows = []
    rows.append({"who": "Squid (combined)", "valence": val, "arousal": aro, "mood": label})
    for p in state.people:
        v = state.last_votes.get(p)
        if v:
            rows.append({"who": p, "valence": v.valence, "arousal": v.arousal, "mood": v.mood})

    df = pd.DataFrame(rows)
    fig = px.scatter(
        df,
        x="valence",
        y="arousal",
        color="who",
        symbol="who",
        range_x=[-1.05, 1.05],
        range_y=[-1.05, 1.05],
        title=None,
    )
    fig.add_hline(y=0, line_width=1, line_dash="dot", line_color="rgba(255,255,255,0.25)")
    fig.add_vline(x=0, line_width=1, line_dash="dot", line_color="rgba(255,255,255,0.25)")
    fig.update_layout(height=380, margin=dict(l=10,r=10,t=10,b=10), plot_bgcolor=pal["bg"], paper_bgcolor=pal["bg"], font=dict(color="rgba(255,255,255,0.85)"))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("#### ⚖️ Influence Weights")
    if not weights:
        st.info("No votes yet. Ask your 3 people to click a mood.")
    else:
        wdf = pd.DataFrame([{ "person": k, "weight": v } for k, v in weights.items()])
        wdf["weight_pct"] = (wdf["weight"] / wdf["weight"].sum() * 100).round(1)
        for _, r in wdf.sort_values("weight", ascending=False).iterrows():
            st.write(f"- **{r['person']}**: {r['weight_pct']}%")

        st.caption("Weights decay over time — older votes matter less.")

# History
st.divider()
st.subheader("📜 Vote History")

if not state.history:
    st.info("No history yet.")
else:
    h = pd.DataFrame([asdict(v) for v in state.history])
    # Make readable
    h["timestamp_utc"] = pd.to_datetime(h["timestamp_utc"], errors="coerce")
    h = h.sort_values("timestamp_utc", ascending=False)
    st.dataframe(h[["timestamp_utc","person","mood","valence","arousal"]].head(50), use_container_width=True)

    # Trend chart: last N entries
    last_n = h.head(120).sort_values("timestamp_utc")
    if len(last_n) >= 2:
        fig2 = px.line(last_n, x="timestamp_utc", y=["valence","arousal"], title=None)
        fig2.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig2, use_container_width=True)

# Save any name changes
save_state(state)
