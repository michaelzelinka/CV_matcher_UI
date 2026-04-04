import streamlit as st
import requests
import pandas as pd

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import csv


# =====================================================================
# ✅ BASE CONFIG
# =====================================================================
BACKEND_URL = "https://cv-parser-aewt.onrender.com/parse"
st.set_page_config(page_title="AI CV Matcher", layout="wide")


# =====================================================================
# ✅ PDF GENERATOR (single-candidate full report)
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
    line(f"Match Score: {score} / 100", 14, 22)
    line("")

    line("Candidate Information:", 14, 20)
    line(f"• Name: {cv['name']}")
    line(f"• Email: {cv['email']}")
    line(f"• Phone: {cv['phone']}")
    line(f"• Experience: {cv['years_experience']} years")
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
# ✅ AI COMMENT: WHY THIS SCORE?
# =====================================================================
def generate_ai_comment(candidate):
    d = candidate.get("details", {})
    score = candidate.get("match_score", 0)

    reasons = []

    # Required skills logic
    if d.get("required_ratio", 0) == 0:
        reasons.append("Candidate does not match any required hard skills.")
    else:
        reasons.append("Candidate matches some required technical skills.")

    # Optional skills logic
    if d.get("optional_ratio", 0) > 0:
        reasons.append("Candidate matches some nice‑to‑have skills.")
    else:
        reasons.append("No optional skills matched.")

    # Experience logic
    if d.get("experience_score", 0) == 10:
        reasons.append("Experience fallback applied (trainee-level or unclear requirement).")
    elif d.get("experience_score", 0) == 0:
        reasons.append("Experience level does not match the expected seniority.")

    # Seniority logic
    if d.get("seniority_score", 0) == 10:
        reasons.append("Seniority matches job expectations.")
    else:
        reasons.append("Seniority differs from the role requirement.")

    # Final summary
    if score < 20:
        summary = "Overall, the candidate has low alignment with the job requirements."
    elif score < 40:
        summary = "Overall, the candidate shows partial alignment with the role."
    elif score < 70:
        summary = "Overall, the candidate is a moderate match."
    else:
        summary = "Overall, the candidate is a strong match."

    return summary + " " + " ".join(reasons)


# =====================================================================
# ✅ EXPORT ALL CANDIDATES – CSV
# =====================================================================
def export_all_candidates_to_csv(results):
    output = BytesIO()
    writer = csv.writer(output)

    writer.writerow([
        "Filename", "Name", "Email", "Phone",
        "Experience (yrs)", "Seniority",
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


# =====================================================================
# ✅ EXPORT ALL CANDIDATES – MULTI-PDF
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
        line(f"Experience: {cv['years_experience']} years")
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
# ✅ SESSION
# =====================================================================
if "results" not in st.session_state:
    st.session_state.results = []


# =====================================================================
# ✅ SIDEBAR – JD INPUT
# =====================================================================
st.sidebar.header("📄 Job Description")
jd_text = st.sidebar.text_area(
    "Paste Job Description here",
    placeholder="Paste JD…",
    height=300
)


# =====================================================================
# ✅ FILE UPLOAD
# =====================================================================
uploaded_files = st.file_uploader(
    "Upload CVs (PDF / DOCX):",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

analyze_btn = st.button("🚀 Analyze CVs", use_container_width=True)


# =====================================================================
# ✅ ANALYSIS
# =====================================================================
if analyze_btn:

    if not uploaded_files:
        st.error("Please upload at least one CV.")
        st.stop()

    if not jd_text.strip():
        st.error("Please paste Job Description.")
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
                st.error(f"Error: {f.name} → {resp.text}")
            else:
                d = resp.json()
                d["filename"] = f.name
                out.append(d)

    st.session_state.results = out


# =====================================================================
# ✅ RESULTS
# =====================================================================
results = st.session_state.results

if results:

    st.success("✅ Analysis complete")

    df = pd.DataFrame([{
        "File": r["filename"],
        "Name": r["cv_data"]["name"],
        "Score": r["match_score"],
        "Experience": r["cv_data"]["years_experience"],
        "Technologies": ", ".join(r["cv_data"]["technologies"]),
    } for r in results])

    best = df["Score"].max()

    def highlight(row):
        return ["background-color: #d4f8d4" if row["Score"] == best else ""] * len(row)

    st.subheader("📊 Comparison Table")
    st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)

    # =================================================================
    # ✅ CANDIDATE DETAIL
    # =================================================================
    st.subheader("🔍 Candidate Detail")

    selected_file = st.selectbox(
        "Select a candidate:",
        df["File"].tolist()
    )

    candidate = next(r for r in results if r["filename"] == selected_file)
    cv = candidate["cv_data"]

    st.markdown(f"### 👤 {cv['name']}")
    st.write(f"**Email:** {cv['email']}")
    st.write(f"**Phone:** {cv['phone']}")
    st.write(f"**Experience:** {cv['years_experience']} years")
    st.write(f"**Seniority:** {cv['seniority']}")
    st.write(f"**Last Position:** {cv['last_position']}")

    st.markdown("#### 🧩 Technologies")
    st.write(", ".join(cv["technologies"]))

    st.markdown("#### 🌐 Languages")
    st.write(", ".join(cv["languages"]))

    st.markdown("#### 📝 Summary")
    st.info(candidate["summary"])


    # =================================================================
    # ✅ WHY THIS SCORE?
    # =================================================================
    st.subheader("🤖 Why this score?")
    st.write(generate_ai_comment(candidate))


    # =================================================================
    # ✅ REQUIRED SKILLS MATCH
    # =================================================================
    st.subheader("🧩 Required Skills Match")

    jd_req = candidate["jd_data"]["required_skills"]
    rows_req = []

    for skill in jd_req:
        matched = any(skill.lower() in t.lower() for t in cv["technologies"])
        rows_req.append({
            "JD Skill": skill,
            "Matched": "✅ Yes" if matched else "❌ No"
        })

    st.table(pd.DataFrame(rows_req))


    # =================================================================
    # ✅ OPTIONAL SKILLS MATCH
    # =================================================================
    st.subheader("🧩 Optional Skills Match")

    jd_opt = candidate["jd_data"]["nice_to_have_skills"]
    rows_opt = []

    for skill in jd_opt:
        matched = any(skill.lower() in t.lower() for t in cv["technologies"])
        rows_opt.append({
            "Optional Skill": skill,
            "Matched": "✅ Yes" if matched else "❌ No"
        })

    st.table(pd.DataFrame(rows_opt))


    # =================================================================
    # ✅ MISSING SKILLS PANEL
    # =================================================================
    st.subheader("❗ Missing Skills")

    missing_required = [
        s for s in jd_req
        if not any(s.lower() in t.lower() for t in cv["technologies"])
    ]

    missing_optional = [
        s for s in jd_opt
        if not any(s.lower() in t.lower() for t in cv["technologies"])
    ]

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
    # ✅ CANDIDATE COMPARISON PANEL
    # =================================================================
    st.subheader("🆚 Compare Candidates")

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

            compare_df = pd.DataFrame([
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
                },
            ])

            st.table(compare_df)


            # Missing skills comparison
            def missing(c):
                return [
                    s for s in c["jd_data"]["required_skills"]
                    if not any(s.lower() in t.lower() for t in c["cv_data"]["technologies"])
                ]

            st.markdown("### ❗ Missing Required Skills – Side by Side")
            comp_rows = []
            for skill in candidate["jd_data"]["required_skills"]:
                comp_rows.append({
                    "Required Skill": skill,
                    candA["cv_data"]["name"]: "❌" if skill in missing(candA) else "✅",
                    candB["cv_data"]["name"]: "❌" if skill in missing(candB) else "✅"
                })

            st.table(pd.DataFrame(comp_rows))


    # =================================================================
    # ✅ EXPORT PANEL
    # =================================================================
    st.subheader("📤 Export All Candidates")

    export_format = st.selectbox(
        "Choose export format:",
        ["CSV", "PDF (multi-page summary)"],
        key="export_format"
    )

    if st.button("Export", use_container_width=True):

        if export_format == "CSV":
            csv_file = export_all_candidates_to_csv(results)
            st.download_button(
                label="Download CSV",
                data=csv_file,
                file_name="candidates_export.csv",
                mime="text/csv"
            )

        elif export_format == "PDF (multi-page summary)":
            pdf_file = export_all_candidates_to_pdf(results)
            st.download_button(
                label="Download PDF",
                data=pdf_file,
                file_name="candidates_export.pdf",
                mime="application/pdf"
            )


    # =================================================================
    # ✅ RAW DEBUG
    # =================================================================
    with st.expander("📦 Raw JSON Response"):
        st.json(candidate)
