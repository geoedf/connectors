from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import requests
import os
import zipfile

class WQPInput(GeoEDFPlugin):

    base_url = "https://cida.usgs.gov/nldi/comid/"
    # no optional params yet, but keep around for future extension
    __optional_params = []
    __required_params = ['comid']

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

        # REST query for sites within 5 kilometers of feature with specified CONID
        self.url = self.base_url+self.comid+"/navigate/UM/wqp/?distance=5"
        # class super class init
        super().__init__()

    # each Input plugin needs to implement this method
    # if error, raise exception; if not, return True

    def get(self):
        # call functions from this module
        try:
            link_request = requests.get(self.url)
            wqp_request = link_request.json()

            json_results = wqp_request['FeatureCollection']

            for site in json_results:
                site_id = site['identifier']
                site_name = site['name']
                site_uri = site['uri']
                wqp_url = "https://www.waterqualitydata.us/data/Result/search?siteid="+site_id+"&mimeType=csv"
                res = requests.get(url=wqp_url, stream=True)

                out_path = '%s/%s' % (self.target_path,site_id)
                with open(out_path,'wb') as out_file:
                    for chunk in res.iter_content(chunk_size=1024*1024):
                        out_file.write(chunk)

                with zipfile.ZipFile(self.target_path + '/' + site_id, 'r') as zip_ref:
                    zip_ref.extractall(self.target_path)

                if os.path.exists(self.target_path + '/' + site_id):
                    os.remove(self.target_path + '/' + site_id)
        except GeoEDFError:
            raise
