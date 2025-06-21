# 🖱️ GUI Setup Guide for AetherPost

**Perfect for beginners!** This guide shows you how to set up AetherPost using GUI tools - no command line required!

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [GitHub Setup (Web Browser)](#github-setup-web-browser)
- [Code Editor Setup](#code-editor-setup)
- [Project Setup](#project-setup)
- [Configuration via GUI](#configuration-via-gui)
- [Running AetherPost](#running-aetherpost)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### Required Software (All GUI-based)

1. **Git for Windows/Mac** - [Download here](https://git-scm.com/downloads)
   - ✅ Choose "Git Bash" option during installation
   - ✅ Select "Use Git from Windows Command Prompt"

2. **Python 3.8+** - [Download here](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation
   - ✅ Choose "Install for all users"

3. **VS Code** - [Download here](https://code.visualstudio.com/)
   - Best GUI editor for Python development
   - Built-in terminal and extensions

4. **GitHub Desktop** (Optional) - [Download here](https://desktop.github.com/)
   - GUI alternative to Git command line

## 🌐 GitHub Setup (Web Browser)

### Step 1: Create GitHub Account

1. **Go to GitHub**: [https://github.com](https://github.com)
2. **Click "Sign up"** in top-right corner
3. **Fill in details**:
   - Username: `your-username`
   - Email: `your-email@example.com`
   - Password: `secure-password`
4. **Verify email** when prompted

### Step 2: Fork AetherPost Repository

1. **Visit AetherPost**: [https://github.com/fununnn/aetherpost](https://github.com/fununnn/aetherpost)
2. **Click "Fork"** button (top-right)
   - ![Fork Button](https://docs.github.com/assets/cb-28613/images/help/repository/fork_button.png)
3. **Choose your account** as the destination
4. **Wait for fork creation** (30 seconds)

### Step 3: Enable GitHub Issues and Discussions

1. **Go to your forked repository** 
2. **Click "Settings"** tab
3. **Scroll to "Features"** section
4. **Check these boxes**:
   - ✅ Issues
   - ✅ Discussions  
   - ✅ Projects
   - ✅ Wiki

## 💻 Code Editor Setup

### Step 1: Install VS Code Extensions

1. **Open VS Code**
2. **Click Extensions** icon (left sidebar) or `Ctrl+Shift+X`
3. **Install these extensions**:

   **Required Extensions:**
   - `Python` by Microsoft
   - `Python IntelliCode` by Microsoft
   - `GitLens` by GitKraken
   - `YAML` by Red Hat

   **Recommended Extensions:**
   - `Claude Code` by Anthropic (for AI assistance)
   - `GitHub Copilot` by GitHub (if you have access)
   - `Error Lens` by Alexander
   - `Auto Rename Tag` by Jun Han

### Step 2: Configure Python Environment

1. **Open VS Code Settings**: `File > Preferences > Settings`
2. **Search for "python"**
3. **Set these options**:
   - `Python: Default Interpreter Path`: Point to your Python installation
   - `Python: Terminal Execute In File Dir`: ✅ Checked
   - `Python: Formatting Provider`: `black`

### Step 3: Clone Your Fork (GUI Method)

**Option A: GitHub Desktop**
1. **Open GitHub Desktop**
2. **Click "Clone a repository from the Internet"**
3. **Select your fork**: `your-username/aetherpost`
4. **Choose local path**: `C:\Users\YourName\Documents\aetherpost`
5. **Click "Clone"**

**Option B: VS Code**
1. **Open VS Code**
2. **Press `Ctrl+Shift+P`** (Command Palette)
3. **Type**: `Git: Clone`
4. **Enter URL**: `https://github.com/your-username/aetherpost.git`
5. **Choose folder** and click "Select Repository Location"

## 🛠️ Project Setup

### Step 1: Open Project in VS Code

1. **Open VS Code**
2. **File > Open Folder**
3. **Navigate** to your cloned `aetherpost` folder
4. **Click "Select Folder"**

### Step 2: Set Up Python Environment

1. **Open VS Code Terminal**: `View > Terminal` or `Ctrl+`` (backtick)
2. **Type these commands one by one**:

```bash
# Create virtual environment
python -m venv aetherpost-env

# Activate virtual environment (Windows)
aetherpost-env\Scripts\activate

# Activate virtual environment (Mac/Linux)
source aetherpost-env/bin/activate

# Install AetherPost
pip install -e .

# Install development dependencies
pip install -r requirements-oss.txt
```

### Step 3: Install AetherPost

1. **In VS Code Terminal**, run:
```bash
pip install aetherpost
```

2. **Verify installation**:
```bash
aetherpost --help
```

You should see the AetherPost help menu!

## ⚙️ Configuration via GUI

### Step 1: Create Project Folder

1. **Create new folder** on your Desktop: `my-aetherpost-project`
2. **Open this folder in VS Code**: `File > Open Folder`

### Step 2: Create Configuration Files

**Create `campaign.yaml`:**
1. **Right-click** in VS Code file explorer
2. **Select "New File"**
3. **Name it**: `campaign.yaml`
4. **Copy this content**:

```yaml
name: "My First Campaign"
concept: "Promoting my awesome project"
urls:
  main: https://my-awesome-project.com
  github: https://github.com/my-username/my-project
  docs: https://my-awesome-project.com/docs
platforms:
  - bluesky
  - reddit
content:
  style: professional
  action: "Check it out!"
  language: en
  hashtags:
    - "#MyProject"
    - "#OpenSource"
    - "#Innovation"
limits:
  free_tier: true
  max_posts_per_day: 10
notifications:
  enabled: true
  auto_apply: false
```

**Create `.env.aetherpost`:**
1. **Create new file**: `.env.aetherpost`
2. **Copy this template**:

```bash
# AetherPost API Configuration
# Keep this file secure and do not commit to version control

# AI Services
OPENAI_API_KEY=your-openai-key-here

# Bluesky (Free - Recommended for beginners)
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_PASSWORD=your-app-password

# Reddit (Free)
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USERNAME=your-reddit-username
REDDIT_PASSWORD=your-reddit-password

# Twitter (Paid - $100/month minimum)
TWITTER_API_KEY=your-twitter-key
TWITTER_API_SECRET=your-twitter-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-access-token-secret
```

### Step 3: Get API Keys (GUI Method)

**OpenAI API Key:**
1. **Visit**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **Sign up/Login**
3. **Click "Create new secret key"**
4. **Copy the key** and paste in `.env.aetherpost`

**Bluesky Setup (Easiest):**
1. **Download Bluesky app** or visit [https://bsky.app](https://bsky.app)
2. **Create account** if you don't have one
3. **Go to Settings > App Passwords**
4. **Create new app password** for AetherPost
5. **Copy credentials** to `.env.aetherpost`

**Reddit Setup:**
1. **Visit**: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. **Click "Create App"**
3. **Fill in**:
   - Name: `AetherPost`
   - Type: `script`
   - Description: `Social media automation`
   - Redirect URI: `http://localhost:8080`
4. **Copy Client ID and Secret** to `.env.aetherpost`

## 🚀 Running AetherPost

### Step 1: Initialize Project

1. **Open VS Code Terminal** in your project folder
2. **Run initialization**:
```bash
aetherpost init
```

3. **AetherPost will**:
   - ✅ Detect your `campaign.yaml`
   - ✅ Load API keys from `.env.aetherpost`
   - ✅ Generate optimized profiles
   - ✅ Set up the workspace

### Step 2: Preview Content

```bash
aetherpost plan
```

This shows you what will be posted before actually posting!

### Step 3: Post Content

```bash
aetherpost apply
```

Confirm when prompted, and your content goes live!

## 🖱️ GUI Workflow Tips

### VS Code Terminal Shortcuts

- **Open Terminal**: `Ctrl+`` (backtick)
- **Clear Terminal**: `Ctrl+K`
- **Split Terminal**: `Ctrl+Shift+5`
- **Previous Command**: `↑` arrow key

### File Management

- **New File**: `Ctrl+N`
- **Save File**: `Ctrl+S`
- **Open File**: `Ctrl+O`
- **Find in Files**: `Ctrl+Shift+F`

### Git Operations (VS Code GUI)

1. **View Changes**: Click "Source Control" icon (left sidebar)
2. **Stage Changes**: Click `+` next to files
3. **Commit**: Type message and press `Ctrl+Enter`
4. **Push**: Click `...` > `Push`

## 🔧 Troubleshooting

### Common Issues & GUI Solutions

**Issue: "Command not found"**
- **Solution**: Restart VS Code and ensure Python is in PATH
- **Check**: Open new terminal and try `python --version`

**Issue: "Module not found"**
- **Solution**: Ensure virtual environment is activated
- **Check**: Terminal prompt should show `(aetherpost-env)`

**Issue: "API key invalid"**
- **Solution**: Double-check `.env.aetherpost` file
- **Check**: No extra spaces or quotes around keys

**Issue: "Permission denied"**
- **Solution**: Run VS Code as administrator (Windows)
- **Check**: File permissions in your project folder

### Getting Help

**VS Code Built-in Help:**
1. **Help menu** > `Welcome`
2. **Command Palette** (`Ctrl+Shift+P`) > `Help: Open Interactive Playground`

**AetherPost Help:**
```bash
aetherpost --help
aetherpost plan --help
aetherpost apply --help
```

**Community Support:**
- **GitHub Issues**: [Report bugs](https://github.com/fununnn/aetherpost/issues)
- **GitHub Discussions**: [Ask questions](https://github.com/fununnn/aetherpost/discussions)

## 🎯 Next Steps for Beginners

### Start Simple
1. **Use Bluesky only** for your first campaign (free and easy)
2. **Keep campaigns small** (1-2 posts to start)
3. **Always use `aetherpost plan`** before `aetherpost apply`

### Gradual Expansion
1. **Add Reddit** after mastering Bluesky
2. **Try different content styles** (professional, casual, technical)
3. **Experiment with hashtags** and content optimization

### Advanced Features
1. **Add AI profile generation** with `--generate-images`
2. **Set up multiple campaigns** for different projects
3. **Use scheduling** and **analytics**

## 🆘 Emergency Commands

If something goes wrong:

```bash
# Stop any running processes
Ctrl+C

# Reset AetherPost configuration
rm -rf .aetherpost/
aetherpost init

# Reinstall AetherPost
pip uninstall aetherpost
pip install aetherpost
```

---

🎉 **Congratulations!** You're now ready to automate your social media with AetherPost using GUI tools!

**Need more help?** Check our [full documentation](https://aether-post.com) or ask in [GitHub Discussions](https://github.com/fununnn/aetherpost/discussions)!