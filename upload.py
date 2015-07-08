#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Build and upload the egg file
#

# Copyright 2013-2015 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

import os
import sys
import burger
import argparse
import makeprojects

#
# Clean up all the temp files after uploading
# Helps in keeping source control from having to track
# temp files
#

def clean(workingDir):

	dirlist = [
		'makeprojects.egg-info',
		'makeprojects-' + makeprojects.__version__,
		'dist',
		'build',
		'temp'
	]
	
	#
	# Delete all folders, including read only files
	#
	
	for item in dirlist:
		burger.deletedirectory(os.path.join(workingDir,item),True)

	#
	# Delete all *.pyc and *.pyo files
	#
	
	nameList = os.listdir(workingDir)
	for baseName in nameList:
		fileName = os.path.join(workingDir,baseName)
		# Is it a file?
		if os.path.isfile(fileName):
			if baseName.endswith('.pyc') or baseName.endswith('.pyo') :
				os.remove(fileName)

#
# Upload the documentation to the server
#

def main(workingDir):

	
	# Parse the command line
	
	parser = argparse.ArgumentParser(
		description='Build and upload a python distribution. Copyright by Rebecca Ann Heineman',
		usage='upload [-h] [-d]')

	parser.add_argument('-c','-clean', dest='clean', action='store_true',
		default=False,
		help='Perform a clean.')

	parser.add_argument('-u','-upload', dest='upload', action='store_true',
		default=False,
		help='Perform a full build and upload to https://pypi.python.org.')

	args = parser.parse_args()

	error = 0
	
	#
	# Perform the upload
	#
	
	if args.upload==True:
		sys.argv = ['setup.py','sdist','upload']
		error = execfile('setup.py')
		
		if error == 0:
			
			# Clean up
			args.clean = True
		else:
			args.clean = False

	else:
		if not args.clean==True:
			sys.argv = ['setup.py','build','sdist']
			error = execfile('setup.py')
	
	#
	# Do a clean and exit
	#
	
	if args.clean==True:
		clean(workingDir)
		error = 0

	return error
		
# 
# If called as a function and not a class,
# call my main
#

if __name__ == "__main__":
	sys.exit(main(os.path.dirname(os.path.abspath(__file__))))
