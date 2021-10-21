#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

from cdo_api_py import Client
import pandas as pd

""" Module for implementing the NOAAStationFilter. This filter expects a comma separated N,S,E,W 
    lat-lon values and a date range in mm/dd/YYYY format. The filter produces a comma separated list of
    station IDs for stations that fall within these spatial bounds and have data for the given date range.
    Date range is required since the default date range is 1970-2012.
"""

class NOAAStationFilter(GeoEDFPlugin):
    __optional_params = []
    __required_params = ['extent','token','start_date','end_date']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for NOAAStationFilter not provided' % param)

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
        extent_vals = list(map((lambda val: float(val)),self.extent.split(',')))

        if len(extent_vals) != 4:
            raise GeoEDFError('NOAAStationFilter requires a N,S,E,W string of floating point numbers as the extent')

        # Check (2) that lat and lon pairs are in the right order
        north = extent_vals[0]
        south = extent_vals[1]
        east = extent_vals[2]
        west = extent_vals[3]

        if south > north:
            raise GeoEDFError('please check the ordering of the south and north extents')
        
        if west > east:
            raise GeoEDFError('please check the ordering of the east and west extents')
            
        # passed semantic checks, prepare dict of extents for API
        extent_dict = {"north": north, "south": south, "east": east, "west": west}
        
        # process dates
        try:
            startdate = pd.to_datetime(self.start_date,format='%m/%d/%Y')
            enddate = pd.to_datetime(self.end_date,format='%m/%d/%Y')
        except:
            raise GeoEDFError("Error parsing dates provided to NOAAStationFiler, please ensure format is mm/dd/YYYY")
            
        # param checks complete
        try:
            # get a client for NCDC API usage
            cdo_client = Client(self.token, default_units="None", default_limit=1000)

            # we are looking for stations with GHCND data
            #The find_stations function returns the dataframe containing stations' info within the input extent.
            stations = cdo_client.find_stations(
                            datasetid="GHCND",
                            extent=extent_dict,
                            startdate=startdate,
                            enddate=enddate,
                            return_dataframe=True)
            
            # filter to only retain stations which have sufficient data for the date range
            stations_to_drop = []
            # Drop stations without enough observations for the given date range
            for i in range(len(stations.maxdate)):
                # get max and min date of each station
                station_maxdate = pd.to_datetime(stations.maxdate[i],format='%Y-%m-%d')
                station_mindate = pd.to_datetime(stations.mindate[i],format='%Y-%m-%d')
                # check if station's maxdate is earlier than enddate
                if station_maxdate < enddate:
                    stations_to_drop.append(i)
                # check if station's mindate is later than startdate
                if station_mindate > startdate:
                    stations_to_drop.append(i)
                    
            # delete stations without enough time length
            valid_stations = stations.drop(stations.index[stations_to_drop])
            
            # add station IDs to values array
            self.values += list(valid_stations.id)
                
        except:
            raise GeoEDFError('Error occurred when querying NCDC API for stations in NOAAStationFiler')

