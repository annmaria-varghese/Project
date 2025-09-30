import streamlit as st
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Get Groq API key from environment (.env or Streamlit Secrets)
groq_api_key = os.getenv("GROQ_API_KEY")

# Streamlit app title
st.title("🌍 Topic Explainer (LangChain + Groq)")

# Show error if API key is missing
if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY not found! Please set it in your .env file or Streamlit Secrets.")
else:
    # Initialize LLM with supported model
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.7)

    # Prompt template
    prompt = ChatPromptTemplate.from_template(
        "Give me a short summary (3 sentences) about {topic}, "
        "then list 3 fun facts about it."
    )

    # Streamlit input
    topic = st.text_input("Enter a topic:")

    # Generate button
    if st.button("Generate") and topic.strip():
        chain = prompt | llm
        result = chain.invoke({"topic": topic})
        st.subheader("Result")
        st.write(result.content)
