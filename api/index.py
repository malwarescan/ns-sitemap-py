from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import tempfile
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our sitemap system
from test.pyscripts.sitemap_priority_system import (
    load_gsc_data, 
    load_page_explorer_data, 
    merge_and_deduplicate
)

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    """Home page with API documentation."""
    return jsonify({
        "message": "Sitemap Priority System API",
        "version": "1.0.0",
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
        "version": "1.0.0"
    })

@app.route('/api/sitemaps')
def list_sitemaps():
    """List all available sitemaps."""
    sitemap_dir = os.path.join(os.path.dirname(__file__), '..', 'test')
    sitemaps = []
    
    if os.path.exists(sitemap_dir):
        for file in os.listdir(sitemap_dir):
            if file.endswith('.xml') and 'sitemap' in file.lower():
                file_path = os.path.join(sitemap_dir, file)
                sitemaps.append({
                    "name": file,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
    
    return jsonify({
        "sitemaps": sitemaps,
        "count": len(sitemaps)
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
        
        # Process the data
        gsc_data = load_gsc_data(gsc_path)
        pe_data = load_page_explorer_data(pe_path)
        merged_data = merge_and_deduplicate(gsc_data, pe_data)
        
        # Clean up temporary files
        os.unlink(gsc_path)
        os.unlink(pe_path)
        
        return jsonify({
            "message": "Sitemaps generated successfully",
            "gsc_urls": len(gsc_data),
            "pe_urls": len(pe_data),
            "merged_urls": len(merged_data),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<sitemap_name>')
def download_sitemap(sitemap_name):
    """Download a specific sitemap file."""
    sitemap_dir = os.path.join(os.path.dirname(__file__), '..', 'test')
    sitemap_path = os.path.join(sitemap_dir, sitemap_name)
    
    if not os.path.exists(sitemap_path):
        return jsonify({"error": "Sitemap not found"}), 404
    
    return send_file(sitemap_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True) 