#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import os
from osgeo import gdal,ogr,osr

""" Module for implementing the GageLocFilter. This is a straightforward filter that takes 
    a geospatial extent specified as a latmin,latmax,lonmin,lonmax tuple and returns the IDs
    of gages that fall within that extent. The filter uses a gage loc shapefile that is packaged 
    along with the Filter python package. By default the resulting gage_ids will be returned as 
    a single comma separated string. If we desire each gage_id to be returned as a distinct value,
    set the optional parallelize parameter to true
"""

class GageLocFilter(GeoEDFPlugin):
    __optional_params = ['parallelize']
    __required_params = ['extent']

    # path to GageLoc shapefile that is installed as part of this filter package
    __gage_loc_shapefile = '/usr/local/data/GageLoc.shp'

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for GageLocFilter not provided' % param)

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

        gage_ids = None
        
        # semantic checks on params
        # Check (1) exactly four values need to be provided in extent
        extent_vals = list(map((lambda val: float(val)),self.extent.split(',')))

        if len(extent_vals) != 4:
            raise GeoEDFError('GageLocFilter requires a string of four floating point numbers as the extent')

        # Check (2) that lat and lon pairs are in the right order
        latmin = extent_vals[0]
        latmax = extent_vals[1]
        lonmin = extent_vals[2]
        lonmax = extent_vals[3]

        if latmin > latmax:
            raise GeoEDFError('please check the ordering of the latmin and latmax extents')
        
        if lonmin > lonmax:
            raise GeoEDFError('please check the ordering of the lonmin and lonmax extents')
            
        # load up the Gage Loc shapefile; we have already reprojected it to EPSG:4326
        driver = ogr.GetDriverByName('ESRI Shapefile')
        inDataset = driver.Open(self.__gage_loc_shapefile, 0)
        if inDataset is None:
            raise GeoEDFError('Error opening GageLoc shapefile in GageLocFilter')
        inLayer = inDataset.GetLayer()

        # find all features/points/gages that fall within the provided extent
        try:
            # loop through features in the layer and retrieve point geometry and X,Y coords
            for feature in inLayer:
                geom = feature.GetGeometryRef()

                # check if lon and lat fall within extents
                point_lon = geom.GetX()
                point_lat = geom.GetY()

                if lonmin <= point_lon <= lonmax:
                    if latmin <= point_lat <= latmax:
                        # fetch the gage ID from SOURCE_FEA field
                        gage_id = feature.GetField("SOURCE_FEA")
                        
                        # if not parallelized, append to gage_ids string, else
                        # append to values
                        if self.parallelize is not None:
                            self.values.append(gage_id)
                        else:
                            if gage_ids is None:
                                gage_ids = '%s' % gage_id
                            else:
                                gage_ids += ',%s' % gage_id
        except:
            raise GeoEDFError("Error finding gages in provided extent in GageLocFilter")

        # if not parallelized, return single value in values array
        if gage_ids is not None:
            self.values.append(gage_ids)
                        


