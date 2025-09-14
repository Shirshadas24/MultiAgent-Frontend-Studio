import streamlit as st
import os
import shutil
import base64
import zipfile
from pathlib import Path
from agent import app, create_project_from_output, parse_code,retrieve_all_threads
from langchain_core.messages import HumanMessage, BaseMessage
from io import BytesIO
import re
import uuid
import time

st.set_page_config(page_title="Agentic Frontend Developer", page_icon="🤖")

def generate_thread_name(user_question: str):
    """Generate a thread name from the first 5 words + timestamp"""
    prompt_words = user_question.lower().split()[:5]
    sanitized_words = [re.sub(r'[^a-z0-9]', '', word) for word in prompt_words]
    project_name = '_'.join([w for w in sanitized_words if w]) or "project"
    timestamp = int(time.time())
    return f"{project_name}_{timestamp}"

def add_thread(thread_name):
    """Add a new thread to session state"""
    if thread_name not in st.session_state['chat_threads']:
        st.session_state['chat_threads'][thread_name] = []

def reset_chat():
    """Reset chat and clear current thread"""
    st.session_state['thread_id'] = None
    st.session_state['messages'] = []
    st.session_state['latest_code'] = ""
    st.session_state['show_preview'] = False

def display_chat_messages(messages):
    for message in messages:
        if message["role"] == "code":
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def get_latest_code_from_messages(messages):
    for msg in reversed(messages):
        if msg.get("role") == "code":
            return msg["content"]
    return ""

def process_agent_stream(user_input, thread_name, is_feedback=False):
    inputs = {"messages": [("user", user_input)]}
    config = {"configurable": {"thread_id": thread_name}}

    for event in app.stream(inputs, config=config):
        for key, value in event.items():
            if value is None:
                continue

            messages = value.get("messages", [])
            if messages:
                last_message = messages[-1]

                if last_message.name in ["supervisor", "enhancer", "code_developer", "validator"]:
                    if not is_feedback:
                        st.info(f"--- Workflow Transition: {last_message.name.upper()} ---")

                if last_message.name == "code_developer":
                    st.session_state.latest_code = last_message.content
                    st.session_state.messages.append({"role": "code", "content": last_message.content})
                    st.session_state.show_preview = True
                    st.session_state.chat_threads[thread_name] = st.session_state.messages.copy()
                    st.rerun()

                if "Final Code Approved!" in str(last_message.content):
                    st.session_state.messages.append({"role": "assistant", "content": last_message.content})
                    st.session_state.show_preview = False
                    st.session_state.chat_threads[thread_name] = st.session_state.messages.copy()
                    st.rerun()

                if key == "__end__":
                    st.session_state.show_preview = False
                    st.session_state.chat_threads[thread_name] = st.session_state.messages.copy()
                    st.rerun()


if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_preview" not in st.session_state:
    st.session_state.show_preview = False
if "latest_code" not in st.session_state:
    st.session_state.latest_code = ""
if "chat_threads" not in st.session_state:
    st.session_state.chat_threads = {}
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
##new
if "chat_threads" not in st.session_state:
    from agent import retrieve_all_threads
    st.session_state.chat_threads = {tid: [] for tid in retrieve_all_threads()}

st.sidebar.title("📂 My Projects")

if st.sidebar.button("➕ New Project"):
    reset_chat()

# st.sidebar.header("Saved Projects")

# for tid in list(st.session_state['chat_threads'].keys())[::-1]:
#     short_name = tid.rsplit("_", 1)[0]  # show only project_name part
#     if st.sidebar.button(short_name, help=tid):  # tooltip shows full name
#         st.session_state['thread_id'] = tid
#         st.session_state['messages'] = st.session_state['chat_threads'][tid]
#         st.session_state['latest_code'] = get_latest_code_from_messages(st.session_state['messages'])
#         st.session_state['show_preview'] = False

##new
st.sidebar.header("Saved Projects")

for tid in list(st.session_state['chat_threads'].keys())[::-1]:
    if st.sidebar.button(str(tid)):
        st.session_state['thread_id'] = tid

        from agent import app
        state = app.get_state(config={"configurable": {"thread_id": tid}})
        msgs = state.values["messages"]

        temp_messages = []
        for msg in msgs:
            if isinstance(msg, HumanMessage):
                role = "user"
            else:
                role = "assistant"
            temp_messages.append({"role": role, "content": msg.content})

        st.session_state['messages'] = temp_messages
        st.session_state['latest_code'] = get_latest_code_from_messages(temp_messages)
        st.session_state['show_preview'] = False

st.title("🤖 Agentic Frontend Developer")
st.markdown("Your personal AI assistant for building frontend code.")

display_chat_messages(st.session_state.messages)

if st.session_state.show_preview:
    st.subheader("Frontend Preview")

    html_code, css_code, js_code = parse_code(st.session_state.latest_code)

    full_html = f"""
    <style>{css_code}</style>
    {html_code}
    <script>{js_code}</script>
    """

    st.components.v1.html(full_html, height=500)

    user_feedback = st.text_input("Please provide feedback or type 'ok' to approve:", key="feedback_input")
    if user_feedback:
        feedback_clean = user_feedback.strip().lower()
        if feedback_clean in ["ok", "ok.", "yes", "looks good", "bye"]:
            final_code_content = st.session_state.latest_code
            html_code, css_code, js_code = parse_code(final_code_content)

            final_code_output = f"""
            Final Code Approved!
            Here is the complete and final code for your frontend:
            ```html
            {html_code}
            ```
            ```css
            {css_code}
            ```
            ```javascript
            {js_code}
            ```
            """

            st.session_state.messages.append({"role": "assistant", "content": final_code_output})
            st.session_state.show_preview = False

            # Save into thread
            if not st.session_state.thread_id:
                st.session_state.thread_id = generate_thread_name("project")
            st.session_state.chat_threads[st.session_state.thread_id] = st.session_state.messages.copy()

            st.rerun()

        else:
            # Continue agent workflow
            st.session_state.messages.append({"role": "user", "content": user_feedback})
            if not st.session_state.thread_id:
                st.session_state.thread_id = generate_thread_name("project")
                add_thread(st.session_state.thread_id)
            process_agent_stream(user_feedback, st.session_state.thread_id, is_feedback=True)
            st.rerun()

else:
    user_request = st.chat_input("Enter your request here")
    if user_request:
        st.session_state.messages.append({"role": "user", "content": user_request})

        if not st.session_state.thread_id:
            st.session_state.thread_id = generate_thread_name(user_request)
            add_thread(st.session_state.thread_id)

        process_agent_stream(user_request, st.session_state.thread_id)
        st.rerun()


if any("Final Code Approved!" in msg.get("content", "") for msg in st.session_state.messages):
    final_code_content = get_latest_code_from_messages(st.session_state.messages)
    if final_code_content:
        html_code, css_code, js_code = parse_code(final_code_content)

        ##
        html_with_links = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Frontend Project</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    {html_code}
    <script src="script.js"></script>
</body>
</html>
"""

        st.download_button(
    label="Download index.html",
    data=html_with_links,
    file_name="index.html",
    mime="text/html"
)



        ##

        # st.download_button(
        #     label="Download index.html",
        #     data=html_code,
        #     file_name="index.html",
        #     mime="text/html"
        # )

        st.download_button(
            label="Download style.css",
            data=css_code,
            file_name="style.css",
            mime="text/css"
        )

        st.download_button(
            label="Download script.js",
            data=js_code,
            file_name="script.js",
            mime="application/javascript"
        )
