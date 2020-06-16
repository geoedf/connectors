#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

""" Module for implementing the PathFilter. This supports an arbitrary string pattern 
    containing variable names to be instantiated by other filters. The pattern can also 
    contain wildcards that will be instantiated based on the connector input. This is a 
    pre filter.
"""

class PathFilter(GeoEDFPlugin):
    # no optional parameters; keep here for future extension
    __optional_params = []
    __required_params = ['pattern']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFConnectorPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for PathFilter not provided' % param)

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
    # if error, raise exception; if not, return value
    # assume this method is called only when all params have been fully instantiated
    def filter(self):
        # collect value
        self.values.append(self.pattern)
