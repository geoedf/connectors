from setuptools import setup, find_packages

setup(name='georangefilter',
      version='0.4',
      description='Filter for taking a bottom left, top right lat-lon pair and producing all possible intermediate lat-lon integer values',
      url='http://github.com/geoedf/georangefilter',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False)
