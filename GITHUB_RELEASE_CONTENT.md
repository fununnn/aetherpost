# GitHub Release v1.5.0 Creation Content

## 📍 URL
https://github.com/fununnn/aetherpost/releases/new

## 📝 Input Content

### Tag
```
v1.5.0
```

### Release Title
```
v1.5.0 - Universal Profile Management
```

### Description
```markdown
# 🚀 AetherPost v1.5.0 - Universal Profile Management

## ✨ Major New Features

### 🌐 Complete Profile Management System
- **Multi-platform support**: Twitter, Bluesky, Mastodon, Instagram, Discord
- **Unified configuration**: Manage all platform profiles from a single `campaign.yaml`
- **Auto-optimization**: Automatically adapts to each platform's character limits
- **Preview functionality**: Review profile updates with `aetherpost plan`

### 🎯 Platform Support
- ✅ **Twitter/X**: Full profile sync (name, bio, website)
- ✅ **Bluesky**: Full profile sync (name, bio, website) 
- ✅ **Mastodon**: Full profile sync (name, bio, website field)
- ✅ **Instagram**: Bio and website sync (business accounts)
- ✅ **Discord**: Bot username updates (API limitations)

## 📋 Usage

```yaml
# campaign.yaml
profile:
  display_name: "My Project"
  bio: "🚀 Amazing tool for developers"
  website: "https://github.com/user/project"
  sync_on_apply: true
```

```bash
aetherpost plan   # Preview profile updates
aetherpost apply  # Apply posts + profile updates
```

## 🔧 Technical Improvements
- Enhanced character limit optimization
- Robust error handling for all platforms
- Unified profile sync architecture
- Comprehensive platform-specific documentation

## 📈 Platform Character Limits
- **Twitter**: 160 chars bio, 50 char name
- **Bluesky**: 256 chars bio, 64 char name  
- **Mastodon**: 500 chars bio, 30 char name
- **Instagram**: 150 chars bio, 30 char name
- **Discord**: 190 chars bio, 32 char name

## 🚀 Installation

```bash
pip install aetherpost==1.5.0
# or
pip install --upgrade aetherpost
```

## 📚 Documentation
- [Profile Management Guide](https://d3b75mcubdhimz.cloudfront.net/profile-management.html)
- [Complete Documentation](https://d3b75mcubdhimz.cloudfront.net)

This release enables consistent branding across all social media platforms with a single, unified configuration!
```

### Assets to Upload
Drag & drop the following files:
- `/home/ubuntu/doc/autopromo/dist/aetherpost-1.5.0-py3-none-any.whl`
- `/home/ubuntu/doc/autopromo/dist/aetherpost-1.5.0.tar.gz`

## ✅ Steps
1. Access the URL above
2. Select Tag: `v1.5.0`
3. Copy & paste Title and Description
4. Upload the 2 files from dist/ folder
5. Click "Publish release"