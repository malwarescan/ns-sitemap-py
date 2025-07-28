#!/usr/bin/env python3
"""
Test script for the Sitemap Priority System
Demonstrates the system with sample data and shows the priority calculation logic.
"""

import os
import tempfile
import csv
from sitemap_priority_system import (
    load_gsc_data,
    load_page_explorer_data,
    merge_and_deduplicate,
    calculate_priority,
    assign_cluster,
    cluster_urls,
    write_xml_sitemap,
    write_sitemap_index,
    main as main_function
)

def create_sample_gsc_data():
    """Create sample Google Search Console data."""
    return [
        {
            'url': 'https://www.namesilo.com/',
            'clicks': 1500,
            'impressions': 5000,
            'ctr': 0.30,
            'position': 1.5
        },
        {
            'url': 'https://www.namesilo.com/blog/domain-names-guide',
            'clicks': 800,
            'impressions': 2000,
            'ctr': 0.40,
            'position': 2.1
        },
        {
            'url': 'https://www.namesilo.com/support/transfer-domain',
            'clicks': 300,
            'impressions': 800,
            'ctr': 0.375,
            'position': 3.2
        },
        {
            'url': 'https://www.namesilo.com/tld/com',
            'clicks': 1200,
            'impressions': 3000,
            'ctr': 0.40,
            'position': 1.8
        },
        {
            'url': 'https://www.namesilo.com/whois',
            'clicks': 200,
            'impressions': 500,
            'ctr': 0.40,
            'position': 4.5
        },
        {
            'url': 'https://www.namesilo.com/domain-broker',
            'clicks': 150,
            'impressions': 400,
            'ctr': 0.375,
            'position': 5.2
        }
    ]

def create_sample_pe_data():
    """Create sample Page Explorer data."""
    return [
        {
            'url': 'https://www.namesilo.com/',
            'importance': 95,
            'depth': 1,
            'internal_links': 150,
            'health': 98
        },
        {
            'url': 'https://www.namesilo.com/blog/domain-names-guide',
            'importance': 85,
            'depth': 3,
            'internal_links': 45,
            'health': 92
        },
        {
            'url': 'https://www.namesilo.com/support/transfer-domain',
            'importance': 75,
            'depth': 4,
            'internal_links': 30,
            'health': 88
        },
        {
            'url': 'https://www.namesilo.com/tld/com',
            'importance': 90,
            'depth': 2,
            'internal_links': 80,
            'health': 95
        },
        {
            'url': 'https://www.namesilo.com/whois',
            'importance': 70,
            'depth': 3,
            'internal_links': 25,
            'health': 85
        },
        {
            'url': 'https://www.namesilo.com/domain-broker',
            'importance': 80,
            'depth': 2,
            'internal_links': 60,
            'health': 90
        }
    ]

def save_sample_data_to_csv(data, filename):
    """Save sample data to CSV file."""
    if not data:
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def test_priority_calculation():
    """Test the priority calculation with sample data."""
    print("=== Testing Priority Calculation ===")
    
    # Create sample data
    gsc_data = create_sample_gsc_data()
    pe_data = create_sample_pe_data()
    
    # Merge data
    merged = merge_and_deduplicate(gsc_data, pe_data)
    
    # Calculate priorities
    for entry in merged:
        priority = calculate_priority(entry)
        entry['calculated_priority'] = priority
        print(f"URL: {entry['url']}")
        print(f"  GSC: clicks={entry.get('clicks', 0)}, ctr={entry.get('ctr', 0):.3f}, position={entry.get('position', 0)}")
        print(f"  PE: importance={entry.get('importance', 0)}, depth={entry.get('depth', 0)}, links={entry.get('internal_links', 0)}")
        print(f"  Calculated Priority: {priority:.3f}")
        print()

def test_clustering():
    """Test the clustering logic."""
    print("=== Testing URL Clustering ===")
    
    # Create sample data
    gsc_data = create_sample_gsc_data()
    pe_data = create_sample_pe_data()
    merged = merge_and_deduplicate(gsc_data, pe_data)
    
    # Calculate priorities
    for entry in merged:
        entry['priority'] = calculate_priority(entry)
    
    # Cluster URLs
    clusters = cluster_urls(merged)
    
    for cluster_name, urls_in_cluster in clusters.items():
        print(f"\nCluster: {cluster_name}")
        print(f"  URLs: {len(urls_in_cluster)}")
        for url_entry in urls_in_cluster:
            url = url_entry['url']
            priority = url_entry['priority']
            print(f"    {url} (priority: {priority:.3f})")

def test_full_pipeline():
    """Test the full pipeline with sample data."""
    print("=== Testing Full Pipeline ===")
    
    # Create temporary files for sample data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as gsc_temp:
        gsc_data = create_sample_gsc_data()
        save_sample_data_to_csv(gsc_data, gsc_temp.name)
        gsc_path = gsc_temp.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as pe_temp:
        pe_data = create_sample_pe_data()
        save_sample_data_to_csv(pe_data, pe_temp.name)
        pe_path = pe_temp.name
    
    # Create output directory
    output_dir = 'test-output'
    
    try:
        # Run the full pipeline
        main_function(gsc_path, pe_path, output_dir)
        
        # List generated files
        print(f"\nGenerated files in {output_dir}:")
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.endswith('.xml'):
                    file_path = os.path.join(output_dir, file)
                    size = os.path.getsize(file_path)
                    print(f"  {file} ({size} bytes)")
    
    finally:
        # Clean up temporary files
        os.unlink(gsc_path)
        os.unlink(pe_path)

def main_test():
    """Run all tests."""
    print("Sitemap Priority System - Test Suite")
    print("=" * 50)
    
    # Test individual components
    test_priority_calculation()
    test_clustering()
    
    # Test full pipeline
    test_full_pipeline()
    
    print("\nTest suite completed!")

if __name__ == "__main__":
    main_test() 