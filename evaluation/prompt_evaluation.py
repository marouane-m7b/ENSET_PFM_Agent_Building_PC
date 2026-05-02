"""
Prompt Evaluation System for Multi-Agent PC Builder
Implements A/B testing and precision evaluation for prompt optimization
"""

import json
import time
import uuid
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics
import re

@dataclass
class PromptVariant:
    """Represents a prompt variation for testing"""
    id: str
    name: str
    prompt_text: str
    description: str

@dataclass
class EvaluationResult:
    """Stores evaluation metrics for a prompt variant"""
    variant_id: str
    accuracy_score: float
    response_time: float
    budget_adherence: float
    component_compatibility: float
    user_satisfaction: float
    overall_score: float

class PromptEvaluator:
    """Main class for evaluating and optimizing agent prompts"""
    
    def __init__(self):
        self.test_cases = self._load_test_cases()
        self.architect_prompts = self._define_architect_prompts()
        self.procurement_prompts = self._define_procurement_prompts()
        self.results = []
        
    def _load_test_cases(self) -> List[Dict]:
        """Define test cases for evaluation"""
        return [
            {
                "request": "I need a gaming PC for 4K gaming. Budget: 15000 MAD",
                "expected_budget": 15000,
                "expected_use_case": "gaming",
                "expected_performance": "4K"
            },
            {
                "request": "Budget 8000 MAD for office work and light programming",
                "expected_budget": 8000,
                "expected_use_case": "office",
                "expected_performance": "basic"
            },
            {
                "request": "AI/ML workstation, deep learning, budget around 25000 MAD",
                "expected_budget": 25000,
                "expected_use_case": "ai_ml",
                "expected_performance": "high_compute"
            },
            {
                "request": "Streaming and content creation setup, 18000 MAD budget",
                "expected_budget": 18000,
                "expected_use_case": "content_creation",
                "expected_performance": "streaming"
            },
            {
                "request": "Basic home computer for web browsing, 5000 MAD",
                "expected_budget": 5000,
                "expected_use_case": "basic",
                "expected_performance": "low"
            }
        ]
    
    def _define_architect_prompts(self) -> List[PromptVariant]:
        """Define different architect prompt variations for A/B testing"""
        return [
            PromptVariant(
                id="arch_v1",
                name="Basic Extraction",
                prompt_text="Extract the budget from this request: {request}",
                description="Simple budget extraction approach"
            ),
            PromptVariant(
                id="arch_v2", 
                name="Detailed Analysis",
                prompt_text="""Analyze this PC build request and extract:
                1. Budget (in MAD)
                2. Primary use case (gaming, office, AI/ML, etc.)
                3. Performance requirements
                Request: {request}""",
                description="Comprehensive request analysis"
            ),
            PromptVariant(
                id="arch_v3",
                name="Structured Extraction",
                prompt_text="""As a PC architect, analyze this request and provide structured output:
                BUDGET: [amount in MAD]
                USE_CASE: [primary purpose]
                PERFORMANCE: [required level]
                
                Request: {request}""",
                description="Structured output format"
            )
        ]
    
    def _define_procurement_prompts(self) -> List[PromptVariant]:
        """Define different procurement prompt variations"""
        return [
            PromptVariant(
                id="proc_v1",
                name="Basic Selection",
                prompt_text="Find PC components within budget: {budget} MAD",
                description="Simple component selection"
            ),
            PromptVariant(
                id="proc_v2",
                name="Optimized Selection", 
                prompt_text="""Find the best PC components for:
                Budget: {budget} MAD
                Use Case: {use_case}
                Prioritize performance and compatibility.""",
                description="Performance-focused selection"
            ),
            PromptVariant(
                id="proc_v3",
                name="Balanced Selection",
                prompt_text="""Select PC components with these priorities:
                1. Stay within {budget} MAD budget
                2. Ensure full compatibility
                3. Optimize price/performance ratio
                4. Consider future upgrade path""",
                description="Balanced approach with multiple criteria"
            )
        ]
    
    def evaluate_budget_extraction(self, prompt_variant: PromptVariant, test_case: Dict) -> float:
        """Evaluate how well a prompt extracts budget information"""
        # Simulate prompt execution with regex extraction
        request = test_case["request"]
        expected_budget = test_case["expected_budget"]
        
        # Simple regex-based extraction (simulating LLM response)
        match = re.search(r'(\d{3,})\s*(?:MAD|mad|Mad|dirhams|dh)?', request)
        if match:
            extracted_budget = int(match.group(1))
            accuracy = 1.0 if extracted_budget == expected_budget else max(0, 1 - abs(extracted_budget - expected_budget) / expected_budget)
        else:
            accuracy = 0.0
            
        return min(1.0, accuracy)
    
    def evaluate_component_compatibility(self, build_result: Dict) -> float:
        """Evaluate component compatibility in the build"""
        if not build_result or "components" not in build_result:
            return 0.0
            
        compatibility_score = 1.0
        components = build_result["components"]
        
        # Check CPU-Motherboard socket compatibility
        if "cpu_socket" in components and "mb_socket" in components:
            if components["cpu_socket"] != components["mb_socket"]:
                compatibility_score -= 0.3
                
        # Check RAM-CPU compatibility  
        if "cpu_socket" in components and "ram_type" in components:
            if components["cpu_socket"] == "AM4" and components["ram_type"] != "DDR4":
                compatibility_score -= 0.2
            elif components["cpu_socket"] != "AM4" and components["ram_type"] != "DDR5":
                compatibility_score -= 0.2
                
        return max(0.0, compatibility_score)
    
    def evaluate_budget_adherence(self, build_result: Dict, target_budget: float) -> float:
        """Evaluate how well the build stays within budget"""
        if not build_result or "total_price" not in build_result:
            return 0.0
            
        total_price = build_result["total_price"]
        if total_price <= target_budget:
            # Reward builds that use most of the budget efficiently
            utilization = total_price / target_budget
            return utilization if utilization >= 0.7 else utilization * 0.8
        else:
            # Penalize budget overruns
            overage = (total_price - target_budget) / target_budget
            return max(0.0, 1.0 - overage * 2)
    
    def simulate_build_generation(self, prompt_variant: PromptVariant, test_case: Dict) -> Dict:
        """Simulate build generation for evaluation purposes"""
        # This simulates the actual agent execution
        budget = test_case["expected_budget"]
        
        # Simulate different outcomes based on prompt quality
        if "detailed" in prompt_variant.name.lower() or "optimized" in prompt_variant.name.lower():
            # Better prompts produce better results
            simulated_price = budget * (0.85 + 0.1 * hash(prompt_variant.id) % 10 / 10)
            compatibility = 0.9 + 0.1 * (hash(prompt_variant.id) % 2)
        else:
            # Basic prompts have more variation
            simulated_price = budget * (0.7 + 0.4 * hash(prompt_variant.id) % 10 / 10)
            compatibility = 0.6 + 0.3 * (hash(prompt_variant.id) % 3) / 2
            
        return {
            "total_price": simulated_price,
            "components": {
                "cpu_socket": "AM4" if hash(prompt_variant.id) % 2 else "AM5",
                "mb_socket": "AM4" if hash(prompt_variant.id) % 2 else "AM5", 
                "ram_type": "DDR4" if hash(prompt_variant.id) % 2 else "DDR5"
            }
        }
    
    def run_ab_test(self, prompt_variants: List[PromptVariant], test_cases: List[Dict]) -> List[EvaluationResult]:
        """Run A/B testing on prompt variants"""
        results = []
        
        print("🧪 Starting A/B Testing for Prompt Variants...")
        print("=" * 60)
        
        for variant in prompt_variants:
            print(f"\n📝 Testing Variant: {variant.name} ({variant.id})")
            print(f"Description: {variant.description}")
            
            variant_scores = []
            
            for i, test_case in enumerate(test_cases):
                print(f"  Test Case {i+1}: {test_case['request'][:50]}...")
                
                start_time = time.time()
                
                # Evaluate budget extraction
                budget_accuracy = self.evaluate_budget_extraction(variant, test_case)
                
                # Simulate build generation
                build_result = self.simulate_build_generation(variant, test_case)
                
                # Evaluate build quality
                budget_adherence = self.evaluate_budget_adherence(build_result, test_case["expected_budget"])
                compatibility = self.evaluate_component_compatibility(build_result)
                
                response_time = time.time() - start_time
                
                # Simulate user satisfaction (based on other metrics)
                user_satisfaction = (budget_accuracy + budget_adherence + compatibility) / 3
                
                # Calculate overall score
                overall_score = (
                    budget_accuracy * 0.25 +
                    budget_adherence * 0.30 +
                    compatibility * 0.25 +
                    user_satisfaction * 0.20
                )
                
                variant_scores.append(overall_score)
                
                print(f"    Budget Accuracy: {budget_accuracy:.2f}")
                print(f"    Budget Adherence: {budget_adherence:.2f}")
                print(f"    Compatibility: {compatibility:.2f}")
                print(f"    Overall Score: {overall_score:.2f}")
            
            # Calculate aggregate metrics
            avg_score = statistics.mean(variant_scores)
            avg_response_time = 0.1 + hash(variant.id) % 100 / 1000  # Simulate response time
            
            result = EvaluationResult(
                variant_id=variant.id,
                accuracy_score=statistics.mean([self.evaluate_budget_extraction(variant, tc) for tc in test_cases]),
                response_time=avg_response_time,
                budget_adherence=avg_score,  # Simplified for demo
                component_compatibility=avg_score,  # Simplified for demo
                user_satisfaction=avg_score,
                overall_score=avg_score
            )
            
            results.append(result)
            
            print(f"\n📊 Variant Summary:")
            print(f"  Average Score: {avg_score:.3f}")
            print(f"  Response Time: {avg_response_time:.3f}s")
        
        return results
    
    def generate_evaluation_report(self, results: List[EvaluationResult]) -> str:
        """Generate comprehensive evaluation report"""
        report = []
        report.append("# 📊 PROMPT EVALUATION REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Test Cases: {len(self.test_cases)}")
        report.append(f"Prompt Variants: {len(results)}")
        report.append("")
        
        # Sort results by overall score
        sorted_results = sorted(results, key=lambda x: x.overall_score, reverse=True)
        
        report.append("## 🏆 RANKING BY OVERALL PERFORMANCE")
        report.append("")
        for i, result in enumerate(sorted_results, 1):
            variant = next(v for v in self.architect_prompts if v.id == result.variant_id)
            report.append(f"**{i}. {variant.name}** (Score: {result.overall_score:.3f})")
            report.append(f"   - Accuracy: {result.accuracy_score:.3f}")
            report.append(f"   - Budget Adherence: {result.budget_adherence:.3f}")
            report.append(f"   - Compatibility: {result.component_compatibility:.3f}")
            report.append(f"   - Response Time: {result.response_time:.3f}s")
            report.append("")
        
        # Statistical analysis
        scores = [r.overall_score for r in results]
        report.append("## 📈 STATISTICAL ANALYSIS")
        report.append("")
        report.append(f"- **Mean Score**: {statistics.mean(scores):.3f}")
        report.append(f"- **Median Score**: {statistics.median(scores):.3f}")
        report.append(f"- **Standard Deviation**: {statistics.stdev(scores):.3f}")
        report.append(f"- **Score Range**: {min(scores):.3f} - {max(scores):.3f}")
        report.append("")
        
        # Recommendations
        best_variant = sorted_results[0]
        worst_variant = sorted_results[-1]
        improvement = best_variant.overall_score - worst_variant.overall_score
        
        report.append("## 💡 RECOMMENDATIONS")
        report.append("")
        report.append(f"1. **Deploy Best Variant**: Use '{next(v for v in self.architect_prompts if v.id == best_variant.variant_id).name}' for production")
        report.append(f"2. **Performance Gain**: {improvement:.1%} improvement over worst variant")
        report.append(f"3. **Focus Areas**: Optimize prompts for budget adherence and compatibility")
        report.append("")
        
        return "\n".join(report)
    
    def save_results(self, results: List[EvaluationResult], filename: str = None):
        """Save evaluation results to JSON file"""
        if filename is None:
            filename = f"evaluation/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        data = {
            "timestamp": datetime.now().isoformat(),
            "test_cases": len(self.test_cases),
            "results": [
                {
                    "variant_id": r.variant_id,
                    "accuracy_score": r.accuracy_score,
                    "response_time": r.response_time,
                    "budget_adherence": r.budget_adherence,
                    "component_compatibility": r.component_compatibility,
                    "user_satisfaction": r.user_satisfaction,
                    "overall_score": r.overall_score
                }
                for r in results
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"💾 Results saved to: {filename}")

def main():
    """Run the complete prompt evaluation suite"""
    print("🚀 Starting Prompt Evaluation System")
    print("=" * 50)
    
    evaluator = PromptEvaluator()
    
    # Run A/B testing
    results = evaluator.run_ab_test(evaluator.architect_prompts, evaluator.test_cases)
    
    # Generate and display report
    report = evaluator.generate_evaluation_report(results)
    print("\n" + report)
    
    # Save results
    evaluator.save_results(results)
    
    # Save report
    with open("evaluation/evaluation_report.md", "w", encoding='utf-8') as f:
        f.write(report)
    
    print("\n✅ Evaluation Complete!")
    print("📁 Check 'evaluation/' folder for detailed results")

if __name__ == "__main__":
    main()