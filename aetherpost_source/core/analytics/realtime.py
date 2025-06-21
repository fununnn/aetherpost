"""Real-time analytics and monitoring system."""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import statistics
from pathlib import Path

from ..logging.logger import logger
from ..exceptions import AetherPostError, ErrorCode


class MetricType(Enum):
    """Types of metrics we track."""
    ENGAGEMENT = "engagement"
    REACH = "reach"
    PERFORMANCE = "performance"
    ERROR = "error"
    USAGE = "usage"


@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: float
    metric_type: MetricType
    platform: Optional[str] = None
    timestamp: float = 0
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


@dataclass
class AnalyticsSnapshot:
    """Snapshot of analytics data at a point in time."""
    timestamp: str
    total_posts: int
    total_engagement: int
    total_reach: int
    platforms_active: List[str]
    top_performing_platform: Optional[str]
    engagement_rate: float
    error_rate: float
    performance_metrics: Dict[str, float]
    recent_activity: List[Dict[str, Any]]


class RealTimeAnalytics:
    """Real-time analytics collection and processing."""
    
    def __init__(self):
        self.metrics: List[Metric] = []
        self.subscribers: List[Callable] = []
        self.data_file = Path("logs/analytics.json")
        self.running = False
        
        # Load historical data
        self._load_data()
        
        # Start background processing
        self._start_background_tasks()
    
    def record_metric(self, name: str, value: float, metric_type: MetricType, 
                     platform: Optional[str] = None, **metadata):
        """Record a new metric."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            platform=platform,
            metadata=metadata
        )
        
        self.metrics.append(metric)
        
        # Keep only recent metrics (last 24 hours)
        cutoff_time = time.time() - 86400
        self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
        
        # Notify subscribers
        self._notify_subscribers(metric)
        
        logger.debug(f"Recorded metric: {name}={value}", extra={
            "metric_name": name,
            "metric_value": value,
            "metric_type": metric_type.value,
            "platform": platform,
            "metadata": metadata
        })
    
    def record_post_engagement(self, platform: str, likes: int, shares: int, 
                              comments: int, reach: int):
        """Record engagement metrics for a post."""
        total_engagement = likes + shares + comments
        engagement_rate = (total_engagement / reach * 100) if reach > 0 else 0
        
        self.record_metric("post_likes", likes, MetricType.ENGAGEMENT, platform)
        self.record_metric("post_shares", shares, MetricType.ENGAGEMENT, platform)
        self.record_metric("post_comments", comments, MetricType.ENGAGEMENT, platform)
        self.record_metric("post_reach", reach, MetricType.REACH, platform)
        self.record_metric("engagement_rate", engagement_rate, MetricType.ENGAGEMENT, platform)
    
    def record_performance_metric(self, operation: str, duration_ms: float, 
                                 platform: Optional[str] = None, success: bool = True):
        """Record performance metrics."""
        self.record_metric(
            f"performance_{operation}",
            duration_ms,
            MetricType.PERFORMANCE,
            platform,
            operation=operation,
            success=success
        )
    
    def record_error(self, error_type: str, platform: Optional[str] = None, 
                    error_code: Optional[int] = None):
        """Record error metrics."""
        self.record_metric(
            "error_count",
            1,
            MetricType.ERROR,
            platform,
            error_type=error_type,
            error_code=error_code
        )
    
    def record_usage(self, feature: str, user_id: Optional[str] = None):
        """Record feature usage metrics."""
        self.record_metric(
            f"usage_{feature}",
            1,
            MetricType.USAGE,
            metadata={"feature": feature, "user_id": user_id}
        )
    
    def get_current_snapshot(self) -> AnalyticsSnapshot:
        """Get current analytics snapshot."""
        now = datetime.now()
        hour_ago = time.time() - 3600
        
        # Filter recent metrics
        recent_metrics = [m for m in self.metrics if m.timestamp > hour_ago]
        
        # Calculate totals
        total_posts = len([m for m in recent_metrics if m.name.startswith("post_")])
        total_engagement = sum(m.value for m in recent_metrics if m.metric_type == MetricType.ENGAGEMENT)
        total_reach = sum(m.value for m in recent_metrics if m.name == "post_reach")
        
        # Platform analysis
        platforms_active = list(set(m.platform for m in recent_metrics if m.platform))
        
        # Top performing platform
        platform_engagement = {}
        for platform in platforms_active:
            platform_metrics = [m for m in recent_metrics if m.platform == platform and m.metric_type == MetricType.ENGAGEMENT]
            platform_engagement[platform] = sum(m.value for m in platform_metrics)
        
        top_platform = max(platform_engagement, key=platform_engagement.get) if platform_engagement else None
        
        # Engagement rate
        engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0
        
        # Error rate
        error_count = len([m for m in recent_metrics if m.metric_type == MetricType.ERROR])
        total_operations = len(recent_metrics)
        error_rate = (error_count / total_operations * 100) if total_operations > 0 else 0
        
        # Performance metrics
        performance_metrics = {}
        perf_metrics = [m for m in recent_metrics if m.metric_type == MetricType.PERFORMANCE]
        for metric in perf_metrics:
            if metric.name not in performance_metrics:
                performance_metrics[metric.name] = []
            performance_metrics[metric.name].append(metric.value)
        
        # Calculate averages
        avg_performance = {
            name: statistics.mean(values) 
            for name, values in performance_metrics.items()
        }
        
        # Recent activity
        recent_activity = []
        for metric in sorted(recent_metrics, key=lambda x: x.timestamp, reverse=True)[:10]:
            recent_activity.append({
                "timestamp": datetime.fromtimestamp(metric.timestamp).isoformat(),
                "name": metric.name,
                "value": metric.value,
                "platform": metric.platform,
                "type": metric.metric_type.value
            })
        
        return AnalyticsSnapshot(
            timestamp=now.isoformat(),
            total_posts=total_posts,
            total_engagement=int(total_engagement),
            total_reach=int(total_reach),
            platforms_active=platforms_active,
            top_performing_platform=top_platform,
            engagement_rate=round(engagement_rate, 2),
            error_rate=round(error_rate, 2),
            performance_metrics=avg_performance,
            recent_activity=recent_activity
        )
    
    def get_trend_data(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get trend data for a specific metric."""
        cutoff_time = time.time() - (hours * 3600)
        relevant_metrics = [
            m for m in self.metrics 
            if m.name == metric_name and m.timestamp > cutoff_time
        ]
        
        # Group by hour
        hourly_data = {}
        for metric in relevant_metrics:
            hour = int(metric.timestamp // 3600) * 3600
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(metric.value)
        
        # Calculate hourly averages
        trend_data = []
        for hour, values in sorted(hourly_data.items()):
            trend_data.append({
                "timestamp": datetime.fromtimestamp(hour).isoformat(),
                "value": statistics.mean(values),
                "count": len(values)
            })
        
        return trend_data
    
    def get_platform_comparison(self) -> Dict[str, Dict[str, float]]:
        """Get comparison data across platforms."""
        hour_ago = time.time() - 3600
        recent_metrics = [m for m in self.metrics if m.timestamp > hour_ago and m.platform]
        
        platform_stats = {}
        
        for platform in set(m.platform for m in recent_metrics):
            platform_metrics = [m for m in recent_metrics if m.platform == platform]
            
            engagement_metrics = [m for m in platform_metrics if m.metric_type == MetricType.ENGAGEMENT]
            reach_metrics = [m for m in platform_metrics if m.metric_type == MetricType.REACH]
            error_metrics = [m for m in platform_metrics if m.metric_type == MetricType.ERROR]
            
            platform_stats[platform] = {
                "total_engagement": sum(m.value for m in engagement_metrics),
                "total_reach": sum(m.value for m in reach_metrics),
                "error_count": len(error_metrics),
                "post_count": len([m for m in platform_metrics if m.name.startswith("post_")]),
                "avg_engagement_rate": statistics.mean([m.value for m in engagement_metrics if m.name == "engagement_rate"]) if any(m.name == "engagement_rate" for m in engagement_metrics) else 0
            }
        
        return platform_stats
    
    def subscribe(self, callback: Callable[[Metric], None]):
        """Subscribe to real-time metric updates."""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from metric updates."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def _notify_subscribers(self, metric: Metric):
        """Notify all subscribers of new metric."""
        for callback in self.subscribers:
            try:
                callback(metric)
            except Exception as e:
                logger.warning(f"Error notifying subscriber: {e}")
    
    def _load_data(self):
        """Load historical analytics data."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                # Load recent metrics (last 24 hours)
                cutoff_time = time.time() - 86400
                for metric_data in data.get('metrics', []):
                    if metric_data.get('timestamp', 0) > cutoff_time:
                        metric = Metric(
                            name=metric_data['name'],
                            value=metric_data['value'],
                            metric_type=MetricType(metric_data['metric_type']),
                            platform=metric_data.get('platform'),
                            timestamp=metric_data['timestamp'],
                            metadata=metric_data.get('metadata')
                        )
                        self.metrics.append(metric)
                
                logger.info(f"Loaded {len(self.metrics)} historical metrics")
                
            except Exception as e:
                logger.warning(f"Failed to load analytics data: {e}")
    
    def _save_data(self):
        """Save analytics data to file."""
        try:
            self.data_file.parent.mkdir(exist_ok=True)
            
            # Save only recent metrics (last 7 days)
            week_ago = time.time() - (7 * 86400)
            recent_metrics = [m for m in self.metrics if m.timestamp > week_ago]
            
            data = {
                "last_updated": datetime.now().isoformat(),
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "metric_type": m.metric_type.value,
                        "platform": m.platform,
                        "timestamp": m.timestamp,
                        "metadata": m.metadata
                    }
                    for m in recent_metrics
                ]
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Analytics data saved")
            
        except Exception as e:
            logger.warning(f"Failed to save analytics data: {e}")
    
    def _start_background_tasks(self):
        """Start background processing tasks."""
        self.running = True
        
        async def background_processor():
            while self.running:
                try:
                    # Save data every 5 minutes
                    self._save_data()
                    
                    # Clean up old metrics
                    cutoff_time = time.time() - 86400
                    old_count = len(self.metrics)
                    self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
                    
                    if len(self.metrics) < old_count:
                        logger.debug(f"Cleaned up {old_count - len(self.metrics)} old metrics")
                    
                    await asyncio.sleep(300)  # 5 minutes
                    
                except Exception as e:
                    logger.error(f"Error in analytics background processor: {e}")
                    await asyncio.sleep(60)
        
        # Start background task
        import threading
        
        def run_background():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(background_processor())
        
        thread = threading.Thread(target=run_background, daemon=True)
        thread.start()
    
    def stop(self):
        """Stop the analytics system."""
        self.running = False
        self._save_data()


class AlertSystem:
    """Alert system for monitoring thresholds."""
    
    def __init__(self, analytics: RealTimeAnalytics):
        self.analytics = analytics
        self.thresholds = {
            "error_rate": 5.0,  # Alert if error rate > 5%
            "engagement_rate": 1.0,  # Alert if engagement rate < 1%
            "response_time": 5000,  # Alert if response time > 5s
        }
        self.alerts_sent = set()
        
        # Subscribe to metrics
        analytics.subscribe(self._check_alert)
    
    def _check_alert(self, metric: Metric):
        """Check if metric triggers an alert."""
        alert_key = f"{metric.name}_{int(metric.timestamp // 3600)}"  # One alert per hour
        
        if alert_key in self.alerts_sent:
            return
        
        should_alert = False
        alert_message = ""
        
        # Check error rate
        if metric.name == "error_count":
            snapshot = self.analytics.get_current_snapshot()
            if snapshot.error_rate > self.thresholds["error_rate"]:
                should_alert = True
                alert_message = f"High error rate detected: {snapshot.error_rate:.1f}%"
        
        # Check engagement rate
        elif metric.name == "engagement_rate" and metric.value < self.thresholds["engagement_rate"]:
            should_alert = True
            alert_message = f"Low engagement rate on {metric.platform}: {metric.value:.1f}%"
        
        # Check response time
        elif metric.name.startswith("performance_") and metric.value > self.thresholds["response_time"]:
            should_alert = True
            alert_message = f"Slow response time for {metric.name}: {metric.value:.0f}ms"
        
        if should_alert:
            self._send_alert(alert_message, metric)
            self.alerts_sent.add(alert_key)
    
    def _send_alert(self, message: str, metric: Metric):
        """Send alert notification."""
        logger.warning(f"ALERT: {message}", extra={
            "alert_type": "performance_alert",
            "metric_name": metric.name,
            "metric_value": metric.value,
            "platform": metric.platform
        })
        
        # Here you could integrate with external alerting systems
        # like Slack, Discord, email, etc.


# Global analytics instance
analytics = RealTimeAnalytics()
alert_system = AlertSystem(analytics)


# Convenience functions
def record_engagement(platform: str, likes: int, shares: int, comments: int, reach: int):
    """Record engagement metrics."""
    analytics.record_post_engagement(platform, likes, shares, comments, reach)


def record_performance(operation: str, duration_ms: float, platform: Optional[str] = None, success: bool = True):
    """Record performance metrics."""
    analytics.record_performance_metric(operation, duration_ms, platform, success)


def record_usage(feature: str, user_id: Optional[str] = None):
    """Record feature usage."""
    analytics.record_usage(feature, user_id)


def get_dashboard_data() -> Dict[str, Any]:
    """Get comprehensive dashboard data."""
    snapshot = analytics.get_current_snapshot()
    platform_comparison = analytics.get_platform_comparison()
    engagement_trend = analytics.get_trend_data("engagement_rate", 24)
    
    return {
        "snapshot": asdict(snapshot),
        "platform_comparison": platform_comparison,
        "trends": {
            "engagement_rate": engagement_trend
        }
    }