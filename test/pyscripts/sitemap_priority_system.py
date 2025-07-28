"""
Sitemap Priority System
----------------------
A modular system for generating structured, priority-driven sitemaps from Google Search Console and Page Explorer data.

Steps:
1. Load GSC and Page Explorer data
2. Merge and deduplicate URLs
3. Calculate composite priority for each URL
4. Cluster URLs by business logic
5. Output protocol-compliant XML sitemaps and sitemap index
"""

import os
import csv
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
from urllib.parse import urlparse

# 1. Data Loading

def load_gsc_data(gsc_path: str) -> List[Dict[str, Any]]:
    """Load Google Search Console data from CSV. Expects columns: url, clicks, impressions, ctr, position."""
    data = []
    try:
        with open(gsc_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                url = row.get('url') or row.get('URL')
                if not url:
                    continue
                data.append({
                    'url': url.strip(),
                    'clicks': float(row.get('clicks', 0)),
                    'impressions': float(row.get('impressions', 0)),
                    'ctr': float(row.get('ctr', 0)),
                    'position': float(row.get('position', 0)),
                })
    except Exception as e:
        print(f"Error loading GSC data: {e}")
    return data

def load_page_explorer_data(pe_path: str) -> List[Dict[str, Any]]:
    """Load Page Explorer data from CSV. Expects columns: url, importance, depth, internal_links, health."""
    data = []
    try:
        with open(pe_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                url = row.get('url') or row.get('URL')
                if not url:
                    continue
                data.append({
                    'url': url.strip(),
                    'importance': float(row.get('importance', 0)),
                    'depth': float(row.get('depth', 0)),
                    'internal_links': float(row.get('internal_links', 0)),
                    'health': float(row.get('health', 0)),
                })
    except Exception as e:
        print(f"Error loading Page Explorer data: {e}")
    return data

# Helper: Normalize URL for deduplication

def normalize_url(url: str) -> str:
    """Normalize URL for deduplication (lowercase, strip trailing slash, remove fragments/query)."""
    try:
        parsed = urlparse(url)
        clean = parsed._replace(query='', fragment='').geturl()
        if clean.endswith('/') and clean != parsed.scheme + '://' + parsed.netloc + '/':
            clean = clean[:-1]
        return clean.lower()
    except Exception:
        return url.lower().rstrip('/')

# 2. Data Merging & Deduplication

def merge_and_deduplicate(gsc_data, pe_data) -> List[Dict[str, Any]]:
    """Merge GSC and Page Explorer data, deduplicate by normalized URL, and combine metrics."""
    merged = defaultdict(dict)
    # Index GSC data
    for entry in gsc_data:
        norm = normalize_url(entry['url'])
        merged[norm].update(entry)
    # Index Page Explorer data
    for entry in pe_data:
        norm = normalize_url(entry['url'])
        merged[norm].update(entry)
    # Add normalized URL as canonical key
    result = []
    for norm_url, data in merged.items():
        data['url'] = norm_url
        result.append(data)
    return result

# 3. Priority Calculation

def calculate_priority(url_entry: Dict[str, Any]) -> float:
    """
    Calculate composite priority using GSC, Page Explorer, and business logic factors.
    
    Priority Formula:
    - GSC Performance (40%): clicks, impressions, CTR, position
    - Page Explorer Metrics (40%): importance, depth, internal links, health
    - Business Logic (20%): homepage boost, TLD priority, content type
    """
    priority = 0.0
    
    # GSC Performance Score (40% weight)
    gsc_score = 0.0
    if 'clicks' in url_entry and 'impressions' in url_entry:
        # Normalize clicks (0-1 scale)
        clicks = url_entry.get('clicks', 0)
        impressions = url_entry.get('impressions', 0)
        ctr = url_entry.get('ctr', 0)
        position = url_entry.get('position', 0)
        
        # Click rate score (higher is better)
        if impressions > 0:
            click_rate = clicks / impressions
            gsc_score += click_rate * 0.3
        
        # CTR score (higher is better)
        gsc_score += min(ctr, 1.0) * 0.3
        
        # Position score (lower position is better)
        if position > 0:
            position_score = max(0, 1 - (position / 100))  # Normalize to 0-1
            gsc_score += position_score * 0.4
    
    # Page Explorer Score (40% weight)
    pe_score = 0.0
    if 'importance' in url_entry:
        importance = url_entry.get('importance', 0)
        depth = url_entry.get('depth', 0)
        internal_links = url_entry.get('internal_links', 0)
        health = url_entry.get('health', 0)
        
        # Importance score (0-1)
        pe_score += min(importance / 100, 1.0) * 0.4
        
        # Depth score (shallow pages are better)
        if depth > 0:
            depth_score = max(0, 1 - (depth / 10))  # Normalize to 0-1
            pe_score += depth_score * 0.2
        
        # Internal links score (more links = better)
        if internal_links > 0:
            links_score = min(internal_links / 100, 1.0)  # Cap at 100 links
            pe_score += links_score * 0.2
        
        # Health score (0-1)
        pe_score += min(health / 100, 1.0) * 0.2
    
    # Business Logic Score (20% weight)
    business_score = 0.0
    url = url_entry.get('url', '').lower()
    
    # Homepage boost
    if url.endswith('/') or url.endswith('/index.html') or url.endswith('/index.php'):
        business_score += 0.5
    
    # TLD pages boost
    if '/tld/' in url or '/domains/' in url:
        business_score += 0.3
    
    # Blog content boost
    if '/blog/' in url:
        business_score += 0.2
    
    # Support content boost
    if '/support/' in url:
        business_score += 0.1
    
    # Tools boost
    if any(tool in url for tool in ['/whois', '/ssl-check', '/dns-check']):
        business_score += 0.2
    
    # Cap business score at 1.0
    business_score = min(business_score, 1.0)
    
    # Calculate final weighted priority
    priority = (gsc_score * 0.4) + (pe_score * 0.4) + (business_score * 0.2)
    
    # Ensure priority is between 0.1 and 1.0
    return max(0.1, min(1.0, priority))

# 4. Clustering/Structuring

def assign_cluster(url: str, metadata: Dict[str, Any]) -> str:
    """
    Assign a URL to a cluster based on patterns and business logic.
    
    Clusters:
    - blog: Blog content
    - support: Support articles and help
    - tlds: TLD-specific pages
    - tools: Utility tools (whois, SSL check, etc.)
    - seo: SEO/service pages
    - misc: Everything else
    """
    url_lower = url.lower()
    
    # Blog content
    if '/blog/' in url_lower:
        return 'blog'
    
    # Support content
    if '/support/' in url_lower or '/help/' in url_lower:
        return 'support'
    
    # TLD pages
    if '/tld/' in url_lower or re.match(r'/domains/[^/]+/?$', url_lower):
        return 'tlds'
    
    # Tools
    if any(tool in url_lower for tool in ['/whois', '/ssl-check', '/dns-check', '/tool']):
        return 'tools'
    
    # SEO/Service pages
    if any(pattern in url_lower for pattern in ['/domain-', '/broker', '/marketplace', '/service']):
        return 'seo'
    
    # Default to misc
    return 'misc'

def cluster_urls(urls: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group URLs into clusters for separate sitemaps."""
    clusters = defaultdict(list)
    
    for url_entry in urls:
        url = url_entry.get('url', '')
        cluster = assign_cluster(url, url_entry)
        clusters[cluster].append(url_entry)
    
    # Sort each cluster by priority (highest first)
    for cluster_name, cluster_urls in clusters.items():
        clusters[cluster_name] = sorted(cluster_urls, key=lambda x: x.get('priority', 0), reverse=True)
    
    return dict(clusters)

# 5. XML Sitemap Output

def write_xml_sitemap(cluster_name: str, urls: List[Dict[str, Any]], output_dir: str):
    """Write a protocol-compliant XML sitemap for a cluster."""
    if not urls:
        print(f"No URLs for cluster: {cluster_name}")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create XML structure
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    for url_entry in urls:
        url_elem = ET.SubElement(urlset, 'url')
        
        # URL location
        loc_elem = ET.SubElement(url_elem, 'loc')
        loc_elem.text = url_entry.get('url', '')
        
        # Last modified (use current date if not available)
        lastmod_elem = ET.SubElement(url_elem, 'lastmod')
        lastmod = url_entry.get('lastmod', datetime.now().strftime('%Y-%m-%d'))
        lastmod_elem.text = lastmod
        
        # Change frequency (based on content type)
        changefreq_elem = ET.SubElement(url_elem, 'changefreq')
        if cluster_name == 'blog':
            changefreq_elem.text = 'weekly'
        elif cluster_name == 'support':
            changefreq_elem.text = 'weekly'
        elif cluster_name == 'tools':
            changefreq_elem.text = 'monthly'
        elif cluster_name == 'tlds':
            changefreq_elem.text = 'monthly'
        else:
            changefreq_elem.text = 'monthly'
        
        # Priority
        priority_elem = ET.SubElement(url_elem, 'priority')
        priority = url_entry.get('priority', 0.5)
        priority_elem.text = f"{priority:.2f}"
    
    # Pretty print XML
    rough_string = ET.tostring(urlset, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Write to file
    output_file = os.path.join(output_dir, f"{cluster_name}-sitemap.xml")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Created {cluster_name}-sitemap.xml with {len(urls)} URLs")

def write_sitemap_index(sitemap_files: List[str], output_dir: str):
    """Write a sitemap index referencing all cluster sitemaps."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create XML structure
    sitemapindex = ET.Element('sitemapindex')
    sitemapindex.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    for sitemap_file in sitemap_files:
        sitemap_elem = ET.SubElement(sitemapindex, 'sitemap')
        
        # Sitemap location
        loc_elem = ET.SubElement(sitemap_elem, 'loc')
        loc_elem.text = f"https://www.namesilo.com/{sitemap_file}"
        
        # Last modified
        lastmod_elem = ET.SubElement(sitemap_elem, 'lastmod')
        lastmod_elem.text = datetime.now().strftime('%Y-%m-%d')
    
    # Pretty print XML
    rough_string = ET.tostring(sitemapindex, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Write to file
    output_file = os.path.join(output_dir, 'sitemap-index.xml')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    
    print(f"Created sitemap-index.xml with {len(sitemap_files)} sitemaps")

# Main Orchestration

def main(gsc_path: str, pe_path: str, output_dir: str):
    """Orchestrate the full pipeline from data loading to sitemap output."""
    print("Starting Sitemap Priority System...")
    
    # 1. Load data
    print("Loading GSC data...")
    gsc_data = load_gsc_data(gsc_path)
    print(f"Loaded {len(gsc_data)} GSC URLs")
    
    print("Loading Page Explorer data...")
    pe_data = load_page_explorer_data(pe_path)
    print(f"Loaded {len(pe_data)} Page Explorer URLs")
    
    # 2. Merge/deduplicate
    print("Merging and deduplicating data...")
    merged = merge_and_deduplicate(gsc_data, pe_data)
    print(f"Merged into {len(merged)} unique URLs")
    
    # 3. Calculate priority
    print("Calculating priorities...")
    for entry in merged:
        entry['priority'] = calculate_priority(entry)
    
    # 4. Cluster
    print("Clustering URLs...")
    clusters = cluster_urls(merged)
    
    # Print cluster statistics
    for cluster_name, urls_in_cluster in clusters.items():
        avg_priority = sum(u.get('priority', 0) for u in urls_in_cluster) / len(urls_in_cluster)
        print(f"  {cluster_name}: {len(urls_in_cluster)} URLs, avg priority: {avg_priority:.3f}")
    
    # 5. Output XML sitemaps
    print("Generating XML sitemaps...")
    sitemap_files = []
    for cluster, urls in clusters.items():
        write_xml_sitemap(cluster, urls, output_dir)
        sitemap_files.append(f"{cluster}-sitemap.xml")
    
    write_sitemap_index(sitemap_files, output_dir)
    
    print(f"Complete! Generated {len(sitemap_files)} sitemaps in {output_dir}")

if __name__ == "__main__":
    # Example usage (paths to be set by user)
    main(
        gsc_path="../gsc-pages.csv",
        pe_path="../page_explorer_data.csv",
        output_dir="../sitemaps-output/"
    ) 