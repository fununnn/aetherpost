"""Reddit-specific configuration models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class RedditConfig(BaseModel):
    """Reddit platform configuration."""
    
    client_id: str = Field(..., description="Reddit app client ID")
    client_secret: str = Field(..., description="Reddit app client secret")
    username: str = Field(..., description="Reddit username")
    password: str = Field(..., description="Reddit password (or app password)")
    user_agent: str = Field(default="AetherPost/1.0", description="User agent string")
    
    # Posting configuration
    default_subreddits: List[str] = Field(
        default=["technology", "programming", "SideProject"],
        description="Default subreddits to post to"
    )
    max_subreddits: int = Field(default=3, description="Maximum number of subreddits to post to")
    
    # Content optimization
    enable_auto_optimization: bool = Field(
        default=True, 
        description="Automatically optimize content for each subreddit"
    )
    avoid_promotional_language: bool = Field(
        default=True,
        description="Replace promotional words with neutral alternatives"
    )
    
    # Rate limiting
    post_delay: int = Field(default=2, description="Delay between posts in seconds")
    respect_rate_limits: bool = Field(default=True, description="Respect Reddit rate limits")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            # Custom encoders if needed
        }


class RedditPostConfig(BaseModel):
    """Configuration for a specific Reddit post."""
    
    subreddit: str = Field(..., description="Target subreddit")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post content")
    flair: Optional[str] = Field(None, description="Post flair")
    nsfw: bool = Field(default=False, description="Mark as NSFW")
    spoiler: bool = Field(default=False, description="Mark as spoiler")
    
    # Targeting
    target_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that match this subreddit"
    )
    tone: str = Field(default="informative", description="Tone for this subreddit")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "subreddit": "programming",
                "title": "Built a new developer tool for API testing",
                "content": "I've been working on a tool that makes API testing easier...",
                "flair": "Project",
                "nsfw": False,
                "spoiler": False,
                "target_keywords": ["tool", "api", "development"],
                "tone": "informative"
            }
        }


class SubredditRules(BaseModel):
    """Rules and recommendations for a specific subreddit."""
    
    name: str = Field(..., description="Subreddit name")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Subreddit description")
    
    # Posting rules
    allows_self_posts: bool = Field(default=True, description="Allows text posts")
    allows_link_posts: bool = Field(default=True, description="Allows link posts")
    allows_images: bool = Field(default=True, description="Allows image posts")
    
    # Content guidelines
    title_max_length: int = Field(default=300, description="Maximum title length")
    required_flair: bool = Field(default=False, description="Flair is required")
    available_flairs: List[str] = Field(default_factory=list, description="Available flairs")
    
    # Promotion rules
    allows_promotion: bool = Field(default=False, description="Allows promotional content")
    self_promotion_ratio: Optional[str] = Field(None, description="Self-promotion ratio rule")
    
    # Recommended posting times
    best_posting_hours: List[int] = Field(
        default=[14, 15, 16, 17, 18],
        description="Best hours to post (UTC)"
    )
    avoid_weekends: bool = Field(default=False, description="Avoid posting on weekends")
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "name": "programming",
                "display_name": "r/programming",
                "description": "Computer programming discussion",
                "allows_self_posts": True,
                "allows_link_posts": True,
                "allows_images": False,
                "title_max_length": 300,
                "required_flair": False,
                "available_flairs": ["Discussion", "Project", "Article"],
                "allows_promotion": False,
                "self_promotion_ratio": "9:1",
                "best_posting_hours": [14, 15, 16, 17, 18],
                "avoid_weekends": False
            }
        }