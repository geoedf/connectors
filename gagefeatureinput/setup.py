from setuptools import setup, find_packages

setup(name='gagefeatureinput',
      version='0.2',
      description='Connector for accessing and merging gage feature data from StreamCat database',
      url='http://github.com/geoedf/connectors',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['pandas','geopandas','requests','hydrofunctions'],
      data_files=[('data',['data/GageLoc.shp','data/GageLoc.dbf','data/GageLoc.prj','data/GageLoc.shx','data/HUC2.shp','data/HUC2.dbf','data/HUC2.prj','data/HUC2.shx'])],
      zip_safe=False)
