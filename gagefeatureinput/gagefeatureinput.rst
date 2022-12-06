GageFeatureInput
===========

.. py:class:: GeoEDF.connector.input.GageFeatureInput()

Module for implementing the Gage feature input connector plugin. 
This plugin will retrieve data from the StreamCat database and produce a CSV file with watershed characteristics. 
The plugin takes a comma separated list of gage IDs as input. 

   .. py:attribute:: gages (str,required)

   This is a comma separated list of gage IDs. The gage IDs will be used to identify the Streamcat files which are downloaded and merged into a CSV file.
