#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Build the egg file for makeprojects for python

setup.py clean
setup.py sdist bdist_wheel
twine upload --verbose dist/*
setup.py flake8

Copyright 2013-2019 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

from __future__ import absolute_import, print_function, unicode_literals
import io
import os
import sys
import setuptools

CWD = os.path.dirname(os.path.abspath(__file__))

# Project specific strings
PROJECT_NAME = 'makeprojects'
PROJECT_KEYWORDS = [
    'burger',
    'perforce',
    'burgerlib',
    'development',
    'makeprojects',
    'xcode',
    'visual studio',
    'visualstudio',
    'codeblocks',
    'watcom',
    'ps4',
    'xboxone',
    'xbox360',
    'vita',
    'mac',
    'ios',
    'android',
    'nintendo',
    'switch'
]

# Manually import the project
PROJECT_MODULE = __import__(PROJECT_NAME)

# Read me file is the long description
with io.open(os.path.join(CWD, 'README.rst'), encoding='utf-8') as filep:
    LONG_DESCRIPTION = filep.read()

# Create the dependency list
INSTALL_REQUIRES = [
    'setuptools >= 17.1',
    'enum34 >= 1.0.0',
    'burger >= 1.1.36',
    'argparse >= 1.0',
    'glob2 >= 0.6',
    'funcsigs >= 1.0'
]

# Project classifiers
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Topic :: Software Development',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7'
]

# Entry points for the generated command line tools
ENTRY_POINTS = {
    'console_scripts': [
        'makeprojects = makeprojects.__main__:main',
        'buildme = makeprojects.buildme:main',
        'cleanme = makeprojects.cleanme:main',
        'rebuildme = makeprojects.rebuildme:main']
}

#
# Parms for setup
#

SETUP_ARGS = dict(

    name=PROJECT_NAME,
    version=PROJECT_MODULE.__version__,

    # Use the readme as the long description
    description=PROJECT_MODULE.__summary__,
    long_description=LONG_DESCRIPTION,
    # long_description_content_type='text/x-rst; charset=UTF-8',
    license=PROJECT_MODULE.__license__,
    url=PROJECT_MODULE.__uri__,

    author=PROJECT_MODULE.__author__,
    author_email=PROJECT_MODULE.__email__,

    keywords=PROJECT_KEYWORDS,
    platforms=['Any'],
    install_requires=INSTALL_REQUIRES,
    zip_safe=False,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',

    classifiers=CLASSIFIERS,
    packages=[PROJECT_NAME],
    package_dir={PROJECT_NAME: PROJECT_NAME},
    include_package_data=True,

    entry_points=ENTRY_POINTS
)

########################################

CLEAN_DIR_LIST = [
    PROJECT_NAME + '.egg-info',
    PROJECT_NAME + '-' + PROJECT_MODULE.__version__,
    'dist',
    'build',
    'temp',
    '.pytest_cache',
    '.tox',
    '.vscode'
]

CLEAN_DIR_RECURSE_LIST = [
    'temp',
    '__pycache__',
    '_build'
]

CLEAN_EXTENSION_LIST = [
    '*.pyc',
    '*.pyo'
]


def clean(working_directory):
    """
    Clean up all the temp files after uploading

    Helps in keeping source control from having to track
    temp files
    """

    # Delete all folders, including read only files
    import burger
    for item in CLEAN_DIR_LIST:
        burger.delete_directory(os.path.join(working_directory, item))

    burger.clean_directories(
        working_directory,
        CLEAN_DIR_RECURSE_LIST,
        recursive=True)

    #
    # Delete all *.pyc and *.pyo files
    #

    burger.clean_files(
        working_directory,
        name_list=CLEAN_EXTENSION_LIST,
        recursive=True)


def myunlock(working_directory, recursive):
    """
    Unlock files locked by Perforce
    """
    result = []
    try:
        import burger
        result = burger.unlock_files(working_directory, recursive)
    except ImportError:
        pass
    return result


def mylock(lock_list):
    """
    Restore the perforce locks
    """
    try:
        import burger
        burger.lock_files(lock_list)
    except ImportError:
        pass

########################################


if __name__ == '__main__':

    # Perform the setup

    # Ensure the directory is the current one
    if CWD:
        os.chdir(CWD)

    # Perform a thorough cleaning job
    if 'clean' in sys.argv:
        clean(CWD)

    # Unlock the files to handle Perforce locking
    LOCK_LIST = myunlock(CWD, True)
    try:
        setuptools.setup(**SETUP_ARGS)

    # If any files were unlocked, relock them
    finally:
        mylock(LOCK_LIST)
