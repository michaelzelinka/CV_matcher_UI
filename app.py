import streamlit as st

# =====================================================================================
# ✅ PAGE CONFIG
# =====================================================================================
st.set_page_config(
    page_title="CV Matcher",
    layout="wide",
)


# =====================================================================================
# ✅ THEME COLORS
# =====================================================================================
PRIMARY = "#2563EB"
CARD_BG = "#FFFFFF"
TEXT = "#111827"
SUBTLE = "#6B7280"
BG = "#F9FAFB"


# =====================================================================================
# ✅ HEADER (Hero Section)
# =====================================================================================

st.markdown(
    f"""
    <div style="text-align:center; margin-top:80px; margin-bottom:40px;">
        <h1 style="font-size:48px; font-weight:700; color:{TEXT}; margin-bottom:10px;">
            AI CV Matcher
        </h1>

        <p style="font-size:20px; color:{SUBTLE}; max-width:650px; margin:auto;">
            Save hours of manual CV review. Instantly compare candidates against your 
            job description using enterprise‑grade AI matching.
        </p>

        <div style="margin-top:40px;">
            <a href="/Compare" target="_self">
                <button style="
                    background:{PRIMARY};
                    border:none;
                    padding:14px 36px;
                    border-radius:8px;
                    font-size:18px;
                    color:white;
                    cursor:pointer;
                ">
                    Try Internal Demo
                </button>
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================================================================
# ✅ FEATURES GRID (4 Cards)
# =====================================================================================

cols = st.columns(4)

features = [
    ("📤", "Upload CVs", "Drag & drop PDF or DOCX files"),
    ("📝", "Paste JD", "Add the job description text"),
    ("⚡", "Instant Scoring", "AI matches CVs 0–100"),
    ("🆚", "Compare", "Side‑by‑side candidate view"),
]

for col, (icon, title, desc) in zip(cols, features):
    with col:
        st.markdown(
            f"""
            <div style="
                background:{CARD_BG};
                padding:24px;
                border-radius:12px;
                border:1px solid #E5E7EB;
                text-align:center;
                height:160px;
            ">
                <div style="font-size:36px; margin-bottom:10px;">{icon}</div>
                <div style="font-size:18px; font-weight:600; color:{TEXT}; margin-bottom:4px;">
                    {title}
                </div>
                <div style="font-size:13px; color:{SUBTLE};">
                    {desc}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# =====================================================================================
# ✅ FOOTER
# =====================================================================================

st.markdown(
    """
    <br><br><br>
    <p style="text-align:center; color:#9CA3AF; font-size:12px;">
        Internal demo build — not for external distribution
    </p>
    """,
    unsafe_allow_html=True
)
