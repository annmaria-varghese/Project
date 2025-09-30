import streamlit as st
import wikipediaapi
import spacy
import random
import requests
from io import BytesIO
from docx import Document
from fpdf import FPDF
import base64

# ------------------- App Setup -------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------- CSS -------------------
st.markdown("""
<style>
body, .stApp { background-color: #3e2f2f; color: #f5f5dc; font-family: "Segoe UI", sans-serif; }
.title { text-align: center; font-size: 50px; font-weight: 700; color: #a4b27f; margin-bottom: 20px; }
.card { background-color: #4a5d23; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0px 4px 12px rgba(0,0,0,0.4); }
.card h3 { color: #f5f5dc !important; }
.fact { padding: 10px; margin: 6px 0; background: #fbfaf6; border-left: 4px solid #a4b27f; border-radius: 6px; color: #222; }
.stButton>button { font-size: 20px; font-weight: 700; padding: 15px 30px; border-radius: 10px; }
.generate-btn { background-color: #a4b27f; color: #3e2f2f; }
.generate-btn:hover { background-color: #8aa14e; }
.surprise-btn { background-color: #f5f5dc; color: #3e2f2f; }
.surprise-btn:hover { background-color: #e5e0b0; }
.quiz-btn { background-color: #ffcc00; color: #3e2f2f; }
.quiz-btn:hover { background-color: #e6b800; }
.export-btn { position: fixed; top: 20px; right: 40px; background-color: #f5f5dc; color: #3e2f2f; font-weight: 700; padding: 10px 20px; border-radius: 10px; z-index:999; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">QuickThink</div>', unsafe_allow_html=True)

# ------------------- Wikipedia & spaCy -------------------
nlp = spacy.load("en_core_web_sm")
wiki = wikipediaapi.Wikipedia(language='en', user_agent='QuickThinkApp/1.0')

# ------------------- Utilities -------------------
def get_summary(keyword, max_sentences=10):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents]
            return " ".join(sents[:max_sentences]) + (" ..." if len(sents)>max_sentences else "")
    except:
        page = wiki.page(keyword)
        if page.exists():
            text = page.text
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents if len(s.text.strip())>20]
            return " ".join(sents[:max_sentences]) + (" ..." if len(sents)>max_sentences else "")
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
            summary = " ".join(sents[:max_sentences]) + (" ..." if len(sents)>max_sentences else "")
            return title, summary
    except:
        return None, None
    return None, None

def extract_takeaways(text, n=3):
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if len(s.text.strip())>20]
    return sentences[:n]

def extract_facts(text, n=4):
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if len(s.text.strip())>30]
    if not sentences:
        return ["No additional insights available."]
    return random.sample(sentences, min(n, len(sentences)))

def generate_quiz_mcq(text, n_questions=5):
    doc = nlp(text)
    candidates = list({ent.text for ent in doc.ents if len(ent.text)>2})
    candidates += [tok.text for tok in doc if tok.pos_ in ["PROPN", "NOUN"] and len(tok.text)>2]
    candidates = list(set(candidates))
    questions=[]
    for _ in range(n_questions):
        if not candidates:
            break
        answer=random.choice(candidates)
        sentence=None
        for s in doc.sents:
            if answer in s.text:
                sentence=s.text.strip()
                break
        if not sentence:
            candidates.remove(answer)
            continue
        options=[answer]+random.sample([w for w in candidates if w!=answer],3)
        while len(options)<4:
            options.append("None of these")
        random.shuffle(options)
        questions.append({"question":sentence.replace(answer,"_____"), "answer":answer, "options":options, "explanation":f"The correct answer is '{answer}'."})
        candidates.remove(answer)
    return questions

def make_docx(title, summary, takeaways, facts):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(summary)
    doc.add_heading("Takeaways", 1)
    for t in takeaways:
        doc.add_paragraph(t, style='List Bullet')
    doc.add_heading("Interesting Facts",1)
    for f in facts:
        doc.add_paragraph(f, style='List Number')
    bio=BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

def download_link_bytes(data: bytes, filename: str, label:str, mime:str):
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:{mime};base64,{b64}" download="{filename}">{label}</a>'

# ------------------- Session State -------------------
if 'last_title' not in st.session_state:
    st.session_state['last_title'] = ""
if 'last_summary' not in st.session_state:
    st.session_state['last_summary'] = ""
if 'takeaways_visible' not in st.session_state:
    st.session_state['takeaways_visible'] = False
if 'facts_visible' not in st.session_state:
    st.session_state['facts_visible'] = False
if 'quiz_started' not in st.session_state:
    st.session_state['quiz_started'] = False
if 'quiz_score' not in st.session_state:
    st.session_state['quiz_score'] = 0
if 'quiz_questions' not in st.session_state:
    st.session_state['quiz_questions'] = []
if 'user_answers' not in st.session_state:
    st.session_state['user_answers'] = []

# ------------------- Top Buttons -------------------
col1, col2, col3, col4 = st.columns([2,2,2,1])
with col1:
    generate_clicked = st.button("Generate", key="generate", help="Generate summary", type="primary")
with col2:
    surprise_clicked = st.button("Surprise Me", key="surprise", help="Random topic")
with col3:
    quiz_clicked = st.button("Quiz Me", key="quizbtn", help="Take a quiz")

with col4:
    # Export button
    if st.session_state.get('last_summary'):
        export_bytes = make_docx(st.session_state['last_title'], st.session_state['last_summary'], extract_takeaways(st.session_state['last_summary']), extract_facts(st.session_state['last_summary']))
        st.markdown(download_link_bytes(export_bytes,f"{st.session_state['last_title']}.docx","Export"),unsafe_allow_html=True)

# ------------------- Generate or Surprise -------------------
essay = ""
title = ""

if generate_clicked and st.session_state.get('last_title') != "":
    keyword = st.text_input("Enter keyword", value=st.session_state['last_title'])
else:
    keyword = st.text_input("Enter keyword", "")

if generate_clicked and keyword.strip():
    title = keyword.strip()
    essay = get_summary(title)
    if essay:
        st.session_state['last_title'] = title
        st.session_state['last_summary'] = essay

if surprise_clicked:
    t,s = get_random_summary()
    if s:
        title=t
        essay=s
        st.session_state['last_title'] = title
        st.session_state['last_summary'] = essay
    else:
        st.error("Couldn't fetch random topic. Try again.")

if st.session_state.get('last_summary'):
    st.markdown(f'<div class="card"><h3>Summary: {st.session_state["last_title"]}</h3></div>', unsafe_allow_html=True)
    st.write(st.session_state['last_summary'])

    # Takeaways
    if st.button("Show Takeaways"):
        st.session_state['takeaways_visible'] = not st.session_state['takeaways_visible']
    if st.session_state['takeaways_visible']:
        takeaways = extract_takeaways(st.session_state['last_summary'], n=3)
        for t in takeaways:
            st.markdown(f'<div class="fact">{t}</div>', unsafe_allow_html=True)

    # Facts
    if st.button("Show Interesting Facts"):
        st.session_state['facts_visible'] = not st.session_state['facts_visible']
    if st.session_state['facts_visible']:
        facts = extract_facts(st.session_state['last_summary'], n=4)
        for f in facts:
            st.markdown(f'<div class="fact">{f}</div>', unsafe_allow_html=True)

# ------------------- Quiz -------------------
if quiz_clicked and st.session_state.get('last_summary'):
    st.session_state['quiz_started'] = True
    st.session_state['quiz_score'] = 0
    st.session_state['quiz_questions'] = generate_quiz_mcq(st.session_state['last_summary'], n_questions=5)
    st.session_state['user_answers'] = [""] * len(st.session_state['quiz_questions'])

if st.session_state.get('quiz_started'):
    st.markdown('<div class="card"><h3>Quiz Me</h3></div>', unsafe_allow_html=True)
    
    for idx, q in enumerate(st.session_state['quiz_questions']):
        st.markdown(f"**Q{idx+1}:** {q['question']}")
        st.session_state['user_answers'][idx] = st.radio(
            "Select answer:",
            q['options'],
            key=f"q{idx}",
            index=q['options'].index(st.session_state['user_answers'][idx]) if st.session_state['user_answers'][idx] in q['options'] else 0
        )
    
    if st.button("Submit Quiz"):
        score = 0
        for idx, q in enumerate(st.session_state['quiz_questions']):
            if st.session_state['user_answers'][idx] == q['answer']:
                score += 1
        st.session_state['quiz_score']
