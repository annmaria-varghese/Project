#!/usr/bin/env python3
import os
import sys
import argparse
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

def load_pdf_text(path):
    reader = PdfReader(path)
    pages = []
    for i, p in enumerate(reader.pages):
        text = p.extract_text()
        if text:
            pages.append(f"[Page {i+1}]\n" + text)
    return "\n\n".join(pages)

def build_index(pdf_paths, index_path="faiss_index"):
    all_texts = []
    for p in pdf_paths:
        p = os.path.abspath(p)
        if not os.path.isfile(p):
            print(f"ERROR: PDF not found: {p}")
            sys.exit(1)
        print(f"Loading {p} ...")
        all_texts.append(load_pdf_text(p))

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = []
    for t in all_texts:
        chunks.extend(splitter.split_text(t))

    print(f"[+] Split into {len(chunks)} chunks.")
    embeddings = OpenAIEmbeddings()
    print("[+] Creating FAISS index (this may take a minute)...")
    vectorstore = FAISS.from_texts(chunks, embeddings)
    vectorstore.save_local(index_path)
    print(f"[+] Saved vector index at '{index_path}'")
    return vectorstore

def load_index(index_path="faiss_index"):
    if not os.path.exists(index_path):
        return None
    embeddings = OpenAIEmbeddings()
    print(f"[+] Loading vector index from '{index_path}' ...")
    return FAISS.load_local(index_path, embeddings)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", nargs="+", required=True, help="PDF file(s) to use")
    parser.add_argument("--build", action="store_true", help="(re)build vector index from PDFs")
    parser.add_argument("--index", default="faiss_index", help="folder to save/load vector index")
    args = parser.parse_args()

    if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"].strip():
        print("ERROR: OPENAI_API_KEY not set.")
        sys.exit(1)

    vs = None
    if args.build:
        vs = build_index(args.pdf, args.index)
    else:
        vs = load_index(args.index)
        if vs is None:
            print("[!] No index found. Building index now...")
            vs = build_index(args.pdf, args.index)

    retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    llm = OpenAI(temperature=0, model_name="gpt-3.5-turbo")
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

    print("\n=== PDF Q&A Ready ===")
    print("Ask a question (type 'exit' or 'quit' to stop).")
    try:
        while True:
            q = input("\nQuestion: ").strip()
            if q.lower() in ("exit", "quit"):
                print("Goodbye — index preserved in folder:", args.index)
                break
            if q == "":
                continue
            answer = qa.run(q)
            print("\nAnswer:\n" + answer)
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye.")

if __name__ == "__main__":
    main()
