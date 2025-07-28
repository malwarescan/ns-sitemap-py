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
            "message": "API is working",
            "timestamp": datetime.now().isoformat(),
            "test_data": [
                {
                    "url": "https://example.com",
                    "priority": 0.85,
                    "cluster": "misc",
                    "clicks": 100,
                    "impressions": 1000,
                    "ctr": 0.1,
                    "position": 5.0
                }
            ]
        }
        
        self.wfile.write(json.dumps(response).encode()) 