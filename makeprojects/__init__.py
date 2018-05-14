""" Makeprojects package """

from __future__ import absolute_import

import enum
from enum import IntEnum, EnumMeta
import burger

from .rebuildme import main as rebuild
from .cleanme import main as clean
from .buildme import main as build

# Copyright 2013-2018 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

#
# Note: This is only executed if makeprojects is imported as a module
#

#
## \package makeprojects
# Root namespace for the makeprojects tool
#

#
# Describe this module
#

## Current version of the library
__version__ = '0.7.0'

## Author's name
__author__ = 'Rebecca Ann Heineman <becky@burgerbecky.com>'

## Name of the module
__title__ = 'makeprojects'

## Summary of the module's use
__summary__ = 'IDE project generator for Visual Studio, XCode, etc...'

## Home page
__uri__ = 'http://burgerbecky.com'

## Email address for bug reports
__email__ = 'becky@burgerbecky.com'

## Type of license used for distribution
__license__ = 'MIT License'

## Copyright owner
__copyright__ = 'Copyright 2013-2018 Rebecca Ann Heineman'

#
## Items to import on "from makeprojects import *"
#

__all__ = [
	'savedefault',
	'newsolution',
	'newproject',

	'FileTypes',
	'ProjectTypes',
	'ConfigurationTypes',
	'IDETypes',
	'PlatformTypes',

	'SourceFile',
	'Property',
	'Project',
	'Solution',
	'visualstudio',
	'watcom',
	'codeblocks',
	'codewarrior',
	'xcode'
]

#
## Class to allow auto generation of enumerations
#

class auto_enum(EnumMeta):
	def __new__(metacls, cls, bases, classdict):

		# Replace the dictionary with a new copy
		original_dict = classdict
		classdict = enum._EnumDict()
		for k, item in original_dict.items():
			classdict[k] = item

		temp = type(classdict)()
		names = set(classdict._member_names)

		# Start the enumeration with this value
		i = 0
		for k in classdict._member_names:

			# Does this entry need assignment?
			# Test by checking for the initial value
			# being set to ().
			item = classdict[k]
			if item != ():
				# Use the assigned value
				i = item
			temp[k] = i

			# Increment for the next assigned value
			i += 1

		# Update the dictionary
		for k, item in classdict.items():
			if k not in names:
				temp[k] = item

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
	## Compile as C
	c = ()
	## Compile as C++
	cpp = ()
	## C/C++ header
	h = ()
	## Objective-C
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
	## Look up a file name extension and return the type
	#
	@staticmethod
	def lookup(test_name):
		for item in FileTypes_lookup:
			if test_name.endswith(item[0]):
				return item[1]
		return None

	def __repr__(self):
		if self == self.user:
			return 'User'
		if self == self.generic:
			return 'Generic'
		if self == self.c:
			return 'C source file'
		if self == self.cpp:
			return 'C++ source file'
		if self == self.h:
			return 'C header file'
		if self == self.m:
			return 'Objective-C file'
		if self == self.xml:
			return 'Xml file'
		if self == self.rc:
			return 'Windows Resource file'
		if self == self.r:
			return 'MacOS Resource file'
		if self == self.hlsl:
			return 'DirectX shader file'
		if self == self.glsl:
			return 'OpenGL shader file'
		if self == self.x360sl:
			return 'Xbox 360 shader file'
		if self == self.vitacg:
			return 'Playstation Vita shader file'
		if self == self.frameworks:
			return 'macOS Framework'
		if self == self.library:
			return 'Statically linked library'
		if self == self.exe:
			return 'Executable file'
		if self == self.xcconfig:
			return 'Apple XCode config file'
		if self == self.x86:
			return 'X86 assembly file'
		if self == self.x64:
			return 'X64 assembly file'
		if self == self.a65:
			return '6502/65816 assembly file'
		if self == self.ppc:
			return 'PowerPC assembly file'
		if self == self.a68:
			return '680x0 assembly file'
		if self == self.image:
			return 'Image file'
		if self == self.ico:
			return 'Windows Icon file'
		if self == self.icns:
			return 'macOS Icon file'
		return None

	__str__ = __repr__


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

FileTypes_lookup = [
	['.c', FileTypes.c],			# C/C++ source code
	['.cc', FileTypes.cpp],
	['.cpp', FileTypes.cpp],
	['.c++', FileTypes.cpp],
	['.hpp', FileTypes.h],			# C/C++ header files
	['.h', FileTypes.h],
	['.hh', FileTypes.h],
	['.i', FileTypes.h],
	['.inc', FileTypes.h],
	['.m', FileTypes.m],			# MacOSX / iOS Objective-C
	['.plist', FileTypes.xml],		# MacOSX / iOS plist files
	['.rc', FileTypes.rc],			# Windows resources
	['.r', FileTypes.r],			# MacOS classic resources
	['.rsrc', FileTypes.r],
	['.hlsl', FileTypes.hlsl],		# DirectX shader files
	['.vsh', FileTypes.glsl],		# OpenGL shader files
	['.fsh', FileTypes.glsl],
	['.glsl', FileTypes.glsl],
	['.x360sl', FileTypes.x360sl],	# Xbox 360 shader files
	['.vitacg', FileTypes.vitacg],	# PS Vita shader files
	['.xml', FileTypes.xml],		# XML data files
	['.x86', FileTypes.x86],		# Intel ASM 80x86 source code
	['.x64', FileTypes.x64],		# AMD 64 bit source code
	['.a65', FileTypes.a65],		# 6502/65816 source code
	['.ppc', FileTypes.ppc],		# PowerPC source code
	['.a68', FileTypes.a68],		# 680x0 source code
	['.ico', FileTypes.ico],		# Windows icon file
	['.icns', FileTypes.icns],		# Mac OSX Icon file
	['.png', FileTypes.image],		# Art files
	['.jpg', FileTypes.image],
	['.bmp', FileTypes.image]
]

#
## Enumeration of supported project types
#

class ProjectTypes(AutoIntEnum):
	## Code library
	library = ()
	## Command line tool
	tool = ()
	## Application
	app = ()
	## Screen saver
	screensaver = ()
	## Shared library (DLL)
	sharedlibrary = ()
	## Empty project
	empty = ()

	def __repr__(self):
		if self == self.library:
			return 'Library'
		if self == self.tool:
			return 'Tool'
		if self == self.app:
			return 'Application'
		if self == self.screensaver:
			return 'ScreenSaver'
		if self == self.sharedlibrary:
			return 'Dynamic Library'
		if self == self.empty:
			return 'Empty'
		return None

	__str__ = __repr__

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
	## Release Link Time Code Generation
	ltcg = ()
	## Code Analysis
	codeanalysis = ()
	## Fast cap
	fastcap = ()

	#
	# Create the platform codes from the platform type for Visual Studio
	#

	def getshortcode(self):
		if self == self.debug:
			return 'dbg'
		if self == self.release:
			return 'rel'
		if self == self.internal:
			return 'int'
		if self == self.profile:
			return 'pro'
		if self == self.ltcg:
			return 'ltc'
		if self == self.codeanalysis:
			return 'cod'
		if self == self.fastcap:
			return 'fas'
		return None

	def __repr__(self):
		if self == self.debug:
			return 'Debug'
		if self == self.release:
			return 'Release'
		if self == self.internal:
			return 'Internal'
		if self == self.profile:
			return 'Profile'
		if self == self.ltcg:
			return 'Release_LTCG'
		if self == self.codeanalysis:
			return 'CodeAnalysis'
		if self == self.fastcap:
			return 'Profile_FastCap'
		return None

	__str__ = __repr__

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
	## Visual studio 2017
	vs2017 = ()

	## Open Watcom 1.9 or later
	watcom = ()

	## Metrowerks Codewarrior 9 / 5.0 (Windows/Mac OS)
	codewarrior50 = ()
	## Metrowerks Codewarrior 10 / 5.8 (Mac OS Carbon)
	codewarrior58 = ()
	## Freescale Codewarrior 5.9 (Nintendo DSi)
	codewarrior59 = ()

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
	## XCode 8
	xcode8 = ()
	## XCode 9
	xcode9 = ()

	## Codeblocks
	codeblocks = ()

	## nmake
	nmake = ()

	#
	# Create the ide code from the ide type
	#

	def getshortcode(self):

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
		if self == self.vs2017:
			return 'v17'

		# Watcom MAKEFILE
		if self == self.watcom:
			return 'wat'

		# Metrowerks / Freescale CodeWarrior
		if self == self.codewarrior50:
			return 'c50'
		if self == self.codewarrior58:
			return 'c58'
		if self == self.codewarrior59:
			return 'c59'

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
		if self == self.xcode8:
			return 'xc8'
		if self == self.xcode9:
			return 'xc9'

		# Codeblocks
		if self == self.codeblocks:
			return 'cdb'

		# nmake
		if self == self.nmake:
			return 'nmk'

		return None

	def __repr__(self):
		if self == self.vs2003:
			return 'Visual Studio 2003'
		if self == self.vs2005:
			return 'Visual Studio 2005'
		if self == self.vs2008:
			return 'Visual Studio 2008'
		if self == self.vs2010:
			return 'Visual Studio 2010'
		if self == self.vs2012:
			return 'Visual Studio 2012'
		if self == self.vs2013:
			return 'Visual Studio 2013'
		if self == self.vs2015:
			return 'Visual Studio 2015'
		if self == self.vs2017:
			return 'Visual Studio 2017'
		if self == self.watcom:
			return 'Open Watcom 1.9 wmake'
		if self == self.codewarrior50:
			return 'CodeWarrior 9'
		if self == self.codewarrior58:
			return 'CodeWarrior 10'
		if self == self.codewarrior59:
			return 'Freescale CodeWarrior 5.9'
		if self == self.xcode3:
			return 'XCode 3.1.4'
		if self == self.xcode4:
			return 'XCode 4'
		if self == self.xcode5:
			return 'XCode 5'
		if self == self.xcode6:
			return 'XCode 6'
		if self == self.xcode7:
			return 'XCode 7'
		if self == self.xcode8:
			return 'XCode 8'
		if self == self.xcode9:
			return 'XCode 9'
		if self == self.codeblocks:
			return 'CodeBlocks 13.12'
		if self == self.nmake:
			return 'GNU make'
		return None

	__str__ = __repr__


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
	## Nintendo Switch
	switch = ()
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
	## Apple IIgs
	iigs = ()

	#
	## Convert the enumeration to a 3 letter code for filename suffix
	#

	def getshortcode(self):
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
		if self == self.switch:
			return 'swi'
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

		# Apple IIgs
		if self == self.iigs:
			return '2gs'
		return None

	#
	## Return True if the type is any windows platform
	#

	def iswindows(self):
		if self == self.windows or self == self.win32 or self == self.win64:
			return True
		return False

	#
	## Return True if the type is a macosx platform
	#

	def ismacosx(self):
		if self == self.macosx or self == self.macosxppc32 or \
			self == self.macosxppc64 or \
			self == self.macosxintel32 or self == self.macosxintel64:
			return True
		return False

	#
	## Return True if the type is a macos classic or carbon platform
	#

	def ismacos(self):
		if self == self.macos9 or self == self.macos968k or \
			self == self.macos9ppc or \
			self == self.maccarbon or self == self.maccarbon68k or \
			self == self.maccarbonppc:
			return True
		return False

	#
	## Return True if the type is macos carbon
	#

	def ismacoscarbon(self):
		if self == self.maccarbon or self == self.maccarbon68k or \
			self == self.maccarbonppc:
			return True
		return False

	#
	## Return True if the type is macos classic (MacOS 1.0 to 9.2.2)
	#

	def ismacosclassic(self):
		if self == self.macos9 or self == self.macos968k or \
			self == self.macos9ppc:
			return True
		return False

	@staticmethod
	def match(first, second):
		if first == second:
			return True
		if first == PlatformTypes.windows or second == PlatformTypes.windows:
			if first.iswindows() == second.iswindows():
				return True
		return False

	#
	## Create the platform codes from the platform type for Visual Studio
	#

	def getvsplatform(self):
		# Windows targets
		if self == PlatformTypes.windows:
			return ['Win32', 'x64']
		if self == PlatformTypes.win32:
			return ['Win32']
		if self == PlatformTypes.win64:
			return ['x64']

		# Microsoft Xbox versions
		if self == PlatformTypes.xbox:
			return ['Xbox']
		if self == PlatformTypes.xbox360:
			return ['Xbox 360']
		if self == PlatformTypes.xboxone:
			return ['Xbox ONE']

		# Sony platforms
		if self == PlatformTypes.ps3:
			return ['PS3']
		if self == PlatformTypes.ps4:
			return ['ORBIS']
		if self == PlatformTypes.vita:
			return ['PSVita']

		# Nintendo platforms
		if self == PlatformTypes.wiiu:
			return ['Cafe']
		if self == PlatformTypes.dsi:
			return ['CTR']
		if self == PlatformTypes.switch:
			return ['Switch']

		# Google platforms
		if self == PlatformTypes.android:
			return ['Android']
		if self == PlatformTypes.shield:
			return ['Tegra-Android',
				'ARM-Android-NVIDIA',
				'AArch64-Android-NVIDIA',
				'x86-Android-NVIDIA',
				'x64-Android-NVIDIA']
		return []

#
## Object for special properties
#
# For every configuration or source file, there are none
# or more properties that affect the generated project
# files either by object or globally
#

class Property(object):
	def __init__(self, configuration=None, platform=None, name=None, data=None):
		# Sanity check
		if not configuration is None and not isinstance(configuration, ConfigurationTypes):
			raise TypeError(
				"parameter 'configuration' must be of type ConfigurationTypes")
		if name is None:
			raise TypeError("Property is missing a name")

		# Save the configuration this matches
		self.configuration = configuration
		# Save the platform type this matches
		self.platform = platform
		# Save the name of the property
		self.name = name
		# Save the data for the property
		self.data = data

	@staticmethod
	def find(entries, name=None, configuration=None, platform=None):
		result = []
		for item in entries:
			if configuration is None or item.configuration is None or item.configuration == configuration:
				if platform is None or item.platform is None or PlatformTypes.match(item.platform, platform):
					if name is None or item.name == name:
						result.append(item)
		return result

	@staticmethod
	def getdata(entries, name=None, configuration=None, platform=None):
		result = []
		for item in entries:
			if configuration is None or item.configuration is None or item.configuration == configuration:
				if platform is None or item.platform is None or PlatformTypes.match(item.platform, platform):
					if name is None or item.name == name:
						result.append(item.data)
		return result

#
## Object for each input file to insert to a solution
#
# For every file that could be included into a project file
# one of these objects is created and attached to a solution object
# for processing
#

class SourceFile(object):

	#
	## Default constructor
	#
	# \param self The 'this' reference
	# \param relativepathname Filename of the input file (relative to the root)
	# \param directory Pathname of the root directory
	# \param filetype Compiler to apply
	# \sa FileTypes_lookup
	#

	def __init__(self, relativepathname, directory, filetype):
		# Sanity check
		if not isinstance(filetype, FileTypes):
			raise TypeError("parameter 'filetype' must be of type FileTypes")

		## File base name with extension (Converted to use windows style slashes on creation)
		self.filename = burger.convert_to_windows_slashes(relativepathname)

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
		slash = '\\'
		index = self.filename.rfind(slash)
		if index == -1:
			slash = '/'
			index = self.filename.rfind(slash)
			if index == -1:
				return ''

		#
		# Remove the basename
		#

		newname = self.filename[0:index]

		#
		# If there are ..\\ at the beginning, remove them
		#

		while newname.startswith('..' + slash):
			newname = newname[3:len(newname)]

		#
		# If there is a .\\, remove the single prefix
		#

		while newname.startswith('.' + slash):
			newname = newname[2:len(newname)]

		return newname

#
# Expose these classes
#

from makeprojects.core import Project, Solution

#
## Calls the internal function to save a default projects.py file
#
# Given a pathname, create and write out a default projects.py file
# that can be used as input to makeprojects to generate project files.
#
# \param destinationfile Pathname of where to save the default python script
#


def savedefault(destinationfile='projects.py'):
	import os
	import shutil
	src = os.path.join(os.path.dirname(
		os.path.abspath(__file__)), 'projects.py')
	try:
		shutil.copyfile(src, destinationfile)
	except Exception as error:
		print error


#
## Create a new instance of a core.Solution
#
# Convenience routine to create a core.Solution instance.
#
# \param name Name of the solution
# \param suffixenable True if suffixes are added to project names to denote project
# type and compiler
# \sa core.Solution
#

def newsolution(name='project', suffixenable=False):
	return Solution(name=name, suffixenable=suffixenable)

#
## Create a new instance of a core.Project
#
# Convenience routine to create a core.Project instance.
#
# \param name Name of the project
# \param projecttype Kind of project to make 'tool','app','library','sharedlibrary'
# \ref ProjectTypes
# \param suffixenable True if suffixes are added to project names to denote project
# type and compiler
# \sa core.Project
#

def newproject(name='project', projecttype=ProjectTypes.tool, suffixenable=False):
	return Project(name=name, projecttype=projecttype, suffixenable=suffixenable)
