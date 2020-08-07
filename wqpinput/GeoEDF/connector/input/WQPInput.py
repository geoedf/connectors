from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import requests
import os

class WQPInput(GeoEDFPlugin):

    base_url = "https://www.waterqualitydata.us/data"
    target_path = "data"
    # no optional params yet, but keep around for future extension
    __optional_params = ['start_date','end_date']
    __required_params = ['site_id']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFInput super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for WQPInput not provided' % param)

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
    # if error, raise exception; if not, return True

    def get(self):
        if (self.start_date == None):
            self.start_date = ''
        if (self.end_date == None):
            self.end_date = '05-01-2020'

        wqp_url = self.base_url+"/Result/search?siteid="+self.site_id+"&StartDateLo="+self.start_date+"&StartDateHi="+self.end_date+"&mimeType=csv"

        try:
            results = requests.get(url=wqp_url, stream=True)
            out_path = '%s/%s.csv' % (self.target_path,self.site_id)
            with open(out_path,'wb') as out_file:
                for chunk in results.iter_content(chunk_size=1024*1024):
                    out_file.write(chunk)
        except GeoEDFError:
            raise