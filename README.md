# LangChain PDF Q&A

## Features
- Load a PDF and ask natural-language questions.
- Uses LangChain with OpenAI embeddings + FAISS index.
- Interactive CLI app.

## Setup
```bash
pip install -r requirements.txt
```

Export your OpenAI API key:
- macOS/Linux: `export OPENAI_API_KEY="sk-..."`
- Windows PowerShell: `$env:OPENAI_API_KEY="sk-..."`

## Usage
1. Place your PDF in the `assets/` folder.
2. Build the index:
```bash
python main.py --pdf assets/my_notes.pdf --build
```
3. Run Q&A:
```bash
python main.py --pdf assets/my_notes.pdf
```
