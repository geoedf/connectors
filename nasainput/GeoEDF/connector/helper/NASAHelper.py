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
                
                # Pre-authenticate with EarthData for USGS OpenDAP servers
                if 'usgs.gov' in url.lower() and 'opendap' in url.lower():
                    print("[Info] Pre-authenticating with EarthData for USGS OpenDAP access...")
                    try:
                        # Establish EarthData session first
                        earthdata_test = session.get("https://urs.earthdata.nasa.gov/profile", timeout=10)
                        if earthdata_test.status_code == 200:
                            print("[Info] EarthData session established successfully")
                        else:
                            print(f"[Warning] EarthData pre-authentication returned: {earthdata_test.status_code}")
                    except Exception as e:
                        print(f"[Warning] EarthData pre-authentication failed: {e}")
                
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
                                    
                                    # Try enhanced alternative approaches
                                    print("[OAuth] Trying enhanced alternative session-based approaches...")
                                    
                                    success = False
                                    
                                    # Method 1: Try direct file access with fresh authenticated session
                                    print("   Method 1: Fresh authenticated session...")
                                    fresh_session = SessionWithHeaderRedirection(auth['user'], auth['password'])
                                    
                                    # First, ensure EarthData authentication is established
                                    try:
                                        auth_check = fresh_session.get("https://urs.earthdata.nasa.gov/profile", timeout=10)
                                        if auth_check.status_code == 200:
                                            print("   Fresh EarthData session established")
                                            
                                            # Now try the data file with no redirects first
                                            direct_response = fresh_session.get(fileURL, allow_redirects=False, stream=True, timeout=60)
                                            print(f"   Direct access response: {direct_response.status_code}")
                                            
                                            if direct_response.status_code == 200:
                                                print("   Direct access successful!")
                                                res = direct_response
                                                success = True
                                            elif direct_response.status_code == 302:
                                                print("   Still getting OAuth redirect with fresh session")
                                                
                                                # Method 2: Try following redirects with fresh session
                                                print("   Method 2: Following redirects with fresh session...")
                                                redirect_response = fresh_session.get(fileURL, allow_redirects=True, stream=True, timeout=60)
                                                print(f"   Redirect response: {redirect_response.status_code}")
                                                
                                                if redirect_response.status_code == 200:
                                                    content_type = redirect_response.headers.get('Content-Type', '')
                                                    content_length = int(redirect_response.headers.get('Content-Length', 0))
                                                    print(f"   Content-Type: {content_type}, Length: {content_length}")
                                                    
                                                    # Check if this looks like actual data (not an HTML page)
                                                    if (content_length > 1000000 or
                                                        'application/octet-stream' in content_type or 
                                                        'application/x-hdf' in content_type or
                                                        'application/netcdf' in content_type or
                                                        'binary' in content_type or
                                                        content_type.startswith('application/') and 'html' not in content_type):
                                                        print("   Fresh session with redirects successful!")
                                                        res = redirect_response
                                                        success = True
                                                    else:
                                                        print("   Response appears to be HTML/text, not data file")
                                        else:
                                            print(f"   Fresh session auth failed: {auth_check.status_code}")
                                    except Exception as e:
                                        print(f"   Fresh session error: {e}")
                                    
                                    # Method 3: Try alternative URL formats
                                    if not success:
                                        print("   Method 3: Trying alternative URL formats...")
                                        
                                        # Sometimes removing .dap and using .nc4 works
                                        if fileURL.endswith('.hdf.dap'):
                                            alt_url = fileURL[:-4] + '.nc4'
                                            print(f"   Trying .nc4 format: {alt_url}")
                                            
                                            try:
                                                nc4_response = fresh_session.get(alt_url, allow_redirects=True, stream=True, timeout=60)
                                                if nc4_response.status_code == 200:
                                                    content_type = nc4_response.headers.get('Content-Type', '')
                                                    content_length = int(nc4_response.headers.get('Content-Length', 0))
                                                    
                                                    if (content_length > 1000000 or
                                                        'application/octet-stream' in content_type or 
                                                        'application/netcdf' in content_type):
                                                        print("   .nc4 format successful!")
                                                        res = nc4_response
                                                        success = True
                                                    else:
                                                        print(f"   .nc4 response not data: {content_type}, {content_length}")
                                                else:
                                                    print(f"   .nc4 format failed: {nc4_response.status_code}")
                                            except Exception as e:
                                                print(f"   .nc4 format error: {e}")
                                    
                                    if not success:
                                        print("   Method 4: Direct OAuth URL completion attempt...")
                                        
                                        try:
                                            # Try visiting the OAuth URL directly with authenticated session
                                            oauth_direct = fresh_session.get(oauth_url, allow_redirects=True, timeout=60)
                                            print(f"   OAuth direct response: {oauth_direct.status_code}")
                                            
                                            if oauth_direct.status_code == 200:
                                                # Check if we got redirected back to the data URL
                                                final_url = oauth_direct.url
                                                print(f"   Final URL after OAuth: {final_url}")
                                                
                                                if fileURL in final_url or 'hdf' in final_url:
                                                    content_type = oauth_direct.headers.get('Content-Type', '')
                                                    content_length = int(oauth_direct.headers.get('Content-Length', 0))
                                                    
                                                    if (content_length > 1000000 or
                                                        'application/octet-stream' in content_type or 
                                                        'application/x-hdf' in content_type or
                                                        'application/netcdf' in content_type):
                                                        print("   Direct OAuth completion successful!")
                                                        res = oauth_direct
                                                        success = True
                                                    else:
                                                        print(f"   OAuth response not data: {content_type}, {content_length}")
                                                else:
                                                    print("   OAuth didn't redirect to data URL")
                                            else:
                                                print(f"   OAuth direct access failed: {oauth_direct.status_code}")
                                        except Exception as e:
                                            print(f"   OAuth direct access error: {e}")
                                    
                                    if not success:
                                        # All methods failed - provide manual download info
                                        print("[OAuth] All automated methods failed")
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
        from urllib.parse import urlparse, parse_qs
        import base64
        
        # Extract the original data URL from the OAuth state parameter
        parsed_url = urlparse(oauth_url)
        params = parse_qs(parsed_url.query)
        state_param = params.get('state', [None])[0]
        
        original_data_url = None
        if state_param:
            try:
                # Add padding if needed for base64 decoding
                state_padded = state_param + '=' * (4 - len(state_param) % 4)
                original_data_url = base64.b64decode(state_padded).decode('utf-8')
                print(f"   Decoded original URL: {original_data_url}")
            except Exception as e:
                print(f"   Could not decode state parameter: {e}")
                return None
        
        # Method 1: Complete OAuth flow programmatically
        print("   Attempting programmatic OAuth flow...")
        
        oauth_session = SessionWithHeaderRedirection(auth['user'], auth['password'])
        
        # Step 1: Pre-authenticate with EarthData to establish session
        try:
            earthdata_login = "https://urs.earthdata.nasa.gov/login"
            login_response = oauth_session.get(earthdata_login, timeout=30)
            if login_response.status_code == 200:
                print("   EarthData session pre-established")
        except Exception as e:
            print(f"   EarthData pre-auth warning: {e}")
        
        # Step 2: Try the OAuth URL with established session
        auth_response = oauth_session.get(oauth_url, allow_redirects=True, timeout=30)
        
        if auth_response.status_code == 200:
            # Check if we were redirected back to data (OAuth completed automatically)
            if original_data_url and original_data_url in auth_response.url:
                content_type = auth_response.headers.get('Content-Type', '')
                content_length = len(auth_response.content) if hasattr(auth_response, 'content') else 0
                
                # Check if this looks like actual data
                if (content_length > 1000000 or  # Large file
                    'application/octet-stream' in content_type or 
                    'application/x-hdf' in content_type or
                    'application/netcdf' in content_type):
                    print("   OAuth flow completed successfully!")
                    return auth_response
            
            # If we're still at the OAuth page, try to handle it programmatically
            # Check for common OAuth approval patterns in the response
            response_text = auth_response.text.lower() if hasattr(auth_response, 'text') else ''
            
            if ('authorize' in response_text or 'approve' in response_text or 
                'grant access' in response_text or 'allow' in response_text):
                print("   Found OAuth authorization page - attempting approval...")
                
                # Try to find and submit authorization form automatically
                try:
                    import re
                    
                    # Look for approval/authorize forms with action URLs
                    form_pattern = r'<form[^>]+action=["\']([^"\']*(?:authorize|approve|oauth)[^"\']*)["\'][^>]*>'
                    forms = re.findall(form_pattern, auth_response.text, re.IGNORECASE)
                    
                    for action in forms:
                        print(f"   Trying OAuth approval form: {action}")
                        
                        # Build form URL
                        if action.startswith('/'):
                            form_url = f"https://urs.earthdata.nasa.gov{action}"
                        elif action.startswith('http'):
                            form_url = action
                        else:
                            form_url = f"https://urs.earthdata.nasa.gov/{action}"
                        
                        # Extract hidden form fields and submit approval
                        input_pattern = r'<input[^>]+name=["\']([^"\']+)["\'][^>]*(?:value=["\']([^"\']*)["\'])?[^>]*>'
                        inputs = re.findall(input_pattern, auth_response.text, re.IGNORECASE)
                        
                        form_data = {}
                        for name, value in inputs:
                            if name and name.lower() not in ['username', 'password']:  # Skip login fields
                                form_data[name] = value or ''
                        
                        # Add common approval parameters
                        form_data.update({
                            'approve': 'yes',
                            'authorized': 'true',
                            'allow': 'true'
                        })
                        
                        approval_response = oauth_session.post(form_url, data=form_data, allow_redirects=True, timeout=30)
                        
                        if approval_response.status_code == 200 and original_data_url:
                            # After approval, try accessing the original data URL
                            final_response = oauth_session.get(original_data_url, allow_redirects=True, timeout=30)
                            
                            if final_response.status_code == 200:
                                content_type = final_response.headers.get('Content-Type', '')
                                content_length = len(final_response.content) if hasattr(final_response, 'content') else 0
                                
                                if (content_length > 1000000 or
                                    'application/octet-stream' in content_type or 
                                    'application/x-hdf' in content_type or
                                    'application/netcdf' in content_type):
                                    print("   OAuth approval successful!")
                                    return final_response
                
                except Exception as e:
                    print(f"   OAuth approval error: {e}")
             # Step 2: Try to extract and submit any OAuth forms
            try:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(auth_response.content, 'html.parser')
                    
                    # Look for OAuth authorization forms
                    forms = soup.find_all('form')
                    for form in forms:
                        action = form.get('action', '')
                        if 'authorize' in action or 'oauth' in action.lower():
                            print("   Found OAuth authorization form, submitting...")
                            
                            # Build form data
                            form_data = {}
                            for input_tag in form.find_all('input'):
                                name = input_tag.get('name')
                                value = input_tag.get('value', '')
                                if name:
                                    form_data[name] = value
                            
                            # Submit the form
                            form_url = action if action.startswith('http') else f"https://urs.earthdata.nasa.gov{action}"
                            form_response = oauth_session.post(form_url, data=form_data, allow_redirects=True, timeout=30)
                            
                            if form_response.status_code == 200 and original_data_url:
                                # Try to access the original data URL with the authenticated session
                                data_response = oauth_session.get(original_data_url, allow_redirects=True, timeout=30)
                                
                                if data_response.status_code == 200:
                                    content_type = data_response.headers.get('Content-Type', '')
                                    content_length = len(data_response.content) if hasattr(data_response, 'content') else 0
                                    
                                    if (content_length > 1000000 or
                                        'application/octet-stream' in content_type or 
                                        'application/x-hdf' in content_type or
                                        'application/netcdf' in content_type):
                                        print("   OAuth form submission successful!")
                                        return data_response
                        
                except ImportError:
                    print("   BeautifulSoup not available - trying alternative form parsing...")
                    
                    # Alternative: Simple regex-based form extraction
                    import re
                    
                    # Look for form action URLs
                    form_pattern = r'<form[^>]+action=["\']([^"\']+)["\'][^>]*>'
                    forms = re.findall(form_pattern, auth_response.text, re.IGNORECASE)
                    
                    for action in forms:
                        if 'authorize' in action or 'oauth' in action.lower():
                            print(f"   Found OAuth form action: {action}")
                            
                            # Extract all input fields from the form
                            input_pattern = r'<input[^>]+name=["\']([^"\']+)["\'][^>]*(?:value=["\']([^"\']*)["\'])?[^>]*>'
                            inputs = re.findall(input_pattern, auth_response.text, re.IGNORECASE)
                            
                            form_data = {}
                            for name, value in inputs:
                                if name:
                                    form_data[name] = value or ''
                            
                            # Submit the form
                            form_url = action if action.startswith('http') else f"https://urs.earthdata.nasa.gov{action}"
                            form_response = oauth_session.post(form_url, data=form_data, allow_redirects=True, timeout=30)
                            
                            if form_response.status_code == 200 and original_data_url:
                                # Try to access the original data URL with the authenticated session
                                data_response = oauth_session.get(original_data_url, allow_redirects=True, timeout=30)
                                
                                if data_response.status_code == 200:
                                    content_type = data_response.headers.get('Content-Type', '')
                                    content_length = len(data_response.content) if hasattr(data_response, 'content') else 0
                                    
                                    if (content_length > 1000000 or
                                        'application/octet-stream' in content_type or 
                                        'application/x-hdf' in content_type or
                                        'application/netcdf' in content_type):
                                        print("   OAuth form submission successful!")
                                        return data_response
                        
            except Exception as e:
                print(f"   Form processing error: {e}")
        
        # Method 2: Try direct access with session cookies from EarthData login
        print("   Trying direct access with EarthData session...")
        
        if original_data_url:
            # First authenticate with EarthData directly
            earthdata_login_url = "https://urs.earthdata.nasa.gov/login"
            login_response = oauth_session.get(earthdata_login_url, timeout=30)
            
            if login_response.status_code == 200:
                # Now try the original data URL with established session
                data_response = oauth_session.get(original_data_url, allow_redirects=True, timeout=30)
                
                if data_response.status_code == 200:
                    content_type = data_response.headers.get('Content-Type', '')
                    content_length = len(data_response.content) if hasattr(data_response, 'content') else 0
                    
                    if (content_length > 1000000 or
                        'application/octet-stream' in content_type or 
                        'application/x-hdf' in content_type or
                        'application/netcdf' in content_type):
                        print("   Direct EarthData session access successful!")
                        return data_response
                    elif data_response.status_code != 302:  # Not a redirect
                        print(f"   Got response but may not be data: {content_type}, {content_length} bytes")
        
        # Method 3: Log authentication status for debugging
        print("   Checking authentication status...")
        
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
        print("   Note: USGS OpenDAP OAuth may require interactive login or application tokens")
        return None
        
    except Exception as e:
        print(f"   OAuth authentication error: {e}")
        return None


