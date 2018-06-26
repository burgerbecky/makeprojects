#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Rebuild a project

Package that handles the command line program 'rebuildme'.

See:
	main()
"""

## \package makeprojects.rebuildme

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os
import argparse
from makeprojects import buildme
from makeprojects import cleanme
from .__pkginfo__ import VERSION

########################################


def main(working_dir=None, args=None):
	"""
	Invoke the command line 'rebuildme'

	Entry point for the program 'rebuildme', this function
	will either get the parameters from sys.argv or the paramater 'args'.

	- '--version', show version
	- '-r', Perform a recursive rebuild
	- '-v', Verbose output
	- '--generate-rcfile', Create .projectsrc in the working directory
	- '--rcfile', Override the configruration file
	- '-f', Stop building on the first build failure
	- '-d', Directory to build
	- '-docs', Build documentation
	- Additional terms are considered specific files to build

	Args:
		working_dir: Directory to rebuild
		args: Command line to use instead of sys.argv
	Returns:
		Zero on no error, non-zero on error
	"""

	# Make sure the working directory is set
	if working_dir is None:
		working_dir = os.getcwd()

	# Parse the command line
	parser = argparse.ArgumentParser( \
		description='Rebuild project files. Copyright by Rebecca Ann Heineman. ' \
		'Invokes cleanme and then buildme')

	parser.add_argument('--version', action='version', \
		version='%(prog)s ' + VERSION)
	parser.add_argument('-r', '-all', dest='recursive', action='store_true', \
		default=False, help='Perform a recursive rebuild')
	parser.add_argument('-v', '-verbose', dest='verbose', action='store_true', \
		default=False, help='Verbose output.')
	parser.add_argument('--generate-rcfile', dest='generate_rc', \
		action='store_true', default=False, \
		help='Generate a sample configuration file and exit.')
	parser.add_argument('--rcfile', dest='rcfile', \
		metavar='<file>', default=None, help='Specify a configuration file.')

	parser.add_argument('-f', dest='fatal', action='store_true', \
		default=False, help='Quit immediately on any error.')
	parser.add_argument('-d', dest='directories', action='append', \
		help='List of directories to build in.')
	parser.add_argument('-docs', dest='documentation', action='store_true', \
		default=False, help='Compile Doxyfile files.')
	parser.add_argument('args', nargs=argparse.REMAINDER, \
		help='project filenames')

	# Parse everything
	args = parser.parse_args(args=args)

	# Output default configuration
	if args.generate_rc:
		from .config import savedefault
		savedefault(working_dir)
		return 0

	# Generate command lines for the tools
	cleanargs = []
	buildargs = []

	# Recursive
	if args.recursive:
		cleanargs.append('-r')
		buildargs.append('-r')

	# Verbose output
	if args.verbose:
		cleanargs.append('-v')
		buildargs.append('-v')

	# Config file
	if args.rcfile:
		cleanargs.extend(['--rcfile', args.rcfile])
		buildargs.extend(['--rcfile', args.rcfile])

	# Fatal
	if args.fatal:
		buildargs.append('-f')

	# Doxygen
	if args.documentation:
		buildargs.append('-docs')

	# Directories to build
	if args.directories:
		for item in args.directories:
			buildargs.extend(['-d', item])

	# Excess entries
	if args.args:
		for item in args.args:
			buildargs.append(item)

	# Clean and then build, couldn't be simpler!
	error = cleanme.main(working_dir, args=cleanargs)
	if not error:
		error = buildme.main(working_dir, args=buildargs)
	return error

# If called as a function and not a class, call my main


if __name__ == "__main__":
	sys.exit(main())
