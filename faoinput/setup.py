from setuptools import setup, find_packages

setup(name='faoconnector',
      version='0.1',
      description='Connector for U.N. FAO dataset)',
      url='http://github.com/geoedf/faoinput',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['requests'],
      zip_safe=False)
