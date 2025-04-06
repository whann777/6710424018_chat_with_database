import streamlit as st
import pandas as pd
import google.generativeai as genai
# Page config
st.set_page_config(page_title="🤖 CSV Chatbot with Gemini", layout="wide")
st.title("🤖 CSV Chatbot with Gemini")
st.write("Upload your dataset and ask questions. Gemini will answer with context awareness!")
# Load API Key & configure Gemini
try:
    key = st.secrets['gemini_api_key']
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    # Create chat session with history
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])
    # Chat role converter
    def role_to_streamlit(role: str) -> str:
        return "assistant" if role == "model" else role
except Exception as e:
    st.error(f"❌ Error initializing Gemini: {e}")
    st.stop()
# Initialize session state
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None
if "dictionary" not in st.session_state:
    st.session_state.dictionary = None
# File upload section
st.subheader("📤 Upload CSV and Optional Dictionary")
data_file = st.file_uploader("Upload Data Transaction", type=["csv"])
dict_file = st.file_uploader("Upload Data Dictionary", type=["csv", "txt"])
if data_file:
    try:
        df = pd.read_csv(data_file)
        st.session_state.dataframe = df
        st.success("✅ Data loaded")
        st.write("### Data Preview")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"❌ Error reading data file: {e}")
if dict_file:
    try:
        if dict_file.name.endswith(".csv"):
            dict_df = pd.read_csv(dict_file)
            dict_text = dict_df.to_string(index=False)
        else:
            dict_text = dict_file.read().decode("utf-8")
        st.session_state.dictionary = dict_text
        st.success("📘 Dictionary loaded")
    except Exception as e:
        st.error(f"❌ Error reading dictionary file: {e}")
# Display previous chat history from Gemini
for message in st.session_state.chat.history:
    with st.chat_message(role_to_streamlit(message.role)):
        st.markdown(message.parts[0].text)
# Chat input from user
if prompt := st.chat_input("💬 Ask me anything about your data..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    # Build context-aware system prompt
    df = st.session_state.dataframe
    dict_info = st.session_state.dictionary or "No dictionary provided."
    df_context = ""
    if df is not None:
        sample_data = df.head(3).to_string()
        stats = df.describe(include="all").to_string()
        df_context = f"""
**Data Preview:**
{sample_data}
**Statistical Summary:**
{stats}
**Data Dictionary:**
{dict_info}
"""
    system_prompt = f"""
You are a data analyst AI. Use the following data context to help answer the user's question.
{df_context}
User Question:
{prompt}
"""
    try:
        # Send system+user message to Gemini
        response = st.session_state.chat.send_message(system_prompt)
        with st.chat_message("assistant"):
            st.markdown(response.text)
    except Exception as e:
        st.error(f"❌ Error generating response: {e}")
