#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import pandas as pd
import requests
from cdo_api_py import Client

""" Module for implementing the GHCND input connector plugin. This plugin will retrieve data for 
    five specific meterological parameters for a given station ID and date range. The plugin returns 
    a CSV file for each parameter with data records for each intervening date. The CSV file is named 
    based on the station and parameter. The new NOAA API is used that does not require tokens.
"""

class GHCNDInput(GeoEDFPlugin):

    # auth is also required by GHCNDInput
    __optional_params = []
    __required_params = ['start_date','end_date','station_id']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFInput super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for GHCNDInput not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))
            
        # set the hardcoded set of meterological params
        # can possibly generalize to fetch any list of params in the future
        self.met_params = ['SNOW','SNWD','TMAX','TMIN','PRCP']

        # class super class init
        super().__init__()

    # each Input plugin needs to implement this method
    # if error, raise exception; if not, return True
    def get(self):

        # semantic checking of parameters
        # process dates
        try:
            startdate = pd.to_datetime(self.start_date,format='%m/%d/%Y')
            enddate = pd.to_datetime(self.end_date,format='%m/%d/%Y')
        except:
            raise GeoEDFError("Error parsing dates provided to GHCNDInput, please ensure format is mm/dd/YYYY")
            
        # param checks complete
        try:
            # parse out station_id
            station_id = self.station_id.split(':')[1]
            
            # use new API
            # construct URL
            station_data_url = "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&dataTypes=SNOW,PRCP,SNWD,TMIN,TMAX&stations=%s&startDate=2010-08-30&endDate=2020-09-30&format=json" % station_id
            
            res = requests.get(station_data_url)
            res.raise_for_status()
            
            station_data = pd.read_json(res.text)

            # first reindex data by date
            station_data.set_index(pd.to_datetime(station_data['DATE']), inplace=True)

        except:
            print("Error fetching GHCND data for station %s in GHCNDInput" % self.station_id)
            return
            
        # for each of the five params, first check if we have sufficient data
        # then write out to CSV file
        for met_param in self.met_params:
            try:
                if met_param == 'PRCP' or met_param == 'TMAX' or met_param == 'TMIN':
                    if met_param in station_data:
                        num_nan = station_data[met_param].isna().sum()
                        if num_nan < 365: # then we are fine
                            # write out csv file
                            param_csvfile = '%s/%s_%s.csv' % (self.target_path,self.station_id,met_param)
                            param_data = station_data.filter([met_param])
                            param_data.to_csv(param_csvfile)
                # check for snow params
                if met_param == 'SNOW' or met_param == 'SNWD':
                    if met_param in station_data:
                        num_nan = station_data[met_param].isna().sum()
                        if num_nan < 3500:
                            # write out csv file
                            param_csvfile = '%s/%s_%s.csv' % (self.target_path,self.station_id,met_param)
                            param_data = station_data.filter([met_param])
                            param_data.to_csv(param_csvfile)
            except:
                raise GeoEDFError("Error occurred while writing out %s data to CSV for station %s in GHCNDInput" % (met_param,self.station_id))
                    
                        
             
                        

