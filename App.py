import streamlit as st
import pandas as pd
import google.generativeai as genai
import textwrap
from IPython.display import Markdown

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
    st.session_state.uploaded_data_list.clear()
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            st.session_state.uploaded_data_list.append((file.name, df))
            st.success(f"{file.name} successfully uploaded and read.")
            st.write(f"### Preview of `{file.name}`")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")

# Checkbox
analyze_data_checkbox = st.checkbox("Analyze CSV Data with AI")

# Chat input
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    try:
        if model is not None:
            if analyze_data_checkbox and st.session_state.uploaded_data_list:
                for filename, df in st.session_state.uploaded_data_list:
                    df_name = "df"
                    locals()[df_name] = df  # dynamically assign dataframe for exec()
                    question = user_input
                    data_dict_text = df.dtypes.astype(str).to_dict()
                    example_record = df.head(2).to_dict(orient="records")

                    # ----- Code1: Create prompt to generate Python code -----
                    code_prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question
and the provided DataFrame information.

Here's the context:

**User Question:**
{question}

**DataFrame Name:**
{df_name}

**DataFrame Details:**
{data_dict_text}

**Sample Data (Top 2 Rows):**
{example_record}

**Instructions:**
1. Write Python code that addresses the user's question by querying or manipulating the DataFrame.
2. **Crucially, use the `exec()` function to execute the generated code.**
3. Do not import pandas
4. Change date column type to datetime
5. **Store the result of the executed code in a variable named `query_result`**
6. Assume the DataFrame is already loaded into a pandas DataFrame object named `{df_name}`. Do not include code to load the DataFrame.
7. Keep the generated code concise and focused on answering the question.
8. If the question requires a specific output format (e.g., a list, a single value), ensure the `query_result` variable holds that format.
"""

                    response = model.generate_content(code_prompt)
                    code_generated = response.text.replace("```python", "").replace("```", "")

                    try:
                        exec(code_generated, globals(), locals())
                        ANSWER = locals().get("query_result", "No result found.")

                        # ----- Code2: Explain the result -----
                        explain_prompt = f'''
The user asked: {question}
Here is the result: {ANSWER}
Please summarize the result and provide your interpretation of the customer's persona or data insight.
'''

                        explanation_response = model.generate_content(explain_prompt)
                        bot_response = explanation_response.text

                        # Store and show
                        st.session_state.chat_history.append(("assistant", bot_response))
                        st.chat_message("assistant").markdown(bot_response)

                    except Exception as e:
                        st.error(f"❌ Error while executing code: {e}")
                        st.code(code_generated, language='python')
            else:
                # Regular chat if not analyzing data
                response = model.generate_content(user_input)
                bot_response = response.text
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)
        else:
            st.warning("Please configure the Gemini API Key to enable chat responses.")
    except Exception as e:
        st.error(f"An error occurred while generating the response: {e}")
