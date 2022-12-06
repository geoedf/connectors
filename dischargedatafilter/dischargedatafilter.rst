DischargeDataFilter
===========

.. py:class:: GeoEDF.connector.input.DischargeDataFilter()

  Module for implementing the DischargeDataFilter. This filter takes a comma separated list of Gage IDs,
  a start and end date, and a coverage % value. The filter uses the Hydrofunctions API to fetch discharge 
  data for this date range and only retains those stations that have atleast coverage % availability wrt 
  the maximum number of days that data is available for among these Gages.

   .. py:attribute:: start (str,required)

   Start date in the format '%m/%d/%Y'.

   .. py:attribute:: end (str,required)
   
   End date in the format '%m/%d/%Y'.
   
   .. py:attribute:: gages (str,required)
   
   Comma separated list of gage IDs. 

   .. py:attribute:: cutoff (int,required)
   
   The cutoff percentage must be an integer value between 1 and 100. 
