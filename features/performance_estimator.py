"""
Performance Estimator - Estimate gaming FPS and benchmark scores
"""

from typing import Dict, Any, List

class PerformanceEstimator:
    """Estimates performance metrics for PC builds"""
    
    # GPU Performance Database (approximate FPS at 1080p High settings)
    GPU_PERFORMANCE = {
        # NVIDIA RTX 40 Series
        "RTX 4090": {"1080p": 240, "1440p": 200, "4k": 120, "score": 10000},
        "RTX 4080": {"1080p": 220, "1440p": 180, "4k": 100, "score": 9000},
        "RTX 4070 Ti": {"1080p": 200, "1440p": 160, "4k": 85, "score": 8000},
        "RTX 4070": {"1080p": 180, "1440p": 140, "4k": 70, "score": 7000},
        "RTX 4060 Ti": {"1080p": 150, "1440p": 110, "4k": 55, "score": 6000},
        "RTX 4060": {"1080p": 130, "1440p": 90, "4k": 45, "score": 5000},
        
        # NVIDIA RTX 30 Series
        "RTX 3090": {"1080p": 200, "1440p": 170, "4k": 95, "score": 8500},
        "RTX 3080": {"1080p": 190, "1440p": 155, "4k": 85, "score": 7800},
        "RTX 3070 Ti": {"1080p": 170, "1440p": 135, "4k": 70, "score": 7000},
        "RTX 3070": {"1080p": 160, "1440p": 125, "4k": 65, "score": 6500},
        "RTX 3060 Ti": {"1080p": 145, "1440p": 105, "4k": 55, "score": 5800},
        "RTX 3060": {"1080p": 120, "1440p": 85, "4k": 45, "score": 5000},
        
        # AMD RX 7000 Series
        "RX 7900 XTX": {"1080p": 230, "1440p": 190, "4k": 110, "score": 9200},
        "RX 7900 XT": {"1080p": 210, "1440p": 170, "4k": 95, "score": 8500},
        "RX 7800 XT": {"1080p": 180, "1440p": 145, "4k": 75, "score": 7200},
        "RX 7700 XT": {"1080p": 160, "1440p": 125, "4k": 65, "score": 6500},
        "RX 7600": {"1080p": 130, "1440p": 90, "4k": 45, "score": 5200},
        
        # AMD RX 6000 Series
        "RX 6950 XT": {"1080p": 200, "1440p": 165, "4k": 90, "score": 8200},
        "RX 6900 XT": {"1080p": 195, "1440p": 160, "4k": 85, "score": 8000},
        "RX 6800 XT": {"1080p": 180, "1440p": 145, "4k": 75, "score": 7400},
        "RX 6800": {"1080p": 165, "1440p": 130, "4k": 68, "score": 6800},
        "RX 6700 XT": {"1080p": 145, "1440p": 110, "4k": 55, "score": 6000},
        "RX 6600 XT": {"1080p": 125, "1440p": 90, "4k": 45, "score": 5200},
        "RX 6600": {"1080p": 110, "1440p": 75, "4k": 38, "score": 4500},
        
        # Older/Budget GPUs
        "GTX 1660 Super": {"1080p": 90, "1440p": 60, "4k": 30, "score": 3800},
        "GTX 1650": {"1080p": 65, "1440p": 40, "4k": 20, "score": 2800},
    }
    
    # CPU Performance Scores (relative)
    CPU_PERFORMANCE = {
        # AMD Ryzen 9
        "Ryzen 9 5950X": 9500,
        "Ryzen 9 5900X": 9000,
        "Ryzen 9 7950X": 10000,
        "Ryzen 9 7900X": 9500,
        
        # AMD Ryzen 7
        "Ryzen 7 5800X": 8000,
        "Ryzen 7 5700X": 7500,
        "Ryzen 7 7700X": 8500,
        
        # AMD Ryzen 5
        "Ryzen 5 5600X": 7000,
        "Ryzen 5 5600": 6500,
        "Ryzen 5 7600X": 7500,
        
        # AMD Ryzen 3
        "Ryzen 3 3300X": 5000,
        "Ryzen 3 3100": 4500,
        
        # Intel i9
        "i9-12900K": 9800,
        "i9-13900K": 10500,
        "i9-14900K": 11000,
        
        # Intel i7
        "i7-12700K": 8500,
        "i7-13700K": 9000,
        "i7-12700F": 8200,
        
        # Intel i5
        "i5-12600K": 7500,
        "i5-13600K": 8000,
        "i5-12400F": 6500,
        
        # Intel i3
        "i3-12100F": 5500,
        "i3-10100": 4500,
    }
    
    @classmethod
    def estimate_gaming_performance(cls, build: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate gaming performance (FPS) for a build"""
        gpu_model = build.get("GPU", {}).get("Model", "")
        
        # Find matching GPU
        gpu_perf = None
        for gpu_name, perf in cls.GPU_PERFORMANCE.items():
            if gpu_name.lower() in gpu_model.lower():
                gpu_perf = perf
                break
        
        if not gpu_perf:
            # Default estimates for unknown GPU
            gpu_perf = {"1080p": 100, "1440p": 70, "4k": 40, "score": 5000}
        
        return {
            "fps_1080p": gpu_perf["1080p"],
            "fps_1440p": gpu_perf["1440p"],
            "fps_4k": gpu_perf["4k"],
            "gpu_score": gpu_perf["score"],
            "confidence": "high" if gpu_model else "estimated"
        }
    
    @classmethod
    def estimate_cpu_performance(cls, build: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate CPU performance score"""
        cpu_model = build.get("CPU", {}).get("Model", "")
        
        # Find matching CPU
        cpu_score = None
        for cpu_name, score in cls.CPU_PERFORMANCE.items():
            if cpu_name.lower() in cpu_model.lower():
                cpu_score = score
                break
        
        if not cpu_score:
            # Default estimate
            cpu_score = 6000
        
        return {
            "cpu_score": cpu_score,
            "single_thread": int(cpu_score * 0.7),
            "multi_thread": cpu_score,
            "confidence": "high" if cpu_model else "estimated"
        }
    
    @classmethod
    def estimate_overall_performance(cls, build: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate overall system performance"""
        gaming_perf = cls.estimate_gaming_performance(build)
        cpu_perf = cls.estimate_cpu_performance(build)
        
        # Calculate overall score
        overall_score = int((gaming_perf["gpu_score"] + cpu_perf["cpu_score"]) / 2)
        
        # Determine performance tier
        if overall_score >= 9000:
            tier = "Extreme"
            description = "Top-tier performance for 4K gaming and professional workloads"
        elif overall_score >= 7500:
            tier = "High-End"
            description = "Excellent for 1440p-4K gaming and content creation"
        elif overall_score >= 6000:
            tier = "Mid-Range"
            description = "Great for 1080p-1440p gaming and productivity"
        elif overall_score >= 4500:
            tier = "Budget"
            description = "Good for 1080p gaming and general use"
        else:
            tier = "Entry-Level"
            description = "Suitable for light gaming and office work"
        
        return {
            "overall_score": overall_score,
            "performance_tier": tier,
            "description": description,
            "gaming_performance": gaming_perf,
            "cpu_performance": cpu_perf
        }
    
    @classmethod
    def format_performance_report(cls, build: Dict[str, Any]) -> str:
        """Generate formatted performance report"""
        perf = cls.estimate_overall_performance(build)
        
        report = "### 🎮 **Performance Estimates**\n\n"
        report += f"**Overall Score:** {perf['overall_score']:,} points\n"
        report += f"**Performance Tier:** {perf['performance_tier']}\n"
        report += f"**Description:** {perf['description']}\n\n"
        
        report += "#### Gaming Performance (Average FPS)\n"
        gaming = perf['gaming_performance']
        report += f"- **1080p High:** ~{gaming['fps_1080p']} FPS\n"
        report += f"- **1440p High:** ~{gaming['fps_1440p']} FPS\n"
        report += f"- **4K High:** ~{gaming['fps_4k']} FPS\n\n"
        
        report += "#### CPU Performance\n"
        cpu = perf['cpu_performance']
        report += f"- **Multi-Thread Score:** {cpu['multi_thread']:,}\n"
        report += f"- **Single-Thread Score:** {cpu['single_thread']:,}\n\n"
        
        report += "*Note: Estimates based on typical gaming scenarios. Actual performance may vary.*\n"
        
        return report
    
    @classmethod
    def get_game_specific_fps(cls, build: Dict[str, Any], resolution: str = "1080p") -> List[Dict]:
        """Get estimated FPS for specific popular games"""
        base_perf = cls.estimate_gaming_performance(build)
        base_fps = base_perf.get(f"fps_{resolution}", 100)
        
        # Game-specific multipliers (relative to average)
        games = [
            {"name": "Fortnite", "multiplier": 1.3, "settings": "Epic"},
            {"name": "CS:GO", "multiplier": 2.0, "settings": "High"},
            {"name": "Valorant", "multiplier": 2.2, "settings": "High"},
            {"name": "Cyberpunk 2077", "multiplier": 0.6, "settings": "High"},
            {"name": "Red Dead Redemption 2", "multiplier": 0.7, "settings": "High"},
            {"name": "Call of Duty: Warzone", "multiplier": 0.9, "settings": "High"},
            {"name": "Apex Legends", "multiplier": 1.1, "settings": "High"},
            {"name": "GTA V", "multiplier": 1.4, "settings": "Very High"},
            {"name": "Minecraft (Shaders)", "multiplier": 1.2, "settings": "High"},
            {"name": "League of Legends", "multiplier": 2.5, "settings": "Very High"},
        ]
        
        results = []
        for game in games:
            estimated_fps = int(base_fps * game["multiplier"])
            results.append({
                "game": game["name"],
                "fps": estimated_fps,
                "settings": game["settings"]
            })
        
        return results
