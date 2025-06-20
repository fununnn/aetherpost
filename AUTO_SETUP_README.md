# AetherPost Auto-Setup Guide for Claude Code & AI Tools

Complete documentation for automated AetherPost initialization without interactive prompts.

## 🎯 Overview

AetherPost supports **two setup modes**:
1. **Auto Setup Mode** - For AI tools, Claude Code, automated workflows
2. **Interactive Setup Mode** - For manual configuration with guided prompts

## 🚀 Auto Setup Mode (Zero Prompts)

### Detection Logic
```bash
# If campaign.yaml exists → Auto Setup Mode (no prompts)
# If campaign.yaml missing → Interactive Setup Mode (guided prompts)
```

### Implementation Steps

#### 1. Install AetherPost
```bash
pip install aetherpost
```

#### 2. Create Required Files

**campaign.yaml** (Required)
```yaml
name: "my-awesome-project"
concept: "AI-powered development tool that enhances productivity"
url: "https://github.com/user/my-awesome-project"
platforms: 
  - twitter
  - reddit
  - youtube

content:
  style: professional  # casual, professional, technical, humorous
  action: "Try it free!"
  language: en  # en, ja, es, fr, de, ko, zh, pt, ru, ar
  hashtags:
    - "#OpenSource"
    - "#DevTools"
    - "#AI"

limits:
  free_tier: true
  max_posts_per_day: 50

notifications:
  enabled: true      # true = preview notifications, false = silent
  auto_apply: false  # true = auto-post, false = require confirmation

# Optional: Specify template (starter, production, enterprise)
template: "production"
```

**.env.aetherpost** (Recommended)
```bash
# AI Services (Required)
OPENAI_API_KEY=sk-proj-your_openai_key_here

# Twitter (Required for Twitter platform)
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here

# Reddit (Required for Reddit platform)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USERNAME=your_reddit_username_here
REDDIT_PASSWORD=your_reddit_password_here

# YouTube (Required for YouTube platform)
YOUTUBE_CLIENT_ID=your_youtube_client_id_here
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret_here

# Bluesky (Required for Bluesky platform)
BLUESKY_HANDLE=your.handle.bsky.social
BLUESKY_PASSWORD=your_bluesky_password

# Notifications (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
LINE_NOTIFY_TOKEN=your_line_notify_token_here
```

#### 3. Execute Auto-Setup
```bash
aetherpost init
# ✅ Detects campaign.yaml → Skips all interactive prompts
# ✅ Detects .env.aetherpost → Loads API keys automatically
# ✅ Creates .aetherpost/ workspace → Ready to use
```

#### 4. Execute Campaign
```bash
aetherpost plan   # Preview AI-generated content
aetherpost apply  # Deploy to platforms (respects notification settings)
```

## 🔧 Platform Requirements

### Minimum Setup (Starter Level)
- **OpenAI API** - AI content generation
- **Twitter API v2** - Tweet posting
- Cost: ~$5-15/month

### Recommended Setup
- **OpenAI API** - AI content generation  
- **Twitter API v2** - Tweet posting
- **Reddit API** - Subreddit posting (Free!)
- Cost: ~$5-15/month

### Advanced Setup  
- **All above** +
- **YouTube Data API v3** - Video management
- Cost: ~$10-25/month

### Complete Setup
- **All above** +
- **Bluesky API** - Decentralized social
- **Instagram Basic Display** - Photo posting
- Cost: ~$15-35/month

## 🤖 Claude Code Implementation Example

```javascript
// 1. Analyze project to determine configuration
const projectAnalysis = analyzeProject();

// 2. Generate campaign.yaml
const campaignConfig = {
  name: projectAnalysis.name,
  concept: projectAnalysis.description,
  platforms: determinePlatforms(projectAnalysis.type),
  content: {
    style: projectAnalysis.tone || 'professional',
    language: projectAnalysis.language || 'en',
    hashtags: generateHashtags(projectAnalysis.keywords)
  },
  notifications: {
    enabled: true,
    auto_apply: false  // Set to true for full automation
  },
  template: projectAnalysis.complexity >= 3 ? 'production' : 'starter'
};

writeFile('campaign.yaml', yaml.stringify(campaignConfig));

// 3. Create .env.aetherpost template
const envTemplate = `# AetherPost API Configuration
OPENAI_API_KEY=\${OPENAI_API_KEY}
TWITTER_API_KEY=\${TWITTER_API_KEY}
TWITTER_API_SECRET=\${TWITTER_API_SECRET}
TWITTER_ACCESS_TOKEN=\${TWITTER_ACCESS_TOKEN}
TWITTER_ACCESS_TOKEN_SECRET=\${TWITTER_ACCESS_TOKEN_SECRET}
${campaignConfig.platforms.includes('reddit') ? `
REDDIT_CLIENT_ID=\${REDDIT_CLIENT_ID}
REDDIT_CLIENT_SECRET=\${REDDIT_CLIENT_SECRET}
REDDIT_USERNAME=\${REDDIT_USERNAME}
REDDIT_PASSWORD=\${REDDIT_PASSWORD}` : ''}`;

writeFile('.env.aetherpost', envTemplate);

// 4. User populates API keys in .env.aetherpost

// 5. Execute auto-setup
exec('aetherpost init');    // No prompts, instant setup
exec('aetherpost plan');    // Preview content
exec('aetherpost apply');   // Execute campaign
```

## ⚡ Notification Modes

### Preview Mode (Default)
```yaml
notifications:
  enabled: true
  auto_apply: false
```
- Sends preview notification to Slack/LINE
- Requires confirmation before posting
- Safe for production use

### Auto Mode (Full Automation)
```yaml
notifications:
  enabled: false  # or true for notifications without confirmation
  auto_apply: true
```
- Posts immediately without confirmation
- Ideal for scheduled/automated campaigns
- Use with caution

## 🔍 Validation & Troubleshooting

### File Validation
```bash
# Check if auto-setup will trigger
ls campaign.yaml     # Should exist
ls .env.aetherpost   # Should exist with API keys

# Test auto-setup
aetherpost init      # Should show "Auto Setup Mode" message
```

### Common Issues
1. **campaign.yaml syntax error** → Check YAML formatting
2. **Missing API keys** → Verify .env.aetherpost format
3. **Permission errors** → Check file permissions
4. **Platform errors** → Validate API credentials

## 📊 Complete Workflow Summary

```bash
# For Claude Code & AI Tools:
# 1. Pre-create files
echo "Creating campaign.yaml and .env.aetherpost..."

# 2. One-command setup
aetherpost init && aetherpost plan && aetherpost apply

# Total commands: 1 (vs 10+ interactive prompts)
# Setup time: <30 seconds (vs 5-10 minutes)
# User intervention: 0 prompts (vs 8+ questions)
```

This auto-setup approach reduces the barrier to social media automation from manual configuration to file-based automation, perfect for AI tools and automated workflows.