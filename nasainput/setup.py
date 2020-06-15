from setuptools import setup, find_packages

setup(name='nasaconnector',
      version='0.1',
      description='Connector for accessing NASA DAAC datasets)',
      url='http://github.com/geoedf/nasainput',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['requests'],
      zip_safe=False)
