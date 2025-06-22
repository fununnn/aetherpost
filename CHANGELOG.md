# Changelog

## [1.8.0] - 2025-06-22

### 🚀 Major Features

#### Security Enhancements
- **Secure Credential Management**: Complete redesign of credential handling with environment variable references
- **Git Security**: All sensitive data moved to `.env.aetherpost` files (gitignored) with `${VAR_NAME}` references in config files
- **Automatic Environment Loading**: ConfigManager now automatically loads `.env.aetherpost` files from multiple search paths

#### Twitter Integration 
- **Full Twitter Support**: Complete Twitter API v2 integration with v1.1 fallback for media uploads
- **Profile Management**: Update Twitter profiles with AI-generated bios and display names
- **Avatar Generation**: AI-powered avatar creation and upload using DALL-E 3
- **Tweet Posting**: Full posting capabilities with hashtags, media, and content optimization

#### Enhanced Profile Management
- **Multi-Platform Support**: Unified profile update system for Twitter and Bluesky
- **AI Avatar Generation**: Generate professional avatars using OpenAI DALL-E 3 for any platform
- **Smart Content Optimization**: Platform-specific bio length limits and content adaptation
- **Environment Variable Expansion**: Dynamic credential resolution from environment variables

#### Developer Experience
- **Consistent Authentication**: Unified credential handling across all commands and platforms  
- **Improved Error Messages**: Better error reporting and debugging information
- **Enhanced Logging**: Comprehensive logging with environment variable loading tracking

### 🔧 Technical Improvements

- **ConfigManager Enhancements**: Added `_load_environment_variables()` and `_expand_environment_variables()` methods
- **Platform Validation**: Enhanced `PlatformCredentials.is_valid()` with Bluesky-specific validation
- **Secure File Handling**: All credential files now use environment variable references
- **Apply Command Fix**: Resolved authentication issues in `aetherpost apply` command

### 📱 Platform Support

- **Twitter (@autopromo_)**: Full profile, avatar, and posting support
- **Bluesky**: Enhanced profile and avatar management with restored functionality
- **Environment Variables**: Secure credential management for all platforms

### 🛠️ Dependencies

- All existing dependencies maintained
- Enhanced security without breaking changes
- Backward compatible credential format (with migration to env vars)

### 🔄 Migration Guide

Existing users should:
1. Create `.env.aetherpost` file with actual credentials
2. Update `credentials.yaml` to use `${VAR_NAME}` format
3. Ensure `.env.aetherpost` is in `.gitignore`

### 📋 Commands Added/Updated

- `aetherpost profile update <platform>` - Enhanced with Twitter support
- `aetherpost profile upload-avatar <platform> --generate` - AI avatar generation
- `aetherpost apply` - Fixed authentication for consistent posting

## [1.7.1] - Previous Release

- Base functionality with Bluesky support
- Initial profile management features
- Campaign configuration system

---

For upgrade instructions and detailed documentation, visit: https://aether-post.com