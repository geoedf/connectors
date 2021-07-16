#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import requests
import os
import xml.etree.ElementTree as ET

""" Module for implementing the OpenDAP Filter. This filter takes a OpenDAP URL as input 
    and parses the catalog entry at that URL to identify all the dataset entries.
    It returns a list of direct HTTP access URLs for those files so that they can be fetched 
    via an Input connector.
"""

class OpenDAPFilter(GeoEDFPlugin):
    __optional_params = []
    __required_params = ['opendap_url']

    # THREDDS namespace
    thredds_ns = '{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}'

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFConnectorPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for OpenDAPFilter not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        # initialize filter values array
        self.values = []

        # class super class init
        super().__init__()

    # each Filter plugin needs to implement this method
    # if error, raise exception; if not, set values attribute
    # assume this method is called only when all params have been fully instantiated
    def filter(self):

        try:
            # construct the catalog URL and attempt to retrieve it using requests

            catalog_url = '%s/catalog.xml' % self.opendap_url

            res = requests.get(catalog_url,stream=True)

            # temporarily save catalog file to directory holding eventual filter output

            outFilename = '%s/catalog.xml' % os.path.dirname(self.target_path)

            with open(outFilename,'wb') as catalogFile:
                for chunk in res.iter_content(chunk_size=1024):
                    catalogFile.write(chunk)

            # parse catalog XML file
            tree = ET.parse(outFilename)

            root = tree.getroot()

            # assuming fixed format and namespaces
            # root > dataset > dataset array > access leaf

            # construct tag keys
            dataset_key = '%sdataset' % self.thredds_ns
            access_key = '%saccess' % self.thredds_ns
            
            for child in root.findall(dataset_key):
                for children in child.findall(dataset_key):
                    for access_child in children.findall(access_key):
                        if access_child.attrib['serviceName'] == 'dap':
                            dataset_path = access_child.attrib['urlPath']
                            filename = os.path.split(dataset_path)[1]
                            # construct direct access URL for NetCDF4 format
                            self.values.append('%s/%s.nc4' % (self.opendap_url,filename))
        except:
            raise GeoEDFError('Unknown error applying OpenDAPFilter')
