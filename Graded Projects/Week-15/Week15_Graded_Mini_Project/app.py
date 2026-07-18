"""
app.py
------
E-Commerce Domain Support Assistant — a RAG-based conversational chatbot with
conversation memory, built with LangChain + OpenAI + FAISS + Streamlit.

Run with:  streamlit run app.py
Requires:  ingest.py to have been run first (so ecommerce_vector_db/ exists),
           and the OPENAI_API_KEY environment variable to be set.
"""

import os
import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# Load OPENAI_API_KEY (and any other vars) from a local .env file, if present.
load_dotenv()

st.set_page_config(
    page_title="E-Commerce Support Chatbot",
    page_icon="🛒",
    layout="centered",
)

VECTOR_DB_PATH = "ecommerce_vector_db"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
TOP_K = 4
HISTORY_TURNS = 6  # number of recent messages carried into the prompt as memory

FALLBACK_MESSAGE = "I don't have enough information in the provided documents."

# Vocareum-issued keys (starting with "voc-") are proxied through Vocareum's own
# gateway, not api.openai.com. Set OPENAI_API_BASE in .env if you're using one.
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE")


@st.cache_resource
def load_vectorstore():
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, base_url=OPENAI_API_BASE)
    return FAISS.load_local(
        VECTOR_DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )


@st.cache_resource
def load_llm():
    return ChatOpenAI(model=CHAT_MODEL, temperature=0, base_url=OPENAI_API_BASE)


vectorstore = load_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
llm = load_llm()

system_prompt = f"""You are a Domain Support Assistant for an e-commerce company.

Use:
1. The provided document context to answer factually
2. Conversation history to understand follow-up questions

Rules:
- Answer ONLY using the provided document context below
- Do NOT rely on outside knowledge or invent information not present in the context
- If the answer is not present in the context, respond exactly with:
  "{FALLBACK_MESSAGE}"
- Be clear, concise, and professional"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------
# UI
# -----------------------------------------
st.title("🛒 E-Commerce Support Chatbot (Memory Enabled)")
st.markdown(
    "Ask about returns, shipping, warranty, payments, or product care. "
    "Follow-up questions are supported."
)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------------
# CHAT INPUT
# -----------------------------------------
user_question = st.chat_input("Ask a question about your order, returns, shipping, etc...")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.spinner("Thinking..."):
        # 1) Build chat history from prior turns (Context Awareness requirement)
        history = st.session_state.messages[-HISTORY_TURNS:]
        chat_history = []
        for m in history:
            if m["role"] == "user":
                chat_history.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                chat_history.append(AIMessage(content=m["content"]))

        # 2) Retrieve relevant chunks using the current question
        docs = retriever.invoke(user_question)
        context = "\n\n".join(doc.page_content for doc in docs)

        # 3) Build the grounded, memory-aware prompt
        system_content = system_prompt + "\n\nDocument Context:\n{context}"
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_content),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{question}"),
        ])

        # 4) Invoke the LLM
        response = llm.invoke(
            prompt.format_messages(
                chat_history=chat_history,
                context=context,
                question=user_question,
            )
        )

    with st.chat_message("assistant"):
        st.markdown(response.content)

    st.session_state.messages.append({"role": "assistant", "content": response.content})
