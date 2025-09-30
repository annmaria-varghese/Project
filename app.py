import streamlit as st
import wikipediaapi
import spacy
import random
import requests
from io import BytesIO
import base64

try:
    from docx import Document
except ImportError:
    Document = None

# ------------------ App Setup ------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------ CSS ------------------
st.markdown("""
<style>
.stApp { background-color: #2b2f2b; color: #f3f2ec; font-family: "Segoe UI", sans-serif; }
.title { text-align: center; font-size: 42px; font-weight: 700; color: #a3b18a !important; margin-bottom: 18px; }
.card { background-color: #f3f2ec; color: #2b2f2b; padding: 20px; border-radius: 12px; border-left: 6px solid #a3b18a; margin-bottom: 18px; box-shadow: 0 6px 20px rgba(0,0,0,0.1);}
.card h3 { color: #4a5d23 !important; margin-bottom: 10px; }
.fact { padding: 10px 14px; margin: 8px 0; background: #fefcf2; border-left: 4px solid #a3b18a; border-radius: 6px; font-size: 15px; color: #222; }
.stButton>button { background-color: #a3b18a; color: #2b2f2b; border-radius: 6px; padding: 8px 16px; border: none; font-weight: 600; }
.stButton>button:hover { background-color: #8b9c5a; transform: translateY(-2px);}
.stTextInput>div>div>input { background-color: #fefcf2; color: #2b2f2b; border-radius: 6px; padding: 10px; border: 1px solid #ddd; }
details > summary { cursor: pointer; font-weight: 600; font-size:16px; margin-bottom:5px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">QuickThink</div>', unsafe_allow_html=True)

# ------------------ Wikipedia & spaCy ------------------
nlp = spacy.load("en_core_web_sm")
wiki = wikipediaapi.Wikipedia(language='en', user_agent='QuickThinkApp/1.0')

# ------------------ Utilities ------------------
def get_online_summary(keyword, max_sentences=10):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents]
            return " ".join(sents[:max_sentences])
    except:
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
    """Random topics list for reliability"""
    topics = ["Python (programming language)", "Artificial intelligence", "SpaceX", 
              "Shakespeare", "Blockchain", "Quantum computing", "Electric car"]
    keyword = random.choice(topics)
    summary = get_online_summary(keyword) or get_offline_summary(keyword)
    return keyword, summary

def extract_takeways(text, n=3):
    doc = nlp(text)
    sents = [s.text.strip() for s in doc.sents if len(s.text.strip()) > 20]
    return sents[:n] if sents else []

def extract_facts(text, num=4):
    doc = nlp(text)
    sents = [s.text.strip() for s in doc.sents if len(s.text.strip()) > 40]
    return random.sample(sents, min(num, len(sents))) if sents else []

def make_docx(title, essay, takeways, facts):
    if Document is None:
        return None
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(essay)
    doc.add_heading("Takeways", level=2)
    for t in takeways:
        doc.add_paragraph(t, style='List Bullet')
    doc.add_heading("Interesting Facts", level=2)
    for f in facts:
        doc.add_paragraph(f, style='List Number')
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def download_button(data: bytes, filename: str, label: str):
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'

# ------------------ Quiz MCQ ------------------
def generate_quiz_mcq(text, n_questions=5):
    doc = nlp(text)
    entities = list({ent.text for ent in doc.ents if len(ent.text) > 2})
    questions = []
    for i in range(min(n_questions, len(entities))):
        answer = random.choice(entities)
        sentence = None
        for s in doc.sents:
            if answer in s.text:
                sentence = s.text.strip()
                break
        if not sentence:
            continue
        # make options
        options = [answer]
        other_ents = [e for e in entities if e != answer]
        random.shuffle(other_ents)
        options.extend(other_ents[:3])
        random.shuffle(options)
        questions.append({"question": sentence.replace(answer, "_____"), 
                          "answer": answer, 
                          "options": options,
                          "explanation": f"The correct answer is '{answer}'."})
    return questions

# ------------------ Main Input ------------------
col1, col2 = st.columns([2,1])
with col1:
    keyword = st.text_input("Enter a keyword", placeholder="e.g., Artificial Intelligence")
    generate_clicked = st.button("Generate")
    surprise_clicked = st.button("Surprise Me")
    quiz_clicked = st.button("Quiz Me")

# ------------------ Session State ------------------
if "essay" not in st.session_state:
    st.session_state.essay = None
    st.session_state.title = None
if "quiz_results" not in st.session_state:
    st.session_state.quiz_results = []

# ------------------ Fetch Content ------------------
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

# ------------------ Display ------------------
if st.session_state.essay:
    essay = st.session_state.essay
    title = st.session_state.title
    takeways = extract_takeways(essay)
    facts = extract_facts(essay)

    st.markdown(f'<div class="card"><h3>{title} - Summary</h3></div>', unsafe_allow_html=True)
    st.write(essay)

    with st.expander("Takeways"):
        for t in takeways:
            st.markdown(f'<div class="fact">• {t}</div>', unsafe_allow_html=True)

    with st.expander("Interesting Facts"):
        for f in facts:
            st.markdown(f'<div class="fact">• {f}</div>', unsafe_allow_html=True)

    # Export DOCX
    if Document:
        doc_bytes = make_docx(title, essay, takeways, facts)
        if doc_bytes:
            st.markdown(download_button(doc_bytes, f"{title}.docx", "Export"), unsafe_allow_html=True)

    # Quiz MCQ
    if quiz_clicked:
        st.markdown('<div class="card"><h3>Quiz</h3></div>', unsafe_allow_html=True)
        quiz = generate_quiz_mcq(essay)
        if not quiz:
            st.info("Not enough content for quiz questions.")
        else:
            score = 0
            for idx, q in enumerate(quiz):
                st.markdown(f"**Q{idx+1}:** {q['question']}")
                choice = st.radio(f"Choose the answer:", q['options'], key=f"quiz_{idx}")
                check = st.button(f"Check Q{idx+1}", key=f"btn_{idx}")
                if check:
                    if choice == q['answer']:
                        st.success("Correct!")
                        score += 1
                    else:
                        st.error(f"Wrong! {q['explanation']}")
            st.markdown(f"**Total Score: {score} / {len(quiz)}**")
