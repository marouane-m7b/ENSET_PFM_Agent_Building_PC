"""
Test Discord Webhook Integration
"""
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def test_discord_webhook():
    """Test sending a message to Discord"""
    
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL not set in .env file")
        return
    
    print(f"🔗 Testing Discord webhook...")
    print(f"URL: {DISCORD_WEBHOOK_URL[:50]}...")
    
    # Sample build data with ALL components
    sample_build = {
        "title": "🖥️ Test PC Build",
        "description": "Testing Discord webhook integration with full component list",
        "color": 0x10a37f,
        "fields": [
            {
                "name": "📊 Build Summary",
                "value": "**Use Case:** Gaming\n**Performance:** High\n**Budget:** 15,000 MAD\n**Total:** 14,800 MAD\n**Savings:** 200 MAD",
                "inline": False
            },
            {
                "name": "**CPU**",
                "value": "AMD Ryzen 5 5600X\n💰 3,500 MAD",
                "inline": True
            },
            {
                "name": "**GPU**",
                "value": "NVIDIA RTX 3060 Ti\n💰 5,500 MAD",
                "inline": True
            },
            {
                "name": "**Motherboard**",
                "value": "MSI B550 Gaming Plus\n💰 1,800 MAD",
                "inline": True
            },
            {
                "name": "**RAM**",
                "value": "Corsair Vengeance 16GB DDR4\n💰 1,200 MAD",
                "inline": True
            },
            {
                "name": "**Storage**",
                "value": "Samsung 970 EVO 1TB NVMe\n💰 1,500 MAD",
                "inline": True
            },
            {
                "name": "**PSU**",
                "value": "Corsair RM750 750W 80+ Gold\n💰 1,000 MAD",
                "inline": True
            },
            {
                "name": "**Cooler**",
                "value": "Cooler Master Hyper 212\n💰 200 MAD",
                "inline": True
            },
            {
                "name": "**Case**",
                "value": "NZXT H510 ATX Mid Tower\n💰 800 MAD",
                "inline": True
            },
            {
                "name": "📈 Budget Utilization",
                "value": "98.7% (14,800 / 15,000 MAD)",
                "inline": False
            }
        ],
        "footer": {
            "text": "AI Hardware Architect • Multi-Agent System"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    payload = {
        "username": "PC Builder Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2888/2888615.png",
        "embeds": [sample_build]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("✅ Discord webhook test successful!")
        print(f"Response: {response.status_code}")
    except Exception as e:
        print(f"❌ Discord webhook test failed: {e}")

if __name__ == "__main__":
    test_discord_webhook()
