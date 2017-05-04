#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Create projects from a json description file
# for XCode, Visual Studio, CodeBlocks and
# other IDEs
#

# Copyright 1995-2016 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

import os
import json
import glob
import shutil
import sys
import platform
import uuid
import hashlib
import subprocess
import copy
import burger
import argparse
import enum
from enum import IntEnum, unique, EnumMeta
import re
import visualstudio
import xcode

#
## \package makeprojects.core
# Core contains the master dispatchers to generate
# a project file for many popular IDEs
#

#
## Class to allow auto generation of enumerations
#

class auto_enum(EnumMeta):
	def __new__(metacls,cls,bases,classdict):
		original_dict = classdict
		# Replace the dictionary with a new copy
		classdict = enum._EnumDict()
		for k,v in original_dict.items():
			classdict[k] = v

		temp = type(classdict)()
		names = set(classdict._member_names)

		# Start the enumeration with this value
		i = 0
		for k in classdict._member_names:
			v = classdict[k]
			# Does this entry need assignment?
			if v != ():
				# Use the assigned value
				i = v
			temp[k] = i
			# Increment for the next assigned value
			i += 1

		# Update the dictionary	
		for k, v in classdict.items():
			if k not in names:
				temp[k] = v

		# Pass the dictionary up
		return super(auto_enum, metacls).__new__(metacls, cls, bases, temp)

#
## Integer enumerator
#

AutoIntEnum = auto_enum('AutoIntEnum', (IntEnum,), {})

#
## Enumeration of supported file types for input
#

class FileTypes(AutoIntEnum):
	## User file type (Unknown)
	user = ()
	## Non compiling file type
	generic = ()
	## Compile as C++ 
	cpp = ()
	## C/C++ header
	h = ()
	## Object-C
	m = ()
	## XML text file
	xml = ()
	## Windows resource file
	rc = ()
	## Mac OS resource file
	r = ()
	## HLSL DirectX Shader
	hlsl = ()
	## GLSL OpenGL Shader
	glsl = ()
	## Xbox 360 DirectX Shader
	x360sl = ()
	## Playstation Vita CG Shader
	vitacg = ()
	## Mac OSX Framework
	frameworks = ()
	## Library
	library = ()
	## Exe
	exe = ()
	## XCode config file
	xcconfig = ()
	## X86 assembly
	x86 = ()
	## X64 assembly
	x64 = ()
	## 6502/65812 assembly
	a65 = ()
	## PowerPC assembly
	ppc = ()
	## 680x0 assembly
	a68 = ()
	## Image files
	image = ()
	## Windows icon files
	ico = ()
	## MacOSX icon files
	icns = ()

#
## Enumeration of supported project types
#

class ProjectTypes(AutoIntEnum):
	## Code library
	library = ()
	## Command line tool
	tool = ()
	## Application
	game = ()
	## Screen saver
	screensaver = ()
	## Shared library (DLL)
	sharedlibrary = ()
	## Empty project
	empty = ()

#
## Enumeration of supported configuration types
#

class ConfigurationTypes(AutoIntEnum):
	## Debug
	debug = ()
	## Release builds
	release = ()
	## Internal builds (Debug enabled, full optimizations)
	internal = ()
	## Profile builds
	profile = ()

#
## Enumeration of supported IDEs
#

class IDETypes(AutoIntEnum):
	## Visual studio 2003
	vs2003 = ()
	## Visual studio 2005
	vs2005 = ()
	## Visual studio 2008
	vs2008 = ()
	## Visual studio 2010
	vs2010 = ()
	## Visual studio 2012
	vs2012 = ()
	## Visual studio 2013
	vs2013 = ()
	## Visual studio 2015
	vs2015 = ()
	## Open Watcom 1.9 or later
	watcom = ()
	## Codewarrior 9 (Windows)
	codewarrior9 = ()
	## Codewarrior 10 (Mac OS Carbon)
	codewarrior10 = ()
	## XCode 3 (PowerPC 3.1.4 is the target version)
	xcode3 = ()
	## XCode 4
	xcode4 = ()
	## XCode 5
	xcode5 = ()
	## XCode 6
	xcode6 = ()
	## XCode 7
	xcode7 = ()
	## Codeblocks
	codeblocks = ()

	#
	# Create the ide code from the ide type
	#

	def getidecode(self):
		# Microsoft Visual Studio
		if self == self.vs2003:
			return 'vc7'
		if self == self.vs2005:
			return 'vc8'
		if self == self.vs2008:
			return 'vc9'
		if self == self.vs2010:
			return 'v10'
		if self == self.vs2012:
			return 'v12'
		if self == self.vs2013:
			return 'v13'
		if self == self.vs2015:
			return 'v15'

		# Watcom MAKEFILE
		if self == self.watcom:
			return 'wat'

		# Metrowerks / Freescale CodeWarrior
		if self == self.codewarrior9:
			return 'cw9'
		if self == self.codewarrior10:
			return 'c10'

		# Apple's XCode
		if self == self.xcode3:
			return 'xc3'
		if self == self.xcode4:
			return 'xc4'
		if self == self.xcode5:
			return 'xc5'
		if self == self.xcode6:
			return 'xc6'
		if self == self.xcode7:
			return 'xc7'

		# Codeblocks
		if self == self.codeblocks:
			return 'cdb'
		return None

#
## Enumeration of supported target platforms
#

class PlatformTypes(AutoIntEnum):
	## Windows 32 and 64 bit Intel
	windows = ()
	## Windows 32 bit intel only
	win32 = ()
	## Window 64 bit intel only
	win64 = ()

	## Mac OSX, all CPUs
	macosx = ()
	## Mac OSX PowerPC 32 bit only
	macosxppc32 = ()
	## Mac OSX PowerPC 64 bit only
	macosxppc64 = ()
	## Mac OSX Intel 32 bit only
	macosxintel32 = ()
	## Mac OSX Intel 64 bit only
	macosxintel64 = ()

	## Mac OS 9, all CPUs
	macos9 = ()
	## Mac OS 9 680x0 only
	macos968k = ()
	## Mac OS 9 PowerPC 32 bit only
	macos9ppc = ()
	## Mac OS Carbon, all CPUs
	maccarbon = ()
	## Mac OS Carbon 680x0 only (CFM)
	maccarbon68k = ()
	## Mac OS Carbon PowerPC 32 bit only
	maccarbonppc = ()

	## iOS, all CPUs
	ios = ()
	## iOS 32 bit ARM only
	ios32 = ()
	## iOS 64 bit ARM only
	ios64 = ()
	## iOS emulator, all CPUs
	iosemu = ()
	## iOS emulator 32 bit Intel only
	iosemu32 = ()
	## iOS emulator 64 bit Intel only
	iosemu64 = ()

	## Microsoft Xbox classic
	xbox = ()
	## Microsoft Xbox 360
	xbox360 = ()
	## Microsoft Xbox ONE
	xboxone = ()

	## Sony PS3
	ps3 = ()
	## Sony PS4
	ps4 = ()
	## Sony Playstation VITA
	vita = ()

	## Nintendo WiiU
	wiiu = ()
	## Nintendo 3DS
	dsi = ()
	## Nintendo DS
	ds = ()

	## Generic Android
	android = ()
	## nVidia SHIELD
	shield = ()
	## Ouya (Now Razor)
	ouya = ()
	## Generic Linux
	linux = ()
	## MSDOS
	msdos = ()
	## BeOS
	beos = ()

	#
	## Convert the enumeration to a 3 letter code for filename suffix
	#

	def getplatformcode(self):
		# Windows targets
		if self == self.windows:
			return 'win'
		if self == self.win32:
			return 'winx86'
		if self == self.win64:
			return 'winx64'

		# Mac OSX targets
		if self == self.macosx:
			return 'osx'
		if self == self.macosxppc32:
			return 'osxp32'
		if self == self.macosxppc64:
			return 'osxp64'
		if self == self.macosxintel32:
			return 'osxx86'
		if self == self.macosxintel64:
			return 'osxx64'

		# Mac OS targets (Pre-OSX)
		if self == self.macos9:
			return 'mac'
		if self == self.macos968k:
			return 'mac68k'
		if self == self.macos9ppc:
			return 'macppc'
		if self == self.maccarbon:
			return 'car'
		if self == self.maccarbon68k:
			return 'car68k'
		if self == self.maccarbonppc:
			return 'carppc'

		# iOS target
		if self == self.ios:
			return 'ios'
		if self == self.ios32:
			return 'iosa32'
		if self == self.ios64:
			return 'iosa64'
		if self == self.iosemu:
			return 'ioe'
		if self == self.iosemu32:
			return 'ioex86'
		if self == self.iosemu64:
			return 'ioex64'

		# Microsoft Xbox versions
		if self == self.xbox:
			return 'xbx'
		if self == self.xbox360:
			return 'x36'
		if self == self.xboxone:
			return 'one'

		# Sony platforms
		if self == self.ps3:
			return 'ps3'
		if self == self.ps4:
			return 'ps4'
		if self == self.vita:
			return 'vit'

		# Nintendo platforms
		if self == self.wiiu:
			return 'wiu'
		if self == self.dsi:
			return 'dsi'
		if self == self.ds:
			return '2ds'

		# Google platforms
		if self == self.android:
			return 'and'
		if self == self.shield:
			return 'shi'
		if self == self.ouya:
			return 'oya'

		# Linux platforms
		if self == self.linux:
			return 'lnx'

		# MSDOS (Watcom or Codeblocks)
		if self == self.msdos:
			return 'dos'

		# BeOS
		if self == self.beos:
			return 'bos'
		return None

	#
	# Create the platform codes from the platform type for Visual Studio
	#

	def getvsplatform(self):
		# Windows targets
		if self==PlatformTypes.windows:
			return ['Win32','x64']
		if self==PlatformTypes.win32:
			return ['Win32']
		if self==PlatformTypes.win64:
			return ['x64']

		# Microsoft Xbox versions
		if self==PlatformTypes.xbox:
			return ['Xbox']
		if self==PlatformTypes.xbox360:
			return ['Xbox 360']
		if self==PlatformTypes.xboxone:
			return ['Xbox ONE']

		# Sony platforms
		if self==PlatformTypes.ps3:
			return ['PS3']
		if self==PlatformTypes.ps4:
			return ['ORBIS']
		if self==PlatformTypes.vita:
			return ['PSVita']

		# Nintendo platforms
		if self==PlatformTypes.wiiu:
			return ['Cafe']
		if self==PlatformTypes.dsi:
			return ['CTR']

		# Google platforms
		if self==PlatformTypes.android:
			return ['Android']
		if self==PlatformTypes.shield:
			return ['Tegra-Android',
				'ARM-Android-NVIDIA',
				'AArch64-Android-NVIDIA',
				'x86-Android-NVIDIA',
				'x64-Android-NVIDIA']
		return []

#
## List of default file extensions and mapped types
#
# When the directory is scanned for input files,
# the files will be tested against this list
# with a forced lowercase filename 
# and determine the type
# of compiler to assign to an input file
#
# This list can be appended or modified to allow
# other file types to be processed
#

defaultcodeextensions = [
	['.c',FileTypes.cpp],			# C/C++ source code
	['.cc',FileTypes.cpp],
	['.cpp',FileTypes.cpp],
	['.c++',FileTypes.cpp],
	['.hpp',FileTypes.h],			# C/C++ header files
	['.h',FileTypes.h],
	['.hh',FileTypes.h],
	['.i',FileTypes.h],
	['.inc',FileTypes.h],
	['.m',FileTypes.m],				# MacOSX / iOS Objective-C
	['.plist',FileTypes.xml],		# MacOSX / iOS plist files
	['.rc',FileTypes.rc],			# Windows resources
	['.r',FileTypes.r],				# MacOS classic resources
	['.rsrc',FileTypes.r],
	['.hlsl',FileTypes.hlsl],		# DirectX shader files
	['.vsh',FileTypes.glsl],		# OpenGL shader files
	['.fsh',FileTypes.glsl],
	['.glsl',FileTypes.glsl],
	['.x360sl',FileTypes.x360sl],	# Xbox 360 shader files
	['.vitacg',FileTypes.vitacg],	# PS Vita shader files
	['.xml',FileTypes.xml],			# XML data files
	['.x86',FileTypes.x86],			# Intel ASM 80x86 source code
	['.x64',FileTypes.x64],			# AMD 64 bit source code
	['.a65',FileTypes.a65],			# 6502/65816 source code
	['.ppc',FileTypes.ppc],			# PowerPC source code
	['.a68',FileTypes.a68],			# 680x0 source code
	['.ico',FileTypes.ico],			# Windows icon file
	['.icns',FileTypes.icns],		# Mac OSX Icon file
	['.png',FileTypes.image],		# Art files
	['.jpg',FileTypes.image],
	['.bmp',FileTypes.image]
]

#
## Object for each input file to insert to a solution
#
# For every file that could be included into a project file
# one of these objects is created and attached to a solution object
# for processing
#

class SourceFile:

	#
	## Default constructor
	#
	# \param self The 'this' reference
	# \param relativepathname Filename of the input file (relative to the root)
	# \param directory Pathname of the root directory
	# \param filetype Compiler to apply
	# \sa defaultcodeextensions
	#

	def __init__(self,relativepathname,directory,filetype):
		# Sanity check
		if not isinstance(filetype,FileTypes):
			raise TypeError("parameter 'filetype' must be of type FileTypes")

		## File base name with extension (Converted to use windows style slashes on creation)
		self.filename = burger.converttowindowsslashes(relativepathname)

		## Directory the file is found in (Full path)
		self.directory = directory

		## File type enumeration, see: \ref FileTypes
		self.type = filetype
	
	#
	## Given a filename with a directory, extract the filename, leaving only the directory
	#
	# To determine if the file should be in a sub group in the project, scan
	# the filename to find if it's a base filename or part of a directory
	# If it's a basename, return an empty string.
	# If it's in a folder, remove any ..\\ prefixes and .\\ prefixes
	# and return the filename with the basename removed
	#
	# \param self The 'this' reference
	#

	def extractgroupname(self):
		index = self.filename.rfind('\\')
		if index==-1:
			return ''

		#
		# Remove the basename
		#
		
		newname = self.filename[0:index]
	
		#
		# If there are ..\\ at the beginning, remove them
		#
	
		while newname.startswith('..\\'):
			newname = newname[3:len(newname)]
	
		#
		# If there is a .\\, remove the single prefix
		#
	
		while newname.startswith('.\\'):
			newname = newname[2:len(newname)]

		return newname
		
#
## Object for processing a project file
#
# This object contains all of the items needed to
# create a project 
# \note Oon most IDEs, this is merged into
# one file, but Visual Studio 2010 and higher
# generates a project file for each project
#

class ProjectData:
	def __init__(self,name='project',projecttype=ProjectTypes.tool,suffixenable=False):
		# Sanity check
		if not isinstance(projecttype,ProjectTypes):
			raise TypeError("parameter 'projecttype' must be of type ProjectTypes")
	
		## Root directory (Default None)
		self.workingDir = None
	
		## Type of project, tool is default ('tool', 'game', 'library')
		self.projecttype = projecttype
	
		## Generic name for the project, 'project' is default
		self.projectname = name
	
		## No parent solution yet
		self.solution = None
	
		## Type of ide
		# 'vs2015', 'vs2013', 'vs2012', 'vs2010', 'vs2008', 'vs2005',
		# 'xcode3', 'xcode4', 'xcode5', 'codewarrior', 'codeblocks',
		# 'watcom'
		self.ide = IDETypes.vs2010
	
		## Generate a windows project as a default
		self.platform = PlatformTypes.windows
	
		## Generate the three default configurations
		self.configurations = ['Debug','Internal','Release']
	
		## No special folder for the final binary
		self.finalfolder = None
	
		## Don't exclude any files
		self.exclude = []
	
		## No special #define for C/C++ code
		self.defines = []
	
		## Scan at the current folder
		self.sourcefolders = ['.']
	
		## No extra folders for include files
		self.includefolders = []
	
		## Initial array of SourceFile in the solution
		self.codefiles = []

		## Initial array of ProjectData records that need to be built first
		self.dependentprojects = []

		## Create default XCode object
		self.xcode = xcode.Defaults()
		
		## Create default Visual Studio object
		self.visualstudio = visualstudio.Defaults()

	#
	## Set the names of the configurations this project will support
	#
	# Given a string or an array of strings, replace the
	# configurations with the new list.
	#
	# \param self The 'this' reference
	# \param configurations String or an array of strings for the new configuration list
	#

	def setconfigurations(self,configurations):
		# Force to a list
		self.configurations = burger.converttoarray(configurations)

	#
	## Set the names of the configurations this project will support
	#
	# Given a string or an array of strings, replace the
	# configurations with the new list.
	#
	# \param self The 'this' reference
	# \param configurations String or an array of strings for the new configuration list
	#

	def setplatform(self,platform):
		# Sanity check
		if not isinstance(platform,PlatformTypes):
			raise TypeError("parameter 'platform' must be of type PlatformTypes")
		self.platform = platform


	def adddependency(self,project):
		# Sanity check
		if not isinstance(project,ProjectData):
			raise TypeError("parameter 'project' must be of type ProjectData")
		self.dependentprojects.append(project)

#
## Object for processing a solution file
#
# This object contains all of the items needed to
# create a solution
#

class SolutionData:
	def __init__(self,name='project',projecttype=ProjectTypes.tool,suffixenable=False):
		# Sanity check
		if not isinstance(projecttype,ProjectTypes):
			raise TypeError("parameter 'projecttype' must be of type ProjectTypes")
	
		## True if verbose output is requested (Default False)
		self.verbose = False

		## Root directory (Default None)
		self.workingDir = os.getcwd()
	
		## Type of project, tool is default ('tool', 'game', 'library')
		self.projecttype = projecttype
	
		## Generic name for the project, 'project' is default
		self.projectname = name
	
		## Type of ide
		# 'vs2015', 'vs2013', 'vs2012', 'vs2010', 'vs2008', 'vs2005',
		# 'xcode3', 'xcode4', 'xcode5', 'codewarrior', 'codeblocks',
		# 'watcom'
		self.ide = IDETypes.vs2010
	
		## Generate a windows project as a default
		self.platform = PlatformTypes.windows
	
		## Generate the three default configurations
		self.configurations = ['Debug','Internal','Release']
	
		## No special folder for the final binary
		self.finalfolder = None
	
		## Don't exclude any files
		self.exclude = []
	
		## No special #define for C/C++ code
		self.defines = []
	
		## Scan at the current folder
		self.sourcefolders = ['.']
	
		## No extra folders for include files
		self.includefolders = []
	
		## Initial array of SourceFile in the solution
		self.codefiles = []

		## Initial array of ProjectData records for projects
		self.projects = []

		## Create default XCode object
		self.xcode = xcode.Defaults()
		
		## Create default Visual Studio object
		self.visualstudio = visualstudio.Defaults()

	#
	## Add a project to the list of projects found in this solution
	#
	# Given a new ProjectData class instance, append it
	# to the list of projects that this solution is
	# managing.
	#
	# \param self The 'this' reference
	# \param project Reference to an instance of a ProjectData
	#

	def addproject(self,project):
		# Sanity check
		if not isinstance(project,ProjectData):
			raise TypeError("parameter 'project' must be of type ProjectData")

		project.solution = self
		self.projects.append(project)

	#
	## Generate a project file and write it out to disk
	#

	def generate(self,ide,platform):
		# Sanity check
		if not isinstance(ide,IDETypes):
			raise TypeError("parameter 'ide' must be of type IDETypes")
		
		self.platform = platform

		if ide==IDETypes.vs2003 or \
			ide==IDETypes.vs2005 or \
			ide==IDETypes.vs2008 or \
			ide==IDETypes.vs2010 or \
			ide==IDETypes.vs2012 or \
			ide==IDETypes.vs2013 or \
			ide==IDETypes.vs2015:
			return visualstudio.generate(self,ide)

		return 10

	#
	## Given a json record, process all the sub sections
	#
	# Given a dictionary created by a json file or
	# manually, update the solution to the new data
	#
	# \param self The 'this' reference	
	# \param myjson Dictionary with key value pairs
	#
	# Acceptable keys
	# \li 'finalfolder' = pathname to store final release binary
	# \li 'kind' = 'tool', 'library', 'game'
	# \li 'projectname' = Name of the project's filename (basename only)
	# \li 'platform' = 'windows', 'macosx', 'linux', 'ps3', 'ps4', 'vita',
	# 'xbox', 'xbox360', 'xboxone', 'shield', 'ios', 'mac', 'msdos',
	# 'beos', 'ouya', 'wiiu', 'dsi'
	# \li 'configurations' = ['Debug', 'Release', 'Internal']
	# \li 'sourcefolders' = ['.','source']
	# \li 'exclude' = [] (List of files to exclude from processing)
	# \li 'defines' = [] (List of #define to add to the project)
	# \li 'includefolders' = [] (List of folders to add for #include )
	# \li 'xcode' = dir() (Keys and values for special cases for xcode projects)
	# \li 'visualstudio' = dir() (Keys and values for special cases for visual studio projects)
	#
	# \sa makeprojects.xcode or makeprojects.visualstudio
	#

	def processjson(self,myjson):
		error = 0
		for key in myjson.keys():
			if key=='finalfolder':
				if myjson[key]=="":
					self.finalfolder = None
				else:
					self.finalfolder = myjson[key]
					
			elif key=='kind':
				# Convert json token to enumeration (Will assert if not enumerated)
				self.projecttype = ProjectTypes[myjson[key]]
			elif key=='projectname':
				self.projectname = myjson[key]
			elif key=='platform':
				self.platform = PlatformTypes[myjson[key]]
				
			elif key=='configurations':
				self.configurations = burger.converttoarray(myjson[key])
			elif key=='sourcefolders':
				self.sourcefolders = burger.converttoarray(myjson[key])
			elif key=='exclude':
				self.exclude = burger.converttoarray(myjson[key])
			elif key=='defines':
				self.defines = burger.converttoarray(myjson[key])
			elif key=='includefolders':
				self.includefolders = burger.converttoarray(myjson[key])

			#
			# Handle IDE specific data
			#
			
			elif key=='xcode':
				error = self.xcode.loadjson(myjson[key])
			elif key=='visualstudio':
				error = self.visualstudio.loadjson(myjson[key])
			else:
				print 'Unknown keyword "' + str(key) + '" with data "' + str(myjson[key]) + '" found in json file'
				error = 1
				
			if error!=0:
				break

		return error
	

	#
	# The script is an array of objects containing solution settings
	# and a list of IDEs to output scripts
	#

	def process(self,myjson):
		error = 0
		for item in myjson:
			if type(item) is dict:
				error = self.processjson(item)
			elif item=='vs2015':
				self.ide = IDETypes.vs2015
				error = visualstudio.generateold(self,IDETypes.vs2015)
			elif item=='vs2013':
				self.ide = IDETypes.vs2013
				error = visualstudio.generateold(self,IDETypes.vs2013)
			elif item=='vs2012':
				self.ide = IDETypes.vs2012
				error = visualstudio.generateold(self,IDETypes.vs2012)
			elif item=='vs2010':
				self.ide = IDETypes.vs2010
				error = visualstudio.generateold(self,IDETypes.vs2010)
			elif item=='vs2008':
				self.ide = IDETypes.vs2008
				error = createvs2008solution(self)
			elif item=='vs2005':
				self.ide = IDETypes.vs2005
				error = createvs2005solution(self)
			elif item=='xcode3':
				self.ide = IDETypes.xcode3
				error = xcode.generate(self)
			elif item=='xcode4':
				self.ide = IDETypes.xcode4
				error = xcode.generate(self)
			elif item=='xcode5':
				self.ide = IDETypes.xcode5
				error = xcode.generate(self)
			elif item=='codewarrior9':
				self.ide = IDETypes.codewarrior9
				error = createcodewarriorsolution(self)
			elif item=='codewarrior10':
				self.ide = IDETypes.codewarrior10
				error = createcodewarriorsolution(self)
			elif item=='codeblocks':
				self.ide = IDETypes.codeblocks
				error = createcodeblockssolution(self)
			elif item=='watcom':
				self.ide = IDETypes.watcom
				error = createwatcomsolution(self)
			else:
				print 'Saving ' + item + ' not implemented yet'
				error = 0
			if error!=0:
				break
		return error

	#
	# Handle the command line case
	# by creating a phony json file and passing it
	# in for processing
	#

	def processcommandline(self,args):

		#
		# Fake json file and initialization record
		#
			
		dictrecord = dict()
		
		#
		# Use the work folder name as the project name
		#
		
		dictrecord['projectname'] = os.path.basename(self.workingDir)
		
		configurations = []
		if args.debug==True:
			configurations.append('Debug')
		if args.internal==True:
			configurations.append('Internal')
		if args.release==True:
			configurations.append('Release')
		if len(configurations)==0:
			configurations = ['Debug','Internal','Release']

		#
		# Only allow finalfolder when release builds are made
		#
		
		if not 'Release' in configurations:
			args.finalfolder==False

		dictrecord['configurations'] = configurations

		#
		# Lib, game or tool?
		#
		
		if args.app==True:
			kind = 'game'
		elif args.library==True:
			kind = 'library'
		else:
			kind = 'tool'
		dictrecord['kind'] = kind

		#
		# Where to find the source
		#
		
		dictrecord['sourcefolders'] = ['.','source/*.*']
		
		#
		# Save the initializer in a fake json record
		# list
		#

		myjson = [dictrecord]
		
		#
		# Xcode projects assume a macosx platform
		# unless directed otherwise
		#
		
		if args.xcode3==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'macosx'
			if args.finalfolder==True:
				initializationrecord['finalfolder'] = xcode.defaultfinalfolder
			myjson.append(initializationrecord)
			myjson.append('xcode3')

		if args.xcode4==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'macosx'
			if args.finalfolder==True:
				initializationrecord['finalfolder'] = xcode.defaultfinalfolder
			myjson.append(initializationrecord)
			myjson.append('xcode4')
			
		if args.xcode5==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'macosx'
			if args.finalfolder==True:
				initializationrecord['finalfolder'] = xcode.defaultfinalfolder
			myjson.append(initializationrecord)
			myjson.append('xcode5')

		#
		# These are windows only
		#
				
		if args.vs2005==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'windows'
			myjson.append(initializationrecord)
			myjson.append('vs2005')

		if args.vs2008==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'windows'
			myjson.append(initializationrecord)
			myjson.append('vs2008')

		if args.vs2010==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'windows'
			if args.finalfolder==True:
				initializationrecord['finalfolder'] = visualstudio.defaultfinalfolder
			myjson.append(initializationrecord)
			myjson.append('vs2010')

		if args.vs2015==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'windows'
			if args.finalfolder==True:
				initializationrecord['finalfolder'] = visualstudio.defaultfinalfolder
			myjson.append(initializationrecord)
			myjson.append('vs2015')

		if args.codeblocks==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'windows'
			myjson.append(initializationrecord)
			myjson.append('codeblocks')

		if args.codewarrior==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'windows'
			myjson.append(initializationrecord)
			myjson.append('codewarrior9')

		if args.watcom==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'windows'
			myjson.append(initializationrecord)
			myjson.append('watcom')

		#
		# These are platform specific, and as such are
		# tied to specific IDEs that are tailored to
		# the specific platforms
		#
		
		if args.xbox360==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'xbox360'
			myjson.append(initializationrecord)
			myjson.append('vs2010')

		if args.ios==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'ios'
			myjson.append(initializationrecord)
			myjson.append('xcode5')

		if args.vita==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'vita'
			myjson.append(initializationrecord)
			myjson.append('vs2010')

		if args.wiiu==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'wiiu'
			myjson.append(initializationrecord)
			myjson.append('vs2013')

		if args.dsi==True:
			initializationrecord = dict()
			initializationrecord['platform'] = 'dsi'
			myjson.append(initializationrecord)
			myjson.append('vs2015')

		if len(myjson)<2:
			print 'No default "projects.json" file found nor any project type specified'
			return 2 
	
		return self.process(myjson)
	
	
#
# Given a base directory and a relative directory
# scan for all the files that are to be included in the project
#

	def scandirectory(self,directory,codefiles,includedirectories,recurse,acceptable):

		#
		# Root directory is a special case
		#
		
		if directory=='.':
			searchDir = self.workingDir
		else:
			searchDir = os.path.join(self.workingDir,directory)

		#
		# Is this a valid directory?
		#
		if os.path.isdir(searchDir):

			#
			# Scan the directory
			#

			nameList = os.listdir(searchDir)
	
			#
			# No files added, yet (Flag for adding directory to the search tree)
			#
	
			found = False
		
			for baseName in nameList:

				#
				# Is this file in the exclusion list?
				#

				testName = baseName.lower()
				skip = False
				for item in self.exclude:
					if testName==item.lower():
						skip = True
						break

				if skip==True:
					continue

				#
				# Is it a file? (Skip links and folders)
				#
			
				fileName = os.path.join(searchDir,baseName)
				if os.path.isfile(fileName):
				
					#
					# Check against the extension list (Skip if not on the list)
					#
				
					for item in defaultcodeextensions:
						if testName.endswith(item[0]):
							
							#
							# Found a match, test if the type is in 
							# the acceptable list
							#
							
							abort = True
							for item2 in acceptable:
								if item[1]==item2:
									abort = False
									break
									
							if abort==True:
								break
									
							#
							# If the directory is the root, then don't prepend a directory
							#
							if directory=='.':
								newfilename = baseName
							else:
								newfilename = directory + os.sep + baseName
						
							#
							# Create a new entry (Using windows style slashes for consistency)
							#
							
							fileentry = SourceFile(newfilename,searchDir,item[1])
							codefiles.append(fileentry)
							if found==False:
								found = True
								includedirectories.append(directory)
							break
			
				#			
				# Process folders only if in recursion mode
				#
			
				elif recurse==True:
					if os.path.isdir(fileName):
						codefiles,includedirectories = self.scandirectory(directory + os.sep + baseName,codefiles,includedirectories,recurse,acceptable)
						
		return codefiles,includedirectories

#
# Obtain the list of source files
#

	def getfilelist(self,acceptable):

		#
		# Get the files that were manually parsed by the json
		# record
		#
	
		codefiles = list(self.codefiles)
		includedirectories = []
		for item in self.sourcefolders:
		
			#
			# Is it a recursive test?
			#
		
			recurse = False
			if item.endswith('/*.*'):
				# Remove the trailing /*.*
				item = item[0:len(item)-4]
				recurse = True
			
			#
			# Scan the folder for files
			#
			
			codefiles,includedirectories = self.scandirectory(item,codefiles,includedirectories,recurse,acceptable)

		#
		# Since the slashes are all windows (No matter what
		# host this script is running on, the sort will yield consistent
		# results so it doesn't matter what platform generated the 
		# file list, it's the same output.
		#
		
		codefiles = sorted(codefiles,cmp=lambda x,y: cmp(x.filename,y.filename))
		return codefiles,includedirectories

#
# Create the platform codes from the platform type for Visual Studio
#

def getconfigurationcode(configuration):
	if configuration=='Debug':
		return 'dbg'
	if configuration=='Release':
		return 'rel'
	if configuration=='Internal':
		return 'int'
	if configuration=='Profile':
		return 'pro'
	# The fallback is the configuration in lower case
	return configuration.lower()

#
# Prune the file list for a specific type
#

def pickfromfilelist(codefiles,itemtype):
	filelist = []
	for item in codefiles:
		if item.type == itemtype:
			filelist.append(item)
	return filelist
	

#
## Save the default projects.py file
#
# If the -default option is parsed from the command line, 
# this function is called to output a sample .py file
#
# \param destinationfile Filename for the .py file to output
#

def savedefault(destinationfile='projects.py'):
	src = os.path.join(os.path.dirname(os.path.abspath(__file__)),'projects.py')
	print src
	try:
		shutil.copyfile(src,destinationfile)
	except Exception, e:
		print e


###################################
#                                 #
# Visual Studio 2003-2013 support #
#                                 #
###################################
	
#
# Dump out a recursive tree of files to reconstruct a
# directory hiearchy for a file list
#
# Used by Visual Studio 2003, 2005 and 2008
#

def dumptreevs2005(indent,string,entry,fp,groups):
	for item in entry:
		if item!='':
			fp.write('\t'*indent + '<Filter Name="' + item + '">\n')
		if string=='':
			merged = item
		else:
			merged = string + '\\' + item
		if merged in groups:
			if item!='':
				tabs = '\t'*(indent+1)
			else:
				tabs = '\t'*indent
			sortlist = sorted(groups[merged],cmp=lambda x,y: cmp(x,y))
			for file in sortlist:
				fp.write(tabs + '<File RelativePath="' + file + '" />\n')					
		key = entry[item]
		# Recurse down the tree
		if type(key) is dict:
			dumptreevs2005(indent+1,merged,key,fp,groups)
		if item!='':
			fp.write('\t'*indent + '</Filter>\n')
	
#
# Create the solution and project file for visual studio 2005
#

def createvs2005solution(solution):
	error = visualstudio.generateold(solution,IDETypes.vs2005)
	if error!=0:
		return error
		
	#
	# Now, let's create the project file
	#
	
	acceptable = [FileTypes.h,FileTypes.cpp,FileTypes.rc,FileTypes.ico]
	codefiles,includedirectories = solution.getfilelist(acceptable)
	listh = pickfromfilelist(codefiles,FileTypes.h)
	listcpp = pickfromfilelist(codefiles,FileTypes.cpp)
	listwindowsresource = pickfromfilelist(codefiles,FileTypes.rc)

	platformcode = solution.platform.getplatformcode()
	solutionuuid = str(uuid.uuid3(uuid.NAMESPACE_DNS,str(solution.visualstudio.outputfilename))).upper()
	projectpathname = os.path.join(solution.workingDir,solution.visualstudio.outputfilename + '.vcproj')
	burger.perforceedit(projectpathname)
	fp = open(projectpathname,'w')
	
	#
	# Save off the xml header
	#
	
	fp.write('<?xml version="1.0" encoding="utf-8"?>\n')
	fp.write('<VisualStudioProject\n')
	fp.write('\tProjectType="Visual C++"\n')
	fp.write('\tVersion="8.00"\n')
	fp.write('\tName="' + solution.projectname + '"\n')
	fp.write('\tProjectGUID="{' + solutionuuid + '}"\n')
	fp.write('\t>\n')

	#
	# Write the project platforms
	#

	fp.write('\t<Platforms>\n')
	for vsplatform in solution.platform.getvsplatform():
		fp.write('\t\t<Platform Name="' + vsplatform + '" />\n')
	fp.write('\t</Platforms>\n')

	#
	# Write the project configurations
	#
	
	fp.write('\t<Configurations>\n')
	for target in solution.configurations:
		for vsplatform in solution.platform.getvsplatform():
			token = target + '|' + vsplatform
			fp.write('\t\t<Configuration\n')
			fp.write('\t\t\tName="' + token + '"\n')
			fp.write('\t\t\tOutputDirectory="bin\\"\n')
			if vsplatform=='x64':
				platformcode2 = 'w64'
			elif vsplatform=='Win32':
				platformcode2 = 'w32'
			else:
				platformcode2 = platformcode
			intdirectory = solution.projectname + solution.ide.getidecode() + platformcode2 + getconfigurationcode(target)
			fp.write('\t\t\tIntermediateDirectory="temp\\' + intdirectory + '"\n')
			if solution.projecttype==ProjectTypes.library:
				# Library
				fp.write('\t\t\tConfigurationType="4"\n')
			else:
				# Application
				fp.write('\t\t\tConfigurationType="1"\n')
			fp.write('\t\t\tUseOfMFC="0"\n')
			fp.write('\t\t\tATLMinimizesCRunTimeLibraryUsage="false"\n')
			# Unicode
			fp.write('\t\t\tCharacterSet="1"\n')
			fp.write('\t\t\t>\n')

			fp.write('\t\t\t<Tool\n')
			fp.write('\t\t\t\tName="VCCLCompilerTool"\n')
			fp.write('\t\t\t\tPreprocessorDefinitions="')
			if target=='Release':
				fp.write('NDEBUG')
			else:
				fp.write('_DEBUG')
			if vsplatform=='x64':
				fp.write(';WIN64;_WINDOWS')
			elif vsplatform=='Win32':
				fp.write(';WIN32;_WINDOWS')
			for item in solution.defines:
				fp.write(';' + item)
			fp.write('"\n')

			fp.write('\t\t\t\tStringPooling="true"\n')
			fp.write('\t\t\t\tExceptionHandling="0"\n')
			fp.write('\t\t\t\tStructMemberAlignment="4"\n')
			fp.write('\t\t\t\tEnableFunctionLevelLinking="true"\n')
			fp.write('\t\t\t\tFloatingPointModel="2"\n')
			fp.write('\t\t\t\tRuntimeTypeInfo="false"\n')
			fp.write('\t\t\t\tPrecompiledHeaderFile=""\n')
			# 8 byte alignment
			fp.write('\t\t\t\tWarningLevel="4"\n')
			fp.write('\t\t\t\tSuppressStartupBanner="true"\n')
			if solution.projecttype==ProjectTypes.library or target!='Release':
				fp.write('\t\t\t\tDebugInformationFormat="3"\n')
				fp.write('\t\t\t\tProgramDataBaseFileName="$(OutDir)\$(TargetName).pdb"\n')
			else:
				fp.write('\t\t\t\tDebugInformationFormat="0"\n')
			
			fp.write('\t\t\t\tCallingConvention="1"\n')
			fp.write('\t\t\t\tCompileAs="2"\n')
			fp.write('\t\t\t\tFavorSizeOrSpeed="1"\n')
			# Disable annoying nameless struct warnings since windows headers trigger this
			fp.write('\t\t\t\tDisableSpecificWarnings="4201"\n')

			if target=='Debug':
				fp.write('\t\t\t\tOptimization="0"\n')
			else:
				fp.write('\t\t\t\tOptimization="2"\n')
				fp.write('\t\t\t\tInlineFunctionExpansion="2"\n')
				fp.write('\t\t\t\tEnableIntrinsicFunctions="true"\n')
				fp.write('\t\t\t\tOmitFramePointers="true"\n')
			if target=='Release':
				fp.write('\t\t\t\tBufferSecurityCheck="false"\n')
				fp.write('\t\t\t\tRuntimeLibrary="0"\n')
			else:
				fp.write('\t\t\t\tBufferSecurityCheck="true"\n')
				fp.write('\t\t\t\tRuntimeLibrary="1"\n')
				
			#
			# Include directories
			#
			fp.write('\t\t\t\tAdditionalIncludeDirectories="')
			addcolon = False
			included = includedirectories + solution.includefolders
			if len(included):
				for dir in included:
					if addcolon==True:
						fp.write(';')
					fp.write(burger.converttowindowsslashes(dir))
					addcolon = True
			if platformcode=='win':
				if addcolon==True:
					fp.write(';')
				if solution.projecttype!=ProjectTypes.library or solution.projectname!='burgerlib':
					fp.write('$(BURGER_SDKS)\\windows\\burgerlib;')
				fp.write('$(BURGER_SDKS)\\windows\\directx9;$(BURGER_SDKS)\\windows\\opengl')
				addcolon = True
			fp.write('"\n')
			fp.write('\t\t\t/>\n')
			
			fp.write('\t\t\t<Tool\n')
			fp.write('\t\t\t\tName="VCResourceCompilerTool"\n')
			fp.write('\t\t\t\tCulture="1033"\n')
			fp.write('\t\t\t/>\n')
			
			if solution.projecttype==ProjectTypes.library:
				fp.write('\t\t\t<Tool\n')
				fp.write('\t\t\t\tName="VCLibrarianTool"\n')
				fp.write('\t\t\t\tOutputFile="&quot;$(OutDir)' + intdirectory + '.lib&quot;"\n')
				fp.write('\t\t\t\tSuppressStartupBanner="true"\n')
				fp.write('\t\t\t/>\n')
				if solution.finalfolder!=None:
					finalfolder = burger.converttowindowsslasheswithendslash(solution.finalfolder)
					fp.write('\t\t\t<Tool\n')
					fp.write('\t\t\t\tName="VCPostBuildEventTool"\n')
					fp.write('\t\t\t\tDescription="Copying $(TargetName)$(TargetExt) to ' + finalfolder + '"\n')
					fp.write('\t\t\t\tCommandLine="&quot;$(perforce)\p4&quot; edit &quot;' + finalfolder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
					fp.write('&quot;$(perforce)\p4&quot; edit &quot;' + finalfolder + '$(TargetName).pdb&quot;&#x0D;&#x0A;')
					fp.write('copy /Y &quot;$(OutDir)$(TargetName)$(TargetExt)&quot; &quot;' + finalfolder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
					fp.write('copy /Y &quot;$(OutDir)$(TargetName).pdb&quot; &quot;' + finalfolder + '$(TargetName).pdb&quot;&#x0D;&#x0A;')
					fp.write('&quot;$(perforce)\p4&quot; revert -a &quot;' + finalfolder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
					fp.write('&quot;$(perforce)\p4&quot; revert -a &quot;' + finalfolder + '$(TargetName).pdb&quot;&#x0D;&#x0A;"\n')
					fp.write('\t\t\t/>\n')
			else:
				fp.write('\t\t\t<Tool\n')
				fp.write('\t\t\t\tName="VCLinkerTool"\n')
				fp.write('\t\t\t\tAdditionalDependencies="burgerlib' + solution.ide.getidecode() + platformcode2 + getconfigurationcode(target) + '.lib"\n')
				fp.write('\t\t\t\tOutputFile="&quot;$(OutDir)' + intdirectory + '.exe&quot;"\n')
				fp.write('\t\t\t\tAdditionalLibraryDirectories="')
				addcolon = False
				for item in solution.includefolders:
					if addcolon==True:
						fp.write(';')
					fp.write(burger.converttowindowsslashes(item))
					addcolon = True
					
				if addcolon==True:
					fp.write(';')
				if solution.projecttype!=ProjectTypes.library:
					fp.write('$(BURGER_SDKS)\\windows\\burgerlib;')
				fp.write('$(BURGER_SDKS)\\windows\\opengl"\n')
				if solution.projecttype==ProjectTypes.tool:
					# main()
					fp.write('\t\t\t\tSubSystem="1"\n')
				else:
					# WinMain()
					fp.write('\t\t\t\tSubSystem="2"\n')
				fp.write('\t\t\t/>\n')
			fp.write('\t\t</Configuration>\n')

	fp.write('\t</Configurations>\n')	
		
	#
	# Save out the filenames
	#
	
	alllists = listh + listcpp + listwindowsresource
	if len(alllists):

		#	
		# Create groups first since Visual Studio uses a nested tree structure
		# for file groupings
		#
		
		groups = dict()
		for item in alllists:
			groupname = item.extractgroupname()
			# Put each filename in its proper group
			if groupname in groups:
				groups[groupname].append(burger.converttowindowsslashes(item.filename))
			else:
				# New group!
				groups[groupname] = [burger.converttowindowsslashes(item.filename)]
		
		#
		# Create a recursive tree in order to store out the file list
		#

		fp.write('\t<Files>\n')
		tree = dict()
		for group in groups:
			#
			# Get the depth of the tree needed
			#
			
			parts = group.split('\\')
			next = tree
			#
			# Iterate over every part
			#
			for x in xrange(len(parts)):
				# Already declared?
				if not parts[x] in next:
					next[parts[x]] = dict()
				# Step into the tree
				next = next[parts[x]]

		# Use this tree to play back all the data
		dumptreevs2005(2,'',tree,fp,groups)
		fp.write('\t</Files>\n')
		
	fp.write('</VisualStudioProject>\n')
	fp.close()

	return 0

			
#
# Create the solution and project file for visual studio 2008
#

def createvs2008solution(solution):
	error = visualstudio.generateold(solution,IDETypes.vs2008)
	if error!=0:
		return error
	#
	# Now, let's create the project file
	#
	
	acceptable = [FileTypes.h,FileTypes.cpp,FileTypes.rc,FileTypes.ico]
	codefiles,includedirectories = solution.getfilelist(acceptable)
	listh = pickfromfilelist(codefiles,FileTypes.h)
	listcpp = pickfromfilelist(codefiles,FileTypes.cpp)
	listwindowsresource = pickfromfilelist(codefiles,FileTypes.rc)

	platformcode = solution.platform.getplatformcode()
	solutionuuid = str(uuid.uuid3(uuid.NAMESPACE_DNS,str(solution.visualstudio.outputfilename))).upper()
	projectpathname = os.path.join(solution.workingDir,solution.visualstudio.outputfilename + '.vcproj')
	burger.perforceedit(projectpathname)
	fp = open(projectpathname,'w')
	
	#
	# Save off the xml header
	#
	
	fp.write('<?xml version="1.0" encoding="utf-8"?>\n')
	fp.write('<VisualStudioProject\n')
	fp.write('\tProjectType="Visual C++"\n')
	fp.write('\tVersion="9.00"\n')
	fp.write('\tName="' + solution.projectname + '"\n')
	fp.write('\tProjectGUID="{' + solutionuuid + '}"\n')
	fp.write('\t>\n')

	#
	# Write the project platforms
	#

	fp.write('\t<Platforms>\n')
	for vsplatform in solution.platform.getvsplatform():
		fp.write('\t\t<Platform Name="' + vsplatform + '" />\n')
	fp.write('\t</Platforms>\n')

	#
	# Write the project configurations
	#
	
	fp.write('\t<Configurations>\n')
	for target in solution.configurations:
		for vsplatform in solution.platform.getvsplatform():
			token = target + '|' + vsplatform
			fp.write('\t\t<Configuration\n')
			fp.write('\t\t\tName="' + token + '"\n')
			fp.write('\t\t\tOutputDirectory="bin\\"\n')
			if vsplatform=='x64':
				platformcode2 = 'w64'
			elif vsplatform=='Win32':
				platformcode2 = 'w32'
			else:
				platformcode2 = platformcode
			intdirectory = solution.projectname + solution.ide.getidecode() + platformcode2 + getconfigurationcode(target)
			fp.write('\t\t\tIntermediateDirectory="temp\\' + intdirectory + '\\"\n')
			if solution.projecttype==ProjectTypes.library:
				# Library
				fp.write('\t\t\tConfigurationType="4"\n')
			else:
				# Application
				fp.write('\t\t\tConfigurationType="1"\n')
			fp.write('\t\t\tUseOfMFC="0"\n')
			fp.write('\t\t\tATLMinimizesCRunTimeLibraryUsage="false"\n')
			# Unicode
			fp.write('\t\t\tCharacterSet="1"\n')
			fp.write('\t\t\t>\n')

			fp.write('\t\t\t<Tool\n')
			fp.write('\t\t\t\tName="VCCLCompilerTool"\n')
			fp.write('\t\t\t\tPreprocessorDefinitions="')
			if target=='Release':
				fp.write('NDEBUG')
			else:
				fp.write('_DEBUG')
			if vsplatform=='x64':
				fp.write(';WIN64;_WINDOWS')
			elif vsplatform=='Win32':
				fp.write(';WIN32;_WINDOWS')
			for item in solution.defines:
				fp.write(';' + item)
			fp.write('"\n')

			fp.write('\t\t\t\tStringPooling="true"\n')
			fp.write('\t\t\t\tExceptionHandling="0"\n')
			fp.write('\t\t\t\tStructMemberAlignment="4"\n')
			fp.write('\t\t\t\tEnableFunctionLevelLinking="true"\n')
			fp.write('\t\t\t\tFloatingPointModel="2"\n')
			fp.write('\t\t\t\tRuntimeTypeInfo="false"\n')
			fp.write('\t\t\t\tPrecompiledHeaderFile=""\n')
			# 8 byte alignment
			fp.write('\t\t\t\tWarningLevel="4"\n')
			fp.write('\t\t\t\tSuppressStartupBanner="true"\n')
			if solution.projecttype==ProjectTypes.library or target!='Release':
				fp.write('\t\t\t\tDebugInformationFormat="3"\n')
				fp.write('\t\t\t\tProgramDataBaseFileName="$(OutDir)\$(TargetName).pdb"\n')
			else:
				fp.write('\t\t\t\tDebugInformationFormat="0"\n')
			
			fp.write('\t\t\t\tCallingConvention="1"\n')
			fp.write('\t\t\t\tCompileAs="2"\n')
			fp.write('\t\t\t\tFavorSizeOrSpeed="1"\n')
			# Disable annoying nameless struct warnings since windows headers trigger this
			fp.write('\t\t\t\tDisableSpecificWarnings="4201"\n')

			if target=='Debug':
				fp.write('\t\t\t\tOptimization="0"\n')
				# Necessary to quiet Visual Studio 2008 warnings
				fp.write('\t\t\t\tEnableIntrinsicFunctions="true"\n')
			else:
				fp.write('\t\t\t\tOptimization="2"\n')
				fp.write('\t\t\t\tInlineFunctionExpansion="2"\n')
				fp.write('\t\t\t\tEnableIntrinsicFunctions="true"\n')
				fp.write('\t\t\t\tOmitFramePointers="true"\n')
			if target=='Release':
				fp.write('\t\t\t\tBufferSecurityCheck="false"\n')
				fp.write('\t\t\t\tRuntimeLibrary="0"\n')
			else:
				fp.write('\t\t\t\tBufferSecurityCheck="true"\n')
				fp.write('\t\t\t\tRuntimeLibrary="1"\n')
				
			#
			# Include directories
			#
			fp.write('\t\t\t\tAdditionalIncludeDirectories="')
			addcolon = False
			included = includedirectories + solution.includefolders
			if len(included):
				for dir in included:
					if addcolon==True:
						fp.write(';')
					fp.write(burger.converttowindowsslashes(dir))
					addcolon = True
			if platformcode=='win':
				if addcolon==True:
					fp.write(';')
				if solution.projecttype!=ProjectTypes.library or solution.projectname!='burgerlib':
					fp.write('$(BURGER_SDKS)\\windows\\burgerlib;')
				fp.write('$(BURGER_SDKS)\\windows\\directx9;$(BURGER_SDKS)\\windows\\opengl')
				addcolon = True
			fp.write('"\n')
			fp.write('\t\t\t/>\n')
			
			fp.write('\t\t\t<Tool\n')
			fp.write('\t\t\t\tName="VCResourceCompilerTool"\n')
			fp.write('\t\t\t\tCulture="1033"\n')
			fp.write('\t\t\t/>\n')
			
			if solution.projecttype==ProjectTypes.library:
				fp.write('\t\t\t<Tool\n')
				fp.write('\t\t\t\tName="VCLibrarianTool"\n')
				fp.write('\t\t\t\tOutputFile="&quot;$(OutDir)' + intdirectory + '.lib&quot;"\n')
				fp.write('\t\t\t\tSuppressStartupBanner="true"\n')
				fp.write('\t\t\t/>\n')
				if solution.finalfolder!=None:
					finalfolder = burger.converttowindowsslasheswithendslash(solution.finalfolder)
					fp.write('\t\t\t<Tool\n')
					fp.write('\t\t\t\tName="VCPostBuildEventTool"\n')
					fp.write('\t\t\t\tDescription="Copying $(TargetName)$(TargetExt) to ' + finalfolder + '"\n')
					fp.write('\t\t\t\tCommandLine="&quot;$(perforce)\p4&quot; edit &quot;' + finalfolder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
					fp.write('&quot;$(perforce)\p4&quot; edit &quot;' + finalfolder + '$(TargetName).pdb&quot;&#x0D;&#x0A;')
					fp.write('copy /Y &quot;$(OutDir)$(TargetName)$(TargetExt)&quot; &quot;' + finalfolder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
					fp.write('copy /Y &quot;$(OutDir)$(TargetName).pdb&quot; &quot;' + finalfolder + '$(TargetName).pdb&quot;&#x0D;&#x0A;')
					fp.write('&quot;$(perforce)\p4&quot; revert -a &quot;' + finalfolder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
					fp.write('&quot;$(perforce)\p4&quot; revert -a &quot;' + finalfolder + '$(TargetName).pdb&quot;&#x0D;&#x0A;"\n')
					fp.write('\t\t\t/>\n')
			else:
				fp.write('\t\t\t<Tool\n')
				fp.write('\t\t\t\tName="VCLinkerTool"\n')
				fp.write('\t\t\t\tAdditionalDependencies="burgerlib' + solution.ide.getidecode() + platformcode2 + getconfigurationcode(target) + '.lib"\n')
				fp.write('\t\t\t\tOutputFile="&quot;$(OutDir)' + intdirectory + '.exe&quot;"\n')
				fp.write('\t\t\t\tAdditionalLibraryDirectories="')
				addcolon = False
				for item in solution.includefolders:
					if addcolon==True:
						fp.write(';')
					fp.write(burger.converttowindowsslashes(item))
					addcolon = True
					
				if addcolon==True:
					fp.write(';')
				if solution.projecttype!=ProjectTypes.library:
					fp.write('$(BURGER_SDKS)\\windows\\burgerlib;')
				fp.write('$(BURGER_SDKS)\\windows\\opengl"\n')
				if solution.projecttype==ProjectTypes.tool:
					# main()
					fp.write('\t\t\t\tSubSystem="1"\n')
				else:
					# WinMain()
					fp.write('\t\t\t\tSubSystem="2"\n')
				fp.write('\t\t\t/>\n')
			fp.write('\t\t</Configuration>\n')

	fp.write('\t</Configurations>\n')	
		
	#
	# Save out the filenames
	#

	alllists = listh + listcpp + listwindowsresource
	if len(alllists):

		#	
		# Create groups first
		#
		
		groups = dict()
		for item in alllists:
			groupname = item.extractgroupname()
			# Put each filename in its proper group
			if groupname in groups:
				groups[groupname].append(burger.converttowindowsslashes(item.filename))
			else:
				# New group!
				groups[groupname] = [burger.converttowindowsslashes(item.filename)]
		
		#
		# Create a recursive tree in order to store out the file list
		#

		fp.write('\t<Files>\n')
		tree = dict()
		for group in groups:
			#
			# Get the depth of the tree needed
			#
			
			parts = group.split('\\')
			next = tree
			#
			# Iterate over every part
			#
			for x in xrange(len(parts)):
				# Already declared?
				if not parts[x] in next:
					next[parts[x]] = dict()
				# Step into the tree
				next = next[parts[x]]

		# Use this tree to play back all the data
		dumptreevs2005(2,'',tree,fp,groups)
		fp.write('\t</Files>\n')
		
	fp.write('</VisualStudioProject>\n')
	fp.close()
		
	return 0

#
# Dump out a recursive tree of files to reconstruct a
# directory hiearchy for codewarrior
#

def dumptreecodewarrior(indent,string,entry,fp,groups,solconfig):
	for item in entry:
		if item!='':
			fp.write('\t'*indent + '<GROUP><NAME>' + item + '</NAME>\n')
		if string=='':
			merged = item
		else:
			merged = string + '\\' + item
		if merged in groups:
			if item!='':
				tabs = '\t'*(indent+1)
			else:
				tabs = '\t'*indent
			sortlist = sorted(groups[merged],cmp=lambda x,y: cmp(x,y))
			if solconfig.startswith('Win'):
				pathformat = 'Windows'
			else:
				pathformat = 'Unix'
			for file in sortlist:
				if pathformat=='Unix':
					file2 = burger.converttolinuxslashes(file)
				else:
					file2 = file
				fp.write(tabs + '<FILEREF>\n')
				fp.write(tabs + '\t<TARGETNAME>' + solconfig + '</TARGETNAME>\n')
				fp.write(tabs + '\t<PATHTYPE>Name</PATHTYPE>\n')
				fp.write(tabs + '\t<PATH>' + os.path.basename(file2) + '</PATH>\n')
				fp.write(tabs + '\t<PATHFORMAT>' + pathformat + '</PATHFORMAT>\n')
				fp.write(tabs + '</FILEREF>\n')
				
		key = entry[item]
		if type(key) is dict:
			dumptreecodewarrior(indent+1,merged,key,fp,groups,solconfig)
		if item!='':
			fp.write('\t'*indent + '</GROUP>\n')
			
#
# Create a codewarrior 9.4 project
#

def createcodewarriorsolution(solution):
		
	#
	# Now, let's create the project file
	#
	
	codefiles,includedirectories = solution.getfilelist([FileTypes.h,FileTypes.cpp,FileTypes.rc,FileTypes.hlsl,FileTypes.glsl])
	platformcode = solution.platform.getplatformcode()
	idecode = solution.ide.getidecode()
	projectfilename = str(solution.projectname + idecode + platformcode)
	projectpathname = os.path.join(solution.workingDir,projectfilename + '.mcp.xml')

	#
	# Save out the filenames
	#
	
	listh = pickfromfilelist(codefiles,FileTypes.h)
	listcpp = pickfromfilelist(codefiles,FileTypes.cpp)
	listwindowsresource = []
	if platformcode=='win':
		listwindowsresource = pickfromfilelist(codefiles,FileTypes.rc)
	
	alllists = listh + listcpp + listwindowsresource

	fp = open(projectpathname,'w')
	
	#
	# Save the standard XML header for CodeWarrior
	#
	
	fp.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
	if platformcode=='mac':
		# Codewarrior 10 for Mac OS
		fp.write('<?codewarrior exportversion="2.0" ideversion="5.8" ?>\n')
	else:
		# Codewarrior 9 for Windows
		fp.write('<?codewarrior exportversion="1.0.1" ideversion="5.0" ?>\n')

	#
	# Begin the project object
	#
	
	fp.write('<PROJECT>\n')

	#
	# Create all of the project targets
	#
	
	fp.write('\t<TARGETLIST>\n')
		
	#
	# Begin with a fake project that will build all of the other projects
	#
	
	fp.write('\t\t<TARGET>\n')
	fp.write('\t\t\t<NAME>Everything</NAME>\n')
	fp.write('\t\t\t<SETTINGLIST>\n')
	fp.write('\t\t\t\t<SETTING><NAME>Linker</NAME><VALUE>None</VALUE></SETTING>\n')
	fp.write('\t\t\t\t<SETTING><NAME>Targetname</NAME><VALUE>Everything</VALUE></SETTING>\n')
	fp.write('\t\t\t</SETTINGLIST>\n')
	fp.write('\t\t\t<FILELIST>\n')
	fp.write('\t\t\t</FILELIST>\n')
	fp.write('\t\t\t<LINKORDER>\n')
	fp.write('\t\t\t</LINKORDER>\n')
	if len(solution.configurations)!=0:
		fp.write('\t\t\t<SUBTARGETLIST>\n')
		for target in solution.configurations:
			if solution.platform==PlatformTypes.windows:
				platformcode2 = 'Win32'
			else:
				platformcode2 = solution.platform.name
			fp.write('\t\t\t\t<SUBTARGET>\n')
			fp.write('\t\t\t\t\t<TARGETNAME>' + platformcode2 + ' ' + target + '</TARGETNAME>\n')	
			fp.write('\t\t\t\t</SUBTARGET>\n')
		fp.write('\t\t\t</SUBTARGETLIST>\n')
	fp.write('\t\t</TARGET>\n')

	#
	# Output each target
	#
	
	for target in solution.configurations:
	
		# Create the target name
		
		if solution.platform==PlatformTypes.windows:
			platformcode2 = 'Win32'
			pathformat = 'Windows'
		else:
			platformcode2 = solution.platform.name
			pathformat = 'Unix'
		fp.write('\t\t<TARGET>\n')
		fp.write('\t\t\t<NAME>' + platformcode2 + ' ' + target + '</NAME>\n')	
		
		#
		# Store the settings for the target
		#
		
		fp.write('\t\t\t<SETTINGLIST>\n')
		
		#
		# Choose the target platform via the linker
		#
		
		
		if solution.platform==PlatformTypes.windows:
		
			#
			# Make sure that BURGER_SDKS are pointed to by the environment variable BURGER_SDKS on
			# windows hosts
			#
			
			fp.write('\t\t\t\t<SETTING><NAME>UserSourceTrees</NAME>\n')
			fp.write('\t\t\t\t\t<SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>Name</NAME><VALUE>BURGER_SDKS</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>Kind</NAME><VALUE>EnvironmentVariable</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>VariableName</NAME><VALUE>BURGER_SDKS</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t</SETTING>\n')
			fp.write('\t\t\t\t</SETTING>\n')
			
			fp.write('\t\t\t\t<SETTING><NAME>Linker</NAME><VALUE>Win32 x86 Linker</VALUE></SETTING>\n')
		else:
			fp.write('\t\t\t\t<SETTING><NAME>Linker</NAME><VALUE>MacOS PPC Linker</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>Targetname</NAME><VALUE>' + platformcode2 + ' ' + target + '</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>OutputDirectory</NAME>\n')
		fp.write('\t\t\t\t\t<SETTING><NAME>Path</NAME><VALUE>bin</VALUE></SETTING>\n')
		fp.write('\t\t\t\t\t<SETTING><NAME>PathFormat</NAME><VALUE>' + pathformat + '</VALUE></SETTING>\n')
		fp.write('\t\t\t\t\t<SETTING><NAME>PathRoot</NAME><VALUE>Project</VALUE></SETTING>\n')
		fp.write('\t\t\t\t</SETTING>\n')
		
		#
		# User include folders
		#
		
		if len(includedirectories)!=0:
			fp.write('\t\t\t\t<SETTING><NAME>UserSearchPaths</NAME>\n')
			for dirnameentry in includedirectories:
				fp.write('\t\t\t\t\t<SETTING>\n')
				fp.write('\t\t\t\t\t\t<SETTING><NAME>SearchPath</NAME>\n')
				if solution.platform==PlatformTypes.windows:
					fp.write('\t\t\t\t\t\t\t<SETTING><NAME>Path</NAME><VALUE>' + burger.converttowindowsslashes(dirnameentry) + '</VALUE></SETTING>\n')
				else:
					fp.write('\t\t\t\t\t\t\t<SETTING><NAME>Path</NAME><VALUE>' + burger.converttolinuxslashes(dirnameentry) + '</VALUE></SETTING>\n')
				fp.write('\t\t\t\t\t\t\t<SETTING><NAME>PathFormat</NAME><VALUE>' + pathformat + '</VALUE></SETTING>\n')
				fp.write('\t\t\t\t\t\t\t<SETTING><NAME>PathRoot</NAME><VALUE>Project</VALUE></SETTING>\n')
				fp.write('\t\t\t\t\t\t</SETTING>\n')
				fp.write('\t\t\t\t\t\t<SETTING><NAME>Recursive</NAME><VALUE>false</VALUE></SETTING>\n')
				fp.write('\t\t\t\t\t\t<SETTING><NAME>FrameworkPath</NAME><VALUE>false</VALUE></SETTING>\n')
				fp.write('\t\t\t\t\t\t<SETTING><NAME>HostFlags</NAME><VALUE>All</VALUE></SETTING>\n')
				fp.write('\t\t\t\t\t</SETTING>\n')
			fp.write('\t\t\t\t</SETTING>\n')

		#
		# Operating system include folders
		#
		
		fp.write('\t\t\t\t<SETTING><NAME>SystemSearchPaths</NAME>\n')
		directoryfolders = []
		
		if solution.projecttype!=ProjectTypes.library or solution.projectname!='burgerlib':
			directoryfolders.append('windows\\burgerlib')
			#directoryfolders.append('windows\\burgerlib4')
		
		directoryfolders.append('windows\\perforce')
		directoryfolders.append('windows\\opengl')
		directoryfolders.append('windows\\directx9')
		

		for dirnameentry in directoryfolders:
			fp.write('\t\t\t\t\t<SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>SearchPath</NAME>\n')
			fp.write('\t\t\t\t\t\t\t<SETTING><NAME>Path</NAME><VALUE>' + dirnameentry + '</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t\t<SETTING><NAME>PathFormat</NAME><VALUE>' + pathformat + '</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t\t<SETTING><NAME>PathRoot</NAME><VALUE>BURGER_SDKS</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t</SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>Recursive</NAME><VALUE>false</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>FrameworkPath</NAME><VALUE>false</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>HostFlags</NAME><VALUE>All</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t</SETTING>\n')

		for dirnameentry in ['MSL','Win32-x86 Support']:
			fp.write('\t\t\t\t\t<SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>SearchPath</NAME>\n')
			fp.write('\t\t\t\t\t\t\t<SETTING><NAME>Path</NAME><VALUE>' + dirnameentry + '</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t\t<SETTING><NAME>PathFormat</NAME><VALUE>' + pathformat + '</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t\t<SETTING><NAME>PathRoot</NAME><VALUE>CodeWarrior</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t</SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>Recursive</NAME><VALUE>true</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>FrameworkPath</NAME><VALUE>false</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t\t<SETTING><NAME>HostFlags</NAME><VALUE>All</VALUE></SETTING>\n')
			fp.write('\t\t\t\t\t</SETTING>\n')

		fp.write('\t\t\t\t</SETTING>\n')

		#
		# Library/Application?
		#
		
		if solution.platform==PlatformTypes.windows:
			platformcode2 = 'w32'
		else:
			platformcode2 = solution.platform.name
		if solution.projecttype==ProjectTypes.library:
			fp.write('\t\t\t\t<SETTING><NAME>MWProject_X86_type</NAME><VALUE>Library</VALUE></SETTING>\n')
			fp.write('\t\t\t\t<SETTING><NAME>MWProject_X86_outfile</NAME><VALUE>' + solution.projectname + idecode + platformcode2 + getconfigurationcode(target) + '.lib</VALUE></SETTING>\n')
		else:
			fp.write('\t\t\t\t<SETTING><NAME>MWProject_X86_type</NAME><VALUE>Application</VALUE></SETTING>\n')
			fp.write('\t\t\t\t<SETTING><NAME>MWProject_X86_outfile</NAME><VALUE>' + solution.projectname + idecode + platformcode2 + getconfigurationcode(target) + '.exe</VALUE></SETTING>\n')

		#
		# Compiler settings for the front end
		#
		
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_cplusplus</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_templateparser</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_instance_manager</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_enableexceptions</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_useRTTI</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_booltruefalse</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_wchar_type</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_ecplusplus</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_dontinline</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_inlinelevel</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_autoinline</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_defer_codegen</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_bottomupinline</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_ansistrict</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_onlystdkeywords</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_trigraphs</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_arm</NAME><VALUE>0</VALUE></SETTING>\n')		
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_checkprotos</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_c99</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_gcc_extensions</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_enumsalwaysint</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_unsignedchars</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_poolstrings</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWFrontEnd_C_dontreusestrings</NAME><VALUE>0</VALUE></SETTING>\n')

		#
		# Preprocessor settings
		#
		
		fp.write('\t\t\t\t<SETTING><NAME>C_CPP_Preprocessor_PrefixText</NAME><VALUE>#define ')
		if target=='Release':
			fp.write('NDEBUG\n')
		else:
			fp.write('_DEBUG\n')
		if platformcode2=='w32':
			fp.write('#define WIN32_LEAN_AND_MEAN\n#define WIN32\n')
		for defineentry in solution.defines:
			fp.write('#define ' + defineentry + '\n')
		fp.write('</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>C_CPP_Preprocessor_MultiByteEncoding</NAME><VALUE>encASCII_Unicode</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>C_CPP_Preprocessor_PCHUsesPrefixText</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>C_CPP_Preprocessor_EmitPragmas</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>C_CPP_Preprocessor_KeepWhiteSpace</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>C_CPP_Preprocessor_EmitFullPath</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>C_CPP_Preprocessor_KeepComments</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>C_CPP_Preprocessor_EmitFile</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>C_CPP_Preprocessor_EmitLine</NAME><VALUE>false</VALUE></SETTING>\n')

		#
		# Warnings panel
		#
		
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_illpragma</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_possunwant</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_pedantic</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_illtokenpasting</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_hidevirtual</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_implicitconv</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_impl_f2i_conv</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_impl_s2u_conv</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_impl_i2f_conv</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_ptrintconv</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_unusedvar</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_unusedarg</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_resultnotused</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_missingreturn</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_no_side_effect</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_extracomma</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_structclass</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_emptydecl</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_filenamecaps</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_filenamecapssystem</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_padding</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_undefmacro</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warn_notinlined</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWWarning_C_warningerrors</NAME><VALUE>0</VALUE></SETTING>\n')

		#
		# X86 code gen
		#
		
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_runtime</NAME><VALUE>Custom</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_processor</NAME><VALUE>PentiumIV</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_use_extinst</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_extinst_mmx</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_extinst_3dnow</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_extinst_cmov</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_extinst_sse</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_extinst_sse2</NAME><VALUE>0</VALUE></SETTING>\n')

		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_use_mmx_3dnow_convention</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_vectorize</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_profile</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_readonlystrings</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_alignment</NAME><VALUE>bytes8</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_intrinsics</NAME><VALUE>1</VALUE></SETTING>\n')
		if target=='Debug':
			fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_optimizeasm</NAME><VALUE>0</VALUE></SETTING>\n')
			fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_disableopts</NAME><VALUE>1</VALUE></SETTING>\n')
		else:
			fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_optimizeasm</NAME><VALUE>1</VALUE></SETTING>\n')
			fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_disableopts</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_relaxieee</NAME><VALUE>1</VALUE></SETTING>\n')

		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_exceptions</NAME><VALUE>ZeroOverhead</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWCodeGen_X86_name_mangling</NAME><VALUE>MWWin32</VALUE></SETTING>\n')
		
		#
		# Global optimizations
		#
		
		if target=='Debug':
			fp.write('\t\t\t\t<SETTING><NAME>GlobalOptimizer_X86__optimizationlevel</NAME><VALUE>Level0</VALUE></SETTING>\n')
		else:
			fp.write('\t\t\t\t<SETTING><NAME>GlobalOptimizer_X86__optimizationlevel</NAME><VALUE>Level4</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>GlobalOptimizer_X86__optfor</NAME><VALUE>Size</VALUE></SETTING>\n')

		#
		# x86 disassembler
		#
		
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showHeaders</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showSectHeaders</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showSymTab</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showCode</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showData</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showDebug</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showExceptions</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showRelocation</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showRaw</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showAllRaw</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showSource</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showHex</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showComments</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_resolveLocals</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_resolveRelocs</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_showSymDefs</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_unmangle</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>PDisasmX86_verbose</NAME><VALUE>false</VALUE></SETTING>\n')

		#
		# x86 linker settings
		#

		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_linksym</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_linkCV</NAME><VALUE>1</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_symfullpath</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_linkdebug</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_debuginline</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_subsystem</NAME><VALUE>Unknown</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_entrypointusage</NAME><VALUE>Default</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_entrypoint</NAME><VALUE></VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_codefolding</NAME><VALUE>Any</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_usedefaultlibs</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_adddefaultlibs</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_mergedata</NAME><VALUE>true</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_zero_init_bss</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_generatemap</NAME><VALUE>0</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_checksum</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_linkformem</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_nowarnings</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_verbose</NAME><VALUE>false</VALUE></SETTING>\n')
		fp.write('\t\t\t\t<SETTING><NAME>MWLinker_X86_commandfile</NAME><VALUE></VALUE></SETTING>\n')

		#
		# Settings are done
		#
		
		fp.write('\t\t\t</SETTINGLIST>\n')
		
		#
		# Add in the list of files
		#
		
		liblist = []
		if solution.projecttype!=ProjectTypes.library:
			if target=='Debug':
				liblist.append('burgerlibcw9w32dbg.lib')
				#liblist.append('burgercw9w32dbg.lib')
			elif target=='Internal':
				liblist.append('burgerlibcw9w32int.lib')
				#liblist.append('burgercw9w32int.lib')
			else:
				liblist.append('burgerlibcw9w32rel.lib')
				#liblist.append('burgercw9w32rel.lib')

		liblist.append('user32.lib')
		liblist.append('kernel32.lib')
		liblist.append('gdi32.lib')
		liblist.append('winmm.lib')
		liblist.append('version.lib')
		liblist.append('shell32.lib')
		liblist.append('advapi32.lib')
		liblist.append('shlwapi.lib')
		liblist.append('ole32.lib')

		if target=='Debug':
			liblist.append('MSL_All_x86_D.lib')
		else:
			liblist.append('MSL_All_x86.lib')

		if len(alllists)!=0:
			
			fp.write('\t\t\t<FILELIST>\n')
			if solution.projecttype!=ProjectTypes.library:
				for i in liblist:
					fp.write('\t\t\t\t<FILE>\n')
					fp.write('\t\t\t\t\t<PATHTYPE>Name</PATHTYPE>\n')
					fp.write('\t\t\t\t\t<PATH>' + i + '</PATH>\n')
					fp.write('\t\t\t\t\t<PATHFORMAT>' + pathformat + '</PATHFORMAT>\n')
					fp.write('\t\t\t\t\t<FILEKIND>Library</FILEKIND>\n')
					if target!='Release': 
						fp.write('\t\t\t\t\t<FILEFLAGS>Debug</FILEFLAGS>\n')
					else:
						fp.write('\t\t\t\t\t<FILEFLAGS></FILEFLAGS>\n')
					fp.write('\t\t\t\t</FILE>\n')
				
			filelist = []
			for i in alllists:
				parts = burger.converttowindowsslashes(i.filename).split('\\')
				filelist.append(parts[len(parts)-1])
		
			filelist = sorted(filelist,cmp=lambda x,y: cmp(x,y))

			for i in filelist:
				fp.write('\t\t\t\t<FILE>\n')
				fp.write('\t\t\t\t\t<PATHTYPE>Name</PATHTYPE>\n')
				fp.write('\t\t\t\t\t<PATH>' + i + '</PATH>\n')
				fp.write('\t\t\t\t\t<PATHFORMAT>' + pathformat + '</PATHFORMAT>\n')
				fp.write('\t\t\t\t\t<FILEKIND>Text</FILEKIND>\n')
				if target!='Release' and (i.endswith('.c') or i.endswith('.cpp')): 
					fp.write('\t\t\t\t\t<FILEFLAGS>Debug</FILEFLAGS>\n')
				else:
					fp.write('\t\t\t\t\t<FILEFLAGS></FILEFLAGS>\n')
				fp.write('\t\t\t\t</FILE>\n')
			
			fp.write('\t\t\t</FILELIST>\n')
		
			fp.write('\t\t\t<LINKORDER>\n')
			if solution.projecttype!=ProjectTypes.library:
				for i in liblist:
					fp.write('\t\t\t\t<FILEREF>\n')
					fp.write('\t\t\t\t\t<PATHTYPE>Name</PATHTYPE>\n')
					fp.write('\t\t\t\t\t<PATH>' + i + '</PATH>\n')
					fp.write('\t\t\t\t\t<PATHFORMAT>' + pathformat + '</PATHFORMAT>\n')
					fp.write('\t\t\t\t</FILEREF>\n')
			for i in filelist:
				fp.write('\t\t\t\t<FILEREF>\n')
				fp.write('\t\t\t\t\t<PATHTYPE>Name</PATHTYPE>\n')
				fp.write('\t\t\t\t\t<PATH>' + i + '</PATH>\n')
				fp.write('\t\t\t\t\t<PATHFORMAT>' + pathformat + '</PATHFORMAT>\n')
				fp.write('\t\t\t\t</FILEREF>\n')
			fp.write('\t\t\t</LINKORDER>\n')
		
		fp.write('\t\t</TARGET>\n')

	#
	# All of the targets are saved
	#
	
	fp.write('\t</TARGETLIST>\n')
	
	#
	# Now output the list of targets
	#
	
	fp.write('\t<TARGETORDER>\n')
	fp.write('\t\t<ORDEREDTARGET><NAME>Everything</NAME></ORDEREDTARGET>\n')
	for target in solution.configurations:
		if solution.platform==PlatformTypes.windows:
			platformcode2 = 'Win32'
		else:
			platformcode2 = solution.platform.name
		fp.write('\t\t<ORDEREDTARGET><NAME>' + platformcode2 + ' ' + target + '</NAME></ORDEREDTARGET>\n')
	fp.write('\t</TARGETORDER>\n')

	#
	# Save the file list as they are displayed in the IDE
	#
	
	if len(alllists):

		#	
		# Create groups first since CodeWarrior uses a nested tree structure
		# for file groupings
		#
		
		groups = dict()
		for item in alllists:
			groupname = item.extractgroupname()
			# Put each filename in its proper group
			if groupname in groups:
				groups[groupname].append(burger.converttowindowsslashes(item.filename))
			else:
				# New group!
				groups[groupname] = [burger.converttowindowsslashes(item.filename)]
		
		#
		# Create a recursive tree in order to store out the file list
		#

		if 'Release' in solution.configurations:
			solconfig = platformcode2 + ' Release'
		else:
			solconfig = platformcode2 + ' ' + solution.configurations[0]

		fp.write('\t<GROUPLIST>\n')
		tree = dict()
		for group in groups:
			#
			# Get the depth of the tree needed
			#
			
			parts = group.split('\\')
			next = tree
			#
			# Iterate over every part
			#
			for x in xrange(len(parts)):
				# Already declared?
				if not parts[x] in next:
					next[parts[x]] = dict()
				# Step into the tree
				next = next[parts[x]]

		# Use this tree to play back all the data
		dumptreecodewarrior(2,'',tree,fp,groups,solconfig)
		
		if solution.projecttype!=ProjectTypes.library:
			liblist = []
				
			liblist.append(['user32.lib',solconfig])
			liblist.append(['kernel32.lib',solconfig])
			liblist.append(['gdi32.lib',solconfig])
			liblist.append(['winmm.lib',solconfig])
			liblist.append(['version.lib',solconfig])
			liblist.append(['shell32.lib',solconfig])
			liblist.append(['advapi32.lib',solconfig])
			liblist.append(['shlwapi.lib',solconfig])
			liblist.append(['ole32.lib',solconfig])
			
			if 'Release' in solution.configurations:
				liblist.append(['burgerlibcw9w32rel.lib','Win32 Release'])
				#liblist.append(['burgercw9w32rel.lib','Win32 Release'])
				liblist.append(['MSL_All_x86.lib','Win32 Release'])
			
			if 'Internal' in solution.configurations:
				liblist.append(['burgerlibcw9w32int.lib','Win32 Internal'])
				#liblist.append(['burgercw9w32int.lib','Win32 Internal'])
				if not 'Release' in solution.configurations:
					liblist.append(['MSL_All_x86.lib','Win32 Internal'])

			if 'Debug' in solution.configurations:
				liblist.append(['burgerlibcw9w32dbg.lib','Win32 Debug'])
				#liblist.append(['burgercw9w32dbg.lib','Win32 Debug'])
				liblist.append(['MSL_All_x86_D.lib','Win32 Debug'])

				
			fp.write('\t\t<GROUP><NAME>Libraries</NAME>\n')
			for i in liblist:
				fp.write('\t\t\t<FILEREF>\n')
				fp.write('\t\t\t\t<TARGETNAME>' + i[1] + '</TARGETNAME>\n')
				fp.write('\t\t\t\t<PATHTYPE>Name</PATHTYPE>\n')
				fp.write('\t\t\t\t<PATH>' + i[0] + '</PATH>\n')
				fp.write('\t\t\t\t<PATHFORMAT>Windows</PATHFORMAT>\n')
				fp.write('\t\t\t</FILEREF>\n')

			fp.write('\t\t</GROUP>\n')
	
		fp.write('\t</GROUPLIST>\n')

	#
	# Close the file
	#
	
	fp.write('</PROJECT>\n')
	fp.close()
	
	#
	# If codewarrior is installed, create the MCP file
	#
	
	cwfile = os.getenv('CWFolder')
	if cwfile!=None and solution.platform==PlatformTypes.windows:
		burger.perforceedit(os.path.join(solution.workingDir,projectfilename + '.mcp'))
		cwfile = os.path.join(cwfile,'Bin','ide')
		cmd = '"' + cwfile + '" /x "' + projectpathname + '" "' + os.path.join(solution.workingDir,projectfilename + '.mcp') + '" /s /c /q'
		sys.stdout.flush()
		error = subprocess.call(cmd,cwd=os.path.dirname(projectpathname),shell=True)
		if error==0:
			os.remove(projectpathname)
		return error
		
	return 0

#
# Create a codeblocks 13.12 project
#

def createcodeblockssolution(solution):
		
	#
	# Now, let's create the project file
	#
	
	codefiles,includedirectories = solution.getfilelist([FileTypes.h,FileTypes.cpp,FileTypes.rc,FileTypes.hlsl,FileTypes.glsl])
	platformcode = solution.platform.getplatformcode()
	idecode = solution.ide.getidecode()
	projectfilename = str(solution.projectname + idecode + platformcode)
	projectpathname = os.path.join(solution.workingDir,projectfilename + '.cbp')

	#
	# Save out the filenames
	#
	
	listh = pickfromfilelist(codefiles,FileTypes.h)
	listcpp = pickfromfilelist(codefiles,FileTypes.cpp)
	listwindowsresource = []
	if platformcode=='win':
		listwindowsresource = pickfromfilelist(codefiles,FileTypes.rc)
	
	alllists = listh + listcpp + listwindowsresource

	burger.perforceedit(projectpathname)
	fp = open(projectpathname,'w')
	
	#
	# Save the standard XML header for CodeBlocks
	#
	
	fp.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
	fp.write('<CodeBlocks_project_file>\n')
	fp.write('\t<FileVersion major="1" minor="6" />\n')
	fp.write('\t<Project>\n')
	
	#
	# Output the project settings
	#
	
	fp.write('\t\t<Option title="burgerlib" />\n')
	fp.write('\t\t<Option makefile="makefile" />\n')
	fp.write('\t\t<Option pch_mode="2" />\n')
	fp.write('\t\t<Option compiler="ow" />\n')
		
	#
	# Output the per target build settings
	#
	
	
	fp.write('\t\t<Build>\n')
	
	fp.write('\t\t\t<Target title="Debug">\n')
	fp.write('\t\t\t\t<Option output="bin/burgerlibcdbwatw32dbg.lib" prefix_auto="0" extension_auto="0" />\n')
	fp.write('\t\t\t\t<Option working_dir="" />\n')
	fp.write('\t\t\t\t<Option object_output="temp/burgerlibcbpwatw32dbg/" />\n')
	if solution.projecttype==ProjectTypes.tool:
		fp.write('\t\t\t\t<Option type="1" />\n')
	else:
		fp.write('\t\t\t\t<Option type="2" />\n')
	fp.write('\t\t\t\t<Option compiler="ow" />\n')
	fp.write('\t\t\t\t<Option createDefFile="1" />\n')
	fp.write('\t\t\t\t<Compiler>\n')
	fp.write('\t\t\t\t\t<Add option="-d2" />\n')
	fp.write('\t\t\t\t\t<Add option="-wx" />\n')
	fp.write('\t\t\t\t\t<Add option="-fp6" />\n')
	fp.write('\t\t\t\t\t<Add option="-6r" />\n')
	fp.write('\t\t\t\t\t<Add option="-fr=$(ERROR_FILE)" />\n')
	fp.write('\t\t\t\t\t<Add option="-d_DEBUG" />\n')
	fp.write('\t\t\t\t</Compiler>\n')
	fp.write('\t\t\t</Target>\n')

	fp.write('\t\t\t<Target title="Internal">\n')
	fp.write('\t\t\t\t<Option output="bin/burgerlibcdbwatw32int.lib" prefix_auto="0" extension_auto="0" />\n')
	fp.write('\t\t\t\t<Option working_dir="" />\n')
	fp.write('\t\t\t\t<Option object_output="temp/burgerlibcbpwatw32int/" />\n')
	if solution.projecttype==ProjectTypes.tool:
		fp.write('\t\t\t\t<Option type="1" />\n')
	else:
		fp.write('\t\t\t\t<Option type="2" />\n')
	fp.write('\t\t\t\t<Option compiler="ow" />\n')
	fp.write('\t\t\t\t<Option createDefFile="1" />\n')
	fp.write('\t\t\t\t<Compiler>\n')
	fp.write('\t\t\t\t\t<Add option="-ox" />\n')
	fp.write('\t\t\t\t\t<Add option="-ot" />\n')
	fp.write('\t\t\t\t\t<Add option="-wx" />\n')
	fp.write('\t\t\t\t\t<Add option="-fr=$(ERROR_FILE)" />\n')
	fp.write('\t\t\t\t\t<Add option="-fp6" />\n')
	fp.write('\t\t\t\t\t<Add option="-6r" />\n')
	fp.write('\t\t\t\t\t<Add option="-d_DEBUG" />\n')
	fp.write('\t\t\t\t</Compiler>\n')
	fp.write('\t\t\t</Target>\n')

	fp.write('\t\t\t<Target title="Release">\n')
	fp.write('\t\t\t\t<Option output="bin/burgerlibcdbwatw32rel.lib" prefix_auto="0" extension_auto="0" />\n')
	fp.write('\t\t\t\t<Option working_dir="" />\n')
	fp.write('\t\t\t\t<Option object_output="temp/burgerlibcbpwatw32rel/" />\n')
	if solution.projecttype==ProjectTypes.tool:
		fp.write('\t\t\t\t<Option type="1" />\n')
	else:
		fp.write('\t\t\t\t<Option type="2" />\n')
	fp.write('\t\t\t\t<Option compiler="ow" />\n')
	fp.write('\t\t\t\t<Option createDefFile="1" />\n')
	fp.write('\t\t\t\t<Compiler>\n')
	fp.write('\t\t\t\t\t<Add option="-ox" />\n')
	fp.write('\t\t\t\t\t<Add option="-ot" />\n')
	fp.write('\t\t\t\t\t<Add option="-wx" />\n')
	fp.write('\t\t\t\t\t<Add option="-fr=$(ERROR_FILE)" />\n')
	fp.write('\t\t\t\t\t<Add option="-fp6" />\n')
	fp.write('\t\t\t\t\t<Add option="-6r" />\n')
	fp.write('\t\t\t\t\t<Add option="-dNDEBUG" />\n')
	fp.write('\t\t\t\t</Compiler>\n')
	fp.write('\t\t\t</Target>\n')
	
	fp.write('\t\t\t<Environment>\n')
	fp.write('\t\t\t\t<Variable name="ERROR_FILE" value="$(TARGET_OBJECT_DIR)foo.err" />\n')
	fp.write('\t\t\t</Environment>\n')
	fp.write('\t\t</Build>\n')
		
	#
	# Output the virtual target
	#
	
	fp.write('\t\t<VirtualTargets>\n')
	fp.write('\t\t\t<Add alias="Everything" targets="')
	for target in solution.configurations:
		fp.write(target + ';')
	fp.write('" />\n')
	fp.write('\t\t</VirtualTargets>\n')
	
	#
	# Output the global compiler settings
	#
	
	fp.write('\t\t<Compiler>\n')
	fp.write('\t\t\t<Add option="-dGLUT_DISABLE_ATEXIT_HACK" />\n')
	fp.write('\t\t\t<Add option="-dGLUT_NO_LIB_PRAGMA" />\n')
	fp.write('\t\t\t<Add option="-dTARGET_CPU_X86=1" />\n')
	fp.write('\t\t\t<Add option="-dTARGET_OS_WIN32=1" />\n')
	fp.write('\t\t\t<Add option="-dTYPE_BOOL=1" />\n')
	fp.write('\t\t\t<Add option="-dUNICODE" />\n')
	fp.write('\t\t\t<Add option="-d_UNICODE" />\n')
	fp.write('\t\t\t<Add option="-dWIN32_LEAN_AND_MEAN" />\n')

	for dirnameentry in includedirectories:
		fp.write('\t\t\t<Add directory=\'&quot;' + burger.converttolinuxslashes(dirnameentry) + '&quot;\' />\n')

	if solution.projecttype!=ProjectTypes.library or solution.projectname!='burgerlib':
		fp.write('\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/burgerlib&quot;\' />\n')
	fp.write('\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/perforce&quot;\' />\n')
	fp.write('\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/opengl&quot;\' />\n')
	fp.write('\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/directx9&quot;\' />\n')
	fp.write('\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/windows5&quot;\' />\n')
	fp.write('\t\t</Compiler>\n')
		
	#
	# Output the list of source files
	#
	
	filelist = []
	for i in alllists:
		filelist.append(burger.converttolinuxslashes(i.filename))
		
	filelist = sorted(filelist,cmp=lambda x,y: cmp(x,y))
	
	for i in filelist:
		fp.write('\t\t<Unit filename="' + i + '" />\n')
	
	#
	# Add the extensions (If any)
	#

	fp.write('\t\t<Extensions>\n')
	fp.write('\t\t\t<code_completion />\n')
	fp.write('\t\t\t<envvars />\n')
	fp.write('\t\t\t<debugger />\n')
	fp.write('\t\t</Extensions>\n')

	#
	# Close the file
	#

	fp.write('\t</Project>\n')	
	fp.write('</CodeBlocks_project_file>\n')
	fp.close()
	return 0

#
# Create an OpenWatcom makefile
#

def createwatcomsolution(solution):
		
	#
	# Now, let's create the project file
	#
	
	codefiles,includedirectories = solution.getfilelist([FileTypes.h,FileTypes.cpp,FileTypes.x86])
	platformcode = solution.platform.getplatformcode()
	idecode = solution.ide.getidecode()
	projectfilename = str(solution.projectname + idecode + platformcode)
	projectpathname = os.path.join(solution.workingDir,projectfilename + '.wmk')

	#
	# Save out the filenames
	#
	
	listh = pickfromfilelist(codefiles,FileTypes.h)
	listcpp = pickfromfilelist(codefiles,FileTypes.cpp)
	listx86 = pickfromfilelist(codefiles,FileTypes.x86)
	listwindowsresource = []
	#if platformcode=='win':
	#	listwindowsresource = pickfromfilelist(codefiles,FileTypes.rc)
	
	alllists = listh + listcpp + listx86 + listwindowsresource

	burger.perforceedit(projectpathname)
	fp = open(projectpathname,'w')
	fp.write(
		'#\n'
		'# Build ' + solution.projectname + ' for ' + solution.platform.name + '\n'
		'#\n\n'
		'#\n'
		'# sourcedir = Set the work directories for the source\n'
		'#\n\n')	

	filelist = []
	for item in alllists:
		filelist.append(burger.converttowindowsslashes(item.filename))
		
	filelist = sorted(filelist,cmp=lambda x,y: cmp(x,y))
	
	sourcedir = []	
	for item in filelist:
		#
		# Remove the filename
		#
		index = item.rfind('\\')
		if index==-1:
			entry = item
		else:
			entry = item[0:index]
		if not entry in sourcedir:
			sourcedir.append(entry)
	
	fp.write("sourcedir = ")
	string = ''
	for item in sourcedir:
		string = string + item + ';'
	
	if len(string):
		# Get rid of the trailing semi colon
		string = string[0:len(string)-1]
		fp.write(string)
		
	fp.write('\n\n'
		'#\n'
		'# Name of the output library\n'
		'#\n\n'
		'projectname = ' + solution.projectname + '\n\n'

		'#\n'
		'# includedir = Header includes\n'
		'#\n\n'
		'includedir = $(sourcedir)')
		
	if len(solution.includefolders):
		string = ''
		for item in solution.includefolders:
			string = string + ';' + burger.converttowindowsslashes(item)
		fp.write(string)
	
	fp.write('\n\n'
		'#\n'
		'# Object files to work with for the library\n'
		'#\n\n')
		
	string = 'objs= &'
	for item in filelist:
		if not item.endswith('.h'):
			index = item.rfind('.')
			if index==-1:
				entry = item
			else:
				entry = item[0:index]

			index = entry.rfind('\\')
			if index==-1:
				entry = entry
			else:
				entry = entry[index+1:len(entry)]

			string = string + '\n\t$(A)\\' + entry + '.obj &'

	# Get rid of the trailing ampersand and space
	string = string[0:len(string)-2]
	fp.write(string + '\n\n')
	
	if solution.finalfolder!=None:
		final = burger.converttowindowsslashes(solution.finalfolder)
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
		platforms = ['x32','dos4gw']
	elif solution.platform == PlatformTypes.windows:
		platforms = ['w32']
	
	if solution.projecttype==ProjectTypes.library:
		suffix = 'lib'
	else:
		suffix = 'exe'
		
	for theplatform in platforms:
		if theplatform=='dos4gw':
			shortplatform = '4gw'
		else:
			shortplatform = theplatform
			
		for target in solution.configurations:
			fp.write('\t@set config=' + target + '\n')
			fp.write('\t@set target=' + theplatform + '\n')
			fp.write('\t@%make $(destdir)\$(projectname)wat' + shortplatform + getconfigurationcode(target) + '.' + suffix + '\n')

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
			if theplatform=='dos4gw':
				theplatform = '4gw'
			fp.write('A = $(basetempdir)wat' + theplatform + getconfigurationcode(target) + '\n'
				'$(destdir)\\$(projectname)wat' + theplatform + getconfigurationcode(target) + '.' + suffix + ' : $+$(OBJS)$- ' + projectfilename + '.wmk\n'
				'\t@if not exist $(destdir) @!mkdir $(destdir)\n')
			if solution.projecttype==ProjectTypes.library:

				fp.write('\t@SET WOW=$+$(OBJS)$-\n'
					'\t@WLIB -q -b -c -n $^@ @WOW\n')

				if solution.finalfolder!=None:
					fp.write('\t@"$(%perforce)\\p4" edit "$(finalfolder)\$^."\n'
						'\t@copy /y "$^@" "$(finalfolder)\\$^."\n'
						'\t@"$(%perforce)\\p4" revert -a "$(finalfolder)\\$^."\n\n')
			else:
				fp.write('\t@SET WOW={$+$(OBJS)$-}\n'
					'\t@$(LINK) $(LFlagsw32) $(LFlags' + target + ') LIBRARY burgerlibwat' + theplatform + getconfigurationcode(target) + '.lib NAME $^@ FILE @wow\n\n')
		
	fp.close()
	return 0

