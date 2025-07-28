#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import csv
from collections import defaultdict

def extract_urls_from_sitemap(source_file):
    urls = []
    
    # Read file content first
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse XML
    root = ET.fromstring(content)
    
    for url_elem in root.findall('.//url'):
        url_data = {}
        loc_elem = url_elem.find('loc')
        if loc_elem is not None and loc_elem.text:
            url_data['loc'] = loc_elem.text.strip()
        else:
            continue
        
        lastmod_elem = url_elem.find('lastmod')
        if lastmod_elem is not None and lastmod_elem.text:
            url_data['lastmod'] = lastmod_elem.text.strip()
        
        priority_elem = url_elem.find('priority')
        if priority_elem is not None and priority_elem.text:
            url_data['original_priority'] = float(priority_elem.text.strip())
        
        urls.append(url_data)
    
    return urls

def categorize_url(url):
    path = url.replace('https://www.namesilo.com', '')
    
    if '/blog/' in path:
        return 'blog-sitemap.xml', 0.8
    elif '/support/' in path:
        return 'support-sitemap.xml', 0.6
    elif '/domain-' in path or '/broker' in path or '/marketplace' in path:
        return 'seo-sitemap.xml', 1.0
    elif re.match(r'^/domains/[^/]+$', path):
        return 'tlds-sitemap.xml', 0.9
    elif '/whois' in path or '/ssl-check' in path or '/dns-check' in path:
        return 'tools-sitemap.xml', 0.7
    else:
        return 'misc-sitemap.xml', 0.5

def create_sitemap_xml(cluster_name, urls):
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    for url_data in urls:
        url_elem = ET.SubElement(urlset, 'url')
        
        loc = ET.SubElement(url_elem, 'loc')
        loc.text = url_data['loc']
        
        if 'lastmod' in url_data:
            lastmod = ET.SubElement(url_elem, 'lastmod')
            lastmod.text = url_data['lastmod']
        
        priority = ET.SubElement(url_elem, 'priority')
        priority.text = f"{url_data['assigned_priority']:.2f}"
    
    return ET.tostring(urlset, encoding='unicode', method='xml')

def main():
    print("Starting sitemap restructuring...")
    
    urls = extract_urls_from_sitemap('sitemap.xml')
    print(f"Extracted {len(urls)} URLs from source sitemap")
    
    categorized_urls = defaultdict(list)
    csv_data = []
    cluster_stats = defaultdict(int)
    
    for url_data in urls:
        cluster_name, priority = categorize_url(url_data['loc'])
        url_data['assigned_priority'] = priority
        url_data['assigned_sitemap'] = cluster_name
        
        categorized_urls[cluster_name].append(url_data)
        cluster_stats[cluster_name] += 1
        
        csv_data.append([
            url_data['loc'],
            cluster_name,
            priority,
            url_data.get('lastmod', ''),
            url_data.get('original_priority', '')
        ])
    
    sitemap_files = []
    
    for cluster_name, cluster_urls in categorized_urls.items():
        print(f"Processing {cluster_name}: {len(cluster_urls)} URLs")
        
        cluster_urls.sort(key=lambda x: x['assigned_priority'], reverse=True)
        
        xml_content = create_sitemap_xml(cluster_name, cluster_urls)
        
        with open(cluster_name, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(xml_content)
        
        sitemap_files.append(cluster_name)
    
    # Create sitemap index
    sitemapindex = ET.Element('sitemapindex')
    sitemapindex.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    for sitemap_file in sitemap_files:
        sitemap_elem = ET.SubElement(sitemapindex, 'sitemap')
        
        loc = ET.SubElement(sitemap_elem, 'loc')
        loc.text = f"https://www.namesilo.com/{sitemap_file}"
        
        lastmod = ET.SubElement(sitemap_elem, 'lastmod')
        lastmod.text = "2025-07-28T00:00:00Z"
    
    xml_content = ET.tostring(sitemapindex, encoding='unicode', method='xml')
    
    with open('sitemap-index.xml', 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(xml_content)
    
    # Create CSV log
    with open('sitemap_restructure_log.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['URL', 'Assigned Sitemap', 'Priority', 'Lastmod', 'Original Priority'])
        writer.writerows(csv_data)
    
    print("\n=== Sitemap Restructuring Statistics ===")
    print(f"Total URLs processed: {sum(cluster_stats.values())}")
    print(f"Total sitemaps created: {len(cluster_stats)}")
    
    print("\nCluster Distribution:")
    for cluster_name, count in sorted(cluster_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / sum(cluster_stats.values())) * 100
        print(f"  {cluster_name}: {count} URLs ({percentage:.1f}%)")
    
    print(f"\nFiles created:")
    print(f"  - sitemap-index.xml (main index)")
    for cluster_name in cluster_stats.keys():
        print(f"  - {cluster_name}")
    print(f"  - sitemap_restructure_log.csv (categorization log)")

if __name__ == "__main__":
    main()
