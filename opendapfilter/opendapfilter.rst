OpenDAPFilter
===========

.. py:class:: GeoEDF.connector.input.OpenDAPFilter()

   Module for implementing the OpenDAP Filter. This filter takes a OpenDAP URL as input 
   and parses the catalog entry at that URL to identify all the dataset entries.
   It returns a list of direct HTTP access URLs for those files so that they can be fetched 
   via an Input connector.

   .. py:attribute:: opendap_url (str,required)

   OpenDAP URL to parse the catalog entry at that point. 
