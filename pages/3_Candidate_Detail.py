import streamlit as st
import pandas as pd

st.set_page_config(page_title="Candidate Detail", layout="wide")

if "selected_candidate" not in st.session_state:
    st.error("No candidate selected. Go to Compare page first.")
    st.stop()

candidate = st.session_state.selected_candidate
cv = candidate["cv_data"]
jd_req = candidate["jd_data"]["required_skills"]
jd_opt = candidate["jd_data"]["nice_to_have_skills"]

st.title(f"Candidate Detail — {cv['name']}")

# HEADER CARD
st.markdown(
    f"""
    <div style='background:white;padding:20px;border-radius:10px;border:1px solid #E5E7EB;'>
        <h2>{cv['name']}</h2>
        <p style='color:#6B7280;'>{cv['seniority']} • {cv['years_experience']} yrs experience</p>
        <h1 style='color:#2563EB;'>{candidate['match_score']}</h1>
    </div>
    """,
    unsafe_allow_html=True
)

tabs = st.tabs(["Skills", "JD Match", "Missing Skills", "Raw JSON"])


# =============================
# ✅ SKILLS TAB
# =============================
with tabsst.subheader("Technologies")
    st.write(", ".join(cv["technologies"]))

    st.subheader("Languages")
    st.write(", ".join(cv["languages"]))


# =============================
# ✅ JD MATCH TAB
# =============================
with tabsst.subheader("Required Skills Match")
    df1 = pd.DataFrame([
        {
            "Skill": s,
            "Match": "✅" if any(s.lower() in t.lower() for t in cv["technologies"]) else "❌"
        }
        for s in jd_req
    ])
    st.table(df1)

    st.subheader("Optional Skills Match")
    df2 = pd.DataFrame([
        {
            "Skill": s,
            "Match": "✅" if any(s.lower() in t.lower() for t in cv["technologies"]) else "❌"
        }
        for s in jd_opt
    ])
    st.table(df2)


# =============================
# ✅ MISSING SKILLS TAB
# =============================
with tabsmissing_req = [s for s in jd_req if not any(s.lower() in t.lower() for t in cv["technologies"])]
    missing_opt = [s for s in jd_opt if not any(s.lower() in t.lower() for t in cv["technologies"])]

    st.subheader("Missing Required Skills")
    st.write(", ".join(missing_req) if missing_req else "✅ None")

    st.subheader("Missing Optional Skills")
    st.write(", ".join(missing_opt) if missing_opt else "✅ None")


# =============================
# ✅ RAW JSON TAB
# =============================
with tabsst.json(candidate)
