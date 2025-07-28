from http.server import BaseHTTPRequestHandler
import json
import os
import tempfile
import csv
from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse, parse_qs
import cgi
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
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                url = row.get('url') or row.get('URL') or row.get('page')
                if not url:
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
    except Exception as e:
        print(f"Error loading CSV data: {e}")
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

def create_sitemap_xml(urls: list, sitemap_name: str) -> str:
    """Create XML sitemap from URL list."""
    # Create root element
    root = ET.Element('urlset')
    root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    # Add URLs
    for url_data in urls:
        url_elem = ET.SubElement(root, 'url')
        
        # URL location
        loc_elem = ET.SubElement(url_elem, 'loc')
        loc_elem.text = url_data['url']
        
        # Last modified (use current time)
        lastmod_elem = ET.SubElement(url_elem, 'lastmod')
        lastmod_elem.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
        
        # Change frequency
        changefreq_elem = ET.SubElement(url_elem, 'changefreq')
        if url_data['cluster'] == 'blog':
            changefreq_elem.text = 'weekly'
        elif url_data['cluster'] == 'support':
            changefreq_elem.text = 'monthly'
        else:
            changefreq_elem.text = 'daily'
        
        # Priority
        priority_elem = ET.SubElement(url_elem, 'priority')
        priority_elem.text = f"{url_data['priority']:.4f}"
    
    # Pretty print XML
    rough_string = ET.tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def create_sitemap_index(clusters: dict) -> str:
    """Create sitemap index XML."""
    root = ET.Element('sitemapindex')
    root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    for cluster_name, urls in clusters.items():
        if urls:  # Only add clusters with URLs
            sitemap_elem = ET.SubElement(root, 'sitemap')
            
            loc_elem = ET.SubElement(sitemap_elem, 'loc')
            loc_elem.text = f"https://your-domain.com/{cluster_name}-sitemap.xml"
            
            lastmod_elem = ET.SubElement(sitemap_elem, 'lastmod')
            lastmod_elem.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Pretty print XML
    rough_string = ET.tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            # Parse multipart form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            # Check if files were uploaded
            if 'gsc_data' not in form or 'pe_data' not in form:
                response = {"error": "Both GSC and Page Explorer CSV files are required"}
                self.wfile.write(json.dumps(response).encode())
                return
            
            gsc_file = form['gsc_data']
            pe_file = form['pe_data']
            
            # Save uploaded files temporarily
            with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as gsc_temp:
                gsc_temp.write(gsc_file.file.read())
                gsc_path = gsc_temp.name
            
            with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as pe_temp:
                pe_temp.write(pe_file.file.read())
                pe_path = pe_temp.name
            
            try:
                # Load data
                gsc_data = load_csv_data(gsc_path, ['clicks', 'impressions', 'ctr', 'position'])
                pe_data = load_csv_data(pe_path, ['importance', 'depth', 'internal_links', 'health'])
                
                # Merge and deduplicate
                merged = defaultdict(dict)
                for entry in gsc_data:
                    norm = normalize_url(entry['url'])
                    merged[norm].update(entry)
                for entry in pe_data:
                    norm = normalize_url(entry['url'])
                    merged[norm].update(entry)
                
                result = []
                for norm_url, data in merged.items():
                    data['url'] = norm_url
                    data['priority'] = calculate_priority(data)
                    data['cluster'] = assign_cluster(norm_url)
                    result.append(data)
                
                # Sort by priority (highest first)
                result.sort(key=lambda x: x['priority'], reverse=True)
                
                # Group by cluster
                clusters = defaultdict(list)
                for item in result:
                    clusters[item['cluster']].append(item)
                
                # Create sitemap XMLs
                sitemaps = {}
                for cluster_name, cluster_urls in clusters.items():
                    if cluster_urls:
                        sitemap_xml = create_sitemap_xml(cluster_urls, f"{cluster_name}-sitemap.xml")
                        sitemaps[f"{cluster_name}-sitemap.xml"] = sitemap_xml
                
                # Create sitemap index
                sitemap_index = create_sitemap_index(clusters)
                sitemaps["sitemap-index.xml"] = sitemap_index
                
                # Calculate statistics
                cluster_stats = {}
                for cluster_name, cluster_urls in clusters.items():
                    if cluster_urls:
                        avg_priority = sum(u['priority'] for u in cluster_urls) / len(cluster_urls)
                        cluster_stats[cluster_name] = {
                            'count': len(cluster_urls),
                            'avg_priority': round(avg_priority, 3),
                            'top_priority': max(u['priority'] for u in cluster_urls)
                        }
                
                response_data = {
                    "message": "Sitemaps generated successfully",
                    "gsc_urls": len(gsc_data),
                    "pe_urls": len(pe_data),
                    "merged_urls": len(result),
                    "timestamp": datetime.now().isoformat(),
                    "cluster_stats": cluster_stats,
                    "sitemaps_created": list(sitemaps.keys()),
                    "sample_data": result[:10] if result else [],  # Keep sample for UI display
                    "full_data": result,  # Include full data
                    "sitemap_content": sitemaps  # Include XML content
                }
                
                self.wfile.write(json.dumps(response_data).encode())
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(gsc_path)
                    os.unlink(pe_path)
                except:
                    pass
                    
        except Exception as e:
            response = {"error": f"Processing error: {str(e)}"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 