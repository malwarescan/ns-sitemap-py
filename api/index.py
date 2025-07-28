from flask import Flask, jsonify, request, send_file, render_template_string
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

# HTML template for the UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sitemap Priority System</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .upload-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
        }
        .file-input {
            margin: 15px 0;
        }
        .file-input label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        .file-input input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 2px dashed #ddd;
            border-radius: 6px;
            background: white;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .results {
            margin-top: 30px;
            display: none;
        }
        .results.show {
            display: block;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .data-table th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }
        .data-table td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        .data-table tr:hover {
            background: #f8f9fa;
        }
        .cluster-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .cluster-blog { background: #e3f2fd; color: #1976d2; }
        .cluster-support { background: #f3e5f5; color: #7b1fa2; }
        .cluster-tlds { background: #e8f5e8; color: #388e3c; }
        .cluster-tools { background: #fff3e0; color: #f57c00; }
        .cluster-seo { background: #fce4ec; color: #c2185b; }
        .cluster-misc { background: #f5f5f5; color: #616161; }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
            border-left: 4px solid #c62828;
        }
        .success {
            background: #e8f5e8;
            color: #2e7d32;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
            border-left: 4px solid #2e7d32;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🗺️ Sitemap Priority System</h1>
        
        <div class="upload-section">
            <h2>Upload Data Files</h2>
            <form id="uploadForm">
                <div class="file-input">
                    <label for="gscFile">Google Search Console Data (CSV)</label>
                    <input type="file" id="gscFile" name="gsc_data" accept=".csv" required>
                </div>
                <div class="file-input">
                    <label for="peFile">Page Explorer Data (CSV)</label>
                    <input type="file" id="peFile" name="pe_data" accept=".csv" required>
                </div>
                <button type="submit" class="btn" id="submitBtn">🚀 Process Data</button>
            </form>
        </div>

        <div id="loading" class="loading" style="display: none;">
            <h3>Processing your data...</h3>
            <p>This may take a few moments.</p>
        </div>

        <div id="error" class="error" style="display: none;"></div>
        <div id="success" class="success" style="display: none;"></div>

        <div id="results" class="results">
            <h2>📊 Processing Results</h2>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="gscCount">0</div>
                    <div class="stat-label">GSC URLs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="peCount">0</div>
                    <div class="stat-label">Page Explorer URLs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="mergedCount">0</div>
                    <div class="stat-label">Merged URLs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="avgPriority">0.00</div>
                    <div class="stat-label">Avg Priority</div>
                </div>
            </div>

            <h3>📋 Sample Data (Top 10 URLs)</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>URL</th>
                        <th>Priority</th>
                        <th>Cluster</th>
                        <th>Clicks</th>
                        <th>Impressions</th>
                        <th>CTR</th>
                        <th>Position</th>
                    </tr>
                </thead>
                <tbody id="dataTable">
                </tbody>
            </table>
        </div>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const gscFile = document.getElementById('gscFile').files[0];
            const peFile = document.getElementById('peFile').files[0];
            
            if (!gscFile || !peFile) {
                showError('Please select both CSV files');
                return;
            }
            
            formData.append('gsc_data', gscFile);
            formData.append('pe_data', peFile);
            
            // Show loading
            showLoading(true);
            hideError();
            hideSuccess();
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showSuccess(result.message);
                    displayResults(result);
                } else {
                    showError(result.error || 'An error occurred');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                showLoading(false);
            }
        });
        
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
            document.getElementById('submitBtn').disabled = show;
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
        
        function hideError() {
            document.getElementById('error').style.display = 'none';
        }
        
        function showSuccess(message) {
            const successDiv = document.getElementById('success');
            successDiv.textContent = message;
            successDiv.style.display = 'block';
        }
        
        function hideSuccess() {
            document.getElementById('success').style.display = 'none';
        }
        
        function displayResults(data) {
            // Update stats
            document.getElementById('gscCount').textContent = data.gsc_urls;
            document.getElementById('peCount').textContent = data.pe_urls;
            document.getElementById('mergedCount').textContent = data.merged_urls;
            
            // Calculate average priority
            if (data.sample_data && data.sample_data.length > 0) {
                const avgPriority = data.sample_data.reduce((sum, item) => sum + item.priority, 0) / data.sample_data.length;
                document.getElementById('avgPriority').textContent = avgPriority.toFixed(2);
            }
            
            // Display sample data
            const tableBody = document.getElementById('dataTable');
            tableBody.innerHTML = '';
            
            if (data.sample_data && data.sample_data.length > 0) {
                data.sample_data.slice(0, 10).forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.url}</td>
                        <td><strong>${item.priority.toFixed(3)}</strong></td>
                        <td><span class="cluster-badge cluster-${item.cluster}">${item.cluster}</span></td>
                        <td>${item.clicks || 0}</td>
                        <td>${item.impressions || 0}</td>
                        <td>${(item.ctr || 0).toFixed(3)}</td>
                        <td>${item.position || 0}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
            
            // Show results
            document.getElementById('results').classList.add('show');
        }
    </script>
</body>
</html>
"""

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
    """Home page with UI."""
    return render_template_string(HTML_TEMPLATE)

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
        
        # Sort by priority (highest first)
        result.sort(key=lambda x: x['priority'], reverse=True)
        
        # Clean up temporary files
        os.unlink(gsc_path)
        os.unlink(pe_path)
        
        return jsonify({
            "message": "Sitemaps processed successfully",
            "gsc_urls": len(gsc_data),
            "pe_urls": len(pe_data),
            "merged_urls": len(result),
            "timestamp": datetime.now().isoformat(),
            "sample_data": result[:10] if result else []
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