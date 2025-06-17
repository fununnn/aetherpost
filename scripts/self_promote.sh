#!/bin/bash

# AetherPost Self-Promotion Script
# Uses AetherPost's own capabilities to promote itself
# 
# This script provides an interactive menu for different types of promotion
# campaigns using AetherPost's built-in features.
#
# Prerequisites:
#   - AetherPost installed (pip install -e .)
#   - .env file with platform credentials
#   - Optional: OpenAI API key for enhanced content generation

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
CAMPAIGN_FILE="$PROJECT_ROOT/campaign_aetherpost.yaml"
PROMOTION_SCRIPT="$PROJECT_ROOT/aetherpost_self_promotion.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AetherPost Self-Promotion${NC}"
echo -e "${BLUE}Using AetherPost to promote AetherPost!${NC}"
echo "========================================="

# Utility functions
log_info() {
    echo -e "${BLUE}$1${NC}"
}

log_success() {
    echo -e "${GREEN}$1${NC}"
}

log_warning() {
    echo -e "${YELLOW}$1${NC}"
}

log_error() {
    echo -e "${RED}$1${NC}"
}

check_dependencies() {
    log_info "📦 Checking dependencies..."
    
    # Check Python
    if ! command -v python &> /dev/null; then
        log_error "❌ Python not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Check AetherPost installation
    if ! python -c "import aetherpost" 2>/dev/null; then
        log_warning "⚠️ AetherPost not installed. Installing..."
        cd "$PROJECT_ROOT"
        pip install -e . || {
            log_error "❌ Failed to install AetherPost"
            exit 1
        }
    fi
    
    log_success "✅ Dependencies ready"
}

check_environment() {
    log_info "🔍 Checking environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "⚠️ No .env file found. Creating template..."
        create_env_template
        log_error "📝 Please edit .env with your credentials and run again"
        exit 1
    fi
    
    if [ ! -f "$CAMPAIGN_FILE" ]; then
        log_error "❌ campaign_aetherpost.yaml not found"
        log_info "Expected location: $CAMPAIGN_FILE"
        exit 1
    fi
    
    if [ ! -f "$PROMOTION_SCRIPT" ]; then
        log_error "❌ aetherpost_self_promotion.py not found"
        log_info "Expected location: $PROMOTION_SCRIPT"
        exit 1
    fi
    
    log_success "✅ Environment configuration ready"
}

create_env_template() {
    cat > "$ENV_FILE" << 'EOF'
# Twitter/X API credentials
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# Bluesky credentials
BLUESKY_IDENTIFIER=your_username_or_email
BLUESKY_PASSWORD=your_app_password

# Mastodon credentials
MASTODON_ACCESS_TOKEN=your_access_token
MASTODON_API_BASE_URL=https://mastodon.social

# Reddit credentials
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password

# OpenAI for content generation (optional)
OPENAI_API_KEY=your_openai_key
EOF
}

# Main dependency and environment checks
check_dependencies
check_environment

show_promotion_menu() {
    echo ""
    log_info "📋 Promotion Options:"
    echo "1. Quick post (using current campaign)"
    echo "2. Custom self-promotion script"
    echo "3. Interactive content generation"
    echo "4. Scheduled promotion campaign"
    echo "5. Reddit-focused technical post"
    echo "6. Show promotion analytics"
    echo "7. Test platform connections"
    echo ""
}

run_quick_post() {
    log_info "🚀 Running quick promotion post..."
    cd "$PROJECT_ROOT"
    python -c "
import asyncio
import os
import sys
sys.path.insert(0, '.')
from aetherpost_self_promotion import AetherPostSelfPromotion

async def quick_post():
    promo = AetherPostSelfPromotion()
    if await promo.setup_connectors():
        await promo.run_promotion_campaign('launch_announcement', dry_run=False)
    else:
        print('❌ Setup failed. Check your .env file.')

asyncio.run(quick_post())
"
}

run_custom_script() {
    log_info "🤖 Running custom self-promotion script..."
    cd "$PROJECT_ROOT"
    python "$PROMOTION_SCRIPT"
}

run_interactive_generation() {
    log_info "💬 Interactive content generation..."
    log_info "📝 Generating content about AetherPost..."
    
    cd "$PROJECT_ROOT"
    
    # Use AetherPost CLI for content generation if available
    if command -v aetherpost &> /dev/null; then
        aetherpost ai generate \
            --prompt "Create a casual social media post highlighting AetherPost's key benefits for developers" \
            --style casual \
            --platform twitter
    else
        log_warning "⚠️ AetherPost CLI not available, using Python script"
        python "$PROMOTION_SCRIPT"
    fi
}

setup_scheduled_promotion() {
    log_info "📅 Setting up scheduled promotion..."
    log_info "This creates a daily promotion script for automation"
    log_info "Example cron entry for daily promotion at 2 PM:"
    echo "0 14 * * * cd $PROJECT_ROOT && ./scripts/self_promote.sh"
    
    # Create a daily promotion script
    cat > "$PROJECT_ROOT/daily_aetherpost_promotion.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python aetherpost_self_promotion.py << 'ANSWERS'
all
y
ANSWERS
EOF
    chmod +x "$PROJECT_ROOT/daily_aetherpost_promotion.sh"
    log_success "✅ Created daily_aetherpost_promotion.sh"
    log_info "You can now add this to your cron schedule for automated promotion"
}

run_reddit_promotion() {
    log_info "🔴 Running Reddit-focused technical promotion..."
    
    if [ -f "$CAMPAIGN_FILE" ]; then
        log_info "📋 Planning Reddit post about AetherPost..."
        
        cd "$PROJECT_ROOT"
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def reddit_promotion():
    from aetherpost_self_promotion import AetherPostSelfPromotion
    
    promo = AetherPostSelfPromotion()
    if await promo.setup_connectors():
        # Focus on technical content for Reddit
        result = await promo.run_promotion_campaign('technical_content', dry_run=False)
        print('✅ Reddit promotion completed')
    else:
        print('❌ Setup failed. Check your .env file.')

asyncio.run(reddit_promotion())
"
    else
        log_error "❌ campaign_aetherpost.yaml not found"
    fi
}

show_analytics() {
    log_info "📊 Promotion Analytics (placeholder)"
    log_info "This feature would show:"
    echo "  • Recent post performance"
    echo "  • Platform engagement metrics"
    echo "  • Growth trends"
    echo "  • Best performing content types"
    log_warning "Full analytics integration coming in future version"
}

test_connections() {
    log_info "🔌 Testing platform connections..."
    cd "$PROJECT_ROOT"
    python -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def test_connections():
    from aetherpost_self_promotion import AetherPostSelfPromotion
    
    promo = AetherPostSelfPromotion()
    success = await promo.setup_connectors()
    
    if success:
        platforms = promo.connector_manager.get_available_platforms()
        print(f'✅ Successfully connected to: {', '.join(platforms)}')
    else:
        print('❌ Connection test failed. Check your credentials.')

asyncio.run(test_connections())
"
}

# Main menu and option handling
show_promotion_menu
read -p "Choose option (1-7): " choice

case $choice in
    1)
        run_quick_post
        ;;
    2)
        run_custom_script
        ;;
    3)
        run_interactive_generation
        ;;
    4)
        setup_scheduled_promotion
        ;;
    5)
        run_reddit_promotion
        ;;
    6)
        show_analytics
        ;;
    7)
        test_connections
        ;;
    *)
        log_error "❌ Invalid option. Please choose 1-7."
        exit 1
        ;;
esac

show_completion_summary() {
    echo ""
    log_success "🎉 AetherPost self-promotion completed!"
    echo ""
    log_info "💡 Tips for ongoing promotion:"
    echo "  • Set up daily automated posts with cron"
    echo "  • Engage with responses and comments"
    echo "  • Share in relevant developer communities"
    echo "  • Highlight new features and improvements"
    echo "  • Ask for feedback and feature requests"
    echo ""
    log_info "📊 Track success with:"
    echo "  • GitHub stars and forks"
    echo "  • Documentation site visits"
    echo "  • Community engagement"
    echo "  • New users and contributors"
    echo ""
    log_info "🔗 Useful links:"
    echo "  • Project repository: https://github.com/your-org/aetherpost"
    echo "  • Documentation: https://docs.aetherpost.dev"
    echo "  • Report issues: https://github.com/your-org/aetherpost/issues"
}

# Show completion summary
show_completion_summary