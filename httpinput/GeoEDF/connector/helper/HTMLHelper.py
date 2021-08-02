#!/usr/bin/env python
# -*- coding: utf-8 -*-

from html.parser import HTMLParser

""" Helper module for parsing http listing of files to extract actual file names.
    We assume that the listing consists of href links to the files themselves & 
    simply return an array of href values that have been scraped from the HTML page.
    Follows the NSIDC example here: https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python
"""

class HTMLHelper(HTMLParser):
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
                    else:
                        self.inLink = True
                        self.lasttag = tag
                        self.path = value # most likely a filepath
                    
    def handle_data(self, data):
        # only run when we are inside an <a> tag
        if self.lasttag == 'a' and self.inLink:
            self.pathList.append(self.path)
