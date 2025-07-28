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
    
    def do_POST(self):
        """Test POST endpoint with sample data"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Return sample processed data
        sample_result = {
            "message": "Test data processed successfully",
            "gsc_urls": 50,
            "pe_urls": 75,
            "merged_urls": 100,
            "timestamp": datetime.now().isoformat(),
            "cluster_stats": {
                "blog": {"count": 20, "avg_priority": 0.75, "top_priority": 0.95},
                "support": {"count": 15, "avg_priority": 0.65, "top_priority": 0.85},
                "tlds": {"count": 30, "avg_priority": 0.90, "top_priority": 1.0},
                "tools": {"count": 10, "avg_priority": 0.70, "top_priority": 0.88},
                "seo": {"count": 15, "avg_priority": 0.80, "top_priority": 0.92},
                "misc": {"count": 10, "avg_priority": 0.50, "top_priority": 0.75}
            },
            "sitemaps_created": ["blog-sitemap.xml", "support-sitemap.xml", "tlds-sitemap.xml", "tools-sitemap.xml", "seo-sitemap.xml", "misc-sitemap.xml", "sitemap-index.xml"],
            "sample_data": [
                {"url": "https://example.com", "priority": 0.95, "cluster": "tlds", "clicks": 500, "impressions": 5000, "ctr": 0.1, "position": 1.0},
                {"url": "https://example.com/blog", "priority": 0.85, "cluster": "blog", "clicks": 200, "impressions": 2000, "ctr": 0.1, "position": 2.0},
                {"url": "https://example.com/support", "priority": 0.75, "cluster": "support", "clicks": 100, "impressions": 1000, "ctr": 0.1, "position": 3.0}
            ],
            "full_data": [
                {"url": "https://example.com", "priority": 0.95, "cluster": "tlds", "clicks": 500, "impressions": 5000, "ctr": 0.1, "position": 1.0},
                {"url": "https://example.com/blog", "priority": 0.85, "cluster": "blog", "clicks": 200, "impressions": 2000, "ctr": 0.1, "position": 2.0},
                {"url": "https://example.com/support", "priority": 0.75, "cluster": "support", "clicks": 100, "impressions": 1000, "ctr": 0.1, "position": 3.0}
            ],
            "sitemap_content": {
                "blog-sitemap.xml": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n  <url>\n    <loc>https://example.com/blog</loc>\n    <lastmod>2025-01-28T12:00:00+00:00</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8500</priority>\n  </url>\n</urlset>",
                "sitemap-index.xml": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<sitemapindex xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n  <sitemap>\n    <loc>https://your-domain.com/blog-sitemap.xml</loc>\n    <lastmod>2025-01-28T12:00:00+00:00</lastmod>\n  </sitemap>\n</sitemapindex>"
            }
        }
        
        self.wfile.write(json.dumps(sample_result).encode()) 