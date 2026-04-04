import streamlit as st
import requests
import pandas as pd

# -------------------------------------------------
# 🔗 Backend URL (Render FastAPI)
# -------------------------------------------------
BACKEND_URL = "https://cv-parser-aewt.onrender.com/parse"

# -------------------------------------------------
# ⚙️ Streamlit Config
# -------------------------------------------------
st.set_page_config(page_title="AI CV Matcher", layout="wide")

st.title("🧠 AI CV Matcher")
st.caption("Analyze multiple CVs against a Job Description in seconds.")


# -------------------------------------------------
# 📄 SIDEBAR — Job Description
# -------------------------------------------------
st.sidebar.header("📄 Job Description")
jd_text = st.sidebar.text_area(
    "Paste the Job Description here:",
    placeholder="Example:\nBackend Developer with Python, SQL, Docker, 3+ years experience…",
    height=300
)


# -------------------------------------------------
# 📁 MAIN — CV Upload
# -------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload one or more CVs (PDF / DOCX):",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

analyze_btn = st.button("🚀 Analyze CVs", use_container_width=True)


# -------------------------------------------------
# 🔄 PROCESSING
# -------------------------------------------------
results = []

if analyze_btn:
    if not uploaded_files:
        st.error("❌ Please upload at least one CV.")
        st.stop()

    if not jd_text.strip():
        st.error("❌ Please paste the Job Description.")
        st.stop()

    with st.spinner("Analyzing CVs… This may take a moment ⏳"):
        for f in uploaded_files:
            files = {"file": (f.name, f.getvalue())}
            data = {"jd": jd_text}

            try:
                response = requests.post(BACKEND_URL, files=files, data=data)
            except Exception as e:
                st.error(f"❌ Failed to call backend for {f.name}: {e}")
                continue

            if response.status_code != 200:
                st.error(f"❌ Error processing {f.name}: {response.text}")
                continue

            parsed = response.json()
            parsed["filename"] = f.name
            results.append(parsed)


# -------------------------------------------------
# ✅ TABLE — Comparison
# -------------------------------------------------
if results:
    st.success("✅ Analysis completed!")

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

    # Highlight best score
    best_score = df["Score"].max()

    def highlight_best(row):
        return [
            "background-color: #d4f8d4" if row["Score"] == best_score else ""
            for _ in row
        ]

    st.subheader("📊 Comparison Table")
    st.dataframe(
        df.style.apply(highlight_best, axis=1), 
        use_container_width=True
    )


    # -------------------------------------------------
    # 🔍 Candidate Detail
    # -------------------------------------------------
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
    st.write(f"**Technologies:** {', '.join(c['technologies'])}")
    st.write(f"**Languages:** {', '.join(c['languages'])}")

    st.markdown("#### 📝 AI Summary")
    st.info(candidate["summary"])

    with st.expander("📦 Raw JSON Response"):
        st.json(candidate)
