"""Version information for AetherPost."""

__version__ = "1.11.1"
__author__ = "AetherPost Team"
__email__ = "team@aetherpost.dev"
__description__ = "Promotion as Code - Automate your app promotion across social media platforms"
__url__ = "https://aether-post.com"
__license__ = "MIT"

# Build information (can be updated during build process)
__build_date__ = "2025-06-29"
__commit_hash__ = "unknown"

def get_version_info():
    """Get detailed version information."""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "url": __url__,
        "build_date": __build_date__,
        "commit": __commit_hash__
    }