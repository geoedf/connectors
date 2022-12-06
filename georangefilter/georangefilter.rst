GeoRangeFilter
===========

.. py:class:: GeoEDF.connector.input.GeoRangeFilter()

    Module for implementing the GeoRangeFilter. This filter expects a comma separated xmin,xmax,ymin,ymax 
    of lat-lon values. The filter produces strings in the form N<lat>W<lon> or S<lat>E<lon> so that there 
    are no negative integers.
    Note: floor is used on the min and ceil is used on the max to convert to integer

   .. py:attribute:: extent (str,required)

   Exactly four comma separated values in the order, `latmin, latmax, lonmin, lonmax`. 
   The filter produces strings in the form N<lat>W<lon> or S<lat>E<lon> so that there 
    are no negative integers.
