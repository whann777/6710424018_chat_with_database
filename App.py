import streamlit as st
import pandas as pd
import google.generativeai as genai

# --------------------------
# 🌐 Setup
# --------------------------
st.title("🧠 Chat + DataFrame Analysis App")
st.subheader("Upload CSV, ask questions, and get smart AI-generated answers.")

gemini_api_key = st.secrets["gemini_api_key"]

# --------------------------
# 🔑 Initialize Gemini
# --------------------------
model = None
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        st.success("Gemini API Key successfully configured.")
    except Exception as e:
        st.error(f"An error occurred while setting up the Gemini model: {e}")

# --------------------------
# 💾 Session State
# --------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_data_list" not in st.session_state:
    st.session_state.uploaded_data_list = []

# --------------------------
# 📜 Display chat history
# --------------------------
for role, message in st.session_state.chat_history:
    st.chat_message(role).markdown(message)

# --------------------------
# 📁 Upload CSV Files
# --------------------------
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

# --------------------------
# 🧠 Chat with Gemini
# --------------------------
analyze_data_checkbox = st.checkbox("Let AI analyze your data")

if user_input := st.chat_input("Type your question here..."):
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").markdown(user_input)

    try:
        if model is not None:
            if analyze_data_checkbox and st.session_state.uploaded_data_list:
                for filename, df in st.session_state.uploaded_data_list:
                    df_name = "df"
                    locals()[df_name] = df
                    question = user_input
                    data_dict_text = df.dtypes.astype(str).to_dict()
                    example_record = df.head(2).to_dict(orient="records")

                    # ----- Prompt for code generation -----
                    code_prompt = f"""
You are a helpful Python code generator.
Your goal is to write Python code snippets based on the user's question
and the provided DataFrame information.

Instructions:
- Do not import pandas.
- Use the exec() function.
- Store the result in a variable named `query_result`.
- Do not explain anything. Return only valid Python code.

User Question: {question}
DataFrame Name: {df_name}
DataFrame Schema: {data_dict_text}
Sample Data: {example_record}
"""

                    response = model.generate_content(code_prompt)
                    code_generated = response.text.replace("```python", "").replace("```", "")

                    # ✅ Run exec() safely without showing code
                    query_result = None
                    try:
                        exec(code_generated, globals(), locals())
                        query_result = locals().get("query_result", None)
                    except Exception as e:
                        if "query_result" not in locals():
                            st.warning("⚠️ Unable to generate a valid answer from your data.")

                    if query_result is not None:
                        ANSWER = query_result

                        # ----- Let Gemini explain the answer -----
                        explain_prompt = f'''
The user asked: {question}
Here is the result: {ANSWER}
Please summarize the result and answer the question directly.
'''

                        explanation_response = model.generate_content(explain_prompt)
                        bot_response = explanation_response.text

                        st.session_state.chat_history.append(("assistant", bot_response))
                        st.chat_message("assistant").markdown(bot_response)
                    else:
                        st.warning("⚠️ Code executed, but no result was returned in `query_result`.")
            else:
                # 🔁 Normal conversation
                response = model.generate_content(user_input)
                bot_response = response.text
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)

        else:
            st.warning("Please provide a valid Gemini API Key to enable responses.")
    except Exception as e:
        st.error(f"An error occurred while generating the response: {e}")


