#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Remove all temporary files in a project's folder

Copyright 2013-2018 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import shutil
import sys
import argparse
import burger

#
## \package makeprojects.cleanme
# Module that contains the code for the command line "cleanme"
#

# Regex .*_Data$

## List of directories to delete if they end with this suffix
DIR_ENDS_WITH = \
[
	'.xcodeproj',		# Special cased in the code
	'_Data',			# Codewarrior droppings
	' Data',			# Codewarrior mac droppings
	'.egg-info'			# Python droppings
]

## List of directories to delete if their names match
DIR_IS = \
[
	'dist',				# Python builder
	'build',			# Python and XCode
	'appfolder',		# Obsolete from burger
	'temp',				# Duh
	'ipch',				# Visual studio
	'bin',				# Built binaries
	'__pycache__',		# Python 3.6 droppings
	'.vs',				# Visual studio 2017 droppings
	'.vscode'			# Visual studio code droppings
]

########################################

def remove_folder(folder_name, verbose=False):
	"""
	Dispose of a folder and print it's name if need be

	Args:
		folder_name: Directory to delete
		verbose: True if the folder name to delete is printed to stdout.
	"""

	if verbose:
		print('Deleting the folder {}'.format(folder_name))
	shutil.rmtree(folder_name, ignore_errors=True)

########################################

def remove_global_data(verbose=False):
	"""
	Delete system data files.

	Remove data that's stored globally so it's only needed to be invoked once
	for either a once shot or recursive clean

	Args:
		verbose: True if the folder name to delete is printed to stdout.
	Returns:
		Integer with the number of files/folders deleted.
	"""

	objectsremoved = 0

	#
	# Metrowerks has some defaults it leaves on build
	# but only for the Windows hosts
	#

	if burger.host_machine() == 'windows':
		local_app_data = os.getenv('LOCALAPPDATA')
		if local_app_data is not None:
			default_cww = os.path.join(local_app_data, 'Metrowerks', 'default.cww')
			if os.path.isfile(default_cww):
				if verbose:
					print('Deleting the file {}'.format(default_cww))
				try:
					burger.delete_file(default_cww)
				except OSError as error:
					print(error)
				else:
					objectsremoved += 1

	return objectsremoved

########################################

def remove_by_file_extension(working_dir, extension_list, verbose=False):
	"""
	Remove all files with specific extensions.

	Note, this function skips over directories, even if their
	names match the extension_list.

	Args:
		working_dir: Directory to delete files from.
		extension_list: Iterable list of file extensions to match
		verbose: True if the folder name to delete is printed to stdout.
	Returns:
		Integer with the number of files/folders deleted.
	"""

	objectsremoved = 0

	# Get the files in the directory
	for base_name in os.listdir(working_dir):
		file_name = os.path.join(working_dir, base_name)

		# Is it a file?
		if os.path.isfile(file_name):

			# Check against the extension list
			for extension in extension_list:
				if base_name.endswith(extension):

					# Bye bye!
					if verbose:
						print('Deleting the file {}'.format(file_name))
					try:
						burger.delete_file(file_name)
					except OSError as error:
						print(error)
					else:
						objectsremoved = objectsremoved+1
					break

	return objectsremoved

########################################

def clean(working_dir, verbose=False):	# pylint: disable=R0912,R0915
	"""
	Perform a "clean" operation on the current folder

	Args:
		working_dir: Directory to delete files from.
		verbose: True if the folder name to delete is printed to stdout.
	Returns:
		Integer with the number of files/folders deleted.
	See:
		recursive_clean()
	"""

	# Iterate through this folder and clean out the contents
	if verbose:
		print('Cleaning the directory "{}"'.format(working_dir))

	objectsremoved = 0

	# If the file Doxyfile exists, then assume that this is a documentation folder

	docsfilename = os.path.join(working_dir, 'Doxyfile')
	found_doxyfile = os.path.isfile(docsfilename)

	# Iterate over all the files/folders for things to purge

	for base_name in os.listdir(working_dir):
		file_name = os.path.join(working_dir, base_name)

		# Handle the directories found
		if os.path.isdir(file_name):

			for item in DIR_ENDS_WITH:
				if base_name.endswith(item):
					if item != '.xcodeproj':
						remove_folder(file_name, verbose)
						objectsremoved += 1
						break

					# XCode project folder are special cased

					# Remove a user's pref files
					objectsremoved += remove_by_file_extension(file_name, ['.mode1v3', '.pbxuser'], verbose)

					# Remove special folders, if found inside the xcode folder
					xcuserdata = os.path.join(file_name, 'xcuserdata')
					if os.path.isdir(xcuserdata):
						remove_folder(xcuserdata, verbose)
						objectsremoved += 1

					xcworkspace = os.path.join(file_name, 'project.xcworkspace')
					if os.path.isdir(xcworkspace):
						remove_folder(xcworkspace, verbose)
						objectsremoved += 1
					break

			else:
				# See if the folder name is a perfect match
				if base_name in DIR_IS:
					remove_folder(file_name, verbose)
					objectsremoved += 1

		# Files to delete...
		# .suo is from Visual Studio
		# .user is from Visual Studio
		# .ncb is from Visual Studio
		# .err is from Watcom and CodeWarrior on Mac and Windows
		# .sdf is from Visual Studio
		# .pyc is from python
		# .layout.cbTemp is from CodeBlocks
		# .DS_Store is from the Mac Finder

		# If Doxygen is found
		# .chm is a documentation file
		# .chw is a chm index/history file
		# .tmp Doxygen work file

		elif os.path.isfile(file_name):
			# These file extensions are history
			# pylint: disable=R0916
			if base_name.endswith('.suo') or \
				base_name.endswith('.user') or \
				base_name.endswith('.ncb') or \
				base_name.endswith('.err') or \
				base_name.endswith('.sdf') or \
				base_name.endswith('.pyc') or \
				base_name.endswith('.layout.cbTemp') or \
				base_name.endswith('.VC.db') or \
				base_name == '.DS_Store':
				if verbose:
					print('Deleting file "{}"'.format(file_name))
				try:
					os.remove(file_name)
				except OSError as error:
					print(error)
				else:
					objectsremoved = objectsremoved+1

			# Remove CodeBlocks files ONLY if a codeblocks project is present
			# to prevent accidental deletion of legitimate files

			elif base_name.endswith('.layout') or \
				base_name.endswith('.depend'):
				if os.path.isfile(os.path.join(working_dir, os.path.splitext(base_name)[0] + '.cbp')):
					if verbose:
						print('Deleting file "{}"'.format(file_name))
					try:
						os.remove(file_name)
					except OSError as error:
						print(error)
					objectsremoved = objectsremoved+1

			# Is it possible to have doxygen leftovers?

			elif found_doxyfile:
				if base_name == 'doxygenerrors.txt' or \
					base_name.endswith('.chm') or \
					base_name.endswith('.chw') or \
					base_name.endswith('.tmp'):
					if verbose:
						print('Deleting file "{}"'.format(file_name))
					os.remove(file_name)
					objectsremoved = objectsremoved+1


	return objectsremoved

########################################

def recursive_clean(working_dir, verbose=False):
	"""
	Clean folders recursively.

	Perform a "clean" operation on the current folder and every folder
	down the line recursively

	Args:
		working_dir: Directory to delete files from.
		verbose: True if the folder name to delete is printed to stdout.
	Returns:
		Total number of files/folders removed
	See:
		clean()
	"""

	# Iterate through this folder and clean out the contents

	# Perform the clean first, to prevent iterating down any
	# folders that will be erased anyways

	objectsremoved = clean(working_dir, verbose)

	# Now, iterate through the current folder for folders to recurse through

	for base_name in os.listdir(working_dir):
		file_name = os.path.join(working_dir, base_name)
		# Handle the directories found
		if os.path.isdir(file_name):
			objectsremoved += recursive_clean(file_name, verbose)

	return objectsremoved

########################################

def main(working_dir=None):
	"""
	Command line shell

	Args:
		working_dir: Directory to operate on, or None for os.getcwd()
	Returns:
		Zero
	"""

	# Make sure working_dir is properly set
	if working_dir is None:
		working_dir = os.getcwd()

	# Parse the command line
	parser = argparse.ArgumentParser( \
		description='Remove project output files. ' \
		'Copyright by Rebecca Ann Heineman', \
		usage='clean [-h] [-r] [-v]')
	parser.add_argument('-r', '-all', dest='all', action='store_true', \
		default=False, help='Perform a recursive clean')
	parser.add_argument('-v', '-verbose', dest='verbose', action='store_true', \
		default=False, help='Verbose output')

	args = parser.parse_args()

	# True if debug spew is requested
	verbose = args.verbose

	# Get rid of one shot data
	objectsremoved = remove_global_data(verbose)

	# Get rid of local data
	if not args.all:
		objectsremoved += clean(working_dir, verbose)
	else:
		if verbose:
			print('Performing a recursive clean')
		objectsremoved += recursive_clean(working_dir, verbose)

	if objectsremoved != 0:
		print('Removed {} objects.'.format(objectsremoved))
	else:
		print('No files or folders were removed.')
	return 0

#
# If called as a function and not a class,
# call my main
#

if __name__ == "__main__":
	sys.exit(main())
