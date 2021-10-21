from setuptools import setup, find_packages

setup(name='noaastationfilter',
      version='0.3',
      description='Filter for taking a north-south-east-west extent and returning NOAA station IDs for stations in that boundary',
      url='http://github.com/geoedf/noaastationfilter',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['cdo-api-py','pandas'],
      zip_safe=False)
