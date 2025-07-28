from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "deployment": "vercel",
            "endpoints": {
                "/api/health": "Health check",
                "/api/test": "Test endpoint",
                "/api/generate": "Generate sitemaps"
            }
        }
        
        self.wfile.write(json.dumps(response).encode()) 