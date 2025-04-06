import streamlit as st
import pandas as pd
import google.generativeai as genai

# Set up the Streamlit app layout
st.title("🧠 My Chatbot and Data Analysis App")
st.subheader("Conversation and Data Analysis")

# Capture Gemini API Key
gemini_api_key = st.secrets['gemini_api_key']

# Initialize the Gemini Model
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("Gemini API Key successfully configured.")
    except Exception as e:
        st.error(f"An error occurred while setting up the Gemini model: {e}")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_data_list" not in st.session_state:
    st.session_state.uploaded_data_list = []  # List of (filename, DataFrame)

# Display previous chat history
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# File uploader: multiple files
st.subheader("Upload CSV for Analysis")
uploaded_files = st.file_uploader("Choose CSV files", type=["csv"], accept_multiple_files=True)
if uploaded_files:
    st.session_state.uploaded_data_list.clear()  # Reset if new files uploaded
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            st.session_state.uploaded_data_list.append((file.name, df))
            st.success(f"{file.name} successfully uploaded and read.")
            st.write(f"### Preview of `{file.name}`")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")

# Checkbox: indicate if user wants AI analysis
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# Chat input
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    try:
        if model is not None:
            # AI data analysis logic
            if analyze_data_checkbox and st.session_state.uploaded_data_list:
                if "analyze" in user_input.lower() or "insight" in user_input.lower():
                    for filename, df in st.session_state.uploaded_data_list:
                        data_description = df.describe().to_string()
                        prompt = f"Analyze the following dataset `{filename}` and provide insights:\n\n{data_description}"
                        response = model.generate_content(prompt)
                        bot_response = response.text
                        st.session_state.chat_history.append(("assistant", bot_response))
                        st.chat_message("assistant").markdown(bot_response)
                else:
                    # Normal conversation
                    response = model.generate_content(user_input)
                    bot_response = response.text
                    st.session_state.chat_history.append(("assistant", bot_response))
                    st.chat_message("assistant").markdown(bot_response)
            else:
                # Normal conversation even if no data
                response = model.generate_content(user_input)
                bot_response = response.text
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
        else:
            st.warning("Please configure the Gemini API Key to enable chat responses.")
    except Exception as e:
        st.error(f"An error occurred while generating the response: {e}")
