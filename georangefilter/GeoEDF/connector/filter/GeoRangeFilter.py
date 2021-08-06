#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import functools
import itertools

""" Module for implementing the GeoRangeFilter. This filter expects a comma separated xmin,xmax,ymin,ymax 
    of lat-lon values. The filter produces strings in the form N<lat>W<lon> or S<lat>E<lon> so that there 
    are no negative integers
    Note: floor is used on the min and ceil is used on the max to convert to integer
"""

class GeoRangeFilter(GeoEDFPlugin):
    __optional_params = []
    __required_params = ['extent']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFConnectorPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for GeoRangeFilter not provided' % param)

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

        # semantic checks on params
        # Check (1) exactly four values need to be provided in extent
        extent_vals = list(map((lambda val: int(float(val))),self.extent.split(',')))

        if len(extent_vals) != 4:
            raise GeoEDFError('GeoRangeFilter requires a latmin,latmax,lonmin,lonmax string as the extent')

        # Check (2) that lat and lon pairs are in the right order
        self.latmin = extent_vals[0]
        self.latmax = extent_vals[1]
        self.lonmin = extent_vals[2]
        self.lonmax = extent_vals[3]

        if self.latmin > self.latmax:
            raise GeoEDFError('extent[0] and extent[1] need to be the latmin and latmax; please check the ordering')
        
        if self.lonmin > self.lonmax:
            raise GeoEDFError('extent[2] and extent[3] need to be the lonmin and lonmax; please check the ordering')

        try:
            # first produce all intermediate values for lat and lon pairs
            # increment max by 1 since int(float()) returns floor
            if self.latmax <= 0:
                # latmin is also < 0 since we've checked ordering
                # we take abs value, flip for right range, and produce S#
                lat_range = list(range(abs(self.latmax),abs(self.latmin)+2))
                lat_vals = list(map((lambda lat_val: 's%d' % lat_val),lat_range))
            else: #latmax is > 0
                if self.latmin < 0:
                    # need to split into two ranges; upto 0 and then > 0
                    lat_range1 = list(range(0,abs(self.latmin)+2))
                    lat_vals = list(map((lambda lat_val: 's%d' % lat_val),lat_range1))

                    lat_range2 = list(range(0,self.latmax+2))
                    lat_vals += list(map((lambda lat_val: 'n%d' % lat_val),lat_range2))
                else: #latmin is >= 0
                    lat_range = list(range(self.latmin,self.latmax+2))
                    lat_vals = list(map((lambda lat_val: 'n%d' % lat_val),lat_range))

            # process lon values
            if self.lonmax <= 0:
                # lonmin is also < 0 since we've checked ordering
                # we take abs value, flip for right range, and produce S#
                lon_range = list(range(abs(self.lonmax),abs(self.lonmin)+2))
                lon_vals = list(map((lambda lon_val: 'w%03d' % lon_val),lon_range))
            else: #lonmax is > 0
                if self.lonmin < 0:
                    # need to split into two ranges; upto 0 and then > 0
                    lon_range1 = list(range(0,abs(self.lonmin)+2))
                    lon_vals = list(map((lambda lon_val: 'w%03d' % lon_val),lon_range1))

                    lon_range2 = list(range(0,self.lonmax+2))
                    lon_vals += list(map((lambda lon_val: 'e%03d' % lon_val),lon_range2))
                else: #lonmin is >= 0
                    lon_range = list(range(self.lonmin,self.lonmax+2))
                    lon_vals = list(map((lambda lon_val: 'e%03d' % lon_val),lon_range))

            # concatenate the lat and lon vals to produce a single string
            for lat_val in lat_vals:
                for lon_val in lon_vals:
                    self.values.append(lat_val+lon_val)
                
        except:
            raise GeoEDFError('Unknown error occurred when attempting to construct filter values')

