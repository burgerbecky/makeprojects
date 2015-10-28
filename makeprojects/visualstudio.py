#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Sub file for makeprojects.
# Handler for Microsoft Visual Studio projects
#

# Copyright 1995-2014 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

import os
import uuid
import burger
import core
import io
from enum import Enum

#
## \package makeprojects.visualstudio
# This module contains classes needed to generate
# project files intended for use by
# Microsoft's Visual Studio IDE
#

#
# Default folder for Windows tools when invoking 'finalfolder'
# from the command line
#

defaultfinalfolder = '$(BURGER_SDKS)/windows/bin/'

#
## Enumeration of supported file types for input
#

class FileVersions(Enum):
	## Visual Studio 2003
	vs2003 = 0
	## Visual Studio 2005
	vs2005 = 1
	## Visual Studio 2008
	vs2008 = 2
	## Visual Studio 2010
	vs2010 = 3
	## Visual Studio 2012
	vs2012 = 4	
	## Visual Studio 2013
	vs2013 = 5	
	## Visual Studio 2015
	vs2015 = 6
	
#
## Solution (.sln) file version number to encode
#

formatversion = [
	'8.00',			# 2003
	'9.00',			# 2005
	'10.00',		# 2008
	'11.00',		# 2010
	'12.00',		# 2012
	'12.00',		# 2013
	'12.00'			# 2015
]

#
## Solution (.sln) year version number to encode
#
	
yearversion = [
	'2003',			# 2003
	'2005',			# 2005
	'2008',			# 2008
	'2010',			# 2010
	'2012',			# 2012
	'2013',			# 2013
	'14'			# 2015
]

#
## Project file suffix to append to the name (It changed after vs2008)
#

projectsuffix = [
	'.vcproj',		# 2003
	'.vcproj',		# 2005
	'.vcproj',		# 2008
	'.vcxproj',		# 2010
	'.vcxproj',		# 2012
	'.vcxproj',		# 2013
	'.vcxproj'		# 2015
]
	
#
## Convert a string to a UUUD
#
# Given a project name string, create a 128 bit unique hash for
# Visual Studio
#

def calcuuid(input):
	return str(uuid.uuid3(uuid.NAMESPACE_DNS,str(input))).upper()

#
# Subroutine for saving out a group of filenames based on compiler used
# Used by the filter exporter
#
	
def writefiltergroup(fp,filelist,groups,compilername):
		
	# Iterate over the list
	for item in filelist:
		# Get the Visual Studio group name
		groupname = item.extractgroupname()
		if groupname!='':
			# Add to the list of groups found
			groups.append(groupname)
			# Write out the record
			fp.write(u'\t\t<' + compilername + ' Include="' + burger.converttowindowsslashes(item.filename) + '">\n')
			fp.write(u'\t\t\t<Filter>' + groupname + '</Filter>\n')
			fp.write(u'\t\t</' + compilername + '>\n')
					
#
## Compare text file and a string for equality
#
# Check if a text file is the same as a string
# by loading the text file and
# testing line by line to verify the equality
# of the contents
# If they are the same, return True
# Otherwise return False
#
# \param filename string object with the pathname of the file to test
# \param string string object to test against
#

def comparefiletostring(filename,string):

	#
	# Do a data compare as a text file
	#
	
	f1 = None
	try:
		f1 = io.open(filename,'r')
		fileOneLines = f1.readlines()
		f1.close()

	except:
		if f1!=None:
			f1.close()
		return False
	
	#
	# Compare the file contents taking into account
	# different line endings
	#
	
	fileTwoLines = string.getvalue().splitlines(True)
	f1size = len(fileOneLines)
	f2size = len(fileTwoLines)
	
	#
	# Not the same size?
	#
	
	if f1size != f2size:
		return False

	x = 0
	for i in fileOneLines:
		if i != fileTwoLines[x]:
			return False
		x += 1
		
	# It's a match!

	return True

	
#
# Class to hold the defaults and settings to output a visualstudio
# compatible project file.
# json keyword "visualstudio" for dictionary of overrides
#

class Defaults:

	#
	# Power up defaults
	#
	
	def __init__(self):
		# Visual studio version code
		self.idecode = None
		# Visual studio platform code
		self.platformcode = None
		# GUID for the project
		self.uuid = None
		# Project filename override
		self.projectfilename = None
		# List of acceptable file types
		self.acceptable = []

		## File version to encode (Default vs2010)
		self.fileversion = FileVersions.vs2010

	#
	# The solution has been set up, perform setup
	# based on the type of project being created
	#
	
	def defaults(self,solution):
		
		#
		# Determine settings for the generated solution file
		#
		
		if solution.ide=='vs2003':
			self.fileversion = FileVersions.vs2003
	
		elif solution.ide=='vs2005':
			self.fileversion = FileVersions.vs2005

		elif solution.ide=='vs2008':
			self.fileversion = FileVersions.vs2008

		elif solution.ide=='vs2010':
			self.fileversion = FileVersions.vs2010

		elif solution.ide=='vs2012':
			self.fileversion = FileVersions.vs2012

		elif solution.ide=='vs2013':
			self.fileversion = FileVersions.vs2013

		elif solution.ide=='vs2015':
			self.fileversion = FileVersions.vs2015
		else:
			# Not supported yet
			return 10

		#
		# Get the config file name and default frameworks
		#
		
		self.idecode = solution.getidecode()
		self.platformcode = solution.getplatformcode()
		self.projectfilename = str(solution.projectname + self.idecode + self.platformcode)
		self.uuid = calcuuid(self.projectfilename)
	
		#
		# Create a list of acceptable files that can be included in the project
		#
		
		self.acceptable = [core.FileTypes.h,core.FileTypes.cpp]
		if self.platformcode=='win':
			self.acceptable.extend([core.FileTypes.rc,core.FileTypes.ico])
			# 2010 or higher supports hlsl and glsl files
			if self.fileversion.value>=FileVersions.vs2010.value:
				self.acceptable.extend([core.FileTypes.hlsl,core.FileTypes.glsl])
				
		# Xbox 360 shaders are supported
		elif self.platformcode=='x36' and self.fileversion==FileVersions.vs2010:
			self.acceptable.append(core.FileTypes.x360sl)
			
		# PS Vita shaders are supported
		elif self.platformcode=='vit' and self.fileversion==FileVersions.vs2010:
			self.acceptable.append(core.FileTypes.vitacg)
			
		return 0
	
	#
	# A json file had the key "visualstudio" with a dictionary.
	# Parse the dictionary for extra control
	#

	def loadjson(self,myjson):
		error = 0
		for key in myjson.keys():
			print 'Unknown keyword "' + str(key) + '" with data "' + str(myjson[key]) + '" found in loadjson'
			error = 1

		return error




#
# The classes below support the .sln file
#


#
# Class to manage a solution file's nested class
#

class NestedProjects:
	def __init__(self,name):
		self.name = name
		self.uuid = calcuuid(name + 'NestedProjects')
		self.uuidlist = []
		
	#
	# Add a uuid to track for this nested project list
	#
	
	def adduuid(self,uuid):
		self.uuidlist.append(uuid)
		
	#
	# Write the record into project record
	#
	
	def write(self,fp):
		fp.write(u'Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "' + self.name + '", "' + self.name + '", "{' + self.uuid + '}"\n')
		fp.write(u'EndProject\n')

	#
	# Inside the GlobalSection(NestedProjects) = preSolution record, output
	# the uuid list this item controls
	#
			
	def writeGlobalSection(self,fp):
		for item in self.uuidlist:
			fp.write(u'\t\t{' + item + '} = {' + self.uuid + '}\n')
			
				
#
## Object that contains constants for specific versions of Visual Studio
#
# Most data is shared from different versions of Visual Studio
# but for the contants that differ, they are stored in
# this class
#

class SolutionFile:

	def __init__(self,fileversion,solution):
		self.fileversion = fileversion
		self.solution = solution
		self.nestedprojects = []
		
	#
	## Add a nested project entry
	#
	
	def addnestedprojects(self,name):
		entry = NestedProjects(name)
		self.nestedprojects.append(entry)
		return entry

	#
	# Serialize the solution file (Requires UTF-8 encoding)
	#

	def write(self,fp):
		#
		# Save off the UTF-8 header marker
		#
		fp.write(u'\xef\xbb\xbf\n')
	
		#
		# Save off the format header
		#
		fp.write(u'Microsoft Visual Studio Solution File, Format Version ' + formatversion[self.fileversion.value] + '\n')

		#
		# Save the version of Visual Studio requested
		#
	
		fp.write(u'# Visual Studio ' + yearversion[self.fileversion.value] + '\n')

		#
		# New lines added for Visual Studio 2015 for file versioning 
		#
		
		if self.fileversion==FileVersions.vs2015:
			fp.write(u'VisualStudioVersion = 14.0.22823.1\n')
			fp.write(u'MinimumVisualStudioVersion = 10.0.40219.1\n')

		#
		# If there were any nested projects, output the master list
		#

		for item in self.nestedprojects:
			item.write(fp)

		#
		# Save off the project record
		#
	
		fp.write(u'Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "' + self.solution.projectname + '", "' + self.solution.visualstudio.projectfilename + projectsuffix[self.fileversion.value] + '", "{' + self.solution.visualstudio.uuid + '}"\n')
		fp.write(u'EndProject\n')
	
		#
		# Begin the Global record
		#
	
		fp.write(u'Global\n')

		#
		# Write out the SolutionConfigurationPlatforms
		#
	
		fp.write(u'\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n')
		vsplatforms	= self.solution.getvsplatform()
		for target in self.solution.configurations:
			for item in vsplatforms:
				token = target + '|' + item
				fp.write(u'\t\t' + token + ' = ' + token + '\n')
		fp.write(u'\tEndGlobalSection\n')

		#
		# Write out the ProjectConfigurationPlatforms
		#
	
		fp.write(u'\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n')
		for target in self.solution.configurations:
			for item in vsplatforms:
				token = target + '|' + item
				fp.write(u'\t\t{' + self.solution.visualstudio.uuid + '}.' + token + '.ActiveCfg = ' + token + '\n')
				fp.write(u'\t\t{' + self.solution.visualstudio.uuid + '}.' + token + '.Build.0 = ' + token + '\n')
		fp.write(u'\tEndGlobalSection\n')

		#
		# Hide nodes section
		#
	
		fp.write(u'\tGlobalSection(SolutionProperties) = preSolution\n')
		fp.write(u'\t\tHideSolutionNode = FALSE\n')
		fp.write(u'\tEndGlobalSection\n')
	
		if len(self.nestedprojects):
			fp.write(u'\tGlobalSection(NestedProjects) = preSolution\n')
			for item in self.nestedprojects:
				item.writeGlobalSection(fp)
			fp.write(u'\tEndGlobalSection\n')
			
		#
		# Close it up!
		#
		
		fp.write(u'EndGlobal\n')	
		return 0

#
# Project file generator (Generates main project file and the filter file)
#

class vsProject:
	
	#
	# Create a project file
	#
	def __init__(self,defaults,codefiles,includedirectories):
		self.defaults = defaults
		# Directories to use for file inclusion
		self.includedirectories = includedirectories
		# Seperate all the files to the types to be generated with
		self.listh = core.pickfromfilelist(codefiles,core.FileTypes.h)
		self.listcpp = core.pickfromfilelist(codefiles,core.FileTypes.cpp)
		self.listwindowsresource = core.pickfromfilelist(codefiles,core.FileTypes.rc)
		self.listhlsl = core.pickfromfilelist(codefiles,core.FileTypes.hlsl)
		self.listglsl = core.pickfromfilelist(codefiles,core.FileTypes.glsl)
		self.listx360sl = core.pickfromfilelist(codefiles,core.FileTypes.x360sl)
		self.listvitacg = core.pickfromfilelist(codefiles,core.FileTypes.vitacg)
		self.listico = core.pickfromfilelist(codefiles,core.FileTypes.ico)
	
	#
	# Write out the project file in the 2010 format
	#
	
	def writeproject2010(self,fp,solution):
		#
		# Save off the xml header
		#
	
		fp.write(u'<?xml version="1.0" encoding="utf-8"?>\n')
		if self.defaults.fileversion.value>=FileVersions.vs2015.value:
			toolsversion = '14.0'
		else:
			toolsversion = '4.0'
		fp.write(u'<Project DefaultTargets="Build" ToolsVersion="' + toolsversion + '" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">\n')

		#
		# nVidia Shield projects have a version header
		#

		if self.defaults.platformcode=='shi':
			fp.write(u'\t<PropertyGroup Label="NsightTegraProject">\n')
			fp.write(u'\t\t<NsightTegraProjectRevisionNumber>8</NsightTegraProjectRevisionNumber>\n')
			fp.write(u'\t</PropertyGroup>\n')

		#
		# Write the project configurations
		#

		fp.write(u'\t<ItemGroup Label="ProjectConfigurations">\n')
		for target in solution.configurations:
			for vsplatform in solution.getvsplatform():
				token = target + '|' + vsplatform
				fp.write(u'\t\t<ProjectConfiguration Include="' + token + '">\n')		
				fp.write(u'\t\t\t<Configuration>' + target + '</Configuration>\n')
				fp.write(u'\t\t\t<Platform>' + vsplatform + '</Platform>\n')
				fp.write(u'\t\t</ProjectConfiguration>\n')
		fp.write(u'\t</ItemGroup>\n')
	
		#
		# Write the project globals
		#
	
		fp.write(u'\t<PropertyGroup Label="Globals">\n')
		fp.write(u'\t\t<ProjectName>' + solution.projectname + '</ProjectName>\n')
		if solution.finalfolder!=None:
			final = burger.converttowindowsslasheswithendslash(solution.finalfolder)
			fp.write(u'\t\t<FinalFolder>' + final + '</FinalFolder>\n')
		fp.write(u'\t\t<ProjectGuid>{' + self.defaults.uuid + '}</ProjectGuid>\n')
		fp.write(u'\t</PropertyGroup>\n')	
	
		#
		# Add in the project includes
		#

		fp.write(u'\t<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.Default.props" />\n')
		if self.defaults.fileversion.value>=FileVersions.vs2015.value:
			fp.write(u'\t<PropertyGroup Label="Configuration">\n')
			fp.write(u'\t\t<PlatformToolset>v140</PlatformToolset>\n')
			fp.write(u'\t</PropertyGroup>\n')
		
		if solution.kind=='library':
			fp.write(u'\t<Import Project="$(BURGER_SDKS)\\visualstudio\\burger.libv10.props" />\n')
		elif solution.kind=='tool':
			fp.write(u'\t<Import Project="$(BURGER_SDKS)\\visualstudio\\burger.toolv10.props" />\n')
		else:
			fp.write(u'\t<Import Project="$(BURGER_SDKS)\\visualstudio\\burger.gamev10.props" />\n')	
		fp.write(u'\t<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.props" />\n')
		fp.write(u'\t<ImportGroup Label="ExtensionSettings" />\n')
		fp.write(u'\t<ImportGroup Label="PropertySheets" />\n')
		fp.write(u'\t<PropertyGroup Label="UserMacros" />\n')

		#
		# Insert compiler settings
		#
	
		if len(self.includedirectories) or \
			len(solution.includefolders) or \
			len(solution.defines):
			fp.write(u'\t<ItemDefinitionGroup>\n')
		
			#
			# Handle global compiler defines
			#
		
			if len(self.includedirectories) or \
				len(solution.includefolders) or \
				len(solution.defines):
				fp.write(u'\t\t<ClCompile>\n')
	
				# Include directories
				if len(self.includedirectories) or len(solution.includefolders):
					fp.write(u'\t\t\t<AdditionalIncludeDirectories>')
					for dir in self.includedirectories:
						fp.write(u'$(ProjectDir)' + burger.converttowindowsslashes(dir) + ';')
					for dir in solution.includefolders:
						fp.write(burger.converttowindowsslashes(dir) + ';')
					fp.write(u'%(AdditionalIncludeDirectories)</AdditionalIncludeDirectories>\n')	

				# Global defines
				if len(solution.defines):
					fp.write(u'\t\t\t<PreprocessorDefinitions>')
					for define in solution.defines:
						fp.write(define + ';')
					fp.write(u'%(PreprocessorDefinitions)</PreprocessorDefinitions>\n')
		
				fp.write(u'\t\t</ClCompile>\n')

			#
			# Handle global linker defines
			#
		
			if len(solution.includefolders):
				fp.write(u'\t\t<Link>\n')
	
				# Include directories
				if len(solution.includefolders):
					fp.write(u'\t\t\t<AdditionalLibraryDirectories>')
					for dir in solution.includefolders:
						fp.write(burger.converttowindowsslashes(dir) + ';')
					fp.write(u'%(AdditionalLibraryDirectories)</AdditionalLibraryDirectories>\n')

				fp.write(u'\t\t</Link>\n')

			fp.write(u'\t</ItemDefinitionGroup>\n')

		#
		# This is needed for the PS3 and PS4 targets :(
		#
	
		if self.defaults.platformcode=='ps3' or self.defaults.platformcode=='ps4':
			fp.write(u'\t<ItemDefinitionGroup Condition="\'$(BurgerConfiguration)\'!=\'Release\'">\n')
			fp.write(u'\t\t<ClCompile>\n')
			fp.write(u'\t\t\t<PreprocessorDefinitions>_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n')
			fp.write(u'\t\t</ClCompile>\n')
			fp.write(u'\t</ItemDefinitionGroup>\n')
			fp.write(u'\t<ItemDefinitionGroup Condition="\'$(BurgerConfiguration)\'==\'Release\'">\n')
			fp.write(u'\t\t<ClCompile>\n')
			fp.write(u'\t\t\t<PreprocessorDefinitions>NDEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n')
			fp.write(u'\t\t</ClCompile>\n')
			fp.write(u'\t</ItemDefinitionGroup>\n')

		#
		# Any source files for the item groups?
		#
		
		if len(self.listh) or \
			len(self.listcpp) or \
			len(self.listwindowsresource) or \
			len(self.listhlsl) or \
			len(self.listglsl) or \
			len(self.listx360sl) or \
			len(self.listvitacg) or \
			len(self.listico):

			fp.write(u'\t<ItemGroup>\n')

			for item in self.listh:
				fp.write(u'\t\t<ClInclude Include="' + burger.converttowindowsslashes(item.filename) + '" />\n')

			for item in self.listcpp:
				fp.write(u'\t\t<ClCompile Include="' + burger.converttowindowsslashes(item.filename) + '" />\n')

			for item in self.listwindowsresource:
				fp.write(u'\t\t<ResourceCompile Include="' + burger.converttowindowsslashes(item.filename) + '" />\n')

			for item in self.listhlsl:
				fp.write(u'\t\t<HLSL Include="' + burger.converttowindowsslashes(item.filename) + '">\n')
				# Cross platform way in splitting the path (MacOS doesn't like windows slashes)
				basename = burger.converttowindowsslashes(item.filename).lower().rsplit('\\',1)[1]
				splitname = os.path.splitext(basename)
				if splitname[0].startswith('vs41'):
					profile = 'vs_4_1'
				elif splitname[0].startswith('vs4'):
					profile = 'vs_4_0'
				elif splitname[0].startswith('vs3'):
					profile = 'vs_3_0'
				elif splitname[0].startswith('vs2'):
					profile = 'vs_2_0'
				elif splitname[0].startswith('vs1'):
					profile = 'vs_1_1'
				elif splitname[0].startswith('vs'):
					profile = 'vs_2_0'
				elif splitname[0].startswith('ps41'):
					profile = 'ps_4_1'
				elif splitname[0].startswith('ps4'):
					profile = 'ps_4_0'
				elif splitname[0].startswith('ps3'):
					profile = 'ps_3_0'
				elif splitname[0].startswith('ps2'):
					profile = 'ps_2_0'
				elif splitname[0].startswith('ps'):
					profile = 'ps_2_0'
				elif splitname[0].startswith('tx'):
					profile = 'tx_1_0'
				elif splitname[0].startswith('gs41'):
					profile = 'gs_4_1'
				elif splitname[0].startswith('gs'):
					profile = 'gs_4_0'
				else:
					profile = 'fx_2_0'
		
				fp.write(u'\t\t\t<VariableName>g_' + splitname[0] + '</VariableName>\n')
				fp.write(u'\t\t\t<TargetProfile>' + profile + '</TargetProfile>\n')
				fp.write(u'\t\t</HLSL>\n')

			for item in self.listx360sl:
				fp.write(u'\t\t<X360SL Include="' + burger.converttowindowsslashes(item.filename) + '">\n')
				# Cross platform way in splitting the path (MacOS doesn't like windows slashes)
				basename = item.filename.lower().rsplit('\\',1)[1]
				splitname = os.path.splitext(basename)
				if splitname[0].startswith('vs3'):
					profile = 'vs_3_0'
				elif splitname[0].startswith('vs2'):
					profile = 'vs_2_0'
				elif splitname[0].startswith('vs1'):
					profile = 'vs_1_1'
				elif splitname[0].startswith('vs'):
					profile = 'vs_2_0'
				elif splitname[0].startswith('ps3'):
					profile = 'ps_3_0'
				elif splitname[0].startswith('ps2'):
					profile = 'ps_2_0'
				elif splitname[0].startswith('ps'):
					profile = 'ps_2_0'
				elif splitname[0].startswith('tx'):
					profile = 'tx_1_0'
				else:
					profile = 'fx_2_0'
		
				fp.write(u'\t\t\t<VariableName>g_' + splitname[0] + '</VariableName>\n')
				fp.write(u'\t\t\t<TargetProfile>' + profile + '</TargetProfile>\n')
				fp.write(u'\t\t</X360SL>\n')

			for item in self.listvitacg:
				fp.write(u'\t\t<VitaCGCompile Include="' + burger.converttowindowsslashes(item.filename) + '">\n')
				# Cross platform way in splitting the path (MacOS doesn't like windows slashes)
				basename = item.filename.lower().rsplit('\\',1)[1]
				splitname = os.path.splitext(basename)
				if splitname[0].startswith('vs'):
					profile = 'sce_vp_psp2'
				else:
					profile = 'sce_fp_psp2'
				fp.write(u'\t\t\t<TargetProfile>' + profile + '</TargetProfile>\n')
				fp.write(u'\t\t</VitaCGCompile>\n')

			for item in self.listglsl:
				fp.write(u'\t\t<GLSL Include="' + burger.converttowindowsslashes(item.filename) + '" />\n')
				
			if self.defaults.fileversion.value>=FileVersions.vs2015.value:
				chunkname = 'Image'
			else:
				chunkname = 'None'
			for item in self.listico:
				fp.write(u'\t\t<' + chunkname + ' Include="' + burger.converttowindowsslashes(item.filename) + '" />\n')
				
			fp.write(u'\t</ItemGroup>\n')	
	
		#
		# Close up the project file!
		#
	
		fp.write(u'\t<Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />\n')
		fp.write(u'\t<ImportGroup Label="ExtensionTargets" />\n')
		fp.write(u'</Project>\n')
		return 0
		
	#
	# Write out the filter file
	#
		
	def writefilter(self,fp):

		#
		# Stock header for the filter
		#
		
		fp.write(u'<?xml version="1.0" encoding="utf-8"?>\n')
		fp.write(u'<Project ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">\n')
		fp.write(u'\t<ItemGroup>\n')

		groups = []
		writefiltergroup(fp,self.listh,groups,u'ClInclude')
		writefiltergroup(fp,self.listcpp,groups,u'ClCompile')
		writefiltergroup(fp,self.listwindowsresource,groups,u'ResourceCompile')
		writefiltergroup(fp,self.listhlsl,groups,u'HLSL')
		writefiltergroup(fp,self.listx360sl,groups,u'X360SL')
		writefiltergroup(fp,self.listvitacg,groups,u'VitaCGCompile')
		writefiltergroup(fp,self.listglsl,groups,u'GLSL')
		# Visual Studio 2015 and later have a "compiler" for ico files
		if self.defaults.fileversion.value>=FileVersions.vs2015.value:
			writefiltergroup(fp,self.listico,groups,u'Image')
		else:
			writefiltergroup(fp,self.listico,groups,u'None')
	
		# Remove all duplicate in the groups
		groupset = set(groups)
		
		# Output the group list
		for item in groupset:
			item = burger.converttowindowsslashes(item)
			groupuuid = calcuuid(self.defaults.projectfilename + item)
			fp.write(u'\t\t<Filter Include="' + item + '">\n')
			fp.write(u'\t\t\t<UniqueIdentifier>{' + groupuuid + '}</UniqueIdentifier>\n')
			fp.write(u'\t\t</Filter>\n')

		fp.write(u'\t</ItemGroup>\n')
		fp.write(u'</Project>\n')	
		
		return len(groupset)

#
# Root object for a Visual Studio Code IDE project file
# Created with the name of the project, the IDE code (vc8, v10)
# the platform code (win, ps4)
#

class Project:
	def __init__(self,defaults,solution):
		self.defaults = defaults
		self.slnfile = SolutionFile(defaults.fileversion,solution)
		self.projects = []

	#
	# Add a nested project into the solution
	#
	
	def addnestedprojects(self,name):
		return self.slnfile.addnestedprojects(name)
		
	#
	# Generate a .sln file for Visual Studio
	#
	
	def writesln(self,fp):
		return self.slnfile.write(fp)

	#
	# Generate a .vcxproj.filters file for Visual Studio 2010 or higher
	#
			
	def writeproject2010(self,fp,solution):
		error = 0
		if len(self.projects):
			for item in self.projects:
				error = item.writeproject2010(fp,solution)
				break
		return error

	#
	# Generate a .vcxproj.filters file for Visual Studio 2010 or higher
	#
			
	def writefilter(self,fp):
		count = 0
		if len(self.projects):
			for item in self.projects:
				count = count + item.writefilter(fp)
		return count
		

###################################
#                                 #
# Visual Studio 2003, 2005, 2008  #
# 2010, 2012 and 2015 support     #
#                                 #
###################################		
	
#
# Create a project file for Visual Studio (All supported flavors)
#

def generate(solution):

	#
	# Configure the Visual Studio writer to the type
	# of solution requested
	#
	
	error = solution.visualstudio.defaults(solution)
	if error!=0:
		return error
		
	#
	# Obtain the list of files of interest to include in
	# the project
	#
	
	codefiles,includedirectories = solution.getfilelist(solution.visualstudio.acceptable)
		
	#
	# Create a blank project
	#
	
	project = Project(solution.visualstudio,solution)
	project.projects.append(vsProject(solution.visualstudio,codefiles,includedirectories))

	#
	# Serialize the solution file and write if changed
	#
	
	fp = io.StringIO()
	project.writesln(fp)
	filename = os.path.join(solution.workingDir,solution.visualstudio.projectfilename + '.sln')
	if comparefiletostring(filename,fp):
		if solution.verbose==True:
			print filename + ' was not changed'
	else:
		burger.perforceedit(filename)
		fp2 = io.open(filename,'w')
		fp2.write(fp.getvalue())
		fp2.close()
	fp.close()
	
	#
	# Create the project file
	#
	
	fp = io.StringIO()
	if solution.visualstudio.fileversion.value>=FileVersions.vs2010.value:
		project.writeproject2010(fp,solution)
		filename = os.path.join(solution.workingDir,solution.visualstudio.projectfilename + projectsuffix[solution.visualstudio.fileversion.value])
		if comparefiletostring(filename,fp):
			if solution.verbose==True:
				print filename + ' was not changed'
		else:
			burger.perforceedit(filename)
			fp2 = io.open(filename,'w')
			fp2.write(fp.getvalue())
			fp2.close()
	fp.close()
	
	
	#
	# If it's visual studio 2010 or higher, output the filter file if needed
	#
	
	if solution.visualstudio.fileversion.value>=FileVersions.vs2010.value:
		
		fp = io.StringIO()
		count = project.writefilter(fp)
		filename = os.path.join(solution.workingDir,solution.visualstudio.projectfilename + '.vcxproj.filters')
		
		# No groups found?
		if count==0:
			# Just delete the file
			os.remove(filename)
		else:
			# Did it change?
			if comparefiletostring(filename,fp):
				if solution.verbose==True:
					print filename + ' was not changed'
			else:
				# Update the file
				burger.perforceedit(filename)
				fp2 = io.open(filename,'w')
				fp2.write(fp.getvalue())
				fp2.close()
		fp.close()

	return 0
	
