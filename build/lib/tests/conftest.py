"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path

from aetherpost.core.config.models import CampaignConfig, ContentConfig, CredentialsConfig
from aetherpost.core.state.manager import StateManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_config():
    """Sample campaign configuration for testing."""
    return CampaignConfig(
        name="test-app",
        concept="Test application for unit testing",
        platforms=["twitter"],
        content=ContentConfig(
            style="casual",
            action="Try it now!"
        )
    )


@pytest.fixture
def sample_credentials():
    """Sample credentials for testing."""
    return CredentialsConfig(
        twitter={
            "api_key": "test_api_key",
            "api_secret": "test_api_secret",
            "access_token": "test_access_token",
            "access_token_secret": "test_access_token_secret"
        },
        claude={
            "api_key": "sk-ant-test_key"
        }
    )


@pytest.fixture
def state_manager(temp_dir):
    """State manager with temporary directory."""
    original_cwd = Path.cwd()
    try:
        # Change to temp directory for test
        import os
        os.chdir(temp_dir)
        
        manager = StateManager()
        yield manager
    finally:
        # Restore original directory
        os.chdir(original_cwd)


@pytest.fixture
def mock_twitter_response():
    """Mock Twitter API response."""
    return {
        "data": {
            "id": "1234567890",
            "text": "Test tweet content"
        }
    }


@pytest.fixture
def mock_claude_response_ai():
    """Mock [AI Service] API response."""
    class MockMessage:
        def __init__(self, text):
            self.content = [MockContent(text)]
    
    class MockContent:
        def __init__(self, text):
            self.text = text
    
    return MockMessage("Generated test content for social media post")