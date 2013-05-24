from setuptools import setup, find_packages

DESCRIPTION = 'Reusable functionality for building distributed workers with trottling.'

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

VERSION = '0.0.1'

setup(
    name='pm-throttling',
    version=VERSION,
    packages=find_packages(),
    author='Tin',
    author_email='iamtin@gmail.com',
    url='https://github.com/Tin/pm-throttling',
    include_package_data=True,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    dependency_links=[
        'https://github.com/downloads/surfly/gevent/gevent-1.0rc2.tar.gz',
    ],
    install_requires=[
        'gevent==1.0rc2',
        'hiredis==0.1.1',
        'redis==2.7.2',
    ],
    platforms=['any'],
)
