# Annotated -> provide additional context without affecting the type itself
# email = Annotated[str, "This has to be a valid email format"]
# print(email.__metadata__) # Print the metadata of the annotated type
# Sequence -> To automatically handle the state updates for sequences such as by adding new messages to a chat history
# add_message(Reducer Function) -> 1. Rule that controls how updates are combined with the existing state.
# 2. Tells us how to merge new data into the current state
# 3. Without a reducer, updates would have replaced the existing value entirely!
# Foe example: Without a reducer
# state = {"messages": ["Hi!"]}
# update = {"messages": ["Nice to meet you!"]}
# new_state = {"messages": ["Nice to meet you!]}
# With a reducer
# state = {"messages": ["Hi!"]}
# update = {"messages": ["Nice to meet you!"]}
# new_state = {"messages": ["Hi!", Nice to meet you!]}

from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage # The foundational class for all message types in langGraph
from langchain_core.messages import ToolMessage # Passes data back to LLM after it calls a tool such as the content and the tool_call_id
from langchain_core.messages import SystemMessage # Message for providing instructions to the LLM
from langgraph.graph.message import add_messages # used to add messages to the state
from langchain_core.tools import tool # Decorator to define a tool function
from langgraph.prebuilt import ToolNode # used to create a node that represents a tool
from langgraph.graph import StateGraph, END 
from langchain_ollama import ChatOllama 

class AgentState(TypedDict):
    
    messages: Annotated[Sequence[BaseMessage], add_messages]

@tool
def add(a: int, b:int):
    
    "This is an addition function"

    return a + b 

@tool
def subtract(a: int, b: int):
    
    "Subtraction function"
    
    return a - b

@tool
def multiply(a: int, b: int):
    
    "Multiplication function"
    
    return a * b

tools = [add, subtract, multiply]

model = ChatOllama(model = "llama3.2").bind_tools(tools)


def model_call(state:AgentState) -> AgentState:
    
    system_prompt = SystemMessage(
        
        content = 
        
        (
            
            "You are a tool-using assistant.\n"
            "Rules:\n"
            "1. Use tools to perform all calculations.\n"
            "2. Call only ONE tool at a time.\n"
            "3. NEVER nest tool calls.\n"
            "4. Wait for a tool result before calling another tool.\n"
            "5. Tool inputs must be integers, not objects.\n"
            "6. After finishing calculations, respond normally.\n"
                
        )
        
    )
    
    response = model.invoke([system_prompt] + state["messages"])
    
    return {"messages": [response]}


def should_continue(state: AgentState): 
    
    messages = state["messages"]
    
    last_message = messages[-1]
    
    if not last_message.tool_calls: 
        
        return "end"
    
    else:
        
        return "continue"

graph = StateGraph(AgentState)

graph.add_node("our_agent", model_call)

tool_node = ToolNode(tools = tools)

graph.add_node("tools", tool_node)

graph.set_entry_point("our_agent")

graph.add_conditional_edges(

    "our_agent",

    should_continue,

    {

        "continue": "tools",

        "end": END

    },

)

graph.add_edge("tools", "our_agent")

app = graph.compile()

def print_stream(stream):
    
    for s in stream:
        
        message = s["messages"][-1]
        
        if isinstance(message, tuple):
            
            print(message)
            
        else:
            
            message.pretty_print()

inputs = {"messages": [("user", "Add 40 + 12. And subtract 5 - 8 and then multiply the result by 6 and then subtract the result from 1000. Also tell me a joke please.")]}

print_stream(app.stream(inputs, stream_mode = "values"))