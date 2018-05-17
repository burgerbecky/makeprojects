#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2018 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

#
## \mainpage makeprojects for Python Index
#
# A tool to generate projects for popular IDEs
#
# \par List of IDE classes
#
# \li \ref makeprojects
# \li \ref makeprojects.core
# \li \ref makeprojects.FileTypes
# \li \ref makeprojects.SourceFile
# \li \ref makeprojects.Solution
# \li \ref makeprojects.Project
#
# \par List of sub packages
#
# \li \ref makeprojects.__pkginfo__
# \li \ref makeprojects.enums
# \li \ref makeprojects.visualstudio
# \li \ref makeprojects.xcode
# \li \ref makeprojects.codewarrior
# \li \ref makeprojects.codeblocks
# \li \ref makeprojects.watcom
#
# To use in your own script:
#
# \code
# from makeprojects import *
#
# solution = newsolution(name='myproject')
# project = newproject(name='myproject')
# solution.addproject(project=project)
#
# project.setconfigurations(['Debug','Internal','Release'])
# project.setplatform(project.Windows)
# project.addsourcefiles(os.path.join(os.getcwd(),'*.*'),recursive=True)
# solution.save(solution.xcode3)
#
# \endcode
#
#
# To install type in 'pip install -U makeprojects' from your python command line
#
# The source can be found at github at https://github.com/burgerbecky/makeprojects
#
# Email becky@burgerbecky.com for comments, bugs or coding suggestions.
#

"""
Module that contains the main() function
"""

## \package __main__

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os
import argparse
import json
import makeprojects

from .core import Solution

#
## Main entry point when invoked as a tool
#
# When makeprojects is invoked as a tool, this main() function
# is called with the current working directory. Arguments will
# be obtained using the argparse class.
#
# \param working_dir String containing the current working directory
# \return Zero if no error, non-zero on error
#

def main(working_dir=None):

	if working_dir is None:
		working_dir = os.getcwd()

	#
	# Create the parseable arguments
	#

	parser = argparse.ArgumentParser(prog='makeprojects', description='Version ' + \
		makeprojects.__version__ + '. ' + makeprojects.__copyright__ + '. ' \
		'Given a .py input file, create project files for most of the popular IDEs.')

	parser.add_argument('-xcode3', dest='xcode3', action='store_true', \
		default=False, help='Build for Xcode 3.')
	parser.add_argument('-xcode4', dest='xcode4', action='store_true', \
		default=False, help='Build for Xcode 4.')
	parser.add_argument('-xcode5', dest='xcode5', action='store_true', \
		default=False, help='Build for Xcode 5.')
	parser.add_argument('-xcode6', dest='xcode6', action='store_true', \
		default=False, help='Build for Xcode 6.')
	parser.add_argument('-xcode7', dest='xcode7', action='store_true', \
		default=False, help='Build for Xcode 7.')
	parser.add_argument('-xcode8', dest='xcode8', action='store_true', \
		default=False, help='Build for Xcode 8.')
	parser.add_argument('-xcode9', dest='xcode9', action='store_true', \
		default=False, help='Build for Xcode 9.')

	parser.add_argument('-vs2005', dest='vs2005', action='store_true', \
		default=False, help='Build for Visual Studio 2005.')
	parser.add_argument('-vs2008', dest='vs2008', action='store_true', \
		default=False, help='Build for Visual Studio 2008.')
	parser.add_argument('-vs2010', dest='vs2010', action='store_true', \
		default=False, help='Build for Visual Studio 2010.')
	parser.add_argument('-vs2012', dest='vs2012', action='store_true', \
		default=False, help='Build for Visual Studio 2012.')
	parser.add_argument('-vs2013', dest='vs2013', action='store_true', \
		default=False, help='Build for Visual Studio 2013.')
	parser.add_argument('-vs2015', dest='vs2015', action='store_true', \
		default=False, help='Build for Visual Studio 2015.')
	parser.add_argument('-vs2017', dest='vs2017', action='store_true', \
		default=False, help='Build for Visual Studio 2017.')

	parser.add_argument('-codeblocks', dest='codeblocks', action='store_true', \
		default=False, help='Build for CodeBlocks 16.01')
	parser.add_argument('-codewarrior', dest='codewarrior', action='store_true', \
		default=False, help='Build for Metrowerks / Freescale CodeWarrior')
	parser.add_argument('-watcom', dest='watcom', action='store_true', \
		default=False, help='Build for Watcom WMAKE')
	parser.add_argument('-ios', dest='ios', action='store_true', \
		default=False, help='Build for iOS with XCode 5 or higher.')
	parser.add_argument('-vita', dest='vita', action='store_true', \
		default=False, help='Build for PS Vita with Visual Studio 2010.')
	parser.add_argument('-360', dest='xbox360', action='store_true', \
		default=False, help='Build for XBox 360 with Visual Studio 2010.')
	parser.add_argument('-wiiu', dest='wiiu', action='store_true', \
		default=False, help='Build for WiiU with Visual Studio 2013.')
	parser.add_argument('-dsi', dest='dsi', action='store_true', \
		default=False, help='Build for Nintendo DSI with Visual Studio 2015.')

	parser.add_argument('-release', dest='release', action='store_true', \
		default=False, help='Create a release target (Default is release/debug/internal)')
	parser.add_argument('-debug', dest='debug', action='store_true', \
		default=False, help='Create a debug target')
	parser.add_argument('-internal', dest='internal', action='store_true', \
		default=False, help='Create an internal target')
	parser.add_argument('-finalfolder', dest='finalfolder', action='store_true', \
		default=False, help='Add a script to copy a release build to a folder and check in with Perforce')
	parser.add_argument('-app', dest='app', action='store_true', \
		default=False, help='Build an application instead of a tool')
	parser.add_argument('-lib', dest='library', action='store_true', \
		default=False, help='Build a library instead of a tool')

	parser.add_argument('-f', dest='jsonfiles', \
		action='append', help='Input file to process')
	parser.add_argument('-v', '-verbose', dest='verbose', action='store_true', \
		default=False, help='Verbose output.')
	parser.add_argument('-default', dest='default', action='store_true', \
		default=False, help='Create a default projects.py file')

	parser.add_argument('args', nargs=argparse.REMAINDER, help='project filenames')

	#
	# Parse the command line
	#
	args = parser.parse_args()

	#
	# Shall a default file be generated?
	#

	if args.default is True:
		from makeprojects import savedefault
		savedefault(os.path.join(working_dir, 'projects.py'))
		return 0

	#
	# Process defaults first
	#

	solution = Solution()
	solution.verbose = args.verbose
	solution.workingDir = working_dir

	#
	# No input file?
	#

	if args.jsonfiles is None:
		if args.args:
			args.jsonfiles = args.args
		else:
			projectpathname = os.path.join(working_dir, 'projects.json')
			if os.path.isfile(projectpathname) is True:
				args.jsonfiles = ['projects.json']
			else:
				return solution.processcommandline(args)

	#
	# Read in the json file
	#

	for jsonarg in args.jsonfiles:
		projectpathname = os.path.join(working_dir, jsonarg)
		if os.path.isfile(projectpathname) != True:
			print(jsonarg + ' was not found')
			return 2

		#
		# To allow '#' and '//' comments, the file has to be pre-processed
		#

		fileref = open(projectpathname, 'r')
		jsonlines = fileref.readlines()
		fileref.close()

		#
		# Remove all lines that have a leading '#' or '//'
		#

		pure = ''
		for item in jsonlines:
			cleanitem = item.lstrip()
			if cleanitem.startswith('#') or cleanitem.startswith('//'):
				# Insert an empty line so that line numbers still match on error
				pure = pure + '\n'
			else:
				pure = pure + item

		#
		# Parse the json file (Handle errors)
		#

		try:
			myjson = json.loads(pure)
		except Exception as error:
			print('{} in parsing {}'.format(error, projectpathname))
			return 2

		#
		# Process the list of commands
		#

		if isinstance(myjson, list):
			error = solution.process(myjson)
		else:
			print('Invalid json input file!')
			error = 2
		if error != 0:
			break

	return error

#
# If invoked as a tool, call the main with the current working directory
#

if __name__ == '__main__':
	sys.exit(main(os.getcwd()))
