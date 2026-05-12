""" 
LangChain Tool Calling Practice - Solutions

This file provides example solutions for the practice exercise on LangChain tool calling. 
It demonstrates how to configure the environment, load tools, run queries, and observe tool calling behavior. 
"""

# Step 1: Import required libraries
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, load_tools

# Step 2: Initialize the LLM
llm = ChatOpenAI(temperature=0)

# Step 3: Load Tools
# "llm-math" = calculator tool
# "serpapi" = search tool (requires SERPAPI_API_KEY set in environment)
tools = load_tools(["serpapi", "llm-math"], llm=llm)

# Step 4: Initialize the Agent
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# --- Task 1: Configure LangChain with model + tools ---
print("Agent initialized successfully with calculator and search tools.")

# --- Task 2: Query requiring only the calculator ---
query_calc = "What is 512/16?"
response_calc = agent.run(query_calc)
print("\nTask 2 - Calculator Query:")
print("Query:", query_calc)
print("Response:", response_calc)

# --- Task 3: Query requiring only the search tool ---
query_search = "Who is the current CEO of Microsoft?"
response_search = agent.run(query_search)
print("\nTask 3 - Search Query:")
print("Query:", query_search)
print("Response:", response_search)

# --- Task 4: Combined query requiring both tools ---
query_combined = "What is the square root of 81 plus the current US President’s first name?"
response_combined = agent.run(query_combined)
print("\nTask 4 - Combined Query:")
print("Query:", query_combined)
print("Response:", response_combined)

# --- Task 5: Reflection ---
print("""
Task 5 - Reflection:
Tool calling reduces hallucinations by letting the LLM fetch real answers instead of guessing. 
For example, math is handled by the calculator and factual updates come from the search tool.
This makes the system more reliable in real-world applications.
""")
