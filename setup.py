# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import re
import glob

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


ROOT_PATH = os.path.dirname(
    os.path.realpath(__file__)
)

SOURCE_PATH = os.path.join(
    ROOT_PATH, 'source'
)

RESOURCE_PATH = os.path.join(
    ROOT_PATH, 'resource'
)

README_PATH = os.path.join(ROOT_PATH, 'README.rst')

with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_nuke', '_version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


# Custom commands.
class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


def get_files_from_folder(folder):
    '''Get all files in a folder in resource folder.'''
    plugin_directory = os.path.join(RESOURCE_PATH, folder)
    plugin_data_files = []

    for root, directories, files in os.walk(plugin_directory):
        files_list = []
        if files:
            for filename in files:
                files_list.append(
                    os.path.join(root, filename)
                )

        if files_list:
            destination_folder = root.replace(
                RESOURCE_PATH, 'ftrack_connect_nuke/ftrack_connect_nuke'
            )
            plugin_data_files.append(
                (destination_folder, files_list)
            )

    return plugin_data_files

data_files = []

for child in os.listdir(
    RESOURCE_PATH
):
    if os.path.isdir(os.path.join(RESOURCE_PATH, child)) and child != 'hook':
        data_files += get_files_from_folder(child)

data_files.append(
    (
        'ftrack_connect_nuke/hook',
        glob.glob(os.path.join(RESOURCE_PATH, 'hook', '*.py'))
    )
)

connect_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect/get/1.1.0.zip'
    '#egg=ftrack-connect-1.1.0'
)

connect_foundry_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-foundry/get/1.1.0.zip'
    '#egg=ftrack-connect-foundry-1.1.0'
)

# Configuration.
setup(
    name='ftrack-connect-nuke',
    version=VERSION,
    description='Repository for ftrack connect nuke.',
    long_description=open(README_PATH).read(),
    keywords='',
    url='https://bitbucket.org/ftrack/ftrack-connect-nuke',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_requires=[
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 1'
    ],
    install_requires=[
        'ftrack-python-api >= 1, < 2',
        'ftrack-connect >= 1.0.0, < 2',
        'ftrack-connect-foundry >= 0.1.0, < 2'
    ],
    tests_require=[
        'pytest >= 2.3.5, < 3'
    ],
    cmdclass={
        'test': PyTest
    },
    dependency_links=[
        ('https://bitbucket.org/ftrack/lowdown/get/0.1.0.zip'
         '#egg=lowdown-0.1.0'),
        connect_dependency_link,
        connect_foundry_dependency_link
    ],
    data_files=data_files
)
