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
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

class Supervisor(BaseModel):
    next: Literal["enhancer", "code_developer"] = Field(
        description="Determines which specialist to activate next in the workflow sequence: "
                    "'enhancer' when user input requires clarification, expansion, or refinement, "
                    "'code_developer' when code writing, debugging, implementation, computation is necessary, "
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
    llm = ChatCohere(
        model="command-r-plus-08-2024",
        cohere_api_key=os.getenv("COHERE_API_KEY")
    )
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
    system_prompt = ("""
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
        Provide the complete code for HTML, CSS, and JavaScript in that specific order, ensuring each block is present and well-formatted.
        
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

def validator_node(state: MessagesState) -> Command[Literal["supervisor", "__end__"]]:
    llm_validator = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite", 
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    last_message = state["messages"][-1]
    generated_code = last_message.content
    user_question = state["messages"][0].content
    
    system_prompt = '''
    You are a code validator. Your only task is to determine if the generated code is relevant to the user's initial request.
    
    - Review the user's original request: "{user_question}".
    - Review the generated code.
    - If the generated code directly addresses the user's request, set 'next' to '__end__'.
    - If the code is completely off-topic, harmful, or fundamentally misunderstands the request, set 'next' to 'supervisor' so the request can be re-evaluated.
    - Your judgment should be based solely on relevance, not on whether the task is "beyond the scope" of a code generator.
    '''.format(user_question=user_question)
    
    messages = [
        {"role": "system", "content": system_prompt},
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
    else:
        print("--- LLM Validation successful. Workflow transitioning to END. ---")
        
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

graph = StateGraph(MessagesState)

graph.add_node("supervisor", supervisor_node)
graph.add_node("enhancer", enhancer)
graph.add_node("code_developer", code_developer)
graph.add_node("validator", validator_node)

graph.add_edge(START, "supervisor")
graph.add_edge("supervisor", "enhancer")
graph.add_edge("supervisor", "code_developer")
graph.add_edge("enhancer", "supervisor")
graph.add_edge("code_developer", "validator")
graph.add_edge("validator", "supervisor")
graph.add_edge("validator", END)

app = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)