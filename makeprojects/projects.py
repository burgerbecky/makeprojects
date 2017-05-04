#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Python file to create a project file using makeprojects
#
# Get the makeprojects library
#

try:
	import makeprojects
except ImportError:
	print 'Module "makeprojects" was not found, please install with "pip install -U makeprojects"'
	import sys
	sys.exit(1)

appname = 'greatapp'

#
# Create the solution file.
#

solution = makeprojects.newsolution(appname)

#
# Create the main project file
#

#project = makeprojects.newproject(appname)
#solution.addproject(project)

#project.setconfigurations(['Debug','Internal','Release'])
#project.setplatform(project.Windows)
#project.addsourcefiles(['./*.*'])

#solution.save(solution.xcode3)

#[
#	// Initial settings
#	{
#		// Name of the project (And output filename)
#		"projectname": "greatapp",
#		// Kind of project (library,game,screensaver,tool)
#		"kind": "tool",
#		// Configurations to generate (Debug,Internal,Release,Profile)
#		"configurations": ["Debug","Internal","Release"],
#		// List of filenames to exclude from parsing
#		"exclude": [],
#		// List of additional defines
#		"defines": [],
#		// Folder to store the final binary that's checked into Perforce
#		"finalfolder": "",
#		// Operating system target to build for (windows,macosx,linux,ps3,ps4,xbox,
#		// xbox360,xboxone,shield,ios,mac,msdos,beos,ouya,vita)
#		"platform" : "windows",
#		// Folders to scan for source code (Append with /*.* for recursive search)
#		"sourcefolders": ["./*.*"],
#		// Folders to add for include files (No file scanning is performed)
#		"includefolders" : []
#	},
#	// Windows -> Visual Studio 2010
#	// (xcode3,xcode4,xcode5,vs2003,vs2005,vs2008,vs2010,vs2012,vs2015,codeblocks,watcom,codewarrior)
#	"vs2010"
#]
