"""
Agent Node Implementations
Individual agent functions for the multi-agent PC builder system
"""

import re
import os
import pandas as pd
import random
from typing import Dict, Any, List
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# Initialize RAG components
embeddings = OllamaEmbeddings(model="nomic-embed-text")
db = Chroma(persist_directory="rag/chroma_db", embedding_function=embeddings)

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

class ArchitectAgent:
    """
    Architect Agent: Analyzes user requirements and extracts key parameters.
    
    Responsibilities:
    - Parse user requests for budget and requirements
    - Identify use case (gaming, work, AI/ML, etc.)
    - Extract performance requirements
    - Prepare structured plan for procurement
    """
    
    @staticmethod
    def process_request(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user request and extract structured requirements using Groq LLM.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with architect analysis
        """
        print("🏗️ Architect Agent: Analyzing user requirements with Groq LLM...")
        request = state.get("user_request", "")
        
        # Use Groq LLM to analyze the request
        prompt = f"""You are a PC hardware architect. Analyze this customer request and extract:
1. Budget (in MAD - Moroccan Dirhams)
2. Use case (gaming, office, ai_ml, content_creation, development, or general)
3. Performance level (basic, medium, or high)

Customer Request: {request}

Respond in this EXACT format:
BUDGET: [number only]
USE_CASE: [one word from the list above]
PERFORMANCE: [basic, medium, or high]
"""
        
        try:
            response = llm.invoke(prompt)
            analysis = response.content
            
            # Parse LLM response
            budget = ArchitectAgent._parse_budget_from_llm(analysis)
            use_case = ArchitectAgent._parse_use_case_from_llm(analysis)
            performance_level = ArchitectAgent._parse_performance_from_llm(analysis)
            
            print(f"💰 Budget identified by LLM: {budget:,} MAD")
            print(f"🎯 Use case identified by LLM: {use_case}")
            print(f"⚡ Performance level: {performance_level}")
            
        except Exception as e:
            print(f"⚠️ Groq API error, using fallback: {e}")
            # Fallback to regex-based extraction
            budget = ArchitectAgent._extract_budget(request)
            use_case = ArchitectAgent._identify_use_case(request)
            performance_level = ArchitectAgent._extract_performance_level(request)
            
            print(f"💰 Budget identified (fallback): {budget:,} MAD")
            print(f"🎯 Use case identified (fallback): {use_case}")
            print(f"⚡ Performance level (fallback): {performance_level}")
        
        return {
            "architect_plan": str(budget),
            "use_case": use_case,
            "budget": budget,
            "performance_level": performance_level,
            "requirements_analysis": {
                "budget": budget,
                "use_case": use_case,
                "performance_level": performance_level,
                "original_request": request
            }
        }
    
    @staticmethod
    def _parse_budget_from_llm(response: str) -> int:
        """Parse budget from LLM response"""
        match = re.search(r'BUDGET:\s*(\d+)', response, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Fallback to any number in the response
        match = re.search(r'(\d{3,})', response)
        return int(match.group(1)) if match else 15000
    
    @staticmethod
    def _parse_use_case_from_llm(response: str) -> str:
        """Parse use case from LLM response"""
        match = re.search(r'USE_CASE:\s*(\w+)', response, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return "general"
    
    @staticmethod
    def _parse_performance_from_llm(response: str) -> str:
        """Parse performance level from LLM response"""
        match = re.search(r'PERFORMANCE:\s*(\w+)', response, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return "medium"
    
    @staticmethod
    def _extract_budget(request: str) -> int:
        """Extract budget from user request."""
        # Look for budget patterns
        patterns = [
            r'budget[:\s]*(\d{3,})\s*(?:MAD|mad|Mad|dirhams|dh)?',
            r'(\d{3,})\s*(?:MAD|mad|Mad|dirhams|dh)\s*budget',
            r'(\d{3,})\s*(?:MAD|mad|Mad|dirhams|dh)',
            r'around\s*(\d{3,})',
            r'maximum\s*(\d{3,})',
            r'up\s*to\s*(\d{3,})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Default budget if none specified
        return 15000
    
    @staticmethod
    def _identify_use_case(request: str) -> str:
        """Identify primary use case from request."""
        request_lower = request.lower()
        
        # Gaming keywords
        if any(word in request_lower for word in ["gaming", "game", "gamer", "fps", "4k gaming", "1080p", "1440p"]):
            return "gaming"
        
        # Work/Office keywords
        elif any(word in request_lower for word in ["work", "office", "business", "productivity", "documents"]):
            return "office"
        
        # AI/ML keywords
        elif any(word in request_lower for word in ["ai", "ml", "machine learning", "deep learning", "training", "neural"]):
            return "ai_ml"
        
        # Content creation keywords
        elif any(word in request_lower for word in ["streaming", "content", "video editing", "rendering", "creator"]):
            return "content_creation"
        
        # Development keywords
        elif any(word in request_lower for word in ["programming", "development", "coding", "software"]):
            return "development"
        
        # Default
        else:
            return "general"
    
    @staticmethod
    def _extract_performance_level(request: str) -> str:
        """Extract performance requirements from request."""
        request_lower = request.lower()
        
        # High performance indicators
        if any(word in request_lower for word in ["high-end", "powerful", "extreme", "4k", "ultra", "maximum"]):
            return "high"
        
        # Medium performance indicators
        elif any(word in request_lower for word in ["medium", "good", "decent", "1440p", "streaming"]):
            return "medium"
        
        # Budget/basic indicators
        elif any(word in request_lower for word in ["budget", "basic", "cheap", "simple", "light", "1080p"]):
            return "basic"
        
        # Default to medium
        else:
            return "medium"

class ProcurementAgent:
    """
    Procurement Agent: Selects optimal PC components using RAG and compatibility logic.
    
    Responsibilities:
    - Query RAG database for component information
    - Ensure hardware compatibility
    - Optimize for budget constraints
    - Generate formatted build quote
    """
    
    @staticmethod
    def select_components(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select optimal PC components based on requirements using Groq LLM + RAG.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with component selection
        """
        print("🛒 Procurement Agent: Selecting optimal components with Groq LLM...")
        
        # Extract requirements
        budget = int(state.get("architect_plan", "15000"))
        use_case = state.get("use_case", "general")
        performance_level = state.get("performance_level", "medium")
        
        print(f"📋 Requirements: Budget={budget:,} MAD, Use Case={use_case}, Performance={performance_level}")
        
        # Query RAG database
        rag_context = ProcurementAgent._query_rag_database(budget, use_case)
        
        # Load component databases
        component_dbs = ProcurementAgent._load_component_databases()
        
        # Use Groq LLM to help with component selection strategy
        try:
            strategy_prompt = f"""You are a PC hardware expert. Given these requirements:
- Budget: {budget} MAD
- Use Case: {use_case}
- Performance Level: {performance_level}

Provide a brief strategy (2-3 sentences) for component selection priorities.
Focus on: What components should get more budget allocation? Any specific compatibility concerns?"""

            response = llm.invoke(strategy_prompt)
            strategy = response.content
            print(f"🧠 LLM Strategy: {strategy[:150]}...")
            
        except Exception as e:
            print(f"⚠️ Groq API error for strategy, continuing: {e}")
            strategy = "Balance performance across all components with focus on use case requirements."
        
        # Select optimal build (using the existing algorithm)
        best_build = ProcurementAgent._optimize_component_selection(
            budget, use_case, performance_level, component_dbs
        )
        
        if not best_build:
            return {"final_build_quote": "❌ Could not find a compatible build within the specified budget."}
        
        # Generate build quote with LLM enhancement
        build_quote = ProcurementAgent._generate_build_quote_with_llm(
            best_build, budget, use_case, strategy
        )
        
        return {
            "final_build_quote": build_quote,
            "selected_components": best_build,
            "total_price": sum(item['Price_MAD'] for item in best_build.values()),
            "llm_strategy": strategy
        }
    
    @staticmethod
    def _query_rag_database(budget: int, use_case: str) -> List[str]:
        """Query RAG database for relevant component information."""
        categories = ["CPUS", "GPUS", "MOTHERBOARDS", "RAM", "STORAGE", "COOLERS", "PSUS", "CASES"]
        context = []
        
        print("💾 Querying RAG database...")
        
        for category in categories:
            try:
                query = f"budget {budget} {use_case} {category}"
                results = db.as_retriever(
                    search_kwargs={"k": 2, "filter": {"category": category}}
                ).invoke(query)
                
                for doc in results:
                    context.append(f"[{category}] {doc.page_content}")
                    
            except Exception as e:
                print(f"⚠️ RAG query failed for {category}: {e}")
        
        print(f"📊 Retrieved {len(context)} component entries from RAG")
        return context
    
    @staticmethod
    def _load_component_databases() -> Dict[str, List[Dict]]:
        """Load and filter component databases."""
        print("📦 Loading component databases...")
        
        component_files = {
            'cpus': 'data/cpus.csv',
            'gpus': 'data/gpus.csv',
            'motherboards': 'data/motherboards.csv',
            'ram': 'data/ram.csv',
            'storage': 'data/storage.csv',
            'coolers': 'data/coolers.csv',
            'psus': 'data/psus.csv',
            'cases': 'data/cases.csv'
        }
        
        databases = {}
        
        for component_type, file_path in component_files.items():
            try:
                df = pd.read_csv(file_path)
                
                # Filter out unavailable components
                original_count = len(df)
                df = df[df['Availability'] != 'Out of Stock']
                available_count = len(df)
                
                print(f"  {component_type.upper()}: {available_count}/{original_count} available")
                
                databases[component_type] = df.to_dict('records')
                
            except Exception as e:
                print(f"❌ Failed to load {component_type}: {e}")
                databases[component_type] = []
        
        return databases
    
    @staticmethod
    def _optimize_component_selection(
        budget: int, 
        use_case: str, 
        performance_level: str, 
        databases: Dict[str, List[Dict]]
    ) -> Dict[str, Dict]:
        """Optimize component selection with compatibility checking."""
        print("🎯 Optimizing component selection...")
        
        best_build = None
        best_price = 0
        max_iterations = 50000
        
        for iteration in range(max_iterations):
            try:
                # Select CPU first (determines socket and platform)
                cpu = random.choice(databases['cpus'])
                
                # Select compatible motherboard
                compatible_motherboards = [
                    mb for mb in databases['motherboards'] 
                    if mb['Socket'] == cpu['Socket']
                ]
                if not compatible_motherboards:
                    continue
                motherboard = random.choice(compatible_motherboards)
                
                # Select compatible RAM
                if cpu['Socket'] == 'AM4':
                    compatible_ram = [ram for ram in databases['ram'] if ram['Type'] == 'DDR4']
                else:
                    compatible_ram = [ram for ram in databases['ram'] if ram['Type'] == 'DDR5']
                
                if not compatible_ram:
                    continue
                ram = random.choice(compatible_ram)
                
                # Select other components
                gpu = random.choice(databases['gpus'])
                storage = random.choice(databases['storage'])
                cooler = random.choice(databases['coolers'])
                psu = random.choice(databases['psus'])
                case = random.choice(databases['cases'])
                
                # Calculate total price
                components = {
                    "CPU": cpu, "GPU": gpu, "Motherboard": motherboard, "RAM": ram,
                    "Storage": storage, "Cooler": cooler, "PSU": psu, "Case": case
                }
                
                total_price = sum(comp['Price_MAD'] for comp in components.values())
                
                # Check if build meets criteria
                if total_price <= budget and total_price > best_price:
                    best_price = total_price
                    best_build = components
                    
                    # Stop if we're close to budget (within 100 MAD)
                    if budget - best_price < 100:
                        print(f"✅ Optimal build found after {iteration + 1} iterations")
                        break
                        
            except (IndexError, KeyError) as e:
                continue
        
        if best_build:
            utilization = best_price / budget
            print(f"💰 Final build: {best_price:,} MAD (Budget utilization: {utilization:.1%})")
        else:
            print("❌ Could not find compatible build within budget")
        
        return best_build
    
    @staticmethod
    def _generate_build_quote_with_llm(build: Dict[str, Dict], budget: int, use_case: str, strategy: str) -> str:
        """Generate formatted build quote with LLM-enhanced descriptions"""
        total_price = sum(comp['Price_MAD'] for comp in build.values())
        
        # Use LLM to generate performance expectations
        try:
            perf_prompt = f"""Given this PC build for {use_case}:
- CPU: {build['CPU']['Brand']} {build['CPU']['Model']}
- GPU: {build['GPU']['Brand']} {build['GPU']['Model']}
- Total: {total_price} MAD

Provide 2-3 brief bullet points about expected performance. Be specific and realistic."""

            response = llm.invoke(perf_prompt)
            performance_notes = response.content.strip()
            
        except Exception as e:
            print(f"⚠️ LLM performance notes failed: {e}")
            performance_notes = ProcurementAgent._generate_fallback_performance_notes(use_case)
        
        quote = "## 🖥️ **Custom PC Build Quote**\n\n"
        quote += "| Category | Brand & Model | Price (MAD) |\n"
        quote += "|---|---|---|\n"
        
        # Component rows
        for category, component in build.items():
            quote += f"| **{category}** | {component['Brand']} {component['Model']} | {component['Price_MAD']:,} |\n"
        
        # Total row
        quote += "|---|---|---|\n"
        quote += f"| **🎯 TOTAL** | **Complete System** | **{total_price:,} MAD** |\n\n"
        
        # Compatibility and optimization info
        quote += "### ✅ **Build Verification**\n"
        quote += f"- **Socket Compatibility**: {build['CPU']['Socket']} (CPU ↔ Motherboard)\n"
        quote += f"- **RAM Compatibility**: {build['RAM']['Type']} (Matches {build['CPU']['Socket']})\n"
        quote += f"- **Use Case Optimization**: {use_case.replace('_', ' ').title()}\n"
        quote += f"- **Budget Utilization**: {total_price/budget:.1%} ({total_price:,}/{budget:,} MAD)\n"
        quote += f"- **Remaining Budget**: {budget - total_price:,} MAD\n\n"
        
        # LLM-generated performance expectations
        quote += "### 🚀 **Expected Performance (AI Analysis)**\n"
        quote += performance_notes + "\n\n"
        
        # Strategy used
        quote += "### 🧠 **Selection Strategy**\n"
        quote += strategy + "\n"
        
        return quote
    
    @staticmethod
    def _generate_fallback_performance_notes(use_case: str) -> str:
        """Generate fallback performance notes if LLM fails"""
        notes = {
            "gaming": "- Good gaming performance at 1080p-1440p\n- Balanced CPU-GPU configuration\n- Suitable for modern AAA titles",
            "ai_ml": "- High compute performance for AI/ML workloads\n- GPU-accelerated training capabilities\n- Good for deep learning tasks",
            "content_creation": "- Excellent for video editing and rendering\n- Multi-core CPU performance\n- Fast storage for large files",
            "office": "- Smooth multitasking for office applications\n- Energy efficient configuration\n- Reliable for daily productivity",
            "development": "- Fast compilation and build times\n- Good for running VMs and containers\n- Multitasking capability",
            "general": "- Well-balanced system for general use\n- Good price-to-performance ratio\n- Versatile for various tasks"
        }
        return notes.get(use_case, notes["general"])

# Export node functions for use in workflow
def architect_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Architect agent node function for LangGraph."""
    return ArchitectAgent.process_request(state)

def procurement_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Procurement agent node function for LangGraph."""
    return ProcurementAgent.select_components(state)