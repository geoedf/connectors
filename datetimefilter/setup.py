from setuptools import setup, find_packages

setup(name='datetimefilter',
      version='0.1',
      description='Filter for producing DateTime strings in various formats)',
      url='http://github.com/geoedf/datetimefilter',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['pandas'],
      zip_safe=False)
