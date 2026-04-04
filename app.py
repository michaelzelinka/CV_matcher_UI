import streamlit as st
import requests
import pandas as pd

# URL backendu (Render)
BACKEND_URL = "https://cv-parser-aewt.onrender.com/parse"

st.set_page_config(page_title="AI CV Matcher", layout="wide")

st.title("🧠 AI CV Matcher")
st.caption("Analyze multiple CVs against a Job Description — now with AI embeddings scoring v3.0")

# --------------------------------------------------------------------
# ✅ Session state (uchová výsledky i po překliknutí selectboxu)
# --------------------------------------------------------------------
if "results" not in st.session_state:
    st.session_state.results = []

# --------------------------------------------------------------------
# ✅ SIDEBAR: Job Description
# --------------------------------------------------------------------
st.sidebar.header("📄 Job Description")
jd_text = st.sidebar.text_area(
    "Paste the Job Description here:",
    placeholder="Example: Backend Developer with Python, SQL, Docker…",
    height=300
)

# --------------------------------------------------------------------
# ✅ MAIN: File upload
# --------------------------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload one or more CVs (PDF / DOCX):",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

analyze_btn = st.button("🚀 Analyze CVs", use_container_width=True)

# --------------------------------------------------------------------
# ✅ ANALYZE LOGIC
# --------------------------------------------------------------------
if analyze_btn:
    if not uploaded_files:
        st.error("Please upload at least one CV.")
        st.stop()

    if not jd_text.strip():
        st.error("Please paste the Job Description.")
        st.stop()

    out = []

    with st.spinner("Analyzing CVs… this may take some time ⏳"):
        for f in uploaded_files:
            files = {"file": (f.name, f.getvalue())}
            data = {"jd": jd_text}

            try:
                response = requests.post(BACKEND_URL, files=files, data=data)
            except Exception as e:
                st.error(f"❌ Backend unreachable for file {f.name}: {e}")
                continue

            if response.status_code != 200:
                st.error(f"❌ Error processing {f.name}: {response.text}")
            else:
                parsed = response.json()
                parsed["filename"] = f.name
                out.append(parsed)

    st.session_state.results = out  # ✅ SAVE to session


# --------------------------------------------------------------------
# ✅ RESULTS TABLE
# --------------------------------------------------------------------
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

    # highlight highest score
    best = df["Score"].max()

    def highlight_best(row):
        return [
            "background-color: #d4f8d4" if row["Score"] == best else ""
            for _ in row
        ]

    st.subheader("📊 Comparison Table")
    st.dataframe(df.style.apply(highlight_best, axis=1), use_container_width=True)


    # ----------------------------------------------------------------
    # ✅ CANDIDATE DETAIL
    # ----------------------------------------------------------------
    st.subheader("🔍 Candidate Detail")

    selected_name = st.selectbox(
        "Select a candidate:",
        df["Name"].tolist()
    )

    candidate = next(r for r in results if r["cv_data"]["name"] == selected_name)
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

    # Debug detail
    with st.expander("📦 Raw JSON Response"):
        st.json(candidate)
