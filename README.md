# Sitemap Priority System

A modular, data-driven system for generating structured, priority-driven sitemaps from Google Search Console and Page Explorer data.

## Features

- **Data Integration**: Loads and merges GSC and Page Explorer data
- **Smart Priority Calculation**: Multi-factor priority scoring using performance metrics
- **Intelligent Clustering**: Automatically categorizes URLs into business-relevant clusters
- **Protocol Compliant**: Generates standard XML sitemaps and sitemap index
- **Production Ready**: Designed for deployment on Vercel with API endpoints

## Quick Start

### Prerequisites

- Python 3.8+
- Google Search Console data (CSV)
- Page Explorer data (CSV)

### Installation

```bash
git clone <your-repo-url>
cd namesilo-sitemaps
pip install -r requirements.txt
```

### Usage

```bash
python test/pyscripts/sitemap_priority_system.py
```

## Data Format

### Google Search Console CSV
Expected columns: `url`, `clicks`, `impressions`, `ctr`, `position`

### Page Explorer CSV  
Expected columns: `url`, `importance`, `depth`, `internal_links`, `health`

## Output

- Individual XML sitemaps for each cluster (blog, support, TLDs, tools, SEO, misc)
- Sitemap index file referencing all cluster sitemaps
- Priority scores based on GSC performance + Page Explorer metrics

## Deployment

### Vercel Setup

1. Connect your GitHub repository to Vercel
2. Configure build settings for Python
3. Set environment variables if needed
4. Deploy!

### API Endpoints (Future)

- `GET /api/sitemaps` - List all sitemaps
- `POST /api/generate` - Generate new sitemaps from uploaded data
- `GET /api/health` - Health check

## Architecture

```
├── test/
│   ├── pyscripts/
│   │   └── sitemap_priority_system.py  # Main system
│   ├── blog-sitemap.xml               # Generated sitemaps
│   ├── support-sitemap.xml
│   ├── tlds-sitemap.xml
│   └── sitemap.xml                    # Sitemap index
├── requirements.txt
├── vercel.json                        # Vercel configuration
└── README.md
```

## Priority Calculation

The system calculates composite priority using:

1. **GSC Metrics** (40%): clicks, impressions, CTR, position
2. **Page Explorer Metrics** (40%): importance, depth, internal links, health  
3. **Business Logic** (20%): homepage boost, TLD priority, etc.

## Clustering Logic

- **Blog**: URLs containing `/blog/`
- **Support**: URLs containing `/support/`
- **TLDs**: URLs matching `/tld/` or `/domains/`
- **Tools**: URLs containing `/whois`, `/ssl-check`, `/dns-check`
- **SEO**: URLs containing `/domain-`, `/broker`, `/marketplace`
- **Misc**: All other URLs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details 