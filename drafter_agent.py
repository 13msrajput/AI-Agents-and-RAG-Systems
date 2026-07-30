from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import (BaseMessage, HumanMessage, ToolMessage, SystemMessage)
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama

document_content = ""
class AgentState(TypedDict):

    messages: Annotated[Sequence[BaseMessage], add_messages]


@tool
def update(content: str) -> str:
    
    "Updates the document with the provided content."

    global document_content

    print("DEBUG:", content)

    cleaned_content = (

        content

        .replace("add ", "")

        .replace("Add ", "")

        .replace("now add ", "")

        .replace("Now add ", "")

        .strip()

    )

    if document_content:

        document_content += "\n" + cleaned_content

    else:

        document_content = cleaned_content

    return f"""Document updated successfully! Current content : {document_content}"""


@tool
def save(filename: str) -> str:
    
    "Save the current document to a text file and finish the process."

    global document_content

    if not filename.endswith(".txt"):

        filename += ".txt"

    try:

        with open(filename, "w", encoding="utf-8") as file:

            file.write(document_content)

        print(f"\nDocument has been saved to: {filename}")

        return f"Document saved successfully as '{filename}'."

    except Exception as e:

        return f"Error saving document: {str(e)}"


tools = [update, save]

model = ChatOllama(

    model = "llama3.2:latest",

    temperature = 0

).bind_tools(tools)


def our_agent(state: AgentState) -> AgentState:

    global document_content

    system_prompt = SystemMessage(
        
        content = f"""
        
                    You are Drafter, a helpful writing assistant.

                    Rules:
                    - Use update tool ONLY when user wants to add or modify content.
                    - Pass ONLY plain text string to update tool.
                    - NEVER create JSON or dictionaries.
                    - NEVER repeat old content.
                    - If user says "show document" or "read document", answer normally WITHOUT tools.
                    - If user wants to save, use save tool.

                    Current document:

                    {document_content}
                    """
                    
    )

    # First interaction
    if not state["messages"]:

        print("\nAI: I'm ready to help you update a document.")

        user_input = input("\nWhat would you like to create? ")

    else:

        last_message = state["messages"][-1]

        # After tool execution -> directly ask next user input
        if isinstance(last_message, ToolMessage):

            print(f"\nCurrent Document:\n{document_content}")

        user_input = input("\nWhat would you like to do with the document?")

        print(f"\nUSER: {user_input}")

    # Handle read/show directly without LLM
    if user_input.lower() in [

        "show document",

        "read document",

        "show",

        "read"

    ]:

        print(f"\nDOCUMENT CONTENT:\n\n{document_content}")

        return {"messages": list(state["messages"])}

    user_message = HumanMessage(content=user_input)

    all_messages = (

        [system_prompt]

        + list(state["messages"])

        + [user_message]

    )

    response = model.invoke(all_messages)

    if response.content:

        print(f"\nAI: {response.content}")

    if hasattr(response, "tool_calls") and response.tool_calls:

        print(

            f"\nUSING TOOLS: "

            f"{[tc['name'] for tc in response.tool_calls]}"

        )

    return {"messages": list(state["messages"]) + [user_message, response]}


def route_tools(state: AgentState):

    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:

        return "tools"

    return END


def should_continue(state: AgentState) -> str:

    last_message = state["messages"][-1]

    if (isinstance(last_message, ToolMessage) and "saved" in last_message.content.lower()):

        return "end"

    return "agent"


def print_messages(messages):

    if not messages:

        return

    for message in messages[-3:]:

        if isinstance(message, ToolMessage):

            print(f"\nTOOL RESULT: {message.content}")


graph = StateGraph(AgentState)

graph.add_node("agent", our_agent)

graph.add_node("tools", ToolNode(tools))

graph.set_entry_point("agent")

graph.add_conditional_edges(
    
    "agent",
    
    route_tools,
    
    {
        
        "tools": "tools",
        
        END: END,
        
    },
    
)

graph.add_conditional_edges(

    "tools",

    should_continue,
    
    {
        
        "agent": "agent",
        
        "end": END,
        
    }

)

app = graph.compile()


def run_document_agent():

    print("\n===== DRAFTER =====")

    state = {"messages": []}

    for step in app.stream(state, stream_mode="values"):

        if "messages" in step:

            print_messages(step["messages"])

    print("\n===== DRAFTER FINISHED =====")


if __name__ == "__main__":

    run_document_agent()