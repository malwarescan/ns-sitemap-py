from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

# HTML template for the UI (very plain)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sitemap Priority System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: white;
        }
        h1 { margin-bottom: 20px; }
        .upload-section { margin-bottom: 20px; }
        .file-input { margin: 10px 0; }
        .file-input label { display: block; margin-bottom: 5px; }
        .btn { background: #ccc; border: 1px solid #999; padding: 10px 20px; cursor: pointer; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .results { margin-top: 20px; display: none; }
        .results.show { display: block; }
        .stats { margin-bottom: 20px; }
        .stat-card { display: inline-block; margin: 5px; padding: 10px; border: 1px solid #ccc; }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .data-table th, .data-table td { border: 1px solid #ccc; padding: 5px; text-align: left; }
        .data-table th { background: #f0f0f0; }
        .loading { text-align: center; padding: 20px; }
        .error { color: red; margin: 10px 0; }
        .success { color: green; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Sitemap Priority System</h1>
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
            <button type="submit" class="btn" id="submitBtn">Process Data</button>
        </form>
    </div>
    <div id="loading" class="loading" style="display: none;">
        <h3>Processing your data...</h3>
        <p>This may take a few moments.</p>
    </div>
    <div id="error" class="error" style="display: none;"></div>
    <div id="success" class="success" style="display: none;"></div>
            <div id="results" class="results">
            <h2>Processing Results</h2>
            <div class="stats">
                <div class="stat-card"><div id="gscCount">0</div><div>GSC URLs</div></div>
                <div class="stat-card"><div id="peCount">0</div><div>Page Explorer URLs</div></div>
                <div class="stat-card"><div id="mergedCount">0</div><div>Merged URLs</div></div>
                <div class="stat-card"><div id="avgPriority">0.00</div><div>Avg Priority</div></div>
            </div>
            
            <div id="clusterStats" class="cluster-stats" style="margin: 20px 0; display: none;">
                <h3>Cluster Statistics</h3>
                <div id="clusterStatsContent"></div>
            </div>
            
            <div id="sitemapDownloads" class="sitemap-downloads" style="margin: 20px 0; display: none;">
                <h3>Generated Sitemaps</h3>
                <div id="sitemapDownloadsContent"></div>
            </div>
            
            <h3>Sample Data (Top 10 URLs)</h3>
            <table class="data-table">
                <thead><tr><th>URL</th><th>Priority</th><th>Cluster</th><th>Clicks</th><th>Impressions</th><th>CTR</th><th>Position</th></tr></thead>
                <tbody id="dataTable"></tbody>
            </table>
            
            <div id="fullDataInfo" style="margin-top: 20px; display: none;">
                <p><strong>Full Data:</strong> <span id="totalUrls">0</span> URLs processed. Download the sitemap files above to get the complete dataset.</p>
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
            
            showLoading(true);
            hideError();
            hideSuccess();
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    body: formData
                });
                
                let result;
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/json')) {
                    result = await response.json();
                } else {
                    const text = await response.text();
                    showError('Server returned non-JSON response: ' + text.substring(0, 200));
                    return;
                }
                
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
            document.getElementById('gscCount').textContent = data.gsc_urls || 0;
            document.getElementById('peCount').textContent = data.pe_urls || 0;
            document.getElementById('mergedCount').textContent = data.merged_urls || 0;
            
            const avgPriority = data.sample_data && data.sample_data.length > 0 
                ? (data.sample_data.reduce((sum, item) => sum + item.priority, 0) / data.sample_data.length).toFixed(3)
                : '0.000';
            document.getElementById('avgPriority').textContent = avgPriority;
            
            // Display cluster statistics
            if (data.cluster_stats) {
                const clusterStatsDiv = document.getElementById('clusterStatsContent');
                clusterStatsDiv.innerHTML = '';
                
                Object.entries(data.cluster_stats).forEach(([cluster, stats]) => {
                    const clusterDiv = document.createElement('div');
                    clusterDiv.style.cssText = 'display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ccc; background: #f9f9f9;';
                    clusterDiv.innerHTML = `
                        <div><strong>${cluster.toUpperCase()}</strong></div>
                        <div>URLs: ${stats.count}</div>
                        <div>Avg Priority: ${stats.avg_priority}</div>
                        <div>Top Priority: ${stats.top_priority.toFixed(3)}</div>
                    `;
                    clusterStatsDiv.appendChild(clusterDiv);
                });
                document.getElementById('clusterStats').style.display = 'block';
            }
            
            // Display sitemap downloads
            if (data.sitemap_content) {
                const downloadsDiv = document.getElementById('sitemapDownloadsContent');
                downloadsDiv.innerHTML = '';
                
                Object.entries(data.sitemap_content).forEach(([filename, xmlContent]) => {
                    const downloadDiv = document.createElement('div');
                    downloadDiv.style.cssText = 'margin: 10px 0; padding: 10px; border: 1px solid #ccc; background: #f0f0f0;';
                    
                    const downloadBtn = document.createElement('button');
                    downloadBtn.textContent = `Download ${filename}`;
                    downloadBtn.style.cssText = 'background: #007cba; color: white; border: none; padding: 8px 16px; cursor: pointer; margin-right: 10px;';
                    downloadBtn.onclick = () => downloadSitemap(filename, xmlContent);
                    
                    const sizeSpan = document.createElement('span');
                    sizeSpan.textContent = `Size: ${(xmlContent.length / 1024).toFixed(1)} KB`;
                    sizeSpan.style.cssText = 'color: #666; font-size: 0.9em;';
                    
                    downloadDiv.appendChild(downloadBtn);
                    downloadDiv.appendChild(sizeSpan);
                    downloadsDiv.appendChild(downloadDiv);
                });
                document.getElementById('sitemapDownloads').style.display = 'block';
            }
            
            // Display sample data table
            const tableBody = document.getElementById('dataTable');
            tableBody.innerHTML = '';
            if (data.sample_data && data.sample_data.length > 0) {
                data.sample_data.slice(0, 10).forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.url}</td>
                        <td>${item.priority.toFixed(3)}</td>
                        <td>${item.cluster}</td>
                        <td>${item.clicks || 0}</td>
                        <td>${item.impressions || 0}</td>
                        <td>${(item.ctr || 0).toFixed(3)}</td>
                        <td>${item.position || 0}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
            
            // Show full data info
            if (data.full_data) {
                document.getElementById('totalUrls').textContent = data.full_data.length;
                document.getElementById('fullDataInfo').style.display = 'block';
            }
            
            document.getElementById('results').classList.add('show');
        }
        
        function downloadSitemap(filename, xmlContent) {
            const blob = new Blob([xmlContent], { type: 'application/xml' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        self.wfile.write(HTML_TEMPLATE.encode()) 