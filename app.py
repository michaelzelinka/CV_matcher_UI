import streamlit as st
import requests
import pandas as pd
import csv
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


# ================================================================
# ✅ CORPORATE THEME
# ================================================================
st.set_page_config(
    page_title="AI CV Matcher",
    layout="wide",
)

CORPORATE_BG = "#F5F7FA"
CARD_BG = "#FFFFFF"
BORDER = "1px solid #E5E7EB"
PRIMARY = "#2563EB"
TEXT = "#111827"
SUBTLE = "#6B7280"
SUCCESS = "#16A34A"
WARN = "#D97706"
ERROR = "#DC2626"


# ================================================================
# ✅ BACKEND URL
# ================================================================
BACKEND_URL = "https://cv-parser-aewt.onrender.com/parse"


# ================================================================
# ✅ STYLE OVERRIDES
# ================================================================
st.markdown(
    f"""
    <style>
        body {{
            background-color: {CORPORATE_BG};
        }}
        .candidate-card {{
            background-color: {CARD_BG};
            padding: 18px;
            border-radius: 10px;
            border: 1px solid #E5E7EB;
            margin-bottom: 14px;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .candidate-card:hover {{
            border-color: {PRIMARY};
            box-shadow: 0 0 8px rgba(37, 99, 235, 0.15);
        }}
        .score-badge {{
            padding: 4px 10px;
            border-radius: 30px;
            color: white;
            font-weight: 600;
        }}
    </style>
    """,
    unsafe_allow_html=True
)


# ================================================================
# ✅ HELPER FUNCTIONS
# ================================================================
def score_color(score):
    if score < 25: return ERROR
    if score < 50: return WARN
    if score < 75: return "#EAB308"  # Yellow
    return SUCCESS


def score_badge(score):
    return f"<span class='score-badge' style='background:{score_color(score)}'>{score}</span>"


def tag(text):
    return f"<span style='background:#E5E7EB; padding:4px 8px; border-radius:6px; margin-right:4px; font-size:13px;'>{text}</span>"


def export_all_candidates_to_csv(results):
    output = BytesIO()
    writer = csv.writer(output)
    writer.writerow(["File", "Name", "Email", "Experience", "Score"])

    for r in results:
        cv = r["cv_data"]
        writer.writerow([
            r["filename"],
            cv["name"],
            cv["email"],
            cv["years_experience"],
            r["match_score"],
        ])
    output.seek(0)
    return output


# ================================================================
# ✅ SIDEBAR
# ================================================================
st.sidebar.title("📄 Job Description")
jd_text = st.sidebar.text_area("Paste JD text here:", height=300)


uploaded_files = st.sidebar.file_uploader(
    "Upload CV files:",
    type=["pdf", "docx"],
    accept_multiple_files=True,
)

if st.sidebar.button("🚀 Analyze"):
    if not uploaded_files:
        st.error("Upload at least one CV.")
        st.stop()
    if not jd_text.strip():
        st.error("Paste a Job Description.")
        st.stop()

    out = []
    with st.spinner("Analyzing candidates…"):
        for f in uploaded_files:
            resp = requests.post(
                BACKEND_URL,
                files={"file": (f.name, f.getvalue())},
                data={"jd": jd_text},
            )
            if resp.status_code == 200:
                parsed = resp.json()
                parsed["filename"] = f.name
                out.append(parsed)
            else:
                st.error(f"Error processing {f.name}: {resp.text}")

    st.session_state.results = out


# ================================================================
# ✅ RESULTS AREA
# ================================================================
st.title("💼 AI CV Matcher — Corporate Edition")

results = st.session_state.get("results", [])

if not results:
    st.info("Upload CV files and paste a Job Description to begin.")
    st.stop()


# ================================================================
# ✅ LEFT: CANDIDATE GRID
# ✅ RIGHT: CANDIDATE DETAIL PANEL
# ================================================================
left, right = st.columns([1, 2])


# ================================================================
# ✅ LEFT PANE — CANDIDATE CARDS
# ================================================================
with left:
    st.subheader("Candidates")

    # Map for selecting detail
    display_map = {
        f"{r['cv_data']['name']} ({r['filename']})": r["filename"]
        for r in results
    }

    if "selected_candidate" not in st.session_state:
        st.session_state.selected_candidate = list(display_map.keys())[0]

    # Render cards
    for display_name, file_id in display_map.items():
        r = next(x for x in results if x["filename"] == file_id)

        score = r["match_score"]
        cv = r["cv_data"]

        card_clicked = st.container()
        with card_clicked:
            st.markdown(
                f"""
                <div class='candidate-card'>
                    <div style='display:flex; justify-content:space-between;'>
                        <div>
                            <div style='font-size:18px; font-weight:600;'>{cv['name']}</div>
                            <div style='color:{SUBTLE}; font-size:13px;'>{cv['years_experience']} yrs • {cv['seniority'] or "N/A"}</div>
                        </div>
                        <div>{score_badge(score)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Click → select candidate
        if st.button(f"Select {file_id}", key=f"btn_{file_id}"):
            st.session_state.selected_candidate = display_name


# ================================================================
# ✅ RIGHT PANE — CANDIDATE DETAIL
# ================================================================
with right:
    selected_display = st.session_state.selected_candidate
    selected_file = display_map[selected_display]

    candidate = next(r for r in results if r["filename"] == selected_file)
    cv = candidate["cv_data"]

    st.subheader(f"Candidate Detail — {cv['name']}")

    # ==========================================
    # HEADER SUMMARY CARD
    # ==========================================
    st.markdown(
        f"""
        <div style='background:white;padding:20px;border-radius:10px;border:1px solid #E5E7EB;margin-bottom:20px;'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div>
                    <div style='font-size:24px;font-weight:700;color:{TEXT};'>{cv['name']}</div>
                    <div style='color:{SUBTLE};font-size:14px;margin-top:4px;'>{cv['seniority']} • {cv['years_experience']} yrs experience</div>
                </div>
                <div style='font-size:32px;'>{score_badge(candidate["match_score"])}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # TABS LAYOUT (Corporate UX)
    # ==========================================
    tabs = st.tabs(["Skills", "Experience", "JD Match", "Missing Skills", "Raw JSON"])

    # TAB: Skills
    with tabs[0]:
        st.markdown("### Technologies")
        st.markdown(" ".join(tag(t) for t in cv["technologies"]), unsafe_allow_html=True)

        st.markdown("### Languages")
        st.markdown(" ".join(tag(l) for l in cv["languages"]), unsafe_allow_html=True)

    # TAB: Experience
    with tabs[1]:
        st.markdown("### Experience Summary")
        st.write(f"- **Years of experience:** {cv['years_experience']}")
        st.write(f"- **Last Position:** {cv['last_position']}")

    # TAB: JD Match
    with tabs[2]:
        jd_req = results[0]["jd_data"]["required_skills"]
        jd_opt = results[0]["jd_data"]["nice_to_have_skills"]

        st.markdown("### Required Skills Match")
        rows = [{
            "Skill": skill,
            "Matched": "✅" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌"
        } for skill in jd_req]
        st.table(pd.DataFrame(rows))

        st.markdown("### Optional Skills Match")
        rows_opt = [{
            "Skill": skill,
            "Matched": "✅" if any(skill.lower() in t.lower() for t in cv["technologies"]) else "❌"
        } for skill in jd_opt]
        st.table(pd.DataFrame(rows_opt))

    # TAB: Missing Skills
    with tabs[3]:
        missing_req = [s for s in jd_req if not any(s.lower() in t.lower() for t in cv["technologies"])]
        missing_opt = [s for s in jd_opt if not any(s.lower() in t.lower() for t in cv["technologies"])]

        st.markdown("### Missing Required Skills")
        if missing_req:
            st.markdown(" ".join(tag(s) for s in missing_req), unsafe_allow_html=True)
        else:
            st.success("All required skills matched!")

        st.markdown("### Missing Optional Skills")
        if missing_opt:
            st.markdown(" ".join(tag(s) for s in missing_opt), unsafe_allow_html=True)
        else:
            st.info("All optional skills matched!")

    # TAB: Raw JSON
    with tabs[4]:
        st.json(candidate)


# ================================================================
# ✅ GLOBAL EXPORT
# ================================================================
st.divider()

st.subheader("📤 Export All Candidates")

col1, col2 = st.columns(2)
with col1:
    if st.button("Download CSV Export"):
        csv_file = export_all_candidates_to_csv(results)
        st.download_button(
            "Download CSV",
            csv_file,
            file_name="candidates.csv",
            mime="text/csv"
        )
with col2:
    if st.button("Download PDF Summary"):
        pdf_file = export_all_candidates_to_pdf(results)
        st.download_button(
            "Download PDF",
            pdf_file,
            file_name="candidates.pdf",
            mime="application/pdf"
        )
