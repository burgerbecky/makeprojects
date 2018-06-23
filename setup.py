#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Build the egg file for makeprojects for python

setup.py clean
setup.py build sdist bdist_wheel upload
setup.py flake8

Copyright 2013-2018 by Rebecca Ann Heineman becky@burgerbecky.com

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
import burger

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
	'android'
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
	'burger >= 1.1.9',
	'argparse >= 1.0',
	'glob2 >= 0.6'
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
	'Programming Language :: Python :: 3.3',
	'Programming Language :: Python :: 3.4',
	'Programming Language :: Python :: 3.5',
	'Programming Language :: Python :: 3.6'
]

# Entry points for the generated command line tools
ENTRY_POINTS = {
	'console_scripts': [ \
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
	python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*',

	classifiers=CLASSIFIERS,
	packages=[PROJECT_NAME],
	package_dir={PROJECT_NAME: PROJECT_NAME},
	package_data={str(PROJECT_NAME): ['.projectsrc']},

	entry_points=ENTRY_POINTS
)

########################################


def cleanpycfiles(working_dir):
	"""
	Delete all *.pyc and *.pyo files (Recursively)
	"""

	for item in os.listdir(working_dir):
		file_name = os.path.join(working_dir, item)

		# Is it a file?
		if os.path.isfile(file_name):

			# Only dispose of the pyo and pyc files
			if item.endswith('.pyc') or item.endswith('.pyo'):
				os.remove(file_name)

		# A directory?
		elif os.path.isdir(file_name):

			# Recurse
			cleanpycfiles(file_name)

########################################


def clean(working_dir):
	"""
	Clean up all the temp files after uploading

	Helps in keeping source control from having to track
	temp files
	"""

	#
	# Specific folders to wipe
	#

	# pylint: disable=C0330
	dirlist = [ \
		PROJECT_NAME + '.egg-info',
		PROJECT_NAME + '-' + PROJECT_MODULE.__version__,
		'dist',
		'build',
		'temp',
		'_build',
		'__pycache__',
		'.pytest_cache',
		'.tox']

	# Delete all specific folders, including read only files

	for item in dirlist:
		burger.delete_directory(os.path.join(working_dir, item))

	#
	# Delete all versioned folders
	#

	for item in os.listdir(working_dir):
		if item.startswith(PROJECT_NAME + '-'):
			burger.delete_directory(os.path.join(working_dir, item))

	#
	# Delete all *.pyc and *.pyo files (Recursively
	#

	cleanpycfiles(working_dir)


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
	LOCK_LIST = burger.unlock_files(CWD, True)
	try:
		setuptools.setup(**SETUP_ARGS)

	# If any files were unlocked, relock them
	finally:
		burger.lock_files(LOCK_LIST)
