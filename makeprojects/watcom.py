#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Sub file for makeprojects.
# Handler for Watcom WMAKE projects
#

# Copyright 1995-2018 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

#
## \package makeprojects.watcom
# This module contains classes needed to generate
# project files intended for use by Open Watcom
# WMAKE 1.9 or higher
#

import os
import burger
import makeprojects.core
from makeprojects import FileTypes, ProjectTypes, PlatformTypes

#
# Create an OpenWatcom makefile
#

def generate(solution, perforce=False, verbose=False):

	#
	# Now, let's create the project file
	#

	codefiles, includedirectories = solution.getfilelist(
		[FileTypes.h, FileTypes.cpp, FileTypes.x86])
	platformcode = solution.platform.getshortcode()
	idecode = solution.ide.getshortcode()
	projectfilename = str(solution.projectname + idecode + platformcode)
	projectpathname = os.path.join(
		solution.workingDir, projectfilename + '.wmk')

	#
	# Save out the filenames
	#

	listh = makeprojects.core.pickfromfilelist(codefiles, FileTypes.h)
	listcpp = makeprojects.core.pickfromfilelist(codefiles, FileTypes.cpp)
	listx86 = makeprojects.core.pickfromfilelist(codefiles, FileTypes.x86)
	listwindowsresource = []
	# if platformcode=='win':
	#	listwindowsresource = makeprojects.core.pickfromfilelist(codefiles, makeprojects.coreFileTypes.rc)

	alllists = listh + listcpp + listx86 + listwindowsresource

	burger.perforce_edit(projectpathname)
	fp = open(projectpathname, 'w')
	fp.write(
		'#\n'
		'# Build ' + solution.projectname + ' for ' + solution.platform.name + '\n'
		'#\n\n'
		'#\n'
		'# sourcedir = Set the work directories for the source\n'
		'#\n\n')

	filelist = []
	for item in alllists:
		filelist.append(burger.convert_to_windows_slashes(item.filename))

	filelist = sorted(filelist, cmp=lambda x, y: cmp(x, y))

	sourcedir = []
	for item in filelist:
		#
		# Remove the filename
		#
		index = item.rfind('\\')
		if index == -1:
			entry = item
		else:
			entry = item[0:index]
		if not entry in sourcedir:
			sourcedir.append(entry)

	fp.write("sourcedir = ")
	string = ''
	for item in sourcedir:
		string = string + item + ';'

	if string:
		# Get rid of the trailing semi colon
		string = string[0:len(string)-1]
		fp.write(string)

	fp.write(
        '\n\n'
		'#\n'
		'# Name of the output library\n'
		'#\n\n'
		'projectname = ' + solution.projectname + '\n\n'
		'#\n'
		'# includedir = Header includes\n'
		'#\n\n'
		'includedir = $(sourcedir)')

	if solution.includefolders:
		string = ''
		for item in solution.includefolders:
			string = string + ';' + burger.convert_to_windows_slashes(item)
		fp.write(string)

	fp.write(
        '\n\n'
		'#\n'
		'# Object files to work with for the library\n'
		'#\n\n')

	string = 'objs= &'
	for item in filelist:
		if not item.endswith('.h'):
			index = item.rfind('.')
			if index == -1:
				entry = item
			else:
				entry = item[0:index]

			index = entry.rfind('\\')
			if index == -1:
				entry = entry
			else:
				entry = entry[index+1:len(entry)]

			string = string + '\n\t$(A)\\' + entry + '.obj &'

	# Get rid of the trailing ampersand and space
	string = string[0:len(string)-2]
	fp.write(string + '\n\n')

	if solution.finalfolder != None:
		final = burger.convert_to_windows_slashes(solution.finalfolder)
		if final.endswith('\\'):
			final = final[0:len(final)-1]

		fp.write('#\n'
				 '# Final location folder\n'
				 '#\n\n'
				 'finalfolder = ' + final + '\n\n')

	fp.write(
		'#\n'
		'# Create the build environment\n'
		'#\n\n'
		'!include $(%sdks)\\watcom\\burger.mif\n\n'
		'#\n'
		'# List the names of all of the final binaries to build\n'
		'#\n\n'
		'all : .SYMBOLIC\n')

	platforms = []
	if solution.platform == PlatformTypes.msdos:
		platforms = ['x32', 'dos4gw']
	elif solution.platform == PlatformTypes.windows:
		platforms = ['w32']

	if solution.projecttype == ProjectTypes.library:
		suffix = 'lib'
	else:
		suffix = 'exe'

	for theplatform in platforms:
		if theplatform == 'dos4gw':
			shortplatform = '4gw'
		else:
			shortplatform = theplatform

		for target in solution.configurations:
			fp.write('\t@set config=' + str(target) + '\n')
			fp.write('\t@set target=' + theplatform + '\n')
			fp.write('\t@%make $(destdir)\\$(projectname)wat' + shortplatform + target.getshortcode() +
					 '.' + suffix + '\n')

	fp.write('\n' +
			 projectfilename + '.wmk :\n'
			 '\t@%null\n'
			 '\n'
			 '#\n'
			 '# A = The object file temp folder\n'
			 '#\n'
			 '\n')

	for theplatform in platforms:
		for target in solution.configurations:
			if theplatform == 'dos4gw':
				theplatform = '4gw'
			fp.write('A = $(basetempdir)wat' + theplatform + target.getshortcode() + '\n'
					 '$(destdir)\\$(projectname)wat' + theplatform + target.getshortcode() + '.' +
					 suffix + ' : $+$(OBJS)$- ' + projectfilename + '.wmk\n'
					 '\t@if not exist $(destdir) @!mkdir $(destdir)\n')
			if solution.projecttype == ProjectTypes.library:

				fp.write('\t@SET WOW=$+$(OBJS)$-\n'
						 '\t@WLIB -q -b -c -n $^@ @WOW\n')

				if solution.finalfolder != None:
					fp.write('\t@"$(%perforce)\\p4" edit "$(finalfolder)\\$^."\n'
							 '\t@copy /y "$^@" "$(finalfolder)\\$^."\n'
							 '\t@"$(%perforce)\\p4" revert -a "$(finalfolder)\\$^."\n\n')
			else:
				fp.write('\t@SET WOW={$+$(OBJS)$-}\n'
						 '\t@$(LINK) $(LFlagsw32) $(LFlags' + str(target) + ') LIBRARY burgerlibwat' +
						 theplatform + target.getshortcode() + '.lib NAME $^@ FILE @wow\n\n')

	fp.close()
	return 0
