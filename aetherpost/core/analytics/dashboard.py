"""Advanced analytics dashboard and insights generation."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import statistics
from dataclasses import dataclass, asdict

from ..state.manager import StateManager


@dataclass
class EngagementMetrics:
    """Engagement metrics for a specific time period."""
    likes: int = 0
    shares: int = 0
    comments: int = 0
    clicks: int = 0
    impressions: int = 0
    reach: int = 0
    
    @property
    def total_engagement(self) -> int:
        return self.likes + self.shares + self.comments + self.clicks
    
    @property
    def engagement_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return (self.total_engagement / self.impressions) * 100


@dataclass
class PlatformInsights:
    """Insights for a specific platform."""
    platform: str
    total_posts: int
    total_engagement: int
    avg_engagement_per_post: float
    best_performing_post: Optional[Dict]
    worst_performing_post: Optional[Dict]
    optimal_posting_times: List[int]
    top_hashtags: List[Tuple[str, float]]
    engagement_trend: List[float]  # Last 30 days
    audience_growth: float  # Percentage change


@dataclass
class ContentInsights:
    """Content performance insights."""
    optimal_length: int
    best_style: str
    best_cta_type: str
    emoji_effectiveness: float
    hashtag_performance: Dict[str, float]
    content_themes: List[Tuple[str, float]]  # Theme and performance score


@dataclass
class TimeInsights:
    """Time-based posting insights."""
    best_days: List[str]
    best_hours: List[int]
    worst_days: List[str]
    worst_hours: List[int]
    seasonal_trends: Dict[str, float]


@dataclass
class CompetitorInsights:
    """Competitive analysis insights."""
    industry_benchmarks: Dict[str, float]
    performance_vs_industry: Dict[str, float]
    content_gap_analysis: List[str]
    opportunity_areas: List[str]


class AnalyticsDashboard:
    """Advanced analytics dashboard for AetherPost campaigns."""
    
    def __init__(self):
        self.state_manager = StateManager()
        self.analytics_cache = self._load_analytics_cache()
    
    def _load_analytics_cache(self) -> Dict:
        """Load cached analytics data."""
        cache_file = Path(".aetherpost/analytics_cache.json")
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {"last_updated": None, "cached_insights": {}}
    
    def _save_analytics_cache(self):
        """Save analytics cache to disk."""
        cache_file = Path(".aetherpost/analytics_cache.json")
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, "w") as f:
            json.dump(self.analytics_cache, f, indent=2, default=str)
    
    def generate_comprehensive_report(self, days: int = 30) -> Dict:
        """Generate comprehensive analytics report."""
        
        state = self.state_manager.load_state()
        if not state or not state.posts:
            return {"error": "No data available for analysis"}
        
        # Filter posts by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_posts = [
            post for post in state.posts 
            if post.created_at >= cutoff_date
        ]
        
        if not recent_posts:
            return {"error": f"No posts found in the last {days} days"}
        
        # Generate insights
        platform_insights = self._generate_platform_insights(recent_posts)
        content_insights = self._generate_content_insights(recent_posts)
        time_insights = self._generate_time_insights(recent_posts)
        
        # Overall metrics
        overall_metrics = self._calculate_overall_metrics(recent_posts)
        
        # Competitive insights (if available)
        competitive_insights = self._generate_competitive_insights(recent_posts)
        
        # Recommendations
        recommendations = self._generate_recommendations(
            platform_insights, content_insights, time_insights
        )
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "period": f"Last {days} days",
            "overall_metrics": overall_metrics,
            "platform_insights": {
                platform: asdict(insights) 
                for platform, insights in platform_insights.items()
            },
            "content_insights": asdict(content_insights),
            "time_insights": asdict(time_insights),
            "competitive_insights": asdict(competitive_insights) if competitive_insights else None,
            "recommendations": recommendations,
            "data_quality": self._assess_data_quality(recent_posts)
        }
        
        # Cache the report
        self.analytics_cache["last_updated"] = datetime.utcnow().isoformat()
        self.analytics_cache["cached_insights"] = report
        self._save_analytics_cache()
        
        return report
    
    def _generate_platform_insights(self, posts: List) -> Dict[str, PlatformInsights]:
        """Generate insights for each platform."""
        platform_insights = {}
        
        # Group posts by platform
        platforms = {}
        for post in posts:
            if post.platform not in platforms:
                platforms[post.platform] = []
            platforms[post.platform].append(post)
        
        for platform, platform_posts in platforms.items():
            # Calculate metrics
            total_posts = len(platform_posts)
            
            engagements = []
            for post in platform_posts:
                if hasattr(post, 'metrics') and post.metrics:
                    engagement = self._calculate_post_engagement(post.metrics)
                    engagements.append(engagement)
            
            total_engagement = sum(engagements)
            avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
            
            # Find best and worst performing posts
            best_post = None
            worst_post = None
            
            if engagements:
                max_engagement = max(engagements)
                min_engagement = min(engagements)
                
                for i, post in enumerate(platform_posts):
                    if engagements[i] == max_engagement:
                        best_post = self._serialize_post(post)
                    elif engagements[i] == min_engagement:
                        worst_post = self._serialize_post(post)
            
            # Optimal posting times
            optimal_times = self._find_optimal_posting_times(platform_posts)
            
            # Top hashtags
            top_hashtags = self._analyze_hashtag_performance(platform_posts)
            
            # Engagement trend (last 30 days)
            engagement_trend = self._calculate_engagement_trend(platform_posts)
            
            # Audience growth (simplified calculation)
            audience_growth = self._estimate_audience_growth(platform_posts)
            
            platform_insights[platform] = PlatformInsights(
                platform=platform,
                total_posts=total_posts,
                total_engagement=total_engagement,
                avg_engagement_per_post=avg_engagement,
                best_performing_post=best_post,
                worst_performing_post=worst_post,
                optimal_posting_times=optimal_times,
                top_hashtags=top_hashtags,
                engagement_trend=engagement_trend,
                audience_growth=audience_growth
            )
        
        return platform_insights
    
    def _generate_content_insights(self, posts: List) -> ContentInsights:
        """Generate content performance insights."""
        
        # Analyze content length effectiveness
        length_performance = {}
        style_performance = {}
        cta_performance = {}
        emoji_scores = []
        hashtag_performance = {}
        
        for post in posts:
            if not hasattr(post, 'content') or not post.content:
                continue
                
            engagement = self._calculate_post_engagement(getattr(post, 'metrics', {}))
            content_text = post.content.get('text', '')
            
            # Length analysis
            length = len(content_text)
            length_bucket = self._categorize_length(length)
            if length_bucket not in length_performance:
                length_performance[length_bucket] = []
            length_performance[length_bucket].append(engagement)
            
            # Style analysis (if available in post metadata)
            style = getattr(post, 'style', None)
            if style:
                if style not in style_performance:
                    style_performance[style] = []
                style_performance[style].append(engagement)
            
            # CTA analysis
            cta_type = self._extract_cta_type(content_text)
            if cta_type not in cta_performance:
                cta_performance[cta_type] = []
            cta_performance[cta_type].append(engagement)
            
            # Emoji analysis
            emoji_count = self._count_emojis(content_text)
            emoji_scores.append((emoji_count, engagement))
            
            # Hashtag analysis
            hashtags = self._extract_hashtags(content_text)
            for hashtag in hashtags:
                if hashtag not in hashtag_performance:
                    hashtag_performance[hashtag] = []
                hashtag_performance[hashtag].append(engagement)
        
        # Find optimal values
        optimal_length = self._find_optimal_length(length_performance)
        best_style = self._find_best_performer(style_performance)
        best_cta = self._find_best_performer(cta_performance)
        emoji_effectiveness = self._analyze_emoji_effectiveness(emoji_scores)
        
        # Process hashtag performance
        hashtag_avg_performance = {
            tag: statistics.mean(scores) 
            for tag, scores in hashtag_performance.items() 
            if len(scores) >= 2
        }
        
        # Content themes (simplified)
        content_themes = self._identify_content_themes(posts)
        
        return ContentInsights(
            optimal_length=optimal_length,
            best_style=best_style,
            best_cta_type=best_cta,
            emoji_effectiveness=emoji_effectiveness,
            hashtag_performance=hashtag_avg_performance,
            content_themes=content_themes
        )
    
    def _generate_time_insights(self, posts: List) -> TimeInsights:
        """Generate time-based posting insights."""
        
        day_performance = {}
        hour_performance = {}
        
        for post in posts:
            if not hasattr(post, 'created_at'):
                continue
                
            engagement = self._calculate_post_engagement(getattr(post, 'metrics', {}))
            
            # Day analysis
            day_name = post.created_at.strftime('%A')
            if day_name not in day_performance:
                day_performance[day_name] = []
            day_performance[day_name].append(engagement)
            
            # Hour analysis
            hour = post.created_at.hour
            if hour not in hour_performance:
                hour_performance[hour] = []
            hour_performance[hour].append(engagement)
        
        # Calculate averages and sort
        day_averages = {
            day: statistics.mean(scores) 
            for day, scores in day_performance.items()
        }
        
        hour_averages = {
            hour: statistics.mean(scores) 
            for hour, scores in hour_performance.items()
        }
        
        # Sort by performance
        sorted_days = sorted(day_averages.items(), key=lambda x: x[1], reverse=True)
        sorted_hours = sorted(hour_averages.items(), key=lambda x: x[1], reverse=True)
        
        best_days = [day for day, _ in sorted_days[:3]]
        worst_days = [day for day, _ in sorted_days[-2:]]
        best_hours = [hour for hour, _ in sorted_hours[:3]]
        worst_hours = [hour for hour, _ in sorted_hours[-2:]]
        
        # Seasonal trends (simplified)
        seasonal_trends = self._analyze_seasonal_trends(posts)
        
        return TimeInsights(
            best_days=best_days,
            best_hours=best_hours,
            worst_days=worst_days,
            worst_hours=worst_hours,
            seasonal_trends=seasonal_trends
        )
    
    def _generate_competitive_insights(self, posts: List) -> Optional[CompetitorInsights]:
        """Generate competitive analysis insights."""
        
        # This would require external data sources
        # For now, return industry benchmarks based on platform
        
        platforms = set(post.platform for post in posts)
        
        # Industry benchmarks (these would come from external APIs)
        benchmarks = {
            "twitter": {"avg_engagement_rate": 0.045, "avg_reach": 1000},
            "linkedin": {"avg_engagement_rate": 0.054, "avg_reach": 500},
            "bluesky": {"avg_engagement_rate": 0.035, "avg_reach": 300}
        }
        
        industry_benchmarks = {}
        performance_vs_industry = {}
        
        for platform in platforms:
            if platform in benchmarks:
                industry_benchmarks[platform] = benchmarks[platform]
                
                # Calculate our performance vs industry
                our_posts = [p for p in posts if p.platform == platform]
                our_engagement_rate = self._calculate_avg_engagement_rate(our_posts)
                
                performance_vs_industry[platform] = {
                    "engagement_rate_ratio": our_engagement_rate / benchmarks[platform]["avg_engagement_rate"]
                }
        
        if not industry_benchmarks:
            return None
        
        # Content gap analysis (simplified)
        content_gaps = [
            "Video content opportunities",
            "User-generated content potential",
            "Interactive content exploration"
        ]
        
        # Opportunity areas
        opportunities = [
            "Posting frequency optimization",
            "Cross-platform content adaptation",
            "Community engagement improvement"
        ]
        
        return CompetitorInsights(
            industry_benchmarks=industry_benchmarks,
            performance_vs_industry=performance_vs_industry,
            content_gap_analysis=content_gaps,
            opportunity_areas=opportunities
        )
    
    def _generate_recommendations(self, platform_insights: Dict, content_insights: ContentInsights, time_insights: TimeInsights) -> List[Dict]:
        """Generate actionable recommendations."""
        
        recommendations = []
        
        # Platform recommendations
        if platform_insights:
            best_platform = max(
                platform_insights.items(), 
                key=lambda x: x[1].avg_engagement_per_post
            )
            
            recommendations.append({
                "category": "Platform Optimization",
                "priority": "high",
                "title": f"Focus on {best_platform[0].title()}",
                "description": f"{best_platform[0].title()} shows the highest engagement rate. Consider increasing posting frequency.",
                "action": f"Increase posting frequency on {best_platform[0]}",
                "impact": "High"
            })
        
        # Content recommendations
        if content_insights.best_style:
            recommendations.append({
                "category": "Content Style",
                "priority": "medium",
                "title": f"Use '{content_insights.best_style}' style more often",
                "description": f"Posts with '{content_insights.best_style}' style perform best in your audience.",
                "action": f"Set default style to '{content_insights.best_style}'",
                "impact": "Medium"
            })
        
        if content_insights.optimal_length:
            recommendations.append({
                "category": "Content Length",
                "priority": "medium",
                "title": f"Target {content_insights.optimal_length} characters",
                "description": "This length shows optimal engagement for your audience.",
                "action": f"Adjust content to ~{content_insights.optimal_length} characters",
                "impact": "Medium"
            })
        
        # Timing recommendations
        if time_insights.best_hours:
            best_hour = time_insights.best_hours[0]
            recommendations.append({
                "category": "Timing Optimization",
                "priority": "high",
                "title": f"Post around {best_hour}:00",
                "description": f"{best_hour}:00 shows highest engagement for your audience.",
                "action": f"Schedule posts for {best_hour}:00",
                "impact": "High"
            })
        
        if time_insights.best_days:
            best_day = time_insights.best_days[0]
            recommendations.append({
                "category": "Day Optimization",
                "priority": "medium",
                "title": f"Prioritize {best_day} posts",
                "description": f"{best_day} shows highest engagement rates.",
                "action": f"Schedule important announcements on {best_day}",
                "impact": "Medium"
            })
        
        # Hashtag recommendations
        top_hashtags = sorted(
            content_insights.hashtag_performance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        if top_hashtags:
            hashtag_list = [tag for tag, _ in top_hashtags]
            recommendations.append({
                "category": "Hashtag Strategy",
                "priority": "low",
                "title": "Use high-performing hashtags",
                "description": f"These hashtags show best performance: {', '.join(hashtag_list)}",
                "action": f"Include these hashtags: {', '.join(hashtag_list)}",
                "impact": "Low"
            })
        
        return recommendations
    
    def _calculate_overall_metrics(self, posts: List) -> Dict:
        """Calculate overall metrics for the period."""
        
        total_posts = len(posts)
        total_engagement = sum(
            self._calculate_post_engagement(getattr(post, 'metrics', {}))
            for post in posts
        )
        
        avg_engagement_per_post = total_engagement / total_posts if total_posts > 0 else 0
        
        # Platform distribution
        platform_distribution = {}
        for post in posts:
            platform = post.platform
            platform_distribution[platform] = platform_distribution.get(platform, 0) + 1
        
        # Engagement distribution
        engagements = [
            self._calculate_post_engagement(getattr(post, 'metrics', {}))
            for post in posts
        ]
        
        engagement_stats = {}
        if engagements:
            engagement_stats = {
                "min": min(engagements),
                "max": max(engagements),
                "median": statistics.median(engagements),
                "std_dev": statistics.stdev(engagements) if len(engagements) > 1 else 0
            }
        
        return {
            "total_posts": total_posts,
            "total_engagement": total_engagement,
            "avg_engagement_per_post": avg_engagement_per_post,
            "platform_distribution": platform_distribution,
            "engagement_statistics": engagement_stats,
            "posting_frequency": total_posts / 30  # Posts per day
        }
    
    def _assess_data_quality(self, posts: List) -> Dict:
        """Assess the quality and completeness of data."""
        
        total_posts = len(posts)
        posts_with_metrics = sum(
            1 for post in posts 
            if hasattr(post, 'metrics') and post.metrics
        )
        
        posts_with_content = sum(
            1 for post in posts 
            if hasattr(post, 'content') and post.content
        )
        
        data_completeness = posts_with_metrics / total_posts if total_posts > 0 else 0
        content_completeness = posts_with_content / total_posts if total_posts > 0 else 0
        
        # Data quality assessment
        quality_score = (data_completeness + content_completeness) / 2
        
        if quality_score >= 0.9:
            quality_level = "Excellent"
        elif quality_score >= 0.7:
            quality_level = "Good"
        elif quality_score >= 0.5:
            quality_level = "Fair"
        else:
            quality_level = "Poor"
        
        return {
            "total_posts": total_posts,
            "posts_with_metrics": posts_with_metrics,
            "data_completeness": data_completeness,
            "content_completeness": content_completeness,
            "quality_score": quality_score,
            "quality_level": quality_level,
            "recommendations": self._get_data_quality_recommendations(quality_score)
        }
    
    def _get_data_quality_recommendations(self, quality_score: float) -> List[str]:
        """Get recommendations for improving data quality."""
        
        recommendations = []
        
        if quality_score < 0.7:
            recommendations.append("Enable analytics tracking for all platforms")
            recommendations.append("Ensure metrics are being collected properly")
        
        if quality_score < 0.5:
            recommendations.append("Check API connections for social media platforms")
            recommendations.append("Verify post content is being stored correctly")
        
        recommendations.append("Run periodic data validation checks")
        
        return recommendations
    
    # Helper methods
    def _calculate_post_engagement(self, metrics: Dict) -> float:
        """Calculate engagement score for a post."""
        if not metrics:
            return 0.0
        
        weights = {
            "likes": 1.0,
            "shares": 2.0,
            "comments": 3.0,
            "clicks": 1.5,
            "retweets": 2.0,
            "replies": 3.0
        }
        
        total_score = 0.0
        for metric, value in metrics.items():
            if metric in weights and isinstance(value, (int, float)):
                total_score += value * weights[metric]
        
        return total_score
    
    def _serialize_post(self, post) -> Dict:
        """Serialize post for JSON output."""
        return {
            "id": getattr(post, 'id', 'unknown'),
            "platform": getattr(post, 'platform', 'unknown'),
            "created_at": getattr(post, 'created_at', datetime.utcnow()).isoformat(),
            "content": getattr(post, 'content', {}),
            "metrics": getattr(post, 'metrics', {})
        }
    
    def _find_optimal_posting_times(self, posts: List) -> List[int]:
        """Find optimal posting times for a platform."""
        hour_performance = {}
        
        for post in posts:
            if hasattr(post, 'created_at'):
                hour = post.created_at.hour
                engagement = self._calculate_post_engagement(getattr(post, 'metrics', {}))
                
                if hour not in hour_performance:
                    hour_performance[hour] = []
                hour_performance[hour].append(engagement)
        
        # Calculate averages and return top 3 hours
        hour_averages = {
            hour: statistics.mean(scores) 
            for hour, scores in hour_performance.items() 
            if len(scores) >= 2
        }
        
        sorted_hours = sorted(hour_averages.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, _ in sorted_hours[:3]]
    
    def _analyze_hashtag_performance(self, posts: List) -> List[Tuple[str, float]]:
        """Analyze hashtag performance."""
        hashtag_performance = {}
        
        for post in posts:
            if hasattr(post, 'content') and post.content:
                content_text = post.content.get('text', '')
                hashtags = self._extract_hashtags(content_text)
                engagement = self._calculate_post_engagement(getattr(post, 'metrics', {}))
                
                for hashtag in hashtags:
                    if hashtag not in hashtag_performance:
                        hashtag_performance[hashtag] = []
                    hashtag_performance[hashtag].append(engagement)
        
        # Calculate averages and return top performers
        hashtag_averages = {
            tag: statistics.mean(scores) 
            for tag, scores in hashtag_performance.items() 
            if len(scores) >= 2
        }
        
        sorted_hashtags = sorted(hashtag_averages.items(), key=lambda x: x[1], reverse=True)
        return sorted_hashtags[:5]
    
    def _calculate_engagement_trend(self, posts: List) -> List[float]:
        """Calculate engagement trend over time."""
        # Group posts by day and calculate daily engagement
        daily_engagement = {}
        
        for post in posts:
            if hasattr(post, 'created_at'):
                date_key = post.created_at.date()
                engagement = self._calculate_post_engagement(getattr(post, 'metrics', {}))
                
                if date_key not in daily_engagement:
                    daily_engagement[date_key] = []
                daily_engagement[date_key].append(engagement)
        
        # Calculate daily averages
        daily_averages = {
            date: statistics.mean(scores) 
            for date, scores in daily_engagement.items()
        }
        
        # Return trend as list (last 30 days)
        sorted_days = sorted(daily_averages.items())
        return [avg for _, avg in sorted_days[-30:]]
    
    def _estimate_audience_growth(self, posts: List) -> float:
        """Estimate audience growth based on reach metrics."""
        # Simplified calculation based on reach changes
        reach_values = []
        
        for post in posts:
            if hasattr(post, 'metrics') and post.metrics:
                reach = post.metrics.get('reach', 0)
                if reach > 0:
                    reach_values.append(reach)
        
        if len(reach_values) < 2:
            return 0.0
        
        # Simple growth calculation
        early_avg = statistics.mean(reach_values[:len(reach_values)//2])
        recent_avg = statistics.mean(reach_values[len(reach_values)//2:])
        
        if early_avg == 0:
            return 0.0
        
        growth_rate = ((recent_avg - early_avg) / early_avg) * 100
        return growth_rate
    
    # Content analysis helpers
    def _categorize_length(self, length: int) -> str:
        """Categorize content length."""
        if length < 100:
            return "short"
        elif length < 200:
            return "medium"
        else:
            return "long"
    
    def _extract_cta_type(self, text: str) -> str:
        """Extract call-to-action type from text."""
        text_lower = text.lower()
        
        cta_patterns = {
            "try": ["try", "test", "demo"],
            "learn": ["learn", "discover", "find out"],
            "get": ["get", "download", "install"],
            "join": ["join", "sign up", "register"],
            "visit": ["visit", "check out", "see"],
            "buy": ["buy", "purchase", "order"]
        }
        
        for cta_type, patterns in cta_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return cta_type
        
        return "other"
    
    def _count_emojis(self, text: str) -> int:
        """Count emojis in text."""
        emoji_count = 0
        for char in text:
            if ord(char) > 127:  # Simple emoji detection
                emoji_count += 1
        return emoji_count
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        import re
        return re.findall(r'#\w+', text)
    
    def _find_optimal_length(self, length_performance: Dict) -> int:
        """Find optimal content length."""
        if not length_performance:
            return 200  # Default
        
        avg_performance = {
            category: statistics.mean(scores) 
            for category, scores in length_performance.items()
        }
        
        best_category = max(avg_performance, key=avg_performance.get)
        
        # Return representative length for category
        length_map = {"short": 80, "medium": 150, "long": 250}
        return length_map.get(best_category, 200)
    
    def _find_best_performer(self, performance_dict: Dict) -> str:
        """Find best performing item from performance dictionary."""
        if not performance_dict:
            return "unknown"
        
        avg_performance = {
            item: statistics.mean(scores) 
            for item, scores in performance_dict.items()
        }
        
        return max(avg_performance, key=avg_performance.get)
    
    def _analyze_emoji_effectiveness(self, emoji_scores: List[Tuple[int, float]]) -> float:
        """Analyze emoji effectiveness."""
        if not emoji_scores:
            return 0.0
        
        with_emoji = [score for count, score in emoji_scores if count > 0]
        without_emoji = [score for count, score in emoji_scores if count == 0]
        
        if not with_emoji or not without_emoji:
            return 0.0
        
        with_avg = statistics.mean(with_emoji)
        without_avg = statistics.mean(without_emoji)
        
        if without_avg == 0:
            return 0.0
        
        return (with_avg / without_avg - 1) * 100  # Percentage improvement
    
    def _identify_content_themes(self, posts: List) -> List[Tuple[str, float]]:
        """Identify content themes and their performance."""
        # Simplified theme identification
        themes = {
            "product": ["product", "feature", "update", "release"],
            "company": ["company", "team", "culture", "news"],
            "educational": ["how", "why", "learn", "tutorial", "guide"],
            "promotional": ["sale", "discount", "offer", "deal", "free"]
        }
        
        theme_performance = {}
        
        for post in posts:
            if hasattr(post, 'content') and post.content:
                content_text = post.content.get('text', '').lower()
                engagement = self._calculate_post_engagement(getattr(post, 'metrics', {}))
                
                for theme, keywords in themes.items():
                    if any(keyword in content_text for keyword in keywords):
                        if theme not in theme_performance:
                            theme_performance[theme] = []
                        theme_performance[theme].append(engagement)
        
        # Calculate averages and return sorted by performance
        theme_averages = {
            theme: statistics.mean(scores) 
            for theme, scores in theme_performance.items() 
            if len(scores) >= 2
        }
        
        sorted_themes = sorted(theme_averages.items(), key=lambda x: x[1], reverse=True)
        return sorted_themes
    
    def _analyze_seasonal_trends(self, posts: List) -> Dict[str, float]:
        """Analyze seasonal trends."""
        # Simplified seasonal analysis
        seasonal_performance = {"spring": [], "summer": [], "fall": [], "winter": []}
        
        for post in posts:
            if hasattr(post, 'created_at'):
                month = post.created_at.month
                engagement = self._calculate_post_engagement(getattr(post, 'metrics', {}))
                
                if month in [3, 4, 5]:
                    seasonal_performance["spring"].append(engagement)
                elif month in [6, 7, 8]:
                    seasonal_performance["summer"].append(engagement)
                elif month in [9, 10, 11]:
                    seasonal_performance["fall"].append(engagement)
                else:
                    seasonal_performance["winter"].append(engagement)
        
        # Calculate averages
        seasonal_averages = {}
        for season, scores in seasonal_performance.items():
            if scores:
                seasonal_averages[season] = statistics.mean(scores)
        
        return seasonal_averages
    
    def _calculate_avg_engagement_rate(self, posts: List) -> float:
        """Calculate average engagement rate for posts."""
        rates = []
        
        for post in posts:
            if hasattr(post, 'metrics') and post.metrics:
                engagement = self._calculate_post_engagement(post.metrics)
                impressions = post.metrics.get('impressions', 0)
                
                if impressions > 0:
                    rate = (engagement / impressions) * 100
                    rates.append(rate)
        
        return statistics.mean(rates) if rates else 0.0