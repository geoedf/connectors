from setuptools import setup, find_packages

setup(name='wqpinput',
      version='0.1',
      description='Connector for EPA/USGA Water Quality Portal',
      url='http://github.com/geoedf/connectors',
      author='Jack Smith',
      author_email='smith1106@marshall.edu',
      license='MIT',
      packages=find_packages(),
      install_requires=['requests'],
      zip_safe=False)
