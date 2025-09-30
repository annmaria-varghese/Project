import streamlit as st
import wikipediaapi
import spacy
import random
import requests
from io import BytesIO
from docx import Document
import base64
import streamlit.components.v1 as components

# ------------------- App Setup -------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------- Colors & CSS -------------------
st.markdown("""
<style>
body, .stApp {
    background-color: #3e2f1c;
    color: #f5f5dc;
    font-family: "Segoe UI", sans-serif;
}

.title {
    text-align: center;
    font-size: 48px;
    font-weight: 800;
    color: #a1c181 !important;
    margin-bottom: 30px;
    letter-spacing: -1px;
}

.card {
    background-color: #4e3d2a;
    padding: 22px;
    border-radius: 14px;
    margin-bottom: 20px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    border-left: 6px solid #a1c181;
}

.card h3 {
    color: #a1c181 !important;
    margin-bottom: 10px;
}

.fact {
    padding: 10px 14px;
    margin: 8px 0;
    background: #5a4635;
    border-left: 4px solid #a1c181;
    border-radius: 6px;
    font-size: 15px;
    color: #f5f5dc !important;
}

.big-button button {
    width: 220px;
    height: 60px;
    font-size: 22px;
    font-weight: 700;
    border-radius: 12px;
    border: none;
    cursor: pointer;
    transition: transform 0.2s ease-in-out;
    margin: 5px;
}

.big-button button:hover {
    transform: scale(1.05);
}

.generate-btn { background-color: #a1c181; color: #3e2f1c; }
.surprise-btn { background-color: #f5deb3; color: #3e2f1c; }
.quiz-btn { background-color: #c2d4c2; color: #3e2f1c; }
.export-btn { background-color: #8fbc8f; color: #3e2f1c; position: fixed; top: 20px; right: 20px; width: 130px; height: 50px; font-size: 16px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ------------------- Load Wikipedia & SpaCy -------------------
wiki = wikipediaapi.Wikipedia(language='en', user_agent='QuickThinkApp/1.0')
nlp = spacy.load("en_core_web_sm")

# ------------------- Utilities -------------------
def get_summary(keyword, max_sents=10):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents]
            return " ".join(sents[:max_sents]) + (" ..." if len(sents) > max_sents else "")
    except:
        page = wiki.page(keyword)
        if page.exists():
            doc = nlp(page.text)
            sents = [s.text.strip() for s in doc.sents if len(s.text.strip())>20]
            return " ".join(sents[:max_sents]) + (" ..." if len(sents) > max_sents else "")
    return None

def get_random_summary(max_sents=10):
    url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            title = data.get("title","Random Topic")
            extract = data.get("extract","")
            doc = nlp(extract)
            sents = [s.text.strip() for s in doc.sents]
            summary = " ".join(sents[:max_sents]) + (" ..." if len(sents)>max_sents else "")
            return title, summary
    except:
        return None, None
    return None, None

def extract_takeaways(text, n=3):
    doc = nlp(text)
    sents = [s.text.strip() for s in doc.sents if len(s.text.strip())>20]
    return sents[:n]

def extract_facts(text, n=4):
    doc = nlp(text)
    sents = [s.text.strip() for s in doc.sents if len(s.text.strip())>30]
    return random.sample(sents, min(n,len(sents))) if sents else ["No additional insights."]

def generate_quiz_mcq(text, n_questions=5):
    doc = nlp(text)
    candidates = list({ent.text for ent in doc.ents if len(ent.text)>2})
    candidates += [tok.text for tok in doc if tok.pos_ in ["PROPN","NOUN"] and len(tok.text)>2]
    candidates = list(set(candidates))
    questions = []
    for _ in range(n_questions):
        if not candidates: break
        answer = random.choice(candidates)
        sentence = None
        for s in doc.sents:
            if answer in s.text:
                sentence = s.text.strip()
                break
        if not sentence:
            candidates.remove(answer)
            continue
        options = [answer]
        other_options = [w for w in candidates if w!=answer]
        random.shuffle(other_options)
        options.extend(other_options[:3])
        while len(options)<4: options.append("None of these")
        random.shuffle(options)
        questions.append({
            "question": sentence.replace(answer,"_____"),
            "answer": answer,
            "options": options,
            "explanation": f"The correct answer is '{answer}'."
        })
        candidates.remove(answer)
    return questions

def make_docx(title, summary, takeaways, facts):
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(summary)
    doc.add_heading("Takeaways", level=2)
    for t in takeaways: doc.add_paragraph(t, style='List Bullet')
    doc.add_heading("Interesting Facts", level=2)
    for f in facts: doc.add_paragraph(f, style='List Number')
    bio = BytesIO(); doc.save(bio); bio.seek(0)
    return bio.getvalue()

def download_bytes(data: bytes, filename: str):
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download {filename}</a>'
    st.markdown(href, unsafe_allow_html=True)

# ------------------- Session State -------------------
if 'last_title' not in st.session_state: st.session_state['last_title'] = ""
if 'last_summary' not in st.session_state: st.session_state['last_summary'] = ""
if 'takeaways_shown' not in st.session_state: st.session_state['takeaways_shown'] = False
if 'facts_shown' not in st.session_state: st.session_state['facts_shown'] = False
if 'quiz_started' not in st.session_state: st.session_state['quiz_started'] = False
if 'quiz_questions' not in st.session_state: st.session_state['quiz_questions'] = []
if 'user_answers' not in st.session_state: st.session_state['user_answers'] = []
if 'quiz_score' not in st.session_state: st.session_state['quiz_score'] = 0

# ------------------- Anchors for scrolling -------------------
st.markdown('<div id="summary_anchor"></div>', unsafe_allow_html=True)
st.markdown('<div id="quiz_anchor"></div>', unsafe_allow_html=True)

# ------------------- Layout -------------------
st.markdown('<div class="title">QuickThink</div>', unsafe_allow_html=True)

# Buttons Row
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("Generate", key="gen"):
        if st.session_state.get("keyword_input"):
            summary = get_summary(st.session_state["keyword_input"])
            if summary:
                st.session_state['last_title'] = st.session_state["keyword_input"]
                st.session_state['last_summary'] = summary
                st.session_state['takeaways_shown'] = False
                st.session_state['facts_shown'] = False
                st.session_state['quiz_started'] = False
                # scroll to summary
                components.html("<script>location.href='#summary_anchor';</script>", height=0)
with col2:
    if st.button("Surprise Me", key="surp"):
        title, summary = get_random_summary()
        if title and summary:
            st.session_state['last_title'] = title
            st.session_state['last_summary'] = summary
            st.session_state['takeaways_shown'] = False
            st.session_state['facts_shown'] = False
            st.session_state['quiz_started'] = False
            components.html("<script>location.href='#summary_anchor';</script>", height=0)
with col3:
    if st.button("Quiz Me", key="quiz"):
        if st.session_state['last_summary']:
            st.session_state['quiz_questions'] = generate_quiz_mcq(st.session_state['last_summary'],5)
            st.session_state['user_answers'] = [""]*len(st.session_state['quiz_questions'])
            st.session_state['quiz_started'] = True
            st.session_state['quiz_score'] = 0
            components.html("<script>location.href='#quiz_anchor';</script>", height=0)

# ------------------- Search Bar -------------------
keyword = st.text_input("Enter a topic:", key="keyword_input")

# -------------------
