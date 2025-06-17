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

### Installation

```bash
git clone https://github.com/your-org/aetherpost.git
cd aetherpost
pip install -r requirements.txt
pip install -e .
```

### Setup

```bash
aetherpost setup wizard
```

### Usage

```bash
# Create campaign (super simple!)
aetherpost init

# Preview content
aetherpost plan

# Execute posts
aetherpost apply

# Quick post
aetherpost now "New feature released! 🚀" --to twitter
```

## 📋 Configuration Example

```yaml
name: "my-awesome-app"
concept: "AI-powered task manager that learns your habits"
url: "https://myapp.com"
platforms: [twitter, bluesky]
content:
  style: casual
  action: "Try it free!"
```

## 🔧 Commands

| Command | Description |
|---------|-------------|
| `aetherpost init` | Initialize new campaign |
| `aetherpost plan` | Preview generated content |
| `aetherpost apply` | Execute posts |
| `aetherpost now <message>` | Quick post |
| `aetherpost stats` | View analytics |

## 📖 Documentation

**🌐 [Complete Documentation Site](https://aetherpost-docs.s3-website-ap-northeast-1.amazonaws.com)**

Quick links:
- [Getting Started](https://aetherpost-docs.s3-website-ap-northeast-1.amazonaws.com/getting-started.html)
- [API Reference](https://aetherpost-docs.s3-website-ap-northeast-1.amazonaws.com/api-reference.html)
- [Developer Guide](https://aetherpost-docs.s3-website-ap-northeast-1.amazonaws.com/developer-onboarding.html)
- [Contributing](https://aetherpost-docs.s3-website-ap-northeast-1.amazonaws.com/contributing.html)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Terraform's Infrastructure-as-Code approach
- Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
- AI content generation powered by [AI Provider](https://www.anthropic.com/) and [OpenAI](https://openai.com/)