#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import os
from osgeo import gdal,ogr,osr

""" Module for implementing the ShpExtentFilter. This is a straightforward filter that takes 
    a shapefile (path) as input and then reprojects to EPSG:4326 and returns the lat-lon extents
    as a tuple (latmin,latmax,lonmin,lonmax).
"""

class ShpExtentFilter(GeoEDFPlugin):
    __optional_params = []
    __required_params = ['shapefile']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFConnectorPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for ShpExtentFilter not provided' % param)

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

        # first load up the shapefile to determine its projection
        driver = ogr.GetDriverByName('ESRI Shapefile')
        inDataset = driver.Open(self.shapefile, 0)
        if inDataset is None:
            raise GeoEDFError('Error opening shapefile %s in ShpExtentFilter' % self.shapefile)
        inLayer = inDataset.GetLayer()
        try:
            inSpatialRef = inLayer.GetSpatialRef()
        except:
            raise GeoEDFError('Error determining projection of input shapefile, cannot fetch extents in lat-lon')

        # construct the desired output projection
        try:
            outSpatialRef = osr.SpatialReference()
            outSpatialRef.ImportFromEPSG(4326)
        except BaseException as e:
            raise GeoEDFError('Error occurred when constructing target projection: %s' % e)

        try:
            # create Coordinate Transformation
            coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

            # get layer extent
            inExtent = inLayer.GetExtent()

            # extent is in the format: xmin,xmax,ymin,ymax

            # construct the point geometry for both bottom left and top right
            # then reproject
            bottomLeft = ogr.Geometry(ogr.wkbPoint)
            bottomLeft.AddPoint(inExtent[0],inExtent[2])

            topRight = ogr.Geometry(ogr.wkbPoint)
            topRight.AddPoint(inExtent[1],inExtent[3])

            bottomLeft.Transform(coordTransform)
            topRight.Transform(coordTransform)

            self.values.append('%f,%f,%f,%f' % (bottomLeft.GetY(),topRight.GetY(),bottomLeft.GetX(),topRight.GetX()))
            
        except:
            raise GeoEDFError("Error occurred when trying to reproject extents")


