#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2016 by Rebecca Ann Heineman becky@burgerbecky.com

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
# \li \ref makeprojects.core.SolutionData
# \li \ref makeprojects.core.ProjectData
# \li \ref makeprojects.core
# \li \ref makeprojects.visualstudio
# \li \ref makeprojects.xcode
#
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
# To install type in 'pip makeprojects' from your python command line
#
# The source can be found at github at https://github.com/burgerbecky/makeprojects
#
# Email becky@burgerbecky.com for comments, bugs or coding suggestions.
#

import sys
import os
import burger
import argparse
import json
from .core import SolutionData

#
# If invoked as a tool, call the main with the current working directory
#

def main(workingDir):

	#
	# Parse the command line
	#
	
	parser = argparse.ArgumentParser(
		prog='makeprojects',
		description='Create project files. Copyright by Rebecca Ann Heineman. Given a .py input file, create project files')

	parser.add_argument('-int',dest='xcodeversion',type=int,
		default=3,
		help='Build for Xcode version 3 through 8')

	parser.add_argument('-xcode3', dest='xcode3', action='store_true',
		default=False,
		help='Build for Xcode 3.')

	parser.add_argument('-xcode4', dest='xcode4', action='store_true',
		default=False,
		help='Build for Xcode 4.')

	parser.add_argument('-xcode5', dest='xcode5', action='store_true',
		default=False,
		help='Build for Xcode 5.')

	parser.add_argument('-vs2005', dest='vs2005', action='store_true',
		default=False,
		help='Build for Visual Studio 2005.')
	parser.add_argument('-vs2008', dest='vs2008', action='store_true',
		default=False,
		help='Build for Visual Studio 2008.')
	parser.add_argument('-vs2010', dest='vs2010', action='store_true',
		default=False,
		help='Build for Visual Studio 2010.')
	parser.add_argument('-vs2015', dest='vs2015', action='store_true',
		default=False,
		help='Build for Visual Studio 2015.')
	parser.add_argument('-codeblocks', dest='codeblocks', action='store_true',
		default=False,
		help='Build for CodeBlocks 13.12')
	parser.add_argument('-codewarrior', dest='codewarrior', action='store_true',
		default=False,
		help='Build for CodeWarrior')
	parser.add_argument('-watcom', dest='watcom', action='store_true',
		default=False,
		help='Build for Watcom WMAKE')
	parser.add_argument('-ios', dest='ios', action='store_true',
		default=False,
		help='Build for iOS with XCode 5 or higher.')
	parser.add_argument('-vita', dest='vita', action='store_true',
		default=False,
		help='Build for PS Vita with Visual Studio 2010.')
	parser.add_argument('-360', dest='xbox360', action='store_true',
		default=False,
		help='Build for XBox 360 with Visual Studio 2010.')
	parser.add_argument('-wiiu', dest='wiiu', action='store_true',
		default=False,
		help='Build for WiiU with Visual Studio 2013.')
	parser.add_argument('-dsi', dest='dsi', action='store_true',
		default=False,
		help='Build for Nintendo DSI with Visual Studio 2015.')

	parser.add_argument('-release', dest='release', action='store_true',
		default=False,
		help='Create a release target (Default is release/debug/internal)')
	parser.add_argument('-debug', dest='debug', action='store_true',
		default=False,
		help='Create a debug target')
	parser.add_argument('-internal', dest='internal', action='store_true',
		default=False,
		help='Create an internal target')
	parser.add_argument('-finalfolder', dest='finalfolder', action='store_true',
		default=False,
		help='Add a script to copy a release build to a folder and check in with Perforce')
	parser.add_argument('-app', dest='app', action='store_true',
		default=False,
		help='Build an application instead of a tool')
	parser.add_argument('-lib', dest='library', action='store_true',
		default=False,
		help='Build a library instead of a tool')

	parser.add_argument('-f',dest='jsonfiles',action='append',
		help='Input file to process')
	parser.add_argument('-v','-verbose',dest='verbose',action='store_true',
		default=False,
		help='Verbose output.')
	parser.add_argument('-default',dest='default',action='store_true',
		help='Create a default projects.py file')

	parser.add_argument('args',nargs=argparse.REMAINDER,help='project filenames')

	args = parser.parse_args()
	verbose = args.verbose

	print 'xcodeversion ' + str(args.xcodeversion)
	
	#
	# Shall a default file be generated?
	#
	
	if args.default==True:
		savedefault(os.path.join(workingDir,'projects.py'))
		return 0
		
	#
	# Process defaults first
	#

	solution = SolutionData()
	solution.verbose = verbose
	solution.workingDir = workingDir
	
	#
	# No input file?
	#
	
	if args.jsonfiles==None:
		projectpathname = os.path.join(workingDir,'projects.json')
		if len(sys.argv)==1 and os.path.isfile(projectpathname)==True:
			args.jsonfiles = ['projects.json']
		else:
			error = solution.processcommandline(args)
			return error
	
	#
	# Read in the json file
	#
	
	for input in args.jsonfiles:
		projectpathname = os.path.join(workingDir,input)
		if os.path.isfile(projectpathname)!=True:
			print input + ' was not found'
			return 2
	
		#
		# To allow '#' and '//' comments, the file has to be pre-processed
		#
		
		fp = open(projectpathname,'r')
		jsonlines = fp.readlines()
		fp.close()
		
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
		except Exception as e:
			print str(e) + ' in parsing ' + projectpathname
			return 2

		#
		# Process the list of commands
		#
	
		if type(myjson) is list:
			error = solution.process(myjson)
		else:
			print 'Invalid json input file!'
			error = 2
		if error!=0:
			break

	return error

#
# If invoked as a tool, call the main with the current working directory
#

if __name__ == '__main__':
	sys.exit(main(os.getcwd()))
