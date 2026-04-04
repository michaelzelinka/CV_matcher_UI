import streamlit as st
import requests
import pandas as pd

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO


# =====================================================================
# ✅ BASE CONFIG
# =====================================================================
BACKEND_URL = "https://cv-parser-aewt.onrender.com/parse"
st.set_page_config(page_title="AI CV Matcher", layout="wide")


# =====================================================================
# ✅ PDF GENERATOR
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

    # Required skills
    if d.get("required_ratio", 0) == 0:
        reasons.append("Candidate does not match any required hard skills.")
    else:
        reasons.append("Candidate matches some of the required technical skills.")

    # Optional skills
    if d.get("optional_ratio", 0) > 0:
        reasons.append("Candidate matches some optional skills.")
    else:
        reasons.append("No optional skills matched.")

    # Experience logic
    if d.get("experience_score", 0) == 10:
        reasons.append("Experience fallback applied (role likely trainee-level).")
    elif d.get("experience_score", 0) == 0:
        reasons.append("Experience does not meet role expectations.")

    # Seniority
    if d.get("seniority_score", 0) == 10:
        reasons.append("Seniority matches job expectations.")
    else:
        reasons.append("Seniority differs from the role expectation.")

    # Final overview
    if score < 20:
        summary = "Overall, the candidate has low alignment with job requirements."
    elif score < 40:
        summary = "Overall, the candidate shows partial alignment with the role."
    elif score < 70:
        summary = "Overall, the candidate is a reasonable match for the role."
    else:
        summary = "Overall, the candidate is a strong match."

    return summary + " " + " ".join(reasons)


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
    placeholder="Paste JD text…",
    height=300
)


# =====================================================================
# ✅ FILE UPLOAD
# =====================================================================
uploaded_files = st.file_uploader(
    "Upload CVs (PDF or DOCX):",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

analyze_btn = st.button("🚀 Analyze")


# =====================================================================
# ✅ ANALYSIS LOGIC
# =====================================================================
if analyze_btn:
    if not uploaded_files:
        st.error("Please upload at least one CV.")
        st.stop()

    if not jd_text.strip():
        st.error("Please paste Job Description.")
        st.stop()

    result_list = []

    with st.spinner("Analyzing CVs…"):
        for f in uploaded_files:
            resp = requests.post(
                BACKEND_URL,
                files={"file": (f.name, f.getvalue())},
                data={"jd": jd_text}
            )

            if resp.status_code != 200:
                st.error(f"Error processing {f.name}: {resp.text}")
                continue

            data = resp.json()
            data["filename"] = f.name
            result_list.append(data)

    st.session_state.results = result_list


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
        "Experience": r["cv_data"]["years_experience"],
        "Technologies": ", ".join(r["cv_data"]["technologies"]),
    } for r in results])

    best = df["Score"].max()

    def highlight_best(row):
        return ["background-color: #d4f8d4" if row["Score"] == best else ""] * len(row)

    st.subheader("📊 Comparison Table")
    st.dataframe(df.style.apply(highlight_best, axis=1), use_container_width=True)


    # =================================================================
    # ✅ CANDIDATE DETAIL (filename-based switching)
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
    # ✅ REQUIRED SKILLS MATCH TABLE
    # =================================================================
    st.subheader("🧩 Required Skills Match")

    jd_req = candidate["jd_data"]["required_skills"]
    rows_req = []

    for skill in jd_req:
        matched = any(skill.lower() in t.lower() for t in cv["technologies"])
        rows_req.append({
            "JD Required Skill": skill,
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
            "JD Optional Skill": skill,
            "Matched": "✅ Yes" if matched else "❌ No"
        })

    st.table(pd.DataFrame(rows_opt))


    # =================================================================
    # ✅ PDF EXPORT
    # =================================================================
    st.subheader("📄 Export PDF")
    pdf_buffer = generate_pdf(candidate)

    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer,
        file_name=f"{cv['name'].replace(' ', '_')}_report.pdf",
        mime="application/pdf"
    )


    # =================================================================
    # ✅ RAW DEBUG
    # =================================================================
    with st.expander("📦 Raw JSON Response"):
        st.json(candidate)
