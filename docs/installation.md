# Installation Guide

This guide covers installing AetherPost OSS on different platforms.

## Quick Install

```bash
# Clone the repository
git clone https://github.com/your-org/aetherpost.git
cd aetherpost

# Install with pip
pip install -e .
```

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, Windows
- **Memory**: 512MB RAM minimum
- **Disk Space**: 100MB for installation
- **Network**: Internet connection for AI APIs and social media

## Installation Methods

### Method 1: From Source (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/aetherpost.git
cd aetherpost

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements-oss.txt

# 4. Install AetherPost
pip install -e .

# 5. Verify installation
aetherpost --help
```

### Method 2: Using pip (When Available)

```bash
# Install from PyPI (when published)
pip install aetherpost

# Verify installation
aetherpost --help
```

### Method 3: Using pipx (Isolated Installation)

```bash
# Install pipx if not available
pip install pipx

# Install AetherPost in isolated environment
pipx install aetherpost

# Verify installation
aetherpost --help
```

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git

# Follow standard installation
git clone https://github.com/your-org/aetherpost.git
cd aetherpost
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-oss.txt
pip install -e .
```

### CentOS/RHEL/Fedora

```bash
# Install Python and git
sudo dnf install python3 python3-pip git  # Fedora
# sudo yum install python3 python3-pip git  # CentOS/RHEL

# Follow standard installation
git clone https://github.com/your-org/aetherpost.git
cd aetherpost
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-oss.txt
pip install -e .
```

### macOS

```bash
# Install Homebrew if not available
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python git

# Follow standard installation
git clone https://github.com/your-org/aetherpost.git
cd aetherpost
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-oss.txt
pip install -e .
```

### Windows

```powershell
# Install Python from https://python.org
# Make sure to check "Add Python to PATH"

# Install Git from https://git-scm.com

# Clone and install
git clone https://github.com/your-org/aetherpost.git
cd aetherpost
python -m venv venv
venv\Scripts\activate
pip install -r requirements-oss.txt
pip install -e .
```

## Docker Installation

```bash
# Build Docker image
docker build -t aetherpost .

# Run with volume mount for configuration
docker run -it --rm \
  -v $(pwd):/workspace \
  -v ~/.aetherpost:/root/.aetherpost \
  aetherpost
```

## Post-Installation Setup

### 1. Verify Installation

```bash
aetherpost --help
aetherpost version  # Should show version info
```

### 2. Initial Configuration

```bash
# Run setup wizard
aetherpost setup wizard

# Or manual setup
aetherpost init
```

### 3. Configure API Keys

```bash
# Interactive setup
aetherpost auth setup

# Manual setup
export OPENAI_API_KEY="your-openai-key"
export AI_API_KEY="your-[AI Service]-key"
```

## Troubleshooting

### Common Issues

#### 1. Permission Errors

```bash
# Use --user flag for pip
pip install --user -r requirements-oss.txt

# Or fix permissions
sudo chown -R $USER ~/.local
```

#### 2. Python Version Issues

```bash
# Check Python version
python --version

# Use python3 explicitly if needed
python3 -m pip install -r requirements-oss.txt
```

#### 3. Missing System Dependencies

```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# macOS
xcode-select --install
```

#### 4. Virtual Environment Issues

```bash
# Remove and recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-oss.txt
```

### Getting Help

- **Documentation**: https://docs.aetherpost.dev
- **Issues**: https://github.com/your-org/aetherpost/issues
- **Discussions**: https://github.com/your-org/aetherpost/discussions

## Upgrading

### From Git

```bash
cd aetherpost
git pull origin main
pip install -r requirements-oss.txt
pip install -e .
```

### From PyPI

```bash
pip install --upgrade aetherpost
```

## Uninstallation

```bash
# Remove package
pip uninstall aetherpost

# Remove configuration (optional)
rm -rf ~/.aetherpost

# Remove virtual environment
rm -rf venv
```

## Next Steps

After installation:

1. [Platform Setup](platforms.md) - Configure social media platforms
2. [AI Provider Setup](ai-providers.md) - Configure AI services
3. [First Campaign](examples.md#first-campaign) - Create your first campaign
4. [Configuration Reference](configuration.md) - Learn about advanced options