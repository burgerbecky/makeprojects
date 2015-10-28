#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Sub file for makeprojects.
# Handler for Apple Computer XCode projects
#

# Copyright 1995-2014 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

import hashlib
import os
import StringIO
import core
import burger

#
## \package makeprojects.xcode
# This module contains classes needed to generate
# project files intended for use by Apple's XCode
# IDE
#

#
# Default folder for MacOSX tools when invoking 'finalfolder'
# from the command line
#

defaultfinalfolder = '$(BURGER_SDKS)/macosx/bin/'

#
# Given a string, create a 96 bit unique hash for XCode
#

def calcuuid(input):
	hash = hashlib.md5(burger.converttowindowsslashes(str(input))).hexdigest()

	#
	# Take the hash string and only use the top 96 bits
	#
	
	return hash[0:24].upper()

#
# Print a list of objects sorted by uuid
#
	
def writelist(selfarray,fp):

	#
	# Only print if there's items to process
	#
	
	if len(selfarray)!=0:
	
		#
		# Sort by uuid
		#
		selfarray = sorted(selfarray,cmp=lambda x,y: cmp(x.uuid,y.uuid))

		# Using the name of the class, output the array of data items
		itemname = selfarray[0].__class__.__name__
		fp.write('\n/* Begin ' + itemname + ' section */\n')
		for item in selfarray:
			item.write(fp)
		fp.write('/* End ' + itemname + ' section */\n')	

#
# Class to hold the defaults and settings to output an XCode
# compatible project file.
# json keyword "xcode" for dictionary of overrides
#

class Defaults:

	#
	# Power up defaults
	#
	
	def __init__(self):
		self.frameworks = []
		self.configfilename = None
		
	#
	# The solution has been set up, perform setup
	# based on the type of project being created
	#
	
	def defaults(self,solution):
		
		#
		# Get the config file name and default frameworks
		#
		
		minimumframeworks = []
		
		# Handle iOS targets
		
		if solution.platform=='ios':
			if solution.kind=='library':
				self.configfilename = 'burger.libxcoios.xcconfig'
			else:
				# Frameworks for an iOS app
				minimumframeworks = [
					'QuartzCore.framework',
					'CoreLocation.framework',
					'AVFoundation.framework',
					'UIKit.framework',
					'Foundation.framework',
					'CoreGraphics.framework'
				]
				if solution.kind=='game':
					self.configfilename = 'burger.gamexcoios.xcconfig'
				else:
					self.configfilename = 'burger.toolxcoios.xcconfig'

		# Handle Mac OSX targets
		
		elif solution.platform=='macosx':
		
			if solution.kind=='library':
				self.configfilename = 'burger.libxcoosx.xcconfig'
			else:
				# Frameworks for a Mac OSX app or tool
				minimumframeworks = [
					'AppKit.framework',
					'Cocoa.framework',
					'Carbon.framework',
					'IOKit.framework',
					'OpenGL.framework',
					'QuartzCore.framework'
				]
				if solution.kind=='game':
					self.configfilename = 'burger.gamexcoosx.xcconfig'
				else:
					self.configfilename = 'burger.toolxcoosx.xcconfig'
				
		#
		# Add the frameworks to the user supplied list
		#
		
		for item in minimumframeworks:
			# Only add if not already in the list
			if not item in self.frameworks:
				self.frameworks.append(item)
	
	#
	# A json file had the key "xcode" with a dictionary.
	# Parse the dictionary for extra control
	#
	
	def loadjson(self,myjson):
		error = 0
		for key in myjson.keys():
			if key=='frameworks':
				self.frameworks = burger.converttoarray(myjson[key])
			else:
				print 'Unknown keyword "' + str(key) + '" with data "' + str(myjson[key]) + '" found in loadjson'
				error = 1
	
		return error

#
# Each PBXBuildFile entry
# This record instructs xcode to build this file
#

class PBXBuildFile:
	def __init__(self,filereference,owner):
		self.filereference = filereference
		self.uuid = calcuuid('PBXBuildFile' + filereference.filename + owner.filename)
		
	def write(self,fp):
		# Is the file a framework?
		if self.filereference.type == core.FileTypes.frameworks:
			type = 'Frameworks'
		else:
		# It's a source file
			type = 'Sources'

		basename = os.path.basename(self.filereference.filename)
		fp.write('\t\t' + self.uuid + ' /* ' + basename + ' in ' + type + ' */ = {isa = PBXBuildFile; fileRef = ' + self.filereference.uuid + ' /* ' + basename + ' */; };\n')


#
# Each PBXFileReference entry
# Get the filename path and XCode type
#

class PBXFileReference:
	def __init__(self,filename,type):
		self.filename = filename
		self.uuid = calcuuid('PBXFileReference' + filename)
		self.type = type
		
	def write(self,fp):
		basename = os.path.basename(self.filename)
		
		#
		# Based on the file type, save out an assumed default to what kind of file XCode
		# is expecting
		#
		
		# Start by saving the uuid and the type of record
		
		fp.write('\t\t' + self.uuid + ' /* ' + basename + ' */ = {isa = PBXFileReference;')
		
		# If not binary, assume UTF-8 encoding
		
		if self.type != core.FileTypes.library and \
			self.type != core.FileTypes.exe and \
			self.type != core.FileTypes.frameworks:
			fp.write(' fileEncoding = 4;');
			
		# Each file type is handled differently
		
		if self.type == core.FileTypes.library:
			fp.write(' explicitFileType = archive.ar; includeInIndex = 0; path = ' + basename + '; sourceTree = BUILT_PRODUCTS_DIR;')
		elif self.type == core.FileTypes.exe:
			if basename.endswith('.app'):
				fp.write(' explicitFileType = wrapper.application; includeInIndex = 0; path = ' + basename + '; sourceTree = BUILT_PRODUCTS_DIR;')
			else:
				fp.write(' explicitFileType = compiled.mach-o.executable; includeInIndex = 0; path = ' + basename + '; sourceTree = BUILT_PRODUCTS_DIR;')
		elif self.type == core.FileTypes.frameworks:
			fp.write(' lastKnownFileType = wrapper.framework; name = ' + basename + '; path = System/Library/Frameworks/' + basename + '; sourceTree = SDKROOT;')
		elif self.type == core.FileTypes.glsl:
			fp.write(' lastKnownFileType = sourcecode.glsl; name = ' + basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')
		elif self.type == core.FileTypes.xml:
			if basename.endswith('.plist'):
				fp.write(' lastKnownFileType = text.plist.xml; name = ' + basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')
			else:
				fp.write(' lastKnownFileType = text.xml; name = ' + basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')
		elif self.type == core.FileTypes.xcconfig:
			fp.write(' lastKnownFileType = text.xcconfig; name = ' + basename + '; path = xcode/' + basename + '; sourceTree = SDKS;')
		elif self.type == core.FileTypes.cpp:
			fp.write(' lastKnownFileType = sourcecode.cpp.cpp; name = ' + basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')
		else:
			fp.write(' lastKnownFileType = sourcecode.c.h; name = ' + basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')

		# Close out the line
		
		fp.write(' };\n');

#
# Each PBXBuildFile entry
#

class PBXBuildRule:
	def __init__(self,owner):
		self.uuid = calcuuid('PBXBuildRule' + owner.projectnamecode)
		
	def write(self,fp):
		fp.write('\t\t' + self.uuid + ' /* PBXBuildRule */ = {\n')
		fp.write('\t\t\tisa = PBXBuildRule;\n')
		fp.write('\t\t\tcompilerSpec = com.apple.compilers.proxy.script;\n')
		fp.write('\t\t\tfilePatterns = "*.glsl";\n')
		fp.write('\t\t\tfileType = pattern.proxy;\n')
		fp.write('\t\t\tisEditable = 1;\n')
		fp.write('\t\t\toutputFiles = (\n')
		fp.write('\t\t\t\t"${INPUT_FILE_DIR}/${INPUT_FILE_BASE}.h",\n')
		fp.write('\t\t\t);\n')
		fp.write('\t\t\tscript = "${SDKS}/macosx/bin/stripcomments ${INPUT_FILE_PATH} -c -l g_${INPUT_FILE_BASE} ${INPUT_FILE_DIR}/${INPUT_FILE_BASE}.h";\n')
		fp.write('\t\t};\n')

#
# Each PBXGroup entry
#

class PBXGroup:
	def __init__(self,name,path):
		self.name = name
		self.path = path
		if path==None:
			path='<group>'
		self.uuid = calcuuid('PBXGroup' + name + path)
		self.filelist = []
		
	def write(self,fp):
		self.filelist = sorted(self.filelist,cmp=lambda x,y: cmp(x[1],y[1]))
		fp.write('\t\t' + self.uuid + ' /* ' + self.name + ' */ = {\n')
		fp.write('\t\t\tisa = PBXGroup;\n')
		fp.write('\t\t\tchildren = (\n')
		# Output groups first
		for item in self.filelist:
			if item[2]==True:
				fp.write('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,\n')
		# Output files last
		for item in self.filelist:
			if item[2]!=True:
				fp.write('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,\n')
		fp.write('\t\t\t);\n')
		if self.path!=None:
			if self.name!=self.path:
				fp.write('\t\t\tname = ' + self.name + ';\n')
			fp.write('\t\t\tpath = ' + self.path + ';\n')
			fp.write('\t\t\tsourceTree = SOURCE_ROOT;\n')
		else:
			fp.write('\t\t\tname = ' + self.name + ';\n')
			fp.write('\t\t\tsourceTree = "<group>";\n')
		fp.write('\t\t};\n')

	#
	# Append a file uuid and name to the end of the list
	#
	
	def append(self,item):
		self.filelist.append([item.uuid,os.path.basename(item.filename),False])

	#
	# Append a group to the end of the list
	#
	
	def appendgroup(self,item):
		self.filelist.append([item.uuid,item.name,True])

#
# Each PBXSourcesBuildPhase entry
#

class PBXSourcesBuildPhase:
	def __init__(self,owner):
		self.owner = owner
		self.uuid = calcuuid('PBXSourcesBuildPhase' + owner.filename)
		self.buildfirstlist = []
		self.buildlist = []
		
	def write(self,fp):
		self.buildfirstlist = sorted(self.buildfirstlist,cmp=lambda x,y: cmp(x[1],y[1]))
		self.buildlist = sorted(self.buildlist,cmp=lambda x,y: cmp(x[1],y[1]))
		fp.write('\t\t' + self.uuid + ' /* Sources */ = {\n')
		fp.write('\t\t\tisa = PBXSourcesBuildPhase;\n')
		fp.write('\t\t\tbuildActionMask = 2147483647;\n')
		fp.write('\t\t\tfiles = (\n')
		for item in self.buildfirstlist:
			fp.write('\t\t\t\t' + item[0].uuid + ' /* ' + item[1] + ' in Sources */,\n')
		for item in self.buildlist:
			fp.write('\t\t\t\t' + item[0].uuid + ' /* ' + item[1] + ' in Sources */,\n')
		fp.write('\t\t\t);\n')
		fp.write('\t\t\trunOnlyForDeploymentPostprocessing = 0;\n')
		fp.write('\t\t};\n')

	#
	# Append a file uuid and name to the end of the list
	#
	
	def append(self,item):
		if (item.filereference.type==core.FileTypes.glsl):
			self.buildfirstlist.append([item,os.path.basename(item.filereference.filename)])
		else:
			self.buildlist.append([item,os.path.basename(item.filereference.filename)])

#
# Each PBXFrameworksBuildPhase entry
#

class PBXFrameworksBuildPhase:
	def __init__(self,owner):
		self.owner = owner
		self.uuid = calcuuid('PBXFrameworksBuildPhase' + owner.filename)
		self.buildlist = []
		
	def write(self,fp):
		self.buildlist = sorted(self.buildlist,cmp=lambda x,y: cmp(x[1],y[1]))
		fp.write('\t\t' + self.uuid + ' /* Frameworks */ = {\n')
		fp.write('\t\t\tisa = PBXFrameworksBuildPhase;\n')
		fp.write('\t\t\tbuildActionMask = 2147483647;\n')
		fp.write('\t\t\tfiles = (\n')
		for item in self.buildlist:
			fp.write('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' in Frameworks */,\n')
		fp.write('\t\t\t);\n')
		fp.write('\t\t\trunOnlyForDeploymentPostprocessing = 0;\n')
		fp.write('\t\t};\n')

	#
	# Append a file uuid and name to the end of the list
	#
	
	def append(self,item):
		self.buildlist.append([item.uuid,os.path.basename(item.filereference.filename)])

#
# Each PBXShellScriptBuildPhase entry
#

class PBXShellScriptBuildPhase:
	def __init__(self,input,output,command):
		self.input = input
		self.output = output
		self.command = command
		self.uuid = calcuuid('PBXShellScriptBuildPhase' + str(input) + output + command)
		
	def write(self,fp):
		fp.write('\t\t' + self.uuid + ' /* ShellScript */ = {\n')
		fp.write('\t\t\tisa = PBXShellScriptBuildPhase;\n')
		fp.write('\t\t\tbuildActionMask = 2147483647;\n')
		fp.write('\t\t\tfiles = (\n')
		fp.write('\t\t\t);\n')
		if len(self.input)!=0:
			fp.write('\t\t\tinputPaths = (\n')
			for item in self.input:
				fp.write('\t\t\t\t"' + item + '",\n')
			fp.write('\t\t\t);\n')
		fp.write('\t\t\toutputPaths = (\n')
		fp.write('\t\t\t\t"' + self.output + '",\n')
		fp.write('\t\t\t);\n')
		fp.write('\t\t\trunOnlyForDeploymentPostprocessing = 0;\n')
		fp.write('\t\t\tshellPath = /bin/sh;\n')
		fp.write('\t\t\tshellScript = "' + self.command + '\\n";\n')
		fp.write('\t\t\tshowEnvVarsInLog = 0;\n')
		fp.write('\t\t};\n')
							
#
# Each PBXProject entry
#

class PBXProject:
	def __init__(self,project):
		self.project = project
		self.uuid = project.uuid
		self.configlistref = None
		self.targetlist = []
		self.rootgroup = None
		
	def write(self,fp):
		fp.write('\t\t' + self.uuid + ' /* Project object */ = {\n')
		fp.write('\t\t\tisa = PBXProject;\n')
		fp.write('\t\t\tattributes = {\n')
		fp.write('\t\t\t\tBuildIndependentTargetsInParallel = YES;\n')
		if self.project.idecode=='xc5':
			fp.write('\t\t\t\tLastUpgradeCheck = 0510;\n')
		fp.write('\t\t\t};\n')
		if self.configlistref!=None:
			fp.write('\t\t\tbuildConfigurationList = ' + self.configlistref.uuid + ' /* Build configuration list for PBXProject "' + self.project.projectnamecode + '" */;\n')

		if self.project.idecode!='xc3':
			fp.write('\t\t\tcompatibilityVersion = "Xcode 3.2";\n')
			fp.write('\t\t\tdevelopmentRegion = English;\n')
		else:
			fp.write('\t\t\tcompatibilityVersion = "Xcode 3.1";\n')

		fp.write('\t\t\thasScannedForEncodings = 1;\n')
		fp.write('\t\t\tknownRegions = (\n')
		fp.write('\t\t\t\ten,\n')
		fp.write('\t\t\t);\n')
		if self.rootgroup!=None:
			fp.write('\t\t\tmainGroup = ' + self.rootgroup.uuid + ' /* ' + self.rootgroup.name + ' */;\n')
		fp.write('\t\t\tprojectDirPath = "";\n')
		fp.write('\t\t\tprojectRoot = "";\n')
		fp.write('\t\t\ttargets = (\n')
		if len(self.targetlist)!=0:
			for item in self.targetlist:
				fp.write('\t\t\t\t' + item.uuid + ' /* ' + item.name + ' */,\n')
		fp.write('\t\t\t);\n')
		fp.write('\t\t};\n')

	#
	# Append a PBXNative target
	#
	
	def append(self,item):
		self.targetlist.append(item)
		
#
# Each PBXNative entry
#

class PBXNativeTarget:
	def __init__(self,parent,name,productreference,productname,producttype):
		self.parent = parent
		self.name = name
		self.productreference = productreference
		self.productname = productname
		self.producttype = producttype
		self.uuid = calcuuid('PBXNativeTarget' + name)
		self.configlistref = None
		self.phases = []
		self.depends = []
		
	def write(self,fp):
		fp.write('\t\t' + self.uuid + ' /* ' + self.name + ' */ = {\n')
		fp.write('\t\t\tisa = PBXNativeTarget;\n')
		if self.configlistref!=None:
			fp.write('\t\t\tbuildConfigurationList = ' + self.configlistref.uuid + ' /* Build configuration list for PBXNativeTarget "' + self.name + '" */;\n')
		fp.write('\t\t\tbuildPhases = (\n')
		for item in self.phases:
			fp.write('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,\n')
		fp.write('\t\t\t);\n')
		fp.write('\t\t\tbuildRules = (\n')
		for item in self.parent.pbxbuildrules:
			fp.write('\t\t\t\t' + item.uuid + ' /* PBXBuildRule */,\n')
		fp.write('\t\t\t);\n')
		fp.write('\t\t\tdependencies = (\n')
		for item in self.depends:
			fp.write('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,\n')
		fp.write('\t\t\t);\n')
		fp.write('\t\t\tname = ' + self.name + ';\n')
		fp.write('\t\t\tproductName = ' + self.productname + ';\n')
		fp.write('\t\t\tproductReference = ' + self.productreference.uuid + ' /* ' + self.productreference.filename + ' */;\n')
		fp.write('\t\t\tproductType = "' + self.producttype + '";\n')
		fp.write('\t\t};\n')

	#
	# Append a Buildphase target
	#
	
	def append(self,uuid,name):
		self.phases.append([uuid,name])

	#
	# Append a dependency
	#
	
	def depend(self,uuid,name):
		self.depends.append([uuid,name])

#
# Each XCBuildConfiguration entry
#

class XCBuildConfiguration:
	def __init__(self,configname,configfilereference,owner,sdkroot,installpath):
		self.configname = configname
		self.configfilereference = configfilereference
		self.sdkroot = sdkroot
		self.installpath = installpath
		self.uuid = calcuuid('XCBuildConfiguration' + owner.pbxtype + owner.targetname + configname)
		
	def write(self,fp):
		fp.write('\t\t' + self.uuid + ' /* ' + self.configname + ' */ = {\n')
		fp.write('\t\t\tisa = XCBuildConfiguration;\n')
		if self.configfilereference!=None:
			fp.write('\t\t\tbaseConfigurationReference = ' + self.configfilereference.uuid + ' /* ' + os.path.basename(self.configfilereference.filename) + ' */;\n')
		fp.write('\t\t\tbuildSettings = {\n')
		if self.sdkroot!=None:
			fp.write('\t\t\t\tSDKROOT = ' + self.sdkroot + ';\n')
		if self.installpath==True:
			fp.write('\t\t\t\tINSTALL_PATH = "$(HOME)/Applications";\n')
		fp.write('\t\t\t};\n')
		fp.write('\t\t\tname = ' + self.configname + ';\n')
		fp.write('\t\t};\n')

#
# Each XCConfigurationList entry
#

class XCConfigurationList:
	def __init__(self,pbxtype,targetname):
		self.pbxtype = pbxtype
		self.targetname = targetname
		self.configurations = []
		self.uuid = calcuuid('XCConfigurationList' + pbxtype + targetname)
		
	def write(self,fp):
		fp.write('\t\t' + self.uuid + ' /* Build configuration list for ' + self.pbxtype + ' "' + self.targetname + '" */ = {\n')
		fp.write('\t\t\tisa = XCConfigurationList;\n')
		fp.write('\t\t\tbuildConfigurations = (\n')
		default = None
		for item in self.configurations:
			if item.configname=='Release':
				default = 'Release'
			elif default==None:
				default = item.configname
			fp.write('\t\t\t\t' + item.uuid + ' /* ' + item.configname + ' */,\n')
		if default==None:
			default='Release'
		fp.write('\t\t\t);\n')
		fp.write('\t\t\tdefaultConfigurationIsVisible = 0;\n')
		fp.write('\t\t\tdefaultConfigurationName = ' + default + ';\n')
		fp.write('\t\t};\n')

#
# Each PBXContainerItemProxy entry
#

class PBXContainerItemProxy:
	def __init__(self,nativetarget,rootuuid):
		self.nativetarget = nativetarget
		self.rootuuid = rootuuid
		self.uuid = calcuuid('PBXContainerItemProxy' + nativetarget.name)
		
	def write(self,fp):
		fp.write('\t\t' + self.uuid + ' /* PBXContainerItemProxy */ = {\n')
		fp.write('\t\t\tisa = PBXContainerItemProxy;\n')
		fp.write('\t\t\tcontainerPortal = ' + self.rootuuid + ' /* Project object */;\n')
		fp.write('\t\t\tproxyType = 1;\n')
		fp.write('\t\t\tremoteGlobalIDString = ' + self.nativetarget.uuid + ';\n')
		fp.write('\t\t\tremoteInfo = "' + self.nativetarget.name + '";\n')
		fp.write('\t\t};\n')

#
# Each PBXTargetDependency entry
#

class PBXTargetDependency:
	def __init__(self,proxy,nativetarget):
		self.proxy = proxy
		self.nativetarget = nativetarget
		self.uuid = calcuuid('PBXTargetDependency' + proxy.nativetarget.name + nativetarget.name)
		
	def write(self,fp):
		fp.write('\t\t' + self.uuid + ' /* PBXTargetDependency */ = {\n')
		fp.write('\t\t\tisa = PBXTargetDependency;\n')
		fp.write('\t\t\ttarget = ' + self.nativetarget.uuid + ' /* ' + self.nativetarget.name + ' */;\n')
		fp.write('\t\t\ttargetProxy = ' + self.proxy.uuid + ' /* PBXContainerItemProxy */;\n')
		fp.write('\t\t};\n')

#
# Root object for an XCode IDE project file
# Created with the name of the project, the IDE code (xc3, xc5)
# the platform code (ios, osx) and the ide version (3 or 5)
#

class Project:
	def __init__(self,projectname,idecode,platformcode):
		self.projectname = projectname
		self.idecode = idecode
		self.platformcode = platformcode
		self.projectnamecode = str(projectname + idecode + platformcode)
		self.uuid = calcuuid('PBXProjectRoot' + self.projectnamecode)
		# No files yet!
		self.pbxfilereferences = []
		self.pbxbuildfiles = []
		self.pbxbuildrules = [PBXBuildRule(self)]
		self.pbxprojects = [PBXProject(self)]
		self.pbxnativetargets = []
		self.pbxgroups = []
		self.sourcesbuildphases = []
		self.framesworksbuildphases = []
		self.shellscriptbuildphases = []
		self.xcbuildconfigurations = []
		self.xcconfigurationlists = []
		self.containeritemproxies = []
		self.targetdependencies = []
	
	#
	# Add a new file reference
	#
	
	def addfilereference(self,filename,type):
		entry = PBXFileReference(filename,type)
		self.pbxfilereferences.append(entry)
		return entry

	#
	# Add a new file reference
	#
	
	def addbuildfile(self,filereference,owner):
		entry = PBXBuildFile(filereference,owner)
		self.pbxbuildfiles.append(entry)
		return entry

	#
	# Add a new file group
	#
	
	def addgroup(self,name,path):
		entry = PBXGroup(name,path)
		self.pbxgroups.append(entry)
		return entry

	#
	# Add a new source build phase list
	#
	
	def addsourcesbuildphase(self,owner):
		entry = PBXSourcesBuildPhase(owner)
		self.sourcesbuildphases.append(entry)
		return entry

	#
	# Add a new native target list
	#
	
	def addnativeproject(self,name,productreference,productname,producttype):
		entry = PBXNativeTarget(self,name,productreference,productname,producttype)
		self.pbxnativetargets.append(entry)
		return entry
		
	#
	# Add a new frameworks build phase list
	#
	
	def addframeworksbuildphase(self,owner):
		entry = PBXFrameworksBuildPhase(owner)
		self.framesworksbuildphases.append(entry)
		return entry

	#
	# Add a new configuration list
	#
	
	def addshellscriptbuildphase(self,input,output,command):
		entry = PBXShellScriptBuildPhase(input,output,command)
		self.shellscriptbuildphases.append(entry)
		return entry

	#
	# Add a new configuration list
	#
	
	def addxcbuildconfigurationlist(self,configname,configfilereference,owner,sdkroot,installpath):
		entry = XCBuildConfiguration(configname,configfilereference,owner,sdkroot,installpath)
		self.xcbuildconfigurations.append(entry)
		return entry

	#
	# Add a new configuration list
	#
	
	def addxcconfigurationlist(self,pbxtype,targetname):
		entry = XCConfigurationList(pbxtype,targetname)
		self.xcconfigurationlists.append(entry)
		return entry

	#
	# Add a new container item proxy
	#
	
	def addcontaineritemproxy(self,nativetarget,rootuuid):
		entry = PBXContainerItemProxy(nativetarget,rootuuid)
		self.containeritemproxies.append(entry)
		return entry

	#
	# Add a new dependency
	#
	
	def adddependency(self,proxy,nativetarget):
		entry = PBXTargetDependency(proxy,nativetarget)
		self.targetdependencies.append(entry)
		return entry
			
	#
	# Dump out the entire file
	#
	
	def write(self,fp):
		#
		# Write the XCode header
		#
	
		fp.write('// !$*UTF8*$!\n')
		fp.write('{\n')
	
		#
		# Always present in an XCode file
		#
	
		fp.write('\tarchiveVersion = 1;\n')
		fp.write('\tclasses = {\n')
		fp.write('\t};\n')
	
		#
		# 42 = XCode 2.4
		# 44 = XCode 3.0
		# 45 = XCode 3.1
		# 46 = XCode 3.2
		#

		if self.idecode=='xc3':
			fp.write('\tobjectVersion = 45;\n')
		else:
			fp.write('\tobjectVersion = 46;\n')
		fp.write('\tobjects = {\n')

		#
		# Write out each of the chunks
		#
		
		writelist(self.pbxbuildfiles,fp)
		writelist(self.pbxbuildrules,fp)
		writelist(self.containeritemproxies,fp)
		writelist(self.pbxfilereferences,fp)
		writelist(self.framesworksbuildphases,fp)
		writelist(self.pbxgroups,fp)
		writelist(self.pbxnativetargets,fp)
		writelist(self.pbxprojects,fp)
		writelist(self.shellscriptbuildphases,fp)
		writelist(self.sourcesbuildphases,fp)
		writelist(self.targetdependencies,fp)
		writelist(self.xcbuildconfigurations,fp)
		writelist(self.xcconfigurationlists,fp)
		
		#
		# Close up the project file
		#
	
		fp.write('\t};\n')
		fp.write('\trootObject = ' + self.uuid + ' /* Project object */;\n')
		fp.write('}\n')


###################################
#                                 #
# Xcode 3, 4 and 5 support        #
#                                 #
###################################		
	
#
# Create a project file for XCode file format version 3.1
#

def generate(solution):
	
	#
	# Find the files to put into the project
	#
	
	codefiles,includedirectories = solution.getfilelist([core.FileTypes.icns,core.FileTypes.h,core.FileTypes.cpp,core.FileTypes.frameworks,core.FileTypes.exe,core.FileTypes.library,core.FileTypes.glsl])

	#
	# Configure the xcode writer to the type
	# of solution requested
	#
	
	solution.xcode.defaults(solution)
	
	#
	# Ensure the slashes are correct for XCode
	#
	
	for item in codefiles:
		item.filename = burger.converttolinuxslashes(item.filename)

	#
	# Determine the ide and target type for the final file name
	#

	idecode = solution.getidecode()
	platformcode = solution.getplatformcode()
	xcodeprojectfile = Project(solution.projectname,idecode,platformcode)
	rootproject = xcodeprojectfile.pbxprojects[0]
	
	#
	# Let's create the solution file!
	#
	
	solutionfoldername = os.path.join(solution.workingDir,xcodeprojectfile.projectnamecode + '.xcodeproj')
	burger.createfolderifneeded(solutionfoldername)
	projectfilename = os.path.join(solutionfoldername,'project.pbxproj')
	
	#
	# Add the configuration file reference (or not)
	#
	
	if solution.xcode.configfilename!=None:
		configfilereference = xcodeprojectfile.addfilereference(solution.xcode.configfilename,core.FileTypes.xcconfig)
	else:
		configfilereference = None
		
	#
	# Add the frameworks to the build list
	#

	for framework in solution.xcode.frameworks:
		item = core.SourceFile(framework,'',core.FileTypes.frameworks)
		codefiles.append(item)	

	#
	# Insert all of the files found into the file references
	#
	
	for item in codefiles:
		# Remove unsupported file types
		if item.type!=core.FileTypes.rc and \
			item.type!=core.FileTypes.r and \
			item.type!=core.FileTypes.hlsl:
			xcodeprojectfile.addfilereference(item.filename,item.type)

	#
	# What's the final output file?
	#
	
	if solution.kind=='library':
		if solution.platform=='ios':
			libextension = 'ios.a'
		else:
			libextension = 'osx.a'
		outputfilereference = xcodeprojectfile.addfilereference('lib' + solution.projectname + idecode + libextension,core.FileTypes.library)
	else:
		if solution.kind=='game':
			outputfilereference = xcodeprojectfile.addfilereference(solution.projectname + '.app',core.FileTypes.exe)
		else:
			outputfilereference = xcodeprojectfile.addfilereference(solution.projectname,core.FileTypes.exe)
	
	#
	# If a fat library, add references for dev and sim targets
	#

	ioslibrary = False
	if solution.platform=='ios':
		if solution.kind=='library':
			ioslibrary = True
	
	if ioslibrary == True:
		devfilereference = xcodeprojectfile.addfilereference('lib' + solution.projectname + idecode + 'dev.a',core.FileTypes.library)
		simfilereference = xcodeprojectfile.addfilereference('lib' + solution.projectname + idecode + 'sim.a',core.FileTypes.library)
		
		#
		# Two targets for "fat" libraries
		#
		
		buildphase1 = xcodeprojectfile.addsourcesbuildphase(devfilereference)
		buildphase2 = xcodeprojectfile.addsourcesbuildphase(simfilereference)
		framephase1 = xcodeprojectfile.addframeworksbuildphase(devfilereference)
		framephase2 = xcodeprojectfile.addframeworksbuildphase(simfilereference)
		
		#
		# Add source files to compile for the ARM and the Intel libs
		#
		
		for item in xcodeprojectfile.pbxfilereferences:
			if item.type==core.FileTypes.cpp or item.type==core.FileTypes.glsl:
				buildphase1.append(xcodeprojectfile.addbuildfile(item,devfilereference))
				buildphase2.append(xcodeprojectfile.addbuildfile(item,simfilereference))
			elif item.type==core.FileTypes.frameworks:
				framephase1.append(xcodeprojectfile.addbuildfile(item,devfilereference))
				framephase2.append(xcodeprojectfile.addbuildfile(item,simfilereference))

	else:
		devfilereference = None
		simfilereference = None
		buildphase1 = xcodeprojectfile.addsourcesbuildphase(outputfilereference)
		framephase1 = xcodeprojectfile.addframeworksbuildphase(outputfilereference)
		for item in xcodeprojectfile.pbxfilereferences:
			if item.type==core.FileTypes.cpp or item.type==core.FileTypes.glsl:
				buildphase1.append(xcodeprojectfile.addbuildfile(item,outputfilereference))
			elif item.type==core.FileTypes.frameworks:
				framephase1.append(xcodeprojectfile.addbuildfile(item,outputfilereference))
	
	#
	# Create the root file group and the Products group
	#
	
	groupproducts = xcodeprojectfile.addgroup('Products',None)
	
	grouproot = xcodeprojectfile.addgroup(xcodeprojectfile.projectname,None)
	grouproot.appendgroup(groupproducts)

	# No frameworks group unless one is warranted
	
	frameworksgroup = None
		
	#
	# Insert all the file references into groups
	#
	
	for item in xcodeprojectfile.pbxfilereferences:
		# Products go into a special group
		if item.type==core.FileTypes.exe:
			groupproducts.append(item)
		elif item.type==core.FileTypes.library:
			groupproducts.append(item)
		elif item.type==core.FileTypes.frameworks:
			
			# Create the group if needed
			
			if frameworksgroup==None:
				frameworksgroup = xcodeprojectfile.addgroup('Frameworks',None)
				grouproot.appendgroup(frameworksgroup)
			
			frameworksgroup.append(item)
		else:
			# Isolate the path
			index = item.filename.rfind('/')
			if index==-1:
				# Put in the root group
				grouproot.append(item)
			else:
				# Separate the path and name
				base = item.filename[index+1:]
				path = item.filename[0:index]
				#
				# See if a group already exists
				#
				found = False
				for matchgroup in xcodeprojectfile.pbxgroups:
					if matchgroup.path!=None and matchgroup.path==path:
						# Add to a pre-existing group
						matchgroup.append(item)
						found = True
						break
				if found==True:
					continue
				
				# Group not found. Iterate and create the group
				# May need multiple levels
				
				#
				# Hack to remove preceding ../ entries
				#
				
				if path.startswith('../'):
					index = 3
				elif path.startswith('../../'):
					index = 6
				else:
					index = 0
				
				notdone = True
				previousgroup = grouproot
				while notdone:
					endindex = path[index:].find('/')
					if endindex==-1:
						# Final level, create group and add reference
						matchgroup = xcodeprojectfile.addgroup(path[index:],path)
						matchgroup.append(item)
						previousgroup.appendgroup(matchgroup)
						notdone = False
					else:
						#
						# See if a group already exists
						#
						temppath = path[0:index+endindex]
						found = False
						for matchgroup in xcodeprojectfile.pbxgroups:
							if matchgroup.path==None:
								continue
							if matchgroup.path==temppath:
								found = True
								break
						
						if found!=True:
							matchgroup = xcodeprojectfile.addgroup(path[index:index+endindex],temppath)
							previousgroup.appendgroup(matchgroup)
						previousgroup = matchgroup
						index = index+endindex+1
		
	#
	# Create the config list for the root project
	#
	
	configlistref = xcodeprojectfile.addxcconfigurationlist('PBXProject',xcodeprojectfile.projectnamecode)
	for item in solution.configurations:
		configlistref.configurations.append(xcodeprojectfile.addxcbuildconfigurationlist(item,configfilereference,configlistref,None,False))
	rootproject.configlistref = configlistref
	rootproject.rootgroup = grouproot

	#
	# Create the PBXNativeTarget config chunks
	#
	
	sdkroot = None
	if solution.platform=='ios':
		sdkroot = 'iphoneos'

	if solution.kind=='library':
		outputtype = 'com.apple.product-type.library.static'
	elif solution.kind=='screensaver':
		outputtype = 'com.apple.product-type.bundle'
	elif solution.kind=='game':
		outputtype = 'com.apple.product-type.application'
	else:
		outputtype = 'com.apple.product-type.tool'
	
	#
	# For a normal project, attach the config to a native target and we're done
	#
	
	if ioslibrary==False:
		configlistref = xcodeprojectfile.addxcconfigurationlist('PBXNativeTarget',xcodeprojectfile.projectname)
		install = False
		if solution.kind=='game':
			install = True
		for item in solution.configurations:
			configlistref.configurations.append(xcodeprojectfile.addxcbuildconfigurationlist(item,None,configlistref,sdkroot,install))
		if solution.kind=='library':
			finalname = xcodeprojectfile.projectnamecode
		else:
			finalname = xcodeprojectfile.projectname
		nativetarget1 = xcodeprojectfile.addnativeproject(finalname,outputfilereference,xcodeprojectfile.projectname,outputtype)
		nativetarget1.configlistref = configlistref
		rootproject.append(nativetarget1)
		nativetarget1.append(buildphase1.uuid,'Sources')
		nativetarget1.append(framephase1.uuid,'Frameworks')

	#
	# For fat binary iOS projects, it's a lot messier
	#
	
	else:
		targetname = xcodeprojectfile.projectnamecode
		configlistref = xcodeprojectfile.addxcconfigurationlist('PBXNativeTarget',targetname)
		for item in solution.configurations:
			configlistref.configurations.append(xcodeprojectfile.addxcbuildconfigurationlist(item,None,configlistref,None,False))
		nativetarget1 = xcodeprojectfile.addnativeproject(targetname,outputfilereference,xcodeprojectfile.projectname,outputtype)
		nativetarget1.configlistref = configlistref
		rootproject.append(nativetarget1)

		targetname = solution.projectname + idecode + 'dev'
		configlistref = xcodeprojectfile.addxcconfigurationlist('PBXNativeTarget',targetname)
		for item in solution.configurations:
			configlistref.configurations.append(xcodeprojectfile.addxcbuildconfigurationlist(item,None,configlistref,'iphoneos',False))
		nativeprojectdev = xcodeprojectfile.addnativeproject(targetname,devfilereference,xcodeprojectfile.projectname,outputtype)
		nativeprojectdev.configlistref = configlistref
		rootproject.append(nativeprojectdev)
	
		nativeprojectdev.append(buildphase1.uuid,'Sources')
		nativeprojectdev.append(framephase1.uuid,'Frameworks')
		devcontainer = xcodeprojectfile.addcontaineritemproxy(nativeprojectdev,xcodeprojectfile.uuid)

		targetname = solution.projectname + idecode + 'sim'
		configlistref = xcodeprojectfile.addxcconfigurationlist('PBXNativeTarget',targetname)
		for item in solution.configurations:
			configlistref.configurations.append(xcodeprojectfile.addxcbuildconfigurationlist(item,None,configlistref,'iphonesimulator',False))
		nativeprojectsim = xcodeprojectfile.addnativeproject(targetname,simfilereference,xcodeprojectfile.projectname,outputtype)
		nativeprojectsim.configlistref = configlistref
		rootproject.append(nativeprojectsim)
	
		nativeprojectsim.append(buildphase2.uuid,'Sources')
		nativeprojectsim.append(framephase2.uuid,'Frameworks')
		simcontainer = xcodeprojectfile.addcontaineritemproxy(nativeprojectsim,xcodeprojectfile.uuid)

		nativetarget1.depend(xcodeprojectfile.adddependency(devcontainer,nativeprojectdev).uuid,'PBXTargetDependency')
		nativetarget1.depend(xcodeprojectfile.adddependency(simcontainer,nativeprojectsim).uuid,'PBXTargetDependency')

	#
	# Add in a shell script build phase if needed
	#
	
	#
	# Is this an application?
	#
	
	if solution.platform=='macosx':
		if solution.kind=='tool':
			input = ['${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}']
			output = '${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
			command = 'if [ ! -d ${SRCROOT}/bin ]; then mkdir ${SRCROOT}/bin; fi\\n' \
				'${CP} ${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME} ${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
			shellbuildphase = xcodeprojectfile.addshellscriptbuildphase(input,output,command)
			nativetarget1.append(shellbuildphase.uuid,'ShellScript')
		elif solution.kind=='game':
			input = ['${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}.app/Contents/MacOS/${EXECUTABLE_NAME}']
			output = '${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}.app/Contents/MacOS/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
			command = 'if [ ! -d ${SRCROOT}/bin ]; then mkdir ${SRCROOT}/bin; fi\\n' \
				'${CP} -r ${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}.app/ ${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}.app/\\n' \
				'mv ${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}.app/Contents/MacOS/${EXECUTABLE_NAME} ${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}.app/Contents/MacOS/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
			shellbuildphase = xcodeprojectfile.addshellscriptbuildphase(input,output,command)
			nativetarget1.append(shellbuildphase.uuid,'ShellScript')

	#
	# Is there a final folder?
	#
	
	if solution.finalfolder!=None:
		if ioslibrary==False:
			input = ['${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}']
		else:
			input = [
				'${BUILD_ROOT}/' + solution.projectname + idecode + 'dev${SUFFIX}/lib' + solution.projectname + idecode + 'dev.a',
				'${BUILD_ROOT}/' + solution.projectname + idecode + 'sim${SUFFIX}/lib' + solution.projectname + idecode + 'sim.a'
			]
		finalfolder = solution.finalfolder.replace('(','{')
		finalfolder = finalfolder.replace(')','}')
		if ioslibrary==True:
			command = '${SDKS}/macosx/bin/p4 edit ' + finalfolder + '${FINAL_OUTPUT}\\nlipo -output ' + \
				finalfolder + '${FINAL_OUTPUT} -create ${BUILD_ROOT}/' + solution.projectname + idecode + \
				'dev${SUFFIX}/lib' + solution.projectname + idecode + 'dev.a ${BUILD_ROOT}/' + solution.projectname + idecode + 'sim${SUFFIX}/lib' + solution.projectname + idecode + 'sim.a\\n';
		elif solution.kind=='library':
			command = '${SDKS}/macosx/bin/p4 edit ' + finalfolder + '${FINAL_OUTPUT}\\n${CP} ${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME} ' + finalfolder + '${FINAL_OUTPUT}\\n'
		else:
			command = 'if [ \\"${CONFIGURATION}\\" == \\"Release\\" ]; then\\n${SDKS}/macosx/bin/p4 edit ' + finalfolder + '${FINAL_OUTPUT}\\n${CP} ${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME} ' + finalfolder + '${FINAL_OUTPUT}\\nfi\\n'
		shellbuildphase = xcodeprojectfile.addshellscriptbuildphase(input,solution.finalfolder + '${FINAL_OUTPUT}',command)
		nativetarget1.append(shellbuildphase.uuid,'ShellScript')
		
	#
	# Serialize the XCode file
	#
	
	fp = StringIO.StringIO()
	xcodeprojectfile.write(fp)
	
	#
	# Did it change?
	#
	
	if burger.comparefiletostring(projectfilename,fp):
		if solution.verbose==True:
			print projectfilename + ' was not changed'
	else:
		burger.perforceedit(projectfilename)
		fp2 = open(projectfilename,'w')
		fp2.write(fp.getvalue())
		fp2.close()
	fp.close()
	return 0
		
