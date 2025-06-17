#!/bin/bash

# AetherPost Documentation Deployment Script
# Deploys documentation to S3 with HTTPS support via CloudFront

set -e

# Configuration
BUCKET_NAME="aetherpost-docs"
REGION="ap-northeast-1"
DOCS_DIR="docs-site"

echo "🚀 AetherPost Documentation Deployment"
echo "======================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first:"
    echo "   pip install awscli"
    exit 1
fi

# Check if docs directory exists
if [ ! -d "$DOCS_DIR" ]; then
    echo "❌ Documentation directory $DOCS_DIR not found"
    echo "   Run 'make build-docs' first"
    exit 1
fi

echo "📋 Configuration:"
echo "   Bucket: $BUCKET_NAME"
echo "   Region: $REGION"
echo "   Source: $DOCS_DIR/"
echo ""

# Create S3 bucket
echo "🪣 Creating S3 bucket..."
aws s3 mb s3://$BUCKET_NAME --region $REGION 2>/dev/null || echo "   Bucket already exists"

# Enable static website hosting
echo "🌐 Configuring static website hosting..."
aws s3 website s3://$BUCKET_NAME \
    --index-document index.html \
    --error-document error.html

# Set bucket policy for public read access
echo "🔓 Setting bucket policy..."
cat > bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
    --bucket $BUCKET_NAME \
    --policy file://bucket-policy.json

rm bucket-policy.json

# Upload documentation
echo "📤 Uploading documentation..."
aws s3 sync $DOCS_DIR/ s3://$BUCKET_NAME/ \
    --delete \
    --cache-control "max-age=3600" \
    --exclude "*.git*"

# Create CloudFront distribution for HTTPS
echo "🔒 Setting up CloudFront for HTTPS..."

# Check if distribution already exists
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[0].DomainName=='$BUCKET_NAME.s3-website-$REGION.amazonaws.com'].Id | [0]" --output text 2>/dev/null || echo "None")

if [ "$DISTRIBUTION_ID" = "None" ] || [ -z "$DISTRIBUTION_ID" ]; then
    echo "   Creating new CloudFront distribution..."
    
    cat > cloudfront-config.json << EOF
{
  "CallerReference": "aetherpost-docs-$(date +%s)",
  "Comment": "AetherPost Documentation HTTPS Distribution",
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-aetherpost-docs",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "Compress": true
  },
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-aetherpost-docs",
        "DomainName": "$BUCKET_NAME.s3-website-$REGION.amazonaws.com",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only"
        }
      }
    ]
  },
  "Enabled": true,
  "DefaultRootObject": "index.html"
}
EOF

    DISTRIBUTION_ID=$(aws cloudfront create-distribution \
        --distribution-config file://cloudfront-config.json \
        --query 'Distribution.Id' \
        --output text)
    
    rm cloudfront-config.json
    
    echo "   Created distribution: $DISTRIBUTION_ID"
    echo "   ⏳ Distribution is deploying (this takes 15-20 minutes)..."
else
    echo "   Found existing distribution: $DISTRIBUTION_ID"
    echo "   🔄 Invalidating cache..."
    
    aws cloudfront create-invalidation \
        --distribution-id $DISTRIBUTION_ID \
        --paths "/*" > /dev/null
fi

# Get URLs
S3_URL="http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
CLOUDFRONT_URL=$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DomainName' --output text 2>/dev/null || echo "deploying...")

echo ""
echo "✅ Deployment complete!"
echo "========================"
echo ""
echo "📋 Access URLs:"
echo "   🔓 S3 (HTTP):      $S3_URL"
echo "   🔒 CloudFront (HTTPS): https://$CLOUDFRONT_URL"
echo ""
echo "📊 Monitoring:"
echo "   aws s3 ls s3://$BUCKET_NAME --recursive --summarize"
echo "   aws cloudfront get-distribution --id $DISTRIBUTION_ID"
echo ""
echo "🔄 To update documentation:"
echo "   make build-docs && ./scripts/deploy-docs.sh"
echo ""

# Save configuration for future use
cat > .docs-config << EOF
BUCKET_NAME=$BUCKET_NAME
REGION=$REGION
DISTRIBUTION_ID=$DISTRIBUTION_ID
S3_URL=$S3_URL
CLOUDFRONT_URL=https://$CLOUDFRONT_URL
EOF

echo "💾 Configuration saved to .docs-config"