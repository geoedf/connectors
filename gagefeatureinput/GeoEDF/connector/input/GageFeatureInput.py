#!/usr/bin/env python
# -*- coding: utf-8 -*-

from geoedfframework.utils.GeoEDFError import GeoEDFError
from geoedfframework.GeoEDFPlugin import GeoEDFPlugin

import pandas as pd
import geopandas as gpd
import requests
import hydrofunctions as hf
from osgeo import ogr

import os
import zipfile

""" Module for implementing the Gage feature input connector plugin. This plugin will retrieve data 
    from the StreamCat database and produce a CSV file with watershed characteristics. The plugin 
    takes a comma separated list of gage IDs as input. 
"""

class GageFeatureInput(GeoEDFPlugin):

    # auth is also required by GageFeatureInput
    __optional_params = []
    __required_params = ['gages']

    # path to GageLoc shapefile that is installed as part of this filter package
    __gage_loc_shapefile = '/usr/local/data/GageLoc.shp'

    # path to HUC2 regions shapefile that is installed as part of this filter package
    __huc2_shapefile = '/usr/local/data/HUC2.shp'

    # StreamCat files that need to be downloaded
    # the regionID suffix is added later
    __streamcat_files = ['Elevation','Dams','NLCD2011','STATSGO_Set2','RoadDensity','WetIndx','STATSGO_Set1','GeoChemPhys3','ImperviousSurfaces2011']

    # dictionary mapping streamcat file to variable(s)
    __streamcat_var = {}
    __streamcat_var['Elevation'] = ['ElevWs']
    __streamcat_var['Dams'] = ['DamDensWs']
    __streamcat_var['NLCD2011'] = ['PctConif2011Ws','PctDecid2011Ws','PctMxtFst2011Ws','PctUrbHi2011Ws','PctUrbLo2011Ws','PctUrbOp2011Ws']
    __streamcat_var['STATSGO_Set2'] = ['PermWs']
    __streamcat_var['RoadDensity'] = ['RdDensWs']
    __streamcat_var['WetIndx'] = ['WetIndexWs']
    __streamcat_var['STATSGO_Set1'] = ['SandWs','ClayWs']
    __streamcat_var['GeoChemPhys3'] = ['HydrlCondWs']
    __streamcat_var['ImperviousSurfaces2011'] = ['PctImp2011Ws']
    
    # we use just kwargs since we need to be able to process the list of attributes
    # and their values to create the dependency graph in the GeoEDFInput super class
    def __init__(self, **kwargs):

        # list to hold all the parameter names; will be accessed in super to 
        # construct dependency graph
        self.provided_params = self.__required_params + self.__optional_params

        # check that all required params have been provided
        for param in self.__required_params:
            if param not in kwargs:
                raise GeoEDFError('Required parameter %s for GageFeatureInput not provided' % param)

        # set all required parameters
        for key in self.__required_params:
            setattr(self,key,kwargs.get(key))

        # set optional parameters
        for key in self.__optional_params:
            # if key not provided in optional arguments, defaults value to None
            setattr(self,key,kwargs.get(key,None))
            
        # class super class init
        super().__init__()

    # helper function to download a file given URL
    def download_file(self,filename):

        # base URL
        url_prefix = 'https://gaftp.epa.gov/epadatacommons/ORD/NHDPlusLandscapeAttributes/StreamCat/HydroRegions/'

        download_url = url_prefix + filename

        try: 
            res = requests.get(download_url,stream=True,verify=False)
            res.raise_for_status()

            outPath = '%s/%s' % (self.target_path,filename)
        
            with open(outPath,'wb') as outFile:
                for chunk in res.iter_content(chunk_size=1024*1024):
                    outFile.write(chunk)

        except:
            raise GeoEDFError('Error downloading StreamCat file %s in GageFeatureInput' % filename)

        return True

    # each Input plugin needs to implement this method
    # if error, raise exception; if not, return True
    def get(self):

        # create a list of gage IDs
        gage_ids = self.gages.split(',')

        # initialize a data frame keyed by gage_ids
        gages_data = {}

        # create a dict of HUC_2 regions with geometries
        # this will be used to check which region a gage is located in
        # also avoids re-reading the shapefile each time
        
        driver = ogr.GetDriverByName('ESRI Shapefile')
        inDataset = driver.Open(self.__huc2_shapefile, 0)
        if inDataset is None:
            raise GeoEDFError('Error opening HUC2 regions shapefile in GageFeatureInput')
        inLayer = inDataset.GetLayer()

        # get discharge area, lat-lon, datum for each gage from NWIS
        for gage_id in gage_ids:

            gage_data = {}
                
            try:
                gage_site_info = hf.site_file(gage_id)

                gage_data['Lat'] = gage_site_info.table['dec_lat_va'].max()
                gage_data['Long'] = gage_site_info.table['dec_long_va'].max()

                gage_data['Datum'] = gage_site_info.table['alt_va'].max()
                gage_data['Discharge_Area'] = gage_site_info.table['drain_area_va'].max()

            except:
                # fail silently and continue
                print('error fetching site info for gage: %s' % gage_id)
                continue

            # find huc_2 region ID for this gage
            # initialize
            gage_data['huc2'] = None

            # create a point geometry for the gage location so we can check intersection
            gage_loc = ogr.Geometry(ogr.wkbPoint)
            gage_loc.AddPoint(float(gage_data['Long']),float(gage_data['Lat']))
            
            # loop through features in layer to determine containing HUC
            for feature in inLayer:
                geom = feature.GetGeometryRef()
                if geom.Contains(gage_loc):
                    gage_data['huc2'] = feature.GetField('huc2')
                    break
            # reset for next round
            inLayer.ResetReading()
            
            gages_data[gage_id] = gage_data

        # convert the gage feature data dict so far into a DataFrame
        gage_feat_df = pd.DataFrame.from_dict(gages_data,orient='index')
        gage_feat_df.index.name = 'Gage_Number2'

        # distinct HUC regions that the gages fall into
        gage_regions = list(set(gage_feat_df['huc2']))

        # download CSVs for the HUC2 regions from StreamCat
        for huc_region in gage_regions:
            # loop through StreamCat files, constructing filename for region
            for streamcat_file in self.__streamcat_files:
                region_streamcat_file = '%s_Region%s.zip' % (streamcat_file,huc_region)
                self.download_file(region_streamcat_file)

                #unzip this file
                region_streamcat_file = '%s/%s_Region%s.zip' % (self.target_path,streamcat_file,huc_region)
                with zipfile.ZipFile(region_streamcat_file,"r") as zip_ref:
                    zip_ref.extractall(self.target_path)

       # get FLComID for each gage
        # read gage loc shapefile using GeoPandas
        gage_loc_df = gpd.read_file(self.__gage_loc_shapefile)
        gage_loc_df.index = gage_loc_df.SOURCE_FEA

        # first merge gage data with gage loc shapefile
        # FLComID will be the new merge key
        gage_feat_df = pd.merge(gage_feat_df,gage_loc_df,how='inner',left_index=True,right_index=True)

        # filter out columns
        keep_col = ['Gage_Number2','Lat','Long','Drainage_Area','Datum','FLComID']
        gage_feat_df = gage_feat_df[keep_col]

        # set index now to FLComID
        gage_feat_df.index = gage_feat_df.FLComID

        # loop through downloaded StreamCat files and merge in
        for huc_region in gage_regions:
            # loop through StreamCat files, constructing filename for region
            for streamcat_file in self.__streamcat_files:
                region_streamcat_file = '%s/%s_Region%s.csv' % (self.target_path,streamcat_file,huc_region)

                gage_var = pd.read_csv(region_streamcat_file)
                gage_var.index = gage_var.COMID

                gage_feat_df = pd.merge(gage_feat_df,gage_var,how='inner',left_index=True,right_index=True)

                keep_col += self.__streamcat_var(streamcat_file)

                gage_feat_df = gage_feat_df[keep_col]
                

        # clean up all temporary files in target path before writing out the dataframe
        for file_or_dir in os.listdir(self.target_path):
            os.remove('%s/%s' % (self.target_path,file_or_dir))

        # write out dataframe to csv
        res_file = '%s/gages.csv' % self.target_path

        gage_feat_df.to_csv(res_file)

                

                
        

                    
                        
             
                        

