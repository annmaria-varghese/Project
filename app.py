import streamlit as st
import wikipediaapi
import spacy
import random
import requests
from io import BytesIO
import base64
import tempfile
import streamlit.components.v1 as components

# optional (only if you want DOCX/PDF export)
# pip install python-docx fpdf
try:
    from docx import Document
    from fpdf import FPDF
except ImportError:
    Document = None
    FPDF = None

# ------------------- App Setup -------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------- Olive-Cream CSS -------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #f7f6f1; color: #2b2b2b; font-family: "Segoe UI", sans-serif; }
    .title { text-align: center; font-size: 40px; font-weight: 700; color: #3c5a3c !important; margin-bottom: 18px; }
    .card { background-color: #fff; padding: 18px; border-radius: 12px; border-left: 6px solid #4a5d23; margin-bottom: 18px; box-shadow: 0 6px 18px rgba(0,0,0,0.06);}
    .card h3 { color: #4a5d23 !important; margin-bottom: 8px; }
    .fact { padding: 10px 14px; margin: 8px 0; background: #fbfaf6; border-left: 4px solid #4a5d23; border-radius: 6px; font-size: 15px; color: #222; }
    .stButton>button { background-color: #4a5d23; color: #fff; border-radius: 6px; padding: 8px 16px; border: none; }
    .stButton>button:hover { background-color: #3c4d1d; transform: translateY(-2px); }
    .stTextInput>div>div>input { background-color: #fff; color: #222; border-radius: 6px; padding: 10px; border: 1px solid #ddd; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">QuickThink</div>', unsafe_allow_html=True)

# ------------------- Wikipedia & spaCy -------------------
nlp = spacy.load("en_core_web_sm")
wiki = wikipediaapi.Wikipedia(language='en', user_agent='QuickThinkApp/1.0')

# ------------------- Utilities -------------------
def get_online_summary(keyword, max_sentences=10):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents]
            return " ".join(sents[:max_sentences])
    except Exception:
        return None

def get_offline_summary(keyword, max_sentences=10):
    page = wiki.page(keyword)
    if page.exists():
        text = page.text
        doc = nlp(text)
        sents = [s.text.strip() for s in doc.sents]
        return " ".join(sents[:max_sentences])
    return None

def get_random_summary(max_sentences=10):
    url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            title = data.get("title", "Random Topic")
            text = data.get("extract", "")
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents]
            return title, " ".join(sents[:max_sentences])
    except Exception:
        return None, None

def extract_key_takeaways(text, n=3):
    doc = nlp(text)
    sents = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
    return sents[:n] if sents else []

def extract_fun_facts(text, num=4):
    doc = nlp(text)
    sents = [s.text.strip() for s in doc.sents if len(s.text.strip()) > 40]
    return random.sample(sents, min(num, len(sents))) if sents else []

# ------------------- Sidebar -------------------
with st.sidebar:
    st.markdown('<div class="card"><h3>QuickThink Features</h3>'
                '<p>Toggle features below:</p></div>', unsafe_allow_html=True)
    tts_enabled = st.checkbox("Enable Listen Mode", value=False)
    quiz_enabled = st.checkbox("Enable Quiz", value=True)
    graph_enabled = st.checkbox("Show Knowledge Map", value=True)
    export_enabled = st.checkbox("Enable Export", value=True)

# ------------------- Main Input -------------------
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('<div class="card"><h3>Search Topic</h3></div>', unsafe_allow_html=True)
    keyword = st.text_input("Enter a keyword", placeholder="e.g., Artificial Intelligence")

    c1, c2 = st.columns(2)
    with c1:
        generate_clicked = st.button("Generate", key="btn_generate")
    with c2:
        surprise_clicked = st.button("Surprise Me", key="btn_surprise")

# ------------------- Logic -------------------
if "essay" not in st.session_state:
    st.session_state.essay = None
    st.session_state.title = None

if generate_clicked and keyword:
    essay = get_online_summary(keyword) or get_offline_summary(keyword)
    if essay:
        st.session_state.essay = essay
        st.session_state.title = keyword
    else:
        st.error("No summary found for this keyword.")

if surprise_clicked:
    title, essay = get_random_summary()
    if essay:
        st.session_state.essay = essay
        st.session_state.title = title
    else:
        st.error("Couldn't fetch a random topic.")

# ------------------- Display Results -------------------
if st.session_state.essay:
    essay = st.session_state.essay
    title = st.session_state.title

    st.markdown(f'<div class="card"><h3>Summary - {title}</h3></div>', unsafe_allow_html=True)
    st.write(essay)

    st.markdown('<div class="card"><h3>Key Takeaways</h3></div>', unsafe_allow_html=True)
    for t in extract_key_takeaways(essay):
        st.markdown(f'<div class="fact">• {t}</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>Interesting Facts</h3></div>', unsafe_allow_html=True)
    for i, f in enumerate(extract_fun_facts(essay), 1):
        st.markdown(f'<div class="fact">{i}. {f}</div>', unsafe_allow_html=True)

    if export_enabled:
        st.markdown('<div class="card"><h3>Export Options</h3></div>', unsafe_allow_html=True)
        if Document and FPDF:
            doc = Document()
            doc.add_heading(title, level=1)
            doc.add_paragraph(essay)
            buffer = BytesIO()
            doc.save(buffer)
            b64 = base64.b64encode(buffer.getvalue()).decode()
            st.markdown(f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{title}.docx">Download DOCX</a>', unsafe_allow_html=True)

