"""
Export Manager - Export builds to various formats
"""

import json
from datetime import datetime
from typing import Dict, Any
import os

class ExportManager:
    """Handles exporting PC builds to different formats"""
    
    @staticmethod
    def export_to_json(build_data: Dict[str, Any], filename: str = None) -> str:
        """Export build to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/build_{timestamp}.json"
        
        os.makedirs("exports", exist_ok=True)
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "build_info": {
                "budget": build_data.get("budget", 0),
                "use_case": build_data.get("use_case", "general"),
                "performance_level": build_data.get("performance_level", "medium"),
                "total_price": build_data.get("total_price", 0)
            },
            "components": build_data.get("selected_components", {}),
            "build_quote": build_data.get("final_build_quote", ""),
            "llm_strategy": build_data.get("llm_strategy", "")
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    @staticmethod
    def export_to_text(build_data: Dict[str, Any], filename: str = None) -> str:
        """Export build to formatted text file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/build_{timestamp}.txt"
        
        os.makedirs("exports", exist_ok=True)
        
        components = build_data.get("selected_components", {})
        total_price = build_data.get("total_price", 0)
        budget = build_data.get("budget", 0)
        
        content = "=" * 60 + "\n"
        content += "  AI HARDWARE ARCHITECT - PC BUILD QUOTE\n"
        content += "=" * 60 + "\n\n"
        content += f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"Budget: {budget:,} MAD\n"
        content += f"Use Case: {build_data.get('use_case', 'general').replace('_', ' ').title()}\n"
        content += f"Performance Level: {build_data.get('performance_level', 'medium').title()}\n\n"
        
        content += "-" * 60 + "\n"
        content += "COMPONENTS\n"
        content += "-" * 60 + "\n\n"
        
        for category, component in components.items():
            content += f"{category.upper()}\n"
            content += f"  Brand: {component.get('Brand', 'N/A')}\n"
            content += f"  Model: {component.get('Model', 'N/A')}\n"
            content += f"  Price: {component.get('Price_MAD', 0):,} MAD\n\n"
        
        content += "-" * 60 + "\n"
        content += f"TOTAL PRICE: {total_price:,} MAD\n"
        content += f"BUDGET UTILIZATION: {(total_price/budget)*100:.1f}%\n"
        content += f"REMAINING BUDGET: {budget - total_price:,} MAD\n"
        content += "=" * 60 + "\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename
    
    @staticmethod
    def export_to_csv(build_data: Dict[str, Any], filename: str = None) -> str:
        """Export build components to CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/build_{timestamp}.csv"
        
        os.makedirs("exports", exist_ok=True)
        
        components = build_data.get("selected_components", {})
        
        content = "Category,Brand,Model,Price_MAD\n"
        for category, component in components.items():
            brand = component.get('Brand', 'N/A')
            model = component.get('Model', 'N/A')
            price = component.get('Price_MAD', 0)
            content += f"{category},{brand},{model},{price}\n"
        
        total_price = build_data.get("total_price", 0)
        content += f"TOTAL,,,{total_price}\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename
