from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import tempfile
import json
import csv
from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# Simplified sitemap functions for Vercel deployment
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
                # Handle different column name variations
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

@app.route('/')
def home():
    """Home page with API documentation."""
    return jsonify({
        "message": "Sitemap Priority System API",
        "version": "1.0.0",
        "status": "deployed",
        "endpoints": {
            "/api/health": "Health check",
            "/api/sitemaps": "List available sitemaps",
            "/api/generate": "Generate new sitemaps (POST with CSV data)",
            "/api/download/<sitemap>": "Download specific sitemap"
        }
    })

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "deployment": "vercel"
    })

@app.route('/api/sitemaps')
def list_sitemaps():
    """List all available sitemaps."""
    return jsonify({
        "sitemaps": [],
        "count": 0,
        "message": "No sitemaps generated yet. Use /api/generate to create sitemaps."
    })

@app.route('/api/generate', methods=['POST'])
def generate_sitemaps():
    """Generate new sitemaps from uploaded CSV data."""
    try:
        # Check if files were uploaded
        if 'gsc_data' not in request.files or 'pe_data' not in request.files:
            return jsonify({"error": "Both GSC and Page Explorer CSV files are required"}), 400
        
        gsc_file = request.files['gsc_data']
        pe_file = request.files['pe_data']
        
        # Save uploaded files temporarily
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as gsc_temp:
            gsc_file.save(gsc_temp.name)
            gsc_path = gsc_temp.name
        
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as pe_temp:
            pe_file.save(pe_temp.name)
            pe_path = pe_temp.name
        
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
        
        # Clean up temporary files
        os.unlink(gsc_path)
        os.unlink(pe_path)
        
        return jsonify({
            "message": "Sitemaps processed successfully",
            "gsc_urls": len(gsc_data),
            "pe_urls": len(pe_data),
            "merged_urls": len(result),
            "timestamp": datetime.now().isoformat(),
            "sample_data": result[:5] if result else []
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<sitemap_name>')
def download_sitemap(sitemap_name):
    """Download a specific sitemap file."""
    return jsonify({
        "error": "Sitemap not found",
        "message": "Use /api/generate to create sitemaps first"
    }), 404

if __name__ == '__main__':
    app.run(debug=True) 