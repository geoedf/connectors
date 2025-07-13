#!/usr/bin/env python3
"""
Check if we need to navigate to a specific year/date directory for individual files.
"""

import requests
from html.parser import HTMLParser

class SimpleHTMLHelper(HTMLParser):
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
                    if self.link in value or self.indexcol in value:
                        break
                    elif 'viewers/viewers' in value:
                        break
                    else:
                        self.inLink = True
                        self.lasttag = tag
                        self.path = value
                    
    def handle_data(self, data):
        if self.lasttag == 'a' and self.inLink:
            self.pathList.append(self.path)

def explore_opendap_navigation():
    """Explore if there are subdirectories with actual .hdf files"""
    
    base_url = "https://opendap.cr.usgs.gov/opendap/hyrax/MOD13Q1.061"
    
    print("=== Exploring OpenDAP Directory Navigation ===")
    
    try:
        session = requests.Session()
        res = session.get(base_url, timeout=30)
        
        if res.status_code == 200:
            parser = SimpleHTMLHelper()
            parser.feed(res.text)
            files = parser.pathList
            
            # Look for directory-like entries
            directories = []
            for filename in files:
                # Directories typically end with / or are single names without extensions
                if filename.endswith('/') or ('.' not in filename and len(filename) > 0):
                    directories.append(filename)
            
            print(f"Potential directories found: {len(directories)}")
            for d in directories[:20]:
                print(f"  {d}")
            if len(directories) > 20:
                print(f"  ... and {len(directories) - 20} more")
            
            # Look for year-based directories
            year_dirs = [d for d in directories if '2023' in d]
            print(f"\nDirectories containing '2023': {len(year_dirs)}")
            for d in year_dirs:
                print(f"  {d}")
                
            # Test a few year directories if they exist
            for year_dir in year_dirs[:3]:
                test_url = f"{base_url}/{year_dir}".rstrip('/')
                print(f"\nTesting subdirectory: {test_url}")
                
                try:
                    subres = session.get(test_url, timeout=30)
                    if subres.status_code == 200:
                        subparser = SimpleHTMLHelper()
                        subparser.feed(subres.text)
                        subfiles = subparser.pathList
                        
                        # Look for .hdf files in subdirectory
                        hdf_files = [f for f in subfiles if f.endswith('.hdf')]
                        print(f"  Found {len(hdf_files)} .hdf files")
                        
                        # Look for files with h10v04
                        h10v04_files = [f for f in subfiles if 'h10v04' in f]
                        print(f"  Found {len(h10v04_files)} files with 'h10v04'")
                        
                        if h10v04_files:
                            print("  Sample h10v04 files:")
                            for f in h10v04_files[:5]:
                                print(f"    {f}")
                                
                    else:
                        print(f"  Failed to access: {subres.status_code}")
                        
                except Exception as e:
                    print(f"  Error accessing subdirectory: {e}")
                    
            # Check if there's a different URL structure for individual files
            print(f"\n=== Testing different URL approaches ===")
            
            # Try a direct file approach
            test_file_url = f"{base_url}/MOD13Q1.A2023001.h10v04.061.2023004184324.hdf.dap.nc4"
            print(f"Testing direct file URL: {test_file_url}")
            
            try:
                file_res = session.head(test_file_url, timeout=30)
                print(f"  Status: {file_res.status_code}")
                if file_res.status_code == 200:
                    print("  File exists! This suggests the correct URL pattern.")
                elif file_res.status_code == 404:
                    print("  File not found with this pattern.")
                else:
                    print(f"  Unexpected status: {file_res.status_code}")
            except Exception as e:
                print(f"  Error testing file URL: {e}")
                
        else:
            print(f"Failed to access base directory: {res.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    explore_opendap_navigation()
