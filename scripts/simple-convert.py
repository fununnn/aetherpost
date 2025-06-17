#!/usr/bin/env python3

import re
import sys
import os

def convert_markdown_to_html(input_file, output_file, title, description, template_file):
    """Simple markdown to HTML converter"""
    
    # Read the template
    with open(template_file, 'r') as f:
        template = f.read()
    
    # Read the markdown
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Simple markdown to HTML conversion
    content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', content, flags=re.MULTILINE)
    
    # Bold and italic
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
    
    # Inline code
    content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)
    
    # Code blocks
    content = re.sub(r'```([^`]*?)```', r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)
    
    # Links
    content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', content)
    
    # Lists
    content = re.sub(r'^- (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)
    content = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', content, flags=re.DOTALL)
    
    # Convert newlines to paragraphs
    paragraphs = content.split('\n\n')
    html_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            p = f'<p>{p}</p>'
        if p:
            html_paragraphs.append(p)
    content = '\n'.join(html_paragraphs)
    
    # Replace template variables
    result = template.replace('$title$', title)
    result = result.replace('$description$', description)
    result = result.replace('$body$', content)
    
    # Write output
    with open(output_file, 'w') as f:
        f.write(result)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python3 simple-convert.py <input.md> <output.html> <title> <description> <template.html>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    title = sys.argv[3]
    description = sys.argv[4]
    template_file = sys.argv[5]
    
    convert_markdown_to_html(input_file, output_file, title, description, template_file)