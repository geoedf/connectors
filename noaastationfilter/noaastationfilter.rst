NOAAStationFilter
===========

.. py:class:: GeoEDF.connector.input.NOAAStationFilter()

   Module for implementing the NOAAStationFilter. This filter expects a comma separated N,S,E,W 
   lat-lon values and a date range in mm/dd/YYYY format. The filter produces a comma separated list of
   station IDs for stations that fall within these spatial bounds and have data for the given date range.
   Date range is required since the default date range is 1970-2012.

   .. py:attribute:: extent (str,required)

   Exactly four comma separated values in the order, `north,south,east,west`.

   .. py:attribute:: token (str,required)
   
   This token is to be specified to get a client for NCDC API usage.
   
   .. py:attribute:: start_date (str,required)

   Start date in the format mm/dd/YYYY.

   .. py:attribute:: end_date (str,required)
   
    End date in the format mm/dd/YYYY.
