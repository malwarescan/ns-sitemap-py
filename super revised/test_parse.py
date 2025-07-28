#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Read file content
with open('sitemap.xml', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File content length: {len(content)}")
print(f"First 200 chars: {content[:200]}")

# Parse XML
root = ET.fromstring(content)
print(f"Root tag: {root.tag}")

# Find URLs
urls = root.findall('.//url')
print(f"Found {len(urls)} URL elements")

if urls:
    first_url = urls[0]
    loc = first_url.find('loc')
    if loc is not None:
        print(f"First URL: {loc.text}")
