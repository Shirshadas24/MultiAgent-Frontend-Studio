from typing import Annotated, Sequence, List, Literal 
from pydantic import BaseModel, Field 
from langchain_core.messages import HumanMessage
from langgraph.types import Command 
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent 
from IPython.display import Image, display 
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_cohere import ChatCohere
import os
import re
from IPython.display import HTML, display
import time
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
# Checkpointer
checkpointer = SqliteSaver(conn=conn)
load_dotenv()
llm= ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"))
class Supervisor(BaseModel):
    next: Literal["enhancer", "code_developer"] = Field(
        description="Determines which specialist to activate next in the workflow sequence: "
                    "'enhancer' when user input requires clarification, expansion, or refinement, "
                    "'code_developer' when code writing, debugging, implementation, computation is necessary, "
                    # "'code_executor' when executing the code, reporting errors and issues is required."
    )
    reason: str = Field(
        description="Detailed justification for the routing decision, explaining the rationale behind selecting the particular specialist and how this advances the task toward completion."
    )

def supervisor_node(state: MessagesState) -> Command[Literal["enhancer", "code_developer" ]]:

    system_prompt = ('''
                 
                You are a Workflow Supervisor orchestrating a team of two specialized agents: a **Prompt Enhancer** and a **Code Developer**. Your goal is to route the user's request to the most appropriate agent to ensure a smooth, efficient workflow.

**Instructions:**
- You are not given any tools. Just decide which agent to route to next.
- Analyze the user's request and the latest agent response.
- **If the request is ambiguous, vague, or incomplete**, route the task to the **Prompt Enhancer** to clarify and expand it.
- **If the request is clear, precise, and requires code development**, route the task to the **Code Developer**.
- **Always provide a concise rationale for your routing decision.**
    ''')
    
    messages = [
        {"role": "system", "content": system_prompt},  
    ] + state["messages"] 
    llm= ChatCohere(
    model="command-r-plus-08-2024",
    cohere_api_key=os.getenv("COHERE_API_KEY"))
    response = llm.with_structured_output(Supervisor).invoke(messages)

    goto = response.next
    reason = response.reason

    print(f"--- Workflow Transition: Supervisor → {goto.upper()} ---")
    
    return Command(
        update={
            "messages": [
                HumanMessage(content=reason, name="supervisor")
            ]
        },
        goto=goto,  
    )
def enhancer(state: MessagesState) -> Command[Literal["supervisor"]]:

    """
        Enhancer agent node that improves and clarifies user queries.
        Takes the original user input and transforms it into a more precise,
        actionable request before passing it to the supervisor.
    """
    system_prompt =( """
    You are a Query Refinement Specialist. Your sole task is to transform ambiguous user requests into a single, clear, and comprehensive instruction for a Code Developer.

**Responsibilities:**
- Analyze the original request for any vagueness, missing details, or assumptions.
- Make reasonable, informed assumptions to fill in any gaps and expand on underdeveloped ideas.
- Restructure the entire request into a single, precise, and actionable paragraph or list.
- **Do not ask questions. Do not provide explanations.**
- **Your entire response must be the final, refined query and nothing else.**
""")
    

    messages = [
        {"role": "system", "content": system_prompt},  
    ] + state["messages"]  

    enhanced_query = llm.invoke(messages)

    print(f"--- Workflow Transition: Prompt Enhancer → Supervisor ---")

    return Command(
        update={
            "messages": [  
                HumanMessage(
                    content=enhanced_query.content, 
                    name="enhancer"  
                )
            ]
        },
        goto="supervisor", 
    )
# Updated code_developer function
def code_developer(state: MessagesState) -> Command[Literal["validator"]]:
    """
    Code developer node that generates and debugs the code based on the query.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    system_prompt = """

        You are a highly skilled Frontend Code Developer specializing in HTML, CSS, and JavaScript.
        Your task is to generate clean, functional, and well-structured code based on the user's request.
        
        **Your Responsibilities:**
        1. Analyze the user's request, considering any enhancements or clarifications.
        2. Generate all necessary code (HTML, CSS, and JavaScript) to fulfill the request.
        3. Ensure the code is production-ready, well-formatted, and adheres to best practices.
        4. Provide the complete code for all three languages in a single, well-organized response.
        5. Do not include any text or explanations outside of the code blocks. Your entire response must be the code itself.
        Provide the complete code for HTML, CSS, and JavaScript in that specific order, ensuring each block is present and well-formatted
        
        **Example Output Format:**
        
        ```html
        <!DOCTYPE html>
        <html>
        ...
        </html>
        ```
        
        ```css
        /* CSS styles here */
        body {
          ...
        }
        ```

        ```javascript
        // JavaScript code here
        document.addEventListener('DOMContentLoaded', () => {
          ...
        });
        ```
        """
        
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]

    result = llm.invoke(messages)
    generated_content = result.content
    
    print("--- Workflow Transition: Code Developer → Validator ---")
    
    return Command(
        update={
            "messages": [ 
                HumanMessage(
                    content=generated_content,
                    name="code_developer"
                )
            ]
        },
        goto="validator", 
    )

class ValidatorLLM(BaseModel):
    next: Literal["supervisor", "__end__"] = Field(
        description="Specifies the next worker in the pipeline: 'supervisor' to continue or '__end__' to terminate."
    )
    reason: str = Field(
        description="The reason for the decision."
    )

def parse_code(content: str):
    """Parses HTML, CSS, and JS from code blocks using a more flexible regex."""
    html_code = ""
    css_code = ""
    js_code = ""

    html_match = re.search(r"```html\s*([\s\S]*?)\s*```", content)
    if html_match:
        html_code = html_match.group(1).strip()
    
    css_match = re.search(r"```css\s*([\s\S]*?)\s*```", content)
    if css_match:
        css_code = css_match.group(1).strip()

    js_match = re.search(r"```javascript\s*([\s\S]*?)\s*```", content)
    if js_match:
        js_code = js_match.group(1).strip()

    return html_code, css_code, js_code

def create_project_from_output(agent_output_content: str, folder_name: str = "project"):
    """
    Parses agent output and creates a folder containing index.html, style.css, and script.js.

    Args:
        agent_output_content (str): The string content from the agent's final output.
        folder_name (str): The name of the folder to create.
    """
    html_code, css_code, js_code = parse_code(agent_output_content)

    if not html_code and not css_code and not js_code:
        print("Error: No valid code blocks found in the agent's output. Files not created.")
        return

    try:
        os.makedirs(folder_name, exist_ok=True)
        print(f"Directory '{folder_name}' created or already exists.")
    except OSError as e:
        print(f"Error creating directory: {e}")
        return

    file_contents = {
        "index.html": html_code,
        "style.css": css_code,
        "script.js": js_code
    }

    for file_name, content in file_contents.items():
        file_path = os.path.join(folder_name, file_name)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
            print(f"File '{file_path}' created successfully.")

# --- Validator Node (Modified) ---
def validator_node(state: MessagesState) -> Command[Literal["supervisor", "__end__"]]:
    llm_validator = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite", 
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    last_message = state["messages"][-1]
    generated_code = last_message.content
    user_question = state["messages"][0].content
    
    system_prompt = '''
    Your task is to ensure the generated code is relevant to the user's initial question.
    - Review the user's original request.
    - Review the generated code.
    - If the code is completely off-topic, harmful, or fundamentally misunderstands the request, route to 'supervisor'.
    - Otherwise, route to '__end__'.
    - Accept code that is "good enough" rather than perfect, focusing on relevance.
    '''
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question},
        {"role": "assistant", "content": generated_code},
    ]

    llm_response = llm_validator.with_structured_output(ValidatorLLM).invoke(messages)
    
    goto = llm_response.next
    reason = llm_response.reason
    
    print(f"LLM Validation: {reason}")
    
    if goto == "supervisor":
        print("--- LLM Validation failed. Routing back to Supervisor for review. ---")
        return Command(
            update={"messages": [HumanMessage(content=f"LLM validation failed: {reason}", name="validator")]},
            goto="supervisor"
        )


    human_feedback_message = None
    for msg in reversed(state["messages"]):
        if msg.type == "human":
            human_feedback_message = msg
            break
            
    if human_feedback_message:
        feedback_content = human_feedback_message.content.strip().lower()
    else:
        feedback_content = ""

    # human_feedback_message = state["messages"][-1]
    # feedback_content = human_feedback_message.content.strip().lower()

    if feedback_content in ["ok", "ok.", "yes", "looks good", "bye"]:
        print("Human approval granted. Workflow transitioning to END.")
        
        final_code_output = f"""
            Final Code Approved!
            Here is the complete and final code for your frontend:
            ```html
            {parse_code(generated_code)[0]}
            ```
            ```css
            {parse_code(generated_code)[1]}
            ```
            ```javascript
            {parse_code(generated_code)[2]}
            ```
        """
        
        return Command(
            update={"messages": [HumanMessage(content=final_code_output, name="final_agent")]},
            goto=END
        )
    else:
        print("User requested changes. Routing back to supervisor.")
        feedback_message = f"The user provided the following feedback: '{feedback_content}'. The code needs to be updated to address this."
        
        return Command(
            update={"messages": [HumanMessage(content=feedback_message, name="validator")]},
            goto="supervisor"
        )
graph = StateGraph(MessagesState)

graph.add_node("supervisor", supervisor_node) 
graph.add_node("enhancer", enhancer)  

graph.add_node("code_developer", code_developer) 
graph.add_node("validator", validator_node)  

graph.add_edge(START, "supervisor")  
# 

# 
app = graph.compile(checkpointer=checkpointer)

##
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)
