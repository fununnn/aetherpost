# Contributing to AetherPost

Thank you for your interest in contributing to AetherPost! We welcome contributions from developers of all skill levels.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Community Guidelines](#community-guidelines)

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Virtual environment tool (venv, conda, etc.)
- Basic understanding of social media APIs

### First-Time Contributors
1. Look for issues labeled `good first issue` or `help wanted`
2. Comment on the issue to claim it
3. Fork the repository
4. Create your feature branch
5. Submit a pull request

## Development Setup

### 1. Fork and Clone
```bash
# Fork via GitHub UI, then:
git clone https://github.com/YOUR_USERNAME/aetherpost.git
cd aetherpost
git remote add upstream https://github.com/original/aetherpost.git
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .

# Install pre-commit hooks
pre-commit install
```

### 3. Configuration
```bash
# Copy example configuration
cp .env.example .env

# Run initial setup
aetherpost dev setup
```

## How to Contribute

### Reporting Bugs
1. Check existing issues first
2. Use the bug report template
3. Include:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Error logs/screenshots

### Suggesting Features
1. Check the roadmap and existing issues
2. Use the feature request template
3. Explain:
   - Use case
   - Proposed solution
   - Alternative approaches
   - Potential impact

### Code Contributions

#### 1. Find or Create an Issue
```bash
# Good issue titles:
"Add Instagram Reels support"
"Fix rate limiting in Twitter connector"
"Improve error messages for auth failures"
```

#### 2. Create Feature Branch
```bash
# Branch naming convention
git checkout -b feature/instagram-reels
git checkout -b fix/twitter-rate-limit
git checkout -b docs/api-examples
```

#### 3. Make Changes
- Write clean, readable code
- Follow existing patterns
- Add/update tests
- Update documentation

#### 4. Commit Messages
```bash
# Format: <type>(<scope>): <subject>

# Types: feat, fix, docs, style, refactor, test, chore

# Examples:
git commit -m "feat(instagram): add Reels posting support"
git commit -m "fix(twitter): handle rate limit errors gracefully"
git commit -m "docs(api): add webhook examples"
```

## Code Standards

### Python Style Guide
- Follow PEP 8
- Use type hints
- Maximum line length: 88 (Black default)
- Use descriptive variable names

```python
# Good
def post_content(
    content: str,
    platforms: List[str],
    schedule_time: Optional[datetime] = None
) -> Dict[str, PostResult]:
    """Post content to specified platforms."""
    results = {}
    for platform in platforms:
        connector = get_connector(platform)
        results[platform] = connector.post(content, schedule_time)
    return results

# Avoid
def post(c, p, t=None):
    r = {}
    for x in p:
        conn = get_conn(x)
        r[x] = conn.post(c, t)
    return r
```

### Documentation
- All public functions need docstrings
- Use Google-style docstrings
- Include examples for complex functions

```python
def create_campaign(config: Dict[str, Any]) -> Campaign:
    """Create a new campaign from configuration.
    
    Args:
        config: Campaign configuration dictionary containing:
            - name: Campaign name
            - schedule: Scheduling information
            - platforms: List of target platforms
    
    Returns:
        Campaign: Created campaign instance
    
    Raises:
        ValidationError: If configuration is invalid
    
    Example:
        >>> campaign = create_campaign({
        ...     "name": "Product Launch",
        ...     "schedule": {"frequency": "daily"},
        ...     "platforms": ["twitter", "linkedin"]
        ... })
    """
```

### Error Handling
```python
# Good: Specific error handling
try:
    result = api_call()
except RateLimitError as e:
    logger.warning(f"Rate limit hit: {e}")
    return retry_with_backoff(api_call, e.retry_after)
except AuthenticationError:
    logger.error("Authentication failed")
    raise
except Exception as e:
    logger.exception("Unexpected error")
    raise AetherPostError(f"Operation failed: {e}")

# Avoid: Bare except
try:
    result = api_call()
except:
    pass
```

## Testing Guidelines

### Test Structure
```python
# tests/test_<module>.py
import pytest
from aetherpost.core import ContentGenerator

class TestContentGenerator:
    def test_create_basic_content(self):
        """Test basic content generation."""
        generator = ContentGenerator()
        content = generator.create(
            topic="Technology",
            tone="professional",
            length=280
        )
        assert len(content["text"]) <= 280
        assert content["metadata"]["tone"] == "professional"
    
    def test_platform_optimization(self):
        """Test platform-specific optimization."""
        # Test implementation
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_connectors.py

# Run with coverage
pytest --cov=aetherpost --cov-report=html

# Run specific test
pytest tests/test_connectors.py::TestTwitter::test_post
```

### Test Requirements
- Minimum 80% code coverage
- All new features must have tests
- Bug fixes should include regression tests
- Use mocks for external API calls

## Pull Request Process

### 1. Before Submitting
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with main

### 2. PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### 3. Review Process
1. Automated checks run
2. Code review by maintainer
3. Address feedback
4. Approval and merge

### 4. After Merge
- Delete your feature branch
- Pull latest main
- Celebrate! 🎉

## Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on what's best for the community

### Communication Channels
- **GitHub Issues**: Bug reports, features
- **Discord**: Real-time discussion
- **Email**: security@aetherpost.dev (security issues only)

### Getting Help
- Check documentation first
- Search existing issues
- Ask in Discord #help channel
- Be patient and respectful

## Recognition

### Contributors
All contributors are recognized in:
- README.md contributors section
- GitHub contributors page
- Release notes

### Special Recognitions
- 🌟 Core Contributor: 10+ merged PRs
- 🐛 Bug Hunter: 5+ bug fixes
- 📚 Documentation Hero: Significant docs improvements
- 🚀 Feature Champion: Major feature implementation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Questions?

Feel free to:
- Open a discussion on GitHub
- Ask in Discord
- Email maintainers@aetherpost.dev

Thank you for contributing to AetherPost! Your efforts help make social media automation accessible to everyone. 🙏