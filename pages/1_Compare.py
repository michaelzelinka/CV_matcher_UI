import streamlit as st
import requests
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Compare Candidates", layout="wide")

BACKEND_URL = "https://cv-parser-aewt.onrender.com/parse"

# Title
st.title("Compare Candidates")

st.markdown("Paste a JD and upload CVs to get instant AI‑powered matching.")

left, right = st.columns([2, 1], gap="large")

# ================================
# ✅ JD input
# ================================
with left:
    st.subheader("Job Description")
    jd_text = st.text_area("Paste Job Description here...", height=280)


# ================================
# ✅ CV upload
# ================================
with right:
    st.subheader("CV Files")
    uploaded_files = st.file_uploader(
        "Upload CV files",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

# ================================
# ✅ Compare button
# ================================
if st.button("🔍 Compare Candidates", use_container_width=True):

    if not uploaded_files:
        st.error("Please upload at least one CV.")
        st.stop()

    if not jd_text.strip():
        st.error("Please paste a Job Description.")
        st.stop()

    out = []
    with st.spinner("Analyzing candidates…"):
        for f in uploaded_files:
            resp = requests.post(
                BACKEND_URL,
                files={"file": (f.name, f.getvalue())},
                data={"jd": jd_text}
            )

            if resp.status_code == 200:
                p = resp.json()
                p["filename"] = f.name
                out.append(p)
            else:
                st.error(f"Error processing {f.name}: {resp.text}")

    st.session_state.compare_results = out
    st.session_state.history = st.session_state.get("history", []) + [{
        "date": pd.Timestamp.now().strftime("%d/%m/%Y"),
        "role": out[0]["jd_data"]["role"] if out else "-",
        "cvs": len(out),
        "best_score": max(r["match_score"] for r in out),
    }]


# ================================
# ✅ RESULTS LIST
# ================================
if "compare_results" in st.session_state:
    results = st.session_state.compare_results

    st.markdown("---")
    st.subheader(f"Results ({len(results)} CVs)")

    results_sorted = sorted(results, key=lambda r: r["match_score"], reverse=True)

    for r in results_sorted:
        cv = r["cv_data"]
        score = r["match_score"]

        with st.container(border=True):
            st.markdown(f"### {cv['name']} — **Score {score}**")
            st.write(f"**Seniority:** {cv['seniority'] or 'N/A'}")
            st.write(f"**Experience:** {cv['years_experience']} years")
            st.write(f"**Technologies:** {', '.join(cv['technologies'])}")
            
            if st.button(f"View Detail → {cv['name']}", key=f"detail_{r['filename']}"):
                st.session_state.selected_candidate = r
                st.switch_page("pages/3_Candidate_Detail.py")
``
