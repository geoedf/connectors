#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import os
import cdsapi
import shutil

""" Module for implementing the era5 input connector plugin. This plugin will make a api call via the
    cdsapi. The api structure has been prebuilt but requires several inputs, including a user id
    and api key pair. The rest of the input completes the api build. The downloaded file is unzipped 
    and the nc files are the outputs that remain.
"""

class Era5Input(GeoEDFPlugin):

    __optional_params = ['dataset','format','region','origin','variable','time_aggregation','horizontal_aggregation','year','version']
    __required_params = ['uid','api_key']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFInput super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for era5 not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))

        # class super class init
        super().__init__()

    # each Input plugin needs to implement this method
    # if error, raise exception; if not, return True
    def get(self):
        # Storing the contents of the config file 
        config_file = "url: https://cds.climate.copernicus.eu/api/v2\nkey: " +self.uid + ":" + self.api_key +"\nverify: 0\n"
        # Writing the config file in the target_path location
        f = open(self.target_path+"/.cdsapirc", "w")
        f.write(config_file)
        f.close()
        # Changing the cdsapi configuration file location
        os.environ['CDSAPI_RC'] = self.target_path +"/.cdsapirc"
        # Making the api call
        try:
            download_path = self.target_path + "/download.zip" 
            c = cdsapi.Client()
            c.verify = False
            c.retrieve(    
                self.dataset,   
                 {        
                    'format': self.format,        
                    'region': self.region,        
                    'origin': self.origin,       
                    'variable': self.variable,        
                    'time_aggregation': self.time_aggregation,        
                    'horizontal_aggregation': self.horizontal_aggregation,        
                    'year': self.year,       
                    'version': self.version,    
                },   
                 download_path)
        except:
            raise GeoEDFError("The UID/API Key Pair was incorrect or the CDS servers are down")
        
        # Unpacking the downloaded file
        try:
                shutil.unpack_archive(download_path, self.target_path)
        except:
            raise GeoEDFError("Could not unzip downloaded files")
        
        # Deleting the unnecessary files to clean the output directory.
        try:
            os.remove(self.target_path+"/.cdsapirc")
            os.remove(download_path)
        except:
            raise GeoEDFError("Could not clean the output directory")
        
        
        return True
            
        
            