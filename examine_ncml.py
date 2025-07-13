#!/usr/bin/env python3
"""
Examine an .ncml aggregation file to understand how individual files are referenced.
"""

import requests
import xml.etree.ElementTree as ET

def examine_ncml_file():
    """Examine a specific .ncml file to understand its structure"""
    
    base_url = "https://opendap.cr.usgs.gov/opendap/hyrax/MOD13Q1.061"
    ncml_file = "h10v04.ncml"  # This should be the tile we're interested in
    ncml_url = f"{base_url}/{ncml_file}"
    
    print("=== Examining .ncml Aggregation File ===")
    print(f"NCML URL: {ncml_url}")
    
    try:
        session = requests.Session()
        res = session.get(ncml_url, timeout=30)
        
        if res.status_code == 200:
            print("✓ NCML file accessible")
            print(f"Content-Type: {res.headers.get('Content-Type', 'Unknown')}")
            print(f"Content-Length: {res.headers.get('Content-Length', 'Unknown')}")
            print()
            
            ncml_content = res.text
            
            # Show first part of content
            print("=== NCML Content (first 3000 chars) ===")
            print(ncml_content[:3000])
            print("..." if len(ncml_content) > 3000 else "")
            print()
            
            # Try to parse as XML to find individual file references
            try:
                root = ET.fromstring(ncml_content)
                print("=== XML Structure Analysis ===")
                print(f"Root tag: {root.tag}")
                print(f"Root attributes: {root.attrib}")
                print()
                
                # Look for aggregation elements
                aggregations = root.findall('.//{http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2}aggregation')
                print(f"Found {len(aggregations)} aggregations")
                
                for agg in aggregations:
                    agg_type = agg.get('type', 'Unknown')
                    dim_name = agg.get('dimName', 'Unknown')
                    print(f"Aggregation type: {agg_type}, dimension: {dim_name}")
                    
                    # Look for netcdf elements (individual files)
                    netcdf_elements = agg.findall('.//{http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2}netcdf')
                    print(f"  Found {len(netcdf_elements)} netcdf elements (individual files)")
                    
                    # Show first few files
                    for i, netcdf in enumerate(netcdf_elements[:10]):
                        location = netcdf.get('location', 'No location')
                        coord_value = netcdf.get('coordValue', 'No coord')
                        print(f"    {i+1}: {location} (coord: {coord_value})")
                        
                        # Check if this contains 2023 data
                        if '2023' in location:
                            print(f"         *** Contains 2023 data! ***")
                    
                    if len(netcdf_elements) > 10:
                        print(f"    ... and {len(netcdf_elements) - 10} more files")
                        
                        # Look specifically for 2023 files
                        files_2023 = [nc for nc in netcdf_elements if '2023' in nc.get('location', '')]
                        print(f"    Files with 2023: {len(files_2023)}")
                        
                        for nc in files_2023[:5]:
                            location = nc.get('location', 'No location')
                            print(f"      2023 file: {location}")
                    
                    print()
                    
            except ET.ParseError as e:
                print(f"XML Parse Error: {e}")
                # Show raw content for debugging
                print("Raw content (first 1000 chars):")
                print(repr(ncml_content[:1000]))
                
        elif res.status_code == 404:
            print("✗ NCML file not found")
            print("Available tiles might be different. Let me check the catalog again...")
            
            # Get available .ncml files from catalog
            catalog_res = session.get(f"{base_url}/catalog.xml", timeout=30)
            if catalog_res.status_code == 200:
                root = ET.fromstring(catalog_res.text)
                datasets = root.findall('.//{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}dataset')
                
                ncml_files = []
                for dataset in datasets:
                    name = dataset.get('name', '')
                    if name.endswith('.ncml') and 'h' in name and 'v' in name:
                        ncml_files.append(name)
                
                print(f"Available .ncml files: {len(ncml_files)}")
                for f in sorted(ncml_files)[:20]:
                    print(f"  {f}")
                    
        else:
            print(f"Failed to access NCML file: {res.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_ncml_file()
