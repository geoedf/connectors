from setuptools import setup, find_packages

setup(name='NWISStatInput',
      version='0.1',
      description='Input plugin for fetching statewise statistics data for a particular NWIS variable and year range',
      url='http://github.com/geoedf/nwisstatinput',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['pandas','hydrofunctions'],
      zip_safe=False)
