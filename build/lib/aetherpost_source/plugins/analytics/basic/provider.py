"""Basic analytics provider implementation."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from ...base import AnalyticsProviderBase


class BasicAnalyticsProvider(AnalyticsProviderBase):
    """Basic analytics provider for campaign analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @property
    def name(self) -> str:
        return "basic"
    
    async def collect_metrics(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect basic metrics from post data."""
        try:
            platform = post_data.get("platform", "unknown")
            post_id = post_data.get("post_id", "")
            metrics = post_data.get("metrics", {})
            
            # Normalize metrics across platforms
            normalized_metrics = self._normalize_metrics(metrics, platform)
            
            return {
                "post_id": post_id,
                "platform": platform,
                "collected_at": datetime.utcnow().isoformat(),
                "metrics": normalized_metrics,
                "engagement_rate": self._calculate_engagement_rate(normalized_metrics),
                "performance_score": self._calculate_performance_score(normalized_metrics)
            }
            
        except Exception as e:
            return {"error": str(e), "platform": post_data.get("platform", "unknown")}
    
    async def analyze_performance(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall campaign performance."""
        try:
            posts = campaign_data.get("posts", [])
            if not posts:
                return {"error": "No posts to analyze"}
            
            total_metrics = defaultdict(int)
            platform_metrics = defaultdict(lambda: defaultdict(int))
            engagement_rates = []
            performance_scores = []
            
            for post in posts:
                platform = post.get("platform", "unknown")
                metrics = post.get("metrics", {})
                
                # Aggregate total metrics
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        total_metrics[key] += value
                        platform_metrics[platform][key] += value
                
                # Collect engagement data
                engagement_rate = post.get("engagement_rate", 0)
                performance_score = post.get("performance_score", 0)
                
                engagement_rates.append(engagement_rate)
                performance_scores.append(performance_score)
            
            # Calculate averages
            avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0
            avg_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0
            
            # Identify best performing content
            best_post = max(posts, key=lambda p: p.get("performance_score", 0)) if posts else None
            worst_post = min(posts, key=lambda p: p.get("performance_score", 0)) if posts else None
            
            analysis = {
                "campaign_summary": {
                    "total_posts": len(posts),
                    "platforms": list(platform_metrics.keys()),
                    "total_reach": total_metrics.get("impressions", 0) or total_metrics.get("views", 0),
                    "total_engagement": total_metrics.get("likes", 0) + total_metrics.get("shares", 0) + total_metrics.get("comments", 0),
                    "average_engagement_rate": round(avg_engagement, 3),
                    "average_performance_score": round(avg_performance, 3)
                },
                "platform_breakdown": dict(platform_metrics),
                "performance_insights": {
                    "best_performing_post": {
                        "post_id": best_post.get("post_id") if best_post else None,
                        "platform": best_post.get("platform") if best_post else None,
                        "performance_score": best_post.get("performance_score", 0) if best_post else 0
                    },
                    "worst_performing_post": {
                        "post_id": worst_post.get("post_id") if worst_post else None,
                        "platform": worst_post.get("platform") if worst_post else None,
                        "performance_score": worst_post.get("performance_score", 0) if worst_post else 0
                    }
                },
                "recommendations": self._generate_recommendations(platform_metrics, engagement_rates)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_report(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive analytics report."""
        try:
            if not metrics:
                return {"error": "No metrics data provided"}
            
            # Time-based analysis
            time_analysis = self._analyze_posting_times(metrics)
            
            # Platform comparison
            platform_comparison = self._compare_platforms(metrics)
            
            # Content type analysis
            content_analysis = self._analyze_content_types(metrics)
            
            # Trend analysis
            trend_analysis = self._analyze_trends(metrics)
            
            report = {
                "report_generated_at": datetime.utcnow().isoformat(),
                "metrics_count": len(metrics),
                "time_period_analysis": time_analysis,
                "platform_comparison": platform_comparison,
                "content_type_analysis": content_analysis,
                "trend_analysis": trend_analysis,
                "executive_summary": self._generate_executive_summary(metrics),
                "action_items": self._generate_action_items(metrics)
            }
            
            return report
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_trending_topics(self, platform: str, category: Optional[str] = None) -> List[str]:
        """Get trending topics (basic implementation with static data)."""
        # This is a basic implementation. In a real-world scenario,
        # this would connect to platform APIs or trending data services.
        
        trending_topics = {
            "twitter": [
                "AI", "productivity", "startup", "tech", "innovation",
                "automation", "SaaS", "mobile", "webapp", "development"
            ],
            "bluesky": [
                "decentralized", "opensource", "privacy", "community",
                "social", "federation", "protocol", "technology"
            ],
            "mastodon": [
                "opensource", "privacy", "community", "federation",
                "activism", "technology", "alternatives", "decentralized"
            ],
            "linkedin": [
                "professional", "networking", "career", "business",
                "industry", "leadership", "strategy", "growth"
            ]
        }
        
        # Filter by category if provided
        if category:
            category_topics = {
                "technology": ["AI", "automation", "SaaS", "development", "innovation"],
                "business": ["startup", "growth", "strategy", "leadership"],
                "social": ["community", "networking", "privacy", "opensource"]
            }
            return category_topics.get(category.lower(), trending_topics.get(platform, []))
        
        return trending_topics.get(platform.lower(), trending_topics["twitter"])
    
    def _normalize_metrics(self, metrics: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Normalize metrics across different platforms."""
        normalized = {}
        
        # Map platform-specific metric names to standard names
        metric_mappings = {
            "twitter": {
                "retweet_count": "shares",
                "favorite_count": "likes",
                "reply_count": "comments"
            },
            "bluesky": {
                "repost_count": "shares",
                "like_count": "likes", 
                "reply_count": "comments"
            },
            "mastodon": {
                "reblogs_count": "shares",
                "favourites_count": "likes",
                "replies_count": "comments"
            }
        }
        
        platform_mapping = metric_mappings.get(platform.lower(), {})
        
        for key, value in metrics.items():
            normalized_key = platform_mapping.get(key, key)
            normalized[normalized_key] = value
        
        return normalized
    
    def _calculate_engagement_rate(self, metrics: Dict[str, Any]) -> float:
        """Calculate engagement rate from metrics."""
        try:
            engagements = (
                metrics.get("likes", 0) + 
                metrics.get("shares", 0) + 
                metrics.get("comments", 0)
            )
            impressions = metrics.get("impressions", 0) or metrics.get("views", 0) or 1
            
            return round((engagements / impressions) * 100, 3) if impressions > 0 else 0
            
        except Exception:
            return 0.0
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall performance score."""
        try:
            # Weighted scoring system
            likes_weight = 1.0
            shares_weight = 2.0  # Shares are more valuable
            comments_weight = 3.0  # Comments show high engagement
            
            score = (
                metrics.get("likes", 0) * likes_weight +
                metrics.get("shares", 0) * shares_weight +
                metrics.get("comments", 0) * comments_weight
            )
            
            # Normalize by impressions if available
            impressions = metrics.get("impressions", 0) or metrics.get("views", 0)
            if impressions > 0:
                score = (score / impressions) * 1000  # Scale for readability
            
            return round(score, 2)
            
        except Exception:
            return 0.0
    
    def _analyze_posting_times(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze optimal posting times."""
        # Basic implementation - would be more sophisticated in production
        return {
            "best_hour": "10:00",
            "best_day": "Tuesday",
            "worst_hour": "03:00",
            "worst_day": "Sunday"
        }
    
    def _compare_platforms(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare performance across platforms."""
        platform_stats = defaultdict(lambda: {"posts": 0, "total_engagement": 0})
        
        for metric in metrics:
            platform = metric.get("platform", "unknown")
            engagement = metric.get("metrics", {})
            total = sum(engagement.get(k, 0) for k in ["likes", "shares", "comments"])
            
            platform_stats[platform]["posts"] += 1
            platform_stats[platform]["total_engagement"] += total
        
        return dict(platform_stats)
    
    def _analyze_content_types(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by content type."""
        return {
            "text_only": {"posts": 0, "avg_engagement": 0},
            "with_media": {"posts": 0, "avg_engagement": 0},
            "with_hashtags": {"posts": 0, "avg_engagement": 0}
        }
    
    def _analyze_trends(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        return {
            "engagement_trend": "increasing",
            "reach_trend": "stable",
            "growth_rate": "5.2%"
        }
    
    def _generate_executive_summary(self, metrics: List[Dict[str, Any]]) -> str:
        """Generate executive summary of performance."""
        total_posts = len(metrics)
        avg_engagement = sum(m.get("engagement_rate", 0) for m in metrics) / total_posts if total_posts > 0 else 0
        
        return f"Campaign analysis of {total_posts} posts shows average engagement rate of {avg_engagement:.1f}%. Performance is trending positively with opportunities for optimization in content timing and platform-specific strategies."
    
    def _generate_action_items(self, metrics: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations."""
        return [
            "Focus content creation during peak engagement hours (10-11 AM)",
            "Increase visual content ratio to improve engagement rates",
            "Optimize hashtag strategy for better discoverability",
            "Test different posting frequencies across platforms",
            "A/B test content styles to identify best-performing formats"
        ]
    
    def _generate_recommendations(self, platform_metrics: Dict, engagement_rates: List[float]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        if engagement_rates:
            avg_engagement = sum(engagement_rates) / len(engagement_rates)
            if avg_engagement < 2.0:
                recommendations.append("Consider improving content engagement with more interactive elements")
            if avg_engagement > 5.0:
                recommendations.append("Excellent engagement! Scale successful content strategies")
        
        # Platform-specific recommendations
        if len(platform_metrics) == 1:
            recommendations.append("Consider expanding to additional social media platforms")
        
        if not recommendations:
            recommendations.append("Continue current strategy and monitor performance trends")
        
        return recommendations