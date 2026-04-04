import streamlit as st

# ================================================================
# ✅ PAGE CONFIG
# ================================================================
st.set_page_config(
    page_title="AI CV Matcher — Dark",
    layout="wide",
)

# ================================================================
# ✅ GLOBAL DARK THEME CSS (stable, safe)
# ================================================================
st.markdown("""
<style>

/* Global background */
body {
    background-color: #0D1117;
}

/* Text */
html, body, [class*="css"] {
    color: #E6EDF3 !important;
    font-family: 'Inter', sans-serif;
}

/* NAVBAR */
.navbar {
    width: 100%;
    background: #161B22;
    padding: 18px 28px;
    border-bottom: 1px solid #30363D;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.navbar-title {
    font-size: 20px;
    font-weight: 600;
}

.navbar-links a {
    margin-left: 22px;
    text-decoration: none;
    color: #8B949E;
    font-size: 15px;
}

.navbar-links a:hover {
    color: #58A6FF;
}

/* HERO SECTION */
.hero-title {
    font-size: 48px;
    font-weight: 700;
    text-align: center;
    margin-top: 60px;
}

.hero-sub {
    font-size: 20px;
    color: #8B949E;
    text-align: center;
    margin-top: -10px;
}

/* CTA BUTTON */
.primary-btn {
    background: linear-gradient(90deg, #1F6FEB, #388BFD);
    padding: 14px 36px;
    border-radius: 10px;
    color: white;
    border: none;
    font-size: 18px;
    font-weight: 600;
    cursor: pointer;
}
.primary-btn:hover {
    background: linear-gradient(90deg, #388BFD, #58A6FF);
}

/* FEATURE CARDS */
.feature-card {
    background: #161B22;
    border: 1px solid #30363D;
    padding: 24px;
    border-radius: 14px;
    height: 160px;
    text-align: center;
}
.feature-icon {
    font-size: 32px;
}
.feature-title {
    font-size: 18px;
    font-weight: 600;
}
.feature-desc {
    font-size: 14px;
    color: #8B949E;
}

</style>
""", unsafe_allow_html=True)


# ================================================================
# ✅ NAVBAR
# ================================================================
st.markdown("""
<div class="navbar">
    <div class="navbar-title">AI CV Matcher</div>
    <div class="navbar-links">
        <a href="/">Home</a>
        <a href="/Compare">Compare</a>
        <a href="/History">History</a>
    </div>
</div>
""", unsafe_allow_html=True)


# ================================================================
# ✅ HERO SECTION
# ================================================================
st.markdown("""
<div class="hero-title">AI CV Matcher</div>
<div class="hero-sub">
    Save hours of manual CV review. Instantly compare candidates against your job description using AI‑powered matching.
</div>

<div style='text-align:center; margin-top:40px;'>
    <a href="/Compare">
        <button class="primary-btn">Try Internal Demo</button>
    </a>
</div>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)


# ================================================================
# ✅ FEATURE CARDS
# ================================================================
cols = st.columns(4)

features = [
    ("📤", "Upload CVs", "Drag & drop PDF or DOCX files"),
    ("📝", "Paste JD", "Add the job description text"),
    ("⚡", "Instant Scoring", "AI matches CVs 0–100"),
    ("🆚", "Compare", "Side-by-side evaluation"),
]

for col, (icon, title, desc) in zip(cols, features):
    with col:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <div class="feature-title">{title}</div>
            <div class="feature-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)


# ================================================================
# ✅ FOOTER
# ================================================================
st.markdown("""
<br><br><br>
<p style="text-align:center; color:#6B7280; font-size:12px;">
    Internal demo build — not for external distribution
</p>
""", unsafe_allow_html=True)
