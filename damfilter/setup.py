from setuptools import setup, find_packages

setup(name='damfilter',
      version='0.1',
      description='Filter for returning the IDs of dams that fall within the given extent',
      url='http://github.com/geoedf/damfilter',
      author='Rajesh Kalyanam',
      author_email='rkalyanapurdue@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False)
