# S3 Free Tier Documentation Hosting Guide

## Overview
This guide helps developers host AetherPost documentation on AWS S3 using the free tier, enabling easy access for new contributors.

## AWS Free Tier Limits
- **Storage**: 5GB for 12 months
- **Requests**: 20,000 GET / 2,000 PUT requests per month
- **Data Transfer**: 15GB outbound per month

## Setup Instructions

### 1. Create S3 Bucket
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create bucket for documentation
aws s3 mb s3://aetherpost-docs --region ap-northeast-1
```

### 2. Enable Static Website Hosting
```bash
# Enable website hosting
aws s3 website s3://aetherpost-docs \
  --index-document index.html \
  --error-document error.html
```

### 3. Set Bucket Policy for Public Access
Create `bucket-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::aetherpost-docs/*"
    }
  ]
}
```

Apply policy:
```bash
aws s3api put-bucket-policy \
  --bucket aetherpost-docs \
  --policy file://bucket-policy.json
```

### 4. Upload Documentation
```bash
# Sync documentation files
aws s3 sync ./docs-site/ s3://aetherpost-docs/ \
  --delete \
  --exclude "*.git*" \
  --content-type "text/html"
```

## Documentation Structure

```
docs-site/
├── index.html          # Landing page
├── getting-started/    # Quick start guides
├── api-reference/      # API documentation
├── tutorials/          # Step-by-step tutorials
├── contributing/       # Contribution guidelines
└── assets/            # Images, CSS, JS
```

## Cost Optimization Tips

1. **Use CloudFlare CDN** (Free)
   - Reduces S3 requests
   - Improves global performance
   - Provides SSL certificate

2. **Compress Assets**
   ```bash
   # Gzip HTML/CSS/JS files
   find docs-site -name "*.html" -o -name "*.css" -o -name "*.js" | \
     xargs gzip -9 -k
   ```

3. **Set Cache Headers**
   ```bash
   aws s3 cp docs-site/ s3://aetherpost-docs/ \
     --recursive \
     --cache-control "max-age=3600"
   ```

## Monitoring Usage

```bash
# Check bucket size
aws s3 ls s3://aetherpost-docs --recursive --summarize | grep "Total Size"

# Monitor requests (CloudWatch)
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name NumberOfObjects \
  --dimensions Name=BucketName,Value=aetherpost-docs \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 86400 \
  --statistics Average
```

## Alternative Free Hosting Options

### GitHub Pages
- Completely free
- Automatic deployment from repository
- Custom domain support

```yaml
# .github/workflows/deploy-docs.yml
name: Deploy Documentation
on:
  push:
    branches: [main]
    paths:
      - 'docs-site/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs-site
```

### Netlify
- 100GB bandwidth/month free
- Automatic HTTPS
- Deploy previews

```toml
# netlify.toml
[build]
  publish = "docs-site/"

[[redirects]]
  from = "/api/*"
  to = "/api-reference/:splat"
  status = 200
```

## Access URL
Once deployed, documentation will be available at:
- S3: `http://aetherpost-docs.s3-website-ap-northeast-1.amazonaws.com`
- CloudFlare: `https://docs.aetherpost.dev` (after setup)
- GitHub Pages: `https://[username].github.io/aetherpost`

## Security Considerations
- Never commit AWS credentials
- Use IAM roles with minimal permissions
- Enable S3 access logging
- Regular security audits

## Support
For questions about documentation hosting:
- Create issue in GitHub repository
- Join community Discord
- Email: support@aetherpost.dev