# app.py
import streamlit as st

# ✨ Page config MUST be first Streamlit command
st.set_page_config(
    page_title="Clarity",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

import os
import json
from data import fetch_real_news, get_articles_by_bias # Import the new fetch function

# Initialize analytics
# Note: Re-initialize to ensure it's re-read if the file changes
# In production, use st.session_state for persistence.
@st.cache_resource
def get_analytics_instance():
    from analytics import Analytics
    return Analytics()

analytics = get_analytics_instance()

# --- ADVANCED CSS (Unchanged from last version, but included for completeness) ---
advanced_css = """
<style>
/* Import fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* CSS Variables for easy theming */
:root {
    --primary-color: #5B47FB; /* A vibrant purple */
    --primary-dark: #4936E8;
    --secondary-color: #F0F2F5; /* Light grey for secondary elements */
    --text-primary: #1A1A2E; /* Dark blue/black for primary text */
    --text-secondary: #6B7280; /* Grey for secondary text */
    --text-tertiary: #9CA3AF; /* Lighter grey */
    --bg-primary: #FFFFFF; /* White background */
    --bg-secondary: #F9FAFB; /* Off-white for cards, etc. */
    --border-color: #E5E7EB; /* Light border color */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global reset and base styles */
* {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

html, body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
    color: var(--text-primary);
    margin: 0;
    padding: 0;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Streamlit overrides */
.stApp {
    background: transparent;
}

.main .block-container {
    padding: 1rem;
    max-width: 100%;
    animation: fadeInUp 0.6s ease-out;
}

/* Typography with better hierarchy */
h1 {
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
    text-align: center !important;
    margin: 0 0 0.25rem 0 !important;
    letter-spacing: -0.02em !important;
    background: linear-gradient(135deg, var(--primary-color) 0%, #7C3AED 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    font-size: 1.125rem;
    color: var(--text-secondary);
    text-align: center;
    margin: 0 0 2rem 0;
    font-weight: 500;
    letter-spacing: -0.01em;
}

h2 { /* Section headers */
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    margin: 2rem 0 1rem 0 !important;
    letter-spacing: -0.01em !important;
    border-bottom: 2px solid var(--secondary-color);
    padding-bottom: 0.5rem;
}

h3 { /* Card titles */
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    margin: 0 0 0.5rem 0 !important;
    letter-spacing: -0.01em !important;
}

/* Bias selector section */
.bias-selector {
    background: var(--bg-primary);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin: 0 0 2rem 0;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-color);
}

.bias-selector h3 {
    text-align: center;
    margin-bottom: 1rem !important;
    font-size: 1.1rem !important;
    color: var(--text-secondary);
}

/* Enhanced slider styling */
.stSlider {
    padding: 0.5rem 0 !important;
}

.stSlider > div > div > div { /* Slider track */
    height: 8px !important;
    background: var(--secondary-color) !important;
    border-radius: 4px !important;
}

.stSlider > div > div > div > div { /* Slider thumb */
    width: 28px !important;
    height: 28px !important;
    background: var(--primary-color) !important;
    border: 4px solid var(--bg-primary) !important;
    box-shadow: var(--shadow-md) !important;
    transition: var(--transition) !important;
    cursor: pointer;
}

.stSlider > div > div > div > div:hover {
    transform: scale(1.1);
    box-shadow: var(--shadow-lg) !important;
}

/* Slider labels with icons */
.slider-labels {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1rem;
    padding: 0 0.5rem;
}

.slider-label {
    display: flex;
    flex-direction: column;
    align-items: center;
    font-size: 0.875rem;
    color: var(--text-tertiary);
    font-weight: 500;
    transition: var(--transition);
    flex: 1;
    text-align: center;
}

.slider-label.active {
    color: var(--primary-color);
    font-weight: 700;
    transform: scale(1.05);
}

.slider-icon {
    font-size: 1.5rem;
    margin-bottom: 0.25rem;
    transition: var(--transition);
}

/* News cards with enhanced styling */
.issue-card {
    background: var(--bg-primary);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-color);
    transition: var(--transition);
    animation: slideIn 0.5s ease-out;
    animation-fill-mode: both;
}

/* Staggered animation for cards */
.issue-card:nth-child(1) { animation-delay: 0.1s; }
.issue-card:nth-child(2) { animation-delay: 0.2s; }
.issue-card:nth-child(3) { animation-delay: 0.3s; }

@media (hover: hover) {
    .issue-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
    }
}

/* Keywords with pill design */
.keywords {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0.75rem 0 1rem 0;
}

.keyword-pill {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    background: var(--secondary-color);
    color: var(--text-secondary);
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
    transition: var(--transition);
}

.keyword-pill:hover {
    background: var(--primary-color);
    color: white;
    transform: scale(1.05);
}

/* Article items with better visual hierarchy */
.article-item {
    display: block;
    padding: 1rem;
    margin: 0.75rem 0;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    text-decoration: none;
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}

.article-item::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    width: 4px;
    background: var(--primary-color);
    transform: translateX(-100%);
    transition: var(--transition);
}

.article-item:hover {
    background: var(--bg-primary);
    box-shadow: var(--shadow-sm);
    transform: translateX(4px);
}

.article-item:hover::before {
    transform: translateX(0);
}

.article-link {
    font-size: 1.0625rem !important;
    color: var(--text-primary) !important;
    text-decoration: none !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
    display: block !important;
    margin-bottom: 0.375rem !important;
}

.article-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem !important;
    color: var(--text-tertiary) !important;
}

.source-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.bias-left .source-badge {
    background: rgba(59, 130, 246, 0.1);
    color: #2563EB;
}

.bias-center .source-badge {
    background: rgba(107, 114, 128, 0.1);
    color: #4B5563;
}

.bias-right .source-badge {
    background: rgba(239, 68, 68, 0.1);
    color: #DC2626;
}

.bias-unavailable {
    background: #E5E7EB;
    color: #9CA3AF;
}

/* Enhanced buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    padding: 0.875rem 2rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    min-height: 48px !important;
    transition: var(--transition) !important;
    box-shadow: 0 4px 14px 0 rgba(91, 71, 251, 0.25) !important;
    width: 100% !important;
    cursor: pointer;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px 0 rgba(91, 71, 251, 0.35) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
    box-shadow: 0 2px 10px 0 rgba(91, 71, 251, 0.2) !important;
}

/* Feedback section with modern design */
.feedback-section {
    background: linear-gradient(135deg, rgba(91, 71, 251, 0.03) 0%, rgba(124, 58, 237, 0.03) 100%);
    border-radius: var(--radius-lg);
    padding: 2rem;
    margin: 3rem 0 2rem 0;
    border: 1px solid rgba(91, 71, 251, 0.1);
    position: relative;
    overflow: hidden;
}

.feedback-section::before {
    content: '💭';
    position: absolute;
    right: 1rem;
    top: 1rem;
    font-size: 3rem;
    opacity: 0.1;
    transform: rotate(15deg);
}

.stTextArea > div > div > textarea {
    border: 2px solid var(--border-color) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem !important;
    font-size: 1rem !important;
    font-family: 'Inter', sans-serif !important;
    transition: var(--transition) !important;
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    min-height: 120px !important;
}

.stTextArea > div > div > textarea:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(91, 71, 251, 0.15) !important;
}

/* Analytics dashboard section */
.analytics-section {
    background: var(--bg-primary);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-top: 2rem;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-color);
}

.analytics-section .stExpanderHeader {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: var(--text-secondary);
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1rem;
}

.metric-card {
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    padding: 1.25rem;
    text-align: center;
    transition: var(--transition);
    border: 1px solid var(--border-color);
}

@media (hover: hover) {
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-sm);
    }
}

.metric-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--primary-color);
    margin: 0 0 0.25rem 0;
}

.metric-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    font-weight: 500;
    margin: 0;
}

/* Animations */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}

/* Responsive adjustments */
@media (min-width: 768px) {
    .main .block-container {
        padding: 2rem;
        max-width: 720px;
    }

    h1 { font-size: 2.5rem !important; }
    .subtitle { font-size: 1.25rem; }
    .issue-card, .bias-selector, .feedback-section, .analytics-section { padding: 2rem; }

    .stButton > button {
        width: auto !important;
        min-width: 150px !important;
    }
    .feedback-section { margin: 3rem auto 2rem auto; }
}
</style>
"""
st.markdown(advanced_css, unsafe_allow_html=True)

# --- App Header ---
st.markdown("<h1>Clarity</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Break the echo chamber with news from all perspectives</p>", unsafe_allow_html=True)

# Log visit (do this early)
if 'visit_logged' not in st.session_state:
    analytics.log_visit()
    st.session_state.visit_logged = True

# --- Country Selector ---
COUNTRY_OPTIONS = {
    'Global (US)': 'us',
    'Australia': 'au',
    'United Kingdom': 'gb',
    'Canada': 'ca',
    'India': 'in',
    'Germany': 'de',
    'France': 'fr',
    'Japan': 'jp',
}
default_country = 'Australia' if st.session_state.get('initial_load', True) else st.session_state.get('country', 'Global (US)')
default_index = list(COUNTRY_OPTIONS.keys()).index(default_country)
st.session_state.initial_load = False

# This widget triggers a rerun when its value changes
selected_country_name = st.selectbox(
    '📍 Select your region',
    options=list(COUNTRY_OPTIONS.keys()),
    index=default_index,
    help="Select a region to view top headlines from that country."
)

selected_country_code = COUNTRY_OPTIONS[selected_country_name]

# Store the selected country in session state
if 'country' not in st.session_state or st.session_state.country != selected_country_code:
    st.session_state.country = selected_country_code
    st.rerun() # Rerun to fetch new articles based on country

# --- Bias Selector ---
st.markdown("<div class='bias-selector'>", unsafe_allow_html=True)
st.markdown("<h3>CHOOSE YOUR PERSPECTIVE</h3>", unsafe_allow_html=True)

bias_preference = st.slider(
    "Bias Preference",
    min_value=-1, max_value=1, value=0, step=1,
    label_visibility="collapsed"
)

# Update slider labels based on current preference
left_class = "active" if bias_preference == -1 else ""
center_class = "active" if bias_preference == 0 else ""
right_class = "active" if bias_preference == 1 else ""

st.markdown(f"""
<div class="slider-labels">
    <div class="slider-label {left_class}"><span class="slider-icon">⬅️</span> Left</div>
    <div class="slider-label {center_class}"><span class="slider-icon">⚖️</span> Center</div>
    <div class="slider-label {right_class}"><span class="slider-icon">➡️</span> Right</div>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Log slider usage (only if it changes)
if 'last_slider_pos' not in st.session_state or st.session_state.last_slider_pos != bias_preference:
    analytics.log_slider_position(bias_preference)
    st.session_state.last_slider_pos = bias_preference

# --- Fetch and Display Issues ---
st.markdown(f"<h2>Top Issues in {selected_country_name}</h2>", unsafe_allow_html=True)

# Use a spinner to show that news is loading
with st.spinner("Fetching today's headlines..."):
    # Pass the selected country code to the fetch function
    ISSUES = fetch_real_news(country_code=selected_country_code)

if not ISSUES:
    st.info("No news issues available from this region at the moment. Please try another region or check back later.")
else:
    for issue_index, issue in enumerate(ISSUES):
        st.markdown(f"<div class='issue-card' style='animation-delay: {issue_index * 0.1}s'>", unsafe_allow_html=True)
        st.markdown(f"<h3>{issue['headline']}</h3>", unsafe_allow_html=True)
        
        # Keywords
        keywords_html = "".join([f"<span class='keyword-pill'>{kw}</span>" for kw in issue['keywords']])
        st.markdown(f"<div class='keywords'><strong>Topics:</strong> {keywords_html}</div>", unsafe_allow_html=True)
        
        # Display the bias badges for this issue to show what's available
        biases_available_html = ""
        for bias_label in ['left', 'center', 'right']:
            badge_class = f"bias-{bias_label}" if bias_label in issue.get('biases_covered', []) else "bias-unavailable"
            biases_available_html += f"<span class='source-badge {badge_class}'>{bias_label.upper()}</span> "

        st.markdown(f"<p style='margin-bottom: 1rem;'><strong>Available Perspectives:</strong> {biases_available_html}</p>", unsafe_allow_html=True)

        filtered_articles = get_articles_by_bias(issue, bias_preference)
        
        if not filtered_articles:
            st.markdown("<p>No articles match your current bias preference for this issue.</p>", unsafe_allow_html=True)
        else:
            for article_index, article in enumerate(filtered_articles):
                bias_class = f"bias-{article['bias']}"
                article_html = f"""
                <a href="{article['url']}" target="_blank" rel="noopener noreferrer" class="article-item" style='animation-delay: {article_index * 0.05}s'>
                    <div class="article-link">{article['title']}</div>
                    <div class="article-meta">
                        <span>{article['source']}</span> • <span class="source-badge {bias_class}">{article['bias'].upper()}</span>
                    </div>
                </a>
                """
                st.markdown(article_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- Feedback Form ---
st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
st.markdown("<h2>Share Your Thoughts</h2>", unsafe_allow_html=True)
feedback_text = st.text_area(
    "How can we improve Clarity? Your feedback is valuable!",
    height=150,
    placeholder="What do you like? What could be better? Any features you'd love to see?",
    label_visibility="collapsed"
)

if st.button("Send Feedback"):
    if feedback_text.strip():
        st.success("🙏 Thank you! Your feedback has been received.")
    else:
        st.warning("Please enter some feedback before sending.")
st.markdown('</div>', unsafe_allow_html=True)

# --- Admin Analytics ---
st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
with st.expander("📊 Site Analytics (Admin Only)", expanded=False):
    admin_password = st.text_input("Enter Admin Password", type="password", key="admin_pass_expander")
    if admin_password == "clarity2023":
        summary = analytics.get_summary()
        st.markdown("<div class='metric-grid'>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='metric-card'><p class='metric-value'>{summary['total_visits']}</p><p class='metric-label'>Total Visits</p></div>
            <div class='metric-card'><p class='metric-value'>{summary['total_clicks']}</p><p class='metric-label'>Article Clicks</p></div>
            <div class='metric-card'><p class='metric-value'>{summary['avg_slider_position']:.1f}</p><p class='metric-label'>Avg. Slider Pos.</p></div>
            <div class='metric-card'><p class='metric-value'>{(summary['total_clicks']/max(1,summary['total_visits'])*100):.0f}%</p><p class='metric-label'>Click/Visit %</p></div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        if summary['clicks_by_url']:
            st.markdown("<h4>Clicks per Article URL:</h4>", unsafe_allow_html=True)
            for url, count in summary['clicks_by_url'].items():
                st.markdown(f"<small><code>{url}</code>: {count} clicks</small>", unsafe_allow_html=True)
        else:
            st.markdown("<small>No article clicks recorded yet.</small>", unsafe_allow_html=True)
    elif admin_password:
        st.error("Incorrect admin password.")
st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<hr style='margin-top: 3rem; border-color: var(--border-color);'>
<p style='text-align: center; font-size: 0.875rem; color: var(--text-tertiary); margin-top:1rem;'>
    Clarity MVP &copy; 2023. Striving for balanced perspectives.
</p>
""", unsafe_allow_html=True)
