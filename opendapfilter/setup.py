from setuptools import setup, find_packages

setup(name='opendapfilter',
      version='0.1',
      description='Filter for producing direct HTTP URLs for files managed by an OpenDAP server',
      url='http://github.com/geoedf/opendapfilter',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=['requests'],
      zip_safe=False)
