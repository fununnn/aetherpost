"""Common utility functions used across AetherPost."""

import re
import json
import yaml
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging

from .base_models import Platform, ContentType, ValidationResult


def generate_id(prefix: str = "") -> str:
    """Generate unique ID with optional prefix."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}" if prefix else unique_id


def safe_filename(text: str, max_length: int = 50) -> str:
    """Convert text to safe filename."""
    # Remove or replace unsafe characters
    safe_text = re.sub(r'[<>:"/\\|?*]', '_', text)
    safe_text = re.sub(r'\s+', '_', safe_text.strip())
    safe_text = safe_text.lower()
    
    # Truncate if too long
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length].rstrip('_')
    
    return safe_text or "unnamed"


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Calculate estimated reading time in minutes."""
    word_count = len(text.split())
    return max(1, round(word_count / words_per_minute))


def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text."""
    hashtag_pattern = r'#(\w+)'
    hashtags = re.findall(hashtag_pattern, text)
    return list(set(hashtags))  # Remove duplicates


def extract_mentions(text: str, platform: Platform) -> List[str]:
    """Extract mentions from text based on platform."""
    if platform == Platform.TWITTER:
        pattern = r'@(\w+)'
    elif platform == Platform.INSTAGRAM:
        pattern = r'@(\w+)'
    elif platform == Platform.REDDIT:
        pattern = r'u/(\w+)'
    elif platform == Platform.GITHUB:
        pattern = r'@(\w+)'
    else:
        pattern = r'@(\w+)'  # Default pattern
    
    mentions = re.findall(pattern, text)
    return list(set(mentions))


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls


def clean_text(text: str, remove_urls: bool = False, remove_hashtags: bool = False, 
               remove_mentions: bool = False) -> str:
    """Clean text by removing specified elements."""
    cleaned = text
    
    if remove_urls:
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        cleaned = re.sub(url_pattern, '', cleaned)
    
    if remove_hashtags:
        cleaned = re.sub(r'#\w+', '', cleaned)
    
    if remove_mentions:
        cleaned = re.sub(r'@\w+', '', cleaned)
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def truncate_smart(text: str, max_length: int, preserve_words: bool = True, 
                  suffix: str = "...") -> str:
    """Smart text truncation that preserves word boundaries."""
    if len(text) <= max_length:
        return text
    
    if not preserve_words:
        return text[:max_length - len(suffix)] + suffix
    
    # Find good truncation points
    truncation_points = [
        text.rfind('.', 0, max_length - len(suffix)),
        text.rfind('\n', 0, max_length - len(suffix)),
        text.rfind(' ', 0, max_length - len(suffix))
    ]
    
    # Use the best truncation point that keeps at least 80% of desired length
    min_length = int(max_length * 0.8)
    best_point = max([p for p in truncation_points if p >= min_length], default=-1)
    
    if best_point > 0:
        return text[:best_point] + suffix
    else:
        # Fallback to word boundary
        words = text[:max_length - len(suffix)].split()
        return ' '.join(words[:-1]) + suffix if len(words) > 1 else text[:max_length - len(suffix)] + suffix


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))


def format_number(number: Union[int, float], short_form: bool = True) -> str:
    """Format numbers for display (e.g., 1.5K, 2.1M)."""
    if not short_form:
        return f"{number:,}"
    
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return str(number)


def parse_time_string(time_str: str) -> Optional[datetime]:
    """Parse various time string formats."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%H:%M:%S",
        "%H:%M"
    ]
    
    for fmt in formats:
        try:
            if ":" in time_str and "-" not in time_str:
                # Time only, assume today
                time_part = datetime.strptime(time_str, fmt).time()
                return datetime.combine(datetime.now().date(), time_part)
            else:
                return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    return None


def calculate_optimal_time(timezone: str = "UTC", target_times: List[str] = None) -> datetime:
    """Calculate next optimal posting time."""
    if not target_times:
        target_times = ["09:00", "13:00", "18:00"]
    
    now = datetime.now()
    today = now.date()
    
    # Find next optimal time today
    for time_str in target_times:
        time_part = datetime.strptime(time_str, "%H:%M").time()
        target_time = datetime.combine(today, time_part)
        
        if target_time > now:
            return target_time
    
    # If no optimal time today, use first time tomorrow
    tomorrow = today + timedelta(days=1)
    first_time = datetime.strptime(target_times[0], "%H:%M").time()
    return datetime.combine(tomorrow, first_time)


def merge_dictionaries(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge multiple dictionaries."""
    result = {}
    
    for dictionary in dicts:
        for key, value in dictionary.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dictionaries(result[key], value)
            else:
                result[key] = value
    
    return result


def load_config_file(file_path: Union[str, Path], default: Any = None) -> Any:
    """Load configuration from YAML or JSON file."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return default
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif file_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                # Try to parse as YAML first, then JSON
                content = f.read()
                try:
                    return yaml.safe_load(content)
                except yaml.YAMLError:
                    return json.loads(content)
    except Exception as e:
        logging.warning(f"Could not load config file {file_path}: {e}")
        return default


def save_config_file(data: Any, file_path: Union[str, Path], format_type: str = "yaml") -> bool:
    """Save data to configuration file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            if format_type.lower() == "yaml":
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            elif format_type.lower() == "json":
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
        return True
    except Exception as e:
        logging.error(f"Could not save config file {file_path}: {e}")
        return False


def create_content_hash(content: str, platform: str = "") -> str:
    """Create hash for content deduplication."""
    content_key = f"{platform}:{content}".encode('utf-8')
    return hashlib.md5(content_key).hexdigest()[:12]


def estimate_engagement(platform: Platform, content: str, follower_count: int = 1000) -> Dict[str, Union[int, float]]:
    """Estimate engagement metrics for content."""
    # Base engagement rates by platform
    base_rates = {
        Platform.TWITTER: 0.045,
        Platform.INSTAGRAM: 0.018,
        Platform.LINKEDIN: 0.024,
        Platform.YOUTUBE: 0.030,
        Platform.TIKTOK: 0.060,
        Platform.REDDIT: 0.080,
        Platform.GITHUB: 0.010
    }
    
    base_rate = base_rates.get(platform, 0.030)
    
    # Adjust based on content characteristics
    multiplier = 1.0
    
    # Questions tend to get more engagement
    if "?" in content:
        multiplier *= 1.3
    
    # Shorter content often performs better
    if len(content) < 100:
        multiplier *= 1.1
    
    # Educational content tends to do well
    if any(word in content.lower() for word in ["how to", "tips", "guide", "tutorial"]):
        multiplier *= 1.2
    
    # Hashtags can boost visibility
    hashtag_count = content.count("#")
    if hashtag_count > 0:
        multiplier *= (1 + hashtag_count * 0.05)
    
    # Calculate estimates
    engagement_rate = base_rate * multiplier
    estimated_reach = min(follower_count * 3, follower_count * multiplier)  # Viral factor
    estimated_engagements = int(estimated_reach * engagement_rate)
    
    return {
        "estimated_reach": int(estimated_reach),
        "engagement_rate": round(engagement_rate, 4),
        "estimated_likes": int(estimated_engagements * 0.7),
        "estimated_comments": int(estimated_engagements * 0.2),
        "estimated_shares": int(estimated_engagements * 0.1)
    }


def validate_content_basic(content: str, platform: Platform, platform_config: Optional[Dict] = None) -> ValidationResult:
    """Basic content validation for platform requirements."""
    errors = []
    warnings = []
    suggestions = []
    score = 100.0
    
    # Character limit validation
    char_limit = None
    if platform_config and "character_limit" in platform_config:
        char_limit = platform_config["character_limit"]
    elif platform == Platform.TWITTER:
        char_limit = 280
    elif platform == Platform.INSTAGRAM:
        char_limit = 2200
    elif platform == Platform.LINKEDIN:
        char_limit = 3000
    
    if char_limit and len(content) > char_limit:
        errors.append(f"Content exceeds {char_limit} character limit ({len(content)} characters)")
        score -= 30
    elif char_limit and len(content) > char_limit * 0.9:
        warnings.append(f"Content is close to character limit ({len(content)}/{char_limit})")
        score -= 10
    
    # Empty content check
    if not content.strip():
        errors.append("Content cannot be empty")
        score -= 50
    
    # Very short content warning
    if len(content.strip()) < 10:
        warnings.append("Content is very short and may not be engaging")
        score -= 15
    
    # Hashtag validation
    hashtags = extract_hashtags(content)
    if platform == Platform.TWITTER and len(hashtags) > 3:
        warnings.append("Too many hashtags for Twitter (recommended: 1-3)")
        score -= 10
    
    # URL validation
    urls = extract_urls(content)
    for url in urls:
        if not validate_url(url):
            errors.append(f"Invalid URL format: {url}")
            score -= 15
    
    # Platform-specific suggestions
    if platform == Platform.INSTAGRAM and not any(char in content for char in "📷🎥📸"):
        suggestions.append("Consider adding visual-related emojis for Instagram")
    
    if platform == Platform.LINKEDIN and not any(word in content.lower() for word in ["professional", "career", "business", "industry"]):
        suggestions.append("Consider adding professional context for LinkedIn")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        score=max(0, score),
        errors=errors,
        warnings=warnings,
        suggestions=suggestions
    )


def batch_process(items: List[Any], batch_size: int = 10) -> List[List[Any]]:
    """Split items into batches for processing."""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches


def retry_operation(func, max_retries: int = 3, delay: float = 1.0, 
                   exponential_backoff: bool = True):
    """Retry decorator for operations that might fail."""
    import time
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(current_delay)
                        if exponential_backoff:
                            current_delay *= 2
                    else:
                        raise last_exception
            
            return wrapper
        return decorator
    
    return decorator if func is None else decorator(func)