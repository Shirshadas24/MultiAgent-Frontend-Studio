from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
# Correct the import statement to include BaseMessage
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Import your agent graph and checkpointer from the main agent file
from main_agent import app, checkpointer, parse_code

app_server = FastAPI(title="Multi-Agent Frontend Dev Backend")

# API Schemas
class RequestState(BaseModel):
    user_query: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    thread_id: str
    response: str
    html: Optional[str] = None
    css: Optional[str] = None
    js: Optional[str] = None

class HistoryItem(BaseModel):
    role: str
    content: str

# Helper function to get history messages
def get_history_messages(thread_id: str) -> List[BaseMessage]:
    state = app.get_state(config={"configurable": {"thread_id": thread_id}})
    if state and "messages" in state.values:
        return state.values["messages"]
    return []

# backend.py (Updated chat_endpoint)

@app_server.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: RequestState):
    thread_id = request.thread_id or str(uuid.uuid4())
    
    input_message = HumanMessage(content=request.user_query)

    try:
        result = app.invoke(
            {"messages": [input_message]},
            config={"configurable": {"thread_id": thread_id}}
        )
    except Exception as e:
        # Catch unexpected errors from the agent and return a structured error response.
        return {
            "thread_id": thread_id,
            "response": f"An unexpected error occurred during agent execution: {str(e)}",
            "html": "",
            "css": "",
            "js": ""
        }

    final_message = result.get("messages", [])[-1]
    response_content = final_message.content
    html_code, css_code, js_code = "", "", ""
    
    # Check if the final message contains the expected code blocks
    if final_message.name == "final_agent":
        # The agent successfully reached the end and should have a final output
        html_code, css_code, js_code = parse_code(response_content)
    elif final_message.name == "code_developer":
        # Handle cases where the agent stops at the code developer step
        html_code, css_code, js_code = parse_code(response_content)
    elif final_message.name == "validator" or final_message.name == "supervisor":
        # If the workflow returned to an intermediate step, provide a non-code response.
        # This prevents the frontend from trying to parse code that doesn't exist.
        response_content = "The agent is still processing your request. Please check the logs for details."

    return {
        "thread_id": thread_id,
        "response": response_content,
        "html": html_code,
        "css": css_code,
        "js": js_code
    }

@app_server.get("/threads")
def list_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return {"threads": list(all_threads)}

@app_server.get("/history/{thread_id}")
def get_history(thread_id: str):
    messages = get_history_messages(thread_id)
    history = []
    for m in messages:
        role = "user" if isinstance(m, HumanMessage) else "assistant"
        content = m.content
        history.append({"role": role, "content": content})
    return {"thread_id": thread_id, "history": history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_server, host="127.0.0.1", port=9999)