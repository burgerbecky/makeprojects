#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Root namespace for the makeprojects tool

"""

#
## \package makeprojects
#
# Makeprojects is a set of functions to generate project files
# for the most popular IDEs and build systems. Included are
# tools to automate building, cleaning and rebuilding projects.
#

#
## \mainpage
#
# \htmlinclude README.html
#
# \par List of IDE classes
#
# \li \ref makeprojects
# \li \ref makeprojects.core
# \li \ref makeprojects.enums.FileTypes
# \li \ref makeprojects.SourceFile
# \li \ref makeprojects.core.Solution
# \li \ref makeprojects.core.Project
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

from __future__ import absolute_import, print_function, unicode_literals

import burger

from .__pkginfo__ import NUMVERSION, VERSION, AUTHOR, TITLE, SUMMARY, URI, \
	EMAIL, LICENSE, COPYRIGHT
from .enums import AutoIntEnum, IDETypes, PlatformTypes, FileTypes, \
	ConfigurationTypes, ProjectTypes

########################################

# pylint: disable=W0105

## Current version of the library as a numeric tuple
__numversion__ = NUMVERSION

## Current version of the library
__version__ = VERSION

## Author's name
__author__ = AUTHOR

## Name of the module
__title__ = TITLE

## Summary of the module's use
__summary__ = SUMMARY

## Home page
__uri__ = URI

## Email address for bug reports
__email__ = EMAIL

## Type of license used for distribution
__license__ = LICENSE

## Copyright owner
__copyright__ = COPYRIGHT

## Items to import on "from makeprojects import *"

__all__ = [
	'build',
	'clean',
	'rebuild',
	'newsolution',
	'newproject',

	'FileTypes',
	'ProjectTypes',
	'ConfigurationTypes',
	'IDETypes',
	'PlatformTypes',

	'SourceFile',
	'Property',
	'visualstudio',
	'watcom',
	'codeblocks',
	'codewarrior',
	'xcode'
]

########################################


def build(working_dir=None, args=None):
	"""
	Invoke the buildme command line from within Python

	Args:
		working_dir: Directory to process, ``None`` for current working directory
		args: Argument list to pass to the command, None uses sys.argv
	Returns:
		Zero on success, system error code on failure
	See:
		makeprojects.buildme
	"""
	from .buildme import main
	return main(working_dir, args)

########################################


def clean(working_dir=None, args=None):
	"""
	Invoke the cleanme command line from within Python

	Args:
		working_dir: Directory to process, ``None`` for current working directory
		args: Argument list to pass to the command, None uses sys.argv
	Returns:
		Zero on success, system error code on failure
	See:
		makeprojects.cleanme
	"""

	from .cleanme import main
	return main(working_dir, args)

########################################


def rebuild(working_dir=None):
	"""
	Invoke the rebuildme command line from within Python

	Args:
		working_dir: Directory to process, ``None`` for current working directory
	Returns:
		Zero on success, system error code on failure
	See:
		makeprojects.rebuildme
	"""
	from .rebuildme import main
	return main(working_dir)

########################################


class Property(object):
	"""
	Object for special properties

	For every configuration or source file, there are none
	or more properties that affect the generated project
	files either by object or globally
	"""

	def __init__(self, configuration=None, platform=None, name=None, data=None):
		# Sanity check
		if configuration is None or \
			not isinstance(configuration, ConfigurationTypes):
			raise TypeError( \
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
		"""
		find
		"""
		result = []
		for item in entries:
			if configuration is None or item.configuration is None or \
				item.configuration == configuration:
				if platform is None or item.platform is None or \
					PlatformTypes.match(item.platform, platform):
					if name is None or item.name == name:
						result.append(item)
		return result

	@staticmethod
	def getdata(entries, name=None, configuration=None, platform=None):
		"""
		getdata
		"""
		result = []
		for item in entries:
			if configuration is None or item.configuration is None or \
				item.configuration == configuration:
				if platform is None or item.platform is None or \
					PlatformTypes.match(item.platform, platform):
					if name is None or item.name == name:
						result.append(item.data)
		return result


class SourceFile(object):

	"""
	Object for each input file to insert to a solution

	For every file that could be included into a project file
	one of these objects is created and attached to a solution object
	for processing
	"""
	#

	#

	def __init__(self, relativepathname, directory, filetype):
		"""
		Default constructor

		Args:
			self: The 'this' reference
			relativepathname: Filename of the input file (relative to the root)
			directory: Pathname of the root directory
			filetype: Compiler to apply
		See:
			_FILETYPES_LOOKUP
		"""
		# Sanity check
		if not isinstance(filetype, FileTypes):
			raise TypeError("parameter 'filetype' must be of type FileTypes")

		## File base name with extension using windows style slashes
		self.filename = burger.convert_to_windows_slashes(relativepathname)

		## Directory the file is found in (Full path)
		self.directory = directory

		## File type enumeration, see: \ref enums.FileTypes
		self.type = filetype

	def extractgroupname(self):
		"""
		Given a filename with a directory, remove the filename

		To determine if the file should be in a sub group in the project, scan
		the filename to find if it's a base filename or part of a directory
		If it's a basename, return an empty string.
		If it's in a folder, remove any ..\\ prefixes and .\\ prefixes
		and return the filename with the basename removed

		Args:
			self: The 'this' reference
		"""

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

########################################


def newsolution(name='project', suffixenable=False):
	"""
	Create a new instance of a core.Solution

	Convenience routine to create a core.Solution instance.

	Args:
		name: Name of the solution
		suffixenable: True if suffixes are added to project names to denote
			project type and compiler
	See:
		core.Solution
	"""

	from .core import Solution
	return Solution(name=name, suffixenable=suffixenable)

########################################


def newproject(name='project', projecttype=ProjectTypes.tool, \
	suffixenable=False):
	"""
	Create a new instance of a core.Project

	Convenience routine to create a core.Project instance.

	Args:
		name: Name of the project
		projecttype: Kind of project to make 'tool', 'app', 'library',
			'sharedlibrary' \ref enums.ProjectTypes
		suffixenable: True if suffixes are added to project names to denote
			project type and compiler
	See:
		core.Project
	"""

	from .core import Project
	return Project(name=name, projecttype=projecttype, suffixenable=suffixenable)
