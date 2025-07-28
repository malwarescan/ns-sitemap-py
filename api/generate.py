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
import re
import requests

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

def analyze_competitor_sitemap(xml_content: str) -> dict:
    """Analyze competitor sitemap for insights and recommendations."""
    try:
        # Parse XML
        root = ET.fromstring(xml_content)
        
        # Extract URLs and metadata
        urls = []
        for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            url_data = {}
            
            loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc_elem is not None:
                url_data['url'] = loc_elem.text
            
            priority_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}priority')
            if priority_elem is not None:
                url_data['priority'] = float(priority_elem.text)
            else:
                url_data['priority'] = 0.5
            
            changefreq_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq')
            if changefreq_elem is not None:
                url_data['changefreq'] = changefreq_elem.text
            else:
                url_data['changefreq'] = 'weekly'
            
            urls.append(url_data)
        
        if not urls:
            return {"error": "No URLs found in competitor sitemap"}
        
        # Analyze URL patterns
        categories = analyze_url_categories(urls)
        
        # Calculate statistics
        priorities = [u['priority'] for u in urls if 'priority' in u]
        avg_priority = sum(priorities) / len(priorities) if priorities else 0.5
        
        # Determine update frequency strategy
        changefreqs = [u['changefreq'] for u in urls if 'changefreq' in u]
        update_frequency = determine_update_frequency(changefreqs)
        
        # Generate insights
        insights = generate_insights(urls, categories, avg_priority)
        
        # Generate recommendations
        recommendations = generate_recommendations(urls, categories, avg_priority)
        
        # Create URL structure analysis
        url_structure = create_url_structure_analysis(categories)
        
        return {
            "total_urls": len(urls),
            "avg_priority": avg_priority,
            "categories": list(categories.keys()),
            "update_frequency": update_frequency,
            "insights": insights,
            "recommendations": recommendations,
            "url_structure": url_structure
        }
        
    except Exception as e:
        return {"error": f"Error analyzing competitor sitemap: {str(e)}"}

def analyze_url_categories(urls: list) -> dict:
    """Categorize URLs by content type."""
    categories = {
        'homepage': [],
        'product_pages': [],
        'category_pages': [],
        'blog_content': [],
        'support_help': [],
        'landing_pages': [],
        'tools_utilities': [],
        'other': []
    }
    
    for url_data in urls:
        url = url_data['url'].lower()
        
        if url.endswith('/') or url.endswith('/index.html') or url.endswith('/index.php'):
            categories['homepage'].append(url_data)
        elif any(pattern in url for pattern in ['/product/', '/item/', '/buy/', '/purchase/']):
            categories['product_pages'].append(url_data)
        elif any(pattern in url for pattern in ['/category/', '/catalog/', '/collection/']):
            categories['category_pages'].append(url_data)
        elif any(pattern in url for pattern in ['/blog/', '/news/', '/article/', '/post/']):
            categories['blog_content'].append(url_data)
        elif any(pattern in url for pattern in ['/support/', '/help/', '/faq/', '/guide/']):
            categories['support_help'].append(url_data)
        elif any(pattern in url for pattern in ['/landing/', '/campaign/', '/promo/']):
            categories['landing_pages'].append(url_data)
        elif any(pattern in url for pattern in ['/tool/', '/calculator/', '/checker/', '/generator/']):
            categories['tools_utilities'].append(url_data)
        else:
            categories['other'].append(url_data)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

def determine_update_frequency(changefreqs: list) -> str:
    """Determine the primary update frequency strategy."""
    if not changefreqs:
        return "Not specified"
    
    freq_count = {}
    for freq in changefreqs:
        freq_count[freq] = freq_count.get(freq, 0) + 1
    
    # Find most common frequency
    most_common = max(freq_count.items(), key=lambda x: x[1])
    return f"Mostly {most_common[0]} ({most_common[1]} URLs)"

def generate_insights(urls: list, categories: dict, avg_priority: float) -> list:
    """Generate strategic insights from competitor analysis."""
    insights = []
    
    # Content strategy insights
    if 'blog_content' in categories and len(categories['blog_content']) > 10:
        insights.append("Strong content marketing focus with extensive blog section")
    
    if 'product_pages' in categories and len(categories['product_pages']) > 20:
        insights.append("Comprehensive product catalog with detailed product pages")
    
    if 'tools_utilities' in categories:
        insights.append("Uses tools and utilities to attract and engage users")
    
    # Priority strategy insights
    if avg_priority > 0.7:
        insights.append("High priority strategy - focuses on quality over quantity")
    elif avg_priority < 0.4:
        insights.append("Quantity-focused strategy - covers extensive content")
    else:
        insights.append("Balanced priority strategy")
    
    # URL structure insights
    total_urls = len(urls)
    if total_urls > 1000:
        insights.append("Large-scale content strategy with extensive URL coverage")
    elif total_urls < 100:
        insights.append("Focused, niche content strategy")
    
    return insights

def generate_recommendations(urls: list, categories: dict, avg_priority: float) -> list:
    """Generate optimization recommendations based on competitor analysis."""
    recommendations = []
    
    # Content recommendations
    if 'blog_content' not in categories:
        recommendations.append("Consider adding a blog section for content marketing")
    
    if 'tools_utilities' not in categories:
        recommendations.append("Explore adding interactive tools to increase user engagement")
    
    if 'support_help' not in categories:
        recommendations.append("Add support/help section to improve user experience")
    
    # Priority recommendations
    if avg_priority > 0.7:
        recommendations.append("Consider expanding content coverage while maintaining quality")
    elif avg_priority < 0.4:
        recommendations.append("Focus on improving content quality and priority scores")
    
    # Structure recommendations
    total_urls = len(urls)
    if total_urls < 50:
        recommendations.append("Expand content coverage to compete more effectively")
    elif total_urls > 2000:
        recommendations.append("Focus on content quality and user experience over quantity")
    
    return recommendations

def create_url_structure_analysis(categories: dict) -> list:
    """Create URL structure analysis for display."""
    structure = []
    
    for category_name, urls in categories.items():
        if urls:
            # Get sample URLs (first 5)
            sample_urls = [url['url'] for url in urls[:5]]
            
            structure.append({
                'name': category_name.replace('_', ' ').title(),
                'count': len(urls),
                'sample_urls': sample_urls
            })
    
    return structure

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
            competitor_url = form.get('competitor_url') if 'competitor_url' in form else None
            
            # Save uploaded files temporarily
            with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as gsc_temp:
                gsc_temp.write(gsc_file.file.read())
                gsc_path = gsc_temp.name
            
            with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as pe_temp:
                pe_temp.write(pe_file.file.read())
                pe_path = pe_temp.name
            
            # Fetch competitor sitemap if URL provided
            competitor_xml = None
            if competitor_url:
                try:
                    response = requests.get(competitor_url, timeout=10)
                    response.raise_for_status()
                    competitor_xml = response.text
                except Exception as e:
                    print(f"Error fetching competitor sitemap: {e}")
                    competitor_xml = None
            
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
                
                # Analyze competitor sitemap if provided
                competitor_analysis = None
                if competitor_xml:
                    try:
                        competitor_analysis = analyze_competitor_sitemap(competitor_xml)
                    except Exception as e:
                        competitor_analysis = {"error": f"Error analyzing competitor sitemap: {str(e)}"}
                
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
                    "sitemap_content": sitemaps,  # Include XML content
                    "competitor_analysis": competitor_analysis  # Include competitor analysis
                }
                
                self.wfile.write(json.dumps(response_data).encode())
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(gsc_path)
                    os.unlink(pe_path)
                    # Removed competitor_path cleanup as it's no longer used
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