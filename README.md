# AetherPost - Promotion as Code

🚀 **AI-powered social media automation for developers**

AetherPost automates your app promotion across social media platforms using AI-generated content and Infrastructure-as-Code principles.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

### OSS Edition (Free)
- 🎯 **Declarative configuration** - Define campaigns in YAML
- 🤖 **AI-generated content** - [AI Service]/OpenAI powered posts
- 📱 **Multi-platform support** - Twitter, Bluesky, Mastodon (up to 3 platforms)
- 🔒 **Secure** - Encrypted credential storage
- ⚡ **Idempotent** - Safe to run multiple times
- 📊 **Basic analytics** - Track post performance
- 🎨 **Style options** - Casual, professional, technical, humorous
- 📝 **Usage limits** - 50 posts/day, 5 campaigns

### Enterprise Edition
- 🚀 **Unlimited usage** - No limits on posts or platforms
- 🤖 **AI Autopilot** - Fully automated content generation
- 📈 **Advanced analytics** - Real-time dashboards and insights
- 👥 **Team management** - Collaboration and approval workflows
- 🔍 **Monitoring** - Comprehensive system monitoring
- 🎯 **Priority support** - Dedicated support team

## 🚀 Quick Start

### Installation & Setup

```bash
# One command install!
pip install aetherpost

# Create campaign
aetherpost init

# That's it!
```

### Usage

```bash
# Preview content
aetherpost plan

# Execute posts
aetherpost apply
```

## 📋 Configuration Example

### Basic Configuration
```yaml
name: "my-awesome-app"
concept: "AI-powered task manager that learns your habits"
url: "https://myapp.com"
platforms: [twitter, bluesky]
content:
  style: casual
  action: "Try it free!"
  language: en  # Default: English
```

### Multi-Language Support
```yaml
# Japanese Campaign
content:
  style: casual
  action: "今すぐ試してみてください！"
  language: ja  # Japanese content generation
  hashtags: ["#AI", "#生産性", "#ツール"]

# Spanish Campaign  
content:
  style: professional
  action: "Pruébalo ahora"
  language: es  # Spanish content generation
  hashtags: ["#IA", "#Productividad"]
```

**Supported Languages**: English (en), Japanese (ja), Spanish (es), French (fr), German (de), Korean (ko), Chinese (zh), Portuguese (pt), Russian (ru), Arabic (ar), and 10+ more.

See [multilang-campaign.yaml](examples/multilang-campaign.yaml) for complete examples.

## 🔧 Commands (Terraform-style)

| Command | Description |
|---------|-------------|
| `aetherpost init` | Initialize new campaign |
| `aetherpost plan` | Preview generated content |
| `aetherpost apply` | Execute posts |
| `aetherpost destroy` | Delete posted content |
| `aetherpost auth` | Manage authentication |
| `aetherpost doctor` | Check configuration |

## 📖 Documentation

**🌐 [Complete Documentation Site](https://d3b75mcubdhimz.cloudfront.net)**

Quick links:
- [Getting Started](https://d3b75mcubdhimz.cloudfront.net/getting-started.html)
- [API Reference](https://d3b75mcubdhimz.cloudfront.net/api-reference.html)
- [Developer Guide](https://d3b75mcubdhimz.cloudfront.net/developer-onboarding.html)
- [Contributing](https://d3b75mcubdhimz.cloudfront.net/contributing.html)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Terraform's Infrastructure-as-Code approach
- Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
- AI content generation powered by [AI Provider](https://www.anthropic.com/) and [OpenAI](https://openai.com/)