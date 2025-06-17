# AetherPost API Reference

## Core API

### ContentGenerator

AI-powered content generation for social media posts.

```python
from aetherpost.core.content import ContentGenerator

generator = ContentGenerator(model="gpt-4")
```

#### Methods

##### `create(topic, tone, length, platform=None)`
Generate content based on parameters.

**Parameters:**
- `topic` (str): Main topic or theme
- `tone` (str): Writing style - "professional", "casual", "humorous", "formal"
- `length` (int): Maximum character count
- `platform` (str, optional): Target platform for optimization

**Returns:**
- `dict`: Generated content with metadata

**Example:**
```python
content = generator.create(
    topic="AI Technology",
    tone="professional",
    length=280,
    platform="twitter"
)
# Returns: {
#   "text": "AI is revolutionizing...",
#   "hashtags": ["#AI", "#Technology"],
#   "metadata": {"sentiment": 0.8, "readability": 9.2}
# }
```

### CampaignManager

Manage content campaigns across platforms.

```python
from aetherpost.core.campaigns import CampaignManager

manager = CampaignManager()
```

#### Methods

##### `create_campaign(config)`
Create a new campaign from configuration.

**Parameters:**
- `config` (dict): Campaign configuration

**Example:**
```python
campaign = manager.create_campaign({
    "name": "Product Launch",
    "schedule": {
        "start_date": "2025-01-20",
        "frequency": "daily",
        "times": ["09:00", "15:00"]
    },
    "platforms": ["twitter", "linkedin"],
    "content_strategy": {
        "topics": ["innovation", "product features"],
        "tone": "exciting"
    }
})
```

##### `execute(campaign_id, dry_run=False)`
Execute a campaign.

**Parameters:**
- `campaign_id` (str): Campaign identifier
- `dry_run` (bool): Preview without posting

**Returns:**
- `CampaignResult`: Execution results

### SecurityManager

Handle authentication and encryption.

```python
from aetherpost.core.security import SecurityManager

security = SecurityManager()
```

#### Methods

##### `encrypt_credentials(platform, credentials)`
Securely store platform credentials.

**Parameters:**
- `platform` (str): Platform name
- `credentials` (dict): API keys and tokens

**Example:**
```python
security.encrypt_credentials("twitter", {
    "api_key": "xxx",
    "api_secret": "yyy",
    "access_token": "zzz"
})
```

## Plugin API

### BaseConnector

Abstract base class for platform connectors.

```python
from aetherpost.plugins.base import BaseConnector

class CustomConnector(BaseConnector):
    def post(self, content, media=None):
        # Implementation
        pass
```

#### Required Methods

##### `post(content, media=None, **kwargs)`
Post content to platform.

**Parameters:**
- `content` (str): Text content
- `media` (list, optional): Media file paths
- `**kwargs`: Platform-specific options

**Returns:**
- `PostResult`: Post ID and metadata

##### `delete(post_id)`
Delete a post.

**Parameters:**
- `post_id` (str): Platform post identifier

**Returns:**
- `bool`: Success status

##### `get_analytics(post_id)`
Retrieve post analytics.

**Parameters:**
- `post_id` (str): Platform post identifier

**Returns:**
- `dict`: Engagement metrics

### PluginRegistry

Dynamic plugin loading system.

```python
from aetherpost.plugins import PluginRegistry

registry = PluginRegistry()
```

#### Methods

##### `register(name, module_path)`
Register a new plugin.

**Parameters:**
- `name` (str): Plugin identifier
- `module_path` (str): Import path

##### `get_connector(platform, config)`
Get configured connector instance.

**Parameters:**
- `platform` (str): Platform name
- `config` (dict): Platform configuration

**Returns:**
- `BaseConnector`: Configured connector

## CLI API

### Command Structure

```bash
aetherpost [OPTIONS] COMMAND [ARGS]...
```

### Global Options
- `--config PATH`: Configuration file path
- `--verbose`: Enable debug logging
- `--quiet`: Suppress output

### Commands

#### `init`
Initialize AetherPost in current directory.

```bash
aetherpost init [--template TEMPLATE]
```

Options:
- `--template`: Starter template ("basic", "enterprise", "agency")

#### `post`
Create a post across platforms.

```bash
aetherpost post "Content" [OPTIONS]
```

Options:
- `--platform PLATFORM`: Target platform(s)
- `--media PATH`: Attach media files
- `--schedule TIME`: Schedule for later
- `--campaign NAME`: Add to campaign

Example:
```bash
aetherpost post "Check out our new feature!" \
  --platform twitter,linkedin \
  --media image.png \
  --schedule "2025-01-20 14:00"
```

#### `campaign`
Manage campaigns.

```bash
aetherpost campaign [create|list|run|delete] [OPTIONS]
```

Subcommands:
- `create`: Create from YAML file
- `list`: Show all campaigns
- `run`: Execute campaign
- `delete`: Remove campaign

#### `auth`
Manage platform authentication.

```bash
aetherpost auth [login|logout|status] PLATFORM
```

Example:
```bash
aetherpost auth login twitter
# Opens browser for OAuth flow
```

#### `analytics`
View post and campaign analytics.

```bash
aetherpost analytics [post|campaign] ID
```

Options:
- `--format`: Output format (json, csv, table)
- `--metric`: Specific metric to display

## Configuration API

### Config Schema

```python
from aetherpost.core.config import AetherPostConfig

config = AetherPostConfig(
    platforms={
        "twitter": {
            "api_key": "xxx",
            "rate_limit": 300
        }
    },
    content={
        "default_tone": "professional",
        "hashtag_limit": 5
    },
    security={
        "encryption_key": "xxx",
        "token_expiry": 3600
    }
)
```

### Environment Variables

- `AETHERPOST_CONFIG`: Config file path
- `AETHERPOST_LOG_LEVEL`: Logging level
- `AETHERPOST_CACHE_DIR`: Cache directory
- `AETHERPOST_PLUGIN_DIR`: Custom plugins

## Data Models

### Post
```python
class Post(BaseModel):
    id: str
    content: str
    platform: str
    media: List[str] = []
    scheduled_time: Optional[datetime]
    metadata: Dict[str, Any] = {}
```

### Campaign
```python
class Campaign(BaseModel):
    id: str
    name: str
    schedule: Schedule
    platforms: List[str]
    posts: List[Post]
    status: str = "draft"
```

### Analytics
```python
class Analytics(BaseModel):
    post_id: str
    views: int
    likes: int
    shares: int
    comments: int
    engagement_rate: float
    timestamp: datetime
```

## Error Handling

### Custom Exceptions

```python
from aetherpost.exceptions import (
    AetherPostError,
    AuthenticationError,
    RateLimitError,
    ConfigurationError
)

try:
    connector.post(content)
except RateLimitError as e:
    print(f"Rate limit hit: {e.retry_after} seconds")
except AuthenticationError:
    print("Please re-authenticate")
```

## Rate Limiting

Built-in rate limiter for API calls:

```python
from aetherpost.utils.rate_limit import RateLimiter

limiter = RateLimiter(
    calls=100,
    period=3600,
    burst=10
)

@limiter.limit
def api_call():
    # Your API call
    pass
```

## Webhooks

### Webhook Events
- `post.created`
- `post.deleted`
- `campaign.started`
- `campaign.completed`
- `error.occurred`

### Setup
```python
from aetherpost.webhooks import WebhookManager

webhooks = WebhookManager()
webhooks.register(
    "https://your-endpoint.com/webhook",
    events=["post.created", "campaign.completed"]
)
```

## Testing Utilities

### Mock Connectors
```python
from aetherpost.testing import MockConnector

mock = MockConnector()
mock.set_response("post", {"id": "123", "url": "https://..."})
```

### Test Fixtures
```python
from aetherpost.testing.fixtures import (
    sample_post,
    sample_campaign,
    sample_config
)
```

## Performance Tips

1. **Batch Operations**
   ```python
   # Good
   connector.post_batch(posts)
   
   # Avoid
   for post in posts:
       connector.post(post)
   ```

2. **Async Operations**
   ```python
   import asyncio
   from aetherpost.async_api import AsyncConnector
   
   async def post_async():
       connector = AsyncConnector()
       await connector.post(content)
   ```

3. **Caching**
   ```python
   from aetherpost.cache import cache
   
   @cache.memoize(timeout=300)
   def expensive_operation():
       # Cached for 5 minutes
       pass
   ```

## Version Compatibility

| AetherPost Version | Python | API Version |
|-------------------|---------|-------------|
| 2.0.x | 3.8+ | v2 |
| 1.x.x | 3.7+ | v1 |

## Migration Guide

### From v1 to v2
```python
# v1
from aetherpost import PostManager
manager = PostManager()

# v2
from aetherpost.core import ContentManager
manager = ContentManager()
```

See [Migration Guide](./migration-v1-to-v2.md) for complete details.