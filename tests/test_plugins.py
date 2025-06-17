"""Test plugin system."""

import pytest
from unittest.mock import Mock, AsyncMock

from aetherpost.plugins.manager import PluginManager
from aetherpost.plugins.base import SNSConnectorBase, AIProviderBase


class MockTwitterConnector(SNSConnectorBase):
    """Mock Twitter connector for testing."""
    
    def __init__(self, credentials):
        self.credentials = credentials
    
    @property
    def name(self) -> str:
        return "twitter"
    
    @property
    def supported_media_types(self):
        return ["image/jpeg", "image/png"]
    
    async def authenticate(self, credentials):
        return credentials.get("api_key") == "valid_key"
    
    async def post(self, content):
        if not content.get("text"):
            return {"error": "No text content", "status": "failed"}
        
        return {
            "id": "1234567890",
            "url": "https://twitter.com/user/status/1234567890",
            "platform": "twitter",
            "status": "published"
        }
    
    async def delete(self, post_id):
        return True
    
    async def get_metrics(self, post_id):
        return {
            "likes": 42,
            "retweets": 12,
            "replies": 5
        }


class MockClaudeProviderAI(AIProviderBase):
    """Mock [AI Service] provider for testing."""
    
    def __init__(self, config):
        self.config = config
    
    @property
    def name(self) -> str:
        return "[AI Service]"
    
    async def generate_text(self, prompt, config):
        return f"Generated text for: {prompt[:20]}..."
    
    async def generate_image(self, prompt, config):
        raise NotImplementedError("[AI Service] does not support image generation")
    
    async def validate_config(self, config):
        return config.get("api_key", "").startswith("sk-ant-")


class TestPluginManager:
    """Test plugin manager functionality."""
    
    @pytest.fixture
    def plugin_manager(self):
        """Create a fresh plugin manager for each test."""
        manager = PluginManager()
        # Clear auto-discovered plugins for testing
        manager.connectors.clear()
        manager.ai_providers.clear()
        manager.analytics_providers.clear()
        return manager
    
    def test_register_connector(self, plugin_manager):
        """Test registering an SNS connector."""
        plugin_manager.register_connector("twitter", MockTwitterConnector)
        
        assert "twitter" in plugin_manager.connectors
        assert plugin_manager.connectors["twitter"] == MockTwitterConnector
    
    def test_register_ai_provider(self, plugin_manager):
        """Test registering an AI provider."""
        plugin_manager.register_ai_provider("[AI Service]", MockClaudeProvider)
        
        assert "[AI Service]" in plugin_manager.ai_providers
        assert plugin_manager.ai_providers["[AI Service]"] == MockClaudeProvider
    
    def test_load_connector(self, plugin_manager):
        """Test loading a connector instance."""
        plugin_manager.register_connector("twitter", MockTwitterConnector)
        
        credentials = {"api_key": "test_key"}
        connector = plugin_manager.load_connector("twitter", credentials)
        
        assert isinstance(connector, MockTwitterConnector)
        assert connector.credentials == credentials
    
    def test_load_ai_provider(self, plugin_manager):
        """Test loading an AI provider instance."""
        plugin_manager.register_ai_provider("[AI Service]", MockClaudeProvider)
        
        config = {"api_key": "sk-ant-test"}
        provider = plugin_manager.load_ai_provider("[AI Service]", config)
        
        assert isinstance(provider, MockClaudeProvider)
        assert provider.config == config
    
    def test_load_unknown_connector(self, plugin_manager):
        """Test loading unknown connector raises error."""
        with pytest.raises(ValueError, match="Unknown connector"):
            plugin_manager.load_connector("unknown", {})
    
    def test_load_unknown_ai_provider(self, plugin_manager):
        """Test loading unknown AI provider raises error."""
        with pytest.raises(ValueError, match="Unknown AI provider"):
            plugin_manager.load_ai_provider("unknown", {})
    
    def test_list_connectors(self, plugin_manager):
        """Test listing available connectors."""
        plugin_manager.register_connector("twitter", MockTwitterConnector)
        plugin_manager.register_connector("bluesky", MockTwitterConnector)
        
        connectors = plugin_manager.list_connectors()
        assert set(connectors) == {"twitter", "bluesky"}
    
    def test_list_ai_providers(self, plugin_manager):
        """Test listing available AI providers."""
        plugin_manager.register_ai_provider("[AI Service]", MockClaudeProvider)
        
        providers = plugin_manager.list_ai_providers()
        assert providers == ["[AI Service]"]
    
    def test_get_connector_info(self, plugin_manager):
        """Test getting connector information."""
        plugin_manager.register_connector("twitter", MockTwitterConnector)
        
        info = plugin_manager.get_connector_info("twitter")
        
        assert info["name"] == "twitter"
        assert info["class"] == "MockTwitterConnector"
        assert "image/jpeg" in info["supported_media_types"]
    
    def test_diagnose(self, plugin_manager):
        """Test plugin diagnostics."""
        plugin_manager.register_connector("twitter", MockTwitterConnector)
        plugin_manager.register_ai_provider("[AI Service]", MockClaudeProvider)
        
        diagnosis = plugin_manager.diagnose()
        
        assert "connectors" in diagnosis
        assert "ai_providers" in diagnosis
        assert "twitter" in diagnosis["connectors"]
        assert "[AI Service]" in diagnosis["ai_providers"]
        
        # Check status
        assert diagnosis["connectors"]["twitter"]["status"] == "ok"
        assert diagnosis["ai_providers"]["[AI Service]"]["status"] == "ok"


class TestMockTwitterConnector:
    """Test mock Twitter connector functionality."""
    
    @pytest.fixture
    def connector(self):
        """Create mock Twitter connector."""
        return MockTwitterConnector({"api_key": "valid_key"})
    
    @pytest.mark.asyncio
    async def test_authenticate_valid(self, connector):
        """Test authentication with valid credentials."""
        result = await connector.authenticate({"api_key": "valid_key"})
        assert result is True
    
    @pytest.mark.asyncio
    async def test_authenticate_invalid(self, connector):
        """Test authentication with invalid credentials."""
        result = await connector.authenticate({"api_key": "invalid_key"})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_post_success(self, connector):
        """Test successful post."""
        content = {"text": "Test post content"}
        result = await connector.post(content)
        
        assert result["status"] == "published"
        assert result["platform"] == "twitter"
        assert "id" in result
        assert "url" in result
    
    @pytest.mark.asyncio
    async def test_post_no_text(self, connector):
        """Test post without text content."""
        content = {}  # No text
        result = await connector.post(content)
        
        assert result["status"] == "failed"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_delete_post(self, connector):
        """Test deleting a post."""
        result = await connector.delete("1234567890")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, connector):
        """Test getting post metrics."""
        metrics = await connector.get_metrics("1234567890")
        
        assert "likes" in metrics
        assert "retweets" in metrics
        assert "replies" in metrics
        assert metrics["likes"] == 42
    
    def test_validate_content(self, connector):
        """Test content validation."""
        # Valid content
        valid_content = {"text": "Test post"}
        issues = connector.validate_content(valid_content)
        assert len(issues) == 0
        
        # Invalid content (no text)
        invalid_content = {}
        issues = connector.validate_content(invalid_content)
        assert len(issues) > 0
        assert any("text" in issue.lower() for issue in issues)


class TestMockClaudeProvider:
    """Test mock [AI Service] provider functionality."""
    
    @pytest.fixture
    def provider(self):
        """Create mock [AI Service] provider."""
        return MockClaudeProvider({"api_key": "sk-ant-test"})
    
    @pytest.mark.asyncio
    async def test_generate_text(self, provider):
        """Test text generation."""
        prompt = "Create a social media post about AI"
        result = await provider.generate_text(prompt, {})
        
        assert "Generated text for:" in result
        assert "Create a social media" in result
    
    @pytest.mark.asyncio
    async def test_generate_image_not_supported(self, provider):
        """Test that image generation is not supported."""
        with pytest.raises(NotImplementedError):
            await provider.generate_image("Test prompt", {})
    
    @pytest.mark.asyncio
    async def test_validate_config_valid(self, provider):
        """Test config validation with valid key."""
        config = {"api_key": "sk-ant-valid_key"}
        result = await provider.validate_config(config)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_config_invalid(self, provider):
        """Test config validation with invalid key."""
        config = {"api_key": "invalid_key"}
        result = await provider.validate_config(config)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_config_missing(self, provider):
        """Test config validation with missing key."""
        config = {}
        result = await provider.validate_config(config)
        assert result is False