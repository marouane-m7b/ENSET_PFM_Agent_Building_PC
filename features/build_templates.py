"""
Build Templates - Pre-configured PC builds for common use cases
"""

from typing import Dict, List

class BuildTemplates:
    """Pre-configured build templates for quick recommendations"""
    
    TEMPLATES = {
        "budget_office": {
            "name": "Budget Office PC",
            "description": "Perfect for office work, web browsing, and light productivity",
            "budget_range": (5000, 8000),
            "use_case": "office",
            "performance_level": "basic",
            "recommended_specs": {
                "CPU": "AMD Ryzen 3 or Intel i3",
                "GPU": "Integrated graphics",
                "RAM": "8GB DDR4",
                "Storage": "256GB SSD",
                "PSU": "400W"
            }
        },
        "gaming_1080p": {
            "name": "1080p Gaming PC",
            "description": "Smooth gaming at 1080p with high settings",
            "budget_range": (8000, 12000),
            "use_case": "gaming",
            "performance_level": "medium",
            "recommended_specs": {
                "CPU": "AMD Ryzen 5 5600X or Intel i5-12400F",
                "GPU": "AMD RX 6600 or NVIDIA RTX 3060",
                "RAM": "16GB DDR4",
                "Storage": "500GB NVMe SSD",
                "PSU": "550W 80+ Bronze"
            }
        },
        "gaming_1440p": {
            "name": "1440p Gaming PC",
            "description": "High-performance gaming at 1440p with ultra settings",
            "budget_range": (15000, 22000),
            "use_case": "gaming",
            "performance_level": "high",
            "recommended_specs": {
                "CPU": "AMD Ryzen 7 5800X or Intel i7-12700K",
                "GPU": "AMD RX 6800 XT or NVIDIA RTX 3070 Ti",
                "RAM": "32GB DDR4",
                "Storage": "1TB NVMe SSD",
                "PSU": "750W 80+ Gold"
            }
        },
        "gaming_4k": {
            "name": "4K Gaming Beast",
            "description": "Ultimate 4K gaming experience with ray tracing",
            "budget_range": (25000, 40000),
            "use_case": "gaming",
            "performance_level": "high",
            "recommended_specs": {
                "CPU": "AMD Ryzen 9 5900X or Intel i9-12900K",
                "GPU": "AMD RX 7900 XTX or NVIDIA RTX 4080",
                "RAM": "32GB DDR5",
                "Storage": "2TB NVMe Gen4 SSD",
                "PSU": "850W 80+ Gold"
            }
        },
        "content_creator": {
            "name": "Content Creation Workstation",
            "description": "Video editing, 3D rendering, and content creation",
            "budget_range": (18000, 30000),
            "use_case": "content_creation",
            "performance_level": "high",
            "recommended_specs": {
                "CPU": "AMD Ryzen 9 5950X or Intel i9-12900K",
                "GPU": "NVIDIA RTX 3070 or better",
                "RAM": "64GB DDR4",
                "Storage": "2TB NVMe SSD + 2TB HDD",
                "PSU": "850W 80+ Gold"
            }
        },
        "ai_ml_workstation": {
            "name": "AI/ML Development Station",
            "description": "Machine learning training and AI development",
            "budget_range": (22000, 45000),
            "use_case": "ai_ml",
            "performance_level": "high",
            "recommended_specs": {
                "CPU": "AMD Ryzen 9 or Intel i9",
                "GPU": "NVIDIA RTX 3090 or RTX 4090 (CUDA cores)",
                "RAM": "64GB DDR4 or DDR5",
                "Storage": "2TB NVMe Gen4 SSD",
                "PSU": "1000W 80+ Platinum"
            }
        },
        "developer_station": {
            "name": "Software Development PC",
            "description": "Programming, compilation, and running VMs",
            "budget_range": (12000, 18000),
            "use_case": "development",
            "performance_level": "medium",
            "recommended_specs": {
                "CPU": "AMD Ryzen 7 or Intel i7",
                "GPU": "Mid-range (GTX 1660 or better)",
                "RAM": "32GB DDR4",
                "Storage": "1TB NVMe SSD",
                "PSU": "650W 80+ Bronze"
            }
        },
        "streaming_setup": {
            "name": "Streaming & Gaming PC",
            "description": "Stream and game simultaneously without lag",
            "budget_range": (16000, 25000),
            "use_case": "content_creation",
            "performance_level": "high",
            "recommended_specs": {
                "CPU": "AMD Ryzen 7 5800X or Intel i7-12700K",
                "GPU": "NVIDIA RTX 3070 or better (NVENC)",
                "RAM": "32GB DDR4",
                "Storage": "1TB NVMe SSD",
                "PSU": "750W 80+ Gold"
            }
        }
    }
    
    @classmethod
    def get_template(cls, template_id: str) -> Dict:
        """Get a specific template by ID"""
        return cls.TEMPLATES.get(template_id, {})
    
    @classmethod
    def get_all_templates(cls) -> Dict:
        """Get all available templates"""
        return cls.TEMPLATES
    
    @classmethod
    def find_matching_templates(cls, budget: int, use_case: str = None) -> List[Dict]:
        """Find templates matching budget and use case"""
        matching = []
        
        for template_id, template in cls.TEMPLATES.items():
            min_budget, max_budget = template["budget_range"]
            
            # Check budget match
            budget_match = min_budget <= budget <= max_budget
            
            # Check use case match
            use_case_match = use_case is None or template["use_case"] == use_case
            
            if budget_match and use_case_match:
                matching.append({
                    "id": template_id,
                    **template
                })
        
        return matching
    
    @classmethod
    def get_template_summary(cls, template_id: str) -> str:
        """Get formatted summary of a template"""
        template = cls.get_template(template_id)
        if not template:
            return "Template not found"
        
        min_budget, max_budget = template["budget_range"]
        
        summary = f"### {template['name']}\n\n"
        summary += f"**Description:** {template['description']}\n\n"
        summary += f"**Budget Range:** {min_budget:,} - {max_budget:,} MAD\n\n"
        summary += f"**Use Case:** {template['use_case'].replace('_', ' ').title()}\n\n"
        summary += "**Recommended Specs:**\n"
        
        for component, spec in template["recommended_specs"].items():
            summary += f"- **{component}:** {spec}\n"
        
        return summary
