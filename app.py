import streamlit as st
import requests
import pandas as pd
import csv
from io import BytesIO

import plotly.graph_objects as go

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


# =====================================================================
# ✅ BACKEND URL
# =====================================================================
BACKEND_URL = "https://cvparser-production-b611.up.railway.app/parse"

st.set_page_config(page_title="CV Analyzer", layout="wide")


# =====================================================================
# ✅ VISUAL TOOLS
# =====================================================================
def render_score_donut(details):
    if not details:
        return None
    if sum(details.values()) == 0:
        return None

    labels = ["String match", "Embedding match", "Experience", "Seniority"]
    values = [
        details.get("string_score", 0),
        details.get("embedding_score", 0),
        details.get("experience_score", 0),
        details.get("seniority_score", 0),
    ]

    fig = go.Figure(
        data=[go.Pie(labels=labels, values=values, hole=0.55)]
    )
    fig.update_layout(title="Score Breakdown", height=350)
    return fig


def render_breakdown_cards(details):
    st.markdown("### 📊 Score Breakdown")
    c1, c2 = st.columns(2)

    with c1:
        st.metric("String match", f"{details.get('string_score', 0):.1f}/40")
        st.metric("Experience", f"{details.get('experience_score', 0):.1f}/10")

    with c2:
        st.metric("Embedding match", f"{details.get('embedding_score', 0):.1f}/40")
        st.metric("Seniority", f"{details.get('seniority_score', 0):.1f}/10")


def render_skill_match(cv_skills, jd_required):
    matched = []
    missing = []

    cv_lower = {s.lower() for s in cv_skills}

    for skill in jd_required:
        if skill.lower() in cv_lower:
            matched.append(skill)
        else:
            missing.append(skill)

    df = pd.DataFrame({
        "Skill": matched + missing,
        "Status": ["✅ Match"] * len(matched) + ["❌ Missing"] * len(missing)
    })

    st.dataframe(df, hide_index=True)


# =====================================================================
# ✅ PDF GENERATION
# =====================================================================
def generate_pdf(candidate):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    x, y = 40, A4[1] - 50

    cv = candidate["cv_data"]
    jd = candidate["jd_data"]
    score = candidate["match_score"]

    def ln(t, size=12, step=18):
        nonlocal y
        c.setFont("Helvetica", size)
        c.drawString(x, y, t)
        y -= step

    ln(f"AI CV Match Report – {cv['name']}", 16, 24)
    ln(f"Match Score: {score} / 100", 14, 22)
    ln("")

    ln("Candidate Information:", 14, 20)
    ln(f"Name: {cv['name']}")
    ln(f"Email: {cv['email']}")
    ln(f"Phone: {cv['phone']}")
    ln(f"Experience: {cv['years_experience']}")
    ln(f"Seniority: {cv['seniority']}")
    ln(f"Last Position: {cv['last_position']}")
    ln("")

    ln("Technologies:", 14, 20)
    for t in cv["technologies"]:
        ln(f"• {t}")

    ln("")
    ln("Languages:", 14, 20)
    for l in cv["languages"]:
        ln(f"• {l}")

    if jd:
        ln("")
        ln("JD Skills:", 14, 20)
        for s in jd["required_skills"]:
            ln(f"• {s}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# =====================================================================
# ✅ EXPORT UTILITIES
# =====================================================================
def export_all_candidates_to_csv(results):
    buffer = BytesIO()
    writer = csv.writer(buffer)
    writer.writerow(["Filename", "Name", "Experience", "Seniority", "Score"])

    for r in results:
        cv = r["cv_data"]
        writer.writerow([
            r["filename"], cv["name"], cv["years_experience"],
            cv["seniority"], r["match_score"],
        ])

    buffer.seek(0)
    return buffer


def export_all_candidates_to_pdf(results):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    for r in results:
        cv = r["cv_data"]
        x, y = 40, A4[1] - 50

        def ln(t, size=12, step=18):
            nonlocal y
            c.setFont("Helvetica", size)
            c.drawString(x, y, t)
            y -= step

        ln(f"Candidate: {cv['name']}", 16, 24)
        ln(f"Score: {r['match_score']}")
        ln(f"Experience: {cv['years_experience']}")
        ln(f"Seniority: {cv['seniority']}")
        ln("")
        ln("Technologies:", 14, 20)
        for t in cv["technologies"]:
            ln(f"• {t}")

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


# =====================================================================
# ✅ SESSION
# =====================================================================
if "results" not in st.session_state:
    st.session_state.results = []


# =====================================================================
# ✅ SIDEBAR + HOTFIX
# =====================================================================
st.sidebar.header("📄 Job Description")

jd_text = st.sidebar.text_area(
    "Paste JD text here:",
    height=280,
    key="jd_input"     # prevents Streamlit caching issue
)

uploaded_files = st.sidebar.file_uploader(
    "Upload CVs (PDF/DOCX):",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if st.sidebar.button("🚀 Analyze CVs", use_container_width=True):

    # ✅ Debug
    st.write("DEBUG_JD:", repr(jd_text))

    # ✅ HOTFIX — JD is required
    if not jd_text or jd_text.strip() == "":
        st.error("❌ JD is empty — please paste job description.")
        st.stop()

    if not uploaded_files:
        st.error("Upload at least one CV.")
        st.stop()

    results = []
    with st.spinner("Analyzing..."):
        for f in uploaded_files:
            try:
                resp = requests.post(
                    BACKEND_URL,
                    files={"file": (f.name, f.getvalue())},
                    data={"jd": jd_text},
                    timeout=30
                )
            except Exception as e:
                st.error(f"Backend unreachable: {e}")
                st.stop()

            if resp.status_code == 200:
                data = resp.json()
                data["filename"] = f.name
                results.append(data)
            else:
                st.error(f"Error: {resp.text}")

    st.session_state.results = results


# =====================================================================
# ✅ RESULTS PAGE
# =====================================================================
results = st.session_state.results
st.title("CV Analyzer")

if results:

    df = pd.DataFrame([
        {
            "File": r["filename"],
            "Name": r["cv_data"]["name"],
            "Score": r["match_score"],
            "Experience": r["cv_data"]["years_experience"],
            "Seniority": r["cv_data"]["seniority"],
        }
        for r in results
    ])
    st.subheader("📊 Comparison Table")
    st.dataframe(df, use_container_width=True)

    st.subheader("🔍 Candidate Detail")
    choices = {f"{r['cv_data']['name']} ({r['filename']})": r for r in results}

    selected = st.selectbox("Select candidate:", list(choices.keys()))
    candidate = choices[selected]

    cv = candidate["cv_data"]
    jd = candidate.get("jd_data")
    details = candidate.get("details", {})
    score = candidate["match_score"]

    # ✅ Score
    st.metric("Match Score", f"{score} %")

    donut = render_score_donut(details)
    if donut:
        st.plotly_chart(donut, use_container_width=True)

    if details:
        render_breakdown_cards(details)

    # ✅ Skills
    st.subheader("✅ Skill Match Overview")
    cv_skills = cv.get("technologies_normalized") or cv.get("technologies") or []

    if jd:
        render_skill_match(cv_skills, jd["required_skills"])
    else:
        st.warning("JD not provided.")

    # ✅ Summary block — FIXED
    with st.expander("📝 Summary"):
        summary = (
            candidate.get("summary")
            or cv.get("summary")
            or "No summary available."
        )
        st.info(summary)

    # ✅ Personal Info
    with st.expander("👤 Personal Info", expanded=False):
        st.write(f"**Name:** {cv['name']}")
        st.write(f"**Email:** {cv['email']}")
        st.write(f"**Phone:** {cv['phone']}")
        st.write(f"**Experience:** {cv['years_experience']}")
        st.write(f"**Seniority:** {cv['seniority']}")
        st.write(f"**Last Position:** {cv['last_position']}")

    # ✅ Export
    with st.expander("📤 Export All Candidates"):
        fmt = st.selectbox("Export format:", ["CSV", "PDF"])
        if st.button("Export Now"):
            if fmt == "CSV":
                csv_file = export_all_candidates_to_csv(results)
                st.download_button("Download CSV", csv_file, file_name="candidates.csv")
            else:
                pdf_file = export_all_candidates_to_pdf(results)
                st.download_button("Download PDF", pdf_file, file_name="candidates.pdf")

    with st.expander("📦 Raw JSON"):
        st.json(candidate)
