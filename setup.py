#from distutils.core import setup
from setuptools import setup
import os 


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='S3Fdw',
    version='0.3.0',
    author='Alexander Goldstein',
    author_email='alexg@eligoenergy.com',
    packages=['s3fdw'],
    url='https://github.com/vickyphang/s3csv_fdw',
    license='LICENSE.txt',
    description='Postgresql Foregin Data Wrapper mapping Amazon S3',
    install_requires=["boto3"],
)
