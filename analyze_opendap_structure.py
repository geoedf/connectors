#!/usr/bin/env python3
"""
Detailed analysis of OpenDAP HTML structure to understand available file formats.
"""

import requests
import fnmatch
import os
from html.parser import HTMLParser

class DetailedHTMLHelper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inLink = False
        self.path = ''
        self.pathList = []
        self.indexcol = ';'
        self.link = 'http'
        
    def handle_starttag(self, tag, attrs):
        self.inLink = False
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    # Keep all hrefs for detailed analysis
                    if self.link in value or self.indexcol in value:
                        break
                    else:
                        self.inLink = True
                        self.lasttag = tag
                        self.path = value
                    
    def handle_data(self, data):
        if self.lasttag == 'a' and self.inLink:
            self.pathList.append(self.path)

def analyze_opendap_structure():
    """Analyze the actual structure of OpenDAP directories"""
    
    base_url = "https://opendap.cr.usgs.gov/opendap/hyrax/MOD13Q1.061"
    wildcard_pattern = "MOD13Q1.A2023*.h10v04.061.*.hdf"
    
    print("=== Detailed OpenDAP Structure Analysis ===")
    print(f"Base URL: {base_url}")
    print(f"Target pattern: {wildcard_pattern}")
    print()
    
    try:
        session = requests.Session()
        res = session.get(base_url, timeout=30)
        
        if res.status_code == 200:
            parser = DetailedHTMLHelper()
            parser.feed(res.text)
            files = parser.pathList
            
            print(f"Total links found: {len(files)}")
            print()
            
            # Group files by extension
            extensions = {}
            matching_base_patterns = []
            
            for filename in files:
                actual_filename = os.path.basename(filename) if '/' in filename else filename
                
                # Check if this could be a file we're looking for (contains key components)
                if 'h10v04' in actual_filename and '2023' in actual_filename:
                    print(f"Potential match: {actual_filename}")
                    
                    # Try to extract the base .hdf filename
                    if '.hdf.' in actual_filename:
                        # This might be a derived format from a .hdf file
                        base_hdf = actual_filename.split('.hdf.')[0] + '.hdf'
                        if fnmatch.fnmatch(base_hdf, wildcard_pattern.replace('.hdf', '')):
                            matching_base_patterns.append((actual_filename, base_hdf))
                
                # Track extensions
                if '.' in actual_filename:
                    ext = actual_filename.split('.')[-1]
                    if ext not in extensions:
                        extensions[ext] = []
                    extensions[ext].append(actual_filename)
            
            print()
            print("=== Available file extensions ===")
            for ext, file_list in sorted(extensions.items()):
                print(f"{ext}: {len(file_list)} files")
                if len(file_list) <= 5:
                    for f in file_list:
                        print(f"  {f}")
                else:
                    for f in file_list[:3]:
                        print(f"  {f}")
                    print(f"  ... and {len(file_list) - 3} more")
                print()
            
            print("=== Potential base .hdf files from derivatives ===")
            for actual_file, base_hdf in matching_base_patterns:
                print(f"Derivative: {actual_file}")
                print(f"Base HDF:   {base_hdf}")
                print(f"Download URL would be: {base_url}/{base_hdf}.dap.nc4")
                print()
                
            # Let's specifically look for files that contain our search terms
            print("=== Files containing 'h10v04' and '2023' ===")
            relevant_files = []
            for filename in files:
                actual_filename = os.path.basename(filename) if '/' in filename else filename
                if 'h10v04' in actual_filename and '2023' in actual_filename:
                    relevant_files.append(actual_filename)
            
            print(f"Found {len(relevant_files)} relevant files:")
            for f in relevant_files[:20]:  # Show first 20
                print(f"  {f}")
            if len(relevant_files) > 20:
                print(f"  ... and {len(relevant_files) - 20} more")
                
        else:
            print(f"Failed to fetch directory: {res.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_opendap_structure()
