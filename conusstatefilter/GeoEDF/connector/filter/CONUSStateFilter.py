#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import os
from osgeo import gdal,ogr,osr

""" Module for implementing the CONUSStateFilter. This is a straightforward filter that returns two char
    state codes for all states in CONUS
"""

class CONUSStateFilter(GeoEDFPlugin):
    __optional_params = []
    __required_params = []

    # path to Tiger state lines shapefile that is installed as part of this filter package
    __states_shapefile = '/usr/local/data/tl_2021_us_state.shp'

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for CONUSStateFilter not provided' % param)

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

        # set lat-lon limits for CONUS to check if state falls in there
        latmin = 24
        latmax = 50
        lonmin = -125
        lonmax = -65

        # load up the tiger lines shapefile;
        driver = ogr.GetDriverByName('ESRI Shapefile')
        inDataset = driver.Open(self.__states_shapefile, 0)
        if inDataset is None:
            raise GeoEDFError('Error opening Tiger States shapefile in CONUSStateFilter')
        inLayer = inDataset.GetLayer()

        # for each state feature check if it's lat-lon falls in CONUS limits
        try:
            # loop through features in the layer and retrieve state USPS code and lat-lon
            for feature in inLayer:
                state_code = feature.GetField("STUSPS")
                state_lat = float(feature.GetField("INTPTLAT"))
                state_lon = float(feature.GetField("INTPTLON"))
                if latmin < state_lat < latmax:
                    if lonmin < state_lon < lonmax:
                        self.values.append(state_code)
        except:
            raise GeoEDFError("Error processing Tiger states shapefile in CONUSStateFilter")
