import os
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage

load_dotenv()

class BuilderState(TypedDict):
    user_request: str
    architect_plan: str
    final_build_quote: str
    messages: List[str]

# Temperature 0.0 makes the AI completely factual and removes all guessing/hallucinations
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0)
embeddings = OllamaEmbeddings(model="nomic-embed-text")
db = Chroma(persist_directory="rag/chroma_db", embedding_function=embeddings)

def architect_node(state: BuilderState):
    print("-> Architect Agent is thinking...")
    request = state["user_request"]
    
    # Restored the rules: No specific models, Maximize Budget, Match exact Plural Categories
    prompt = f"""You are an elite PC hardware architect in Morocco. 
    Analyze this user request: '{request}'
    
    CRITICAL RULES:
    1. DO NOT name specific product models. 
    2. DO NOT specify exact core counts for CPUs or exact VRAM for GPUs. Just specify the Performance Tier (e.g., "High-End" or "Mid-Range").
    3. MAXIMIZE the budget.
    
    Output exactly one requirement for ALL 8 categories below:
    - CPUS: (Specify exact socket: AM4, AM5, or LGA1700, and tier. NO CORE COUNTS.)
    - GPUS: (Specify target tier to consume the budget. NO VRAM COUNTS.)
    - MOTHERBOARDS: (Specify the exact socket type matching the CPUS)
    - RAM: (Specify DDR4 or DDR5 to match the motherboard, and capacity)
    - STORAGE: (Specify capacity and type)
    - COOLERS: (Specify Air or AIO Liquid)
    - PSUS: (Specify minimum wattage)
    - CASES: (Specify ATX form factor)
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"architect_plan": response.content}

def procurement_node(state: BuilderState):
    print("-> Procurement Agent is mapping the database...")
    request = state["user_request"] 
    plan = state["architect_plan"]
    
    all_data = db.get(include=["documents", "metadatas"])
    
    # THE ULTIMATE FIX: Dump the entire metadata dictionary directly into the text!
    # It will look like: "[METADATA: {'source': 'data/cpus.csv', ...}] Brand: Intel..."
    context = "\n".join([
        f"[METADATA: {meta}] {doc}" 
        for meta, doc in zip(all_data['metadatas'], all_data['documents'])
    ])
    
    prompt = f"""You are the Procurement Manager fulfilling this exact user request: '{request}'

    Architect Plan:
    {plan}

    Available Inventory (EVERY ITEM IN STORE):
    {context}

    CRITICAL RULES - READ CAREFULLY:
    1. CHAIN OF THOUGHT: You MUST start your response with a <thinking> block. Step-by-step, select exactly one IN-STOCK item for ALL 8 categories. Verify CPU and Motherboard socket compatibility. Add up the prices to ensure you stay under the user's budget.
    2. FIND THE CPUS: Look at the [METADATA: ...] blocks. You will find the CPUs there (look for 'source': 'data/cpus.csv' or similar). You CANNOT leave the CPU blank.
    3. ANTI-HALLUCINATION: Copy the exact Brand and Model from the inventory text. Do not invent items.
    4. THE OUTPUT: After the </thinking> block, output ONLY the final Markdown table and the Total Cost.

    REQUIRED FORMAT:
    <thinking>
    - CPUS: Found [Brand] [Model], Socket: [Socket], Price: [Price]
    - GPUS: Found [Brand] [Model], Price: [Price]
    ...
    - Total Math: [Sum] MAD. Fits budget? [Yes/No]
    </thinking>

    | Category | Component | Price_MAD |
    |---|---|---|
    (8 rows here)

    **Total Estimated Cost:** [Sum] MAD
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_build_quote": response.content}

workflow = StateGraph(BuilderState)
workflow.add_node("architect", architect_node)
workflow.add_node("procurement", procurement_node)
workflow.add_edge(START, "architect")
workflow.add_edge("architect", "procurement")
workflow.add_edge("procurement", END)

agent_app = workflow.compile()