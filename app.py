import streamlit as st
import wikipediaapi
import spacy
import random
from io import BytesIO
from docx import Document
import base64

# ------------------- App Setup -------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------- CSS -------------------
st.markdown("""
<style>
.stApp {background-color: #3e2f2f; color: #f0f0e6; font-family: "Segoe UI", sans-serif;}
.title {text-align: center; font-size: 50px; font-weight: 700; color: #a8b56f !important; margin-bottom: 20px; letter-spacing: -1px;}
.card {background-color: #4e3e3e; padding: 20px; border-radius: 12px; margin-bottom: 18px; border-left: 6px solid #a8b56f; box-shadow: 0 6px 18px rgba(0,0,0,0.3);}
.card h3 {color: #a8b56f !important; margin-bottom: 10px;}
.fact {padding: 10px 14px; margin: 8px 0; background: #5e4e4e; border-left: 4px solid #a8b56f; border-radius: 6px; font-size: 15px; color: #f0f0e6;}
.big-button button {background-color: #a8b56f; color: #3e2f2f; font-size: 22px; font-weight: 700; padding: 18px 30px; border-radius: 12px; margin: 5px; border: none; transition: all 0.2s;}
.big-button button:hover {background-color: #c1d27b; transform: scale(1.05);}
.stTextInput>div>div>input {background-color: #5e4e4e; color: #f0f0e6; border-radius: 6px; padding: 10px; border: 1px solid #a8b56f;}
#export-btn {position: fixed; top: 20px; right: 30px; background-color:#a8b56f; color:#3e2f2f; padding:12px 20px; border-radius:8px; font-weight:bold; font-size:16px; text-decoration:none;}
#export-btn:hover {background-color:#c1d27b; transform: scale(1.05);}
</style>
""", unsafe_allow_html=True)

# ------------------- Wikipedia & spaCy -------------------
nlp = spacy.load("en_core_web_sm")
wiki = wikipediaapi.Wikipedia(language='en', user_agent='QuickThinkApp/1.0')

# ------------------- Utilities -------------------
def get_summary(keyword, max_sentences=10):
    page = wiki.page(keyword)
    if page.exists():
        text = page.text
        sents = [s.text.strip() for s in nlp(text).sents if len(s.text.strip())>20]
        return " ".join(sents[:max_sentences]) + (" ..." if len(sents) > max_sentences else "")
    return None

def get_random_summary(max_sentences=10):
    # get all page titles (simplified random pick)
    titles = ["Artificial intelligence", "Python (programming language)", "Machine learning", "Quantum mechanics", "SpaceX", "Climate change", "Blockchain", "Neural network", "Cryptocurrency", "Galileo Galilei"]
    keyword = random.choice(titles)
    summary = get_summary(keyword, max_sentences)
    return keyword, summary

def extract_takeaways(text, n=3):
    sents = [s.text.strip() for s in nlp(text).sents if len(s.text.strip())>20]
    if not sents: return ["No takeaways."]
    return random.sample(sents,min(n,len(sents)))

def extract_facts(text,n=4):
    sents = [s.text.strip() for s in nlp(text).sents if len(s.text.strip())>25]
    if not sents: return ["No facts."]
    return random.sample(sents,min(n,len(sents)))

def generate_quiz_mcq(text,n_questions=5):
    doc = nlp(text)
    candidates = list({ent.text for ent in doc.ents if len(ent.text)>2})
    candidates += [tok.text for tok in doc if tok.pos_ in ["PROPN","NOUN"] and len(tok.text)>2]
    candidates = list(set(candidates))
    questions=[]
    for _ in range(n_questions):
        if not candidates: break
        answer=random.choice(candidates)
        sentence=None
        for s in doc.sents:
            if answer in s.text: sentence=s.text.strip(); break
        if not sentence: candidates.remove(answer); continue
        options=[answer]
        other_opts=[w for w in candidates if w!=answer]
        random.shuffle(other_opts)
        options.extend(other_opts[:3])
        while len(options)<4: options.append("None of these")
        random.shuffle(options)
        questions.append({"question":sentence.replace(answer,"_____"),"answer":answer,"options":options,"explanation":f"The correct answer is '{answer}'."})
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
    bio=BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

def get_export_link(title, summary, takeaways, facts):
    doc_bytes = make_docx(title,summary,takeaways,facts)
    b64 = base64.b64encode(doc_bytes).decode()
    return f'<a id="export-btn" href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="{title}.docx">Export</a>'

# ------------------- Session State -------------------
if 'summary' not in st.session_state: st.session_state['summary']=""
if 'title' not in st.session_state: st.session_state['title']=""
if 'takeaways' not in st.session_state: st.session_state['takeaways']=[]
if 'facts' not in st.session_state: st.session_state['facts']=[]
if 'quiz_started' not in st.session_state: st.session_state['quiz_started']=False
if 'quiz_questions' not in st.session_state: st.session_state['quiz_questions']=[]
if 'quiz_answers' not in st.session_state: st.session_state['quiz_answers']=[]

# ------------------- Header -------------------
st.markdown('<div class="title">QuickThink</div>', unsafe_allow_html=True)

# ------------------- Search Bar & Buttons -------------------
keyword = st.text_input("Enter a keyword or topic", placeholder="e.g., Artificial Intelligence")
col1,col2,col3 = st.columns([1,1,1])
with col1: generate_clicked = st.button("Generate")
with col2: surprise_clicked = st.button("Surprise Me")
with col3: quiz_clicked = st.button("Quiz Me")

# ------------------- Generate / Surprise -------------------
if generate_clicked and keyword.strip():
    summary = get_summary(keyword)
    if summary:
        st.session_state['summary']=summary
        st.session_state['title']=keyword
        st.session_state['takeaways']=extract_takeaways(summary)
        st.session_state['facts']=extract_facts(summary)
        st.session_state['quiz_started']=False
    else: st.error("Could not fetch summary for this topic.")

if surprise_clicked:
    title, summary = get_random_summary()
    if summary:
        st.session_state['summary']=summary
        st.session_state['title']=title
        st.session_state['takeaways']=extract_takeaways(summary)
        st.session_state['facts']=extract_facts(summary)
        st.session_state['quiz_started']=False
    else: st.error("Couldn't fetch random topic.")

# ------------------- Display Summary -------------------
if st.session_state['summary']:
    st.markdown(f'<div class="card"><h3>Summary - {st.session_state["title"]}</h3></div>', unsafe_allow_html=True)
    st.write(st.session_state['summary'])
    with st.expander("Takeaways"):
        for t in st.session_state['takeaways']:
            st.markdown(f'<div class="fact">{t}</div>', unsafe_allow_html=True)
    with st.expander("Interesting Facts"):
        for f in st.session_state['facts']:
            st.markdown(f'<div class="fact">{f}</div>', unsafe_allow_html=True)

# ------------------- Quiz -------------------
if quiz_clicked and st.session_state['summary']:
    st.session_state['quiz_started']=True
    st.session_state['quiz_questions']=generate_quiz_mcq(st.session_state['summary'],5)
    st.session_state['quiz_answers'] = [""]*len(st.session_state['quiz_questions'])

if st.session_state['quiz_started']:
    st.markdown('<div class="card"><h3>Quiz Me</h3></div>', unsafe_allow_html=True)
    for idx,q in enumerate(st.session_state['quiz_questions']):
        st.markdown(f"**Q{idx+1}:** {q['question']}")
        default_idx=0
        if st.session_state['quiz_answers'][idx] in q['options']:
            default_idx=q['options'].index(st.session_state['quiz_answers'][idx])
        st.session_state['quiz_answers'][idx] = st.radio("Select answer:", q['options'], index=default_idx, key=f"q{idx}")
    if st.button("Submit Quiz"):
        score=0
        for idx,q in enumerate(st.session_state['quiz_questions']):
            if st.session_state['quiz_answers'][idx]==q['answer']: score+=1
        st.markdown(f"**Your Score: {score} / {len(st.session_state['quiz_questions'])}**")
        for idx,q in enumerate(st.session_state['quiz_questions']):
            if st.session_state['quiz_answers'][idx]==q['answer']:
                st.success(f"Q{idx+1}: Correct ✅")
            else:
                st.error(f"Q{idx+1}: Wrong ❌ — {q['explanation']}")

# ------------------- Export Button -------------------
if st.session_state['summary']:
    st.markdown(get_export_link(st.session_state['title'], st.session_state['summary'], st.session_state['takeaways'], st.session_state['facts']), unsafe_allow_html=True)
