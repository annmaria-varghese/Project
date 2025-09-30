import streamlit as st
import wikipediaapi
import spacy
import random
import requests
from io import BytesIO
from docx import Document

# ------------------- App Setup -------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------- Darkish + Olive-Cream CSS -------------------
st.markdown("""
<style>
body {background-color:#1f1f1f;}
.stApp {background-color:#1f1f1f; font-family:'Segoe UI', sans-serif;}
.title {text-align:center; font-size:60px; font-weight:900; color:#a2c523; margin-bottom:40px;}
.button-large {padding:25px 60px; font-size:24px; font-weight:bold; margin:15px; border-radius:15px; color:#fff; border:none; cursor:pointer; transition:0.3s;}
#generate {background-color:#a2c523;}
#generate:hover {background-color:#8bb31f; transform:scale(1.05);}
#surprise {background-color:#6b8e23;}
#surprise:hover {background-color:#5c7a1c; transform:scale(1.05);}
#quiz {background-color:#3c6e71;}
#quiz:hover {background-color:#2b5053; transform:scale(1.05);}
#export {position:fixed; top:20px; right:20px; background-color:#ff6f61; padding:15px 30px; font-weight:bold; border-radius:12px; color:#fff; border:none; cursor:pointer; transition:0.3s;}
#export:hover {background-color:#e55b50; transform:scale(1.05);}
.card {background-color:#2b2b2b; padding:25px; border-radius:20px; border-left:8px solid #a2c523; margin:20px 0; box-shadow:0 8px 25px rgba(0,0,0,0.5); color:#f0f0e8;}
.fact {padding:15px 18px; margin:10px 0; background:#3b3b3b; border-left:5px solid #a2c523; border-radius:10px; color:#f0f0e8;}
</style>
""", unsafe_allow_html=True)

# ------------------- Wikipedia & spaCy -------------------
nlp = spacy.load("en_core_web_sm")
wiki = wikipediaapi.Wikipedia(language='en', user_agent='QuickThinkApp/1.0')

# ------------------- Utility Functions -------------------
def get_summary(keyword, max_sentences=10):
    try:
        res = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}", timeout=6)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents]
            return " ".join(sents[:max_sentences]) + (" ..." if len(sents)>max_sentences else "")
    except:
        pass
    page = wiki.page(keyword)
    if page.exists():
        text = page.text
        doc = nlp(text)
        sents = [s.text.strip() for s in doc.sents if len(s.text.strip())>20]
        return " ".join(sents[:max_sentences]) + (" ..." if len(sents)>max_sentences else "")
    return None

def get_random_topic(max_sentences=10):
    try:
        res = requests.get("https://en.wikipedia.org/api/rest_v1/page/random/summary", timeout=6).json()
        title = res.get("title")
        extract = res.get("extract")
        doc = nlp(extract)
        sents = [s.text.strip() for s in doc.sents]
        summary = " ".join(sents[:max_sentences]) + (" ..." if len(sents)>max_sentences else "")
        return title, summary
    except:
        sample_list = ["Python (programming language)","Artificial intelligence","Machine learning","SpaceX","Quantum mechanics"]
        title = random.choice(sample_list)
        summary = get_summary(title)
        return title, summary

def extract_takeaways(text, n=3):
    doc = nlp(text)
    sents = [sent.text.strip() for sent in doc.sents if len(sent.text.strip())>20]
    return sents[:n]

def extract_fun_facts(text, n=4):
    doc = nlp(text)
    sents = [sent.text.strip() for sent in doc.sents if len(sent.text.strip())>20]
    return random.sample(sents, min(n,len(sents))) if sents else ["No facts available."]

def generate_quiz_mcq(text, n_questions=5):
    doc = nlp(text)
    candidates = list({ent.text for ent in doc.ents if len(ent.text)>2})
    candidates += [tok.text for tok in doc if tok.pos_ in ["PROPN","NOUN"] and len(tok.text)>2]
    candidates = list(set(candidates))
    questions=[]
    for _ in range(n_questions):
        if not candidates: break
        answer = random.choice(candidates)
        sentence = None
        for s in doc.sents:
            if answer in s.text:
                sentence=s.text.strip()
                break
        if not sentence:
            candidates.remove(answer)
            continue
        options=[answer]
        other_options=[w for w in candidates if w!=answer]
        random.shuffle(other_options)
        options.extend(other_options[:3])
        while len(options)<4: options.append("None of these")
        random.shuffle(options)
        questions.append({"question":sentence.replace(answer,"_____"), "answer":answer, "options":options, "explanation":f"The correct answer is '{answer}'."})
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
    bio=BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

# ------------------- Session State -------------------
if 'takeaways_open' not in st.session_state: st.session_state['takeaways_open']=False
if 'facts_open' not in st.session_state: st.session_state['facts_open']=False
if 'quiz_started' not in st.session_state: st.session_state['quiz_started']=False
if 'quiz_score' not in st.session_state: st.session_state['quiz_score']=0

# ------------------- Export Button -------------------
if st.button("Export", key="export_btn"):
    if st.session_state.get('last_summary'):
        summary, takeaways, facts = st.session_state['last_summary']
        docx_bytes = make_docx(st.session_state.get('last_title','QuickThink Topic'), summary, takeaways, facts)
        st.download_button("Download Document", data=docx_bytes, file_name=f"{st.session_state.get('last_title','topic')}.docx")

# ------------------- Title -------------------
st.markdown('<div class="title">QuickThink</div>', unsafe_allow_html=True)

# ------------------- Search & Buttons -------------------
keyword = st.text_input("Enter a keyword", placeholder="e.g., Artificial Intelligence", label_visibility="collapsed")
col1, col2, col3 = st.columns([1,1,1])
with col1: generate_clicked = st.button("Generate", key="gen_btn")
with col2: surprise_clicked = st.button("Surprise Me", key="surprise_btn")
with col3: quiz_clicked = st.button("Quiz Me", key="quiz_btn")

# ------------------- Generate / Surprise -------------------
if generate_clicked and keyword:
    summary = get_summary(keyword)
    title = keyword
elif surprise_clicked:
    title, summary = get_random_topic()
else:
    summary = None

if summary:
    st.session_state['last_title'] = title
    takeaways = extract_takeaways(summary)
    facts = extract_fun_facts(summary)
    st.session_state['last_summary'] = (summary, takeaways, facts)

# ------------------- Display Results -------------------
if st.session_state.get('last_summary'):
    summary, takeaways, facts = st.session_state['last_summary']
    st.markdown(f'<div class="card"><h3>Summary</h3>{summary}</div>', unsafe_allow_html=True)

    if st.button("Takeaways"):
        st.session_state['takeaways_open'] = not st.session_state['takeaways_open']
    if st.session_state['takeaways_open']:
        st.markdown(''.join([f'<div class="fact">{i+1}. {t}</div>' for i,t in enumerate(takeaways)]), unsafe_allow_html=True)

    if st.button("Interesting Facts"):
        st.session_state['facts_open'] = not st.session_state['facts_open']
    if st.session_state['facts_open']:
        st.markdown(''.join([f'<div class="fact">{i+1}. {f}</div>' for i,f in enumerate(facts)]), unsafe_allow_html=True)

# ------------------- Quiz -------------------
if quiz_clicked and st.session_state.get('last_summary'):
    st.session_state['quiz_started']=True
    st.session_state['quiz_score']=0
    st.session_state['quiz_questions']=generate_quiz_mcq(st.session_state['last_summary'][0], n_questions=5)

if st.session_state.get('quiz_started'):
    st.markdown('<div class="card"><h3>Quiz Me</h3></div>', unsafe_allow_html=True)
    score=0
    for idx,q in enumerate(st.session_state['quiz_questions']):
        st.markdown(f"**Q{idx+1}:** {q['question']}")
        choice = st.radio("", q['options'], key=f"q{idx}")
        if st.button("Check Answer", key=f"check{idx}"):
            if choice==q['answer']:
                st.success("Correct!")
                score+=1
            else:
                st.error(f"Wrong! {q['explanation']}")
    st.markdown(f"**Your Score:** {score} / {len(st.session_state['quiz_questions'])}")
