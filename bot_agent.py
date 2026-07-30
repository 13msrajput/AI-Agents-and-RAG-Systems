from typing import TypedDict, List # used for type annotations
from langchain_core.messages import HumanMessage # used to define the structure of the data
from langgraph.graph import StateGraph, START, END # used to create a state graph for the agent
from langchain_ollama import ChatOllama # used to interact with the Ollama chat model

class AgentState(TypedDict):

    """represents the state of the agent""" # Define the structure of the agent's state

    messages: List[HumanMessage] # List of messages exchanged with the user

llm = ChatOllama(model = "gemma:2b") # Initialize the chat model using ollama with the specified model

def process(state: AgentState) -> AgentState: 

    """ Process the current state and return a new state with an updated message""" # Define a function to process the agent's state

    response = llm.invoke(state["messages"]) # Get a response from the model using the current messages

    print(f"\nAI: {response.content}") # Print the AI's response

    return state # Return the updated state

graph = StateGraph(AgentState) # Create a state graph for the agent

graph.add_node("process", process) # Add the process function as a node in the graph

graph.add_edge(START, "process") # Connect the Start node to the process node

graph.add_edge("process", END) # Connect the process node to the End node

agent = graph.compile() # Compile the graph into an agent

user_input = input("Enter: ") # Get user input

while user_input != "exit": # Continue until the user types "exit"

    initial_state = {"messages": [HumanMessage(content=user_input)]} # Initialize the state with the user's message

    result = agent.invoke(initial_state) # Invoke the agent with the initial state

    user_input = input("\nEnter: ") # Get user input