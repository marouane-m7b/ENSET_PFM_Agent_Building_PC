"""
Build Comparator - Compare multiple PC builds side-by-side
"""

from typing import List, Dict, Any
import pandas as pd

class BuildComparator:
    """Compare multiple PC builds"""
    
    @staticmethod
    def compare_builds(builds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple builds and return comparison data"""
        if not builds or len(builds) < 2:
            return {"error": "Need at least 2 builds to compare"}
        
        comparison = {
            "build_count": len(builds),
            "price_comparison": BuildComparator._compare_prices(builds),
            "component_comparison": BuildComparator._compare_components(builds),
            "performance_comparison": BuildComparator._compare_performance(builds),
            "value_analysis": BuildComparator._analyze_value(builds)
        }
        
        return comparison
    
    @staticmethod
    def _compare_prices(builds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare prices across builds"""
        prices = [b.get("total_price", 0) for b in builds]
        
        return {
            "prices": prices,
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": sum(prices) / len(prices),
            "price_difference": max(prices) - min(prices),
            "cheapest_index": prices.index(min(prices)),
            "most_expensive_index": prices.index(max(prices))
        }
    
    @staticmethod
    def _compare_components(builds: List[Dict[str, Any]]) -> Dict[str, List]:
        """Compare components across builds"""
        categories = ["CPU", "GPU", "Motherboard", "RAM", "Storage", "PSU", "Case", "Cooler"]
        
        comparison = {}
        for category in categories:
            comparison[category] = []
            for build in builds:
                components = build.get("selected_components", {})
                if category in components:
                    comp = components[category]
                    comparison[category].append({
                        "brand": comp.get("Brand", "N/A"),
                        "model": comp.get("Model", "N/A"),
                        "price": comp.get("Price_MAD", 0)
                    })
                else:
                    comparison[category].append(None)
        
        return comparison
    
    @staticmethod
    def _compare_performance(builds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare estimated performance"""
        from features.performance_estimator import PerformanceEstimator
        
        performance_scores = []
        for build in builds:
            components = build.get("selected_components", {})
            perf = PerformanceEstimator.estimate_overall_performance(components)
            performance_scores.append(perf["overall_score"])
        
        return {
            "scores": performance_scores,
            "best_performance_index": performance_scores.index(max(performance_scores)),
            "worst_performance_index": performance_scores.index(min(performance_scores)),
            "performance_difference": max(performance_scores) - min(performance_scores)
        }
    
    @staticmethod
    def _analyze_value(builds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze price-to-performance value"""
        from features.performance_estimator import PerformanceEstimator
        
        value_scores = []
        for build in builds:
            components = build.get("selected_components", {})
            price = build.get("total_price", 1)
            perf = PerformanceEstimator.estimate_overall_performance(components)
            
            # Value = Performance / Price (higher is better)
            value = perf["overall_score"] / price if price > 0 else 0
            value_scores.append(value)
        
        best_value_index = value_scores.index(max(value_scores))
        
        return {
            "value_scores": value_scores,
            "best_value_index": best_value_index,
            "best_value_build": builds[best_value_index].get("build_id", best_value_index)
        }
    
    @staticmethod
    def format_comparison_table(builds: List[Dict[str, Any]]) -> str:
        """Format comparison as markdown table"""
        if not builds or len(builds) < 2:
            return "Need at least 2 builds to compare"
        
        comparison = BuildComparator.compare_builds(builds)
        
        output = "## 🔍 **Build Comparison**\n\n"
        
        # Price comparison
        output += "### 💰 Price Comparison\n\n"
        output += "| Build | Total Price | Budget | Utilization |\n"
        output += "|---|---|---|---|\n"
        
        for i, build in enumerate(builds):
            price = build.get("total_price", 0)
            budget = build.get("budget", 0)
            util = (price / budget * 100) if budget > 0 else 0
            output += f"| Build {i+1} | {price:,} MAD | {budget:,} MAD | {util:.1f}% |\n"
        
        output += "\n"
        
        # Component comparison
        output += "### 🔧 Component Comparison\n\n"
        comp_data = comparison["component_comparison"]
        
        for category, components in comp_data.items():
            if any(c is not None for c in components):
                output += f"**{category}:**\n"
                for i, comp in enumerate(components):
                    if comp:
                        output += f"- Build {i+1}: {comp['brand']} {comp['model']} ({comp['price']:,} MAD)\n"
                output += "\n"
        
        # Performance comparison
        output += "### ⚡ Performance Comparison\n\n"
        perf_data = comparison["performance_comparison"]
        output += "| Build | Performance Score |\n"
        output += "|---|---|\n"
        
        for i, score in enumerate(perf_data["scores"]):
            marker = " 🏆" if i == perf_data["best_performance_index"] else ""
            output += f"| Build {i+1}{marker} | {score:,} points |\n"
        
        output += "\n"
        
        # Value analysis
        output += "### 💎 Value Analysis\n\n"
        value_data = comparison["value_analysis"]
        best_value = value_data["best_value_index"]
        output += f"**Best Value:** Build {best_value + 1} (Best performance per MAD spent)\n\n"
        
        return output
    
    @staticmethod
    def get_winner_recommendation(builds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Determine which build is best for different criteria"""
        comparison = BuildComparator.compare_builds(builds)
        
        price_comp = comparison["price_comparison"]
        perf_comp = comparison["performance_comparison"]
        value_comp = comparison["value_analysis"]
        
        return {
            "best_budget": {
                "index": price_comp["cheapest_index"],
                "reason": "Lowest price"
            },
            "best_performance": {
                "index": perf_comp["best_performance_index"],
                "reason": "Highest performance score"
            },
            "best_value": {
                "index": value_comp["best_value_index"],
                "reason": "Best price-to-performance ratio"
            }
        }
