# AetherPost - Promotion as Code

🚀 **AI-powered social media automation for developers**

AetherPost automates your app promotion across social media platforms using AI-generated content and Infrastructure-as-Code principles.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AI-Friendly](https://img.shields.io/badge/AI--Friendly-Claude%20Code%20%7C%20Copilot-purple.svg)](CODE_GUIDELINES.md)
[![Beginner-Friendly](https://img.shields.io/badge/Beginner--Friendly-GUI%20Setup-green.svg)](GUI_SETUP_GUIDE.md)

## ✨ Features

### OSS Edition (Free)
- 🎯 **Declarative configuration** - Define campaigns in YAML
- 🤖 **AI-generated content** - OpenAI GPT-powered posts
- 📱 **Multi-platform support** - Twitter, Reddit, YouTube, Bluesky, Instagram (5 platforms)
- 🆕 **Universal profile management** - Sync profiles across all platforms automatically
- 🔒 **Secure** - Encrypted credential storage with .env.aetherpost
- ⚡ **Auto-setup mode** - Zero-prompt initialization for AI tools
- 📊 **Smart notifications** - Slack/LINE preview notifications
- 🎨 **Style options** - Casual, professional, technical, humorous
- 🌍 **Multi-language** - 20+ languages supported
- 📝 **Usage limits** - 50 posts/day, 5 campaigns

### Key Capabilities
- 🚀 **Two setup modes** - Auto-setup (Claude Code) vs Interactive prompts
- 🔄 **Terraform-style workflow** - init, plan, apply commands
- 📱 **Notification modes** - Preview confirmations or auto-posting
- 🎯 **API tier system** - Starter, Recommended, Advanced, Complete
- ⚡ **Production ready** - 100% tested with real API validation

## 🚀 Quick Start

AetherPost supports **two setup modes** based on file detection:

### 🤖 Auto Setup Mode

**For automated workflows with pre-configured files**

```bash
# 1. Install AetherPost
pip install aetherpost

# 2. Pre-create configuration files:
#    - campaign.yaml (project settings)
#    - .env.aetherpost (API keys)

# 3. Auto-initialize (zero prompts)
aetherpost init

# 4. Preview and deploy
aetherpost plan && aetherpost apply
```

### 📝 Interactive Setup Mode (Manual Configuration)

**For step-by-step guided setup**

```bash
# 1. Install AetherPost
pip install aetherpost

# 2. Interactive setup with prompts
aetherpost init

# 3. Preview and deploy
aetherpost plan && aetherpost apply
```

> **Auto-Detection:** If `campaign.yaml` exists → Auto Setup Mode, otherwise → Interactive Setup Mode

## 📋 Configuration Examples

### Complete campaign.yaml
```yaml
name: "my-awesome-app"
concept: "AI-powered task manager that learns your habits"
url: "https://github.com/user/my-awesome-app"
platforms: 
  - twitter
  - reddit
  - youtube

content:
  style: professional  # casual, professional, technical, humorous
  action: "Try it free!"
  language: en  # en, ja, es, fr, de, ko, zh, pt, ru, ar, etc.
  hashtags:
    - "#AI"
    - "#ProductivityTool"
    - "#OpenSource"

limits:
  free_tier: true
  max_posts_per_day: 50

notifications:
  enabled: true      # Send preview notifications
  auto_apply: false  # Require confirmation (set true for auto-posting)

# Optional: Template hint for advanced features
template: "production"  # starter, production, enterprise
```

### API Configuration (.env.aetherpost)
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

# Notifications (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

### Multi-Language Examples
```yaml
# Japanese Campaign
content:
  style: casual
  action: "今すぐ試してみてください！"
  language: ja
  hashtags: ["#AI", "#生産性", "#ツール"]

# Spanish Campaign  
content:
  style: professional
  action: "Pruébalo ahora"
  language: es
  hashtags: ["#IA", "#Productividad"]
```

**Supported Languages**: English (en), Japanese (ja), Spanish (es), French (fr), German (de), Korean (ko), Chinese (zh), Portuguese (pt), Russian (ru), Arabic (ar), and more.

## 🔧 Commands (Terraform-style)

| Command | Description | Mode |
|---------|-------------|------|
| `aetherpost init` | Initialize workspace (auto-detects existing config) | Auto/Interactive |
| `aetherpost plan` | Preview AI-generated content for all platforms | Both |
| `aetherpost apply` | Execute campaign (respects notification settings) | Both |
| `aetherpost status` | Check campaign status and analytics | Both |
| `aetherpost auth` | Manage API authentication | Both |

### Notification Modes
- **Preview Mode** (`notifications.enabled: true`) - Sends preview notification before posting
- **Auto Mode** (`notifications.auto_apply: true`) - Posts immediately without confirmation

## 🔑 API Requirements

### Quick Reference
| Level | APIs Required | Monthly Cost | Setup Time |
|-------|---------------|--------------|------------|
| **Starter** | OpenAI + Twitter | $5-15 | ~10 min |
| **Recommended** | + Reddit | $5-15 | ~20 min |
| **Advanced** | + YouTube | $10-25 | ~30 min |
| **Complete** | + Bluesky + Instagram | $15-35 | ~45 min |

> 💡 **Auto Setup**: The `aetherpost init` command guides you through API collection with direct setup links and validation.

## 📖 Documentation

### For AI Tools & Claude Code
| Document | Purpose | Use Case |
|----------|---------|----------|
| **[AUTO_SETUP_README.md](AUTO_SETUP_README.md)** | **Auto-setup guide** | **Zero-prompt automation** |
| [sample-campaign.yaml](sample-campaign.yaml) | Configuration template | File generation |
| [sample.env.aetherpost](sample.env.aetherpost) | API keys template | Environment setup |

### For Manual Setup
**🌐 [Complete Documentation Site](https://d3b75mcubdhimz.cloudfront.net)**

| Document | Purpose |
|----------|---------|
| [Getting Started](https://d3b75mcubdhimz.cloudfront.net/getting-started.html) | Step-by-step guide |
| [API Requirements](https://d3b75mcubdhimz.cloudfront.net/#api-requirements) | API setup levels |
| [Platform Setup](https://d3b75mcubdhimz.cloudfront.net/guides/platforms.html) | Platform integration |

## 🤝 Contributing

**AetherPost welcomes all contributors!** We're an AI-friendly OSS project that supports modern development workflows.

### 🤖 AI-Assisted Development Welcome
- ✅ **Claude Code, GitHub Copilot, and other AI tools fully supported**
- ✅ **AI-generated code accepted** (with proper review and testing)
- ✅ **Co-author credit** for AI contributions encouraged

### 🔰 Beginner-Friendly
- 📖 **[GUI Setup Guide](GUI_SETUP_GUIDE.md)** - No command line required!
- 📋 **[Code Guidelines](CODE_GUIDELINES.md)** - Comprehensive standards
- 🛠️ **[Contributing Guide](CONTRIBUTING.md)** - Step-by-step process

### 🎯 Contribution Opportunities
- **New platform connectors** (Instagram, LinkedIn, TikTok)
- **AI provider integrations** (Google Gemini, local models)
- **Analytics and visualization**
- **Documentation and tutorials**
- **Bug fixes and improvements**

**Get started**: [CONTRIBUTING.md](CONTRIBUTING.md) | **Need help?** [GitHub Discussions](https://github.com/fununnn/aetherpost/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Terraform's Infrastructure-as-Code approach
- Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
- AI content generation powered by advanced language models and [OpenAI](https://openai.com/)