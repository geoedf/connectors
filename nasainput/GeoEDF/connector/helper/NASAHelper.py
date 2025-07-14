#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
import os
import fnmatch
from geoedfframework.utils.GeoEDFError import GeoEDFError
from .HTMLHelper import HTMLHelper

""" Helper module for performing HTTP GET and POST operations.
    This module is primarily intended for use with the NASAInput connector.
    It is assumed that we need to login to EarthData to be able to access this 
    dataset. 
    Follows the example here: https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python
"""

# overriding requests.Session.rebuild_auth to mantain headers when redirected
 
class SessionWithHeaderRedirection(requests.Session):
 
    AUTH_HOST = 'urs.earthdata.nasa.gov'
 
    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)
 
   # Overrides from the library to keep headers when redirected to or from
   # the NASA auth host.
    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url

        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)

            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != self.AUTH_HOST and \
                    original_parsed.hostname != self.AUTH_HOST:
                del headers['Authorization']
        return

def validateAuth(auth):
    """ validates an authentication dictionary to look for specific keys,
	returns a boolean result
    """
    return ('user' in auth and 'password' in auth)

def getFilename(resp,url):
    """ tries to figure out the filename by either looking at the response 
        header for content-disposition, or by extracting the last segment of the URL
    """
    filename = ''
    if "Content-Disposition" in resp.headers.keys():
        if 'filename' in resp.headers["Content-Disposition"]:
            filename = re.findall("filename=(.+)", resp.headers["Content-Disposition"])[0]
        else:
            filename = url.split("/")[-1]
    else:
        filename = url.split("/")[-1]
    return filename

# get a list of files from the HTTP site & match against the wildcard path in the URL
# assume * is the only wildcard character
def getFileList(url, auth):
    if '*' in url: #has wildcard
        # first get the base URL to get a listing of files
        partitioned = url.rpartition('/')
        base_url = partitioned[0]
        poss_filename = partitioned[2]
        # naive check whether poss_filename is indeed a file
        if '.' in poss_filename and '*' in poss_filename:
            filename_pattern = poss_filename
            try:
                # Check if this is an OpenDAP server by looking at URL pattern
                is_opendap = 'opendap' in base_url.lower()
                
                # For OpenDAP servers, try unauthenticated directory listing first
                # since directory listings are often publicly accessible
                if is_opendap:
                    try:
                        import requests
                        res = requests.get(base_url)
                        res.raise_for_status()
                    except requests.exceptions.HTTPError:
                        # If unauthenticated fails, fall back to authenticated request
                        session = SessionWithHeaderRedirection(auth['user'], auth['password'])
                        res = session.get(base_url)
                        res.raise_for_status()
                else:
                    # For non-OpenDAP servers, use authenticated request
                    session = SessionWithHeaderRedirection(auth['user'], auth['password'])
                    res = session.get(base_url)
                    res.raise_for_status()
                
                # parse the returned HTML to get a possible file listing
                parser = HTMLHelper()
                parser.feed(res.text)
                files = parser.pathList

                result = []
                
                for filename in files:
                    # some filenames may be an absolute or relative path
                    if '/' in filename:
                        actual_filename = os.path.basename(filename)
                    else:
                        actual_filename = filename
                    
                    # For OpenDAP servers, look for .hdf.dap files (not raw .hdf)
                    if is_opendap:
                        # OpenDAP servers expose service endpoints like .hdf.dap, not raw .hdf files
                        # Look for .hdf.dap files and extract the base HDF filename for pattern matching
                        if actual_filename.endswith('.hdf.dap'):
                            # Extract base HDF filename (remove .dap suffix)
                            base_hdf_name = actual_filename[:-4]  # Remove .dap to get .hdf file
                            
                            # Match the base HDF filename against the pattern
                            base_pattern = filename_pattern
                            if base_pattern.endswith('.dap'):
                                base_pattern = base_pattern[:-4]  # Remove .dap to get .hdf pattern
                            
                            if fnmatch.fnmatch(base_hdf_name, base_pattern):
                                # For data download, use .dap extension (not .dap.nc4)
                                download_filename = base_hdf_name + '.dap'
                                
                                # if path leads with a /, we need to revise the url, else can just append
                                if filename.startswith('/'):
                                    # get the URL prefix
                                    if base_url.startswith('https://'):
                                        skip = 8 # number of characters to skip in prefix
                                    elif base_url.startswith('http://'):
                                        skip = 7
                                    else:
                                        skip = 0

                                    next_slash = base_url.find('/',skip)
                                    if next_slash != -1:
                                        url_prefix = base_url[:next_slash]
                                    else:
                                        url_prefix = base_url
                                    # Use the directory path from filename but with download_filename
                                    file_dir = os.path.dirname(filename)
                                    if file_dir:
                                        result.append('%s%s/%s' % (url_prefix, file_dir, download_filename))
                                    else:
                                        result.append('%s/%s' % (url_prefix, download_filename))
                                else:
                                    result.append('%s/%s' % (base_url, download_filename))
                    else:
                        # For non-OpenDAP servers, use original logic
                        if fnmatch.fnmatch(actual_filename, filename_pattern):
                            # if path leads with a /, we need to revise the url, else can just append
                            if filename.startswith('/'):
                                # get the URL prefix
                                if base_url.startswith('https://'):
                                    skip = 8 # number of characters to skip in prefix
                                elif base_url.startswith('http://'):
                                    skip = 7
                                else:
                                    skip = 0

                                next_slash = base_url.find('/',skip)
                                if next_slash != -1:
                                    url_prefix = base_url[:next_slash]
                                else:
                                    url_prefix = base_url
                                result.append('%s%s' % (url_prefix,filename))
                            else:
                                result.append('%s/%s' % (base_url,filename))
                return result
            except requests.exceptions.HTTPError as e:
                # Handle missing date directories gracefully (common in satellite data)
                if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                    # 404 means the date directory doesn't exist - return empty list
                    return []
                else:
                    # Other HTTP errors are genuine problems
                    raise GeoEDFError(f'Error accessing file listing at URL: {e}')
            except Exception as e:
                raise GeoEDFError(f'Unexpected error during file listing: {e}')
        else:
            raise GeoEDFError('URL does not point to a file or set of files')
    else:
        # For single file URLs, check if this is an OpenDAP server
        # and if the URL needs .dap.nc4 extension for data access
        if 'opendap' in url.lower() and url.endswith('.hdf'):
            # For OpenDAP servers, append .dap to .hdf files for data access
            return [url + '.dap']
        else:
            # For non-OpenDAP servers or URLs already with proper extension
            return [url]


def getFile(url, auth=None, path=None): 
    """ download file(s) at url and save to path
	if path is None, save to /tmp
	auth is an optional dictionary with user and password
	returns boolean result
    """

    # validate that URL is not null
    if url is None:
        raise GeoEDFError('Null URL provided for getFile')

    # default path to /tmp
    if path is None:
        path = '/tmp'

    # if no auth provided, use an non-authenticated request
    # if insufficient/incorrect auth provided, return error
    try:
        if auth is None:
            raise GeoEDFError('Authentication required for accessing NASA data')
        else:
            
            if validateAuth(auth): # auth validated for completeness
                session = SessionWithHeaderRedirection(auth['user'], auth['password'])
                
                # Always use getFileList to get properly formatted URLs (handles both wildcard and single file cases)
                fileURLList = getFileList(url,auth)
                
                # Handle cases where no files are found (e.g., missing date directories)
                if not fileURLList:
                    # No files found - this is normal for satellite data with gaps
                    # Return True to indicate successful processing (even though no files downloaded)
                    return True
                
                # recreate session object since file listing may not need auth
                session = SessionWithHeaderRedirection(auth['user'], auth['password'])
                downloaded_count = 0
                
                for fileURL in fileURLList:
                    try:
                        # Try direct download first
                        res = session.get(fileURL, stream=True, allow_redirects=False)
                        
                        if res.status_code == 302:
                            # OAuth redirect detected - handle automatically
                            oauth_url = res.headers.get('Location')
                            if oauth_url and 'oauth/authorize' in oauth_url:
                                print(f"[OAuth] OAuth redirect detected for: {fileURL}")
                                print("[OAuth] Attempting automated OAuth authentication...")
                                
                                # Try automated OAuth authentication
                                oauth_response = handle_oauth_authentication(session, oauth_url, auth)
                                
                                if oauth_response and oauth_response.status_code == 200:
                                    print("[OAuth] OAuth authentication successful!")
                                    res = oauth_response
                                else:
                                    print("[OAuth] OAuth authentication failed")
                                    print(f"[OAuth] Manual download required: {oauth_url}")
                                    print(f"[OAuth] Original file URL: {fileURL}")
                                    print("[OAuth] Please download manually using browser with EarthData login")
                                    continue
                            else:
                                # Non-OAuth redirect - follow normally
                                res = session.get(fileURL, stream=True)
                        
                        # For direct access (200) or successful OAuth, continue with download
                        if res.status_code != 200:
                            res.raise_for_status()
                        
                        # get the name of the file to save
                        outFilename = getFilename(res,fileURL)
                        outPath = '%s/%s' % (path,outFilename.strip('"'))
                        with open(outPath,'wb') as outFile:
                            for chunk in res.iter_content(chunk_size=1024*1024):
                                outFile.write(chunk)
                        downloaded_count += 1
                        
                    except requests.exceptions.HTTPError as e:
                        # Handle individual file download errors gracefully
                        if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                            # File not found - skip this file but continue with others
                            continue
                        else:
                            # Other HTTP errors should be raised
                            raise e
                
                # Return True if we successfully processed the request (even if no files downloaded)  
                if downloaded_count > 0:
                    print(f"[Success] Successfully downloaded {downloaded_count} file(s)")
                else:
                    print(f"[Info] Processed {len(fileURLList)} file(s) - check output above for OAuth URLs if needed")
                    
                return True

            else: # auth could not be validated
                raise GeoEDFError('Invalid authentication provided!')
  
    except GeoEDFError: # known error
        raise
    except requests.exceptions.HTTPError:
        raise

def handle_oauth_authentication(session, oauth_url, auth):
    """
    Handle OAuth authentication automatically using username/password
    
    Args:
        session: The requests session object
        oauth_url: The OAuth authorization URL
        auth: Dictionary with 'user' and 'password' keys
        
    Returns:
        Response object if successful, None if failed
    """
    try:
        # Method 1: Create a new session and try to authenticate with EarthData
        print("   Trying EarthData login with OAuth redirect...")
        
        # Create a fresh session for OAuth handling
        oauth_session = SessionWithHeaderRedirection(auth['user'], auth['password'])
        
        # First, establish session with EarthData by accessing the OAuth URL
        response = oauth_session.get(oauth_url, allow_redirects=True, timeout=30)
        
        # Check if we got redirected back to the original data URL
        if response.status_code == 200:
            final_url = response.url
            content_type = response.headers.get('Content-Type', '')
            content_length = len(response.content) if hasattr(response, 'content') else 0
            
            print(f"   Final URL after OAuth: {final_url}")
            print(f"   Content-Type: {content_type}")
            print(f"   Content-Length: {content_length}")
            
            # Check if this looks like actual data
            if (content_length > 1000000 or  # Large file
                'application/octet-stream' in content_type or 
                'application/x-hdf' in content_type or
                'application/netcdf' in content_type or
                'dap' in final_url.lower()):  # OpenDAP data
                return response
        
        # Method 2: If OAuth redirect didn't work, try direct authentication to original server
        print("   Trying direct server authentication...")
        
        # Parse the OAuth URL to extract the original URL from state parameter
        from urllib.parse import urlparse, parse_qs
        import base64
        
        parsed_url = urlparse(oauth_url)
        params = parse_qs(parsed_url.query)
        state_param = params.get('state', [None])[0]
        
        if state_param:
            try:
                # Add padding if needed for base64 decoding
                state_padded = state_param + '=' * (4 - len(state_param) % 4)
                decoded_state = base64.b64decode(state_padded).decode('utf-8')
                print(f"   Decoded original URL: {decoded_state}")
                
                # If the decoded URL is the same as what we started with, 
                # the issue is authentication, not URL format
                if decoded_state != oauth_url:
                    # Try a direct request to the original data URL with authenticated session
                    print("   Trying direct access to original URL with authenticated session...")
                    response = oauth_session.get(decoded_state, allow_redirects=False, timeout=30)
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if ('application/octet-stream' in content_type or 
                            'application/x-hdf' in content_type or
                            'application/netcdf' in content_type or
                            len(response.content) > 1000000):
                            return response
                    elif response.status_code == 302:
                        print("   Still getting redirected - OAuth credentials may be invalid")
                        
            except Exception as e:
                print(f"   Could not decode state parameter: {e}")
        
        # Method 3: Log authentication status for debugging
        print("   Checking authentication status...")
        
        # Try a simple authenticated request to EarthData to verify credentials
        try:
            auth_test_url = "https://urs.earthdata.nasa.gov/profile"
            auth_response = oauth_session.get(auth_test_url, timeout=10)
            if auth_response.status_code == 200:
                print("   EarthData credentials appear valid")
            else:
                print(f"   EarthData authentication issue: {auth_response.status_code}")
        except Exception as e:
            print(f"   Could not verify EarthData credentials: {e}")
        
        print("   All OAuth authentication methods failed")
        print("   Note: USGS OpenDAP OAuth may require interactive login or special token")
        return None
        
    except Exception as e:
        print(f"   OAuth authentication error: {e}")
        return None


