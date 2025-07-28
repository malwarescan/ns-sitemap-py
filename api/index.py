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
        .tabs { margin: 20px 0; }
        .tab-buttons { border-bottom: 1px solid #ccc; margin-bottom: 20px; }
        .tab-button { 
            background: #f0f0f0; 
            border: 1px solid #ccc; 
            border-bottom: none; 
            padding: 10px 20px; 
            cursor: pointer; 
            margin-right: 5px; 
        }
        .tab-button.active { 
            background: white; 
            border-bottom: 1px solid white; 
            margin-bottom: -1px; 
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .url-structure { 
            max-height: 400px; 
            overflow-y: auto; 
            border: 1px solid #ccc; 
            padding: 10px; 
            background: #f9f9f9; 
        }
        .cluster-section { margin-bottom: 20px; }
        .cluster-header { 
            background: #e0e0e0; 
            padding: 8px; 
            font-weight: bold; 
            margin-bottom: 10px; 
        }
        .url-item { 
            padding: 5px 10px; 
            border-bottom: 1px solid #eee; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .url-item:hover { background: #f0f0f0; }
        .url-text { flex: 1; }
        .url-priority { 
            background: #007cba; 
            color: white; 
            padding: 2px 8px; 
            border-radius: 3px; 
            font-size: 0.8em; 
        }
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
                        <div class="file-input">
                            <label for="competitorUrl">Competitor Sitemap URL (Optional)</label>
                            <input type="url" id="competitorUrl" name="competitor_url" placeholder="https://competitor.com/sitemap.xml">
                            <small style="color: #666;">Enter a competitor's sitemap URL to automatically fetch and analyze their structure</small>
                        </div>
                        <button type="submit" class="btn" id="submitBtn">Process Data</button>
                        <button type="button" class="btn" id="testBtn" onclick="testAPI()" style="margin-left: 10px; background: #28a745;">Test API</button>
                    </form>
                </div>
    <div id="loading" class="loading" style="display: none;">
        <h3>Processing your data...</h3>
        <p>This may take a few moments.</p>
        <div id="statusIndicator" style="margin-top: 10px; font-size: 0.9em; color: #666;"></div>
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
            
                            <div class="tabs">
                    <div class="tab-buttons">
                        <button class="tab-button active" onclick="showTab('sample')">Sample Data</button>
                        <button class="tab-button" onclick="showTab('structure')">URL Structure</button>
                        <button class="tab-button" onclick="showTab('competitor')">Competitor Analysis</button>
                    </div>
                
                <div id="sampleTab" class="tab-content active">
                    <h3>Sample Data (Top 10 URLs)</h3>
                    <table class="data-table">
                        <thead><tr><th>URL</th><th>Priority</th><th>Cluster</th><th>Clicks</th><th>Impressions</th><th>CTR</th><th>Position</th></tr></thead>
                        <tbody id="dataTable"></tbody>
                    </table>
                </div>
                
                <div id="structureTab" class="tab-content">
                    <h3>URL Structure Preview</h3>
                    <div class="url-structure" id="urlStructure"></div>
                </div>
                
                <div id="competitorTab" class="tab-content">
                    <h3>Competitor Analysis</h3>
                    <div id="competitorAnalysis">
                        <p>Upload a competitor's sitemap to see analysis and optimization recommendations.</p>
                    </div>
                </div>
            </div>
            
            <div id="fullDataInfo" style="margin-top: 20px; display: none;">
                <p><strong>Full Data:</strong> <span id="totalUrls">0</span> URLs processed. Download the sitemap files above to get the complete dataset.</p>
            </div>
        </div>
    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            console.log('Form submitted - starting processing...');
            
            const formData = new FormData();
            const gscFile = document.getElementById('gscFile').files[0];
            const peFile = document.getElementById('peFile').files[0];
            const competitorUrl = document.getElementById('competitorUrl').value.trim();
            
            console.log('Files selected:', {
                gscFile: gscFile ? gscFile.name : 'none',
                peFile: peFile ? peFile.name : 'none',
                competitorUrl: competitorUrl || 'none'
            });
            
            if (!gscFile || !peFile) {
                showError('Please select both CSV files');
                console.log('Error: Missing required files');
                return;
            }
            
            formData.append('gsc_data', gscFile);
            formData.append('pe_data', peFile);
            
            if (competitorUrl) {
                formData.append('competitor_url', competitorUrl);
            }
            
            showLoading(true);
            hideError();
            hideSuccess();
            
            updateStatus('Preparing data...');
            console.log('Sending request to /api/generate...');
            
            try {
                updateStatus('Sending request to server...');
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    body: formData
                });
                
                updateStatus('Processing response...');
                console.log('Response received:', {
                    status: response.status,
                    statusText: response.statusText,
                    contentType: response.headers.get('content-type')
                });
                
                let result;
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/json')) {
                    result = await response.json();
                    console.log('JSON response:', result);
                } else {
                    const text = await response.text();
                    console.log('Non-JSON response:', text.substring(0, 500));
                    showError('Server returned non-JSON response: ' + text.substring(0, 200));
                    return;
                }
                
                if (response.ok) {
                    console.log('Success - displaying results');
                    showSuccess(result.message);
                    displayResults(result);
                } else {
                    console.log('Error response:', result);
                    showError(result.error || 'An error occurred');
                }
            } catch (error) {
                console.error('Network error:', error);
                showError('Network error: ' + error.message);
            } finally {
                showLoading(false);
                console.log('Processing completed');
            }
        });
        
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
            document.getElementById('submitBtn').disabled = show;
        }
        
        function updateStatus(message) {
            const statusDiv = document.getElementById('statusIndicator');
            if (statusDiv) {
                statusDiv.textContent = message;
            }
            console.log('Status:', message);
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
                
                // Display URL structure in the preview tab
                displayUrlStructure(data.full_data);
            }
            
            // Display competitor analysis if available
            if (data.competitor_analysis) {
                displayCompetitorAnalysis(data.competitor_analysis);
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
        
        async function testAPI() {
            showLoading(true);
            hideError();
            hideSuccess();
            
            try {
                const response = await fetch('/api/test', {
                    method: 'POST'
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
                    showSuccess('Test successful! Sample data loaded.');
                    displayResults(result);
                } else {
                    showError(result.error || 'Test failed');
                }
            } catch (error) {
                showError('Test error: ' + error.message);
            } finally {
                showLoading(false);
            }
        }
        
        function showTab(tabName) {
            // Hide all tab contents
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Remove active class from all tab buttons
            const tabButtons = document.querySelectorAll('.tab-button');
            tabButtons.forEach(button => button.classList.remove('active'));
            
            // Show selected tab content
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            // Add active class to clicked button
            event.target.classList.add('active');
        }
        
        function displayUrlStructure(fullData) {
            if (!fullData || fullData.length === 0) return;
            
            // Group URLs by cluster
            const clusters = {};
            fullData.forEach(item => {
                if (!clusters[item.cluster]) {
                    clusters[item.cluster] = [];
                }
                clusters[item.cluster].push(item);
            });
            
            const structureDiv = document.getElementById('urlStructure');
            structureDiv.innerHTML = '';
            
            // Sort clusters by priority (highest average priority first)
            const sortedClusters = Object.entries(clusters).sort((a, b) => {
                const avgA = a[1].reduce((sum, item) => sum + item.priority, 0) / a[1].length;
                const avgB = b[1].reduce((sum, item) => sum + item.priority, 0) / b[1].length;
                return avgB - avgA;
            });
            
            sortedClusters.forEach(([clusterName, clusterUrls]) => {
                const clusterSection = document.createElement('div');
                clusterSection.className = 'cluster-section';
                
                const clusterHeader = document.createElement('div');
                clusterHeader.className = 'cluster-header';
                const avgPriority = clusterUrls.reduce((sum, item) => sum + item.priority, 0) / clusterUrls.length;
                clusterHeader.innerHTML = `
                    ${clusterName.toUpperCase()} (${clusterUrls.length} URLs, Avg Priority: ${avgPriority.toFixed(3)})
                `;
                
                clusterSection.appendChild(clusterHeader);
                
                // Sort URLs within cluster by priority
                clusterUrls.sort((a, b) => b.priority - a.priority);
                
                clusterUrls.forEach(urlItem => {
                    const urlDiv = document.createElement('div');
                    urlDiv.className = 'url-item';
                    
                    const urlText = document.createElement('div');
                    urlText.className = 'url-text';
                    urlText.textContent = urlItem.url;
                    
                    const prioritySpan = document.createElement('span');
                    prioritySpan.className = 'url-priority';
                    prioritySpan.textContent = urlItem.priority.toFixed(3);
                    
                    urlDiv.appendChild(urlText);
                    urlDiv.appendChild(prioritySpan);
                    clusterSection.appendChild(urlDiv);
                });
                
                structureDiv.appendChild(clusterSection);
            });
        }
        
        function displayCompetitorAnalysis(analysis) {
            const analysisDiv = document.getElementById('competitorAnalysis');
            analysisDiv.innerHTML = '';
            
            // Competitor Overview
            const overviewDiv = document.createElement('div');
            overviewDiv.style.cssText = 'margin-bottom: 20px; padding: 15px; background: #f0f8ff; border: 1px solid #007cba;';
            overviewDiv.innerHTML = `
                <h4>Competitor Overview</h4>
                <p><strong>Total URLs:</strong> ${analysis.total_urls}</p>
                <p><strong>Average Priority:</strong> ${analysis.avg_priority.toFixed(3)}</p>
                <p><strong>Content Categories:</strong> ${analysis.categories.join(', ')}</p>
                <p><strong>Update Frequency:</strong> ${analysis.update_frequency}</p>
            `;
            analysisDiv.appendChild(overviewDiv);
            
            // Strategy Insights
            const insightsDiv = document.createElement('div');
            insightsDiv.style.cssText = 'margin-bottom: 20px; padding: 15px; background: #fff3cd; border: 1px solid #ffc107;';
            insightsDiv.innerHTML = `
                <h4>Strategy Insights</h4>
                <ul>
                    ${analysis.insights.map(insight => `<li>${insight}</li>`).join('')}
                </ul>
            `;
            analysisDiv.appendChild(insightsDiv);
            
            // Optimization Recommendations
            const recommendationsDiv = document.createElement('div');
            recommendationsDiv.style.cssText = 'margin-bottom: 20px; padding: 15px; background: #d1ecf1; border: 1px solid #17a2b8;';
            recommendationsDiv.innerHTML = `
                <h4>Optimization Recommendations</h4>
                <ul>
                    ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            `;
            recommendationsDiv.appendChild(recommendationsDiv);
            
            // URL Structure Comparison
            if (analysis.url_structure) {
                const structureDiv = document.createElement('div');
                structureDiv.style.cssText = 'margin-bottom: 20px;';
                structureDiv.innerHTML = `
                    <h4>URL Structure Analysis</h4>
                    <div class="url-structure" style="max-height: 300px;">
                        ${analysis.url_structure.map(category => `
                            <div class="cluster-section">
                                <div class="cluster-header">${category.name} (${category.count} URLs)</div>
                                ${category.sample_urls.map(url => `
                                    <div class="url-item">
                                        <div class="url-text">${url}</div>
                                    </div>
                                `).join('')}
                            </div>
                        `).join('')}
                    </div>
                `;
                analysisDiv.appendChild(structureDiv);
            }
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