#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import os
import pandas as pd
import hydrofunctions as hf


""" Module for implementing the NWISStatInput. This plugin takes a start and end year pair, a two char state 
    code, and a variable (numeric parameterCd) as input. The plugin uses the Hydrofunctions API to fetch the 
    annual mean value for this variable for all stations in this state and for the given year range. The plugin
    outputs a csv file with year, station ID, and mean value in each row.
"""

class NWISStatInput(GeoEDFPlugin):
    __optional_params = []
    __required_params = ['start_yr','end_yr','state','variable']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for NWISStatInput not provided' % param)

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
    # if error, raise exception; if not, set values attribute
    # assume this method is called only when all params have been fully instantiated
    def get(self):

        # semantic checks on params
        # check (0) that start and end year are numeric
        if not isinstance(self.start_yr,int) or not isinstance(self.end_yr,int):
            raise GeoEDFError('Start and end year parameters need to be integers')
            
        # Check (1) start and end year are in right order
        if self.start_yr > self.end_yr:
            raise GeoEDFError('Start year be later than end year in NWISStatInput')

        # initialize data array
        var_data = []
        
        for year in range(self.start_yr,self.end_yr+1):
            # next query Hydrofunctions for parameter data for the provided state code
            try:
                start_dt = '%d-01-01' % year
                end_dt = '%d-12-31' % year
                # query data for all stations in given state for this year
                state_res = hf.NWIS(stateCd=self.state,start_date=start_dt,end_date=end_dt,parameterCd=self.variable)
                # compute statistics and extract mean
                state_stats = state_res.df().mean().to_dict()
                # keys are station IDs
                for key,val in state_stats.items():
                    #only extract the annual state values
                    if key.endswith('00003'):
                        # construct a new dict record 
                        data = dict()
                        # construct station ID
                        stn_id = 'USGS:%s' % key.split(':')[1]
                        # determine lat-lon for station from metadata
                        state_res_meta = state_res.meta
                        data['lat'] = None
                        data['lon'] = None
                        if stn_id in state_res_meta:
                            if 'siteLatLongSrs' in state_res_meta[stn_id]:
                                if 'latitude' in state_res_meta[stn_id]['siteLatLongSrs']:
                                    data['lat'] = state_res_meta[stn_id]['siteLatLongSrs']['latitude']
                                if 'longitude' in state_res_meta[stn_id]['siteLatLongSrs']:
                                    data['lon'] = state_res_meta[stn_id]['siteLatLongSrs']['longitude']
                        data['year'] = year
                        data['stn'] = stn_id
                        data['value'] = val
                        var_data.append(data)
            except hf.exceptions.HydroNoDataError:
                pass
            except hf.exceptions.HydroUserWarning:
                pass
            except:
                print("Error retrieving data for variable %s in year %d for state %s in NWISStatInput" % (self.variable,year,self.state))
                pass
        try:
            #write out to csv file
            var_df = pd.DataFrame(var_data)
            outfile = '%s/%s_%s.csv' % (self.target_path,self.state,self.variable)
            var_df.to_csv(outfile,index=False)
        except:
            raise GeoEDFError("Error writing out data for variable %s for state %s in NWISStatInput" % (self.variable,self.state))

                        


