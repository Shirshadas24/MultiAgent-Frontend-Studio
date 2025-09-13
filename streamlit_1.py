

# import streamlit as st
# import os
# import shutil
# import base64
# import zipfile
# from pathlib import Path
# # Make sure your app, create_project_from_output, and parse_code are correctly imported
# from agent import app, create_project_from_output, parse_code
# from langchain_core.messages import HumanMessage, BaseMessage
# from io import BytesIO
# import re

# st.set_page_config(page_title="Agentic Frontend Developer", page_icon="🤖")

# # --- Streamlit UI Setup ---
# st.title("🤖 Agentic Frontend Developer")
# st.markdown("Your personal AI assistant for building frontend code.")

# # --- Session State Initialization ---
# if "messages" not in st.session_state:
#     st.session_state.messages = []
# if "show_preview" not in st.session_state:
#     st.session_state.show_preview = False
# if "latest_code" not in st.session_state:
#     st.session_state.latest_code = ""

# # --- Helper Functions ---
# def display_chat_messages(messages):
#     for message in messages:
#         if message["role"] == "code":
#             continue
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

# def get_latest_code_from_messages(messages):
#     for msg in reversed(messages):
#         if msg.get("role") == "code":
#             return msg["content"]
#     return ""

# def process_agent_stream(user_input, thread_id, is_feedback=False):
#     inputs = {"messages": [("user", user_input)]}
#     config = {"configurable": {"thread_id": thread_id}}
    
#     for event in app.stream(inputs, config=config):
#         for key, value in event.items():
#             if value is None:
#                 continue

#             messages = value.get("messages", [])
#             if messages:
#                 last_message = messages[-1]
                
#                 if last_message.name in ["supervisor", "enhancer", "code_developer", "validator"]:
#                     if not is_feedback:
#                         st.info(f"--- Workflow Transition: {last_message.name.upper()} ---")
                        
#                 if last_message.name == "code_developer":
#                     st.session_state.latest_code = last_message.content
#                     st.session_state.messages.append({"role": "code", "content": last_message.content})
#                     st.session_state.show_preview = True
#                     st.rerun()

#                 if "Final Code Approved!" in str(last_message.content):
#                     st.session_state.messages.append({"role": "assistant", "content": last_message.content})
#                     st.session_state.show_preview = False
#                     st.rerun()
                
#                 if key == "__end__":
#                     st.session_state.show_preview = False
#                     st.rerun()

# # --- Main Logic ---
# display_chat_messages(st.session_state.messages)

# if st.session_state.show_preview:
#     st.subheader("Frontend Preview")
    
#     html_code, css_code, js_code = parse_code(st.session_state.latest_code)
    
#     full_html = f"""
#     <style>{css_code}</style>
#     {html_code}
#     <script>{js_code}</script>
#     """
    
#     st.components.v1.html(full_html, height=500)
    
#     # user_feedback = st.text_input("Please provide feedback or type 'ok' to approve:", key="feedback_input")
#     # if user_feedback:
#     #     st.session_state.messages.append({"role": "user", "content": user_feedback})
#     #     process_agent_stream(user_feedback, "my_design_project_3", is_feedback=True)
#     #     st.rerun()
#     user_feedback = st.text_input("Please provide feedback or type 'ok' to approve:", key="feedback_input")
#     if user_feedback:
#         feedback_clean = user_feedback.strip().lower()
#         if feedback_clean in ["ok", "ok.", "yes", "looks good", "bye"]:
#         # ✅ Directly finalize here, don't send back to agent
#             final_code_content = st.session_state.latest_code
#             html_code, css_code, js_code = parse_code(final_code_content)

#             final_code_output = f"""
#         Final Code Approved!
#         Here is the complete and final code for your frontend:
#         ```html
#         {html_code}
#         ```
#         ```css
#         {css_code}
#         ```
#         ```javascript
#         {js_code}
#         ```
#         """

#             st.session_state.messages.append({"role": "assistant", "content": final_code_output})
#             st.session_state.show_preview = False
#             st.rerun()

#         else:
#         # 🚀 For real feedback, continue agent workflow
#             st.session_state.messages.append({"role": "user", "content": user_feedback})
#             process_agent_stream(user_feedback, "my_design_project_3", is_feedback=True)
#             st.rerun()


# else:
#     user_request = st.chat_input("Enter your request here")
#     if user_request:
#         st.session_state.messages.append({"role": "user", "content": user_request})
#         process_agent_stream(user_request, "my_design_project_3")
#         st.rerun()

# # --- Code Download Button ---
# if any("Final Code Approved!" in msg.get("content", "") for msg in st.session_state.messages):
#     final_code_content = get_latest_code_from_messages(st.session_state.messages)
#     if final_code_content:
#         html_code, css_code, js_code = parse_code(final_code_content)
        
#         # zip_buffer = BytesIO()
#         # with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
#         #     zipf.writestr("index.html", html_code)
#         #     zipf.writestr("style.css", css_code)
#         #     zipf.writestr("script.js", js_code)
#         # zip_buffer.seek(0)
        
#         # st.download_button(
#         #     label="Download Project Folder as .zip",
#         #     data=zip_buffer,
#         #     file_name="frontend_project.zip",
#         #     mime="application/zip",
#         # )
#         ##
#         # Download index.html
#         st.download_button(
#     label="Download index.html",
#     data=html_code,
#     file_name="index.html",
#     mime="text/html"
# )

# # Download style.css
#         st.download_button(
#     label="Download style.css",
#     data=css_code,
#     file_name="style.css",
#     mime="text/css"
# )

# # Download script.js
#         st.download_button(
#     label="Download script.js",
#     data=js_code,
#     file_name="script.js",
#     mime="application/javascript"
# )