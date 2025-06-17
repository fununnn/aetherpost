"""Test configuration management."""

import pytest
import tempfile
from pathlib import Path

from aetherpost.core.config.parser import ConfigLoader, SmartConfigParser
from aetherpost.core.config.models import CampaignConfig, ContentConfig


class TestSmartConfigParser:
    """Test smart configuration parsing."""
    
    def test_parse_concept(self):
        """Test concept parsing to AI prompt."""
        parser = SmartConfigParser()
        result = parser.parse_concept("AI task manager")
        
        assert "ai_prompt" in result
        assert "AI task manager" in result["ai_prompt"]
        assert "140 characters" in result["ai_prompt"]
    
    def test_parse_tone_casual(self):
        """Test casual tone parsing."""
        parser = SmartConfigParser()
        result = parser.parse_tone("casual")
        
        assert result["style"] == "friendly"
        assert result["emoji_level"] == "high"
        assert result["formality"] == "casual"
    
    def test_parse_tone_professional(self):
        """Test professional tone parsing."""
        parser = SmartConfigParser()
        result = parser.parse_tone("professional")
        
        assert result["style"] == "formal"
        assert result["emoji_level"] == "none"
        assert result["formality"] == "business"
    
    def test_parse_when_immediate(self):
        """Test immediate time parsing."""
        parser = SmartConfigParser()
        result = parser.parse_when("now")
        
        assert result["type"] == "immediate"
    
    def test_parse_when_weekly(self):
        """Test weekly recurring time parsing."""
        parser = SmartConfigParser()
        result = parser.parse_when("every week")
        
        assert result["type"] == "recurring"
        assert result["interval"] == "weekly"


class TestConfigLoader:
    """Test configuration loading and saving."""
    
    def test_generate_basic_template(self):
        """Test basic template generation."""
        loader = ConfigLoader()
        template = loader.generate_template("basic")
        
        assert "name:" in template
        assert "concept:" in template
        assert "platforms:" in template
        assert "twitter" in template
    
    def test_generate_minimal_template(self):
        """Test minimal template generation."""
        loader = ConfigLoader()
        template = loader.generate_template("minimal")
        
        assert "name:" in template
        assert "concept:" in template
        assert "platforms:" in template
        assert len(template.split('\n')) <= 5  # Should be very short
    
    def test_save_and_load_config(self, temp_dir):
        """Test saving and loading configuration."""
        # Change to temp directory
        import os
        original_cwd = Path.cwd()
        os.chdir(temp_dir)
        
        try:
            loader = ConfigLoader()
            
            # Create test config
            config = CampaignConfig(
                name="test-app",
                concept="Test application",
                platforms=["twitter"],
                content=ContentConfig(style="casual", action="Try it!")
            )
            
            # Save config
            loader.save_campaign_config(config, "test_campaign.yaml")
            
            # Load config
            loaded_config = loader.load_campaign_config("test_campaign.yaml")
            
            assert loaded_config.name == "test-app"
            assert loaded_config.concept == "Test application"
            assert loaded_config.platforms == ["twitter"]
            assert loaded_config.content.style == "casual"
        
        finally:
            os.chdir(original_cwd)
    
    def test_validate_config_valid(self, sample_config):
        """Test validation of valid configuration."""
        loader = ConfigLoader()
        issues = loader.validate_config(sample_config)
        
        assert len(issues) == 0
    
    def test_validate_config_missing_name(self):
        """Test validation with missing name."""
        loader = ConfigLoader()
        
        config = CampaignConfig(
            name="",  # Empty name
            concept="Test application",
            platforms=["twitter"]
        )
        
        issues = loader.validate_config(config)
        assert len(issues) > 0
        assert any("name" in issue.lower() for issue in issues)
    
    def test_validate_config_missing_concept(self):
        """Test validation with missing concept."""
        loader = ConfigLoader()
        
        config = CampaignConfig(
            name="test-app",
            concept="",  # Empty concept
            platforms=["twitter"]
        )
        
        issues = loader.validate_config(config)
        assert len(issues) > 0
        assert any("concept" in issue.lower() for issue in issues)
    
    def test_validate_config_no_platforms(self):
        """Test validation with no platforms."""
        loader = ConfigLoader()
        
        config = CampaignConfig(
            name="test-app",
            concept="Test application",
            platforms=[]  # No platforms
        )
        
        issues = loader.validate_config(config)
        assert len(issues) > 0
        assert any("platform" in issue.lower() for issue in issues)


class TestCampaignConfig:
    """Test campaign configuration model."""
    
    def test_valid_config_creation(self):
        """Test creating valid configuration."""
        config = CampaignConfig(
            name="test-app",
            concept="Test application",
            platforms=["twitter", "bluesky"]
        )
        
        assert config.name == "test-app"
        assert config.concept == "Test application"
        assert config.platforms == ["twitter", "bluesky"]
    
    def test_invalid_platform_validation(self):
        """Test validation of invalid platform."""
        with pytest.raises(ValueError):
            CampaignConfig(
                name="test-app",
                concept="Test application",
                platforms=["invalid_platform"]
            )
    
    def test_empty_name_validation(self):
        """Test validation of empty name."""
        with pytest.raises(ValueError):
            CampaignConfig(
                name="",
                concept="Test application",
                platforms=["twitter"]
            )
    
    def test_whitespace_name_validation(self):
        """Test validation of whitespace-only name."""
        with pytest.raises(ValueError):
            CampaignConfig(
                name="   ",
                concept="Test application",
                platforms=["twitter"]
            )
    
    def test_default_values(self):
        """Test default values are set correctly."""
        config = CampaignConfig(
            name="test-app",
            concept="Test application",
            platforms=["twitter"]
        )
        
        assert config.content.style == "casual"
        assert config.content.action == "Learn more"
        assert config.content.max_length == 280
        assert config.schedule.type == "immediate"
        assert config.analytics is True