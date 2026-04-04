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
# ✅ PDF GENERATORS
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
    line(f"Match Score: {score}/100", 14, 20)
    line("")

    line("Candidate Information:", 14, 20)
    line(f"Name: {cv['name']}")
    line(f"Email: {cv['email']}")
    line(f"Phone: {cv['phone']}")
    line(f"Experience: {cv['years_experience']}")
    line(f"Seniority: {cv['seniority']}")
    line(f"Last Position: {cv['last_position']}")
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
    line(f"Required Score: {details.get('required_score', 0):.2f}")
    line(f"Optional Score: {details.get('optional_score', 0):.2f}")
    line(f"Experience Score: {details.get('experience_score', 0):.2f}")
    line(f"Seniority Score: {details.get('seniority_score', 0):.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def export_all_candidates_to_csv(results):
    output = BytesIO()
    writer = csv.writer(output)

    writer.writerow([
        "Filename", "Name", "Email", "Phone",
        "Experience", "Seniority",
        "Technologies", "Languages", "Score"
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
        line(f"Score: {r['match_score']}/100")
        line(f"Experience: {cv['years_experience']}")
        line(f"Seniority: {cv['seniority']}")
        line(f"File: {r['filename']}")
        line("")
        line("Technologies:", 14, 20)
        for t in cv["technologies"]:
            line(f"• {t}")

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

    comments = []

    if d.get("required_score", 0) == 0:
        comments.append("Candidate does not match any required hard skills.")
    else:
        comments.append("Candidate matches some required technical skills.")

    if d.get("optional_score", 0) > 0:
        comments.append("Candidate matches some optional skills.")
    else:
        comments.append("No optional skills matched.")

    if d.get("experience_score", 0) == 0:
        comments.append("Experience does not fully meet expectations.")
    else:
        comments.append("Experience contributes positively to the score.")

    if d.get("seniority_score", 0) < 0:
        comments.append("Seniority level is misaligned with the role.")
    else:
        comments.append("Seniority alignment is acceptable.")

    # Summary
    if score < 20:
        summary = "Overall very weak alignment with the role."
    elif score < 40:
        summary = "Partial alignment with the job requirements."
    elif score < 70:
        summary = "A fair match for the role."
    else:
        summary = "A strong candidate for this position."

    return summary + " " + " ".join(comments)


# =====================================================================
# ✅ SESSION
# =====================================================================
if "results" not in st.session_state:
    st.session_state.results = []


# =====================================================================
# ✅ SIDEBAR JD INPUT
# =====================================================================
st.sidebar.header("📄 Job Description")
jd_text = st.sidebar.text_area("Paste JD text here", height=300)


# =====================================================================
# ✅ FILE UPLOAD + ANALYZE
# =====================================================================
uploaded_files = st.file_uploader("Upload CVs (PDF/DOCX):", type=["pdf", "docx"], accept_multiple_files=True)

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
# ✅ SHOW RESULTS
# =====================================================================
results = st.session_state.results

if results:
    st.success("✅ Analysis complete")

    df = pd.DataFrame([{
        "File": r["filename"],
        "Name": r["cv_data"]["name"],
        "Score": r["match_score"],
        "Experience": r["cv_data"]["years_experience"]
    } for r in results])

    best = df["Score"].max()

    def highlight(row):
        return ["background-color:#d4f8d4" if row["Score"] == best else ""] * len(row)

    st.subheader("📊 Comparison Table")
    st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)

    # =================================================================
    # ✅ Candidate Detail
    # =================================================================
    st.subheader("🔍 Candidate Detail")

    selected_file = st.selectbox("Select candidate:", df["File"].tolist(), key="selected_candidate_file")

    candidate = next(r for r in results if r["filename"] == selected_file)
    cv = candidate["cv_data"]

    # PERSONAL INFO
    with st.expander(f"👤 Personal Info — {selected_file}", expanded=True):
        st.write(f"**Name:** {cv['name']}")
        st.write(f"**Email:** {cv['email']}")
        st.write(f"**Phone:** {cv['phone']}")
        st.write(f"**Experience:** {cv['years_experience']}")
        st.write(f"**Seniority:** {cv['seniority']}")
        st.write(f"**Last Position:** {cv['last_position']}")

    # TECHNOLOGIES
    with st.expander(f"🧩 Technologies — {selected_file}", expanded=False):
        st.write(", ".join(cv["technologies"]))

    # LANGUAGES
    with st.expander(f"🌐 Languages — {selected_file}", expanded=False):
        st.write(", ".join(cv["languages"]))

    # SUMMARY
    with st.expander(f"📝 Summary — {selected_file}", expanded=False):
        st.info(candidate["summary"])

    # WHY THIS SCORE
    with st.expander(f"🤖 Why this score? — {selected_file}", expanded=False):
        st.write(generate_ai_comment(candidate))

    # REQUIRED
    jd_req = candidate["jd_data"]["required_skills"]
    rows_req = [{
        "Skill": skill,
        "Matched": "✅ Yes" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌ No"
    } for skill in jd_req]

    with st.expander(f"🧩 Required Skills Match — {selected_file}", expanded=False):
        st.table(pd.DataFrame(rows_req))

    # OPTIONAL
    jd_opt = candidate["jd_data"]["nice_to_have_skills"]
    rows_opt = [{
        "Skill": skill,
        "Matched": "✅ Yes" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌ No"
    } for skill in jd_opt]

    with st.expander(f"🧩 Optional Skills Match — {selected_file}", expanded=False):
        st.table(pd.DataFrame(rows_opt))

    # MISSING SKILLS
    missing_req = [s for s in jd_req if not any(s.lower() in t.lower() for t in cv["technologies"])]
    missing_opt = [s for s in jd_opt if not any(s.lower() in t.lower() for t in cv["technologies"])]

    with st.expander(f"❗ Missing Skills — {selected_file}", expanded=False):
        if missing_req:
            st.warning("Missing Required: " + ", ".join(missing_req))
        else:
            st.success("All required skills present.")

        if missing_opt:
            st.info("Missing Optional: " + ", ".join(missing_opt))
        else:
            st.success("All optional skills present.")

    # =================================================================
    # ✅ Comparison Module
    # =================================================================
    with st.expander("🆚 Compare Candidates", expanded=False):

        if len(results) > 1:
            colA, colB = st.columns(2)
            with colA:
                left_file = st.selectbox("Candidate A", [r["filename"] for r in results], key="cmpA")
            with colB:
                right_file = st.selectbox("Candidate B", [r["filename"] for r in results], key="cmpB")

            if left_file != right_file:
                candA = next(r for r in results if r["filename"] == left_file)
                candB = next(r for r in results if r["filename"] == right_file)

                st.markdown("### 🔄 Comparison Overview")
                compare_df = pd.DataFrame([
                    {
                        "Attribute": "Score",
                        candA["cv_data"]["name"]: candA["match_score"],
                        candB["cv_data"]["name"]: candB["match_score"]
                    },
                    {
                        "Attribute": "Experience",
                        candA["cv_data"]["name"]: candA["cv_data"]["years_experience"],
                        candB["cv_data"]["name"]: candB["cv_data"]["years_experience"]
                    },
                    {
                        "Attribute": "Seniority",
                        candA["cv_data"]["name"]: candA["cv_data"]["seniority"],
                        candB["cv_data"]["name"]: candB["cv_data"]["seniority"]
                    }
                ])
                st.table(compare_df)

                # SIDE BY SIDE REQUIRED SKILLS
                st.markdown("### ❗ Missing Required Skills (Side by Side)")

                rows = []
                for skill in jd_req:
                    rows.append({
                        "Skill": skill,
                        candA["cv_data"]["name"]: "❌" if skill not in candA["cv_data"]["technologies"] else "✅",
                        candB["cv_data"]["name"]: "❌" if skill not in candB["cv_data"]["technologies"] else "✅"
                    })

                st.table(pd.DataFrame(rows))

    # =================================================================
    # ✅ GLOBAL EXPORT PANEL
    # =================================================================
    with st.expander("📤 Export All Candidates", expanded=False):

        export_format = st.selectbox("Format:", ["CSV", "PDF (summary)"], key="exp_fmt")

        if st.button("Export Now", key="export_btn", use_container_width=True):
            if export_format == "CSV":
                csv_data = export_all_candidates_to_csv(results)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="candidates_export.csv",
                    mime="text/csv"
                )

            else:
                pdf_data = export_all_candidates_to_pdf(results)
                st.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name="candidates_export.pdf",
                    mime="application/pdf"
                )

    # =================================================================
    # ✅ RAW JSON
    # =================================================================
    with st.expander(f"📦 Raw JSON Response — {selected_file}", expanded=False):
        st.json(candidate)
