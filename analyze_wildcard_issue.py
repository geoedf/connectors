#!/usr/bin/env python3
"""
Standalone test to analyze wildcard pattern matching without GeoEDF dependencies.
This will help understand why wildcard downloads aren't working.
"""

import requests
import fnmatch
import os
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
                    # some simple filtering to skip spurious hrefs
                    if self.link in value or self.indexcol in value:
                        break
                    # Skip OpenDAP viewer URLs
                    elif 'viewers/viewers' in value:
                        break
                    else:
                        self.inLink = True
                        self.lasttag = tag
                        self.path = value # most likely a filepath
                    
    def handle_data(self, data):
        # only run when we are inside an <a> tag
        if self.lasttag == 'a' and self.inLink:
            self.pathList.append(self.path)

def analyze_opendap_wildcard():
    """Analyze why wildcard patterns don't work with OpenDAP servers"""
    
    # The exact URL and pattern from the YAML
    base_url = "https://opendap.cr.usgs.gov/opendap/hyrax/MOD13Q1.061"
    wildcard_pattern = "MOD13Q1.A2023*.h10v04.061.*.hdf"
    
    print("=== OpenDAP Wildcard Analysis ===")
    print(f"Base URL: {base_url}")
    print(f"Wildcard pattern: {wildcard_pattern}")
    print()
    
    try:
        # Fetch the directory listing
        print("Fetching directory listing...")
        session = requests.Session()
        res = session.get(base_url, timeout=30)
        
        print(f"Status code: {res.status_code}")
        
        if res.status_code == 200:
            # Parse HTML to see what files are available
            parser = SimpleHTMLHelper()
            parser.feed(res.text)
            files = parser.pathList
            
            print(f"Total links found in HTML: {len(files)}")
            print()
            
            # Categorize the files
            hdf_files = []
            viewer_files = []
            metadata_files = []
            other_files = []
            
            for filename in files:
                actual_filename = os.path.basename(filename) if '/' in filename else filename
                
                if actual_filename.endswith('.hdf'):
                    hdf_files.append(actual_filename)
                elif 'viewers' in filename:
                    viewer_files.append(filename)
                elif actual_filename.endswith(('.xml', '.dmr', '.dds', '.das')):
                    metadata_files.append(actual_filename)
                else:
                    other_files.append(actual_filename)
            
            print("=== File categorization ===")
            print(f"Direct .hdf files: {len(hdf_files)}")
            print(f"Viewer URLs: {len(viewer_files)}")
            print(f"Metadata files: {len(metadata_files)}")
            print(f"Other files: {len(other_files)}")
            print()
            
            # Show some examples of each category
            if hdf_files:
                print("Sample .hdf files:")
                for f in hdf_files[:5]:
                    print(f"  {f}")
                if len(hdf_files) > 5:
                    print(f"  ... and {len(hdf_files) - 5} more")
                print()
                
            if viewer_files:
                print("Sample viewer URLs:")
                for f in viewer_files[:5]:
                    print(f"  {f}")
                if len(viewer_files) > 5:
                    print(f"  ... and {len(viewer_files) - 5} more")
                print()
                
            if metadata_files:
                print("Sample metadata files:")
                for f in metadata_files[:5]:
                    print(f"  {f}")
                if len(metadata_files) > 5:
                    print(f"  ... and {len(metadata_files) - 5} more")
                print()
                
            if other_files:
                print("Sample other files:")
                for f in other_files[:5]:
                    print(f"  {f}")
                if len(other_files) > 5:
                    print(f"  ... and {len(other_files) - 5} more")
                print()
            
            # Now test pattern matching on .hdf files
            print("=== Pattern matching test ===")
            base_pattern = wildcard_pattern
            if base_pattern.endswith('.dap.nc4'):
                base_pattern = base_pattern[:-8]
            
            print(f"Pattern for matching: {base_pattern}")
            
            matching_files = []
            for filename in hdf_files:
                if fnmatch.fnmatch(filename, base_pattern):
                    matching_files.append(filename)
            
            print(f"Files matching pattern: {len(matching_files)}")
            for f in matching_files:
                print(f"  {f}")
                
            if not matching_files:
                print("\nNo direct .hdf files match the pattern!")
                print("This explains why wildcard downloads return no files.")
                print()
                
                # Let's see if we can extract base filenames from viewer URLs
                print("=== Attempting to extract base filenames from viewer URLs ===")
                
                base_names_from_viewers = []
                for viewer_url in viewer_files:
                    # Example viewer URL: MOD13Q1.A2023001.h10v04.061.2023004184324.hdf.html
                    if '.hdf.html' in viewer_url:
                        base_name = viewer_url.replace('.html', '')
                        if fnmatch.fnmatch(base_name, base_pattern):
                            base_names_from_viewers.append(base_name)
                
                print(f"Base filenames extracted from viewer URLs matching pattern: {len(base_names_from_viewers)}")
                for f in base_names_from_viewers[:10]:
                    print(f"  {f}")
                    
                if base_names_from_viewers:
                    print("\nThese could be used to construct download URLs by appending .dap.nc4")
                    print("Example download URLs:")
                    for f in base_names_from_viewers[:3]:
                        download_url = f"{base_url}/{f}.dap.nc4"
                        print(f"  {download_url}")
        else:
            print(f"Failed to fetch directory listing: {res.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_opendap_wildcard()
