import streamlit as st
import requests
import uuid
from streamlit.components.v1 import html
import zipfile
from io import BytesIO

st.set_page_config(page_title="Multi-Agent Frontend Dev", layout="wide")
st.title("Web Dev AI Agent with Memory")

API_URL = "http://127.0.0.1:9999"

# ---------- Session State Initialization ----------
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = None
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []
if "code" not in st.session_state:
    st.session_state["code"] = {"html": "", "css": "", "js": ""}

# ---------- Sidebar for Chat Management ----------
st.sidebar.title("Conversations")

if st.sidebar.button("New Chat", key="new_chat_button"):
    st.session_state["thread_id"] = str(uuid.uuid4())
    st.session_state["message_history"] = []
    st.session_state["code"] = {"html": "", "css": "", "js": ""}
    st.rerun()

try:
    threads = requests.get(f"{API_URL}/threads").json()["threads"]
    for t_id in sorted(threads, reverse=True):
        if st.sidebar.button(f"Thread {t_id[:8]}...", key=t_id):
            st.session_state["thread_id"] = t_id
            history_response = requests.get(f"{API_URL}/history/{t_id}").json()["history"]
            st.session_state["message_history"] = history_response
            st.session_state["code"] = {"html": "", "css": "", "js": ""}
            st.rerun()
except requests.exceptions.ConnectionError:
    st.sidebar.error("Backend not running. Please start the backend server.")

# ---------- Main UI Layout (Columns) ----------
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Chat Interface")
    for message in st.session_state["message_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_query = st.chat_input("Describe the website you want...")
    if user_query:
        st.session_state["message_history"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
        
        payload = {
            "user_query": user_query,
            "thread_id": st.session_state["thread_id"],
        }
        
        try:
            with st.spinner("Generating code..."):
                response = requests.post(f"{API_URL}/chat", json=payload).json()
            
            # --- IMPORTANT FIX ---
            if "thread_id" in response:
                st.session_state["thread_id"] = response["thread_id"]
                ai_response = response["response"]
                st.session_state["code"] = {
                    "html": response.get("html", ""),
                    "css": response.get("css", ""),
                    "js": response.get("js", ""),
                }
                st.session_state["message_history"].append({"role": "assistant", "content": ai_response})
            else:
                st.error("Received an invalid response from the backend. The agent may have encountered an error.")
                st.session_state["message_history"].append({"role": "assistant", "content": "An error occurred while generating the response. Please try again."})
            
            st.rerun()

        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the backend server. Please make sure it is running.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            st.session_state["message_history"].append({"role": "assistant", "content": "An unexpected error occurred. Please try again."})

with col2:
    st.header("Code & Live Preview")
    
    tab1, tab2, tab3 = st.tabs(["HTML", "CSS", "JavaScript"])
    with tab1:
        st.code(st.session_state["code"]["html"], language="html")
    with tab2:
        st.code(st.session_state["code"]["css"], language="css")
    with tab3:
        st.code(st.session_state["code"]["js"], language="javascript")
        
    st.subheader("Live Preview")
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            {st.session_state["code"]["css"]}
        </style>
    </head>
    <body>
        {st.session_state["code"]["html"]}
        <script>
            {st.session_state["code"]["js"]}
        </script>
    </body>
    </html>
    """
    
    html(full_html, height=500, scrolling=True)

    def create_zip_in_memory(code_dict):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_name, content in code_dict.items():
                if content:
                    zip_file.writestr(file_name, content)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    if st.session_state["code"]["html"]:
        zip_data = create_zip_in_memory({
            "index.html": st.session_state["code"]["html"],
            "style.css": st.session_state["code"]["css"],
            "script.js": st.session_state["code"]["js"],
        })
        
        st.download_button(
            label="Download Code Folder",
            data=zip_data,
            file_name="website.zip",
            mime="application/zip"
        )