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
            st.write(f"### Preview of {file.name}")
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
                    # เตรียมข้อมูลสำหรับ prompt
                    df_name = "df"
                    locals()[df_name] = df
                    question = user_input
                    data_dict_text = df.dtypes.astype(str).to_dict()
                    example_record = df.head(2).to_dict(orient="records")

                    # ----------------------------------------
                    # 🧠 Code1: ให้ Gemini สร้างโค้ด Python
                    # ----------------------------------------
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
2. Use the exec() function to execute the generated code.
3. Do not import pandas.
4. Change date column type to datetime if needed.
5. Store the result in a variable named query_result.
"""

                    response = model.generate_content(code_prompt)
                    code_generated = response.text.replace("
python", "").replace("
", "")

                    try:
                        # 👨‍💻 Run the generated code
                        exec(code_generated, globals(), locals())
                        ANSWER = locals().get("query_result", "No result returned.")

                        # ----------------------------------------
                        # 🧠 Code2: อธิบายผลลัพธ์แบบ Insight
                        # ----------------------------------------
                        explain_prompt = f'''
The user asked: {question}
Here is the result: {ANSWER}
Please summarize the result and provide your interpretation or insight.
'''

                        explanation_response = model.generate_content(explain_prompt)
                        bot_response = explanation_response.text

                        st.session_state.chat_history.append(("assistant", bot_response))
                        st.chat_message("assistant").markdown(bot_response)

                    except Exception as e:
                        st.error(f"❌ Error executing generated code: {e}")
                        st.code(code_generated, language="python")

            else:
                # -------------------------------
                # 💬 Normal Chat (not about data)
                # -------------------------------
                response = model.generate_content(user_input)
                bot_response = response.text
                st.session_state.chat_history.append(("assistant", bot_response))
                st.chat_message("assistant").markdown(bot_response)

        else:
            st.warning("Please provide a valid Gemini API Key to enable responses.")
    except Exception as e:
        st.error(f"An error occurred while generating the response: {e}")

