#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Package that reads, parses and processes the configuration file
"""

## \package makeprojects.config

from __future__ import absolute_import, print_function, unicode_literals

import os
import configparser
import io
import shutil
import burger

## Projectsrc file to detect first
_DOT_PROJECTSRC = '.projectsrc'

## Projectsrc file to detect secondly
_PROJECTSRC = 'projectsrc'

## Projectsrc location environment variable
_PROJECTSRC_VAR = 'PROJECTSRC'

## Location of the user's home directory
USER_HOME = os.path.expanduser('~')

if 'MAKEPROJECTS_HOME' in os.environ:
	## Location of makeprojects home directory if redirected
	PROJECTS_HOME = os.environ['MAKEPROJECTS_HOME']
else:
	PROJECTS_HOME = USER_HOME

########################################


def savedefault(destinationfile='.projectsrc'):
	"""
	Calls the internal function to save a default .projectsrc file

	Given a pathname, create and write out a default .projectsrc file
	that can be used as input to makeprojects to generate project files.

	Args:
		destinationfile: Pathname of where to save the default configuation file
	"""

	src = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.projectsrc')
	try:
		shutil.copyfile(src, destinationfile)
	except OSError as error:
		print(error)

########################################


def find_projectsrc(working_dir=None):
	"""
	Search for the projectsrc file.

	Scan for the .projectsrc file starting from the current working directory
	and search downwards until the root directoy is it. If not found, search in
	the user's home directory or for linux/macOS, in /etc

	Args:
		working_dir: Directory to scan first for the preferences file, None to
			use the current working directory
	Returns:
		Pathname of the configuration file, or None if no file was found.
	"""

	# Is there a makeprojects rc file in the current directory or
	# any directory in the chain?

	if working_dir is None:
		working_dir = os.getcwd()

	result = burger.traverse_directory(working_dir, \
		(_DOT_PROJECTSRC, _PROJECTSRC), True)
	if result:
		return result[0]

	# See if there's an environment variable pointing to a file
	if _PROJECTSRC_VAR in os.environ and \
		os.path.exists(os.environ[_PROJECTSRC_VAR]):
		result = os.environ[_PROJECTSRC_VAR]
	else:
		# Scan the usual suspects for a global instance

		# If '~' doesn't expand or /root, use the current folder
		if USER_HOME == '~' or USER_HOME == '/root':
			result = _DOT_PROJECTSRC
		else:
			# Check the user's home folder
			result = os.path.join(USER_HOME, _DOT_PROJECTSRC)
			if os.path.isfile(result):
				return result
			result = os.path.join(USER_HOME, '.config', _PROJECTSRC)

	if not os.path.isfile(result):

		# If not found, use /etc/projectsrc for system globals on non
		# windows platforms
		if not burger.get_windows_host_type() and \
			os.path.isfile('/etc/' + _PROJECTSRC):
			result = '/etc/' + _PROJECTSRC
		else:
			result = None
	return result


## Full pathname of the configuration file
PROJECTSRC = find_projectsrc()

########################################


def import_configuration(file_name=None, verbose=True):
	"""
	Load in the configuration file

	Using the file PROJECTSRC, load it in and parse it as an INI
	file using the configparser python class.

	Args:
		file_name: File to load for configuration
		verbose: If True, print the loaded file''s name.

	Returns:
		An empty parser object or filled with a successfully loaded file
	"""

	if file_name is None:
		file_name = PROJECTSRC

	parser = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))

	if file_name and os.path.exists(file_name):

		# If a DOM marker was used, utf_8_sig will handle it
		with io.open(file_name, 'r', encoding='utf_8_sig') as filep:
			parser.read_file(filep)

		# If any markers are in upper case, force to lower case
		# by manually scanning the keys and forcing them to lower case
		# This is needed to allow case insensitivity in the file
		# because the class only does case sensitive compares

		# pylint: disable=W0212
		for sect, values in list(parser._sections.items()):
			if values and not sect.islower():
				parser._sections[sect.lower()] = values

		if verbose:
			print('Using configuration file {}'.format(file_name))
	elif verbose:
		print('No configuration file found, using defaults')
	return parser


## Parser object containing the current configuration file object
CONFIG_PARSER = None
# import_configuration()
