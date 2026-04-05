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
BACKEND_URL = "https://cv-parser-aewt.onrender.com/parse"

st.set_page_config(page_title="CV Analyzer", layout="wide")


# =====================================================================
# ✅ VISUALIZATION HELPERS
# =====================================================================
def render_score_donut(details):
    labels = ["String match", "Embedding match", "Experience", "Seniority"]
    values = [
        details["string_score"],
        details["embedding_score"],
        details["experience_score"],
        details["seniority_score"]
    ]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.55)])
    fig.update_layout(title="Score Breakdown", height=350)
    return fig


def render_breakdown_cards(details):
    st.markdown("### 📊 Score Breakdown")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("String match", f"{details['string_score']:.1f}/40")
        st.metric("Experience", f"{details['experience_score']:.1f}/10")
    with c2:
        st.metric("Embedding match", f"{details['embedding_score']:.1f}/40")
        st.metric("Seniority", f"{details['seniority_score']:.1f}/10")


def render_skill_match(cv_skills, jd_required):
    matched = []
    missing = []

    cv_lower = {s.lower() for s in cv_skills}

    for s in jd_required:
        if s.lower() in cv_lower:
            matched.append(s)
        else:
            missing.append(s)

    df = pd.DataFrame({
        "Skill": matched + missing,
        "Status": ["✅ Match"] * len(matched) + ["❌ Missing"] * len(missing)
    })

    st.dataframe(df, hide_index=True)


# =====================================================================
# ✅ PDF GENERATOR
# =====================================================================
def generate_pdf(candidate):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x, y = 40, height - 50

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
# ✅ AI COMMENT
# =====================================================================
def generate_ai_comment(candidate):
    d = candidate.get("details", {})
    score = candidate.get("match_score", 0)

    parts = []
    if d.get("required_score", 0) == 0:
        parts.append("Candidate does not match required skills.")
    else:
        parts.append("Candidate matches some required skills.")

    if d.get("optional_score", 0) > 0:
        parts.append("Candidate matches several optional skills.")
    else:
        parts.append("No optional skills matched.")

    if d.get("experience_score", 0) == 0:
        parts.append("Experience does not fully meet JD expectations.")
    else:
        parts.append("Experience contributes positively.")

    if d.get("seniority_score", 0) < 0:
        parts.append("Seniority appears misaligned with the role.")

    if score < 20:
        summary = "Overall weak match."
    elif score < 40:
        summary = "Moderate partial match."
    elif score < 70:
        summary = "Reasonable match."
    else:
        summary = "Strong match."

    return summary + " " + " ".join(parts)


# =====================================================================
# ✅ CSV EXPORT
# =====================================================================
def export_all_candidates_to_csv(results):
    output = BytesIO()
    writer = csv.writer(output)

    writer.writerow(["Filename", "Name", "Experience", "Seniority", "Score"])
    for r in results:
        cv = r["cv_data"]
        writer.writerow([
            r["filename"],
            cv["name"],
            cv["years_experience"],
            cv["seniority"],
            r["match_score"]
        ])

    output.seek(0)
    return output


# =====================================================================
# ✅ PDF EXPORT
# =====================================================================
def export_all_candidates_to_pdf(results):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    for r in results:
        cv = r["cv_data"]
        y = A4[1] - 50
        x = 40

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
# ✅ SESSION STATE
# =====================================================================
if "results" not in st.session_state:
    st.session_state.results = []


# =====================================================================
# ✅ SIDEBAR (JD input)
# =====================================================================
st.sidebar.header("📄 Job Description")
jd_text = st.sidebar.text_area("Paste JD text here:", height=280)

uploaded_files = st.sidebar.file_uploader(
    "Upload CVs (PDF/DOCX):", type=["pdf", "docx"], accept_multiple_files=True
)

if st.sidebar.button("🚀 Analyze CVs", use_container_width=True):

    if not uploaded_files:
        st.error("Upload at least one CV.")
        st.stop()

    if not jd_text.strip():
        st.error("Paste a Job Description.")
        st.stop()

    out = []
    with st.spinner("Analyzing..."):
        for f in uploaded_files:
            resp = requests.post(
                BACKEND_URL,
                files={"file": (f.name, f.getvalue())},
                data={"jd": jd_text},
            )
            if resp.status_code == 200:
                p = resp.json()
                p["filename"] = f.name
                out.append(p)
            else:
                st.error(f"Error with {f.name}: {resp.text}")

    st.session_state.results = out


# =====================================================================
# ✅ RESULTS
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

    display_names = {f"{r['cv_data']['name']} ({r['filename']})": r for r in results}

    selected_display = st.selectbox("Select candidate:", list(display_names.keys()))
    candidate = display_names[selected_display]

    cv = candidate["cv_data"]
    jd = candidate["jd_data"]
    score = candidate["match_score"]
    
    details = candidate.get("details", {
        "string_score": 0,
        "embedding_score": 0,
        "experience_score": 0,
        "seniority_score": 0,
    })


    # ✅ TOP SCORE
    st.metric("Match Score", f"{score} %")

    # ✅ VISUAL BREAKDOWN — donut
    st.plotly_chart(
        render_score_donut(details),
        use_container_width=True
    )

    # ✅ VISUAL BREAKDOWN — cards
    render_breakdown_cards(details)

    # ✅ SKILL MATCH TABLE
    st.subheader("✅ Skill Match Overview")
    render_skill_match(
        cv_skills=cv["technologies_normalized"],
        jd_required=jd["required_skills"]
    )

    # -- Personal Info --
    with st.expander("👤 Personal Info", expanded=False):
        st.write(f"**Name:** {cv['name']}")
        st.write(f"**Email:** {cv['email']}")
        st.write(f"**Phone:** {cv['phone']}")
        st.write(f"**Experience:** {cv['years_experience']}")
        st.write(f"**Seniority:** {cv['seniority']}")
        st.write(f"**Last Position:** {cv['last_position']}")

    # -- Technologies --
    with st.expander("🧩 Technologies"):
        st.write(", ".join(cv["technologies"]))

    # -- Languages --
    with st.expander("🌐 Languages"):
        st.write(", ".join(cv["languages"]))

    # -- Summary --
    with st.expander("📝 Summary"):
        st.info(candidate["summary"])

    # -- Required Skills --
    jd_req = jd["required_skills"]
    rows_req = [{
        "Skill": skill,
        "Match": "✅" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌"
    } for skill in jd_req]

    with st.expander("✅ Required Skills Match"):
        st.table(pd.DataFrame(rows_req))

    # -- Optional Skills --
    jd_opt = jd["nice_to_have_skills"]
    rows_opt = [{
        "Skill": skill,
        "Match": "✅" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌"
    } for skill in jd_opt]

    with st.expander("✨ Optional Skills Match"):
        st.table(pd.DataFrame(rows_opt))

    # -- Missing Skills --
    with st.expander("❗ Missing Skills"):
        missing_req = [s for s in jd_req if not any(s.lower() in t.lower() for t in cv["technologies"])]
        missing_opt = [s for s in jd_opt if not any(s.lower() in t.lower() for t in cv["technologies"])]

        st.write("### Missing Required")
        st.warning(", ".join(missing_req) if missing_req else "✅ None")

        st.write("### Missing Optional")
        st.info(", ".join(missing_opt) if missing_opt else "✅ None")

    # -- Compare candidates --
    with st.expander("🆚 Compare Candidates"):
        if len(results) > 1:
            colA, colB = st.columns(2)
            left = colA.selectbox("Candidate A", list(display_names.keys()), key="cmpA")
            right = colB.selectbox("Candidate B", list(display_names.keys()), key="cmpB")

            if left != right:
                A = display_names[left]
                B = display_names[right]

                st.write("### Comparison Overview")
                comp_df = pd.DataFrame([
                    {
                        "Attribute": "Score",
                        A["cv_data"]["name"]: A["match_score"],
                        B["cv_data"]["name"]: B["match_score"]
                    },
                ])
                st.table(comp_df)

    # -- Export --
    with st.expander("📤 Export All Candidates"):
        fmt = st.selectbox("Export format:", ["CSV", "PDF"])
        if st.button("Export Now"):
            if fmt == "CSV":
                csv_file = export_all_candidates_to_csv(results)
                st.download_button("Download CSV", csv_file, file_name="candidates.csv", mime="text/csv")
            else:
                pdf_file = export_all_candidates_to_pdf(results)
                st.download_button("Download PDF", pdf_file, file_name="candidates.pdf", mime="application/pdf")

    # -- JSON --
    with st.expander("📦 Raw JSON"):
        st.json(candidate)
