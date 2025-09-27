import gradio as gr
from main import conversation_chain  # import your RAG chain from main.py

# Track conversation history
chat_history = []

def chat_with_rag(query, history):
    if not query.strip():
        return history, history
    response = conversation_chain.invoke({"question": query, "chat_history": history})
    history.append((query, response["answer"]))
    return history, history

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Ask me anything!")
    msg.submit(chat_with_rag, inputs=[msg, chatbot], outputs=[chatbot, chatbot])

# Opens browser and provides public URL
demo.launch(share=True)
