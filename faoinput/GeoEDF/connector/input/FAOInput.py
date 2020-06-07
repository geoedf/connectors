from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import requests
import os
import zipfile

class FAOInput(GeoEDFPlugin):

    url = "http://fenixservices.fao.org/faostat/static/bulkdownloads/datasets_E.json"
    # no optional params yet, but keep around for future extension
    __optional_params = []
    __required_params = ['dataset_names']

    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFInput super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for FAOInput not provided' % param)

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
        # call functions from this module
        try:
            link_request = requests.get(self.url)
            fao_request = link_request.json()

            json_datasets = fao_request['Datasets']
            final_data = json_datasets['Dataset']

            for dataset_name in self.dataset_names:
                for dataset in final_data:
                    if dataset['DatasetName'] == dataset_name:
                        res = requests.get(url=dataset['FileLocation'], stream=True)

                        out_path = '%s/%s' % (self.target_path,dataset_name)
                        with open(out_path,'wb') as out_file:
                            for chunk in res.iter_content(chunk_size=1024*1024):
                                out_file.write(chunk)

                        with zipfile.ZipFile(self.target_path + '/' + dataset_name, 'r') as zip_ref:
                            zip_ref.extractall(self.target_path)

                        if os.path.exists(self.target_path + '/' + dataset_name):
                            os.remove(self.target_path + '/' + dataset_name)
        except GeoEDFError:
            raise
