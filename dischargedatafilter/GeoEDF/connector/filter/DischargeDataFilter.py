#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import os
import pandas as pd
import hydrofunctions as hf
import numpy as np
import math


""" Module for implementing the DischargeDataFilter. This filter takes a comma separated list of Gage IDs,
    a start and end date, and a coverage % value. The filter uses the Hydrofunctions API to fetch discharge 
    data for this date range and only retains those stations that have atleast coverage % availability wrt 
    the maximum number of days that data is available for among these Gages.
"""

class DischargeDataFilter(GeoEDFPlugin):
    __optional_params = []
    __required_params = ['start','end','gages','cutoff']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for DischargeDataFilter not provided' % param)

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

        # first transform comma separated gage IDs into a list of strings
        gage_ids = self.gages.rstrip().split(',')

        # since HF cannot handle a large number of station IDs, split into chunks of 100
        num_split = math.ceil(len(gage_ids)/100)

        gage_id_chunks = np.array_split(gage_ids,num_split)
        
        # semantic checks on params
        # Check (1) start and end date are dates and in right order
        try:
            start_date = pd.to_datetime(self.start,format='%m/%d/%Y')
            end_date = pd.to_datetime(self.end,format='%m/%d/%Y')
        except ValueError as e:
            raise GeoEDFError('Invalid values provided for start or end date to DischargeDateFilter : %s' % e)
        except:
            raise GeoEDFError('Invalid values provided for start or end date to DischargeDataFilter')

        if start_date > end_date:
            raise GeoEDFError('Start date cannot be later than end date in DischargeFilter')

        # make sure cutoff is an integer < 100
        try:
            self.cutoff = int(self.cutoff)
            if self.cutoff < 1 or self.cutoff > 100:
                raise GeoEDFError('Cutoff parameter in DischargeDataFilter must be an integer between 1 and 100')
        except:
            raise GeoEDFError('Cutoff parameter in DischargeDataFilter must be an integer between 1 and 100')

        # next query Hydrofunctions for discharge data for the provided gages
        # 00060 is discharge parameter
        try:
            # process each chunk separately and merge the resulting dataframes
            # discharges holds the merged DF
            discharges = None
            for gage_chunk in gage_id_chunks:
                chunk_data = hf.NWIS(list(gage_chunk),'dv',start_date=start_date.strftime('%Y-%m-%d'),end_date=end_date.strftime('%Y-%m-%d'),parameterCd='00060')
                if discharges is None:
                    discharges = chunk_data.df()
                else:
                    # simple merge
                    discharges = discharges.merge(chunk_data.df(),how='outer',left_index=True,right_index=True)
            
            # get the statistics of retrieved data, we are looking for count
            # in order to filter by coverage %
            stn_data = discharges.describe()

            # maximum data available
            max_count = stn_data.loc['count'].max()

            # cutoff number of days
            count_cutoff = (max_count * self.cutoff)/100

            # filter by availability
            keep_stn = (stn_data.loc['count'] >= count_cutoff)

            valid_stns = keep_stn[keep_stn].index.to_list()

            # clean up station IDs since the returned IDs have USGS:####:param format
            filtered_ids = list(map(lambda stn_id: stn_id.split(':')[1],valid_stns))

            # if any remain, set the return value to a comma separated list of these IDs
            if len(filtered_ids) > 0:
                self.values.append(','.join(filtered_ids))
        except:
            raise GeoEDFError("Error retrieving discharge data for gages in DischargeDataFilter")

                        


