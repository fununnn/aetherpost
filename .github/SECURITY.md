# Security Policy

## Supported Versions

We actively support the following versions of AetherPost:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 🔒 Private Disclosure

**DO NOT** create a public issue for security vulnerabilities.

Instead, please:

1. **Email us**: Send details to security@aetherpost.dev
2. **Use GitHub Security**: Report via [GitHub Security Advisories](https://github.com/your-org/aetherpost/security/advisories)

### 📝 What to Include

Please provide:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and severity
- **Reproduction**: Steps to reproduce the issue
- **Environment**: OS, Python version, AetherPost version
- **Proof of Concept**: Code or screenshots (if applicable)

### ⏱️ Response Timeline

- **Initial Response**: Within 24 hours
- **Assessment**: Within 72 hours
- **Fix Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: Next release cycle

### 🏆 Recognition

We appreciate security researchers and will:

- Credit you in the security advisory (unless you prefer to remain anonymous)
- Include you in our Hall of Fame
- Consider rewards for significant findings

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version
2. **Secure API Keys**: Store credentials securely
   ```bash
   # Use environment variables
   export OPENAI_API_KEY="your-key-here"
   
   # Or encrypted .env files
   aetherpost auth setup --encrypt
   ```
3. **Review Permissions**: Limit social media app permissions
4. **Monitor Usage**: Check for unusual activity

### For Contributors

1. **Dependency Security**: Run security scans
   ```bash
   pip-audit
   safety check
   ```
2. **Code Review**: All PRs require review
3. **Static Analysis**: Use security linters
4. **Secrets Management**: Never commit secrets

## Known Security Considerations

### API Key Storage

- ✅ **Encrypted**: Keys encrypted at rest using `cryptography`
- ✅ **Local**: No keys sent to our servers
- ✅ **Scoped**: Minimal required permissions

### Network Security

- ✅ **HTTPS**: All API calls use HTTPS
- ✅ **Rate Limiting**: Built-in rate limiting
- ✅ **Validation**: Input validation and sanitization

### Dependencies

- ✅ **Minimal**: Keep dependencies minimal
- ✅ **Audited**: Regular security audits
- ✅ **Updated**: Automated dependency updates

## Scope

This security policy covers:

- ✅ AetherPost core application
- ✅ Official plugins and connectors
- ✅ Infrastructure and deployment
- ❌ Third-party plugins (unless developed by us)
- ❌ Social media platforms themselves

## Security Features

### OSS Edition

- 🔐 **Local Encryption**: API keys encrypted locally
- 🛡️ **Input Validation**: All inputs validated
- 📊 **Usage Limits**: Built-in rate limiting
- 🔍 **Audit Logs**: Basic logging for security events

### Enterprise Edition

- 🏢 **Team Management**: Role-based access control
- 📋 **Compliance**: SOC2, GDPR compliance
- 🔒 **Advanced Encryption**: Hardware security modules
- 👥 **SSO Integration**: Enterprise identity providers
- 📈 **Security Monitoring**: Real-time security alerts

## Security Tools

We use these tools for security:

- **Static Analysis**: Bandit, Semgrep
- **Dependency Scanning**: pip-audit, Safety
- **Secrets Detection**: GitGuardian, TruffleHog
- **Container Scanning**: Trivy, Snyk
- **Infrastructure**: Terraform security scanning

## Compliance

### Data Protection

- **GDPR**: EU data protection compliance
- **CCPA**: California privacy compliance  
- **Privacy**: No personal data collection in OSS version

### Industry Standards

- **OWASP**: Follow OWASP Top 10 guidelines
- **CIS**: CIS security benchmarks
- **NIST**: NIST Cybersecurity Framework

## Contact

- **Security Email**: security@aetherpost.dev
- **General Contact**: team@aetherpost.dev
- **Documentation**: https://docs.aetherpost.dev/security

---

**Note**: This security policy is for AetherPost OSS. Enterprise customers have additional security features and dedicated support channels.