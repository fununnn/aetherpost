"""Intelligent content optimization and A/B testing."""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import hashlib

from ..state.manager import StateManager
from ..config.models import CampaignConfig


class ContentOptimizer:
    """Optimizes content based on performance data and A/B testing."""
    
    def __init__(self):
        self.state_manager = StateManager()
        self.optimization_history = self._load_optimization_history()
    
    def _load_optimization_history(self) -> Dict:
        """Load historical optimization data."""
        history_file = Path(".aetherpost/optimization_history.json")
        if history_file.exists():
            try:
                with open(history_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {"experiments": [], "insights": [], "performance_data": {}}
    
    def _save_optimization_history(self):
        """Save optimization history to disk."""
        history_file = Path(".aetherpost/optimization_history.json")
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(history_file, "w") as f:
            json.dump(self.optimization_history, f, indent=2, default=str)
    
    async def optimize_content(self, config: CampaignConfig, platform: str) -> Dict:
        """Generate optimized content based on historical performance."""
        
        # Get performance insights
        insights = self._analyze_performance_patterns(platform)
        
        # Generate content variants
        variants = await self._generate_content_variants(config, platform, insights)
        
        # Select best variant based on optimization strategy
        best_variant = self._select_optimal_variant(variants, insights)
        
        # Log optimization decision
        self._log_optimization_decision(platform, variants, best_variant, insights)
        
        return best_variant
    
    def _analyze_performance_patterns(self, platform: str) -> Dict:
        """Analyze historical performance to identify patterns."""
        
        state = self.state_manager.load_state()
        if not state or not state.posts:
            return {"confidence": "low", "patterns": {}}
        
        # Filter posts for this platform
        platform_posts = [p for p in state.posts if p.platform == platform]
        
        if len(platform_posts) < 3:
            return {"confidence": "low", "patterns": {}}
        
        patterns = {}
        
        # Analyze timing patterns
        timing_performance = self._analyze_timing_patterns(platform_posts)
        patterns["timing"] = timing_performance
        
        # Analyze content length patterns
        length_performance = self._analyze_length_patterns(platform_posts)
        patterns["length"] = length_performance
        
        # Analyze emoji usage patterns
        emoji_performance = self._analyze_emoji_patterns(platform_posts)
        patterns["emojis"] = emoji_performance
        
        # Analyze hashtag effectiveness
        hashtag_performance = self._analyze_hashtag_patterns(platform_posts)
        patterns["hashtags"] = hashtag_performance
        
        # Analyze call-to-action effectiveness
        cta_performance = self._analyze_cta_patterns(platform_posts)
        patterns["call_to_action"] = cta_performance
        
        confidence = "high" if len(platform_posts) >= 10 else "medium"
        
        return {
            "confidence": confidence,
            "patterns": patterns,
            "sample_size": len(platform_posts)
        }
    
    def _analyze_timing_patterns(self, posts: List) -> Dict:
        """Analyze optimal posting times."""
        timing_data = {}
        
        for post in posts:
            if hasattr(post, 'created_at') and hasattr(post, 'metrics'):
                hour = post.created_at.hour
                engagement = self._calculate_engagement_score(post.metrics)
                
                if hour not in timing_data:
                    timing_data[hour] = []
                timing_data[hour].append(engagement)
        
        # Calculate average engagement per hour
        hourly_averages = {}
        for hour, engagements in timing_data.items():
            hourly_averages[hour] = sum(engagements) / len(engagements)
        
        # Find best and worst hours
        if hourly_averages:
            best_hour = max(hourly_averages, key=hourly_averages.get)
            worst_hour = min(hourly_averages, key=hourly_averages.get)
            
            return {
                "best_hour": best_hour,
                "worst_hour": worst_hour,
                "hourly_performance": hourly_averages
            }
        
        return {}
    
    def _analyze_length_patterns(self, posts: List) -> Dict:
        """Analyze optimal content length."""
        length_buckets = {"short": [], "medium": [], "long": []}
        
        for post in posts:
            if hasattr(post, 'content') and hasattr(post, 'metrics'):
                content_length = len(post.content.get('text', ''))
                engagement = self._calculate_engagement_score(post.metrics)
                
                if content_length < 100:
                    length_buckets["short"].append(engagement)
                elif content_length < 200:
                    length_buckets["medium"].append(engagement)
                else:
                    length_buckets["long"].append(engagement)
        
        # Calculate averages
        length_performance = {}
        for bucket, engagements in length_buckets.items():
            if engagements:
                length_performance[bucket] = sum(engagements) / len(engagements)
        
        if length_performance:
            best_length = max(length_performance, key=length_performance.get)
            return {
                "best_length_category": best_length,
                "performance_by_length": length_performance
            }
        
        return {}
    
    def _analyze_emoji_patterns(self, posts: List) -> Dict:
        """Analyze emoji usage effectiveness."""
        with_emoji = []
        without_emoji = []
        
        for post in posts:
            if hasattr(post, 'content') and hasattr(post, 'metrics'):
                text = post.content.get('text', '')
                engagement = self._calculate_engagement_score(post.metrics)
                
                # Simple emoji detection
                if any(ord(char) > 127 for char in text):
                    with_emoji.append(engagement)
                else:
                    without_emoji.append(engagement)
        
        result = {}
        if with_emoji:
            result["with_emoji_avg"] = sum(with_emoji) / len(with_emoji)
        if without_emoji:
            result["without_emoji_avg"] = sum(without_emoji) / len(without_emoji)
        
        if with_emoji and without_emoji:
            result["emoji_boost"] = result["with_emoji_avg"] / result["without_emoji_avg"]
            result["recommendation"] = "use_emojis" if result["emoji_boost"] > 1.1 else "minimal_emojis"
        
        return result
    
    def _analyze_hashtag_patterns(self, posts: List) -> Dict:
        """Analyze hashtag effectiveness."""
        hashtag_performance = {}
        
        for post in posts:
            if hasattr(post, 'content') and hasattr(post, 'metrics'):
                text = post.content.get('text', '')
                engagement = self._calculate_engagement_score(post.metrics)
                
                # Extract hashtags
                import re
                hashtags = re.findall(r'#\w+', text)
                
                for hashtag in hashtags:
                    if hashtag not in hashtag_performance:
                        hashtag_performance[hashtag] = []
                    hashtag_performance[hashtag].append(engagement)
        
        # Calculate averages and sort by performance
        hashtag_averages = {}
        for hashtag, engagements in hashtag_performance.items():
            if len(engagements) >= 2:  # Only include hashtags used multiple times
                hashtag_averages[hashtag] = sum(engagements) / len(engagements)
        
        # Sort by performance
        sorted_hashtags = sorted(hashtag_averages.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "top_hashtags": sorted_hashtags[:5],
            "hashtag_performance": hashtag_averages
        }
    
    def _analyze_cta_patterns(self, posts: List) -> Dict:
        """Analyze call-to-action effectiveness."""
        cta_patterns = {
            "try": [], "learn": [], "check": [], "get": [], "join": [],
            "download": [], "visit": [], "discover": [], "none": []
        }
        
        for post in posts:
            if hasattr(post, 'content') and hasattr(post, 'metrics'):
                text = post.content.get('text', '').lower()
                engagement = self._calculate_engagement_score(post.metrics)
                
                # Classify CTA type
                cta_type = "none"
                for pattern in cta_patterns.keys():
                    if pattern in text and pattern != "none":
                        cta_type = pattern
                        break
                
                cta_patterns[cta_type].append(engagement)
        
        # Calculate averages
        cta_performance = {}
        for cta_type, engagements in cta_patterns.items():
            if engagements:
                cta_performance[cta_type] = sum(engagements) / len(engagements)
        
        if cta_performance:
            best_cta = max(cta_performance, key=cta_performance.get)
            return {
                "best_cta_type": best_cta,
                "cta_performance": cta_performance
            }
        
        return {}
    
    def _calculate_engagement_score(self, metrics: Dict) -> float:
        """Calculate normalized engagement score."""
        if not metrics:
            return 0.0
        
        # Weight different engagement types
        weights = {
            "likes": 1.0,
            "retweets": 2.0,
            "replies": 3.0,
            "clicks": 1.5,
            "shares": 2.0,
            "comments": 3.0
        }
        
        total_score = 0.0
        for metric, value in metrics.items():
            if metric in weights and isinstance(value, (int, float)):
                total_score += value * weights[metric]
        
        return total_score
    
    async def _generate_content_variants(self, config: CampaignConfig, platform: str, insights: Dict) -> List[Dict]:
        """Generate multiple content variants for testing."""
        
        variants = []
        
        # Base variant (original style)
        base_variant = await self._generate_base_variant(config, platform)
        variants.append({
            "type": "base",
            "content": base_variant,
            "optimization_factors": []
        })
        
        # Optimized variants based on insights
        if insights.get("confidence") != "low":
            patterns = insights.get("patterns", {})
            
            # Length-optimized variant
            if "length" in patterns:
                length_variant = await self._generate_length_optimized_variant(config, platform, patterns["length"])
                variants.append({
                    "type": "length_optimized",
                    "content": length_variant,
                    "optimization_factors": ["length"]
                })
            
            # Emoji-optimized variant
            if "emojis" in patterns:
                emoji_variant = await self._generate_emoji_optimized_variant(config, platform, patterns["emojis"])
                variants.append({
                    "type": "emoji_optimized", 
                    "content": emoji_variant,
                    "optimization_factors": ["emojis"]
                })
            
            # Hashtag-optimized variant
            if "hashtags" in patterns:
                hashtag_variant = await self._generate_hashtag_optimized_variant(config, platform, patterns["hashtags"])
                variants.append({
                    "type": "hashtag_optimized",
                    "content": hashtag_variant,
                    "optimization_factors": ["hashtags"]
                })
            
            # CTA-optimized variant
            if "call_to_action" in patterns:
                cta_variant = await self._generate_cta_optimized_variant(config, platform, patterns["call_to_action"])
                variants.append({
                    "type": "cta_optimized",
                    "content": cta_variant,
                    "optimization_factors": ["call_to_action"]
                })
        
        # Always include a high-performing template variant
        template_variant = await self._generate_template_variant(config, platform)
        variants.append({
            "type": "template",
            "content": template_variant,
            "optimization_factors": ["template"]
        })
        
        return variants
    
    async def _generate_base_variant(self, config: CampaignConfig, platform: str) -> Dict:
        """Generate base content variant."""
        from ..content.generator import ContentGenerator
        
        # Use existing content generator
        content_generator = ContentGenerator({})  # Credentials handled elsewhere
        return await content_generator.generate_content(config, platform)
    
    async def _generate_length_optimized_variant(self, config: CampaignConfig, platform: str, length_insights: Dict) -> Dict:
        """Generate content optimized for length."""
        
        best_length = length_insights.get("best_length_category", "medium")
        
        # Modify config for optimal length
        optimized_config = config.copy()
        if hasattr(optimized_config, 'content') and optimized_config.content:
            if best_length == "short":
                optimized_config.content.max_length = 120
            elif best_length == "medium":
                optimized_config.content.max_length = 180
            else:  # long
                optimized_config.content.max_length = 280
        
        return await self._generate_base_variant(optimized_config, platform)
    
    async def _generate_emoji_optimized_variant(self, config: CampaignConfig, platform: str, emoji_insights: Dict) -> Dict:
        """Generate content optimized for emoji usage."""
        
        base_content = await self._generate_base_variant(config, platform)
        
        recommendation = emoji_insights.get("recommendation", "use_emojis")
        
        if recommendation == "use_emojis":
            # Add strategic emojis
            text = base_content.get("text", "")
            optimized_text = self._add_strategic_emojis(text)
            base_content["text"] = optimized_text
        elif recommendation == "minimal_emojis":
            # Remove excessive emojis
            text = base_content.get("text", "")
            optimized_text = self._reduce_emojis(text)
            base_content["text"] = optimized_text
        
        return base_content
    
    async def _generate_hashtag_optimized_variant(self, config: CampaignConfig, platform: str, hashtag_insights: Dict) -> Dict:
        """Generate content with optimized hashtags."""
        
        base_content = await self._generate_base_variant(config, platform)
        
        top_hashtags = hashtag_insights.get("top_hashtags", [])
        
        if top_hashtags:
            # Replace hashtags with top-performing ones
            text = base_content.get("text", "")
            
            # Remove existing hashtags
            import re
            text_without_hashtags = re.sub(r'#\w+', '', text).strip()
            
            # Add top-performing hashtags
            selected_hashtags = [tag for tag, _ in top_hashtags[:3]]
            hashtag_string = " " + " ".join(selected_hashtags)
            
            base_content["text"] = text_without_hashtags + hashtag_string
        
        return base_content
    
    async def _generate_cta_optimized_variant(self, config: CampaignConfig, platform: str, cta_insights: Dict) -> Dict:
        """Generate content with optimized call-to-action."""
        
        base_content = await self._generate_base_variant(config, platform)
        
        best_cta_type = cta_insights.get("best_cta_type", "learn")
        
        # CTA templates
        cta_templates = {
            "try": ["Try it now!", "Give it a try!", "Try it free!"],
            "learn": ["Learn more!", "Discover more!", "Find out more!"],
            "check": ["Check it out!", "Take a look!", "See for yourself!"],
            "get": ["Get started!", "Get yours now!", "Get it today!"],
            "join": ["Join us!", "Join now!", "Be part of it!"],
            "download": ["Download now!", "Get the app!", "Install today!"],
            "visit": ["Visit our site!", "Check our website!", "See more online!"],
            "discover": ["Discover now!", "Explore more!", "Uncover the details!"]
        }
        
        if best_cta_type in cta_templates:
            cta_options = cta_templates[best_cta_type]
            selected_cta = random.choice(cta_options)
            
            # Replace existing CTA or add one
            text = base_content.get("text", "")
            # Simple CTA replacement logic
            base_content["text"] = f"{text.rstrip()} {selected_cta}"
        
        return base_content
    
    async def _generate_template_variant(self, config: CampaignConfig, platform: str) -> Dict:
        """Generate content using high-performing templates."""
        
        # Template-based content generation
        templates = {
            "announcement": "🚀 Introducing {name} - {concept}! {action}",
            "feature": "✨ New in {name}: {concept}. {action}",
            "update": "📢 {name} update: {concept}! {action}",
            "launch": "🎉 {name} is live! {concept}. {action}"
        }
        
        template_key = random.choice(list(templates.keys()))
        template = templates[template_key]
        
        # Fill template with config data
        filled_template = template.format(
            name=config.name or "Our Product",
            concept=config.concept or "Amazing new features",
            action=getattr(config.content, 'action', 'Learn more!') if config.content else 'Learn more!'
        )
        
        return {
            "text": filled_template,
            "template_used": template_key
        }
    
    def _add_strategic_emojis(self, text: str) -> str:
        """Add strategic emojis to improve engagement."""
        
        emoji_map = {
            "new": "🆕", "launch": "🚀", "update": "📢", "feature": "✨",
            "awesome": "🔥", "great": "👍", "amazing": "🤩", "free": "🎁"
        }
        
        # Add emojis based on keywords
        for keyword, emoji in emoji_map.items():
            if keyword in text.lower() and emoji not in text:
                text = text.replace(keyword, f"{keyword} {emoji}", 1)
                break
        
        return text
    
    def _reduce_emojis(self, text: str) -> str:
        """Reduce excessive emoji usage."""
        
        # Simple emoji removal (remove characters with high unicode values)
        import re
        # Remove repeated emojis
        text = re.sub(r'([\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF])\1+', r'\1', text)
        
        return text
    
    def _select_optimal_variant(self, variants: List[Dict], insights: Dict) -> Dict:
        """Select the most promising variant."""
        
        confidence = insights.get("confidence", "low")
        
        if confidence == "low":
            # Use base variant for low confidence
            return next((v for v in variants if v["type"] == "base"), variants[0])
        
        elif confidence == "medium":
            # Prefer optimized variants but not too aggressive
            for variant in variants:
                if variant["type"] in ["length_optimized", "emoji_optimized"]:
                    return variant
            return variants[0]
        
        else:  # high confidence
            # Use most heavily optimized variant
            optimized_variants = [v for v in variants if len(v["optimization_factors"]) > 0]
            if optimized_variants:
                # Sort by number of optimization factors
                best_variant = max(optimized_variants, key=lambda x: len(x["optimization_factors"]))
                return best_variant
        
        return variants[0]
    
    def _log_optimization_decision(self, platform: str, variants: List[Dict], selected: Dict, insights: Dict):
        """Log optimization decision for future analysis."""
        
        decision_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "platform": platform,
            "variants_generated": len(variants),
            "selected_variant": selected["type"],
            "optimization_factors": selected["optimization_factors"],
            "insights_confidence": insights.get("confidence"),
            "sample_size": insights.get("sample_size", 0)
        }
        
        if "insights" not in self.optimization_history:
            self.optimization_history["insights"] = []
        
        self.optimization_history["insights"].append(decision_log)
        
        # Keep only last 100 decisions
        self.optimization_history["insights"] = self.optimization_history["insights"][-100:]
        
        self._save_optimization_history()
    
    async def setup_ab_test(self, config: CampaignConfig, test_config: Dict) -> str:
        """Set up an A/B test experiment."""
        
        experiment_id = hashlib.md5(f"{config.name}{datetime.utcnow()}".encode()).hexdigest()[:8]
        
        experiment = {
            "id": experiment_id,
            "name": test_config.get("name", f"Test-{experiment_id}"),
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=test_config.get("duration_days", 7))).isoformat(),
            "status": "active",
            "variants": test_config.get("variants", []),
            "metric": test_config.get("metric", "engagement_rate"),
            "traffic_split": test_config.get("traffic_split", [50, 50]),
            "results": {}
        }
        
        if "experiments" not in self.optimization_history:
            self.optimization_history["experiments"] = []
        
        self.optimization_history["experiments"].append(experiment)
        self._save_optimization_history()
        
        return experiment_id
    
    def get_ab_test_variant(self, experiment_id: str) -> Optional[Dict]:
        """Get the appropriate variant for an A/B test."""
        
        experiment = next(
            (exp for exp in self.optimization_history.get("experiments", []) 
             if exp["id"] == experiment_id and exp["status"] == "active"),
            None
        )
        
        if not experiment:
            return None
        
        # Check if experiment has ended
        end_date = datetime.fromisoformat(experiment["end_date"])
        if datetime.utcnow() > end_date:
            experiment["status"] = "completed"
            self._save_optimization_history()
            return None
        
        # Random variant selection based on traffic split
        traffic_split = experiment.get("traffic_split", [50, 50])
        variants = experiment.get("variants", [])
        
        if len(variants) != len(traffic_split):
            return None
        
        # Weighted random selection
        total_weight = sum(traffic_split)
        random_value = random.random() * total_weight
        
        cumulative_weight = 0
        for i, weight in enumerate(traffic_split):
            cumulative_weight += weight
            if random_value <= cumulative_weight:
                return variants[i] if i < len(variants) else variants[0]
        
        return variants[0]
    
    def record_ab_test_result(self, experiment_id: str, variant_id: str, metrics: Dict):
        """Record A/B test result."""
        
        experiment = next(
            (exp for exp in self.optimization_history.get("experiments", []) 
             if exp["id"] == experiment_id),
            None
        )
        
        if not experiment:
            return
        
        if "results" not in experiment:
            experiment["results"] = {}
        
        if variant_id not in experiment["results"]:
            experiment["results"][variant_id] = []
        
        experiment["results"][variant_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        })
        
        self._save_optimization_history()
    
    def analyze_ab_test_results(self, experiment_id: str) -> Dict:
        """Analyze A/B test results and determine winner."""
        
        experiment = next(
            (exp for exp in self.optimization_history.get("experiments", []) 
             if exp["id"] == experiment_id),
            None
        )
        
        if not experiment or "results" not in experiment:
            return {"error": "Experiment not found or no results"}
        
        results = experiment["results"]
        metric = experiment.get("metric", "engagement_rate")
        
        variant_performance = {}
        
        for variant_id, variant_results in results.items():
            if not variant_results:
                continue
            
            # Calculate average performance for the metric
            metric_values = []
            for result in variant_results:
                metrics = result.get("metrics", {})
                if metric in metrics:
                    metric_values.append(metrics[metric])
            
            if metric_values:
                variant_performance[variant_id] = {
                    "average": sum(metric_values) / len(metric_values),
                    "count": len(metric_values),
                    "total": sum(metric_values)
                }
        
        if not variant_performance:
            return {"error": "No valid results found"}
        
        # Determine winner
        winner = max(variant_performance.items(), key=lambda x: x[1]["average"])
        
        # Calculate statistical significance (simplified)
        confidence = "high" if winner[1]["count"] >= 30 else "medium" if winner[1]["count"] >= 10 else "low"
        
        return {
            "experiment_id": experiment_id,
            "metric": metric,
            "winner": {
                "variant_id": winner[0],
                "performance": winner[1]
            },
            "all_variants": variant_performance,
            "confidence": confidence,
            "recommendation": f"Use variant {winner[0]}" if confidence != "low" else "Continue testing"
        }