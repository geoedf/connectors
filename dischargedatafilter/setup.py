from setuptools import setup, find_packages

setup(name='dischargedatafilter',
      version='0.1',
      description='Filter for determining which gages have data coverage for dates above a given cutoff percentage',
      url='http://github.com/geoedf/dischargedatafilter',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['requests','pandas','hydrofunctions'],
      zip_safe=False)
