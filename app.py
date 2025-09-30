import streamlit as st
import wikipediaapi
import spacy
import random
import requests

# ------------------- App Setup -------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------- Custom Professional CSS -------------------
st.markdown(
    """
    <style>
    /* Background */
    .stApp {
        background-color: #0e1117;
        color: #f5f5f5;
        font-family: "Segoe UI", sans-serif;
    }

    /* Title */
    .title {
        text-align: center;
        font-size: 40px;
        font-weight: 700;
        color: #ffffff !important;
        margin-bottom: 25px;
        letter-spacing: -0.5px;
    }

    /* Card style */
    .card {
        background-color: #1a1c23;
        padding: 22px;
        border-radius: 12px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        margin-bottom: 22px;
        color: #e1e1e1 !important;
    }

    /* Headings inside cards */
    .card h3 {
        color: #4dabf7 !important;
        font-weight: 600;
        margin-bottom: 10px;
    }

    /* Facts styling */
    .fact {
        padding: 10px 14px;
        margin: 8px 0;
        background: #2a2d36;
        border-left: 4px solid #4dabf7;
        border-radius: 6px;
        font-size: 15px;
        color: #f1f1f1 !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #4dabf7;
        color: #ffffff;
        font-weight: 600;
        border-radius: 6px;
        padding: 8px 18px;
        border: none;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #1e90ff;
        transform: translateY(-2px);
    }

    /* Input box */
    .stTextInput>div>div>input {
        background-color: #2d2f3e;
        color: #ffffff;
        border-radius: 6px;
        padding: 10px;
        border: 1px solid #444;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------- Title -------------------
st.markdown('<div class="title">QuickThink</div>', unsafe_allow_html=True)

# ------------------- User Instructions -------------------
st.markdown(
    """
    <div class="card">
        <h3>Getting Started</h3>
        <p>QuickThink gives you a concise overview of any topic along with a set of key insights.</p>
        <ol>
            <li>Enter a keyword or topic of interest.</li>
            <li>Click <b>Generate</b> to fetch information.</li>
            <li>Read a compact summary and explore useful facts.</li>
        </ol>
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------- Load spaCy -------------------
nlp = spacy.load("en_core_web_sm")

# ------------------- Wikipedia API -------------------
wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='QuickThinkApp/1.0 (your_email@example.com)'
)

# ------------------- Functions -------------------
def get_online_summary(keyword, max_chars=500):
    """Try to fetch summary from Wikipedia online"""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            return text[:max_chars] + "..." if len(text) > max_chars else text
    except:
        return None

def get_offline_summary(keyword, max_chars=500):
    """Use wikipedia-api local"""
    page = wiki.page(keyword)
    if page.exists():
        text = page.text
        return text[:max_chars] + "..." if len(text) > max_chars else text
    return None

def extract_fun_facts(text, num_facts=3):
    """Extract random fun facts from the text"""
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
    if not sentences:
        return ["No additional insights available."]
    return random.sample(sentences, min(num_facts, len(sentences)))

# ------------------- User Input -------------------
keyword = st.text_input("Enter a keyword", placeholder="e.g., Artificial Intelligence")

if st.button("Generate"):
    if not keyword.strip():
        st.warning("Please enter a keyword.")
    else:
        # Try online first
        essay = get_online_summary(keyword)
        if essay:
            st.info("Fetched online summary")
        else:
            essay = get_offline_summary(keyword)
            if essay:
                st.info("Using offline cached summary")
            else:
                st.error("No article found for this keyword.")
                essay = None

        if essay:
            st.markdown('<div class="card"><h3>Summary</h3></div>', unsafe_allow_html=True) 
            st.write(essay)

            st.markdown('<div class="card"><h3>Key Insights</h3></div>', unsafe_allow_html=True) 
            facts = extract_fun_facts(essay)
            for i, fact in enumerate(facts, 1):
                st.markdown(f'<div class="fact">{i}. {fact}</div>', unsafe_allow_html=True)
