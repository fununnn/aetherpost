# Contributing to AetherPost

Thank you for your interest in contributing to AetherPost! We welcome contributions from everyone.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Community](#community)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/aetherpost.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Submit a pull request

## 🛠️ Development Setup

### Prerequisites

- Python 3.8 or higher
- pip or poetry
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/aetherpost.git
cd aetherpost

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests to verify setup
pytest
```

### Environment Setup

```bash
# Copy example environment file
cp .env.example .env.aetherpost

# Edit with your API keys (optional for development)
nano .env.aetherpost
```

## 🤝 How to Contribute

### 🐛 Bug Reports

When filing an issue, please include:

- **Description**: Clear description of the bug
- **Steps to reproduce**: Step-by-step instructions
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, AetherPost version
- **Logs**: Relevant error messages or logs

### ✨ Feature Requests

For feature requests, please:

- Check if the feature already exists
- Describe the use case and benefits
- Provide examples if possible
- Consider implementation complexity

### 🤖 AI-Assisted Development Welcome!

**AetherPost is an AI-friendly OSS project!** We encourage and support AI-assisted development:

### Approved AI Tools
- ✅ **Claude Code** (Anthropic) - Full support
- ✅ **GitHub Copilot** - Approved  
- ✅ **TabNine, Cursor, Replit AI** - Approved
- ✅ **ChatGPT Code Interpreter** - Approved

### AI Contribution Guidelines
- **Always review** AI-generated code before submitting
- **Add proper tests** for AI-generated functionality
- **Document AI usage** in commit messages:
  ```bash
  git commit -m "feat: add Instagram connector
  
  Co-authored-by: Claude <claude@anthropic.com>"
  ```
- **Follow our style guide** regardless of code origin

See our [Code Guidelines](CODE_GUIDELINES.md) for detailed AI development policies.

## 🔧 Code Contributions

We welcome contributions for:

- **Bug fixes**
- **New platform connectors** (Instagram, LinkedIn, etc.)
- **AI provider integrations** (Google Gemini, local models, etc.)
- **Analytics providers**
- **CLI improvements**
- **Documentation**
- **Tests**

## 📝 Pull Request Process

1. **Fork & Clone**: Fork the repo and clone your fork
2. **Branch**: Create a feature branch from `main`
3. **Develop**: Make your changes following our style guidelines
4. **Test**: Ensure all tests pass and add new tests if needed
5. **Document**: Update documentation if needed
6. **Commit**: Use clear, descriptive commit messages
7. **Push**: Push to your fork
8. **PR**: Open a pull request with a clear description

### PR Requirements

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated (if applicable)
- [ ] Commit messages are clear
- [ ] No merge conflicts

## 🎨 Style Guidelines

### Python Code Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 88 characters (Black default)
- **Imports**: Use `isort` for import sorting
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings

### Code Formatting

We use automated tools for consistent formatting:

```bash
# Format code
black aetherpost tests
isort aetherpost tests

# Lint code
flake8 aetherpost tests
mypy aetherpost
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

feat(twitter): add thread support
fix(auth): resolve token refresh issue
docs(readme): update installation instructions
test(connectors): add platform connector tests
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aetherpost --cov-report=html

# Run specific test file
pytest tests/test_connectors.py

# Run tests for specific platform
pytest tests/test_connectors.py -k twitter
```

### Writing Tests

- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows
- **Mock external APIs**: Use `pytest-mock` for API calls

Example test structure:

```python
def test_twitter_connector_post():
    """Test Twitter connector posting functionality."""
    connector = TwitterConnector(mock_credentials)
    result = connector.post({"text": "Test post"})
    assert result["status"] == "success"
```

## 🏗️ Project Structure

```
aetherpost/
├── aetherpost/           # Main package
│   ├── cli/             # CLI commands
│   ├── core/            # Core functionality
│   ├── plugins/         # Plugin system
│   └── templates/       # Content templates
├── tests/               # Test suite
├── docs/                # Documentation
├── scripts/             # Utility scripts
└── examples/            # Usage examples
```

## 📚 Documentation

When contributing, please update relevant documentation:

- **Docstrings**: For new functions/classes
- **README**: For new features or changes
- **API docs**: For new CLI commands
- **Examples**: For new use cases

## 🌟 Priority Areas

We're especially looking for contributions in:

1. **Platform Connectors**
   - Instagram
   - LinkedIn
   - TikTok
   - Discord
   - Slack

2. **AI Providers**
   - Google Gemini
   - Local LLM support
   - Custom model integration

3. **Analytics**
   - Advanced metrics
   - Visualization
   - Export formats

4. **Developer Experience**
   - VS Code extension improvements
   - Better error messages
   - CLI usability

## 💬 Community

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat (coming soon)

## ❓ Questions?

If you have questions about contributing:

1. Check existing [Issues](https://github.com/your-org/aetherpost/issues)
2. Look through [Discussions](https://github.com/your-org/aetherpost/discussions)
3. Open a new issue with the `question` label

Thank you for contributing to AetherPost! 🚀