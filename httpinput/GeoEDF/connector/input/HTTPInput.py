#!/usr/bin/env python
# -*- coding: utf-8 -*-

from GeoEDF.connector.helper import HTTPHelper
from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

""" Module for implementing the HTTP input connector plugin. 
    Assumes no authentication is required to the server.
    This module will implement the get() method required for all input plugins.
"""

class HTTPInput(GeoEDFPlugin):

    # auth is also required by HTTPInput
    # no optional params yet, but keep around for future extension
    __optional_params = []
    __required_params = ['url']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFInput super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for HTTPInput not provided' % param)

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

        try:
            # download file from the URL
            # target_path is set by the connector on input instantiation
            HTTPHelper.getFile(self.url,self.target_path)
            return True
        except GeoEDFError:
            raise
        except:
            raise

