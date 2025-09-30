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

# ------------------- CSS Styling -------------------
st.markdown("""
<style>
.stApp { background-color: #f7f6f1; color: #2b2b2b; font-family: "Segoe UI", sans-serif; }
.title { text-align: center; font-size: 48px; font-weight: 700; color: #3c5a3c !important; margin-bottom: 15px; }
.search-bar { display: flex; justify-content: center; margin-bottom: 20px; }
.buttons { display: flex; justify-content: center; gap: 15px; margin-bottom: 25px; }
.stButton>button { background-color: #4a5d23; color: #fff; border-radius: 6px; padding: 10px 18px; border: none; font-weight: 600; }
.stButton>button:hover { background-color: #3c4d1d; transform: translateY(-2px); }
.card { background-color: #fff; padding: 18px; border-radius: 12px; border-left: 6px solid #4a5d23; margin-bottom: 18px; box-shadow: 0 6px 18px rgba(0,0,0,0.06);}
.card h3 { color: #4a5d23 !important; margin-bottom: 8px; }
.fact { padding: 10px 14px; margin: 8px 0; background: #fbfaf6; border-left: 4px solid #4a5d23; border-radius: 6px; font-size: 15px; color: #222; }
.stTextInput>div>div>input { background-color: #fff; color: #222; border-radius: 6px; padding: 10px; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# ------------------- Wikipedia & spaCy -------------------
nlp = spacy.load("en_core_web_sm")
wiki = wikipediaapi.Wikipedia(language='en', user_agent='QuickThinkApp/1.0')

# ------------------- Utilities -------------------
def get_online_summary(keyword, max_sentences=10):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{keyword}"
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            text = res.json().get("extract", "")
            doc = nlp(text)
            sents = [s.text.strip() for s in doc.sents]
            return " ".join(sents[:max_sentences]) + (" ..." if len(sents) > max_sentences else "")
    except:
        return None

def get_offline_summary(keyword, max_sentences=10):
    page = wiki.page(keyword)
    if page.exists():
        text = page.text
        doc = nlp(text)
        sents = [s.text.strip() for s in doc.sents if len(s.text.strip())>20]
        return " ".join(sents[:max_sentences]) + (" ..." if len(sents) > max_sentences else "")
    return None

def get_random_summary(max_sentences=10):
    url = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            title = data.get("title", "Random Topic")
            extract = data.get("extract", "")
            doc = nlp(extract)
            sents = [s.text.strip() for s in doc.sents]
            summary = " ".join(sents[:max_sentences]) + (" ..." if len(sents) > max_sentences else "")
            return title, summary
    except:
        return None, None

def extract_key_takeaways(text, n=3):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip())>20]
    return sentences[:n] if sentences else ["No takeaways available."]

def extract_fun_facts(text, n=4):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip())>30]
    return random.sample(sentences, min(n,len(sentences))) if sentences else ["No interesting facts available."]

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

def download_button_bytes(data: bytes, filename: str, label: str, mime: str):
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:{mime};base64,{b64}" download="{filename}">{label}</a>'
    return href

def generate_quiz_mcq(text, n_questions=5):
    doc = nlp(text)
    candidates = list({ent.text for ent in doc.ents if len(ent.text)>2})
    candidates += [tok.text for tok in doc if tok.pos_ in ["PROPN","NOUN"] and len(tok.text)>2]
    candidates = list(set(candidates))
    questions=[]
    for _ in range(n_questions):
        if not candidates:
            break
        answer = random.choice(candidates)
        sentence=None
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
        while len(options)<4:
            options.append("None of these")
        random.shuffle(options)
        questions.append({
            "question": sentence.replace(answer,"_____"),
            "answer": answer,
            "options": options,
            "explanation": f"The correct answer is '{answer}'."
        })
        candidates.remove(answer)
    return questions

# ------------------- Main UI -------------------
st.markdown('<div class="card"><h3>QuickThink Features</h3>'
            '<ul>'
            '<li>Concise Summaries</li>'
            '<li>Interactive Takeaways & Facts</li>'
            '<li>Surprise Me random topics</li>'
            '<li>Quiz Me (5 Questions)</li>'
            '</ul></div>', unsafe_allow_html=True)

# Search Bar
keyword = st.text_input("Enter a keyword or topic", placeholder="e.g., Artificial Intelligence")

# Centered Buttons
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("Generate"):
        action = "generate"
with col2:
    if st.button("Surprise Me"):
        action = "surprise"
with col3:
    if st.button("Quiz Me"):
        action = "quiz"

st.write("")  # spacing

# Export button top-right
st.markdown("""
<div style="position:fixed; top:20px; right:20px; z-index:999;">
""", unsafe_allow_html=True)
# placeholder for export button if essay exists later

# ------------------- Fetch / Display -------------------
essay=""
title=""
takeaways=[]
facts=[]
questions=[]

if 'action' in locals():
    if action=="generate":
        if keyword.strip()=="":
            st.warning("Enter a keyword!")
        else:
            essay=get_online_summary(keyword,10)
            if not essay:
                essay=get_offline_summary(keyword,10)
            title=keyword
    elif action=="surprise":
        title, essay=get_random_summary(10)
        if not essay:
            st.error("Couldn't fetch random topic.")
    elif action=="quiz":
        if keyword.strip()=="":
            st.warning("Enter a keyword for quiz!")
        else:
            essay=get_online_summary(keyword,10)
            if not essay:
                essay=get_offline_summary(keyword,10)
            title=keyword
            questions=generate_quiz_mcq(essay,5)

# ------------------- Display Content -------------------
if essay:
    # Export button
    docx_bytes = make_docx(title, essay, extract_key_takeaways(essay,3), extract_fun_facts(essay,4))
    href_docx = download_button_bytes(docx_bytes,f"{title}.docx","Export","application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.markdown(f'<div style="position:fixed; top:20px; right:20px; z-index:999;">{href_docx}</div>', unsafe_allow_html=True)

    # Takeaways toggle
    st.markdown('<div class="card"><h3 style="cursor:pointer" onclick="document.getElementById(\'take\').style.display=\'block\'">Takeaways</h3>'
                '<div id="take" style="display:none;">'+
                ''.join([f'<div class="fact">• {t}</div>' for t in extract_key_takeaways(essay,3)])+
                '</div></div>', unsafe_allow_html=True)

    # Interesting Facts toggle
    st.markdown('<div class="card"><h3 style="cursor:pointer" onclick="document.getElementById(\'facts\').style.display=\'block\'">Interesting Facts</h3>'
                '<div id="facts" style="display:none;">'+
                ''.join([f'<div class="fact">{i+1}. {f}</div>' for i,f in]()
