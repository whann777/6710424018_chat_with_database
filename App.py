import streamlit as st
import pandas as pd
import google.generativeai as genai

# Setup app
st.title("📊 AI DataFrame Question Answering")
st.subheader("Upload CSV, ask a question, and get a smart answer.")

# Gemini API
gemini_api_key = st.secrets['gemini_api_key']

model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("Gemini model ready!")
    except Exception as e:
        st.error(f"Error loading Gemini: {e}")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_data_list" not in st.session_state:
    st.session_state.uploaded_data_list = []

# Chat history
for role, msg in st.session_state.chat_history:
    st.chat_message(role).markdown(msg)

# Upload multiple CSV files
st.subheader("Upload CSV")
uploaded_files = st.file_uploader("Upload CSV(s)", type=["csv"], accept_multiple_files=True)
if uploaded_files:
    st.session_state.uploaded_data_list.clear()
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            st.session_state.uploaded_data_list.append((file.name, df))
            st.success(f"{file.name} uploaded")
            st.write(f"**Preview of `{file.name}`**")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")

# Ask AI with data
if user_input := st.chat_input("Ask your question about the uploaded data..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    if model is None:
        st.warning("Gemini model not loaded. Please check API key.")
    elif not st.session_state.uploaded_data_list:
        st.warning("Please upload at least one CSV file.")
    else:
        try:
            for file_name, df in st.session_state.uploaded_data_list:
                df_name = "df"
                locals()[df_name] = df  # assign for exec()
                question = user_input
                data_dict_text = df.dtypes.astype(str).to_dict()
                example_record = df.head(2).to_dict(orient="records")

                # === STEP 1: Generate Python code ===
                code_prompt = f"""
You are a Python code generator.

Your task:
- Write Python code to answer the user question using the DataFrame named `{df_name}`.
- Assume the DataFrame is already loaded.
- Do NOT import pandas.
- If the data has a date column, convert it to datetime before filtering.
- Store the final answer in a variable named `query_result`.
- Use `exec()` when executing.

User Question:
{question}

DataFrame Schema:
{data_dict_text}

Sample Data:
{example_record}
"""
                response = model.generate_content(code_prompt)
                code_generated = response.text.replace("```python", "").replace("```", "")

                try:
                    exec(code_generated, globals(), locals())  # 🧪 execute code
                    query_result = locals().get("query_result", "No result returned.")

                    # === STEP 2: Ask Gemini to explain ===
                    explain_prompt = f"""
The user asked: {question}

Here is the result: {query_result}

Please answer the user's question clearly using this result.
"""

                    explanation_response = model.generate_content(explain_prompt)
                    final_answer = explanation_response.text

                    st.session_state.chat_history.append(("assistant", final_answer))
                    st.chat_message("assistant").markdown(final_answer)

                except Exception as e:
                    st.error(f"⚠️ Error running generated code: {e}")
                    st.code(code_generated, language="python")
        except Exception as e:
            st.error(f"Error processing the question: {e}")
