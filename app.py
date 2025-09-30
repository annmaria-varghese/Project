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
/* App background and font */
.stApp {background-color: #3e2f2f; color: #f0f0e6; font-family: "Segoe UI", sans-serif;}

/* Title */
.title {text-align: center; font-size: 50px; font-weight: 700; color: #a8b56f !important; margin-bottom: 20px; letter-spacing: -1px;}

/* Cards */
.card {background-color: #4e3e3e; padding: 20px; border-radius: 12px; margin-bottom: 18px; border-left: 6px solid #a8b56f; box-shadow: 0 6px 18px rgba(0,0,0,0.3);}
.card h3 {color: #a8b56f !important; margin-bottom: 10px;}

/* Facts and takeaways */
.fact {padding: 10px 14px; margin: 8px 0; background: #5e4e4e; border-left: 4px solid #a8b56f; border-radius: 6px; font-size: 15px; color: #f0f0e6;}

/* Buttons */
.big-button button {background-color: #a8b56f; color: #3e2f2f; font-size: 18px; font-weight: 700; padding: 14px 28px; border-radius: 10px; margin: 5px; border: none; transition: all 0.2s;}
.big-button button:hover {background-color: #c1d27b; transform: scale(1.05);}

/* Input box */
.stTextInput>div>div>input {background-color: #5e4e4e; color: #f0f0e6; border-radius: 6px; padding: 10px; border: 1px solid #a8b56f;}
</style>
""", unsafe_allow_html=True)

# ------------------- Wikipedia & spaCy -------------------
nlp = spacy.load("en_core_web_sm")
wiki = wikipediaapi.Wikipedia(language='en', user_agent='QuickThinkApp/1.0')

# ------------------- Utilities -------------------
def get_summary(keyword, max_sentences=10):
    """Try online, fallback offline"""
    # Online
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            sents = [s.text.strip() for s in nlp(text).sents]
            return " ".join(sents[:max_sentences]) + (" ..." if len(sents) > max_sentences else "")
    except:
        pass
    # Offline fallback
    page = wiki.page(keyword)
    if page.exists():
        text = page.text
        sents = [s.text.strip() for s in nlp(text).sents if len(s.text.strip())>20]
        return " ".join(sents[:max_sentences]) + (" ..." if len(sents) > max_sentences else "")
    return None

def get_random_summary(max_sentences=10):
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            title = data.get("title","Random Topic")
            text = data.get("extract","")
            sents = [s.text.strip() for s in nlp(text).sents]
            summary = " ".join(sents[:max_sentences]) + (" ..." if len(sents)>max_sentences else "")
            return title, summary
    except:
        pass
    return None, None

def extract_takeaways(text, n=3):
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if len(s.text.strip())>20]
    if not sentences: return ["No takeaways available."]
    return random.sample(sentences, min(n,len(sentences)))

def extract_facts(text, n=4):
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if len(s.text.strip())>25]
    if not sentences: return ["No facts available."]
    return random.sample(sentences, min(n,len(sentences)))

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
            if answer in s.text: sentence=s.text.strip(); break
        if not sentence: candidates.remove(answer); continue
        options = [answer]
        other_opts = [w for w in candidates if w!=answer]
        random.shuffle(other_opts)
        options.extend(other_opts[:3])
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
    doc.add_heading(title,level=1)
    doc.add_paragraph(summary)
    doc.add_heading("Takeaways",level=2)
    for t in takeaways: doc.add_paragraph(t,style='List Bullet')
    doc.add_heading("Interesting Facts",level=2)
    for f in facts: doc.add_paragraph(f,style='List Number')
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

def download_docx(title, summary, takeaways, facts):
    doc_bytes = make_docx(title,summary,takeaways,facts)
    b64 = base64.b64encode(doc_bytes).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{title}.docx">Export</a>'
    return href

# ------------------- State Initialization -------------------
if 'summary' not in st.session_state: st.session_state['summary'] = ""
if 'title' not in st.session_state: st.session_state['title'] = ""
if 'takeaways' not in st.session_state: st.session_state['takeaways'] = []
if 'facts' not in st.session_state: st.session_state['facts'] = []
if 'quiz_questions' not in st.session_state: st.session_state['quiz_questions'] = []
if 'quiz_answers' not in st.session_state: st.session_state['quiz_answers'] = []
if 'quiz_started' not in st.session_state: st.session_state['quiz_started'] = False

# ------------------- Header -------------------
st.markdown('<div class="title">QuickThink</div>', unsafe_allow_html=True)

# ------------------- Search Bar & Buttons -------------------
keyword = st.text_input("Enter a keyword or topic", placeholder="e.g., Artificial Intelligence")

col1, col2, col3, col4 = st.columns([1,1,1,1])
with col1:
    generate_clicked = st.button("Generate")
with col2:
    surprise_clicked = st.button("Surprise Me")
with col3:
    quiz_clicked = st.button("Quiz Me")
with col4:
    if st.session_state['summary']:
        st.markdown(download_docx(st.session_state['title'], st.session_state['summary'], st.session_state['takeaways'], st.session_state['facts']), unsafe_allow_html=True)

# ------------------- Generate / Surprise -------------------
if generate_clicked and keyword.strip():
    summary = get_summary(keyword, max_sentences=10)
    if summary:
        st.session_state['summary'] = summary
        st.session_state['title'] = keyword
        st.session_state['takeaways'] = extract_takeaways(summary,3)
        st.session_state['facts'] = extract_facts(summary,4)
        st.session_state['quiz_started'] = False
    else:
        st.error("Could not fetch summary for this topic.")
elif surprise_clicked:
    title, summary = get_random_summary(max_sentences=10)
    if summary:
        st.session_state['summary'] = summary
        st.session_state['title'] = title
        st.session_state['takeaways'] = extract_takeaways(summary,3)
        st.session_state['facts'] = extract_facts(summary,4)
        st.session_state['quiz_started'] = False
    else:
        st.error("Couldn't fetch random topic.")

# ------------------- Display Summary -------------------
if st.session_state['summary']:
    st.markdown(f'<div class="card"><h3>Summary - {st.session_state["title"]}</h3></div>', unsafe_allow_html=True)
    st.write(st.session_state['summary'])

    # Takeaways collapsible
    with st.expander("Takeaways"):
        for t in st.session_state['takeaways']:
            st.markdown(f'<div class="fact">{t}</div>', unsafe_allow_html=True)
    # Interesting Facts collapsible
    with st.expander("Interesting Facts"):
        for f in st.session_state['facts']:
            st.markdown(f'<div class="fact">{f}</div>', unsafe_allow_html=True)

# ------------------- Quiz -------------------
if quiz_clicked and st.session_state['summary']:
    st.session_state['quiz_started'] = True
    st.session_state['quiz_questions'] = generate_quiz_mcq(st.session_state['summary'],5)
    st.session_state['quiz_answers'] = [""]*len(st.session_state['quiz_questions'])

if st.session_state['quiz_started']:
    st.markdown('<div class="card"><h3>Quiz Me</h3></div>', unsafe_allow_html=True)
    for idx,q in enumerate(st.session_state['quiz_questions']):
        st.markdown(f"**Q{idx+1}:** {q['question']}")
        default_index = 0
        if st.session_state['quiz_answers'][idx] in q['options']:
            default_index = q['options'].index(st.session_state['quiz_answers'][idx])
        st.session_state['quiz_answers'][idx] = st.radio("Select answer:", q['options'], index=default_index, key=f"q{idx}")

    if st.button("Submit Quiz"):
        score = 0
        for idx,q in enumerate(st.session_state['quiz_questions']):
            if st.session_state['quiz_answers'][idx]==q['answer']:
                score+=1
        st.markdown(f"**Your Score: {score} / {len(st.session_state['quiz_questions'])}**")
        for idx,q in enumerate(st.session_state['quiz_questions']):
            if st.session_state['quiz_answers'][idx]==q['answer']:
                st.success(f"Q{idx+1}: Correct ✅")
            else:
                st.error(f"Q{idx+1}: Wrong ❌ — {q['explanation']}")
