import streamlit as st
import requests
import pandas as pd
import csv

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO


# =====================================================================
# ✅ BASE CONFIG
# =====================================================================
BACKEND_URL = "https://cv-parser-aewt.onrender.com/parse"
st.set_page_config(page_title="AI CV Matcher", layout="wide")


# =====================================================================
# ✅ PDF GENERATOR — single candidate report
# =====================================================================
def generate_pdf(candidate):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    x = 40
    y = height - 50

    cv = candidate["cv_data"]
    jd = candidate["jd_data"]
    score = candidate["match_score"]
    details = candidate.get("details", {})

    def line(t, fontsize=12, spacing=18):
        nonlocal y
        c.setFont("Helvetica", fontsize)
        c.drawString(x, y, t)
        y -= spacing

    line(f"AI CV Match Report – {cv['name']}", 16, 24)
    line(f"Match Score: {score} / 100", 14, 20)
    line("")

    line("Candidate Information:", 14, 20)
    line(f"• Name: {cv['name']}")
    line(f"• Email: {cv['email']}")
    line(f"• Phone: {cv['phone']}")
    line(f"• Experience: {cv['years_experience']}")
    line(f"• Seniority: {cv['seniority']}")
    line(f"• Last Position: {cv['last_position']}")
    line("")

    line("Technologies:", 14, 20)
    for t in cv["technologies"]:
        line(f"• {t}")
    line("")

    line("Languages:", 14, 20)
    for lang in cv["languages"]:
        line(f"• {lang}")
    line("")

    if jd:
        line("JD Required Skills:", 14, 20)
        for s in jd["required_skills"]:
            line(f"• {s}")
        line("")

    line("Scoring Breakdown:", 14, 20)
    line(f"• Required Match: {round(details.get('required_ratio', 0) * 100)}%")
    line(f"• Optional Match: {round(details.get('optional_ratio', 0) * 100)}%")
    line(f"• Experience Score: {round(details.get('experience_score', 0))}/20")
    line(f"• Seniority Score: {round(details.get('seniority_score', 0))}/10")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# =====================================================================
# ✅ AI COMMENT — WHY THIS SCORE?
# =====================================================================
def generate_ai_comment(candidate):
    d = candidate.get("details", {})
    score = candidate.get("match_score", 0)

    parts = []

    if d.get("required_ratio", 0) == 0:
        parts.append("Candidate does not match any required hard skills.")
    else:
        parts.append("Candidate matches some required technical skills.")

    if d.get("optional_ratio", 0) > 0:
        parts.append("Candidate matches some optional skills.")
    else:
        parts.append("No optional skills matched.")

    if d.get("experience_score", 0) == 10:
        parts.append("Experience fallback applied (trainee-level role or unclear requirement).")
    elif d.get("experience_score", 0) == 0:
        parts.append("Experience level does not meet role expectations.")

    if d.get("seniority_score", 0) == 10:
        parts.append("Seniority matches job expectations.")
    else:
        parts.append("Seniority differs from the role requirement.")

    if score < 20:
        summary = "Overall, the candidate has poor alignment with the job requirements."
    elif score < 40:
        summary = "Overall, the candidate shows partial alignment."
    elif score < 70:
        summary = "Overall, the candidate is a moderate match."
    else:
        summary = "Overall, the candidate is a strong match."

    return summary + " " + " ".join(parts)


# =====================================================================
# ✅ EXPORT — CSV for ALL candidates
# =====================================================================
def export_all_candidates_to_csv(results):
    output = BytesIO()
    writer = csv.writer(output)

    writer.writerow([
        "Filename", "Name", "Email", "Phone",
        "Experience (yrs)", "Seniority",
        "Technologies", "Languages",
        "Score"
    ])

    for r in results:
        cv = r["cv_data"]
        writer.writerow([
            r["filename"],
            cv["name"],
            cv["email"],
            cv["phone"],
            cv["years_experience"],
            cv["seniority"],
            ", ".join(cv["technologies"]),
            ", ".join(cv["languages"]),
            r["match_score"]
        ])

    output.seek(0)
    return output


# =====================================================================
# ✅ EXPORT — Multi‑PDF for ALL candidates
# =====================================================================
def export_all_candidates_to_pdf(results):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    x = 40

    for r in results:
        cv = r["cv_data"]
        y = height - 50

        def line(t, fontsize=12, spacing=18):
            nonlocal y
            c.setFont("Helvetica", fontsize)
            c.drawString(x, y, t)
            y -= spacing

        line(f"Candidate: {cv['name']}", 16, 24)
        line(f"Score: {r['match_score']} / 100", 14, 20)
        line(f"Experience: {cv['years_experience']}")
        line(f"Seniority: {cv['seniority']}")
        line(f"File: {r['filename']}")
        line("Technologies:", 14, 20)

        for t in cv["technologies"]:
            line(f"• {t}")

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
# ✅ SIDEBAR — JD INPUT
# =====================================================================
st.sidebar.header("📄 Job Description")
jd_text = st.sidebar.text_area("Paste JD here:", height=300)


# =====================================================================
# ✅ FILE UPLOAD + ANALYZE BUTTON
# =====================================================================
uploaded_files = st.file_uploader(
    "Upload CVs (PDF/DOCX):",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if st.button("🚀 Analyze CVs"):
    if not uploaded_files:
        st.error("Please upload at least one CV.")
        st.stop()

    if not jd_text.strip():
        st.error("Please paste a Job Description.")
        st.stop()

    out = []
    with st.spinner("Analyzing…"):
        for f in uploaded_files:
            resp = requests.post(
                BACKEND_URL,
                files={"file": (f.name, f.getvalue())},
                data={"jd": jd_text}
            )

            if resp.status_code != 200:
                st.error(f"Error processing {f.name}: {resp.text}")
                continue

            parsed = resp.json()
            parsed["filename"] = f.name
            out.append(parsed)

    st.session_state.results = out


# =====================================================================
# ✅ RESULTS PRESENTATION
# =====================================================================
results = st.session_state.results

if results:

    st.success("✅ Analysis complete")

    df = pd.DataFrame([{
        "File": r["filename"],
        "Name": r["cv_data"]["name"],
        "Score": r["match_score"],
        "Experience": r["cv_data"]["years_experience"],
    } for r in results])

    best = df["Score"].max()

    def highlight(row):
        return ["background-color: #d4f8d4" if row["Score"] == best else ""] * len(row)

    st.subheader("📊 Comparison Table")
    st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)


    # =================================================================
    # ✅ CANDIDATE DETAIL (COLLAPSIBLE SECTIONS)
    # =================================================================
    st.subheader("🔍 Candidate Detail")

    selected_file = st.selectbox(
        "Select a candidate:",
        df["File"].tolist()
    )

    candidate = next(r for r in results if r["filename"] == selected_file)
    cv = candidate["cv_data"]

    # PERSONAL INFO
    with st.expander("👤 Personal Info", expanded=True):
        st.write(f"**Name:** {cv['name']}")
        st.write(f"**Email:** {cv['email']}")
        st.write(f"**Phone:** {cv['phone']}")
        st.write(f"**Experience:** {cv['years_experience']}")
        st.write(f"**Seniority:** {cv['seniority']}")
        st.write(f"**Last Position:** {cv['last_position']}")

    # TECHNOLOGIES
    with st.expander("🧩 Technologies", expanded=False):
        st.write(", ".join(cv["technologies"]))

    # LANGUAGES
    with st.expander("🌐 Languages", expanded=False):
        st.write(", ".join(cv["languages"]))

    # SUMMARY
    with st.expander("📝 Summary", expanded=False):
        st.info(candidate["summary"])


    # =================================================================
    # ✅ AI COMMENT
    # =================================================================
    with st.expander("🤖 Why this score?", expanded=False):
        st.write(generate_ai_comment(candidate))


    # =================================================================
    # ✅ REQUIRED SKILLS MATCH
    # =================================================================
    jd_req = candidate["jd_data"]["required_skills"]
    rows_req = [{
        "JD Skill": skill,
        "Matched": "✅ Yes" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌ No"
    } for skill in jd_req]

    with st.expander("🧩 Required Skills Match", expanded=False):
        st.table(pd.DataFrame(rows_req))


    # =================================================================
    # ✅ OPTIONAL SKILLS MATCH
    # =================================================================
    jd_opt = candidate["jd_data"]["nice_to_have_skills"]
    rows_opt = [{
        "Optional Skill": skill,
        "Matched": "✅ Yes" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌ No"
    } for skill in jd_opt]

    with st.expander("🧩 Optional Skills Match", expanded=False):
        st.table(pd.DataFrame(rows_opt))


    # =================================================================
    # ✅ MISSING SKILLS
    # =================================================================
    missing_required = [s for s in jd_req if not any(s.lower() in t.lower() for t in cv["technologies"])]
    missing_optional = [s for s in jd_opt if not any(s.lower() in t.lower() for t in cv["technologies"])]

    with st.expander("❗ Missing Skills", expanded=False):

        if missing_required:
            st.markdown("### Missing Required Skills")
            st.warning(", ".join(missing_required))
        else:
            st.markdown("✅ Candidate meets all required skills!")

        if missing_optional:
            st.markdown("### Missing Optional Skills")
            st.info(", ".join(missing_optional))
        else:
            st.markdown("✅ Candidate meets all optional skills!")


    # =================================================================
    # ✅ CANDIDATE COMPARISON (SIDE-BY-SIDE)
    # =================================================================
    with st.expander("🆚 Compare Candidates", expanded=False):

        if len(results) > 1:
            colA, colB = st.columns(2)

            with colA:
                left_file = st.selectbox(
                    "Candidate A",
                    [r["filename"] for r in results],
                    key="cmp_left"
                )

            with colB:
                right_file = st.selectbox(
                    "Candidate B",
                    [r["filename"] for r in results],
                    key="cmp_right"
                )

            if left_file != right_file:
                candA = next(r for r in results if r["filename"] == left_file)
                candB = next(r for r in results if r["filename"] == right_file)

                st.markdown("### 🔄 Comparison Overview")

                overview = pd.DataFrame([
                    {
                        "Attribute": "Score",
                        candA["cv_data"]["name"]: candA["match_score"],
                        candB["cv_data"]["name"]: candB["match_score"]
                    },
                    {
                        "Attribute": "Experience (yrs)",
                        candA["cv_data"]["name"]: candA["cv_data"]["years_experience"],
                        candB["cv_data"]["name"]: candB["cv_data"]["years_experience"]
                    },
                    {
                        "Attribute": "Seniority",
                        candA["cv_data"]["name"]: candA["cv_data"]["seniority"],
                        candB["cv_data"]["name"]: candB["cv_data"]["seniority"]
                    }
                ])

                st.table(overview)

                # SIDE-BY-SIDE MISSING REQUIRED SKILLS
                st.markdown("### ❗ Missing Required Skills (Side by Side)")

                def missing(c):
                    return [
                        s for s in c["jd_data"]["required_skills"]
                        if not any(s.lower() in t.lower() for t in c["cv_data"]["technologies"])
                    ]

                comp_rows = [{
                    "Skill": skill,
                    candA["cv_data"]["name"]: "❌" if skill in missing(candA) else "✅",
                    candB["cv_data"]["name"]: "❌" if skill in missing(candB) else "✅"
                } for skill in candidate["jd_data"]["required_skills"]]

                st.table(pd.DataFrame(comp_rows))


    # =================================================================
    # ✅ EXPORT PANEL (CSV / PDF)
    # =================================================================
    with st.expander("📤 Export All Candidates", expanded=False):

        export_format = st.selectbox(
            "Choose export format:",
            ["CSV", "PDF (multi-page summary)"],
            key="export_format"
        )

        if st.button("Export", use_container_width=True):
            if export_format == "CSV":
                csv_buf = export_all_candidates_to_csv(results)
                st.download_button(
                    label="Download CSV",
                    data=csv_buf,
                    file_name="candidates_export.csv",
                    mime="text/csv"
                )
            else:
                pdf_buf = export_all_candidates_to_pdf(results)
                st.download_button(
                    label="Download PDF",
                    data=pdf_buf,
                    file_name="candidates_export.pdf",
                    mime="application/pdf"
                )


    # =================================================================
    # ✅ RAW DEBUG
    # =================================================================
    with st.expander("📦 Raw JSON Response", expanded=False):
        st.json(candidate)
