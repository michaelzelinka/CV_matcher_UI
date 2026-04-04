import streamlit as st
import requests
import pandas as pd

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO


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

    def line(text, fontsize=12, spacing=18):
        nonlocal y
        c.setFont("Helvetica", fontsize)
        c.drawString(x, y, text)
        y -= spacing

    # Header
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
    line(f"• Required Skills Match: {round(details.get('required_ratio', 0) * 100)} %")
    line(f"• Optional Skills Match: {round(details.get('optional_ratio', 0) * 100)} %")
    line(f"• Experience Score: {round(details.get('experience_score', 0))}/20")
    line(f"• Seniority Score: {round(details.get('seniority_score', 0))}/10")

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
# ✅ SIDEBAR – JD INPUT
# =====================================================================
st.sidebar.header("📄 Job Description")
jd_text = st.sidebar.text_area(
    "Paste the Job Description here:",
    placeholder="Example: Junior Backend Developer with Python, SQL…",
    height=300
)


# =====================================================================
# ✅ FILE UPLOAD
# =====================================================================
uploaded_files = st.file_uploader(
    "Upload one or more CVs (PDF / DOCX):",
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
        st.error("Please paste the Job Description.")
        st.stop()

    out = []

    with st.spinner("Analyzing CVs… ⏳"):
        for f in uploaded_files:
            files = {"file": (f.name, f.getvalue())}
            data = {"jd": jd_text}

            try:
                r = requests.post(BACKEND_URL, files=files, data=data)
            except Exception as e:
                st.error(f"Backend unreachable for file {f.name}: {e}")
                continue

            if r.status_code != 200:
                st.error(f"❌ Error processing {f.name}: {r.text}")
            else:
                parsed = r.json()
                parsed["filename"] = f.name
                out.append(parsed)

    st.session_state.results = out


# =====================================================================
# ✅ RESULTS TABLE
# =====================================================================
results = st.session_state.results

if results:
    st.success("✅ Analysis complete!")

    rows = []
    for r in results:
        rows.append({
            "File": r["filename"],
            "Name": r["cv_data"]["name"],
            "Score": r["match_score"],
            "Experience (yrs)": r["cv_data"]["years_experience"],
            "Technologies": ", ".join(r["cv_data"]["technologies"]),
        })

    df = pd.DataFrame(rows)

    best = df["Score"].max()

    def highlight_best(row):
        return ["background-color: #d4f8d4" if row["Score"] == best else ""] * len(row)

    st.subheader("📊 Comparison Table")
    st.dataframe(df.style.apply(highlight_best, axis=1), use_container_width=True)


    # =================================================================
    # ✅ CANDIDATE DETAIL (fixed: now selects by filename)
    # =================================================================
    st.subheader("🔍 Candidate Detail")

    selected_file = st.selectbox(
        "Select a candidate:",
        df["File"].tolist()
    )

    candidate = next(r for r in results if r["filename"] == selected_file)
    c = candidate["cv_data"]

    st.markdown(f"### 👤 {c['name']}")
    st.write(f"**Email:** {c['email']}")
    st.write(f"**Phone:** {c['phone']}")
    st.write(f"**Experience:** {c['years_experience']} years")
    st.write(f"**Seniority:** {c['seniority']}")
    st.write(f"**Last Position:** {c['last_position']}")

    st.markdown("#### 🧩 Technologies")
    st.write(", ".join(c["technologies"]))

    st.markdown("#### 🌐 Languages")
    st.write(", ".join(c["languages"]))

    st.markdown("#### 📝 Summary")
    st.info(candidate["summary"])


    # =================================================================
    # ✅ SCORING BREAKDOWN v2.0
    # =================================================================
    st.subheader("📈 Scoring Breakdown (v2.0)")

    details = candidate.get("details", {})

    required_ratio = details.get("required_ratio", 0)
    optional_ratio = details.get("optional_ratio", 0)
    req_score = details.get("required_score", required_ratio * 60)
    opt_score = details.get("optional_score", optional_ratio * 10)
    exp_score = details.get("experience_score", 0)
    sen_score = details.get("seniority_score", 0)
    final_score = candidate["match_score"]

    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Required Match", f"{round(required_ratio * 100)}%", f"{round(req_score)}/60")
    with colB:
        st.metric("Optional Match", f"{round(optional_ratio * 100)}%", f"{round(opt_score)}/10")
    with colC:
        st.metric("Final Score", f"{final_score} / 100")

    colD, colE = st.columns(2)
    with colD:
        st.metric("Experience Score", f"{round(exp_score)}/20")
    with colE:
        st.metric("Seniority Score", f"{round(sen_score)}/10")


    # =================================================================
    # ✅ REQUIRED SKILLS TABLE
    # =================================================================
    st.markdown("### 🧩 Required Skills Match")

    jd_req = candidate["jd_data"]["required_skills"] if candidate["jd_data"] else []
    cv_raw = candidate["cv_data"]["technologies"]

    rows_req = []
    for skill in jd_req:
        matched = any(skill.lower() in t.lower() for t in cv_raw)
        rows_req.append({
            "JD Required Skill": skill,
            "Matched": "✅ Yes" if matched else "❌ No"
        })

    st.table(pd.DataFrame(rows_req))


    # =================================================================
    # ✅ OPTIONAL SKILLS TABLE
    # =================================================================
    st.markdown("### 🧩 Nice-to-Have Skills Match")

    jd_opt = candidate["jd_data"]["nice_to_have_skills"] if candidate["jd_data"] else []

    rows_opt = []
    for skill in jd_opt:
        matched = any(skill.lower() in t.lower() for t in cv_raw)
        rows_opt.append({
            "JD Optional Skill": skill,
            "Matched": "✅ Yes" if matched else "❌ No"
        })

    st.table(pd.DataFrame(rows_opt))


    # =================================================================
    # ✅ PDF EXPORT
    # =================================================================
    st.subheader("📄 Export PDF Report")
    pdf_buffer = generate_pdf(candidate)

    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer,
        file_name=f"{c['name'].replace(' ', '_')}_report.pdf",
        mime="application/pdf"
    )


    # =================================================================
    # ✅ RAW DEBUG
    # =================================================================
    with st.expander("📦 Raw JSON Response"):
        st.json(candidate)
