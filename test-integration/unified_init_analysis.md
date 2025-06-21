# AetherPost Unified Init Command Analysis

## Current Command Structure

### 1. Current Init Commands

The `aetherpost init` command currently offers:
- **Basic Initialization**: Creates workspace (.aetherpost), campaign.yaml, .gitignore
- **Template Selection**: starter, production, enterprise
- **Platform Configuration**: Multi-platform selection
- **API Key Collection**: Interactive collection of API keys
- **Language Support**: 10+ languages
- **Notification Settings**: Preview/auto-apply modes
- **Auto-Setup Mode**: Detects existing campaign.yaml and auto-configures

Key features:
- Interactive by default (with --quick option)
- Validates API key formats
- Creates environment templates
- Supports upgrade mode (--upgrade)

### 2. Other Related Commands

#### `aetherpost setup wizard`
- Interactive setup for new users
- Creates campaign configuration
- Sets up authentication
- Tests setup automatically
- Shows next steps with ASCII banner

#### `aetherpost auth setup`
- Platform-specific authentication
- Supports Twitter, OpenAI, Bluesky, Instagram
- Validates credentials
- Encrypts and saves credentials

#### `aetherpost doctor`
- System health checks
- Dependency verification
- Network connectivity tests
- Configuration validation
- Automatic fix attempts (--fix)

#### `aetherpost profile generate`
- Generates optimized social media profiles
- Creates copyable text files
- Platform-specific bio optimization
- Character limit awareness

## Overlapping Functionality

1. **Authentication Setup**
   - `init` collects API keys
   - `auth setup` also manages credentials
   - `setup wizard` includes authentication

2. **Configuration Creation**
   - `init` creates campaign.yaml
   - `setup wizard` also creates campaign config

3. **Validation & Testing**
   - `doctor` validates configuration
   - `setup wizard` tests setup
   - `auth test` validates credentials

## Proposed Unified Init Command Design

### Core Principle: Progressive Disclosure
Start simple, reveal complexity as needed.

### Command Structure

```bash
aetherpost init [OPTIONS]
```

### Modes of Operation

#### 1. **Express Mode** (Default - 30 seconds)
```bash
aetherpost init
```
- Auto-detects project (name, git URL, README)
- Sets up Twitter + OpenAI (minimal viable setup)
- Creates basic campaign.yaml
- Prompts for essential API keys only
- Shows clear next steps

#### 2. **Guided Mode** (2-3 minutes)
```bash
aetherpost init --guided
```
- Interactive platform selection
- Language and style configuration
- Notification preferences
- API key collection with validation
- Optional profile generation
- Connection testing

#### 3. **Advanced Mode** (5+ minutes)
```bash
aetherpost init --advanced
```
- All guided features plus:
- Backend selection (local/AWS/cloud)
- Cost estimation
- Advanced scheduling options
- Multi-environment setup
- Custom templates

#### 4. **Auto Mode** (< 10 seconds)
```bash
aetherpost init --auto
```
- Detects existing campaign.yaml
- Reads .env.aetherpost if present
- Auto-configures everything
- No prompts unless critical

### Unified Features

#### 1. **Smart Detection**
- Git repository info
- README.md parsing
- Package.json/pyproject.toml analysis
- Existing configuration detection
- Language inference from project

#### 2. **Progressive Authentication**
```
Phase 1: Essential (Twitter + AI)
Phase 2: Extended (Reddit, YouTube)
Phase 3: Complete (All platforms)
```

#### 3. **Integrated Health Check**
- Run mini-doctor after setup
- Show status dashboard
- Offer immediate fixes
- Test connections inline

#### 4. **Profile Generation Integration**
```
"Would you like to optimize your social profiles too?" [Y/n]
```
- Generate profiles during init
- Export to .aetherpost/profiles/
- Show preview in terminal

#### 5. **Smart Defaults**
- Detect CI/CD environment
- GitHub Actions workflow generation
- Docker support detection
- VS Code settings

### New Subcommands

```bash
aetherpost init status      # Show current setup status
aetherpost init upgrade     # Upgrade existing setup
aetherpost init repair      # Fix broken configuration
aetherpost init template    # Generate from templates
aetherpost init from-url    # Initialize from GitHub repo
```

### Implementation Benefits

1. **Single Entry Point**: Users only need to remember `aetherpost init`
2. **Progressive Complexity**: Beginners aren't overwhelmed
3. **Reduced Redundancy**: No duplicate auth/config code
4. **Better UX**: Guided experience from start to finish
5. **Integrated Testing**: Validate as you go

### Migration Path

1. Keep existing commands as aliases initially
2. Show deprecation notices with new command info
3. Gradually phase out redundant commands
4. Maintain backward compatibility for CI/CD

### Example User Flows

#### New User - Express
```
$ aetherpost init
🚀 Welcome to AetherPost! Let's get you started in 30 seconds.

📦 Detected: my-awesome-app (from git)
📝 Project: "AI-powered task manager" (from README)

✨ Setting up essentials:
  • Twitter/X ✓
  • OpenAI ✓

🔑 Enter your API keys:
OpenAI API Key: sk-...
Twitter API Key: ...

✅ Setup complete! You're ready to promote.

Next: aetherpost plan (preview your first post)
```

#### Existing User - Auto
```
$ aetherpost init --auto
🔍 Found existing configuration...
✅ Loaded 5 API keys from .env.aetherpost
✅ Validated campaign.yaml
✅ All systems operational

Ready to post! Use: aetherpost apply
```

#### Power User - Advanced
```
$ aetherpost init --advanced
[Full interactive setup with all options]
```

## Conclusion

A unified init command would:
1. Simplify the user experience
2. Reduce code duplication
3. Provide a clear progression path
4. Integrate related functionality
5. Maintain flexibility for different use cases

The key is making the simple case simple while keeping the complex case possible.