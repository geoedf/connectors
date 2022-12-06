GHCNDInput
===========

.. py:class:: GeoEDF.connector.input.GHCNDInput()

   Module for implementing the GHCND input connector plugin. This plugin will retrieve data for 
   five specific meterological parameters for a given station ID and date range. The plugin returns 
   a CSV file for each parameter with data records for each intervening date. The CSV file is named 
   based on the station and parameter. The new NOAA API is used that does not require tokens.

   .. py:attribute:: start_date (str,required)

   This is in the format, '%m/%d/%Y'. This specifies the start range for the date.
   
   .. py:attribute:: end_date (str,required)

   This is in the format, '%m/%d/%Y'. This specifies the end range for the date. 

   .. py:attribute:: station_id (str,required)

   The station id is used to create the API request for the to download the dataset from NOAA.
