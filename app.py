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

    def line(text, fontsize=12, spacing=18):
        nonlocal y
        c.setFont("Helvetica", fontsize)
        c.drawString(x, y, text)
        y -= spacing

    line(f"AI CV Match Report – {cv['name']}", 16, 24)
    line(f"Final Score: {score} / 100", 14, 20)
    line("")

    line("Candidate Info:", 14, 20)
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

        def line(text, fontsize=12, spacing=18):
            nonlocal y
            c.setFont("Helvetica", fontsize)
            c.drawString(x, y, text)
            y -= spacing

        line(f"Candidate: {cv['name']}", 16, 24)
        line(f"Score: {r['match_score']}")
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

    parts = []

    if d.get("required_score", 0) == 0:
        parts.append("Candidate does not match any required hard skills.")
    else:
        parts.append("Candidate matches some required skills.")

    if d.get("optional_score", 0) > 0:
        parts.append("Candidate matches several optional skills.")
    else:
        parts.append("Optional skills show no match.")

    if d.get("experience_score", 0) == 0:
        parts.append("Experience does not meet expectations.")
    else:
        parts.append("Experience contributes positively.")

    if d.get("seniority_score", 0) < 0:
        parts.append("Seniority is misaligned with the role.")

    if score < 20:
        summary = "Overall weak alignment with the role."
    elif score < 40:
        summary = "Partial fit."
    elif score < 70:
        summary = "Reasonable match."
    else:
        summary = "Strong match."

    return summary + " " + " ".join(parts)


# =====================================================================
# ✅ SESSION INIT
# =====================================================================
if "results" not in st.session_state:
    st.session_state.results = []


# =====================================================================
# ✅ SIDEBAR INPUT (JD)
# =====================================================================
st.sidebar.header("📄 Job Description")
jd_text = st.sidebar.text_area("Paste JD here:", height=300)


# =====================================================================
# ✅ UPLOAD + ANALYZE
# =====================================================================
uploaded_files = st.file_uploader(
    "Upload CVs (PDF/DOCX):",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if st.button("🚀 Analyze"):
    if not uploaded_files:
        st.error("Please upload at least one CV.")
        st.stop()

    if not jd_text.strip():
        st.error("Please paste the Job Description.")
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
# ✅ RESULTS
# =====================================================================
results = st.session_state.results

if results:
    st.success("✅ Analysis complete")

    # table
    df = pd.DataFrame([{
        "File": r["filename"],
        "Name": r["cv_data"]["name"],
        "Score": r["match_score"],
        "Experience": r["cv_data"]["years_experience"],
    } for r in results])

    best = df["Score"].max()

    def highlight(row):
        return ["background-color:#d4f8d4" if row["Score"] == best else "" for _ in row]

    st.subheader("📊 Comparison Table")
    st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)

    # =================================================================
    # ✅ CANDIDATE DETAIL
    # =================================================================
    st.subheader("🔍 Candidate Detail")

    # Map for display and internal selection
    display_map = {
        f"{r['cv_data']['name']} ({r['filename']})": r["filename"]
        for r in results
    }

    selected_display = st.selectbox(
        "Select candidate:",
        list(display_map.keys()),
        key="selected_candidate"
    )

    selected_file = display_map[selected_display]
    candidate = next(r for r in results if r["filename"] == selected_file)
    cv = candidate["cv_data"]

    # PERSONAL INFO
    with st.expander(f"👤 Personal Info — {selected_display}", expanded=True):
        st.write(f"**Name:** {cv['name']}")
        st.write(f"**Email:** {cv['email']}")
        st.write(f"**Phone:** {cv['phone']}")
        st.write(f"**Experience:** {cv['years_experience']}")
        st.write(f"**Seniority:** {cv['seniority']}")
        st.write(f"**Last Position:** {cv['last_position']}")

    # TECHNOLOGIES
    with st.expander(f"🧩 Technologies — {selected_display}", expanded=False):
        st.write(", ".join(cv["technologies"]))

    # LANGUAGES
    with st.expander(f"🌐 Languages — {selected_display}", expanded=False):
        st.write(", ".join(cv["languages"]))

    # SUMMARY
    with st.expander(f"📝 Summary — {selected_display}", expanded=False):
        st.info(candidate["summary"])

    # WHY SCORE
    with st.expander(f"🤖 Why this score? — {selected_display}", expanded=False):
        st.write(generate_ai_comment(candidate))

    # REQUIRED SKILL MATCH
    jd_req = results[0]["jd_data"]["required_skills"]  # ✅ consistent JD source
    rows_req = [{
        "Skill": skill,
        "Matched": "✅" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌"
    } for skill in jd_req]

    with st.expander(f"🧩 Required Skills Match — {selected_display}", expanded=False):
        st.table(pd.DataFrame(rows_req))

    # OPTIONAL SKILL MATCH
    jd_opt = results[0]["jd_data"]["nice_to_have_skills"]
    rows_opt = [{
        "Skill": skill,
        "Matched": "✅" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌"
    } for skill in jd_opt]

    with st.expander(f"🧩 Optional Skills Match — {selected_display}", expanded=False):
        st.table(pd.DataFrame(rows_opt))

    # MISSING SKILLS
    with st.expander(f"❗ Missing Skills — {selected_display}", expanded=False):
        missing_req = [s for s in jd_req if not any(s.lower() in t.lower() for t in cv["technologies"])]
        missing_opt = [s for s in jd_opt if not any(s.lower() in t.lower() for t in cv["technologies"])]

        if missing_req:
            st.warning("Missing Required: " + ", ".join(missing_req))
        else:
            st.success("Candidate meets all required skills.")

        if missing_opt:
            st.info("Missing Optional: " + ", ".join(missing_opt))
        else:
            st.success("Candidate meets all optional skills.")

    # =================================================================
    # ✅ COMPARE CANDIDATES (FULLY FIXED)
    # =================================================================
    with st.expander("🆚 Compare Candidates", expanded=False):

        if len(results) > 1:

            compare_map = {
                f"{r['cv_data']['name']} ({r['filename']})": r["filename"]
                for r in results
            }

            colA, colB = st.columns(2)
            with colA:
                left_disp = st.selectbox("Candidate A:", list(compare_map.keys()), key="cmpA")
            with colB:
                right_disp = st.selectbox("Candidate B:", list(compare_map.keys()), key="cmpB")

            if left_disp != right_disp:
                candA = next(r for r in results if r["filename"] == compare_map[left_disp])
                candB = next(r for r in results if r["filename"] == compare_map[right_disp])

                st.markdown("### 🔄 Comparison Overview")

                overview = pd.DataFrame([
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
                    },
                ])
                st.table(overview)

                # JD (global)
                jd_req_global = results[0]["jd_data"]["required_skills"]

                def has_skill(cv_skills, skill):
                    return any(skill.lower() in s.lower() for s in cv_skills)

                comp_rows = [{
                    "Skill": skill,
                    candA["cv_data"]["name"]: "✅" if has_skill(candA["cv_data"]["technologies"], skill) else "❌",
                    candB["cv_data"]["name"]: "✅" if has_skill(candB["cv_data"]["technologies"], skill) else "❌"
                } for skill in jd_req_global]

                st.markdown("### ❗ Required Skills – Side by Side")
                st.table(pd.DataFrame(comp_rows))

    # =================================================================
    # ✅ EXPORT PANEL
    # =================================================================
    with st.expander("📤 Export All Candidates", expanded=False):
        export_format = st.selectbox("Export format:", ["CSV", "PDF"], key="exp_fmt")

        if st.button("Export Now", key="exp_btn", use_container_width=True):
            if export_format == "CSV":
                file = export_all_candidates_to_csv(results)
                st.download_button(
                    "Download CSV",
                    file,
                    file_name="candidates.csv",
                    mime="text/csv"
                )
            else:
                file = export_all_candidates_to_pdf(results)
                st.download_button(
                    "Download PDF",
                    file,
                    file_name="candidates.pdf",
                    mime="application/pdf"
                )

    # =================================================================
    # ✅ RAW JSON
    # =================================================================
    with st.expander(f"📦 Raw JSON — {selected_display}", expanded=False):
        st.json(candidate)
