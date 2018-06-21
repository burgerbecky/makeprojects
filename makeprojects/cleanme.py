#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Remove all temporary files in a project's folder
"""

## \package makeprojects.cleanme

from __future__ import absolute_import, print_function, unicode_literals

import os
import shutil
import sys
import argparse
import re
import burger
from .config import import_configuration
from .__pkginfo__ import VERSION

## Match *.cbp
_CODEBLOCKS_MATCH = re.compile('.*\\.cbp\\Z(?ms)')

## Match *.py
_PYTHON_MATCH = re.compile('.*\\.py\\Z(?ms)')

########################################


class CleanFileLists(object):
	"""
	Class to store file list information
	"""

	def __init__(self):
		"""
		Declares the internal variables

		See:
			CleanFileLists.reset()
		"""

		## List of re.compile().match entries of directories
		self.directory_list = []

		## List of re.compile().match entries of files
		self.file_list = []

		## List of environment expandable filename strings
		self.global_file_list = []

########################################

	def reset(self):
		"""
		Reset the values to defaults

		See:
			CleanFileLists.__init__()
		"""

		self.__init__()

########################################

	def load_section_entries(self, config, section):
		"""
		Read data in from a section in a config file

		Scan the entries 'directories', 'files', and 'global_files' in
		the config file and add them into this class instance.

		Args:
			config: Configuration object
			section: Name of the section of interest
		"""

		# Convert directory names to regex.match
		if config.has_option(section, 'directories'):
			self.directory_list.extend(burger.translate_to_regex_match( \
				burger.parse_csv(config.get(section, 'directories'))))

		# Convert file names to regex.match
		if config.has_option(section, 'files'):
			self.file_list.extend(burger.translate_to_regex_match( \
				burger.parse_csv(config.get(section, 'files'))))

		# Handle the global file names
		if config.has_option(section, 'global_files'):
			self.global_file_list.extend(burger.parse_csv( \
				config.get(section, 'global_files')))

########################################


def remove_folder(folder_name, verbose=False):
	"""
	Dispose of a folder and print it's name if need be

	Args:
		folder_name: Directory to delete
		verbose: True if the folder name to delete is printed to stdout.
	See:
		remove_by_file_extension() or remove_global_files()
	"""

	if verbose:
		print('Deleting the folder {}'.format(folder_name))
	shutil.rmtree(folder_name, ignore_errors=True)

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
	See:
		remove_folder() or remove_global_files()
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
						objectsremoved += 1
					break

	return objectsremoved

########################################


def remove_global_files(working_dir, file_list, verbose=False):
	"""
	Given a list of global files, delete them

	Delete a list of files. Environment variables are acceptable
	as part of the filename.

	Examples:
		makeprojects.cleanme.remove_global_files(['$(SDKS)/foo.txt', 'temp.txt'])

	Args:
		working_dir: Directory for relative file names.
		file_list: List of filenames to delete
		verbose: If True, print the name of every deleted file
	Returns:
		Number of files deleted
	See:
		remove_folder() or remove_by_file_extension()
	"""

	# No files deleted yet
	objectsremoved = 0

	# Only change directories if there's anything to process
	if file_list:

		# Save the directory and use the passed one for processing
		saved_dir = os.getcwd()
		os.chdir(working_dir)

		# Process the files
		for item in file_list:

			# Expand variable names
			file_path = os.path.abspath(os.path.expandvars(item))

			# If it's a file, delete it
			if os.path.isfile(file_path):
				if verbose:
					print('Deleting the file {}'.format(file_path))
				try:
					burger.delete_file(file_path)
				except OSError as error:
					print(error)
				else:
					objectsremoved += 1

		os.chdir(saved_dir)
	return objectsremoved

########################################


class Clean(object):
	"""
	Class to clean a folder
	"""

	def __init__(self):
		"""
		Declares the internal variables
		"""

		## If True, clean prefs inside of xcode project files
		self.purge_xcode = False

		## Name of the doxygen file
		self.doxyfile = 'doxyfile'

		## Configuration for [clean]
		self.root = CleanFileLists()

		## Configuration for [clean:python]
		self.python = CleanFileLists()

		## Configuration for [clean:doxygen]
		self.doxygen = CleanFileLists()

		## Configuration for [clean:codeblocks]
		self.codeblocks = CleanFileLists()

########################################

	def reset(self):
		"""
		Reset the values to defaults
		"""

		self.root.reset()
		self.python.reset()
		self.doxygen.reset()
		self.codeblocks.reset()

########################################

	def load_config(self, config):
		"""
		Read the configuation file

		Read all entries in the config file.

		Args:
			config: Configuration object
		"""

		# Get the one shot variables

		# XCode prefs
		if config.has_option('clean', 'purge_xcode'):
			self.purge_xcode = config.getboolean('clean', 'purge_xcode')

		# Doxyfile name
		if config.has_option('clean', 'doxyfile'):
			self.doxyfile = config.get('clean', 'doxyfile').strip().lower()

		# Get the file records for the root and the host computer
		self.root.load_section_entries(config, 'clean')
		if burger.get_windows_host_type():
			self.root.load_section_entries(config, 'clean:windows')
		if burger.get_mac_host_type():
			self.root.load_section_entries(config, 'clean:macos')
		if burger.host_machine() == 'linux':
			self.root.load_section_entries(config, 'clean:linux')

		# Get the special settings for project type folders
		self.python.load_section_entries(config, 'clean:python')
		self.doxygen.load_section_entries(config, 'clean:doxygen')
		self.codeblocks.load_section_entries(config, 'clean:codeblocks')

########################################

	def process(self, working_dir, verbose=False, recursive=False, first=True):
		"""
		Clean the files based on the settings

		Args:
			working_dir: Directory to clean
			verbose: True if progress messages are desired
			recursive: True if directories are to be traversed
			first: Used internally, always pass True
		Returns:
			Number of items deleted
		"""

		# Initial message
		if first and verbose:
			print('Cleaning {}{}...'.format(working_dir, \
				' recursively' if recursive else ''))

		objectsremoved = 0
		# Only process global files once
		if first:
			objectsremoved = remove_global_files(working_dir, \
				self.root.global_file_list, verbose=verbose)

		# Scan the directory for specific files to determine behavior
		# Detect python, codeblocks, doxygen and handle the xcode prefs
		# file deletion

		list_dir = os.listdir(working_dir)
		doxygen = False
		python = False
		codeblocks = False
		for base_name in list_dir:

			file_name = os.path.join(working_dir, base_name)

			# Do a case insensitive compare
			base_name = base_name.lower()
			if base_name == self.doxyfile:
				if os.path.isfile(file_name):
					doxygen = True
					continue

			if _CODEBLOCKS_MATCH.match(base_name):
				if os.path.isfile(file_name):
					codeblocks = True
					continue

			if _PYTHON_MATCH.match(base_name):
				if os.path.isfile(file_name):
					python = True
					continue

			# XCode project folder are special cased
			# If the xcode pref files are to be deleted, do so.

			if self.purge_xcode and base_name.endswith('.xcodeproj'):
				# Make sure this is a folder
				if os.path.isdir(file_name):

					# Remove a user's pref files
					objectsremoved += remove_by_file_extension(file_name, \
						('.mode1v3', '.pbxuser'), verbose)

					# Remove special folders, if found inside the xcode folder
					for item in ('xcuserdata', 'project.xcworkspace'):
						xcode_dir = os.path.join(file_name, item)
						if os.path.isdir(xcode_dir):
							remove_folder(xcode_dir, verbose)
							objectsremoved += 1

		# Create the directory list based on which is based on
		# which types of projects were found

		dir_list = list(self.root.directory_list)
		file_list = list(self.root.file_list)
		if python:
			dir_list.extend(self.python.directory_list)
			file_list.extend(self.python.file_list)
		if doxygen:
			dir_list.extend(self.doxygen.directory_list)
			file_list.extend(self.doxygen.file_list)
		if codeblocks:
			dir_list.extend(self.codeblocks.directory_list)
			file_list.extend(self.codeblocks.file_list)

		# Perform the deletion
		for base_name in list_dir:

			# Get the full path name
			file_name = os.path.join(working_dir, base_name)

			# Handle the directories found
			if os.path.isdir(file_name):
				# Is this in the list?
				for item in dir_list:
					if item(base_name):
						# Delete it
						remove_folder(file_name, verbose)
						objectsremoved += 1
						break
				else:
					if recursive:
						objectsremoved += self.process(file_name, verbose, recursive, False)
			# Handle the files found
			elif os.path.isfile(file_name):
				# Is this in the list?
				for item in file_list:
					if item(base_name):
						# Delete it
						if verbose:
							print('Deleting file "{}"'.format(file_name))
						try:
							os.remove(file_name)
						except OSError as error:
							print(error)
						else:
							objectsremoved += 1
						break

		return objectsremoved

########################################


def main(working_dir=None, args=None):
	"""
	Command line shell

	Args:
		working_dir: Directory to operate on, or None for os.getcwd()
		args: Command line to use instead of sys.argv
	Returns:
		Zero
	"""

	# Make sure working_dir is properly set
	if working_dir is None:
		working_dir = os.getcwd()

	# usage='clean [-h] [-r] [-v]',
	# Parse the command line
	parser = argparse.ArgumentParser( \
		description='Remove project output files. ' \
		'Copyright by Rebecca Ann Heineman',
		add_help=True)

	parser.add_argument('--version', action='version', \
		version='%(prog)s ' + VERSION)
	parser.add_argument('-r', '-all', dest='recursive', action='store_true', \
		default=False, help='Perform a recursive clean')
	parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', \
		default=False, help='Verbose output.')
	parser.add_argument('--generate-rcfile', dest='generate_rc', \
		action='store_true', default=False, \
		help='Generate a sample configuration file and exit.')
	parser.add_argument('--rcfile', dest='rcfile', \
		metavar='<file>', default=None, help='Specify a configuration file.')

	# Parse everything
	args = parser.parse_args(args=args)

	# True if debug spew is requested
	verbose = args.verbose

	# Output default configuration
	if args.generate_rc:
		from .config import savedefault
		savedefault()
		return 0

	# Load the configuration file
	config = import_configuration(file_name=args.rcfile, verbose=verbose)

	# Create an instance of the cleaner
	cleaner = Clean()
	# Load in the configuration
	cleaner.load_config(config=config)
	# Remove the data
	objectsremoved = cleaner.process(working_dir, verbose=verbose, \
		recursive=args.recursive)

	# Wrap up!
	if verbose:
		if objectsremoved:
			print('Removed {} objects.'.format(objectsremoved))
		else:
			print('No files or folders were removed.')
	return 0


# If called as a function and not a class,
# call my main

if __name__ == "__main__":
	sys.exit(main())
