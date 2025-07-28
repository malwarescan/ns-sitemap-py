#!/usr/bin/env python3
"""
Simplified test script for the sitemap priority system
"""

import csv
from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    try:
        parsed = urlparse(url)
        clean = parsed._replace(query='', fragment='').geturl()
        if clean.endswith('/') and clean != parsed.scheme + '://' + parsed.netloc + '/':
            clean = clean[:-1]
        return clean.lower()
    except Exception:
        return url.lower().rstrip('/')

def load_csv_data(file_path: str, expected_columns: list) -> list:
    """Load data from CSV file."""
    data = []
    try:
        print(f"Loading CSV from: {file_path}")
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            print(f"CSV headers: {reader.fieldnames}")
            
            for row_num, row in enumerate(reader):
                # Try different possible URL column names
                url = row.get('url') or row.get('URL') or row.get('page') or row.get('Page') or row.get('link') or row.get('Link')
                if not url:
                    print(f"Row {row_num + 1}: No URL found in columns {list(row.keys())}")
                    continue
                
                entry = {'url': url.strip()}
                for col in expected_columns:
                    if col in row:
                        try:
                            entry[col] = float(row[col])
                        except (ValueError, TypeError):
                            entry[col] = 0.0
                    else:
                        entry[col] = 0.0
                data.append(entry)
                
                if row_num < 3:  # Print first 3 rows for debugging
                    print(f"Row {row_num + 1}: {entry}")
                    
    except Exception as e:
        print(f"Error loading CSV data: {e}")
        import traceback
        traceback.print_exc()
    return data

def calculate_priority(url_entry: dict) -> float:
    """Calculate priority score for a URL."""
    priority = 0.0
    
    # GSC Performance Score (40% weight)
    gsc_score = 0.0
    clicks = url_entry.get('clicks', 0)
    impressions = url_entry.get('impressions', 0)
    ctr = url_entry.get('ctr', 0)
    position = url_entry.get('position', 0)
    
    if impressions > 0:
        click_rate = clicks / impressions
        gsc_score += click_rate * 0.3
    
    gsc_score += min(ctr, 1.0) * 0.3
    
    if position > 0:
        position_score = max(0, 1 - (position / 100))
        gsc_score += position_score * 0.4
    
    # Page Explorer Score (40% weight)
    pe_score = 0.0
    importance = url_entry.get('importance', 0)
    depth = url_entry.get('depth', 0)
    internal_links = url_entry.get('internal_links', 0)
    health = url_entry.get('health', 0)
    
    pe_score += min(importance / 100, 1.0) * 0.4
    
    if depth > 0:
        depth_score = max(0, 1 - (depth / 10))
        pe_score += depth_score * 0.2
    
    if internal_links > 0:
        links_score = min(internal_links / 100, 1.0)
        pe_score += links_score * 0.2
    
    pe_score += min(health / 100, 1.0) * 0.2
    
    # Business Logic Score (20% weight)
    business_score = 0.0
    url = url_entry.get('url', '').lower()
    
    if url.endswith('/') or url.endswith('/index.html'):
        business_score += 0.5
    
    if '/tld/' in url or '/domains/' in url:
        business_score += 0.3
    
    if '/blog/' in url:
        business_score += 0.2
    
    if '/support/' in url:
        business_score += 0.1
    
    if any(tool in url for tool in ['/whois', '/ssl-check', '/dns-check']):
        business_score += 0.2
    
    business_score = min(business_score, 1.0)
    
    # Calculate final weighted priority
    priority = (gsc_score * 0.4) + (pe_score * 0.4) + (business_score * 0.2)
    
    return max(0.1, min(1.0, priority))

def assign_cluster(url: str) -> str:
    """Assign a URL to a cluster."""
    url_lower = url.lower()
    
    if '/blog/' in url_lower:
        return 'blog'
    elif '/support/' in url_lower or '/help/' in url_lower:
        return 'support'
    elif '/tld/' in url_lower or '/domains/' in url_lower:
        return 'tlds'
    elif any(tool in url_lower for tool in ['/whois', '/ssl-check', '/dns-check']):
        return 'tools'
    elif any(pattern in url_lower for pattern in ['/domain-', '/broker', '/marketplace']):
        return 'seo'
    else:
        return 'misc'

def test_system():
    """Test the sitemap system with sample data"""
    print("🧪 Testing Sitemap Priority System...")
    
    # Test 1: Load CSV data
    print("\n1. Testing CSV data loading...")
    try:
        gsc_data = load_csv_data('sample_gsc_data.csv', ['clicks', 'impressions', 'ctr', 'position'])
        pe_data = load_csv_data('sample_pe_data.csv', ['importance', 'depth', 'internal_links', 'health'])
        
        print(f"✅ GSC data loaded: {len(gsc_data)} URLs")
        print(f"✅ Page Explorer data loaded: {len(pe_data)} URLs")
        
        if len(gsc_data) == 0 or len(pe_data) == 0:
            print("❌ No data loaded from CSV files")
            return False
            
    except Exception as e:
        print(f"❌ Error loading CSV data: {e}")
        return False
    
    # Test 2: Merge and process data
    print("\n2. Testing data processing...")
    try:
        # Merge and deduplicate
        merged = defaultdict(dict)
        for entry in gsc_data:
            norm = normalize_url(entry['url'])
            merged[norm].update(entry)
        for entry in pe_data:
            norm = normalize_url(entry['url'])
            merged[norm].update(entry)
        
        print(f"✅ Merged data: {len(merged)} unique URLs")
        
        # Process priorities and clusters
        result = []
        for norm_url, data in merged.items():
            data['url'] = norm_url
            data['priority'] = calculate_priority(data)
            data['cluster'] = assign_cluster(norm_url)
            result.append(data)
        
        print(f"✅ Processed result: {len(result)} URLs")
        
        if len(result) == 0:
            print("❌ No processed data")
            return False
            
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        return False
    
    # Test 3: Create clusters
    print("\n3. Testing clustering...")
    try:
        # Sort by priority
        result.sort(key=lambda x: x['priority'], reverse=True)
        
        # Group by cluster
        clusters = defaultdict(list)
        for item in result:
            clusters[item['cluster']].append(item)
        
        print(f"✅ Clusters created: {list(clusters.keys())}")
        
        for cluster_name, cluster_urls in clusters.items():
            print(f"   - {cluster_name}: {len(cluster_urls)} URLs")
            
    except Exception as e:
        print(f"❌ Error creating clusters: {e}")
        return False
    
    # Test 4: Show sample results
    print("\n4. Sample results:")
    print("Top 5 URLs by priority:")
    for i, item in enumerate(result[:5]):
        print(f"   {i+1}. {item['url']} (Priority: {item['priority']:.3f}, Cluster: {item['cluster']})")
    
    print(f"\n✅ All tests passed! Processed {len(result)} URLs into {len(clusters)} clusters.")
    return True

if __name__ == "__main__":
    success = test_system()
    if success:
        print("\n🎉 System is working correctly!")
        exit(0)
    else:
        print("\n💥 System has issues that need to be fixed.")
        exit(1) 