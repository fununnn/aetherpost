# Configuration Reference

This guide covers all configuration options for AetherPost OSS.

## Configuration Files

AetherPost uses several configuration files:

```
~/.aetherpost/           # User configuration directory
├── config.yaml          # Main configuration
├── credentials.json     # Encrypted API keys
├── usage.json          # Usage tracking (OSS limits)
└── logs/               # Application logs

./campaign.yaml         # Project-specific campaign
./.env.aetherpost      # Environment variables
```

## Campaign Configuration

### Basic Structure

```yaml
# campaign.yaml - Minimal example
name: "my-awesome-app"
concept: "AI-powered task manager"
platforms: [twitter, bluesky]
content:
  style: casual
  action: "Try it free!"
```

### Complete Example

```yaml
# campaign.yaml - Complete example
name: "taskmaster"
concept: "AI-powered task manager that learns your work patterns"
url: "https://taskmaster.app"
version: "2.1.0"

# Target platforms
platforms:
  - twitter
  - bluesky
  - mastodon

# Content configuration
content:
  style: casual              # casual, professional, technical, humorous
  action: "Try it free!"     # Call-to-action
  hashtags:                  # Optional hashtags
    - "productivity"
    - "AI"
    - "opensource"
  
  # Platform-specific overrides
  twitter:
    style: professional
    max_length: 280
  
  bluesky:
    style: casual
    include_url: true

# Scheduling
schedule:
  timezone: "UTC"
  times:
    - "09:00"  # 9 AM
    - "15:00"  # 3 PM
  frequency: daily  # daily, weekly, manual

# Media (OSS: basic only)
media:
  generate: false    # Auto-generate images
  path: "./images"   # Custom image directory

# Analytics (OSS: basic only)
analytics:
  enabled: true
  track_engagement: true
  export_format: json

# Advanced options
advanced:
  dry_run: false
  backup_posts: true
  review_required: true
```

## Environment Variables

### Required API Keys

```bash
# AI Providers (choose one or both)
OPENAI_API_KEY="sk-..."              # OpenAI GPT models
AI_API_KEY="sk-ant-..."       # AI Provider

# Social Media Platforms
TWITTER_API_KEY="..."
TWITTER_API_SECRET="..."
TWITTER_ACCESS_TOKEN="..."
TWITTER_ACCESS_TOKEN_SECRET="..."

BLUESKY_HANDLE="user.bsky.social"
BLUESKY_PASSWORD="..."

MASTODON_ACCESS_TOKEN="..."
MASTODON_API_BASE_URL="https://mastodon.social"
```

### Optional Configuration

```bash
# AetherPost Configuration
AETHERPOST_EDITION="oss"             # oss or enterprise
AETHERPOST_CONFIG_DIR="~/.aetherpost"
AETHERPOST_LOG_LEVEL="INFO"          # DEBUG, INFO, WARNING, ERROR
AETHERPOST_CACHE_DIR="~/.aetherpost/cache"

# Security
AETHERPOST_ENCRYPT_CREDENTIALS="true"
AETHERPOST_MASTER_KEY="..."          # For credential encryption
```

## User Configuration

### ~/.aetherpost/config.yaml

```yaml
# Global user configuration
user:
  name: "Your Name"
  email: "your@email.com"
  timezone: "UTC"

# Default preferences
defaults:
  platforms: [twitter]
  style: casual
  ai_provider: openai
  review_required: true

# AI Configuration
ai:
  provider: openai        # openai, anthropic, both
  model: gpt-4           # Model to use
  temperature: 0.7       # Creativity (0.0-1.0)
  max_tokens: 500        # Response length
  
  # Provider-specific settings
  openai:
    model: "gpt-4"
    temperature: 0.7
  
  anthropic:
    model: "ai-model-v3-20240229"
    max_tokens: 1000

# Platform defaults
platforms:
  twitter:
    style: professional
    include_hashtags: true
    max_length: 280
  
  bluesky:
    style: casual
    include_url: true
  
  mastodon:
    style: technical
    include_hashtags: true

# OSS Edition Limits (read-only)
limits:
  max_platforms: 3
  max_posts_per_day: 50
  max_campaigns: 5
  features:
    advanced_analytics: false
    autopilot: false
    team_management: false

# Logging
logging:
  level: INFO
  file: "~/.aetherpost/logs/aetherpost.log"
  max_size: "10MB"
  backup_count: 5
```

## Platform-Specific Configuration

### Twitter/X

```yaml
twitter:
  style: professional
  max_length: 280
  include_hashtags: true
  thread_support: false     # Enterprise only
  auto_reply: false         # Enterprise only
  
  # Rate limiting
  rate_limit:
    posts_per_hour: 10
    posts_per_day: 50
```

### Bluesky

```yaml
bluesky:
  style: casual
  include_url: true
  include_preview: true
  max_length: 300
  
  # Moderation
  content_filter: moderate
```

### Mastodon

```yaml
mastodon:
  instance: "mastodon.social"
  style: technical
  visibility: public       # public, unlisted, private
  sensitive: false
  spoiler_text: ""
```

## Content Templates

### Style Configuration

```yaml
content:
  styles:
    casual:
      tone: friendly
      emoji_usage: moderate
      formality: low
      
    professional:
      tone: authoritative
      emoji_usage: minimal
      formality: high
      
    technical:
      tone: informative
      emoji_usage: rare
      formality: medium
      technical_terms: encouraged
      
    humorous:
      tone: playful
      emoji_usage: high
      formality: low
      humor_type: light
```

### Content Types

```yaml
content:
  types:
    announcement:
      template: "Exciting news! {concept}. {action}"
      platforms: [twitter, bluesky]
      
    feature_update:
      template: "New in v{version}: {description}. {action}"
      hashtags: ["update", "features"]
      
    maintenance:
      template: "Scheduled maintenance for {name}. {details}"
      style: professional
```

## Command-Line Configuration

### Global Options

```bash
# Configuration file location
aetherpost --config=/path/to/config.yaml

# Verbose output
aetherpost --verbose plan

# Dry run mode
aetherpost --dry-run apply

# Specific platform
aetherpost --platform=twitter now "Hello world"
```

### Environment Override

```bash
# Override AI provider
AETHERPOST_AI_PROVIDER=anthropic aetherpost plan

# Override log level
AETHERPOST_LOG_LEVEL=DEBUG aetherpost apply
```

## Security Configuration

### Credential Encryption

```yaml
security:
  encrypt_credentials: true
  master_key_file: "~/.aetherpost/master.key"
  key_rotation_days: 90
  
  # Backup
  backup_encrypted: true
  backup_location: "~/.aetherpost/backups"
```

### Rate Limiting

```yaml
rate_limiting:
  enabled: true
  
  # Global limits (OSS)
  daily_posts: 50
  hourly_posts: 10
  
  # Per-platform limits
  twitter:
    posts_per_hour: 5
    posts_per_day: 20
  
  bluesky:
    posts_per_hour: 10
    posts_per_day: 30
```

## Validation

### Configuration Validation

```bash
# Validate campaign configuration
aetherpost validate campaign.yaml

# Validate user configuration
aetherpost validate --config

# Check API key setup
aetherpost auth test
```

### Schema

AetherPost validates configuration against JSON schemas:

```bash
# Check schema compliance
aetherpost validate --schema campaign.yaml

# Generate sample configuration
aetherpost init --sample > sample-campaign.yaml
```

## Migration

### From v1.x to v2.x

```bash
# Backup current configuration
cp -r ~/.aetherpost ~/.aetherpost.backup

# Run migration
aetherpost migrate --from=1.x --to=2.x

# Verify migration
aetherpost validate --config
```

## Troubleshooting

### Common Issues

1. **Invalid Configuration**
   ```bash
   aetherpost validate campaign.yaml
   ```

2. **Missing API Keys**
   ```bash
   aetherpost auth setup
   ```

3. **Permission Issues**
   ```bash
   chmod 600 ~/.aetherpost/credentials.json
   ```

4. **Platform Limits**
   ```bash
   aetherpost stats --usage
   ```

### Debug Mode

```bash
# Enable debug logging
export AETHERPOST_LOG_LEVEL=DEBUG
aetherpost plan

# Check configuration loading
aetherpost debug config

# Test platform connections
aetherpost debug platforms
```

## See Also

- [Installation Guide](installation.md)
- [Platform Setup](platforms.md)
- [AI Provider Setup](ai-providers.md)
- [Examples](examples.md)