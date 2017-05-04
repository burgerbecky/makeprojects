#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2016 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

#
# Note: This is only executed if makeprojects is imported as a module
#

#
## \package makeprojects Master package
# All packages for project generation is contained in this package.
#
# \par List of notable classes
# 
# \li \ref makeprojects.core.FileTypes
# \li \ref makeprojects.core.SourceFile
# \li \ref makeprojects.core.SolutionData
# \li \ref makeprojects.core.ProjectData
#
# \par List of sub packages
#
# \li \ref makeprojects.core
# \li \ref makeprojects.visualstudio
# \li \ref makeprojects.xcode
#

#
# Describe this module
#

## Current version of the library
__version__ = '0.6.0'

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
__copyright__ = 'Copyright 2013-2016 Rebecca Ann Heineman'

#
## Items to import on "from makeprojects import *"
#

__all__ = [
	'__version__',
	'__author__',
	'__title__',
	'__summary__',
	'__uri__',
	'__email__',
	'__license__',
	'__copyright__',
	'savedefault',
	'newsolution',
	'newproject',

	'FileTypes',
	'ProjectTypes',
	'IDETypes',
	'PlatformTypes',
	'ConfigurationTypes',
	
	'SourceFile',
	'ProjectData',
	'SolutionData',
	'visualstudio',
#	'watcom',
#	'codeblocks',
#	'codewarrior',
	'xcode'
]

#
# Expose these classes
#

from core import FileTypes,ProjectTypes,IDETypes,PlatformTypes,ConfigurationTypes

from core import SourceFile,ProjectData,SolutionData

#
## Calls the internal function to save a default projects.py file
#
#\param destinationfile Pathname of where to save the default python script
#\sa core.savedefault()
#

def savedefault(destinationfile='projects.py'):
	from .core import savedefault
	return savedefault(destinationfile)

#
## Create a new instance of a core.SolutionData
#
#\param name Name of the solution
#\param suffixenable True if suffixes are added to project names to denote project type and compiler
#\sa core.SolutionData
#

def newsolution(name='project',suffixenable=False):
	return SolutionData(name=name,suffixenable=suffixenable)

#
## Create a new instance of a core.ProjectData
#
#\param name Name of the project
#\param projecttype Kind of project to make 'tool','game','library','dll'
#\param suffixenable True if suffixes are added to project names to denote project type and compiler
#\sa core.ProjectData
#

def newproject(name='project',projecttype=ProjectTypes.tool,suffixenable=False):
	return ProjectData(name=name,projecttype=projecttype,suffixenable=suffixenable)
