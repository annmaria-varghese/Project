import streamlit as st
import wikipediaapi
import spacy
import random
import requests
from io import BytesIO
from docx import Document
import base64

# ------------------- App Setup -------------------
st.set_page_config(page_title="QuickThink", layout="wide")

# ------------------- Dark Brown + Olive Green CSS -------------------
st.markdown("""
<style>
.stApp { background-color: #3b2f2f; color: #f2f0e6; font-family: "Segoe UI", sans-serif; }
.title { text-align:center; font-size:48px; font-weight:700; color:#a3b18a !important; margin-bottom:20px;}
.card { background-color: #4b3b3b; padding:20px; border-radius:12px; border-left:6px solid #a3b18a; margin-bottom:20px;}
.card h3 { color:#a3b18a !important; margin-bottom:10px;}
.fact { padding:10px 14px; margin:8px 0; background:#5a4545; border-left:4px solid #a3b18a; border-radius:6px; font-size:15px; color:#f2f0e6;}
.stButton>button { background-color:#a3b18a; color:#3b2f2f; border-radius:8px; padding:15px 25px; font-size:18px; font-weight:bold; }
.stButton>button:hover { background-color:#8fa66a; transform:translateY(-2px); }
.stTextInput>div>div>input { background-color:#5a4545; color:#f2f0e6; border-radius:6px; padding:10px; border:1px solid #8fa66a;}
</style>
""", unsafe_allow_html=True)

# ------------------- Title -------------------
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
        return None

def get_random_summary(max_sentences=10):
    url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            title = data.get("title","Random Topic")
            text = data.get("extract","")
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents]
            summary = " ".join(sents[:max_sentences]) + (" ..." if len(sents)>max_sentences else "")
            return title, summary
    except:
        return None, None

def extract_takeaways(text, n=3):
    doc = nlp(text)
    sents = [s.text.strip() for s in doc.sents if len(s.text.strip())>20]
    return sents[:n]

def extract_facts(text, n=4):
    doc = nlp(text)
    sents = [s.text.strip() for s in doc.sents if len(s.text.strip())>30]
    return random.sample(sents, min(n,len(sents))) if sents else ["No interesting facts available."]

def generate_quiz_mcq(text, n_questions=5):
    doc = nlp(text)
    candidates = list({ent.text for ent in doc.ents if len(ent.text)>2})
    candidates += [tok.text for tok in doc if tok.pos_ in ["PROPN","NOUN"] and len(tok.text)>2]
    candidates = list(set(candidates))
    questions = []
    for _ in range(n_questions):
        if not candidates: break
        answer = random.choice(candidates)
        sentence = next((s.text.strip() for s in doc.sents if answer in s.text), None)
        if not sentence:
            candidates.remove(answer)
            continue
        options = [answer] + random.sample([w for w in candidates if w != answer], min(3,len(candidates)-1))
        while len(options)<4: options.append("None of these")
        random.shuffle(options)
        questions.append({"question":sentence.replace(answer,"_____"),"answer":answer,"options":options,"explanation":f"The correct answer is '{answer}'."})
        candidates.remove(answer)
    return questions

def make_docx(title, summary, takeaways, facts):
    doc = Document()
    doc.add_heading(title,0)
    doc.add_paragraph(summary)
    doc.add_heading("Takeaways",1)
    for t in takeaways: doc.add_paragraph(t, style='List Bullet')
    doc.add_heading("Interesting Facts",1)
    for f in facts: doc.add_paragraph(f, style='List Number')
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

def download_link_bytes(data:bytes, filename:str,label:str):
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'
    return href

# ------------------- Session State -------------------
if 'last_title' not in st.session_state: st.session_state['last_title'] = ""
if 'last_summary' not in st.session_state: st.session_state['last_summary'] = ""
if 'takeaways_shown' not in st.session_state: st.session_state['takeaways_shown'] = False
if 'facts_shown' not in st.session_state: st.session_state['facts_shown'] = False
if 'quiz_started' not in st.session_state: st.session_state['quiz_started'] = False
if 'quiz_score' not in st.session_state: st.session_state['quiz_score'] = 0
if 'quiz_questions' not in st.session_state: st.session_state['quiz_questions'] = []
if 'user_answers' not in st.session_state: st.session_state['user_answers'] = []

# ------------------- Top Buttons -------------------
col1,col2,col3,col4 = st.columns([2,2,2,1])
with col1:
    if st.button("Generate", key="gen_btn"): st.session_state['action']="generate"
with col2:
    if st.button("Surprise Me", key="surp_btn"): st.session_state['action']="surprise"
with col3:
    if st.button("Quiz Me", key="quiz_btn"): st.session_state['action']="quiz"
with col4:
    if st.session_state['last_summary']:
        doc_bytes = make_docx(st.session_state['last_title'], st.session_state['last_summary'], extract_takeaways(st.session_state['last_summary']), extract_facts(st.session_state['last_summary']))
        st.markdown(download_link_bytes(doc_bytes,f"{st.session_state['last_title']}.docx","Export"), unsafe_allow_html=True)

# ------------------- Actions -------------------
action = st.session_state.get('action',"")
if action=="generate":
    keyword = st.text_input("Enter Keyword", "")
    if keyword.strip():
        summary = get_summary(keyword)
        if summary:
            st.session_state['last_title'] = keyword
            st.session_state['last_summary'] = summary
            st.session_state['takeaways_shown'] = False
            st.session_state['facts_shown'] = False
        else: st.error("Couldn't fetch content.")
elif action=="surprise":
    title, summary = get_random_summary()
    if summary:
        st.session_state['last_title'] = title
        st.session_state['last_summary'] = summary
        st.session_state['takeaways_shown'] = False
        st.session_state['facts_shown'] = False
    else:
        st.error("Couldn't fetch random topic.")
elif action=="quiz":
    if st.session_state['last_summary']:
        st.session_state['quiz_started'] = True
        st.session_state['quiz_questions'] = generate_quiz_mcq(st.session_state['last_summary'],5)
        st.session_state['user_answers'] = [""]*len(st.session_state['quiz_questions'])
        st.session_state['quiz_score'] = 0
    else:
        st.warning("Generate a topic first to start Quiz!")

# ------------------- Display Content -------------------
if st.session_state['last_summary']:
    st.markdown(f"### Summary: {st.session_state['last_title']}")
    st.write(st.session_state['last_summary'])

    if st.button("Show Takeaways"):
        st.session_state['takeaways_shown'] = not st.session_state['takeaways_shown']
    if st.session_state['takeaways_shown']:
        for t in extract_takeaways(st.session_state['last_summary']):
            st.markdown(f'<div class="fact">{t}</div>', unsafe_allow_html=True)

    if st.button("Show Interesting Facts"):
        st.session_state['facts_shown'] = not st.session_state['facts_shown']
    if st.session_state['facts_shown']:
        for f in extract_facts(st.session_state['last_summary']):
            st.markdown(f'<div class="fact">{f}</div>', unsafe_allow_html=True)

# ------------------- Quiz Section -------------------
if st.session_state['quiz_started']:
    st.markdown('<div class="card"><h3>Quiz Me</h3></div>', unsafe_allow_html=True)
    for idx,q in enumerate(st.session_state['quiz_questions']):
        st.markdown(f"**Q{idx+1}:** {q['question']}")
        st.session_state['user_answers'][idx] = st.radio("Select answer:", q['options'], key=f"q{idx}", index=q['options'].index(st.session_state['user_answers'][idx]) if st.session_state['user_answers'][idx] in q['options'] else 0)
    if st.button("Submit Quiz"):
        score=0
        for idx,q in enumerate(st.session_state['quiz_questions']):
            if st.session_state['user_answers'][idx] = st.radio(
            "Select answer:",
            q['options'],
            key=f"q{idx}",
            index=q['options'].index(st.session_state['user_answers'][idx])
            if st.session_state['user_answers'][idx] in q['options'] else 0
        )
    
    # Submit button
    if st.button("Submit Quiz"):
        score = 0
        # Check answers
        for idx, q in enumerate(st.session_state['quiz_questions']):
            if st.session_state['user_answers'][idx] == q['answer']:
                score += 1
                st.success(f"Q{idx+1}: Correct! ✅")
            else:
                st.error(f"Q{idx+1}: Wrong ❌ — {q['explanation']}")
        st.session_state['quiz_score'] = score
        st.markdown(f"**Your Total Score: {st.session_state['quiz_score']} / {len(st.session_state['quiz_questions'])}**")
        # Reset quiz after submission if you want:
        st.session_state['quiz_started'] = False

