#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sub file for makeprojects.
Handler for Apple Computer XCode projects
"""

# Copyright 1995-2019 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

from __future__ import absolute_import, print_function, unicode_literals
import hashlib
import os
import operator
import burger
from burger import StringIO
from makeprojects import FileTypes, ProjectTypes, \
    PlatformTypes, SourceFile

# pylint: disable=C0302

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

DEFAULT_FINAL_FOLDER = '$(BURGER_SDKS)/macosx/bin/'


IOS_MINIMUM_FRAMEWORKS = [
    'AVFoundation.framework',
    'CoreGraphics.framework',
    'CoreLocation.framework',
    'Foundation.framework',
    'QuartzCore.framework',
    'UIKit.framework'
]

MACOS_MINIMUM_FRAMEWORKS = [
    'AppKit.framework',
    'AudioToolbox.framework',
    'AudioUnit.framework',
    'Carbon.framework',
    'Cocoa.framework',
    'CoreAudio.framework',
    'IOKit.framework',
    'OpenGL.framework',
    'QuartzCore.framework',
    'SystemConfiguration.framework'
]


def calcuuid(input_str):
    """
    Given a string, create a 96 bit unique hash for XCode
    """

    temphash = hashlib.md5(
        burger.convert_to_windows_slashes(input_str).encode('utf-8')).hexdigest()

    # Take the hash string and only use the top 96 bits

    return temphash[0:24].upper()


def writelist(selfarray, filep):
    """
    Print a list of objects sorted by uuid
    """

    #
    # Only print if there's items to process
    #

    if selfarray:

        #
        # Sort by uuid
        #
        selfarray = sorted(selfarray, key=operator.attrgetter('uuid'))

        # Using the name of the class, output the array of data items
        itemname = selfarray[0].__class__.__name__
        filep.write('\n/* Begin ' + itemname + ' section */\n')
        for item in selfarray:
            item.write(filep)
        filep.write('/* End ' + itemname + ' section */\n')


class Defaults(object):
    """
    Class to hold the defaults and settings to output an XCode
    compatible project file.
    json keyword "xcode" for dictionary of overrides
    """

    #
    # Power up defaults
    #

    def __init__(self):
        self.frameworks = []
        self.configfilename = None

    def defaults(self, solution):
        """
        The solution has been set up, perform setup
        based on the type of project being created
        """
        #
        # Get the config file name and default frameworks
        #

        minimumframeworks = []

        # Handle iOS targets

        if solution.projects[0].get_attribute('platform') == PlatformTypes.ios:
            if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
                self.configfilename = 'burger.libxcoios.xcconfig'
            else:
                # Frameworks for an iOS app
                minimumframeworks.extend(IOS_MINIMUM_FRAMEWORKS)
                if solution.projects[0].get_attribute('project_type') == ProjectTypes.app:
                    self.configfilename = 'burger.gamexcoios.xcconfig'
                else:
                    self.configfilename = 'burger.toolxcoios.xcconfig'

        # Handle Mac OSX targets

        elif solution.projects[0].get_attribute('platform') == PlatformTypes.macosx:

            if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
                self.configfilename = 'burger.libxcoosx.xcconfig'
            else:
                # Frameworks for a Mac OSX app or tool
                minimumframeworks.extend(MACOS_MINIMUM_FRAMEWORKS)
                if solution.projects[0].get_attribute('project_type') == ProjectTypes.app:
                    self.configfilename = 'burger.gamexcoosx.xcconfig'
                else:
                    self.configfilename = 'burger.toolxcoosx.xcconfig'

        #
        # Add the frameworks to the user supplied list
        #

        for item in minimumframeworks:
            # Only add if not already in the list
            if item not in self.frameworks:
                self.frameworks.append(item)

    def loadjson(self, myjson):
        """
        A json file had the key "xcode" with a dictionary.
        Parse the dictionary for extra control
        """
        error = 0
        for key in myjson.keys():
            if key == 'frameworks':
                self.frameworks = burger.convert_to_array(myjson[key])
            else:
                print('Unknown keyword "' + str(key) + '" with data "' +
                      str(myjson[key]) + '" found in loadjson')
                error = 1

        return error


class PBXBuildFile(object):
    """
    Each PBXBuildFile entry
    This record instructs xcode to build this file
    """

    def __init__(self, filereference, owner):
        self.filereference = filereference
        self.uuid = calcuuid(
            'PBXBuildFile' + filereference.filename + owner.filename)

    def write(self, filep):
        """
        Write this record to output
        """
        # Is the file a framework?
        if self.filereference.type == FileTypes.frameworks:
            ref_type = 'Frameworks'
        else:
            # It's a source file
            ref_type = 'Sources'

        basename = os.path.basename(self.filereference.filename)
        filep.write('\t\t' + self.uuid + ' /* ' + basename + ' in ' + ref_type
                    + ' */ = {isa = PBXBuildFile; fileRef = ' + self.filereference.uuid
                    + ' /* ' + basename + ' */; };\n')


class PBXFileReference(object):
    """
    Each PBXFileReference entry
    Get the filename path and XCode type
    """

    def __init__(self, filename, ref_type):
        self.filename = filename
        self.uuid = calcuuid('PBXFileReference' + filename)
        self.type = ref_type

    def write(self, filep):
        """
        Write this record to output
        """

        basename = os.path.basename(self.filename)

        #
        # Based on the file type, save out an assumed default to what kind of file
        # XCode is expecting
        #

        # Start by saving the uuid and the type of record

        filep.write('\t\t' + self.uuid + ' /* ' + basename +
                    ' */ = {isa = PBXFileReference;')

        # If not binary, assume UTF-8 encoding

        if self.type != FileTypes.library and \
                self.type != FileTypes.exe and \
                self.type != FileTypes.frameworks:
            filep.write(' fileEncoding = 4;')

        # Each file type is handled differently

        if self.type == FileTypes.library:
            filep.write(' explicitFileType = archive.ar; includeInIndex = 0; '
                        'path = ' + basename + '; sourceTree = BUILT_PRODUCTS_DIR;')
        elif self.type == FileTypes.exe:
            if basename.endswith('.app'):
                filep.write(' explicitFileType = wrapper.application; '
                            'includeInIndex = 0; path = ' + basename
                            + '; sourceTree = BUILT_PRODUCTS_DIR;')
            else:
                filep.write(' explicitFileType = "compiled.mach-o.executable"; '
                            'includeInIndex = 0; path = ' + basename
                            + '; sourceTree = BUILT_PRODUCTS_DIR;')
        elif self.type == FileTypes.frameworks:
            filep.write(' lastKnownFileType = wrapper.framework; name = ' + basename
                        + '; path = System/Library/Frameworks/' + basename
                        + '; sourceTree = SDKROOT;')
        elif self.type == FileTypes.glsl:
            filep.write(' lastKnownFileType = sourcecode.glsl; name = ' + basename +
                        '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')
        elif self.type == FileTypes.xml:
            if basename.endswith('.plist'):
                filep.write(' lastKnownFileType = text.plist.xml; name = ' + basename +
                            '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')
            else:
                filep.write(' lastKnownFileType = text.xml; name = ' + basename +
                            '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')
        elif self.type == FileTypes.xcconfig:
            filep.write(' lastKnownFileType = text.xcconfig; name = ' + basename +
                        '; path = xcode/' + basename + '; sourceTree = BURGER_SDKS;')
        elif self.type == FileTypes.cpp:
            filep.write(' lastKnownFileType = sourcecode.cpp.cpp; name = ' +
                        basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')
        else:
            filep.write(' lastKnownFileType = sourcecode.c.h; name = ' + basename +
                        '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;')

        # Close out the line

        filep.write(' };\n')


class PBXBuildRule(object):
    """
    Each PBXBuildFile entry
    """

    def __init__(self, owner):
        self.uuid = calcuuid('PBXBuildRule' + owner.projectnamecode)

    def write(self, filep):
        """
        Write this record to output
        """

        filep.write('\t\t' + self.uuid + ' /* PBXBuildRule */ = {\n')
        filep.write('\t\t\tisa = PBXBuildRule;\n')
        filep.write('\t\t\tcompilerSpec = com.apple.compilers.proxy.script;\n')
        filep.write('\t\t\tfilePatterns = "*.glsl";\n')
        filep.write('\t\t\tfileType = pattern.proxy;\n')
        filep.write('\t\t\tisEditable = 1;\n')
        filep.write('\t\t\toutputFiles = (\n')
        filep.write('\t\t\t\t"${INPUT_FILE_DIR}/${INPUT_FILE_BASE}.h",\n')
        filep.write('\t\t\t);\n')
        filep.write('\t\t\tscript = "${BURGER_SDKS}/macosx/bin/stripcomments '
                    '${INPUT_FILE_PATH}'
                    ' -c -l g_${INPUT_FILE_BASE} ${INPUT_FILE_DIR}/${INPUT_FILE_BASE}.h";\n')
        filep.write('\t\t};\n')


class PBXGroup(object):
    """
    Each PBXGroup entry
    """

    def __init__(self, name, path):
        self.name = name
        self.path = path
        if path is None:
            path = '<group>'
        self.uuid = calcuuid('PBXGroup' + name + path)
        self.filelist = []

    def write(self, filep):
        """
        Write this record to output
        """

        self.filelist = sorted(self.filelist, key=operator.itemgetter(1))
        filep.write('\t\t' + self.uuid + ' /* ' + self.name + ' */ = {\n')
        filep.write('\t\t\tisa = PBXGroup;\n')
        filep.write('\t\t\tchildren = (\n')
        # Output groups first
        for item in self.filelist:
            if item[2] is True:
                filep.write('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,\n')
        # Output files last
        for item in self.filelist:
            if item[2] is not True:
                filep.write('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,\n')
        filep.write('\t\t\t);\n')
        if self.path is not None:
            if self.name != self.path:
                filep.write('\t\t\tname = ' + self.name + ';\n')
            filep.write('\t\t\tpath = ' + self.path + ';\n')
            filep.write('\t\t\tsourceTree = SOURCE_ROOT;\n')
        else:
            filep.write('\t\t\tname = ' + self.name + ';\n')
            filep.write('\t\t\tsourceTree = "<group>";\n')
        filep.write('\t\t};\n')

    def append(self, item):
        """
        Append a file uuid and name to the end of the list
        """
        self.filelist.append(
            [item.uuid, os.path.basename(item.filename), False])

    def appendgroup(self, item):
        """
        Append a group to the end of the list
        """
        self.filelist.append([item.uuid, item.name, True])


class PBXSourcesBuildPhase(object):
    """
    Each PBXSourcesBuildPhase entry
    """

    def __init__(self, owner):
        self.owner = owner
        self.uuid = calcuuid('PBXSourcesBuildPhase' + owner.filename)
        self.buildfirstlist = []
        self.buildlist = []

    def write(self, filep):
        """
        Write this record to output
        """

        self.buildfirstlist = sorted(
            self.buildfirstlist, key=operator.itemgetter(1))
        self.buildlist = sorted(
            self.buildlist, key=operator.itemgetter(1))
        filep.write('\t\t' + self.uuid + ' /* Sources */ = {\n')
        filep.write('\t\t\tisa = PBXSourcesBuildPhase;\n')
        filep.write('\t\t\tbuildActionMask = 2147483647;\n')
        filep.write('\t\t\tfiles = (\n')
        for item in self.buildfirstlist:
            filep.write('\t\t\t\t' + item[0].uuid +
                        ' /* ' + item[1] + ' in Sources */,\n')
        for item in self.buildlist:
            filep.write('\t\t\t\t' + item[0].uuid +
                        ' /* ' + item[1] + ' in Sources */,\n')
        filep.write('\t\t\t);\n')
        filep.write('\t\t\trunOnlyForDeploymentPostprocessing = 0;\n')
        filep.write('\t\t};\n')

    def append(self, item):
        """
        Append a file uuid and name to the end of the list
        """

        if item.filereference.type == FileTypes.glsl:
            self.buildfirstlist.append(
                [item, os.path.basename(item.filereference.filename)])
        else:
            self.buildlist.append(
                [item, os.path.basename(item.filereference.filename)])


class PBXFrameworksBuildPhase(object):
    """
    Each PBXFrameworksBuildPhase entry
    """

    def __init__(self, owner):
        self.owner = owner
        self.uuid = calcuuid('PBXFrameworksBuildPhase' + owner.filename)
        self.buildlist = []

    def write(self, filep):
        """
        Write this record to output
        """

        self.buildlist = sorted(
            self.buildlist, key=operator.itemgetter(1))
        filep.write('\t\t' + self.uuid + ' /* Frameworks */ = {\n')
        filep.write('\t\t\tisa = PBXFrameworksBuildPhase;\n')
        filep.write('\t\t\tbuildActionMask = 2147483647;\n')
        filep.write('\t\t\tfiles = (\n')
        for item in self.buildlist:
            filep.write('\t\t\t\t' + item[0] + ' /* ' +
                        item[1] + ' in Frameworks */,\n')
        filep.write('\t\t\t);\n')
        filep.write('\t\t\trunOnlyForDeploymentPostprocessing = 0;\n')
        filep.write('\t\t};\n')

    def append(self, item):
        """
        Append a file uuid and name to the end of the list
        """
        self.buildlist.append(
            [item.uuid, os.path.basename(item.filereference.filename)])


class PBXShellScriptBuildPhase(object):
    """
    Each PBXShellScriptBuildPhase entry
    """

    def __init__(self, input_data, output, command):
        self.input = input_data
        self.output = output
        self.command = command
        self.uuid = calcuuid('PBXShellScriptBuildPhase' +
                             ''.join(input_data) + output + command)

    def write(self, filep):
        """
        Write this record to output
        """

        filep.write('\t\t' + self.uuid + ' /* ShellScript */ = {\n')
        filep.write('\t\t\tisa = PBXShellScriptBuildPhase;\n')
        filep.write('\t\t\tbuildActionMask = 2147483647;\n')
        filep.write('\t\t\tfiles = (\n')
        filep.write('\t\t\t);\n')
        if self.input:
            filep.write('\t\t\tinputPaths = (\n')
            for item in self.input:
                filep.write('\t\t\t\t"' + item + '",\n')
            filep.write('\t\t\t);\n')
        filep.write('\t\t\toutputPaths = (\n')
        filep.write('\t\t\t\t"' + self.output + '",\n')
        filep.write('\t\t\t);\n')
        filep.write('\t\t\trunOnlyForDeploymentPostprocessing = 0;\n')
        filep.write('\t\t\tshellPath = /bin/sh;\n')
        filep.write('\t\t\tshellScript = "' + self.command + '\\n";\n')
        filep.write('\t\t\tshowEnvVarsInLog = 0;\n')
        filep.write('\t\t};\n')


class PBXProject(object):
    """
    Each PBXProject entry
    """

    def __init__(self, project):
        self.project = project
        self.uuid = project.uuid
        self.configlistref = None
        self.targetlist = []
        self.rootgroup = None

    def write(self, filep):
        """
        Write this record to output
        """

        filep.write('\t\t' + self.uuid + ' /* Project object */ = {\n')
        filep.write('\t\t\tisa = PBXProject;\n')
        filep.write('\t\t\tattributes = {\n')
        filep.write('\t\t\t\tBuildIndependentTargetsInParallel = YES;\n')
        if self.project.idecode == 'xc5':
            filep.write('\t\t\t\tLastUpgradeCheck = 0510;\n')
        filep.write('\t\t\t};\n')
        if self.configlistref is not None:
            filep.write('\t\t\tbuildConfigurationList = ' + self.configlistref.uuid
                        + ' /* Build configuration list for PBXProject "'
                        + self.project.projectnamecode + '" */;\n')

        if self.project.idecode != 'xc3':
            filep.write('\t\t\tcompatibilityVersion = "Xcode 3.2";\n')
            filep.write('\t\t\tdevelopmentRegion = English;\n')
        else:
            filep.write('\t\t\tcompatibilityVersion = "Xcode 3.1";\n')

        filep.write('\t\t\thasScannedForEncodings = 1;\n')
        filep.write('\t\t\tknownRegions = (\n')
        filep.write('\t\t\t\ten,\n')
        filep.write('\t\t\t);\n')
        if self.rootgroup is not None:
            filep.write('\t\t\tmainGroup = ' + self.rootgroup.uuid +
                        ' /* ' + self.rootgroup.name + ' */;\n')
        filep.write('\t\t\tprojectDirPath = "";\n')
        filep.write('\t\t\tprojectRoot = "";\n')
        filep.write('\t\t\ttargets = (\n')
        if self.targetlist:
            for item in self.targetlist:
                filep.write('\t\t\t\t' + item.uuid +
                            ' /* ' + item.name + ' */,\n')
        filep.write('\t\t\t);\n')
        filep.write('\t\t};\n')

    def append(self, item):
        """
        Append a PBXNative target
        """
        self.targetlist.append(item)


class PBXNativeTarget(object):
    """
    Each PBXNative entry
    """

    def __init__(self, parent, name, productreference, productname, producttype):
        self.parent = parent
        self.name = name
        self.productreference = productreference
        self.productname = productname
        self.producttype = producttype
        self.uuid = calcuuid('PBXNativeTarget' + name)
        self.configlistref = None
        self.phases = []
        self.depends = []

    def write(self, filep):
        """
        Write this record to output
        """

        filep.write('\t\t' + self.uuid + ' /* ' + self.name + ' */ = {\n')
        filep.write('\t\t\tisa = PBXNativeTarget;\n')
        if self.configlistref is not None:
            filep.write('\t\t\tbuildConfigurationList = ' + self.configlistref.uuid
                        + ' /* Build configuration list for PBXNativeTarget "'
                        + self.name + '" */;\n')
        filep.write('\t\t\tbuildPhases = (\n')
        for item in self.phases:
            filep.write('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,\n')
        filep.write('\t\t\t);\n')
        filep.write('\t\t\tbuildRules = (\n')
        for item in self.parent.pbxbuildrules:
            filep.write('\t\t\t\t' + item.uuid + ' /* PBXBuildRule */,\n')
        filep.write('\t\t\t);\n')
        filep.write('\t\t\tdependencies = (\n')
        for item in self.depends:
            filep.write('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,\n')
        filep.write('\t\t\t);\n')
        filep.write('\t\t\tname = ' + self.name + ';\n')
        filep.write('\t\t\tproductName = ' + self.productname + ';\n')
        filep.write('\t\t\tproductReference = ' + self.productreference.uuid +
                    ' /* ' + self.productreference.filename + ' */;\n')
        filep.write('\t\t\tproductType = "' + self.producttype + '";\n')
        filep.write('\t\t};\n')

    def append(self, uuid, name):
        """
        Append a Buildphase target
        """
        self.phases.append([uuid, name])

    def depend(self, uuid, name):
        """
        Append a dependency
        """
        self.depends.append([uuid, name])


class XCBuildConfiguration(object):
    """
    Each XCBuildConfiguration entry
    """

    def __init__(self, configname, configfilereference, owner, sdkroot,
                 installpath):
        self.configname = configname
        self.configfilereference = configfilereference
        self.sdkroot = sdkroot
        self.installpath = installpath
        self.uuid = calcuuid('XCBuildConfiguration' +
                             owner.pbxtype + owner.targetname + str(configname))

    def write(self, filep):
        """
        Write this record to output
        """

        filep.write('\t\t' + self.uuid + ' /* ' +
                    str(self.configname) + ' */ = {\n')
        filep.write('\t\t\tisa = XCBuildConfiguration;\n')
        if self.configfilereference is not None:
            filep.write('\t\t\tbaseConfigurationReference = '
                        + self.configfilereference.uuid
                        + ' /* ' + os.path.basename(self.configfilereference.filename) + ' */;\n')
        filep.write('\t\t\tbuildSettings = {\n')
        if self.sdkroot is not None:
            filep.write('\t\t\t\tSDKROOT = ' + self.sdkroot + ';\n')
        if self.installpath is True:
            filep.write('\t\t\t\tINSTALL_PATH = "$(HOME)/Applications";\n')
        filep.write('\t\t\t};\n')
        filep.write('\t\t\tname = ' + str(self.configname) + ';\n')
        filep.write('\t\t};\n')


class XCConfigurationList(object):
    """
    Each XCConfigurationList entry
    """

    def __init__(self, pbxtype, targetname):
        self.pbxtype = pbxtype
        self.targetname = targetname
        self.configurations = []
        self.uuid = calcuuid('XCConfigurationList' + pbxtype + targetname)

    def write(self, filep):
        """
        Write this record to output
        """

        filep.write('\t\t' + self.uuid + ' /* Build configuration list for ' +
                    self.pbxtype + ' "' + self.targetname + '" */ = {\n')
        filep.write('\t\t\tisa = XCConfigurationList;\n')
        filep.write('\t\t\tbuildConfigurations = (\n')
        default = None
        for item in self.configurations:
            if item.configname == 'Release':
                default = 'Release'
            elif default is None:
                default = str(item.configname)
            filep.write('\t\t\t\t' + item.uuid + ' /* ' +
                        str(item.configname) + ' */,\n')
        if default is None:
            default = 'Release'
        filep.write('\t\t\t);\n')
        filep.write('\t\t\tdefaultConfigurationIsVisible = 0;\n')
        filep.write('\t\t\tdefaultConfigurationName = ' + default + ';\n')
        filep.write('\t\t};\n')


class PBXContainerItemProxy(object):
    """
    Each PBXContainerItemProxy entry
    """

    def __init__(self, nativetarget, rootuuid):
        self.nativetarget = nativetarget
        self.rootuuid = rootuuid
        self.uuid = calcuuid('PBXContainerItemProxy' + nativetarget.name)

    def write(self, filep):
        """
        Write this record to output
        """

        filep.write('\t\t' + self.uuid + ' /* PBXContainerItemProxy */ = {\n')
        filep.write('\t\t\tisa = PBXContainerItemProxy;\n')
        filep.write('\t\t\tcontainerPortal = ' +
                    self.rootuuid + ' /* Project object */;\n')
        filep.write('\t\t\tproxyType = 1;\n')
        filep.write('\t\t\tremoteGlobalIDString = ' +
                    self.nativetarget.uuid + ';\n')
        filep.write('\t\t\tremoteInfo = "' + self.nativetarget.name + '";\n')
        filep.write('\t\t};\n')


class PBXTargetDependency(object):
    """
    Each PBXTargetDependency entry
    """

    def __init__(self, proxy, nativetarget):
        self.proxy = proxy
        self.nativetarget = nativetarget
        self.uuid = calcuuid('PBXTargetDependency' +
                             proxy.nativetarget.name + nativetarget.name)

    def write(self, filep):
        """
        Write this record to output
        """

        filep.write('\t\t' + self.uuid + ' /* PBXTargetDependency */ = {\n')
        filep.write('\t\t\tisa = PBXTargetDependency;\n')
        filep.write('\t\t\ttarget = ' + self.nativetarget.uuid +
                    ' /* ' + self.nativetarget.name + ' */;\n')
        filep.write('\t\t\ttargetProxy = ' + self.proxy.uuid +
                    ' /* PBXContainerItemProxy */;\n')
        filep.write('\t\t};\n')


class Project(object):
    """
    Root object for an XCode IDE project file
    Created with the name of the project, the IDE code (xc3, xc5)
    the platform code (ios, osx)
    """

    def __init__(self, projectname, idecode, platformcode):
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

    def addfilereference(self, filename, ref_type):
        """
        Add a new file reference
        """

        entry = PBXFileReference(filename, ref_type)
        self.pbxfilereferences.append(entry)
        return entry

    def addbuildfile(self, filereference, owner):
        """
        Add a new file reference
        """

        entry = PBXBuildFile(filereference, owner)
        self.pbxbuildfiles.append(entry)
        return entry

    def addgroup(self, name, path):
        """
        Add a new file group
        """
        entry = PBXGroup(name, path)
        self.pbxgroups.append(entry)
        return entry

    def addsourcesbuildphase(self, owner):
        """
        Add a new source build phase list
        """

        entry = PBXSourcesBuildPhase(owner)
        self.sourcesbuildphases.append(entry)
        return entry

    def addnativeproject(self, name, productreference, productname, producttype):
        """
        Add a new native target list
        """

        entry = PBXNativeTarget(
            self, name, productreference, productname, producttype)
        self.pbxnativetargets.append(entry)
        return entry

    def addframeworksbuildphase(self, owner):
        """
        Add a new frameworks build phase list
        """
        entry = PBXFrameworksBuildPhase(owner)
        self.framesworksbuildphases.append(entry)
        return entry

    def addshellscriptbuildphase(self, input_data, output, command):
        """
        Add a new configuration list
        """
        entry = PBXShellScriptBuildPhase(input_data, output, command)
        self.shellscriptbuildphases.append(entry)
        return entry

    def addxcbuildconfigurationlist(self, configname, configfilereference,
                                    owner, sdkroot, installpath):
        """
        Add a new configuration list
        """
        entry = XCBuildConfiguration(
            configname, configfilereference, owner, sdkroot, installpath)
        self.xcbuildconfigurations.append(entry)
        return entry

    def addxcconfigurationlist(self, pbxtype, targetname):
        """
        Add a new configuration list
        """
        entry = XCConfigurationList(pbxtype, targetname)
        self.xcconfigurationlists.append(entry)
        return entry

    def addcontaineritemproxy(self, nativetarget, rootuuid):
        """
        Add a new container item proxy
        """
        entry = PBXContainerItemProxy(nativetarget, rootuuid)
        self.containeritemproxies.append(entry)
        return entry

    def adddependency(self, proxy, nativetarget):
        """
        Add a new dependency
        """
        entry = PBXTargetDependency(proxy, nativetarget)
        self.targetdependencies.append(entry)
        return entry

    def write(self, filep):
        """
        Dump out the entire file
        """

        #
        # Write the XCode header
        #

        filep.write('// !$*UTF8*$!\n')
        filep.write('{\n')

        #
        # Always present in an XCode file
        #

        filep.write('\tarchiveVersion = 1;\n')
        filep.write('\tclasses = {\n')
        filep.write('\t};\n')

        #
        # 42 = XCode 2.4
        # 44 = XCode 3.0
        # 45 = XCode 3.1
        # 46 = XCode 3.2
        #

        if self.idecode == 'xc3':
            filep.write('\tobjectVersion = 45;\n')
        else:
            filep.write('\tobjectVersion = 46;\n')
        filep.write('\tobjects = {\n')

        #
        # Write out each of the chunks
        #

        writelist(self.pbxbuildfiles, filep)
        writelist(self.pbxbuildrules, filep)
        writelist(self.containeritemproxies, filep)
        writelist(self.pbxfilereferences, filep)
        writelist(self.framesworksbuildphases, filep)
        writelist(self.pbxgroups, filep)
        writelist(self.pbxnativetargets, filep)
        writelist(self.pbxprojects, filep)
        writelist(self.shellscriptbuildphases, filep)
        writelist(self.sourcesbuildphases, filep)
        writelist(self.targetdependencies, filep)
        writelist(self.xcbuildconfigurations, filep)
        writelist(self.xcconfigurationlists, filep)

        #
        # Close up the project file
        #

        filep.write('\t};\n')
        filep.write('\trootObject = ' + self.uuid + ' /* Project object */;\n')
        filep.write('}\n')


#
# Xcode 3, 4 and 5 support
#

def generate(solution):
    """
    Create a project file for XCode file format version 3.1
    """

    #
    # Find the files to put into the project
    #

    codefiles, _ = solution.getfilelist(
        [FileTypes.icns, FileTypes.h, FileTypes.cpp, FileTypes.frameworks,
         FileTypes.exe, FileTypes.library, FileTypes.glsl])

    #
    # Configure the xcode writer to the type
    # of solution requested
    #

    solution.xcode.defaults(solution)

    #
    # Determine the ide and target type for the final file name
    #

    idecode = solution.ide.get_short_code()
    platformcode = solution.projects[0].get_attribute('platform').get_short_code()
    xcodeprojectfile = Project(solution.attributes['name'], idecode, platformcode)
    rootproject = xcodeprojectfile.pbxprojects[0]

    #
    # Ensure the slashes are correct for XCode
    #

    for item in codefiles:
        item.filename = burger.convert_to_linux_slashes(item.filename)

    #
    # Let's create the solution file!
    #

    solutionfoldername = os.path.join(
        solution.attributes['working_directory'], xcodeprojectfile.projectnamecode + '.xcodeproj')
    burger.create_folder_if_needed(solutionfoldername)
    projectfilename = os.path.join(solutionfoldername, 'project.pbxproj')

    #
    # Add the configuration file reference (or not)
    #

    if solution.xcode.configfilename is not None:
        configfilereference = xcodeprojectfile.addfilereference(
            solution.xcode.configfilename, FileTypes.xcconfig)
    else:
        configfilereference = None

    #
    # Add the frameworks to the build list
    #

    for framework in solution.xcode.frameworks:
        item = SourceFile(framework, '', FileTypes.frameworks)
        codefiles.append(item)

    #
    # Insert all of the files found into the file references
    #

    for item in codefiles:
        # Remove unsupported file types
        if item.type != FileTypes.rc and \
                item.type != FileTypes.r and \
                item.type != FileTypes.hlsl:
            xcodeprojectfile.addfilereference(item.filename, item.type)

    #
    # What's the final output file?
    #

    if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
        if solution.projects[0].get_attribute('platform') == PlatformTypes.ios:
            libextension = 'ios.a'
        else:
            libextension = 'osx.a'
        outputfilereference = xcodeprojectfile.addfilereference(
            'lib' + solution.attributes['name'] + idecode + libextension, FileTypes.library)
    else:
        if solution.projects[0].get_attribute('project_type') == ProjectTypes.app:
            outputfilereference = xcodeprojectfile.addfilereference(
                solution.attributes['name'] + '.app', FileTypes.exe)
        else:
            outputfilereference = xcodeprojectfile.addfilereference(
                solution.attributes['name'], FileTypes.exe)

    #
    # If a fat library, add references for dev and sim targets
    #

    ioslibrary = False
    if solution.projects[0].get_attribute('platform') == PlatformTypes.ios:
        if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
            ioslibrary = True

    if ioslibrary is True:
        devfilereference = xcodeprojectfile.addfilereference(
            'lib' + solution.attributes['name'] + idecode + 'dev.a', FileTypes.library)
        simfilereference = xcodeprojectfile.addfilereference(
            'lib' + solution.attributes['name'] + idecode + 'sim.a', FileTypes.library)

        #
        # Two targets for "fat" libraries
        #

        buildphase1 = xcodeprojectfile.addsourcesbuildphase(devfilereference)
        buildphase2 = xcodeprojectfile.addsourcesbuildphase(simfilereference)
        framephase1 = xcodeprojectfile.addframeworksbuildphase(
            devfilereference)
        framephase2 = xcodeprojectfile.addframeworksbuildphase(
            simfilereference)

        #
        # Add source files to compile for the ARM and the Intel libs
        #

        for item in xcodeprojectfile.pbxfilereferences:
            if item.type == FileTypes.cpp or item.type == FileTypes.glsl:
                buildphase1.append(
                    xcodeprojectfile.addbuildfile(item, devfilereference))
                buildphase2.append(
                    xcodeprojectfile.addbuildfile(item, simfilereference))
            elif item.type == FileTypes.frameworks:
                framephase1.append(
                    xcodeprojectfile.addbuildfile(item, devfilereference))
                framephase2.append(
                    xcodeprojectfile.addbuildfile(item, simfilereference))

    else:
        devfilereference = None
        simfilereference = None
        buildphase1 = xcodeprojectfile.addsourcesbuildphase(
            outputfilereference)
        framephase1 = xcodeprojectfile.addframeworksbuildphase(
            outputfilereference)
        for item in xcodeprojectfile.pbxfilereferences:
            if item.type == FileTypes.cpp or item.type == FileTypes.glsl:
                buildphase1.append(xcodeprojectfile.addbuildfile(
                    item, outputfilereference))
            elif item.type == FileTypes.frameworks:
                framephase1.append(xcodeprojectfile.addbuildfile(
                    item, outputfilereference))

    #
    # Create the root file group and the Products group
    #

    groupproducts = xcodeprojectfile.addgroup('Products', None)

    grouproot = xcodeprojectfile.addgroup(xcodeprojectfile.projectname, None)
    grouproot.appendgroup(groupproducts)

    # No frameworks group unless one is warranted

    frameworksgroup = None

    #
    # Insert all the file references into groups
    #

    for item in xcodeprojectfile.pbxfilereferences:
        # Products go into a special group
        if item.type == FileTypes.exe:
            groupproducts.append(item)
        elif item.type == FileTypes.library:
            groupproducts.append(item)
        elif item.type == FileTypes.frameworks:

            # Create the group if needed

            if frameworksgroup is None:
                frameworksgroup = xcodeprojectfile.addgroup('Frameworks', None)
                grouproot.appendgroup(frameworksgroup)

            frameworksgroup.append(item)
        else:
            # Isolate the path
            index = item.filename.rfind('/')
            if index == -1:
                # Put in the root group
                grouproot.append(item)
            else:
                # Separate the path and name
                # base = item.filename[index+1:]
                path = item.filename[0:index]
                #
                # See if a group already exists
                #
                found = False
                for matchgroup in xcodeprojectfile.pbxgroups:
                    if matchgroup.path is not None and matchgroup.path == path:
                        # Add to a pre-existing group
                        matchgroup.append(item)
                        found = True
                        break
                if found is True:
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
                    if endindex == -1:
                        # Final level, create group and add reference
                        matchgroup = xcodeprojectfile.addgroup(
                            path[index:], path)
                        matchgroup.append(item)
                        previousgroup.appendgroup(matchgroup)
                        notdone = False
                    else:
                        #
                        # See if a group already exists
                        #
                        temppath = path[0:index + endindex]
                        found = False
                        for matchgroup in xcodeprojectfile.pbxgroups:
                            if matchgroup.path is None:
                                continue
                            if matchgroup.path == temppath:
                                found = True
                                break

                        if found is not True:
                            matchgroup = xcodeprojectfile.addgroup(
                                path[index:index + endindex], temppath)
                            previousgroup.appendgroup(matchgroup)
                        previousgroup = matchgroup
                        index = index + endindex + 1

    #
    # Create the config list for the root project
    #

    configlistref = xcodeprojectfile.addxcconfigurationlist(
        'PBXProject', xcodeprojectfile.projectnamecode)
    for item in solution.projects[0].configurations:
        configlistref.configurations.append(
            xcodeprojectfile.addxcbuildconfigurationlist(
                item.attributes['name'], configfilereference, configlistref, None, False))
    rootproject.configlistref = configlistref
    rootproject.rootgroup = grouproot

    #
    # Create the PBXNativeTarget config chunks
    #

    sdkroot = None
    if solution.projects[0].get_attribute('platform') == PlatformTypes.ios:
        sdkroot = 'iphoneos'

    if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
        outputtype = 'com.apple.product-type.library.static'
    elif solution.projects[0].get_attribute('project_type') == ProjectTypes.screensaver:
        outputtype = 'com.apple.product-type.bundle'
    elif solution.projects[0].get_attribute('project_type') == ProjectTypes.app:
        outputtype = 'com.apple.product-type.application'
    else:
        outputtype = 'com.apple.product-type.tool'

    #
    # For a normal project, attach the config to a native target and we're done
    #

    if ioslibrary is False:
        configlistref = xcodeprojectfile.addxcconfigurationlist(
            'PBXNativeTarget', xcodeprojectfile.projectname)
        install = False
        if solution.projects[0].get_attribute('project_type') == ProjectTypes.app:
            install = True
        for item in solution.projects[0].configurations:
            configlistref.configurations.append(
                xcodeprojectfile.addxcbuildconfigurationlist(
                    item.attributes['name'], None, configlistref, sdkroot, install))
        if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
            finalname = xcodeprojectfile.projectnamecode
        else:
            finalname = xcodeprojectfile.projectname
        nativetarget1 = xcodeprojectfile.addnativeproject(
            finalname, outputfilereference, xcodeprojectfile.projectname, outputtype)
        nativetarget1.configlistref = configlistref
        rootproject.append(nativetarget1)
        nativetarget1.append(buildphase1.uuid, 'Sources')
        nativetarget1.append(framephase1.uuid, 'Frameworks')

    #
    # For fat binary iOS projects, it's a lot messier
    #

    else:
        targetname = xcodeprojectfile.projectnamecode
        configlistref = xcodeprojectfile.addxcconfigurationlist(
            'PBXNativeTarget', targetname)
        for item in solution.projects[0].configurations:
            configlistref.configurations.append(
                xcodeprojectfile.addxcbuildconfigurationlist(
                    item.attributes['name'], None, configlistref, None, False))
        nativetarget1 = xcodeprojectfile.addnativeproject(
            targetname, outputfilereference, xcodeprojectfile.projectname, outputtype)
        nativetarget1.configlistref = configlistref
        rootproject.append(nativetarget1)

        targetname = solution.attributes['name'] + idecode + 'dev'
        configlistref = xcodeprojectfile.addxcconfigurationlist(
            'PBXNativeTarget', targetname)
        for item in solution.projects[0].configurations:
            configlistref.configurations.append(
                xcodeprojectfile.addxcbuildconfigurationlist(
                    item.attributes['name'], None, configlistref, 'iphoneos', False))
        nativeprojectdev = xcodeprojectfile.addnativeproject(
            targetname, devfilereference, xcodeprojectfile.projectname, outputtype)
        nativeprojectdev.configlistref = configlistref
        rootproject.append(nativeprojectdev)

        nativeprojectdev.append(buildphase1.uuid, 'Sources')
        nativeprojectdev.append(framephase1.uuid, 'Frameworks')
        devcontainer = xcodeprojectfile.addcontaineritemproxy(
            nativeprojectdev, xcodeprojectfile.uuid)

        targetname = solution.attributes['name'] + idecode + 'sim'
        configlistref = xcodeprojectfile.addxcconfigurationlist(
            'PBXNativeTarget', targetname)
        for item in solution.projects[0].configurations:
            configlistref.configurations.append(
                xcodeprojectfile.addxcbuildconfigurationlist(
                    item.attributes['name'], None, configlistref, 'iphonesimulator', False))
        nativeprojectsim = xcodeprojectfile.addnativeproject(
            targetname, simfilereference, xcodeprojectfile.projectname, outputtype)
        nativeprojectsim.configlistref = configlistref
        rootproject.append(nativeprojectsim)

        nativeprojectsim.append(buildphase2.uuid, 'Sources')
        nativeprojectsim.append(framephase2.uuid, 'Frameworks')
        simcontainer = xcodeprojectfile.addcontaineritemproxy(
            nativeprojectsim, xcodeprojectfile.uuid)

        nativetarget1.depend(xcodeprojectfile.adddependency(
            devcontainer, nativeprojectdev).uuid, 'PBXTargetDependency')
        nativetarget1.depend(xcodeprojectfile.adddependency(
            simcontainer, nativeprojectsim).uuid, 'PBXTargetDependency')

    #
    # Add in a shell script build phase if needed
    #

    #
    # Is this an application?
    #

    if solution.projects[0].get_attribute('platform') == PlatformTypes.macosx:
        if solution.projects[0].get_attribute('project_type') == ProjectTypes.tool:
            input_data = ['${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}']
            output = '${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
            command = 'if [ ! -d ${SRCROOT}/bin ]; then mkdir ${SRCROOT}/bin; fi\\n' \
                '${CP} ${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME} ' \
                '${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
            shellbuildphase = xcodeprojectfile.addshellscriptbuildphase(
                input_data, output, command)
            nativetarget1.append(shellbuildphase.uuid, 'ShellScript')
        elif solution.projects[0].get_attribute('project_type') == ProjectTypes.app:
            input_data = [
                '${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}.app'
                '/Contents/MacOS/${EXECUTABLE_NAME}']
            output = '${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}.app' \
                '/Contents/MacOS/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
            command = 'if [ ! -d ${SRCROOT}/bin ]; then mkdir ${SRCROOT}/bin; fi\\n' \
                '${CP} -r ${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}.app/ ' \
                '${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}.app/\\n' \
                'mv ${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}.app' \
                '/Contents/MacOS/${EXECUTABLE_NAME} ' \
                '${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}.app' \
                '/Contents/MacOS/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
            shellbuildphase = xcodeprojectfile.addshellscriptbuildphase(
                input_data, output, command)
            nativetarget1.append(shellbuildphase.uuid, 'ShellScript')

    #
    # Is there a final folder?
    #

    deploy_folder = None
    for configuration in solution.projects[0].configurations:
        if configuration.attributes.get('deploy_folder'):
            deploy_folder = configuration.attributes.get('deploy_folder')

    if deploy_folder is not None:
        if ioslibrary is False:
            input_data = ['${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}']
        else:
            input_data = [
                '${BUILD_ROOT}/' + solution.attributes['name'] + idecode +
                'dev${SUFFIX}/lib' + solution.attributes['name'] + idecode + 'dev.a',
                '${BUILD_ROOT}/' + solution.attributes['name'] + idecode +
                'sim${SUFFIX}/lib' +
                solution.attributes['name'] + idecode + 'sim.a'
            ]
        deploy_folder = deploy_folder.replace('(', '{')
        deploy_folder = deploy_folder.replace(')', '}')
        if ioslibrary is True:
            command = 'p4 edit ' + deploy_folder + '${FINAL_OUTPUT}\\nlipo -output ' + \
                deploy_folder + '${FINAL_OUTPUT} -create ${BUILD_ROOT}/' + \
                solution.attributes['name'] + idecode + \
                'dev${SUFFIX}/lib' + solution.attributes['name'] + idecode + \
                'dev.a ${BUILD_ROOT}/' + \
                solution.attributes['name'] + idecode + \
                'sim${SUFFIX}/lib' + solution.attributes['name'] + \
                idecode + 'sim.a\\n'
        elif solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
            command = 'p4 edit ' + deploy_folder + \
                '${FINAL_OUTPUT}\\n${CP} ' \
                '${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME} ' + \
                deploy_folder + '${FINAL_OUTPUT}\\n'
        else:
            command = 'if [ \\"${CONFIGURATION}\\" == \\"Release\\" ]; ' \
                'then\\np4 edit ' + deploy_folder + \
                '${FINAL_OUTPUT}\\n${CP} ' \
                '${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME} ' + \
                deploy_folder + '${FINAL_OUTPUT}\\nfi\\n'
        shellbuildphase = xcodeprojectfile.addshellscriptbuildphase(
            input_data, deploy_folder + '${FINAL_OUTPUT}', command)
        nativetarget1.append(shellbuildphase.uuid, 'ShellScript')

    #
    # Serialize the XCode file
    #

    filep = StringIO()
    xcodeprojectfile.write(filep)

    #
    # Did it change?
    #

    if burger.compare_file_to_string(projectfilename, filep):
        if solution.get_attribute('verbose'):
            print(projectfilename + ' was not changed')
    else:
        burger.perforce_edit(projectfilename)
        filep2 = open(projectfilename, 'w')
        filep2.write(filep.getvalue())
        filep2.close()
    filep.close()
    return 0
