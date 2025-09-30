import streamlit as st
import wikipediaapi
import spacy
import random
import requests

# ------------------- App Setup -------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------- Custom Olive-Cream CSS -------------------
st.markdown(
    """
    <style>
    /* Background */
    .stApp {
        background-color: #fdfcf7; /* Cream */
        color: #2b2b2b;
        font-family: "Segoe UI", sans-serif;
    }

    /* Title */
    .title {
        text-align: center;
        font-size: 40px;
        font-weight: 700;
        color: #3c5a3c !important; /* Olive Green */
        margin-bottom: 25px;
        letter-spacing: -0.5px;
    }

    /* Card style */
    .card {
        background-color: #e9e8e2; /* Soft cream */
        padding: 22px;
        border-radius: 12px;
        border-left: 6px solid #4a5d23; /* Olive accent */
        margin-bottom: 22px;
        color: #2b2b2b !important;
    }

    /* Headings inside cards */
    .card h3 {
        color: #4a5d23 !important;
        font-weight: 700;
        margin-bottom: 12px;
    }

    /* Facts styling */
    .fact {
        padding: 10px 14px;
        margin: 8px 0;
        background: #f6f5ef;
        border-left: 4px solid #4a5d23;
        border-radius: 6px;
        font-size: 15px;
        color: #2b2b2b !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #4a5d23;
        color: #ffffff;
        font-weight: 600;
        border-radius: 6px;
        padding: 10px 20px;
        border: none;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #3c4d1d;
        transform: translateY(-2px);
    }

    /* Input box */
    .stTextInput>div>div>input {
        background-color: #ffffff;
        color: #2b2b2b;
        border-radius: 6px;
        padding: 10px;
        border: 1px solid #ccc;
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
        <p>QuickThink helps you learn smarter, faster, and more efficiently. With just one keyword, it generates meaningful content and insights tailored for quick exploration.</p>
        <ul>
            <li><b>Concise Summaries</b> – Get an easy-to-read breakdown of your chosen topic.</li>
            <li><b>Key Insights</b> – Discover interesting facts you might not know.</li>
            <li><b>Minimal Effort</b> – One keyword is all it takes to start learning.</li>
            <li><b>Clean Interface</b> – A distraction-free environment focused on knowledge.</li>
        </ul>
        <p><i>Perfect for students, curious minds, and anyone who loves fast learning.</i></p>
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
def get_online_summary(keyword, max_sentences=10):
    """Fetch a longer summary from Wikipedia (about 10 sentences)."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            sentences = text.split(". ")
            return ". ".join(sentences[:max_sentences]) + ("..." if len(sentences) > max_sentences else "")
    except:
        return None

def get_offline_summary(keyword, max_sentences=10):
    """Fallback using wikipedia-api"""
    page = wiki.page(keyword)
    if page.exists():
        sentences = page.text.split(". ")
        return ". ".join(sentences[:max_sentences]) + ("..." if len(sentences) > max_sentences else "")
    return None

def extract_fun_facts(text, num_facts=3):
    """Extract random fun facts from the text"""
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 25]
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
        if not essay:
            essay = get_offline_summary(keyword)

        if not essay:
            st.error("No article found for this keyword.")
        else:
            st.markdown('<div class="card"><h3>Summary</h3></div>', unsafe_allow_html=True) 
            st.write(essay)

            st.markdown('<div class="card"><h3>Key Insights</h3></div>', unsafe_allow_html=True) 
            facts = extract_fun_facts(essay)
            for i, fact in enumerate(facts, 1):
                st.markdown(f'<div class="fact">{i}. {fact}</div>', unsafe_allow_html=True)
