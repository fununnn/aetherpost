#!/usr/bin/env python3
"""Fix all profile generation methods to include github_url parameter."""

import re
import sys

# Read the profile generator file
file_path = '/home/ubuntu/.asdf/installs/python/3.12.3/lib/python3.12/site-packages/aetherpost_source/core/profiles/generator.py'

with open(file_path, 'r') as f:
    content = f.read()

# Pattern to find ProfileContent constructors that don't have github_url
pattern = r'(return ProfileContent\([^)]*website_url=website_url,)(\s*location=)'

# Replace with github_url addition
replacement = r'\1\n            github_url=github_url,\2'

# Apply the replacement
new_content = re.sub(pattern, replacement, content)

# Also need to add github_url extraction in methods that don't have it
# Pattern to find URL extraction without github_url
url_pattern = r'(# Use main website URL.*?\n\s+urls = context\.get\("urls", \{\}\)\s*\n\s+website_url = [^\n]+)(\s*\n\s+return ProfileContent)'

url_replacement = r'\1\n        github_url = urls.get("github") or context.get("github_url")\2'

new_content = re.sub(url_pattern, url_replacement, new_content, flags=re.DOTALL)

# Write back the modified content
with open(file_path, 'w') as f:
    f.write(new_content)

print("Fixed profile generation methods to include github_url")