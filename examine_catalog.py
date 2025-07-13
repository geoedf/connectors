#!/usr/bin/env python3
"""
Examine the OpenDAP catalog.xml to understand how to discover individual files.
"""

import requests
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

def examine_catalog():
    """Examine the OpenDAP catalog to understand file discovery"""
    
    base_url = "https://opendap.cr.usgs.gov/opendap/hyrax/MOD13Q1.061"
    catalog_url = f"{base_url}/catalog.xml"
    
    print("=== Examining OpenDAP Catalog ===")
    print(f"Catalog URL: {catalog_url}")
    
    try:
        session = requests.Session()
        res = session.get(catalog_url, timeout=30)
        
        if res.status_code == 200:
            print("✓ Catalog accessible")
            print(f"Content-Type: {res.headers.get('Content-Type', 'Unknown')}")
            print()
            
            # Save and parse the XML
            catalog_content = res.text
            
            # Pretty print first part
            print("=== Catalog Content (first 2000 chars) ===")
            print(catalog_content[:2000])
            print("..." if len(catalog_content) > 2000 else "")
            print()
            
            # Try to parse as XML
            try:
                root = ET.fromstring(catalog_content)
                print("=== XML Structure Analysis ===")
                print(f"Root tag: {root.tag}")
                print(f"Root attributes: {root.attrib}")
                print()
                
                # Look for datasets or services
                datasets = root.findall('.//{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}dataset')
                services = root.findall('.//{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}service')
                
                print(f"Found {len(datasets)} datasets")
                print(f"Found {len(services)} services")
                print()
                
                # Examine services
                if services:
                    print("=== Services ===")
                    for service in services:
                        print(f"Service: {service.attrib}")
                    print()
                
                # Examine datasets (looking for ones with h10v04 and 2023)
                relevant_datasets = []
                for dataset in datasets:
                    name = dataset.get('name', '')
                    if 'h10v04' in name and '2023' in name:
                        relevant_datasets.append(dataset)
                
                print(f"=== Relevant Datasets (h10v04 + 2023): {len(relevant_datasets)} ===")
                for dataset in relevant_datasets[:10]:  # Show first 10
                    name = dataset.get('name', 'Unknown')
                    url_path = dataset.get('urlPath', 'No URL')
                    print(f"Name: {name}")
                    print(f"URL Path: {url_path}")
                    
                    # Check for access elements
                    access_elements = dataset.findall('.//{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}access')
                    for access in access_elements:
                        service_name = access.get('serviceName', 'Unknown')
                        url_path = access.get('urlPath', 'No URL')
                        print(f"  Access: {service_name} -> {url_path}")
                    print()
                    
                if not relevant_datasets:
                    print("No datasets found with h10v04 and 2023 in the name")
                    
                    # Show a few example datasets to understand the structure
                    print("=== Sample Datasets ===")
                    for dataset in datasets[:5]:
                        name = dataset.get('name', 'Unknown')
                        print(f"  {name}")
                
            except ET.ParseError as e:
                print(f"XML Parse Error: {e}")
                print("Content might not be valid XML")
                
        else:
            print(f"Failed to access catalog: {res.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_catalog()
