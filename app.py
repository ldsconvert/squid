import streamlit as st

# ✅ ASCII art rewritten to avoid quote issues completely
SQUID_ART = """
        _.-[====]-._
      .'  _     _ '.
     /   (_)   (_)  \
    |  ,           , |
    |   \  .-.  //  |
     \  '._____. ' /
      '.  "---"  .'
        '-._____.-'
"""

# ✅ Session state
if "hunger" not in st.session_state:
    st.session_state.hunger = 50

if "happiness" not in st.session_state:
    st.session_state.happiness = 50

# ✅ UI
st.title("Squishy the Virtual Pet")

st.text(SQUID_ART)

st.write(f"Hunger: {st.session_state.hunger}")
st.write(f"Happiness: {st.session_state.happiness}")

# ✅ Buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("Feed"):
        st.session_state.hunger = max(0, st.session_state.hunger - 10)

with col2:
    if st.button("Play"):
        st.session_state.happiness = min(100, st.session_state.happiness + 10)
