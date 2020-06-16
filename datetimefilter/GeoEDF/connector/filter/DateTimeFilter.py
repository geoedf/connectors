#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import pandas as pd

""" Module for implementing the DateTimeFilter. This supports a date time string pattern 
    that specifies the kinds of values that will be returned from the filter. The user 
    also provides a start date (in mm/dd/yyyy format) with optional timestamp as hh:mm:ss; 
    and an optional end date. If an end date is provided, it is assumed that the user wants 
    to generate all dates between the start and end subject to a period parameter. The period 
    is a number followed by a character such as D,M,Y etc. for day, month and year. E.g. 2M is 
    a period of 2 months. The DateTimeFilter is a pre filter that can be used to generate 
    a string representation of all intervening dates.
"""

class DateTimeFilter(GeoEDFPlugin):
    # has_time is Boolean, False by default
    # if end is provided, period also needs to be provided
    __optional_params = ['end','period','has_time']
    __required_params = ['pattern','start']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFConnectorPlugin super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for DateTimeFilter not provided' % param)

        # specific check for conditionally required params
        # if end is provided, also need a period
        if 'end' in kwargs:
            if 'period' not in kwargs:
                raise GeoEDFError('Period is required for DateTimeFilter when both start and end are provided.')

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))
            # if has_time is not provided, set to False
            if key == 'has_time':
                if self.has_time is None:
                    self.has_time = False

        # initialize filter values array
        self.values = []

        # class super class init
        super().__init__()

    # each Filter plugin needs to implement this method
    # if error, raise exception; if not, set values attribute
    # assume this method is called only when all params have been fully instantiated
    def filter(self):

        # convert the start and end dates from strings to Pandas DateTime
        try:
            # check if time is present
            if self.has_time:
                start_date = pd.to_datetime(self.start,format='%m/%d/%Y %H:%M:%S')
            else:
                start_date = pd.to_datetime(self.start,format='%m/%d/%Y')
            if self.end is not None:
                if self.has_time:
                    end_date = pd.to_datetime(self.end,format='%m/%d/%Y %H:%M:%S')
                else:
                    end_date = pd.to_datetime(self.end,format='%m/%d/%Y')
        except ValueError as e:
            raise GeoEDFError('Invalid values provided for start or end date to DateTimeFilter : %s' % e)
        except:
            raise GeoEDFError('Invalid values provided for start or end date to DateTimeFilter')

        # use the period to generate all intervening dates
        try:
            if self.end is not None:
                all_dates = pd.date_range(start=start_date,end=end_date,freq=self.period)
            else:
                all_dates = [start_date]
            
            # convert back to string using the pattern
            for dt in all_dates:
                self.values.append(dt.strftime(self.pattern))

        except ValueError as e:
            raise GeoEDFError('Error applying DateTimeFilter : %s' % e)
        except:
            raise GeoEDFError('Unknown error applying DateTimeFilter')
