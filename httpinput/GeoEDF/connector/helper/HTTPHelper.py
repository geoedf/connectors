#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
import os
import fnmatch
from geoedfframework.utils.GeoEDFError import GeoEDFError
from .HTMLHelper import HTMLHelper

""" Helper module for performing HTTP GET and POST operations.
"""

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
def getFileList(url):
    if '*' in url: #has wildcard
        # first get the base URL to get a listing of files
        partitioned = url.rpartition('/')
        base_url = partitioned[0]
        poss_filename = partitioned[2]
        # naive check whether poss_filename is indeed a file
        if '.' in poss_filename and '*' in poss_filename:
            filename_pattern = poss_filename
            try:
                # get a listing of files from the base_url
                res = requests.get(base_url)
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
                    if fnmatch.fnmatch(actual_filename,filename_pattern):
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
            except requests.exceptions.HTTPError:
                raise GeoEDFError('Error accessing file listing at URL')
            except:
                raise
        else:
            raise GeoEDFError('URL does not point to a file or set of files')
    else:
        return [url]


def getFile(url, path=None): 
    """ download file(s) at url and save to path
	if path is None, save to /tmp
	returns boolean result
    """

    # validate that URL is not null
    if url is None:
        raise GeoEDFError('Null URL provided for getFile')

    # default path to /tmp
    if path is None:
        path = '/tmp'

    try:
        # if there is a wildcard in the URL, we need to process a list of files instead
        if '*' in url:
            fileURLList = getFileList(url)
            for fileURL in fileURLList:
                res = requests.get(fileURL,stream=True)
                res.raise_for_status()
                        
                # get the name of the file to save
                outFilename = getFilename(res,fileURL)
                outPath = '%s/%s' % (path,outFilename.strip('"'))
                with open(outPath,'wb') as outFile:
                    for chunk in res.iter_content(chunk_size=1024*1024):
                        outFile.write(chunk)
            return True
        else: # no wildcard
            res = requests.get(url, stream=True)
            res.raise_for_status()

            # get the name of the file to save
            outFilename = getFilename(res,url)
            outPath = '%s/%s' % (path,outFilename.strip('"'))
            with open(outPath,'wb') as outFile:
                for chunk in res.iter_content(chunk_size=1024*1024):
                    outFile.write(chunk)
            return True

    except GeoEDFError: # known error
        raise
    except requests.exceptions.HTTPError:
        raise
	    
    
