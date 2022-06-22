from setuptools import setup, find_packages

setup(name='ghcndinput',
      version='0.2',
      description='Connector for accessing NOAA NCDC GHCND meterological datasets',
      url='http://github.com/geoedf/connectors',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['cdo-api-py','pandas','requests'],
      zip_safe=False)
