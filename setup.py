"""Setup script for AetherPost."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README and requirements
here = Path(__file__).parent
long_description = (here / "README.md").read_text(encoding="utf-8")

# Use OSS-specific requirements for cleaner installation
oss_requirements_file = here / "requirements-oss.txt"
if oss_requirements_file.exists():
    requirements = oss_requirements_file.read_text(encoding="utf-8").strip().split("\n")
else:
    requirements = (here / "requirements.txt").read_text(encoding="utf-8").strip().split("\n")

# Filter out comments and optional dependencies
requirements = [
    req.strip() for req in requirements 
    if req.strip() and not req.strip().startswith("#") and not req.strip().startswith("-")
]

# Core requirements (without optional dev dependencies)
core_requirements = [req for req in requirements if not any(
    dev_pkg in req for dev_pkg in ["pytest", "black", "ruff"]
)]

setup(
    name="aetherpost",
    version="1.2.0",
    description="Promotion as Code - Automate your app promotion across social media platforms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AetherPost Team",
    author_email="team@aetherpost.dev",
    url="https://github.com/fununnn/aetherpost",
    project_urls={
        "Documentation": "https://d3b75mcubdhimz.cloudfront.net",
        "Source": "https://github.com/fununnn/aetherpost",
        "Issues": "https://github.com/fununnn/aetherpost/issues",
    },
    packages=find_packages(),
    include_package_data=True,
    install_requires=core_requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0", 
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aetherpost=aetherpost.cli.main:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications",
    ],
    python_requires=">=3.8",
    keywords="social media automation promotion marketing twitter bluesky mastodon AI content generation",
    zip_safe=False,
)