# Sitemap Priority System - Complete Documentation

## Overview

The Sitemap Priority System is a modular, data-driven solution for generating structured, priority-driven sitemaps from Google Search Console (GSC) and Page Explorer data. It implements best practices for traditional, semantic, and agentic SEO optimization.

## Key Features

### 🎯 **Smart Priority Calculation**
- **Multi-factor scoring**: Combines GSC performance metrics (40%), Page Explorer data (40%), and business logic (20%)
- **Performance-based**: Uses actual clicks, impressions, CTR, and position data
- **Content-aware**: Considers page importance, depth, internal links, and health scores
- **Business-driven**: Applies domain registrar-specific logic (homepage boost, TLD priority, etc.)

### 🏗️ **Intelligent Clustering**
- **Semantic organization**: Groups URLs by content type and business function
- **6 specialized clusters**: blog, support, TLDs, tools, SEO, misc
- **Automatic categorization**: Uses regex patterns and business rules
- **Priority sorting**: Each cluster sorted by calculated priority (highest first)

### 📊 **Data Integration**
- **GSC data**: clicks, impressions, CTR, position
- **Page Explorer data**: importance, depth, internal links, health
- **Automatic deduplication**: Normalizes URLs and merges metrics
- **Flexible input**: Supports CSV format with configurable column names

### 🚀 **Production Ready**
- **Vercel deployment**: Full API endpoints for web service
- **Protocol compliant**: Generates standard XML sitemaps and sitemap index
- **Scalable architecture**: Modular design for easy extension
- **Comprehensive testing**: Test suite with sample data

## Architecture

```
├── test/pyscripts/
│   ├── sitemap_priority_system.py    # Core system
│   └── test_priority_system.py       # Test suite
├── api/
│   └── index.py                      # Vercel API endpoints
├── requirements.txt                  # Python dependencies
├── vercel.json                      # Vercel configuration
└── README.md                        # Project overview
```

## Priority Calculation Algorithm

### Formula Breakdown

**Final Priority = (GSC Score × 0.4) + (Page Explorer Score × 0.4) + (Business Logic Score × 0.2)**

#### 1. GSC Performance Score (40% weight)
- **Click Rate** (30%): `clicks / impressions` - Higher is better
- **CTR** (30%): Click-through rate - Higher is better  
- **Position** (40%): `1 - (position / 100)` - Lower position is better

#### 2. Page Explorer Score (40% weight)
- **Importance** (40%): `importance / 100` - Higher is better
- **Depth** (20%): `1 - (depth / 10)` - Shallow pages are better
- **Internal Links** (20%): `min(links / 100, 1)` - More links = better
- **Health** (20%): `health / 100` - Higher is better

#### 3. Business Logic Score (20% weight)
- **Homepage boost**: +0.5 for homepage URLs
- **TLD pages**: +0.3 for TLD-specific pages
- **Blog content**: +0.2 for blog URLs
- **Support content**: +0.1 for support URLs
- **Tools**: +0.2 for utility tools

## Clustering Logic

### Cluster Categories

| Cluster | Pattern | Priority | Change Freq | Description |
|---------|---------|----------|-------------|-------------|
| **blog** | `/blog/` | 0.8 | weekly | Blog articles and content |
| **support** | `/support/`, `/help/` | 0.6 | weekly | Support articles and help |
| **tlds** | `/tld/`, `/domains/[tld]` | 0.9 | monthly | TLD-specific pages |
| **tools** | `/whois`, `/ssl-check`, `/dns-check` | 0.7 | monthly | Utility tools |
| **seo** | `/domain-`, `/broker`, `/marketplace` | 1.0 | monthly | SEO/service pages |
| **misc** | `.*` | 0.5 | monthly | Everything else |

## Usage Examples

### Basic Usage

```python
from sitemap_priority_system import main

# Generate sitemaps from CSV data
main(
    gsc_path="gsc-pages.csv",
    pe_path="page_explorer_data.csv", 
    output_dir="sitemaps-output/"
)
```

### API Usage (Vercel)

```bash
# Health check
curl https://your-project.vercel.app/api/health

# List available sitemaps
curl https://your-project.vercel.app/api/sitemaps

# Generate new sitemaps (POST with CSV files)
curl -X POST https://your-project.vercel.app/api/generate \
  -F "gsc_data=@gsc-pages.csv" \
  -F "pe_data=@page_explorer_data.csv"

# Download specific sitemap
curl https://your-project.vercel.app/api/download/blog-sitemap.xml
```

## Data Format Requirements

### Google Search Console CSV
```csv
url,clicks,impressions,ctr,position
https://www.namesilo.com/,1500,5000,0.30,1.5
https://www.namesilo.com/blog/guide,800,2000,0.40,2.1
```

### Page Explorer CSV
```csv
url,importance,depth,internal_links,health
https://www.namesilo.com/,95,1,150,98
https://www.namesilo.com/blog/guide,85,3,45,92
```

## Output Structure

### Generated Files
```
sitemaps-output/
├── blog-sitemap.xml          # Blog content (weekly updates)
├── support-sitemap.xml       # Support articles (weekly updates)  
├── tlds-sitemap.xml          # TLD pages (monthly updates)
├── tools-sitemap.xml         # Utility tools (monthly updates)
├── seo-sitemap.xml           # SEO/service pages (monthly updates)
├── misc-sitemap.xml          # Miscellaneous content (monthly updates)
└── sitemap-index.xml         # Master sitemap index
```

### XML Structure
```xml
<?xml version="1.0" ?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.namesilo.com/blog/domain-guide</loc>
    <lastmod>2025-07-28</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.59</priority>
  </url>
</urlset>
```

## Deployment

### Vercel Setup
1. **Connect Repository**: Link your GitHub repo to Vercel
2. **Auto-detect**: Vercel detects Python project automatically
3. **Deploy**: Automatic deployment on every push
4. **API Endpoints**: Available at `https://your-project.vercel.app/api/*`

### Environment Variables
- No required environment variables for basic functionality
- Optional: Add API keys for enhanced features

## Testing

### Run Test Suite
```bash
cd test/pyscripts
python3 test_priority_system.py
```

### Test Output
```
Sitemap Priority System - Test Suite
==================================================
=== Testing Priority Calculation ===
URL: https://www.namesilo.com/
  GSC: clicks=1500, ctr=0.300, position=1.5
  PE: importance=95, depth=1, links=150
  Calculated Priority: 0.712

=== Testing URL Clustering ===
Cluster: blog
  URLs: 1
    https://www.namesilo.com/blog/domain-names-guide (priority: 0.594)

=== Testing Full Pipeline ===
Starting Sitemap Priority System...
Loaded 6 GSC URLs
Loaded 6 Page Explorer URLs
Merged into 6 unique URLs
Complete! Generated 6 sitemaps in test-output
```

## Performance Metrics

### Priority Distribution Example
- **Homepage**: 0.712 (highest - homepage + high GSC performance)
- **TLD pages**: 0.661 (high - TLD boost + good metrics)
- **Blog content**: 0.594 (medium - good content metrics)
- **Tools**: 0.545 (medium - utility boost)
- **Support**: 0.527 (lower - deeper content)
- **SEO pages**: 0.554 (medium - service page boost)

### Scalability
- **Input**: Handles thousands of URLs efficiently
- **Output**: Generates multiple specialized sitemaps
- **Memory**: Optimized for large datasets
- **Speed**: Fast processing with minimal overhead

## Best Practices

### Data Quality
- **Clean URLs**: Ensure URLs are properly formatted
- **Complete data**: Fill missing values with defaults
- **Regular updates**: Refresh GSC and Page Explorer data monthly
- **Validation**: Verify CSV format before processing

### SEO Optimization
- **Priority accuracy**: Use real performance data
- **Content clustering**: Group related content logically
- **Update frequency**: Match changefreq to content update schedule
- **Index submission**: Submit sitemap index to search engines

### Maintenance
- **Version control**: Track changes in Git
- **Testing**: Run test suite before deployment
- **Monitoring**: Check API health endpoints
- **Documentation**: Keep this documentation updated

## Future Enhancements

### Planned Features
- **Real-time updates**: Webhook integration for live data
- **Advanced filtering**: More sophisticated URL filtering rules
- **Custom clustering**: User-defined cluster categories
- **Analytics dashboard**: Visual priority and performance metrics
- **Multi-language support**: International sitemap generation

### API Extensions
- **Bulk processing**: Handle multiple datasets
- **Scheduling**: Automated sitemap generation
- **Notifications**: Email alerts for new sitemaps
- **Integration**: Connect with other SEO tools

## Support

### Troubleshooting
- **Import errors**: Check Python version (3.8+ required)
- **Data issues**: Verify CSV format and column names
- **Deployment problems**: Check Vercel logs and configuration
- **Performance issues**: Monitor memory usage with large datasets

### Resources
- **Documentation**: This file and README.md
- **Code examples**: Test suite in `test_priority_system.py`
- **API reference**: Vercel API endpoints documentation
- **Community**: GitHub issues and discussions

---

**Version**: 1.0.0  
**Last Updated**: 2025-07-28  
**Maintainer**: Sitemap Priority System Team 