import streamlit as st
import fitz
from docx import Document
import os
import tempfile
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain

# ===== File extraction functions =====
def extract_text(file_path):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext == ".pdf":
        doc = fitz.open(file_path)
        return "\n".join(page.get_text("text") for page in doc)
    elif ext == ".docx":
        doc = Document(file_path)
        text = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                text.append("\t".join(cell.text for cell in row.cells))
        return "\n".join(text)
    elif ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")

# ===== Build retriever =====
def get_file_retriever(file_path):
    text = extract_text(file_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.create_documents([text])
    embeddings = OllamaEmbeddings(model="all-minilm")
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore.as_retriever()

# ===== Streamlit UI =====
st.set_page_config(page_title="PaperTalk", page_icon="📄", layout="wide")

# Custom CSS for chat bubbles
st.markdown("""
    <style>
        .chat-bubble-user {
            background-color: #DCF8C6;
            border-radius: 12px;
            padding: 10px;
            margin: 5px 0;
            text-align: right;
        }
        .chat-bubble-bot {
            background-color: #F1F0F0;
            border-radius: 12px;
            padding: 10px;
            margin: 5px 0;
            text-align: left;
        }
        .stTextInput>div>div>input {
            border-radius: 10px;
            border: 2px solid #4CAF50;
        }
    </style>
""", unsafe_allow_html=True)

st.title("PaperTalk – Chat with Your Files")
st.markdown("Upload a **PDF/DOCX/TXT** file and start asking questions.")

uploaded_file = st.file_uploader(" Upload your file", type=["pdf", "docx", "txt", "md"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    retriever = get_file_retriever(tmp_path)
    llm = OllamaLLM(model="gemma3:1b", base_url="http://localhost:11434")
    conversation_chain = ConversationalRetrievalChain.from_llm(llm, retriever=retriever)

    if "history" not in st.session_state:
        st.session_state.history = []

    query = st.text_input("💬 Ask me anything about your file:")
    if query:
        response = conversation_chain.invoke({"question": query, "chat_history": st.session_state.history})
        st.session_state.history.append((query, response["answer"]))

    # Show conversation as chat bubbles
    for q, a in st.session_state.history:
        st.markdown(f"<div class='chat-bubble-user'> <b>You:</b> {q}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-bubble-bot'>🤖<b>PaperTalk:</b> {a}</div>", unsafe_allow_html=True)

