#!/usr/bin/env python3
"""
Implement OAuth support for the NASA Input connector
"""

import requests
from urllib.parse import urlparse, parse_qs
import base64

def implement_oauth_download(original_url, bearer_token=None, username=None, password=None):
    """
    Implement OAuth download flow for USGS OpenDAP servers
    
    Args:
        original_url: The .hdf.dap URL that triggers OAuth redirect
        bearer_token: EarthData bearer token (if available)
        username/password: EarthData credentials for fallback
    """
    
    print(f"Attempting OAuth download for: {original_url}")
    print("="*60)
    
    # Step 1: Make initial request to trigger OAuth redirect
    print("Step 1: Triggering OAuth redirect...")
    try:
        response = requests.get(original_url, allow_redirects=False, timeout=10)
        print(f"Initial response status: {response.status_code}")
        
        if response.status_code == 302:
            oauth_url = response.headers.get('Location')
            print("✅ OAuth redirect detected!")
            print(f"OAuth URL: {oauth_url}")
            
            # Step 2: Parse OAuth URL parameters
            parsed_url = urlparse(oauth_url)
            params = parse_qs(parsed_url.query)
            
            print("\nOAuth Parameters:")
            print(f"  Client ID: {params.get('client_id', ['N/A'])[0]}")
            print(f"  Redirect URI: {params.get('redirect_uri', ['N/A'])[0]}")
            print(f"  State: {params.get('state', ['N/A'])[0][:50]}...")
            
            # Decode state to see original URL
            try:
                state_encoded = params.get('state', [''])[0]
                state_decoded = base64.b64decode(state_encoded + '==').decode('utf-8')  # Add padding
                print(f"  Decoded State (original URL): {state_decoded}")
            except Exception as e:
                print(f"  Could not decode state: {e}")
            
            # Step 3: Try different authentication methods
            return try_oauth_authentication(oauth_url, bearer_token, username, password)
            
        else:
            print(f"❌ No OAuth redirect - got status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in initial request: {e}")
        return False

def try_oauth_authentication(oauth_url, bearer_token=None, username=None, password=None):
    """Try different authentication methods for OAuth URL"""
    
    print("\nStep 2: Attempting OAuth authentication...")
    
    # Method 1: Bearer token
    if bearer_token:
        print("Trying bearer token authentication...")
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'User-Agent': 'GeoEDF-NASAInput/1.0'
        }
        
        try:
            response = requests.get(oauth_url, headers=headers, allow_redirects=True, timeout=10)
            print(f"Bearer token response: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'application/octet-stream' in content_type or 'hdf' in content_type.lower():
                    print("✅ SUCCESS with bearer token!")
                    return True
                else:
                    print(f"Bearer token got response but wrong content type: {content_type}")
            
        except Exception as e:
            print(f"Bearer token error: {e}")
    
    # Method 2: Basic auth with username/password
    if username and password:
        print("Trying basic authentication...")
        try:
            response = requests.get(oauth_url, auth=(username, password), allow_redirects=True, timeout=10)
            print(f"Basic auth response: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'application/octet-stream' in content_type or 'hdf' in content_type.lower():
                    print("✅ SUCCESS with basic auth!")
                    return True
                    
        except Exception as e:
            print(f"Basic auth error: {e}")
    
    # Method 3: Session-based approach (simulating browser)
    print("Trying session-based approach...")
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    if bearer_token:
        session.headers.update({'Authorization': f'Bearer {bearer_token}'})
    
    try:
        response = session.get(oauth_url, allow_redirects=True, timeout=10)
        print(f"Session response: {response.status_code}")
        print(f"Final URL: {response.url}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            print(f"Content-Type: {content_type}")
            
            if 'application/octet-stream' in content_type or 'hdf' in content_type.lower():
                print("✅ SUCCESS with session approach!")
                return True
                
    except Exception as e:
        print(f"Session error: {e}")
    
    print("❌ All authentication methods failed")
    return False

def test_oauth_implementation():
    """Test the OAuth implementation with real URLs"""
    
    # Test URL that we know redirects to OAuth
    test_url = "https://opendap.cr.usgs.gov/opendap/hyrax/DP131/MOTA/MCD15A3H.061/2002.07.16/MCD15A3H.A2002197.h09v07.061.2020077144157.hdf.dap"
    
    # Your bearer token
    bearer_token = "eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6Imp1bmdoYXdvbyIsImV4cCI6MTc1NzYzNTY1MywiaWF0IjoxNzUyNDUxNjUzLCJpc3MiOiJodHRwczovL3Vycy5lYXJ0aGRhdGEubmFzYS5nb3YiLCJpZGVudGl0eV9wcm92aWRlciI6ImVkbF9vcHMiLCJhY3IiOiJlZGwiLCJhc3N1cmFuY2VfbGV2ZWwiOjN9.ELBSZoXPT0AXzmwciVBYXAltdOtj9oAPrRdtZzWIGmmRj-XOnniFsy79HCFXwdc0RAcd0Fh9QBN1NhMx1UvK9plmiXh2NZzHajgj4GDkuMpAhL9IxgKI5kZo8jlRkkpjSZTkuOcTzKsPqWRmz16dlGBHtzzYkonAH6H8mF3IdQ80SRuED1OxErDupU2tzfinbUat2f-rkGdxDVqKB4yzE-gvxNLaY2TIIXXEtEO8CU_BjATwhgCdbyf6aWs9B9OObeKO9IAeL5qa5QdCZ_89jY22m9Ltqb7-D54aWuLjS8thUeB6Nff7Wzk18cbP2If5r56l32-nZCBlFhmaTI9vyw"
    
    print("Testing OAuth Implementation")
    print("="*60)
    
    success = implement_oauth_download(test_url, bearer_token=bearer_token)
    
    if success:
        print("\n🎉 OAuth implementation successful!")
        print("This can be integrated into the NASAHelper.py")
    else:
        print("\n⚠️  OAuth implementation needs refinement")
        print("Manual download with browser session is the current workaround")

if __name__ == "__main__":
    test_oauth_implementation()
