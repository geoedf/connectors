from setuptools import setup, find_packages

setup(name='httpinput',
      version='0.3',
      description='Connector for accessing files at a given HTTP URL',
      url='http://github.com/geoedf/connectors',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['requests'],
      zip_safe=False)
