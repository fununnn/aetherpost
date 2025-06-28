# AetherPost Code Guidelines

Welcome to AetherPost! This document outlines our coding standards, AI tool usage policies, and best practices for contributors.

## 🤖 AI Development Policy

### ✅ AI Tools Welcome!

AetherPost is an **AI-friendly OSS project**. We encourage and support the use of AI coding assistants:

#### Approved Development Tools
- **GitHub Copilot** - ✅ AI coding assistant
- **TabNine** - ✅ Code completion
- **Cursor** - ✅ AI-powered editor
- **Replit AI** - ✅ Cloud development
- **VS Code Extensions** - ✅ IntelliSense and linting
- **JetBrains IDEs** - ✅ Professional development tools

#### AI Usage Guidelines

**✅ Encouraged Uses:**
- Code generation and completion
- Refactoring and optimization
- Test case generation
- Documentation writing
- Bug fixing assistance
- Code review suggestions
- Architecture planning

**⚠️ Requirements:**
- Always review AI-generated code before committing
- Add appropriate tests for AI-generated functionality
- Ensure code follows our style guidelines
- Document complex AI-generated logic

**❌ Not Allowed:**
- Submitting unreviewed AI code
- AI-generated code without proper testing
- Copying proprietary code patterns from AI
- Including sensitive data in AI prompts

### Development Transparency

We encourage transparency in development practices:

```bash
# Preferred commit format for tool-assisted development
git commit -m "feat: implement Twitter threading support

- Added thread creation functionality
- Implemented proper error handling
- Included comprehensive test coverage"

# For AI-assisted development
git commit -m "feat: add profile validation

🤖 Developed with AI assistance
- Comprehensive input validation
- Error handling and logging
- Unit test coverage"
```

## 🎯 Code Standards

### Python Style Guide

**Base Standards:**
- Follow [PEP 8](https://pep8.org/) with Black formatting
- Line length: 88 characters
- Type hints required for public APIs
- Google-style docstrings

**AI-Enhanced Development:**
```python
from typing import Dict, List, Optional, Union
import asyncio
import logging

logger = logging.getLogger(__name__)

class PlatformConnector:
    """Base class for social media platform connectors.
    
    This class provides a common interface for all platform integrations,
    ensuring consistent behavior across Twitter, Bluesky, Instagram, etc.
    
    Attributes:
        platform_name: Human-readable platform name
        api_version: Platform API version being used
        rate_limits: Per-endpoint rate limiting configuration
    """
    
    def __init__(self, credentials: Dict[str, str]) -> None:
        """Initialize platform connector with authentication.
        
        Args:
            credentials: Platform-specific API credentials
            
        Raises:
            ValueError: If required credentials are missing
            ConnectionError: If initial API validation fails
        """
        self.credentials = self._validate_credentials(credentials)
        self.session = self._create_session()
    
    async def post_content(
        self, 
        content: str, 
        media: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Union[str, int]]] = None
    ) -> Dict[str, Union[str, bool]]:
        """Post content to the platform.
        
        Args:
            content: Text content to post
            media: Optional list of media file paths
            metadata: Platform-specific metadata (hashtags, mentions, etc.)
            
        Returns:
            Dict containing:
                - success: Boolean indicating post success
                - post_id: Platform-specific post identifier
                - url: Direct link to the posted content
                - error: Error message if success is False
                
        Example:
            >>> connector = TwitterConnector(creds)
            >>> result = await connector.post_content(
            ...     "Hello world!",
            ...     metadata={"hashtags": ["test", "demo"]}
            ... )
            >>> print(result["url"])
            "https://twitter.com/user/status/123456789"
        """
        try:
            # Implementation here
            pass
        except Exception as e:
            logger.error(f"Failed to post to {self.platform_name}: {e}")
            return {"success": False, "error": str(e)}
```

### CLI Command Structure

**Typer-based Commands:**
```python
import typer
from rich.console import Console
from typing import Optional, List

app = typer.Typer(help="Platform management commands")
console = Console()

@app.command()
def create(
    name: str = typer.Argument(..., help="Platform connector name"),
    template: str = typer.Option("basic", help="Connector template type"),
    interactive: bool = typer.Option(True, help="Use interactive setup"),
    dry_run: bool = typer.Option(False, help="Show what would be created")
) -> None:
    """Create a new platform connector.
    
    This command scaffolds a new platform integration with proper
    authentication, rate limiting, and error handling.
    """
    if dry_run:
        console.print(f"[dim]Would create {name} connector with {template} template[/dim]")
        return
    
    console.print(f"[green]Creating {name} connector...[/green]")
    # Implementation
```

### Configuration Management

**YAML Configuration:**
```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import yaml

@dataclass
class PlatformConfig:
    """Platform-specific configuration settings."""
    name: str
    enabled: bool = True
    rate_limit: int = 100
    retry_attempts: int = 3
    timeout: float = 30.0
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'PlatformConfig':
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        if self.rate_limit <= 0:
            errors.append("rate_limit must be positive")
        if self.timeout <= 0:
            errors.append("timeout must be positive")
        return errors
```

## 🧪 Testing Standards

### Test Structure

**Comprehensive Testing:**
```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from aetherpost.connectors.twitter import TwitterConnector

class TestTwitterConnector:
    """Test suite for Twitter platform connector."""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock Twitter API credentials for testing."""
        return {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "access_token": "test_token",
            "access_token_secret": "test_token_secret"
        }
    
    @pytest.fixture
    def connector(self, mock_credentials):
        """Create connector instance for testing."""
        return TwitterConnector(mock_credentials)
    
    @pytest.mark.asyncio
    async def test_post_content_success(self, connector):
        """Test successful content posting."""
        with patch.object(connector, '_make_api_request') as mock_request:
            mock_request.return_value = {
                "data": {"id": "123456789", "text": "Test post"}
            }
            
            result = await connector.post_content("Test post")
            
            assert result["success"] is True
            assert result["post_id"] == "123456789"
            assert "twitter.com" in result["url"]
    
    @pytest.mark.asyncio
    async def test_post_content_rate_limit(self, connector):
        """Test rate limit handling."""
        with patch.object(connector, '_make_api_request') as mock_request:
            mock_request.side_effect = RateLimitError("Rate limit exceeded")
            
            result = await connector.post_content("Test post")
            
            assert result["success"] is False
            assert "rate limit" in result["error"].lower()
    
    def test_credential_validation(self):
        """Test credential validation logic."""
        # Test missing credentials
        with pytest.raises(ValueError, match="Missing required credential"):
            TwitterConnector({"api_key": "test"})
        
        # Test invalid credentials
        with pytest.raises(ValueError, match="Invalid credential format"):
            TwitterConnector({"api_key": "", "api_secret": "test"})
```

### Integration Testing

**Real API Testing (Optional):**
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("TWITTER_API_KEY"), reason="No API credentials")
class TestTwitterIntegration:
    """Integration tests with real Twitter API."""
    
    def setup_class(self):
        """Setup real API credentials from environment."""
        self.connector = TwitterConnector({
            "api_key": os.getenv("TWITTER_API_KEY"),
            "api_secret": os.getenv("TWITTER_API_SECRET"),
            "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
            "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        })
    
    @pytest.mark.asyncio
    async def test_authentication(self):
        """Test real API authentication."""
        result = await self.connector.verify_credentials()
        assert result["success"] is True
```

## 📁 Project Architecture

### Plugin System

**Modular Design:**
```
aetherpost_source/
├── plugins/
│   ├── connectors/           # Platform integrations
│   │   ├── twitter/
│   │   │   ├── __init__.py
│   │   │   ├── connector.py  # Main connector class
│   │   │   ├── auth.py       # Authentication logic
│   │   │   ├── models.py     # Data models
│   │   │   └── config.yaml   # Platform configuration
│   │   ├── bluesky/
│   │   └── instagram/
│   ├── ai_providers/         # AI service integrations
│   │   ├── openai/
│   │   ├── gemini/
│   │   └── local/
│   └── analytics/            # Analytics providers
│       ├── basic/
│       └── advanced/
```

### Core Components

**Clean Architecture:**
```python
# core/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ContentGenerator(ABC):
    """Interface for content generation services."""
    
    @abstractmethod
    async def generate_content(
        self, 
        prompt: str, 
        platform: str, 
        style: str = "professional"
    ) -> Dict[str, Any]:
        """Generate platform-optimized content."""
        pass

class PlatformConnector(ABC):
    """Interface for social media platform connectors."""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with platform API."""
        pass
    
    @abstractmethod
    async def post_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """Post content to platform."""
        pass
```

## 🔄 Development Workflow

### AI-Assisted Development Process

1. **Planning Phase**
   ```bash
   # Use AI to help plan features
   claude code --prompt "Plan a new Instagram connector for AetherPost"
   ```

2. **Implementation Phase**
   ```bash
   # Generate boilerplate code
   claude code --generate connector --platform instagram
   
   # Implement core functionality with AI assistance
   # Review and test all generated code
   ```

3. **Testing Phase**
   ```bash
   # Generate comprehensive tests
   claude code --generate tests --for connectors/instagram/
   
   # Run full test suite
   pytest --cov=aetherpost_source --cov-report=html
   ```

4. **Documentation Phase**
   ```bash
   # Generate documentation
   claude code --docs --update README.md
   
   # Review and commit
   git add . && git commit -m "feat: add Instagram connector

   Co-authored-by: Claude <claude@anthropic.com>"
   ```

### Code Review Process

**AI-Enhanced Reviews:**
- Use AI tools to suggest improvements
- Automated code quality checks
- Human review for business logic
- Test coverage verification

## 🚨 Security Guidelines

### API Key Management

**Secure Practices:**
- Never commit API keys to git
- Use `.env.aetherpost` for local development
- Environment variables for production
- Encrypted storage for sensitive data

```python
# security/credential_manager.py
import os
from cryptography.fernet import Fernet
from typing import Dict, Optional

class CredentialManager:
    """Secure credential storage and retrieval."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize with optional encryption key."""
        self.encryption_key = encryption_key or os.getenv("AETHERPOST_ENCRYPTION_KEY")
        if self.encryption_key:
            self.cipher = Fernet(self.encryption_key.encode())
    
    def store_credential(self, key: str, value: str) -> None:
        """Store encrypted credential."""
        if self.cipher:
            encrypted_value = self.cipher.encrypt(value.encode())
            # Store encrypted_value safely
        else:
            # Fallback to environment variable
            os.environ[key] = value
```

## 📝 Documentation Standards

### Code Documentation

**Comprehensive Docstrings:**
```python
def process_campaign_content(
    campaign_config: Dict[str, Any],
    platforms: List[str],
    ai_provider: str = "openai"
) -> Dict[str, List[Dict[str, Any]]]:
    """Process campaign configuration and generate platform-specific content.
    
    This function takes a campaign configuration and generates optimized
    content for each specified platform using the configured AI provider.
    
    Args:
        campaign_config: Campaign configuration dictionary containing:
            - name: Campaign name (required)
            - concept: Core concept description (required)
            - style: Content style (optional, default: "professional")
            - hashtags: List of hashtags (optional)
            - urls: Dict of URLs (main, github, docs, etc.)
        platforms: List of platform names to generate content for
        ai_provider: AI service to use for content generation
    
    Returns:
        Dictionary mapping platform names to lists of generated content items.
        Each content item contains:
            - text: Generated post text
            - hashtags: Platform-specific hashtags
            - media_suggestions: Suggested media types
            - character_count: Content length
            - platform_optimizations: Platform-specific adjustments
    
    Raises:
        ValueError: If campaign_config is missing required fields
        ConnectionError: If AI provider is unreachable
        RateLimitError: If AI provider rate limits are exceeded
    
    Example:
        >>> config = {
        ...     "name": "Product Launch",
        ...     "concept": "Revolutionary AI tool",
        ...     "style": "professional",
        ...     "urls": {"main": "https://myapp.com"}
        ... }
        >>> result = process_campaign_content(config, ["twitter", "bluesky"])
        >>> print(result["twitter"][0]["text"])
        "Introducing our revolutionary AI tool! Transform your workflow..."
    """
    # Implementation here
    pass
```

## 🌟 Contribution Recognition

### AI-Assisted Contributions

We value all contributions, including AI-assisted ones:

- **AI-Generated Code**: Fully credited when properly reviewed and tested
- **Hybrid Development**: Human creativity + AI efficiency
- **Innovation Encouraged**: Novel AI workflows and techniques
- **Learning Supported**: We help contributors learn AI-assisted development

### Recognition System

- **Contributor Credits**: All contributors listed in README
- **AI Tool Credits**: Tools used credited in commit messages
- **Feature Highlights**: Major AI-assisted features showcased
- **Community Showcase**: Best practices shared with community

## 🎓 Learning Resources

### AI Development Best Practices

**Recommended Practices:**
- Start with AI for boilerplate and structure
- Use human expertise for business logic
- Always test AI-generated code thoroughly
- Iterate and improve AI prompts
- Document AI-assisted development decisions

**Learning Path:**
1. **Beginner**: Use AI for simple code completion
2. **Intermediate**: Generate test cases and documentation
3. **Advanced**: Architect complex features with AI assistance
4. **Expert**: Create AI-enhanced development workflows

---

**Questions about AI-assisted development?** Open an issue with the `ai-development` label!

**Ready to contribute?** Check our [CONTRIBUTING.md](CONTRIBUTING.md) for the step-by-step process!

🚀 **Happy coding with AI!**