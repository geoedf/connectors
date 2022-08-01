#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import os
from osgeo import gdal,ogr,osr
import requests
import json

""" Module for implementing the DamFilter. This is a straightforward filter that takes either
    a shapefile (path) as input or a tuple of latmin,latmax,lonmin,lonmax extents to find 
    all national dams that fall within that extent. The shapefile is reprojected to EPSG:4326 
    to determine the lat-lon extent before querying for dams.
"""

class DamFilter(GeoEDFPlugin):
    __optional_params = ['shapefile','extent']
    __required_params = []

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFConnectorPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for DamFilter not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))
            
        # check if neither of the optional params have been provided
        # note that shapefile takes precedence
        if self.shapefile is None and self.extent is None:
            raise GeoEDFError('Either a shapefile path or extent needs to be provided for DamFilter')
            
        # initialize filter values array
        self.values = []

        # class super class init
        super().__init__()

    # each Filter plugin needs to implement this method
    # if error, raise exception; if not, set values attribute
    # assume this method is called only when all params have been fully instantiated
    def filter(self):

        if self.shapefile is not None:
            # first load up the shapefile (if any) to determine its projection
            driver = ogr.GetDriverByName('ESRI Shapefile')
            inDataset = driver.Open(self.shapefile, 0)
            if inDataset is None:
                raise GeoEDFError('Error opening shapefile %s in DamFilter' % self.shapefile)
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

                self.extent = '%f,%f,%f,%f' % (bottomLeft.GetY(),topRight.GetY(),bottomLeft.GetX(),topRight.GetX())
            
            except:
                raise GeoEDFError("Error occurred when trying to reproject extents in DamFilter")
                
        # at this point self.extent should not be empty
        # parse out extent into lat-lon min and max
        lat_lons = self.extent.split(',')
        if len(lat_lons) != 4:
            raise GeoEDFError('Error determining lat-lon min and max from extents in DamFilter')
            
        lat_min = float(lat_lons[0])
        lat_max = float(lat_lons[1])
        lon_min = float(lat_lons[2])
        lon_max = float(lat_lons[3])
            
        # query for dams list to filter to given extent
        r = requests.get("https://fim.sec.usace.army.mil/ci/fim/getAllEAPStructure")
        damsMetadata = json.loads(r.content)
        for dam in damsMetadata:
            try:
                damID = dam['ID']
                damLat = float(dam['LAT'])
                damLon = float(dam['LON'])
            
                # check to see if dam falls within extent
                if lat_min <= damLat and damLat <= lat_max and lon_min <= damLon and damLon <= lon_max:
                    self.values.append(damID)
            except:
                # some error parsing dam metadata, continue 
                continue
