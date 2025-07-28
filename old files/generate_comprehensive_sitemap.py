#!/usr/bin/env python3
"""
Comprehensive Sitemap Generator for NameSilo.com
Generates an AI-optimized sitemap from urllist.txt with proper priorities and change frequencies.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import re

def determine_priority_and_frequency(url):
    """Determine priority and change frequency based on URL patterns."""
    
    # High priority core business pages
    if url in [
        'https://www.namesilo.com/',
        'https://www.namesilo.com/domain/search-domains',
        'https://www.namesilo.com/domain/transfer-domains',
        'https://www.namesilo.com/hosting',
        'https://www.namesilo.com/email',
        'https://www.namesilo.com/ssl',
        'https://www.namesilo.com/Marketplace',
        'https://www.namesilo.com/pricing',
        'https://www.namesilo.com/discount-program',
        'https://www.namesilo.com/discounts-and-promotions'
    ]:
        return 0.9, 'daily'
    
    # AI-specific pages
    if '/ai' in url:
        return 0.9, 'weekly'
    
    # Blog content - high priority for semantic search
    if '/blog/' in url:
        return 0.8, 'monthly'
    
    # Support articles
    if '/support/v2/articles/' in url:
        if '/domain-manager/' in url or '/email/' in url:
            return 0.7, 'monthly'
        else:
            return 0.6, 'monthly'
    
    # Tools and services
    if any(x in url for x in ['/whois', '/free-logo-maker', '/domain_tools.php', '/api-reference']):
        return 0.7, 'weekly'
    
    # Account and user pages
    if any(x in url for x in ['/sign-up', '/login', '/loyalty-program']):
        return 0.7, 'monthly'
    
    # Payment options
    if '/payment-options/' in url:
        return 0.6, 'monthly'
    
    # Custom domain integrations
    if '/CustomDomain/' in url:
        return 0.6, 'monthly'
    
    # Reseller pages
    if '/reseller/' in url:
        return 0.8, 'weekly'
    
    # RSS and dynamic content
    if 'auction_rss.php' in url:
        return 0.8, 'hourly'
    
    # Legal and policy pages
    if any(x in url for x in ['/terms.php', '/Support/Privacy-Policy', '/terms-and-conditions']):
        return 0.5, 'yearly'
    
    # About and company information
    if any(x in url for x in ['/about-us', '/about/about-namesilo']):
        return 0.6, 'monthly'
    
    # Default for other pages
    return 0.6, 'monthly'

def create_sitemap():
    """Create comprehensive sitemap from urllist.txt."""
    
    # Create root element with namespaces
    root = ET.Element('urlset')
    root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    root.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')
    root.set('xmlns:video', 'http://www.google.com/schemas/sitemap-video/1.1')
    root.set('xmlns:news', 'http://www.google.com/schemas/sitemap-news/0.9')
    root.set('xmlns:xhtml', 'http://www.w3.org/1999/xhtml')
    
    # Read URLs from urllist.txt
    with open('urllist.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    # Current timestamp
    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Process each URL
    for url in urls:
        priority, changefreq = determine_priority_and_frequency(url)
        
        # Create URL element
        url_elem = ET.SubElement(root, 'url')
        
        # Location
        loc_elem = ET.SubElement(url_elem, 'loc')
        loc_elem.text = url
        
        # Last modified
        lastmod_elem = ET.SubElement(url_elem, 'lastmod')
        lastmod_elem.text = current_time
        
        # Change frequency
        changefreq_elem = ET.SubElement(url_elem, 'changefreq')
        changefreq_elem.text = changefreq
        
        # Priority
        priority_elem = ET.SubElement(url_elem, 'priority')
        priority_elem.text = str(priority)
        
        # Add image for homepage
        if url == 'https://www.namesilo.com/':
            image_elem = ET.SubElement(url_elem, '{http://www.google.com/schemas/sitemap-image/1.1}image')
            
            image_loc = ET.SubElement(image_elem, '{http://www.google.com/schemas/sitemap-image/1.1}loc')
            image_loc.text = 'https://www.namesilo.com/images/namesilo-logo.png'
            
            image_title = ET.SubElement(image_elem, '{http://www.google.com/schemas/sitemap-image/1.1}title')
            image_title.text = 'NameSilo - Domain Registration and Web Hosting'
            
            image_caption = ET.SubElement(image_elem, '{http://www.google.com/schemas/sitemap-image/1.1}caption')
            image_caption.text = 'NameSilo provides affordable domain registration, web hosting, and online services'
    
    # Create pretty XML
    rough_string = ET.tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Write to file
    with open('sitemap-comprehensive.xml', 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Generated comprehensive sitemap with {len(urls)} URLs")
    print("File: sitemap-comprehensive.xml")

if __name__ == "__main__":
    create_sitemap() 