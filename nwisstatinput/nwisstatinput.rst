NWISStatInput
===========

.. py:class:: GeoEDF.connector.input.NWISStatInput()

    Module for implementing the NWISStatInput. This plugin takes a start and end year pair, a two char state 
    code, and a variable (numeric parameterCd) as input. The plugin uses the Hydrofunctions API to fetch the 
    annual mean value for this variable for all stations in this state and for the given year range. The plugin
    outputs a csv file with year, station ID, and mean value in each row.

   .. py:attribute:: start_yr (int,required)

   Integer variable for the start year. 

   .. py:attribute:: end_yr (int,required)

   Integer variable for the end year. 
   
   .. py:attribute:: state (str,required)

   This is a two character code that corresponds to the US state. 
   
   .. py:attribute:: variable (str,required)
   
   Numeric parameterCd for the Hydrofunctions API.
   
