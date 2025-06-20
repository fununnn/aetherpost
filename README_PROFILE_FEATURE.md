# AetherPost Profile Management Feature

## Overview

AetherPost can automatically manage and sync your project's profile across all social media platforms. This ensures consistent branding and saves time updating each platform manually.

## How it Works

### 1. Add Profile Settings to campaign.yaml

```yaml
# Your existing campaign configuration
name: "my-project"
platforms:
  - twitter
  - bluesky
  - reddit

# Add profile configuration
profile:
  display_name: "My Awesome Project"
  bio: "🚀 Revolutionary AI tool | Open Source | Developer-friendly"
  website: "https://github.com/user/my-project"
  sync_on_apply: true  # Enable automatic profile updates
```

### 2. Run Plan to Preview

```bash
aetherpost plan
```

This will show:
- Your campaign content
- Profile updates that will be applied
- Platform-specific optimizations

### 3. Apply to Update Everything

```bash
aetherpost apply
```

This will:
- Post your campaign content
- Update profiles on all configured platforms
- Generate optimized bio for each platform's character limits

## Platform-Specific Features

### Character Limits
- **Twitter**: 160 characters bio, 50 character name
- **Bluesky**: 256 characters bio, 64 character name  
- **Reddit**: 200 characters bio, 20 character name
- **YouTube**: 1000 characters bio, 100 character name
- **Instagram**: 150 characters bio, 30 character name
- **Mastodon**: 500 characters bio, 30 character name
- **Discord**: 190 characters bio (bot only), 32 character name

### Auto-Optimization
AetherPost automatically:
- Truncates text to fit platform limits
- Adds relevant hashtags when space allows
- Preserves emojis and key information
- Formats for maximum impact

## Examples

### Basic Profile
```yaml
profile:
  display_name: "AetherPost"
  bio: "Social media automation for developers"
  website: "https://aetherpost.dev"
```

### Detailed Profile
```yaml
profile:
  display_name: "AetherPost"
  bio: "🚀 AI-Powered Social Media Automation | 5-Platform Support | Open Source | Developer-Friendly CLI Tool"
  website: "https://github.com/fununnn/aetherpost"
  keywords: ["automation", "social-media", "ai", "opensource"]
  sync_on_apply: true
```

### Platform-Specific Overrides
```yaml
profile:
  display_name: "AetherPost"
  bio: "Default bio for most platforms"
  website: "https://aetherpost.dev"
  
  # Override for specific platforms
  overrides:
    twitter:
      bio: "🚀 Social automation for devs. 5 platforms, 1 command."
    youtube:
      bio: |
        AetherPost - Complete Social Media Automation Platform
        
        ✅ 5 Platform Support (Twitter, Reddit, YouTube, Bluesky, Instagram)
        ✅ AI-Powered Content Generation
        ✅ Developer-Friendly CLI
        ✅ 100% Open Source
        
        Get started: pip install aetherpost
```

## Current Limitations

### Automated Updates Supported
- ✅ **Bluesky**: Full profile sync (name, bio, website)
- ✅ **Twitter**: Full profile sync (name, bio, website) 
- ✅ **Mastodon**: Full profile sync (name, bio, website field)
- ✅ **Instagram**: Bio and website sync (business accounts only)
- 🔄 **Discord**: Bot username only (limited API capabilities)
- 🔄 **Reddit**: Display name only (API limitations)
- 🔄 **YouTube**: Manual OAuth flow required

### Manual Updates Required
For platforms with API limitations, AetherPost will:
1. Generate optimized profile content
2. Save to `.aetherpost/profiles/` directory
3. Provide copy-paste ready text
4. Show direct links to profile settings

## Best Practices

1. **Keep it Concise**: Short, impactful bios work best
2. **Use Emojis**: They stand out and save characters
3. **Include Keywords**: Help people find your project
4. **Update Regularly**: Keep profiles fresh with project updates
5. **Test First**: Use a test account before updating production

## Troubleshooting

### Profile Not Updating
- Check API credentials in `.env.aetherpost`
- Verify platform permissions (especially for Instagram business accounts)
- Run `aetherpost doctor` to diagnose issues

### Character Limit Errors
- AetherPost auto-truncates, but review the result
- Use platform-specific overrides for custom text
- Remove less important information first

### API Rate Limits
- Profile updates count against API limits
- Space out updates if hitting limits
- Disable `sync_on_apply` for high-frequency posting