# Changelog

## [1.11.0] - 2025-06-29

### 🔔 New Features: Smart Notification System
- **Slack/LINE Preview Notifications**: Send content previews to Slack/LINE before posting for approval
- **Real-time Preview Generation**: Rich content previews with platform-specific formatting
- **Interactive Approval Workflow**: Manual approval required before actual posting to social platforms
- **Multiple Notification Channels**: Support for Slack webhooks, LINE Notify, and Discord webhooks
- **Japanese LINE Integration**: Native Japanese message formatting with emoji and character limits

### 📁 Project Context Intelligence 
- **Smart Project Reading**: Automatically read and analyze project files for content generation
- **Security-First File Access**: Path traversal prevention, sensitive info filtering, 10KB file limits
- **Differential Content Generation**: Detect file changes and generate posts based on recent updates
- **Project Snapshot Management**: Track file changes with MD5 hashing for intelligent difference detection
- **AI Context Integration**: Include project structure and recent changes in AI content generation prompts

### ⚙️ Enhanced Configuration Management
- **Advanced Campaign Settings**: Extended `campaign.yaml` with notification and context configurations
- **Environment-Based Authentication**: Secure token management via `SLACK_WEBHOOK_URL` and `LINE_NOTIFY_TOKEN`
- **Interactive Setup Improvements**: Detailed notification channel selection in `aetherpost init`
- **Flexible Context Monitoring**: Configure watched folders, exclude patterns, and security settings
- **Timeout and Approval Controls**: Configurable approval timeouts and notification requirements

### 🛠️ Technical Improvements
- **Notification Architecture**: Complete `PreviewNotificationManager` system with channel abstraction
- **Error Handling Enhancement**: Standardized error codes and recovery mechanisms
- **Configuration Model Updates**: Pydantic models for `NotificationsConfig` and `NotificationChannelConfig`
- **Async Notification Support**: Full async/await support for all notification channels
- **Content Preview Engine**: Rich preview generation with platform-specific block formatting

### 🎯 User Experience
- **3-Step Workflow Enhancement**: `init` → `plan` → `apply` with integrated notifications
- **Real-time Feedback**: Live notification sending status with success/failure reporting
- **Context-Aware Posting**: Posts that reference actual project changes and current development status
- **Multi-language Support**: Japanese notification messages with proper formatting and emoji usage
- **Approval Safety**: No accidental posting - explicit approval required for all social media updates

## [1.10.2] - 2025-06-28

### 🔧 Platform Integration Fixes
- **Bluesky Avatar Upload**: Fixed blob upload implementation for AT Protocol compliance with proper binary data handling
- **Character Encoding**: Resolved multilingual content issues across all platforms with comprehensive UTF-8 support
- **Twitter Profile Updates**: Fixed API method calls for profile image uploads using correct v1.1 endpoints
- **Platform Optimization**: Added platform-specific image size requirements and automatic resizing

### 🎨 Media Management
- **Image Optimization**: Implemented automatic image resizing for platform limits (240KB → 24KB for Bluesky)
- **UTF-8 Support**: Complete Japanese, Chinese, Korean, emoji character support with proper charset headers
- **Blob Handling**: Proper Content-Type and binary data formatting for AT Protocol compliance

### 🛠️ CI/CD & Build Improvements
- **Workflow Optimization**: Simplified testing to Python 3.10-3.11 for faster builds
- **Build Fixes**: Corrected package directory references (aetherpost → aetherpost_source)
- **Version Consistency**: Updated all version references to 1.10.2 across build files
- **Security Streamlining**: Removed overly complex security workflows for cleaner CI

### 📚 Documentation & Architecture
- **Technical Documentation**: Complete codebase structure and function reference in CLAUDE.md
- **Architecture Overview**: Comprehensive unified platform system design documentation
- **Platform Requirements**: Detailed image size and format specifications for all 5 platforms

### 🧪 Testing & Validation
- **Real API Testing**: Verified actual platform updates with live credentials on Twitter and Bluesky
- **Multilingual Testing**: Confirmed character encoding across Japanese, Chinese, Korean languages
- **Image Upload Testing**: Validated avatar uploads with proper resizing and format conversion
- **Integration Testing**: End-to-end workflow testing with real platform APIs

### 🚀 Core Features
- **3-Command Workflow**: Simplified `init` → `plan` → `apply` automation
- **5-Platform Support**: Twitter, Bluesky, Instagram, LinkedIn, YouTube integration
- **AI Avatar Generation**: OpenAI DALL-E 3 powered professional avatar creation
- **Automatic Profile Updates**: Cross-platform profile synchronization with smart content optimization
- **Content Generation**: AI-powered, platform-optimized content creation with anti-repetition

### 🔒 Security & Reliability
- **Credential Management**: Secure environment variable handling with `.env.aetherpost` files
- **Error Recovery**: Robust error handling with automatic retry mechanisms
- **Rate Limiting**: Adaptive rate limiting to prevent API quota exhaustion
- **Input Validation**: Comprehensive validation for all user inputs and configurations

## [1.10.1] - 2025-06-23

### 🐛 Bug Fixes
- **Version Display**: Fixed version tracking display in console output
- **Error Handling**: Improved error handling for version parsing edge cases
- **Logging**: Enhanced debug logging for version detection process

## [1.10.0] - 2025-06-23

### 🚀 Major Features
- **Project Context System**: Complete implementation of dynamic content generation
- **Version Tracking**: Automatic version change detection and specialized announcements
- **Security-First Design**: Comprehensive file access validation and secret scanning
- **Content Diversity**: Post history tracking prevents repetitive content

### ✨ New Capabilities
- **Semantic Versioning**: Full major.minor.patch analysis and classification
- **CHANGELOG Integration**: Automatic parsing of change descriptions
- **Priority Content**: Version updates get highest priority in generation
- **Enhanced Hashtags**: Context-aware hashtag generation

### 🎯 Breaking Changes
- **API Changes**: New project context configuration format
- **Config Updates**: Enhanced security validation requirements

## [1.9.4] - 2025-06-23

### 🐛 Bug Fix
- **Version Detection**: Improved version tracking reliability and logging
- **Security Patterns**: Enhanced secret detection to reduce false positives
- **Context Reading**: Better handling of project files without blocking legitimate content

### ✨ Minor Enhancements
- **Debug Logging**: Added detailed version detection logging for troubleshooting
- **Pattern Matching**: More precise secret detection patterns

## [1.9.3] - 2025-06-23

### 🔧 Bug Fixes & Security
- **Security Updates**: Updated all dependencies to latest secure versions
- **Vulnerability Resolution**: Fixed 4 security vulnerabilities (2 high, 2 moderate)
- **Dependency Updates**: Updated cryptography, pydantic, openai, and other critical packages

### 🚀 New Features
- **Version Tracking System**: Implemented automatic version change detection and announcement
- **Smart Content Generation**: Added project context-aware content generation avoiding repetition
- **Semantic Versioning**: Full support for major.minor.patch version analysis
- **CHANGELOG Integration**: Automatic parsing and integration of changelog entries into posts

### ✨ Enhancements  
- **Content Diversity**: Post history tracking prevents repetitive content
- **Version-Priority Posts**: Version updates get highest priority in content generation
- **Enhanced Hashtags**: Automatic version-specific hashtags (#VersionUpdate, #NewRelease)

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