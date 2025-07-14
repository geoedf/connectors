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
    
    # Remove any surrounding quotes from filename
    filename = filename.strip('"\'')
    
    print(f"[Debug] Original filename from URL (after quote removal): {filename}")
    
    # For OpenDAP downloads, handle different format extensions appropriately
    if (filename.endswith('.hdf.dap') or 
        filename.endswith('.hdf.dods') or 
        filename.endswith('.hdf.nc4') or 
        filename.endswith('.hdf.nc')):
        
        content_type = resp.headers.get('Content-Type', '').lower()
        
        print("[Debug] Found OpenDAP data file - processing extension")
        
        # Determine the base filename and appropriate extension
        if filename.endswith('.hdf.nc4'):
            # .nc4 is already NetCDF4/HDF5 format - keep the .nc4 extension
            base_filename = filename[:-8]  # Remove .hdf.nc4
            final_extension = '.nc4'
            format_info = "NetCDF4 format (HDF5-compatible)"
            keep_original = True
        elif filename.endswith('.hdf.dap'):
            base_filename = filename[:-8]  # Remove .hdf.dap
            final_extension = '.h5'
            format_info = "DAP format -> HDF5"
            keep_original = False
        elif filename.endswith('.hdf.dods'):
            base_filename = filename[:-9]  # Remove .hdf.dods
            final_extension = '.h5'
            format_info = "DODS format -> HDF5"
            keep_original = False
        elif filename.endswith('.hdf.nc'):
            base_filename = filename[:-7]  # Remove .hdf.nc
            final_extension = '.nc'
            format_info = "NetCDF3 format"
            keep_original = True
        
        # Apply the appropriate extension
        filename = base_filename + final_extension
        
        print(f"[Info] OpenDAP file processed: {filename}")
        print(f"[Info] Format: {format_info}")
        if keep_original:
            print("[Info] Keeping original extension for format compatibility")
        else:
            print("[Info] Converted to .h5 extension for HDF5 tools")
        print(f"[Info] Content-Type: {content_type}")
    else:
        print(f"[Debug] No conversion needed for filename: {filename}")
        if filename.endswith('.dap'):
            print("[Debug] File ends with .dap but not .hdf.dap - checking exact format...")
            print(f"[Debug] Filename length: {len(filename)}, ends with: '{filename[-10:]}'")
    
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
                                # For OpenDAP data download, prefer NetCDF4 format which is HDF5-compatible
                                # The .nc4 format is what works with h5dump and HDF5 tools
                                # Order of preference based on compatibility:
                                # 1. .nc4 - NetCDF4 format (HDF5-based, works with h5dump)
                                # 2. .dods - Binary DODS format 
                                # 3. .nc - NetCDF3 format
                                # 4. .dap - DAP format (may return XML metadata)
                                
                                preferred_formats = ['.nc4', '.dods', '.nc', '.dap']
                                
                                for format_ext in preferred_formats:
                                    download_filename = base_hdf_name + format_ext
                                    
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
                                    
                                    # For now, just add the first preferred format
                                    # The download logic will handle fallbacks if needed
                                    break
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
        if 'opendap' in url.lower() and url.endswith('.hdf'):
            # For OpenDAP servers, prefer NetCDF4 format which is HDF5-compatible
            # The .nc4 format is what works with h5dump and HDF5 tools
            preferred_formats = ['.nc4', '.dods', '.nc', '.dap']
            
            # Return multiple URLs to try in order (download logic will handle fallbacks)
            return [url + format_ext for format_ext in preferred_formats]
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
                    # For OpenDAP servers with multiple format options, try each until we get binary data
                    if isinstance(fileURL, list):
                        url_attempts = fileURL
                    else:
                        url_attempts = [fileURL]
                    
                    download_successful = False
                    
                    for attempt_url in url_attempts:
                        if download_successful:
                            break
                            
                        print(f"[Attempt] Trying URL: {attempt_url}")
                        
                        try:
                            # Try direct download first
                            res = session.get(attempt_url, stream=True, allow_redirects=False)
                            
                            if res.status_code == 302:
                                # OAuth redirect detected - handle automatically
                                oauth_url = res.headers.get('Location')
                                if oauth_url and 'oauth/authorize' in oauth_url:
                                    print(f"[OAuth] OAuth redirect detected for: {attempt_url}")
                                    print("[OAuth] Attempting automated OAuth authentication...")
                                    
                                    # Try automated OAuth authentication
                                    oauth_response = handle_oauth_authentication(session, oauth_url, auth)
                                    
                                    if oauth_response and oauth_response.status_code == 200:
                                        print("[OAuth] OAuth authentication successful!")
                                        res = oauth_response
                                    else:
                                        print("[OAuth] OAuth authentication failed - trying next URL format")
                                        continue
                                else:
                                    # Non-OAuth redirect - follow normally
                                    res = session.get(attempt_url, stream=True)
                            
                            # For direct access (200) or successful OAuth, continue with download
                            if res.status_code != 200:
                                print(f"[Error] HTTP {res.status_code} for {attempt_url} - trying next format")
                                continue
                            
                            # Check if we got XML metadata instead of binary data
                            content_type = res.headers.get('Content-Type', 'unknown')
                            
                            # Detect XML metadata responses (common issue with OpenDAP .dap URLs)
                            is_xml_metadata = False
                            if ('xml' in content_type.lower() or 
                                'text' in content_type.lower() or
                                content_type == 'application/vnd.opendap.dap4.data'):
                                
                                # Check first few bytes to confirm it's XML
                                first_chunk = next(res.iter_content(chunk_size=512), b'')
                                if first_chunk.startswith(b'<?xml') or first_chunk.startswith(b'<'):
                                    is_xml_metadata = True
                                    print(f"[Warning] Got XML metadata from {attempt_url} - trying next format")
                                    print(f"[Warning] Content-Type: {content_type}")
                                    continue
                            
                            # If we get here, we have a potentially good response
                            print(f"[Success] Got valid response from: {attempt_url}")
                            
                            # get the name of the file to save
                            outFilename = getFilename(res, attempt_url)
                            outPath = '%s/%s' % (path, outFilename.strip('"'))
                            
                            # Log download details
                            content_length = res.headers.get('Content-Length', 'unknown')
                            print(f"[Download] File: {outFilename}")
                            print(f"[Download] Content-Type: {content_type}")
                            print(f"[Download] Content-Length: {content_length} bytes")
                            
                            # Download and validate the content
                            with open(outPath, 'wb') as outFile:
                                first_chunk_written = False
                                for chunk in res.iter_content(chunk_size=1024*1024):
                                    if not first_chunk_written and chunk:
                                        # Check first chunk for content type
                                        if chunk.startswith(b'<?xml') or chunk.startswith(b'<'):
                                            print("[Warning] Downloaded file appears to be XML metadata, not binary data")
                                            print("[Warning] First 200 chars:", chunk[:200])
                                            # Don't break here - save the file anyway for debugging
                                        elif chunk.startswith(b'\x89HDF'):
                                            print("[Info] Confirmed: Downloaded file is HDF5 binary data")
                                            if outFilename.endswith('.nc4'):
                                                print("[Info] NetCDF4 file confirmed - compatible with h5dump")
                                        elif chunk.startswith(b'CDF'):
                                            print("[Info] Confirmed: Downloaded file is NetCDF binary data")
                                            if outFilename.endswith('.nc4'):
                                                print("[Info] NetCDF4 file confirmed - compatible with h5dump")
                                            elif outFilename.endswith('.nc'):
                                                print("[Info] NetCDF3 file confirmed")
                                        else:
                                            print(f"[Info] Binary data detected (first 20 bytes): {chunk[:20].hex()}")
                                            if outFilename.endswith('.nc4'):
                                                print("[Info] Assuming NetCDF4 format based on .nc4 extension")
                                        first_chunk_written = True
                                    outFile.write(chunk)
                            
                            downloaded_count += 1
                            download_successful = True
                            break  # Exit the URL attempts loop since we succeeded
                            
                        except requests.exceptions.HTTPError as e:
                            # Handle individual file download errors gracefully
                            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                                print(f"[Warning] 404 Not Found for {attempt_url} - trying next format")
                                continue
                            else:
                                print(f"[Error] HTTP error for {attempt_url}: {e}")
                                continue
                        except Exception as e:
                            print(f"[Error] Unexpected error for {attempt_url}: {e}")
                            continue
                    
                    if not download_successful:
                        print("[Error] All URL formats failed for this file - skipping")
                
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


