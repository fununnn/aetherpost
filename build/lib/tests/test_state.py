"""Test state management."""

import pytest
from datetime import datetime

from aetherpost.core.state.manager import StateManager, PostRecord, CampaignState


class TestStateManager:
    """Test state management functionality."""
    
    def test_initialize_campaign(self, state_manager):
        """Test campaign initialization."""
        state = state_manager.initialize_campaign("test-campaign")
        
        assert state.campaign_id.startswith("campaign-")
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.updated_at, datetime)
        assert len(state.posts) == 0
        assert len(state.media) == 0
    
    def test_add_post(self, state_manager):
        """Test adding a post record."""
        # Initialize campaign first
        state_manager.initialize_campaign("test-campaign")
        
        # Add post
        post = state_manager.add_post(
            platform="twitter",
            post_id="1234567890",
            url="https://twitter.com/user/status/1234567890",
            content={"text": "Test post content"}
        )
        
        assert post.platform == "twitter"
        assert post.post_id == "1234567890"
        assert post.url == "https://twitter.com/user/status/1234567890"
        assert post.content["text"] == "Test post content"
        assert post.status == "published"
        
        # Verify it's in state
        assert len(state_manager.state.posts) == 1
        assert state_manager.state.posts[0].post_id == "1234567890"
    
    def test_update_post_metrics(self, state_manager):
        """Test updating post metrics."""
        # Initialize and add post
        state_manager.initialize_campaign("test-campaign")
        post = state_manager.add_post(
            platform="twitter",
            post_id="1234567890",
            url="https://twitter.com/user/status/1234567890",
            content={"text": "Test post"}
        )
        
        # Update metrics
        metrics = {"likes": 42, "retweets": 12, "replies": 5}
        state_manager.update_post_metrics("1234567890", metrics)
        
        # Verify metrics updated
        updated_post = state_manager.state.posts[0]
        assert updated_post.metrics["likes"] == 42
        assert updated_post.metrics["retweets"] == 12
        assert updated_post.metrics["replies"] == 5
    
    def test_add_media(self, state_manager):
        """Test adding media record."""
        # Initialize campaign first
        state_manager.initialize_campaign("test-campaign")
        
        # Add media
        media = state_manager.add_media(
            media_type="image",
            path="./test-image.png",
            provider="dalle-3"
        )
        
        assert media.type == "image"
        assert media.path == "./test-image.png"
        assert media.provider == "dalle-3"
        assert isinstance(media.created_at, datetime)
        
        # Verify it's in state
        assert len(state_manager.state.media) == 1
        assert state_manager.state.media[0].path == "./test-image.png"
    
    def test_get_posts_by_platform(self, state_manager):
        """Test filtering posts by platform."""
        # Initialize and add posts
        state_manager.initialize_campaign("test-campaign")
        
        state_manager.add_post("twitter", "123", "url1", {"text": "Twitter post"})
        state_manager.add_post("bluesky", "456", "url2", {"text": "Bluesky post"})
        state_manager.add_post("twitter", "789", "url3", {"text": "Another Twitter post"})
        
        # Get Twitter posts
        twitter_posts = state_manager.get_posts_by_platform("twitter")
        assert len(twitter_posts) == 2
        assert all(post.platform == "twitter" for post in twitter_posts)
        
        # Get Bluesky posts
        bluesky_posts = state_manager.get_posts_by_platform("bluesky")
        assert len(bluesky_posts) == 1
        assert bluesky_posts[0].platform == "bluesky"
    
    def test_get_successful_posts(self, state_manager):
        """Test filtering successful posts."""
        # Initialize and add posts
        state_manager.initialize_campaign("test-campaign")
        
        # Add successful post
        post1 = state_manager.add_post("twitter", "123", "url1", {"text": "Success"})
        
        # Add failed post by manually setting status
        post2 = state_manager.add_post("bluesky", "456", "url2", {"text": "Failed"})
        post2.status = "failed"
        
        successful_posts = state_manager.get_successful_posts()
        assert len(successful_posts) == 1
        assert successful_posts[0].post_id == "123"
        assert successful_posts[0].status == "published"
    
    def test_calculate_analytics(self, state_manager):
        """Test analytics calculation."""
        # Initialize and add posts with metrics
        state_manager.initialize_campaign("test-campaign")
        
        # Add posts with different metrics
        post1 = state_manager.add_post("twitter", "123", "url1", {"text": "Post 1"})
        post1.metrics = {"likes": 10, "retweets": 5, "impressions": 100}
        
        post2 = state_manager.add_post("bluesky", "456", "url2", {"text": "Post 2"})
        post2.metrics = {"likes": 20, "retweets": 8, "views": 200}
        
        # Calculate analytics
        analytics = state_manager.calculate_analytics()
        
        assert analytics.total_reach == 300  # 100 + 200
        assert analytics.total_engagement == 43  # 10+5 + 20+8
        
        # Check platform performance
        assert "twitter" in analytics.platform_performance
        assert "bluesky" in analytics.platform_performance
        
        twitter_perf = analytics.platform_performance["twitter"]
        assert twitter_perf["posts"] == 1
        assert twitter_perf["total_reach"] == 100
        assert twitter_perf["total_engagement"] == 15
    
    def test_get_state_summary(self, state_manager):
        """Test state summary generation."""
        # Initialize campaign
        state_manager.initialize_campaign("test-campaign")
        
        # Add some data
        state_manager.add_post("twitter", "123", "url1", {"text": "Post 1"})
        state_manager.add_post("bluesky", "456", "url2", {"text": "Post 2"})
        state_manager.add_media("image", "test.png", "dalle-3")
        
        # Get summary
        summary = state_manager.get_state_summary()
        
        assert summary["campaign_id"].startswith("campaign-")
        assert summary["total_posts"] == 2
        assert summary["successful_posts"] == 2
        assert set(summary["platforms"]) == {"twitter", "bluesky"}
        assert summary["total_media"] == 1
    
    def test_save_and_load_state(self, state_manager):
        """Test state persistence."""
        # Initialize and populate state
        state_manager.initialize_campaign("test-campaign")
        original_campaign_id = state_manager.state.campaign_id
        
        state_manager.add_post("twitter", "123", "url1", {"text": "Test post"})
        state_manager.add_media("image", "test.png", "dalle-3")
        
        # Save state
        state_manager.save_state()
        
        # Create new manager and load state
        new_manager = StateManager()
        loaded_state = new_manager.load_state()
        
        assert loaded_state is not None
        assert loaded_state.campaign_id == original_campaign_id
        assert len(loaded_state.posts) == 1
        assert len(loaded_state.media) == 1
        assert loaded_state.posts[0].post_id == "123"
    
    def test_load_nonexistent_state(self, state_manager):
        """Test loading state when file doesn't exist."""
        # Should return None when no state file exists
        state = state_manager.load_state()
        assert state is None


class TestPostRecord:
    """Test post record model."""
    
    def test_post_record_creation(self):
        """Test creating a post record."""
        post = PostRecord(
            id="post-123",
            platform="twitter",
            post_id="1234567890",
            url="https://twitter.com/user/status/1234567890",
            created_at=datetime.utcnow(),
            content={"text": "Test post"}
        )
        
        assert post.id == "post-123"
        assert post.platform == "twitter"
        assert post.post_id == "1234567890"
        assert post.status == "published"  # Default status
        assert post.variant_id is None  # Default variant_id
        assert post.content["text"] == "Test post"
    
    def test_post_record_with_metrics(self):
        """Test post record with metrics."""
        post = PostRecord(
            id="post-123",
            platform="twitter",
            post_id="1234567890",
            url="https://twitter.com/user/status/1234567890",
            created_at=datetime.utcnow(),
            content={"text": "Test post"},
            metrics={"likes": 42, "retweets": 12}
        )
        
        assert post.metrics["likes"] == 42
        assert post.metrics["retweets"] == 12