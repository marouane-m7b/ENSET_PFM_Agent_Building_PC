"""
Test script to verify Groq API integration
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

print("🧪 Testing Groq API Integration...")
print("=" * 50)

# Initialize Groq LLM
try:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.0,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    print("✅ Groq LLM initialized successfully")
    
    # Test simple query
    print("\n📝 Testing simple query...")
    response = llm.invoke("Say 'Hello from Groq!' in one sentence.")
    print(f"Response: {response.content}")
    
    # Test PC builder query
    print("\n🖥️ Testing PC builder query...")
    test_request = "I need a gaming PC for 15000 MAD"
    
    prompt = f"""You are a PC hardware architect. Analyze this customer request and extract:
1. Budget (in MAD - Moroccan Dirhams)
2. Use case (gaming, office, ai_ml, content_creation, development, or general)
3. Performance level (basic, medium, or high)

Customer Request: {test_request}

Respond in this EXACT format:
BUDGET: [number only]
USE_CASE: [one word from the list above]
PERFORMANCE: [basic, medium, or high]
"""
    
    response = llm.invoke(prompt)
    print(f"Analysis:\n{response.content}")
    
    print("\n✅ All tests passed! Groq API is working correctly.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPlease check:")
    print("1. GROQ_API_KEY is set in .env file")
    print("2. API key is valid")
    print("3. Internet connection is working")
