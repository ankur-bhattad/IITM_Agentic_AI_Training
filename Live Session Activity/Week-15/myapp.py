import os
import streamlit as st
import utils

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(
    page_title="HR Support Chatbot",
    page_icon="💼",
    layout="centered"
)

VECTOR_DB_PATH = "hr_vector_db"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

@st.cache_resource
def load_vectorstore():
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return FAISS.load_local(
        VECTOR_DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

vectorstore = load_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

@st.cache_resource
def load_llm():
    return ChatOpenAI(model=CHAT_MODEL, temperature=0)

llm = load_llm()

system_prompt = """You are an HR Support Assistant.

Use:
1. HR policy context to answer factually
2. Conversation history to understand follow-up questions

Rules:
- Answer ONLY using HR policy context
- If unsure, say: "I’m not sure based on current HR policies."
- Do NOT invent information"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------
# UI
# -----------------------------------------
st.title("💼 HR Support Chatbot (Memory Enabled)")
st.markdown(
    "Ask HR-related questions. Follow-up questions are supported."
)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------------
# CHAT INPUT
# -----------------------------------------
user_question = st.chat_input("Ask an HR-related question...")

if user_question:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_question
    })

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.spinner("Thinking..."):
        # 1. Import LangChain message types
        from langchain_core.messages import HumanMessage, AIMessage

        # 2. Convert Streamlit history dicts to LangChain Message objects
        history = st.session_state.messages[-6:]
        chat_history = []
        for m in history:
            if m["role"] == "user":
                chat_history.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                chat_history.append(AIMessage(content=m["content"]))

        # 3. Retrieve docs using current question only
        docs = retriever.invoke(user_question)
        context = "\n\n".join(doc.page_content for doc in docs)

        # DEBUG: Uncomment the line below if you want to verify your vector DB is returning data
        # st.write("Retrieved Context Length:", len(context))

        # 4. Correctly formatted system instruction string combined without python f-string conflict
        system_content = system_prompt + "\n\nHR Policy Context:\n{context}"

        # Re-build prompt structure right before parsing variables
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_content),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{question}")
        ])

        # 5. Format and invoke the LLM
        response = llm.invoke(
            prompt.format_messages(
                chat_history=chat_history,
                context=context,
                question=user_question
            )
        )

    with st.chat_message("assistant"):
        st.markdown(response.content)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response.content
    })
