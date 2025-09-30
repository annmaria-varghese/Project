import streamlit as st
import wikipediaapi
import spacy
import random
import requests
from io import BytesIO
from docx import Document

# ------------------- App Setup -------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------- CSS -------------------
st.markdown("""
<style>
.stApp { background-color: #f0f0e8; color: #2b2b2b; font-family: "Segoe UI", sans-serif; }
.title { text-align: center; font-size: 48px; font-weight: 700; color: #4a5d23 !important; margin-bottom: 20px; }
input { background-color: #fff; color: #222; border-radius: 6px; padding: 10px; border: 1px solid #aaa; width:100%; }
button { background-color:#4a5d23; color:#fff; padding:10px 20px; border:none; border-radius:6px; margin:4px; }
button:hover { background-color:#3c4d1d; cursor:pointer; }
.card { background-color:#fff; padding:20px; border-radius:12px; border-left:5px solid #4a5d23; margin:10px 0; box-shadow:0 4px 10px rgba(0,0,0,0.05);}
.fact { padding:8px 12px; margin:6px 0; background:#fbfaf6; border-left:4px solid #4a5d23; border-radius:6px; color:#222; }
</style>
""", unsafe_allow_html=True)

# ------------------- Wikipedia & spaCy -------------------
nlp = spacy.load("en_core_web_sm")
wiki = wikipediaapi.Wikipedia(language='en', user_agent='QuickThinkApp/1.0')

# ------------------- Utility Functions -------------------
def get_summary(keyword, max_sentences=10):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents]
            return " ".join(sents[:max_sentences]) + (" ..." if len(sents) > max_sentences else "")
    except:
        pass
    page = wiki.page(keyword)
    if page.exists():
        text = page.text
        doc = nlp(text)
        sents = [s.text.strip() for s in doc.sents if len(s.text.strip()) > 20]
        return " ".join(sents[:max_sentences]) + (" ..." if len(sents) > max_sentences else "")
    return None

def extract_takeaways(text, n=3):
    doc = nlp(text)
    sents = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
    return sents[:n]

def extract_fun_facts(text, n=4):
    doc = nlp(text)
    sents = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
    return random.sample(sents, min(n, len(sents))) if sents else ["No facts available."]

def generate_quiz_mcq(text, n_questions=5):
    doc = nlp(text)
    candidates = list({ent.text for ent in doc.ents if len(ent.text) > 2})
    candidates += [tok.text for tok in doc if tok.pos_ in ["PROPN", "NOUN"] and len(tok.text) > 2]
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
        other_options = [w for w in candidates if w != answer]
        random.shuffle(other_options)
        options.extend(other_options[:3])
        while len(options) < 4:
            options.append("None of these")
        random.shuffle(options)
        questions.append({"question": sentence.replace(answer, "_____"), "answer": answer, "options": options, "explanation": f"The correct answer is '{answer}'."})
        candidates.remove(answer)
    return questions

def make_docx(title, summary, takeaways, facts):
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(summary)
    doc.add_heading("Takeaways", level=2)
    for t in takeaways:
        doc.add_paragraph(t, style='List Bullet')
    doc.add_heading("Interesting Facts", level=2)
    for f in facts:
        doc.add_paragraph(f, style='List Number')
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

# ------------------- Session State -------------------
if 'takeaways_open' not in st.session_state:
    st.session_state['takeaways_open'] = False
if 'facts_open' not in st.session_state:
    st.session_state['facts_open'] = False
if 'quiz_started' not in st.session_state:
    st.session_state['quiz_started'] = False
if 'quiz_score' not in st.session_state:
    st.session_state['quiz_score'] = 0

# ------------------- UI -------------------
st.markdown('<div class="title">QuickThink</div>', unsafe_allow_html=True)

keyword = st.text_input("Enter a keyword", placeholder="e.g., Artificial Intelligence")

col1, col2, col3 = st.columns(3)
with col1:
    generate_clicked = st.button("Generate")
with col2:
    surprise_clicked = st.button("Surprise Me")
with col3:
    quiz_clicked = st.button("Quiz Me")

export_btn = st.button("Export")  # top right corner
if export_btn and st.session_state.get('last_summary'):
    summary, takeaways, facts = st.session_state['last_summary']
    docx_bytes = make_docx(st.session_state.get('last_title','QuickThink Topic'), summary, takeaways, facts)
    st.download_button("Download Document", data=docx_bytes, file_name=f"{st.session_state.get('last_title','topic')}.docx")

# ------------------- Fetch summary -------------------
if generate_clicked or surprise_clicked:
    if surprise_clicked:
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
            res = requests.get(url, timeout=6).json()
            keyword = res.get("title")
        except:
            st.error("Couldn't fetch random topic.")
    summary = get_summary(keyword)
    if not summary:
        st.error("Topic not found. Try another keyword.")
    else:
        st.session_state['last_title'] = keyword
        takeaways = extract_takeaways(summary)
        facts = extract_fun_facts(summary)
        st.session_state['last_summary'] = (summary, takeaways, facts)

# ------------------- Display Results -------------------
if st.session_state.get('last_summary'):
    summary, takeaways, facts = st.session_state['last_summary']
    st.markdown(f'<div class="card"><h3>Summary</h3>{summary}</div>', unsafe_allow_html=True)

    # Takeaways
    if st.button("Takeaways"):
        st.session_state['takeaways_open'] = not st.session_state['takeaways_open']
    if st.session_state['takeaways_open']:
        st.markdown(''.join([f'<div class="fact">{i+1}. {t}</div>' for i, t in enumerate(takeaways)]), unsafe_allow_html=True)

    # Interesting Facts
    if st.button("Interesting Facts"):
        st.session_state['facts_open'] = not st.session_state['facts_open']
    if st.session_state['facts_open']:
        st.markdown(''.join([f'<div class="fact">{i+1}. {f}</div>' for i, f in enumerate(facts)]), unsafe_allow_html=True)

# ------------------- Quiz -------------------
if quiz_clicked and st.session_state.get('last_summary'):
    st.session_state['quiz_started'] = True
    st.session_state['quiz_score'] = 0
    st.session_state['quiz_questions'] = generate_quiz_mcq(st.session_state['last_summary'][0], n_questions=5)

if st.session_state.get('quiz_started'):
    st.markdown('<div class="card"><h3>Quiz Me</h3></div>', unsafe_allow_html=True)
    score = 0
    for idx, q in enumerate(st.session_state['quiz_questions']):
        st.markdown(f"**Q{idx+1}:** {q['question']}")
        choice = st.radio("", q['options'], key=f"q{idx}")
        if st.button("Check Answer", key=f"check{idx}"):
            if choice == q['answer']:
                st.success("Correct!")
                score += 1
            else:
                st.error(f"Wrong! {q['explanation']}")
    st.markdown(f"**Your Score:** {score} / {len(st.session_state['quiz_questions'])}")
