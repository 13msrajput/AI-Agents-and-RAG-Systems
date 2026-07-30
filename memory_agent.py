from typing import TypedDict, List, Union 
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama 

class AgentState(TypedDict):

    "represents the state of the agent"

    messages: List[Union[HumanMessage, AIMessage]] # List of messages exchanged with the user and AI

llm = ChatOllama(model = "gemma:2b")

def process(state: AgentState) -> AgentState:

    """This node will solve the request you input""" 

    response = llm.invoke(state["messages"]) # Get a response from the model using the current messages

    state["messages"].append(AIMessage(content = response.content)) # Append the AI's response to the messages

    print(f"\nAI: {response.content}") # Print the AI's response

    print("\nCURRENT STATE: ", state["messages"]) # Print the current state of messages

    return state 

graph = StateGraph(AgentState)

graph.add_node("process", process) # Add the process function as a node in the graph

graph.add_edge(START, "process")

graph.add_edge("process", END) 

agent = graph.compile() 

conversation_history = [] # To store the conversation history

user_input = input("Enter: ") 

while user_input != "exit": # Continue until the user types "exit"

    conversation_history.append(HumanMessage(content = user_input)) # Append the user's message to the conversation history

    initial_state = {"messages": conversation_history} # Initialize the state with the user's message and conversation history

    result = agent.invoke(initial_state)

    conversation_history = result["messages"] # Update the conversation history with the latest messages

    user_input = input("\nEnter: ") 


with open("conversation_history.txt", "w") as file: # Save the conversation history to a file
    
    file.write("Conversation History:\n\n") # Write a header to the file

    for message in conversation_history: # Iterate through the conversation history

        if isinstance(message, HumanMessage): # If the message is from the user

            file.write(f"You: {message.content}\n") # Write the user's message to the file

        elif isinstance(message, AIMessage): # If the message is from the AI

            file.write(f"AI: {message.content}\n\n") # Write the AI's message to the file

    file.write("End of Conversation\n") # Write a footer to the file

print("Conversation history saved to conversation_history.txt") # Notify that the conversation history has been saved