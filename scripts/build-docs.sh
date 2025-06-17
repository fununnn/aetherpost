#!/bin/bash

# AetherPost Documentation Builder
# Converts markdown files to HTML for static site deployment

set -e

DOCS_SOURCE="docs"
DOCS_OUTPUT="docs-site"
TEMPLATE_DIR="scripts/templates"

echo "🔨 Building AetherPost Documentation"
echo "==================================="

# Check if pandoc is available
if ! command -v pandoc &> /dev/null; then
    echo "⚠️ Pandoc not found. Creating simple HTML conversion..."
    USE_SIMPLE_CONVERSION=true
else
    USE_SIMPLE_CONVERSION=false
fi

# Create output directory
mkdir -p $DOCS_OUTPUT

# Copy existing assets
echo "📁 Copying assets..."
if [ -d "$DOCS_OUTPUT/css" ]; then
    echo "   CSS files already exist"
else
    mkdir -p $DOCS_OUTPUT/css
fi
if [ -d "$DOCS_OUTPUT/js" ]; then
    echo "   JS files already exist"
else
    mkdir -p $DOCS_OUTPUT/js
fi
if [ -d "$DOCS_OUTPUT/images" ]; then
    echo "   Image directory already exists"
else
    mkdir -p $DOCS_OUTPUT/images
fi

# Create HTML template if it doesn't exist
if [ ! -f "$TEMPLATE_DIR/page.html" ]; then
    mkdir -p $TEMPLATE_DIR
    cat > $TEMPLATE_DIR/page.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title$ - AetherPost Documentation</title>
    <meta name="description" content="$description$">
    <link rel="stylesheet" href="../css/style.css">
    <link rel="icon" type="image/x-icon" href="../images/favicon.ico">
</head>
<body>
    <header class="header">
        <nav class="nav">
            <div class="nav-brand">
                <h1><a href="../index.html">🚀 AetherPost</a></h1>
                <span class="tagline">Promotion as Code</span>
            </div>
            <ul class="nav-links">
                <li><a href="../index.html">Home</a></li>
                <li><a href="getting-started.html">Getting Started</a></li>
                <li><a href="api-reference.html">API Reference</a></li>
                <li><a href="contributing.html">Contributing</a></li>
            </ul>
        </nav>
    </header>

    <main class="main">
        <div class="container">
            <div class="doc-page">
                $body$
            </div>
        </div>
    </main>

    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-brand">
                    <h3>AetherPost</h3>
                    <p>Making social media automation accessible to developers.</p>
                </div>
                <div class="footer-links">
                    <div class="footer-section">
                        <h4>Documentation</h4>
                        <ul>
                            <li><a href="getting-started.html">Getting Started</a></li>
                            <li><a href="api-reference.html">API Reference</a></li>
                            <li><a href="configuration.html">Configuration</a></li>
                        </ul>
                    </div>
                    <div class="footer-section">
                        <h4>Community</h4>
                        <ul>
                            <li><a href="contributing.html">Contributing</a></li>
                            <li><a href="https://github.com/your-org/aetherpost">GitHub</a></li>
                            <li><a href="https://github.com/your-org/aetherpost/issues">Issues</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2025 AetherPost. Licensed under MIT License.</p>
            </div>
        </div>
    </footer>

    <script src="../js/script.js"></script>
</body>
</html>
EOF
fi

# Convert markdown files to HTML
echo "📝 Converting markdown files..."

# Function to convert markdown to HTML
convert_markdown() {
    local input_file="$1"
    local output_file="$2"
    local title="$3"
    local description="${4:-AetherPost documentation}"
    
    echo "   Converting $input_file -> $output_file"
    
    if [ "$USE_SIMPLE_CONVERSION" = true ]; then
        # Simple conversion without pandoc
        python3 scripts/simple-convert.py "$input_file" "$output_file" "$title" "$description" "$TEMPLATE_DIR/page.html"
    else
        pandoc "$input_file" \
            --from markdown \
            --to html \
            --template "$TEMPLATE_DIR/page.html" \
            --metadata title="$title" \
            --metadata description="$description" \
            --highlight-style tango \
            --output "$output_file"
    fi
}

# Convert individual documentation files
if [ -f "$DOCS_SOURCE/developer-onboarding.md" ]; then
    convert_markdown "$DOCS_SOURCE/developer-onboarding.md" \
        "$DOCS_OUTPUT/developer-onboarding.html" \
        "Developer Guide" \
        "Complete guide for developers contributing to AetherPost"
fi

if [ -f "$DOCS_SOURCE/api-reference.md" ]; then
    convert_markdown "$DOCS_SOURCE/api-reference.md" \
        "$DOCS_OUTPUT/api-reference.html" \
        "API Reference" \
        "Complete API reference for AetherPost"
fi

if [ -f "$DOCS_SOURCE/contributing.md" ]; then
    convert_markdown "$DOCS_SOURCE/contributing.md" \
        "$DOCS_OUTPUT/contributing.html" \
        "Contributing" \
        "How to contribute to AetherPost development"
fi

if [ -f "$DOCS_SOURCE/s3-free-tier-hosting.md" ]; then
    convert_markdown "$DOCS_SOURCE/s3-free-tier-hosting.md" \
        "$DOCS_OUTPUT/s3-hosting.html" \
        "S3 Hosting" \
        "Deploy documentation on AWS S3 free tier"
fi

# Convert additional files if they exist
if [ -f "$DOCS_SOURCE/configuration.md" ]; then
    convert_markdown "$DOCS_SOURCE/configuration.md" \
        "$DOCS_OUTPUT/configuration.html" \
        "Configuration" \
        "Complete configuration reference for AetherPost"
fi

if [ -f "$DOCS_SOURCE/installation.md" ]; then
    convert_markdown "$DOCS_SOURCE/installation.md" \
        "$DOCS_OUTPUT/installation.html" \
        "Installation" \
        "Installation guide for AetherPost"
fi

# Create getting started page from README if needed
if [ ! -f "$DOCS_OUTPUT/getting-started.html" ] && [ -f "README.md" ]; then
    convert_markdown "README.md" \
        "$DOCS_OUTPUT/getting-started.html" \
        "Getting Started" \
        "Quick start guide for AetherPost"
fi

# Create simple JavaScript file if it doesn't exist
if [ ! -f "$DOCS_OUTPUT/js/script.js" ]; then
    cat > $DOCS_OUTPUT/js/script.js << 'EOF'
// AetherPost Documentation JavaScript

// Copy code to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copied to clipboard!');
    }).catch(function() {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showNotification('Copied to clipboard!');
    });
}

// Show notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'copy-notification show';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 2000);
}

// Add copy buttons to code blocks
document.addEventListener('DOMContentLoaded', function() {
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(function(codeBlock) {
        const pre = codeBlock.parentElement;
        const button = document.createElement('button');
        button.className = 'copy-btn';
        button.innerHTML = '📋';
        button.title = 'Copy to clipboard';
        
        button.addEventListener('click', function() {
            copyToClipboard(codeBlock.textContent);
        });
        
        pre.style.position = 'relative';
        pre.appendChild(button);
    });
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
EOF
fi

# Add Makefile target
echo ""
echo "📋 Adding Makefile targets..."
if ! grep -q "build-docs:" Makefile 2>/dev/null; then
    cat >> Makefile << 'EOF'

# Documentation building and deployment
build-docs:
	@echo "🔨 Building documentation..."
	./scripts/build-docs.sh
	@echo "✅ Documentation built in docs-site/"

deploy-docs: build-docs
	@echo "🚀 Deploying documentation to S3..."
	./scripts/deploy-docs.sh

serve-docs: build-docs
	@echo "🌐 Serving documentation locally..."
	@echo "Open http://localhost:8000 in your browser"
	@cd docs-site && python -m http.server 8000
EOF
fi

echo ""
echo "✅ Documentation build complete!"
echo "================================"
echo ""
echo "📁 Generated files in $DOCS_OUTPUT/:"
find $DOCS_OUTPUT -name "*.html" | sort
echo ""
echo "🌐 To preview locally:"
echo "   make serve-docs"
echo ""
echo "🚀 To deploy to S3:"
echo "   make deploy-docs"
echo ""
echo "📝 To rebuild:"
echo "   make build-docs"