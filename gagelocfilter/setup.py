from setuptools import setup, find_packages

setup(name='gagelocfilter',
      version='0.2',
      description='Filter for returning the gage IDs for gages that fall within the provided geo boundary',
      url='http://github.com/geoedf/gagelocfilter',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      data_files=[('data',['data/GageLoc.shp','data/GageLoc.dbf','data/GageLoc.prj','data/GageLoc.shx'])],
      zip_safe=False)
