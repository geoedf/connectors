GageLocFilter
===========

.. py:class:: GeoEDF.connector.input.GageLocFilter()

   Module for implementing the GageLocFilter. This is a straightforward filter that takes 
   a geospatial extent specified as a latmin,latmax,lonmin,lonmax tuple and returns the IDs
   of gages that fall within that extent. The filter uses a gage loc shapefile that is packaged 
   along with the Filter python package. By default the resulting gage_ids will be returned as 
   a single comma separated string. If we desire each gage_id to be returned as a distinct value,
   set the optional parallelize parameter to true.

   .. py:attribute:: extent (str,required)

   Exactly four comma separated values in the order, `latmin, latmax, lonmin, lonmax`. This provides the extent to find all features/points/gages that fall within the provided extent.

   .. py:attribute:: parallelize (boolean,optional)

   If we desire each gage_id to be returned as a distinct value, set the optional parallelize parameter to true.
