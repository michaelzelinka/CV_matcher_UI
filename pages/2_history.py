import streamlit as st
import pandas as pd

st.set_page_config(page_title="History", layout="wide")

st.title("History")

history = st.session_state.get("history", [])

if not history:
    st.info("No comparisons performed yet.")
    st.stop()

df = pd.DataFrame(history)

st.dataframe(df, use_container_width=True)

st.markdown("Click any row in the Compare page to re-run a comparison.")
