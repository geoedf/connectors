from setuptools import setup, find_packages

setup(name='conusstatefilter',
      version='0.1',
      description='Filter for returning list of two char state codes for CONUS',
      url='http://github.com/geoedf/conusstatefilter',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      data_files=[('data',['data/tl_2021_us_state.shp','data/tl_2021_us_state.dbf','data/tl_2021_us_state.prj','data/tl_2021_us_state.shx'])],
      zip_safe=False)
