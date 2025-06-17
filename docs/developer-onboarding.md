# AetherPost Developer Onboarding Guide

## Welcome to AetherPost! 🚀

AetherPost is an enterprise-grade social media automation platform that helps businesses manage their content across multiple platforms efficiently.

## Quick Start (5 minutes)

### 1. Clone and Setup
```bash
# Clone repository
git clone https://github.com/your-org/aetherpost.git
cd aetherpost

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Run Your First Command
```bash
# Initialize AetherPost
aetherpost init

# Create a test post
aetherpost post "Hello from AetherPost!" --platform twitter
```

## Architecture Overview

```
aetherpost/
├── aetherpost/
│   ├── core/           # Core functionality
│   ├── plugins/        # Platform connectors
│   ├── cli/            # Command-line interface
│   └── utils/          # Shared utilities
├── tests/              # Test suite
├── docs/               # Documentation
└── examples/           # Usage examples
```

## Core Concepts

### 1. Campaigns
Organize your content strategy:
```yaml
# campaign.yaml
name: "Product Launch"
schedule:
  start_date: "2025-01-20"
  frequency: "daily"
  
posts:
  - content: "Exciting news coming soon!"
    platforms: ["twitter", "linkedin"]
```

### 2. Platform Connectors
Each platform has its own connector:
```python
# Example: Creating a custom connector
from aetherpost.plugins.base import BaseConnector

class MyPlatformConnector(BaseConnector):
    def post(self, content, media=None):
        # Your implementation
        pass
```

### 3. Content Generation
AI-powered content creation:
```python
from aetherpost.core.content import ContentGenerator

generator = ContentGenerator()
content = generator.create(
    topic="Tech Innovation",
    tone="professional",
    length=280
)
```

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-platform

# Make changes
# Write tests
# Run tests
pytest tests/

# Submit PR
git push origin feature/new-platform
```

### 2. Testing
```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_connectors.py::test_twitter

# Check coverage
pytest --cov=aetherpost
```

### 3. Code Style
```bash
# Format code
black aetherpost/

# Lint
flake8 aetherpost/

# Type checking
mypy aetherpost/
```

## Adding a New Platform

### Step 1: Create Connector
```python
# aetherpost/plugins/connectors/newplatform/connector.py
from aetherpost.plugins.base import BaseConnector

class NewPlatformConnector(BaseConnector):
    def __init__(self, config):
        super().__init__(config)
        self.api = self._setup_api()
    
    def post(self, content, media=None):
        return self.api.create_post(content, media)
    
    def delete(self, post_id):
        return self.api.delete_post(post_id)
```

### Step 2: Add Configuration
```python
# aetherpost/plugins/connectors/newplatform/config.py
from pydantic import BaseModel

class NewPlatformConfig(BaseModel):
    api_key: str
    api_secret: str
    base_url: str = "https://api.newplatform.com"
```

### Step 3: Register Plugin
```python
# aetherpost/plugins/registry.py
AVAILABLE_PLUGINS = {
    "twitter": "aetherpost.plugins.connectors.twitter",
    "newplatform": "aetherpost.plugins.connectors.newplatform",
}
```

## Common Tasks

### Running Locally
```bash
# Start development server
aetherpost server --debug

# Watch for changes
aetherpost dev --reload
```

### Database Operations
```bash
# Initialize database
aetherpost db init

# Run migrations
aetherpost db migrate

# Seed test data
aetherpost db seed
```

### Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use built-in debugger
import pdb; pdb.set_trace()
```

## API Reference Quick Links

- [Core API](./api-reference/core.md)
- [Plugin API](./api-reference/plugins.md)
- [CLI Commands](./api-reference/cli.md)
- [Configuration](./api-reference/config.md)

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure package is installed in development mode
   pip install -e .
   ```

2. **API Rate Limits**
   ```python
   # Use built-in rate limiting
   from aetherpost.utils.rate_limit import RateLimiter
   
   limiter = RateLimiter(calls=100, period=3600)
   ```

3. **Authentication Failures**
   ```bash
   # Re-authenticate
   aetherpost auth refresh --platform twitter
   ```

## Getting Help

- 📖 [Full Documentation](https://docs.aetherpost.dev)
- 💬 [Discord Community](https://discord.gg/aetherpost)
- 🐛 [Issue Tracker](https://github.com/your-org/aetherpost/issues)
- 📧 Email: dev@aetherpost.dev

## Next Steps

1. ✅ Complete the [Tutorial](./tutorials/first-campaign.md)
2. 📚 Read the [Architecture Guide](./architecture.md)
3. 🤝 Review [Contributing Guidelines](./contributing.md)
4. 🎯 Pick a [Good First Issue](https://github.com/your-org/aetherpost/labels/good%20first%20issue)

Welcome aboard! We're excited to have you contributing to AetherPost! 🎉