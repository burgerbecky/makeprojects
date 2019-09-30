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

#
## \package makeprojects.xcode
# This module contains classes needed to generate
# project files intended for use by Apple's XCode IDE
#

from __future__ import absolute_import, print_function, unicode_literals
import hashlib
import os
import operator
from burger import create_folder_if_needed, save_text_file_if_newer, \
    convert_to_windows_slashes, convert_to_linux_slashes
from .enums import FileTypes, ProjectTypes, PlatformTypes, IDETypes
from .core import SourceFile, Configuration
from .core import Project as CoreProject

# pylint: disable=C0302

TABS = '\t'

SUPPORTED_IDES = (
    IDETypes.xcode3,
    IDETypes.xcode4,
    IDETypes.xcode5,
    IDETypes.xcode6,
    IDETypes.xcode7,
    IDETypes.xcode8,
    IDETypes.xcode9,
    IDETypes.xcode10)

## Version values
# Tuple of objectVersion, , compatibilityVersion, developmentRegion
OBJECT_VERSIONS = {
    IDETypes.xcode3: ('45', None, 'Xcode 3.1', None),
    IDETypes.xcode4: ('46', '0420', 'Xcode 3.2', 'English'),
    IDETypes.xcode5: ('46', '0510', 'Xcode 3.2', 'English'),
    IDETypes.xcode6: ('47', '0600', 'Xcode 6.3', None),
    IDETypes.xcode7: ('47', '0700', 'Xcode 6.3', None),
    IDETypes.xcode8: ('48', '0800', 'Xcode 8.0', None),
    IDETypes.xcode9: ('50', '0900', 'Xcode 9.3', None),
    IDETypes.xcode10: ('51', '1030', 'Xcode 10.0', None)
}

########################################


def test(ide, platform_type):
    """ Filter for supported platforms

    Args:
        ide: IDETypes
        platform_type: PlatformTypes
    Returns:
        True if supported, False if not
    """

    # pylint: disable=unused-argument
    return platform_type in (
        PlatformTypes.macosxintel32, PlatformTypes.macosxintel64,
        PlatformTypes.macosxppc32, PlatformTypes.macosxppc64,
        PlatformTypes.ios32, PlatformTypes.ios64,
        PlatformTypes.iosemu32, PlatformTypes.iosemu64)

########################################


def calcuuid(input_str):
    """
    Given a string, create a 96 bit unique hash for XCode
    """

    temphash = hashlib.md5(convert_to_windows_slashes(
        input_str).encode('utf-8')).hexdigest()

    # Take the hash string and only use the top 96 bits

    return temphash[0:24].upper()


def writelist(selfarray, line_list):
    """
    Print a list of objects sorted by uuid
    """

    # Only print if there's items to process
    if selfarray:

        # Sort by uuid
        selfarray = sorted(selfarray, key=operator.attrgetter('uuid'))

        # Using the name of the class, output the array of data items
        itemname = selfarray[0].__class__.__name__
        line_list.append('')
        line_list.append('/* Begin ' + itemname + ' section */')
        for item in selfarray:
            item.generate(line_list)
        line_list.append('/* End ' + itemname + ' section */')


class PBXBuildFile(object):
    """
    Each PBXBuildFile entry
    This record instructs xcode to build this file
    """

    def __init__(self, filereference, owner):
        self.filereference = filereference
        self.uuid = calcuuid(
            'PBXBuildFile' + filereference.filename + owner.filename)

    def generate(self, line_list):
        """
        Write this record to output
        """
        # Is the file a framework?
        if self.filereference.type is FileTypes.frameworks:
            ref_type = 'Frameworks'
        else:
            # It's a source file
            ref_type = 'Sources'

        basename = os.path.basename(self.filereference.filename)
        line_list.append(
            '\t\t' +
            self.uuid +
            ' /* ' +
            basename +
            ' in ' +
            ref_type +
            ' */ = {isa = PBXBuildFile; fileRef = ' +
            self.filereference.uuid +
            ' /* ' +
            basename +
            ' */; };')


class PBXFileReference(object):
    """
    Each PBXFileReference entry
    Get the filename path and XCode type
    """

    def __init__(self, filename, ref_type):

        filename = convert_to_linux_slashes(filename)
        self.filename = filename
        self.uuid = calcuuid('PBXFileReference' + filename)
        self.type = ref_type

    def generate(self, line_list):
        """
        Write this record to output
        """

        basename = os.path.basename(self.filename)

        # Based on the file type, save out an assumed default to what
        # kind of file XCode is expecting

        # Start by saving the uuid and the type of record

        entry = '\t\t' + self.uuid + ' /* ' + \
            basename + ' */ = {isa = PBXFileReference;'

        # If not binary, assume UTF-8 encoding

        if self.type not in (FileTypes.library, FileTypes.exe,
                             FileTypes.frameworks):
            entry = entry + ' fileEncoding = 4;'

        # Each file type is handled differently

        if self.type is FileTypes.library:
            entry = entry + ' explicitFileType = archive.ar; includeInIndex = 0; ' + \
                'path = ' + basename + '; sourceTree = BUILT_PRODUCTS_DIR;'
        elif self.type is FileTypes.exe:
            if basename.endswith('.app'):
                entry = entry + ' explicitFileType = wrapper.application; ' + \
                    'includeInIndex = 0; path = ' + basename + \
                    '; sourceTree = BUILT_PRODUCTS_DIR;'
            else:
                entry = entry + ' explicitFileType = "compiled.mach-o.executable"; ' + \
                    'includeInIndex = 0; path = ' + basename + '; sourceTree = BUILT_PRODUCTS_DIR;'
        elif self.type is FileTypes.frameworks:
            entry = entry + ' lastKnownFileType = wrapper.framework; name = ' + basename + \
                '; path = System/Library/Frameworks/' + basename + '; sourceTree = SDKROOT;'
        elif self.type is FileTypes.glsl:
            entry = entry + ' lastKnownFileType = sourcecode.glsl; name = ' + \
                basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;'
        elif self.type is FileTypes.xml:
            if basename.endswith('.plist'):
                entry = entry + ' lastKnownFileType = text.plist.xml; name = ' + \
                    basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;'
            else:
                entry = entry + ' lastKnownFileType = text.xml; name = ' + basename + \
                    '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;'
        elif self.type is FileTypes.xcconfig:
            entry = entry + ' lastKnownFileType = text.xcconfig; name = ' + \
                basename + '; path = xcode/' + basename + '; sourceTree = BURGER_SDKS;'
        elif self.type is FileTypes.cpp:
            entry = entry + ' lastKnownFileType = sourcecode.cpp.cpp; name = ' + \
                basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;'
        else:
            entry = entry + ' lastKnownFileType = sourcecode.c.h; name = ' + \
                basename + '; path = ' + self.filename + '; sourceTree = SOURCE_ROOT;'

        # Close out the line
        line_list.append(entry + ' };')
        return 0


class PBXBuildRule(object):
    """
    Each PBXBuildFile entry
    """

    def __init__(self, owner):
        self.owner = owner
        self.uuid = calcuuid('PBXBuildRule' + owner.solution.xcode_folder_name)

    def generate(self, line_list):
        """
        Write this record to output
        """

        line_list.append('\t\t' + self.uuid + ' /* PBXBuildRule */ = {')
        line_list.append('\t\t\tisa = PBXBuildRule;')
        line_list.append(
            '\t\t\tcompilerSpec = com.apple.compilers.proxy.script;')
        line_list.append('\t\t\tfilePatterns = "*.glsl";')
        line_list.append('\t\t\tfileType = pattern.proxy;')
        line_list.append('\t\t\tisEditable = 1;')
        line_list.append('\t\t\toutputFiles = (')
        line_list.append('\t\t\t\t"${INPUT_FILE_DIR}/${INPUT_FILE_BASE}.h",')
        line_list.append('\t\t\t);')
        line_list.append(
            '\t\t\tscript = "${BURGER_SDKS}/macosx/bin/stripcomments '
            '${INPUT_FILE_PATH}'
            ' -c -l g_${INPUT_FILE_BASE} '
            '${INPUT_FILE_DIR}/${INPUT_FILE_BASE}.h";')
        line_list.append('\t\t};')


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

    def generate(self, line_list):
        """
        Write this record to output
        """

        self.filelist = sorted(self.filelist, key=operator.itemgetter(1))
        line_list.append('\t\t' + self.uuid + ' /* ' + self.name + ' */ = {')
        line_list.append('\t\t\tisa = PBXGroup;')
        line_list.append('\t\t\tchildren = (')
        # Output groups first
        for item in self.filelist:
            if item[2] is True:
                line_list.append(
                    '\t\t\t\t' +
                    item[0] +
                    ' /* ' +
                    item[1] +
                    ' */,')
        # Output files last
        for item in self.filelist:
            if item[2] is not True:
                line_list.append(
                    '\t\t\t\t' +
                    item[0] +
                    ' /* ' +
                    item[1] +
                    ' */,')
        line_list.append('\t\t\t);')
        if self.path is not None:
            if self.name != self.path:
                line_list.append('\t\t\tname = ' + self.name + ';')
            line_list.append('\t\t\tpath = ' + self.path + ';')
            line_list.append('\t\t\tsourceTree = SOURCE_ROOT;')
        else:
            line_list.append('\t\t\tname = ' + self.name + ';')
            line_list.append('\t\t\tsourceTree = "<group>";')
        line_list.append('\t\t};')
        return 0

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

    def generate(self, line_list):
        """
        Write this record to output
        """

        self.buildfirstlist = sorted(
            self.buildfirstlist, key=operator.itemgetter(1))
        self.buildlist = sorted(
            self.buildlist, key=operator.itemgetter(1))
        line_list.append('\t\t' + self.uuid + ' /* Sources */ = {')
        line_list.append('\t\t\tisa = PBXSourcesBuildPhase;')
        line_list.append('\t\t\tbuildActionMask = 2147483647;')
        line_list.append('\t\t\tfiles = (')
        for item in self.buildfirstlist:
            line_list.append('\t\t\t\t' + item[0].uuid +
                             ' /* ' + item[1] + ' in Sources */,')
        for item in self.buildlist:
            line_list.append('\t\t\t\t' + item[0].uuid +
                             ' /* ' + item[1] + ' in Sources */,')
        line_list.append('\t\t\t);')
        line_list.append('\t\t\trunOnlyForDeploymentPostprocessing = 0;')
        line_list.append('\t\t};')
        return 0

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

    def generate(self, line_list):
        """
        Write this record to output
        """

        self.buildlist = sorted(
            self.buildlist, key=operator.itemgetter(1))
        line_list.append('\t\t' + self.uuid + ' /* Frameworks */ = {')
        line_list.append('\t\t\tisa = PBXFrameworksBuildPhase;')
        line_list.append('\t\t\tbuildActionMask = 2147483647;')
        line_list.append('\t\t\tfiles = (')
        for item in self.buildlist:
            line_list.append('\t\t\t\t' + item[0] + ' /* ' +
                             item[1] + ' in Frameworks */,')
        line_list.append('\t\t\t);')
        line_list.append('\t\t\trunOnlyForDeploymentPostprocessing = 0;')
        line_list.append('\t\t};')

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

    def generate(self, line_list):
        """
        Write this record to output
        """

        line_list.append('\t\t' + self.uuid + ' /* ShellScript */ = {')
        line_list.append('\t\t\tisa = PBXShellScriptBuildPhase;')
        line_list.append('\t\t\tbuildActionMask = 2147483647;')
        line_list.append('\t\t\tfiles = (')
        line_list.append('\t\t\t);')
        if self.input:
            line_list.append('\t\t\tinputPaths = (')
            for item in self.input:
                line_list.append('\t\t\t\t"' + item + '",')
            line_list.append('\t\t\t);')
        line_list.append('\t\t\toutputPaths = (')
        line_list.append('\t\t\t\t"' + self.output + '",')
        line_list.append('\t\t\t);')
        line_list.append('\t\t\trunOnlyForDeploymentPostprocessing = 0;')
        line_list.append('\t\t\tshellPath = /bin/sh;')
        line_list.append('\t\t\tshellScript = "' + self.command + '\\n";')
        line_list.append('\t\t\tshowEnvVarsInLog = 0;')
        line_list.append('\t\t};')


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

    def generate(self, line_list):
        """
        Write this record to output
        """

        line_list.append('\t\t' + self.uuid + ' /* Project object */ = {')
        line_list.append('\t\t\tisa = PBXProject;')
        line_list.append('\t\t\tattributes = {')
        line_list.append('\t\t\t\tBuildIndependentTargetsInParallel = YES;')
        upgrade = OBJECT_VERSIONS.get(self.project.solution.ide)[1]
        if upgrade:
            line_list.append('\t\t\t\tLastUpgradeCheck = {};'.format(upgrade))
        line_list.append('\t\t\t};')
        if self.configlistref is not None:
            line_list.append(
                '\t\t\tbuildConfigurationList = ' +
                self.configlistref.uuid +
                ' /* Build configuration list for PBXProject "' +
                self.project.solution.name +
                '" */;')

        line_list.append('\t\t\tcompatibilityVersion = "{}";'.format(OBJECT_VERSIONS.get(self.project.solution.ide)[2]))
        region = OBJECT_VERSIONS.get(self.project.solution.ide)[3]
        if region:
            line_list.append('\t\t\tdevelopmentRegion = {};'.format(region))

        line_list.append('\t\t\thasScannedForEncodings = 1;')
        line_list.append('\t\t\tknownRegions = (')
        line_list.append('\t\t\t\ten,')
        line_list.append('\t\t\t);')
        if self.rootgroup is not None:
            line_list.append('\t\t\tmainGroup = ' + self.rootgroup.uuid +
                             ' /* ' + self.rootgroup.name + ' */;')
        line_list.append('\t\t\tprojectDirPath = "";')
        line_list.append('\t\t\tprojectRoot = "";')
        line_list.append('\t\t\ttargets = (')
        if self.targetlist:
            for item in self.targetlist:
                line_list.append('\t\t\t\t' + item.uuid +
                                 ' /* ' + item.name + ' */,')
        line_list.append('\t\t\t);')
        line_list.append('\t\t};')

    def append(self, item):
        """
        Append a PBXNative target
        """
        self.targetlist.append(item)


class PBXNativeTarget(object):
    """
    Each PBXNative entry
    """

    def __init__(self, parent, name, productreference,
                 productname, producttype):
        self.parent = parent
        self.name = name
        self.productreference = productreference
        self.productname = productname
        self.producttype = producttype
        self.uuid = calcuuid('PBXNativeTarget' + name)
        self.configlistref = None
        self.phases = []
        self.depends = []

    def generate(self, line_list):
        """
        Write this record to output
        """

        line_list.append('\t\t' + self.uuid + ' /* ' + self.name + ' */ = {')
        line_list.append('\t\t\tisa = PBXNativeTarget;')
        if self.configlistref is not None:
            line_list.append(
                '\t\t\tbuildConfigurationList = ' +
                self.configlistref.uuid +
                ' /* Build configuration list for PBXNativeTarget "' +
                self.name +
                '" */;')
        line_list.append('\t\t\tbuildPhases = (')
        for item in self.phases:
            line_list.append('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,')
        line_list.append('\t\t\t);')
        line_list.append('\t\t\tbuildRules = (')
        for item in self.parent.pbxbuildrules:
            line_list.append('\t\t\t\t' + item.uuid + ' /* PBXBuildRule */,')
        line_list.append('\t\t\t);')
        line_list.append('\t\t\tdependencies = (')
        for item in self.depends:
            line_list.append('\t\t\t\t' + item[0] + ' /* ' + item[1] + ' */,')
        line_list.append('\t\t\t);')
        line_list.append('\t\t\tname = ' + self.name + ';')
        line_list.append('\t\t\tproductName = ' + self.productname + ';')
        line_list.append(
            '\t\t\tproductReference = ' +
            self.productreference.uuid +
            ' /* ' +
            self.productreference.filename +
            ' */;')
        line_list.append('\t\t\tproductType = "' + self.producttype + '";')
        line_list.append('\t\t};')
        return 0

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

    def generate(self, line_list):
        """
        Write this record to output
        """

        line_list.append('\t\t' + self.uuid + ' /* ' +
                         str(self.configname) + ' */ = {')
        line_list.append('\t\t\tisa = XCBuildConfiguration;')
        if self.configfilereference is not None:
            line_list.append(
                '\t\t\tbaseConfigurationReference = ' +
                self.configfilereference.uuid +
                ' /* ' +
                os.path.basename(
                    self.configfilereference.filename) +
                ' */;')
        line_list.append('\t\t\tbuildSettings = {')
        if self.sdkroot is not None:
            line_list.append('\t\t\t\tSDKROOT = ' + self.sdkroot + ';')
        if self.installpath is True:
            line_list.append('\t\t\t\tINSTALL_PATH = "$(HOME)/Applications";')
        line_list.append('\t\t\t};')
        line_list.append('\t\t\tname = ' + str(self.configname) + ';')
        line_list.append('\t\t};')


class XCConfigurationList(object):
    """
    Each XCConfigurationList entry
    """

    def __init__(self, pbxtype, targetname):
        self.pbxtype = pbxtype
        self.targetname = targetname
        self.configuration_list = []
        self.uuid = calcuuid('XCConfigurationList' + pbxtype + targetname)

    def generate(self, line_list):
        """
        Write this record to output
        """

        line_list.append(
            '\t\t' +
            self.uuid +
            ' /* Build configuration list for ' +
            self.pbxtype +
            ' "' +
            self.targetname +
            '" */ = {')
        line_list.append('\t\t\tisa = XCConfigurationList;')
        line_list.append('\t\t\tbuildConfigurations = (')
        default = None
        found = set()
        for item in self.configuration_list:
            if item.configname in found:
                continue
            found.add(item.configname)
            if item.configname == 'Release':
                default = 'Release'
            elif default is None:
                default = item.configname
            line_list.append('\t\t\t\t' + item.uuid + ' /* ' +
                             item.configname + ' */,')
        if default is None:
            default = 'Release'
        line_list.append('\t\t\t);')
        line_list.append('\t\t\tdefaultConfigurationIsVisible = 0;')
        line_list.append('\t\t\tdefaultConfigurationName = ' + default + ';')
        line_list.append('\t\t};')


class PBXContainerItemProxy(object):
    """
    Each PBXContainerItemProxy entry
    """

    def __init__(self, nativetarget, rootuuid):
        self.nativetarget = nativetarget
        self.rootuuid = rootuuid
        self.uuid = calcuuid('PBXContainerItemProxy' + nativetarget.name)

    def generate(self, line_list):
        """
        Write this record to output
        """

        line_list.append(
            '\t\t' +
            self.uuid +
            ' /* PBXContainerItemProxy */ = {')
        line_list.append('\t\t\tisa = PBXContainerItemProxy;')
        line_list.append('\t\t\tcontainerPortal = ' +
                         self.rootuuid + ' /* Project object */;')
        line_list.append('\t\t\tproxyType = 1;')
        line_list.append('\t\t\tremoteGlobalIDString = ' +
                         self.nativetarget.uuid + ';')
        line_list.append('\t\t\tremoteInfo = "' + self.nativetarget.name + '";')
        line_list.append('\t\t};')


class PBXTargetDependency(object):
    """
    Each PBXTargetDependency entry
    """

    def __init__(self, proxy, nativetarget):
        self.proxy = proxy
        self.nativetarget = nativetarget
        self.uuid = calcuuid('PBXTargetDependency' +
                             proxy.nativetarget.name + nativetarget.name)

    def generate(self, line_list):
        """
        Write this record to output
        """

        line_list.append('\t\t' + self.uuid + ' /* PBXTargetDependency */ = {')
        line_list.append('\t\t\tisa = PBXTargetDependency;')
        line_list.append('\t\t\ttarget = ' + self.nativetarget.uuid +
                         ' /* ' + self.nativetarget.name + ' */;')
        line_list.append('\t\t\ttargetProxy = ' + self.proxy.uuid +
                         ' /* PBXContainerItemProxy */;')
        line_list.append('\t\t};')


class Project(object):
    """
    Root object for an XCode IDE project file
    Created with the name of the project, the IDE code (xc3, xc5)
    the platform code (ios, osx)
    """

    def __init__(self, solution):
        """
        Init the project generator
        """
        self.solution = solution
        self.uuid = calcuuid('PBXProjectRoot' + solution.xcode_folder_name)

        idecode = solution.ide.get_short_code()
        rootproject = PBXProject(self)

        # No files yet!
        self.pbxfilereferences = []
        self.pbxbuildfiles = []
        self.pbxbuildrules = []
        self.pbxprojects = [rootproject]
        self.pbxnativetargets = []
        self.pbxgroups = []
        self.sourcesbuildphases = []
        self.framesworksbuildphases = []
        self.shellscriptbuildphases = []
        self.xcbuildconfigurations = []
        self.xcconfigurationlists = []
        self.containeritemproxies = []
        self.targetdependencies = []

        found_glsl = False

        # Process all the projects and configurations
        for project in solution.project_list:
            # Process the filenames
            project.get_file_list([FileTypes.icns,
                                   FileTypes.h,
                                   FileTypes.cpp,
                                   FileTypes.frameworks,
                                   FileTypes.exe,
                                   FileTypes.library,
                                   FileTypes.glsl])

            for item in project.configuration_list[0].frameworks_list:
                item = SourceFile(item, '', FileTypes.frameworks)
                project.codefiles.append(item)

            for item in project.codefiles:
                if item.type is FileTypes.glsl:
                    found_glsl = True
                self.addfilereference(item.relative_pathname, item.type)

            # What's the final output file?
            if project.project_type is ProjectTypes.library:
                if project.platform is PlatformTypes.ios:
                    libextension = 'ios.a'
                else:
                    libextension = 'osx.a'
                outputfilereference = self.addfilereference(
                    'lib' + solution.name + idecode + libextension,
                    FileTypes.library)
            elif project.project_type is ProjectTypes.app:
                outputfilereference = self.addfilereference(
                    solution.name + '.app', FileTypes.exe)
            elif project.project_type is not ProjectTypes.empty:
                outputfilereference = self.addfilereference(
                    solution.name, FileTypes.exe)
            else:
                outputfilereference = None

            # If a fat library, add references for dev and sim targets
            ioslibrary = False
            if project.platform is PlatformTypes.ios:
                if project.project_type is ProjectTypes.library:
                    ioslibrary = True

            if ioslibrary:
                devfilereference = self.addfilereference(
                    'lib' + solution.name + idecode + 'dev.a', FileTypes.library)
                simfilereference = self.addfilereference(
                    'lib' + solution.name + idecode + 'sim.a', FileTypes.library)

                # Two targets for "fat" libraries
                buildphase1 = self.addsourcesbuildphase(
                    devfilereference)
                buildphase2 = self.addsourcesbuildphase(
                    simfilereference)
                framephase1 = self.addframeworksbuildphase(
                    devfilereference)
                framephase2 = self.addframeworksbuildphase(
                    simfilereference)

                # Add source files to compile for the ARM and the Intel libs

                for item in self.pbxfilereferences:
                    if item.type is FileTypes.cpp or item.type is FileTypes.glsl:
                        buildphase1.append(
                            self.addbuildfile(item, devfilereference))
                        buildphase2.append(
                            self.addbuildfile(item, simfilereference))
                    elif item.type is FileTypes.frameworks:
                        framephase1.append(
                            self.addbuildfile(item, devfilereference))
                        framephase2.append(
                            self.addbuildfile(item, simfilereference))

            else:
                if outputfilereference:
                    devfilereference = None
                    simfilereference = None
                    buildphase1 = self.addsourcesbuildphase(
                        outputfilereference)
                    framephase1 = self.addframeworksbuildphase(
                        outputfilereference)
                    for item in self.pbxfilereferences:
                        if item.type is FileTypes.cpp or item.type is FileTypes.glsl:
                            buildphase1.append(self.addbuildfile(
                                item, outputfilereference))
                        elif item.type is FileTypes.frameworks:
                            framephase1.append(self.addbuildfile(
                                item, outputfilereference))

            # Create the root file group and the Products group
            groupproducts = PBXGroup('Products', None)

            grouproot = self.addgroup(solution.name, None)

            # No frameworks group unless one is warranted

            frameworksgroup = None

            # Insert all the file references into groups

            for item in self.pbxfilereferences:
                # Products go into a special group
                if item.type is FileTypes.exe:
                    groupproducts.append(item)
                elif item.type is FileTypes.library:
                    groupproducts.append(item)
                elif item.type is FileTypes.frameworks:

                    # Create the group if needed

                    if frameworksgroup is None:
                        frameworksgroup = self.addgroup(
                            'Frameworks', None)
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
                        # base = item.relative_pathname[index+1:]
                        path = item.filename[0:index]
                        #
                        # See if a group already exists
                        #
                        found = False
                        for matchgroup in self.pbxgroups:
                            if matchgroup.path is not None and matchgroup.path == path:
                                # Add to a pre-existing group
                                matchgroup.append(item)
                                found = True
                                break
                        if found:
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
                                matchgroup = self.addgroup(
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
                                for matchgroup in self.pbxgroups:
                                    if matchgroup.path is None:
                                        continue
                                    if matchgroup.path == temppath:
                                        found = True
                                        break

                                if not found:
                                    matchgroup = self.addgroup(
                                        path[index:index + endindex], temppath)
                                    previousgroup.appendgroup(matchgroup)
                                previousgroup = matchgroup
                                index = index + endindex + 1


            # Any output?
            if groupproducts.filelist:
                self.pbxgroups.append(groupproducts)
                grouproot.appendgroup(groupproducts)
            # Create the config list for the root project

            configlistref = self.addxcconfigurationlist(
                'PBXProject', solution.name)
            for item in project.configuration_list:
                configlistref.configuration_list.append(
                    self.addxcbuildconfigurationlist(
                        item.name, None, configlistref, None, False))
            rootproject.configlistref = configlistref
            rootproject.rootgroup = grouproot

            #
            # Create the PBXNativeTarget config chunks
            #

            sdkroot = None
            if project.platform is PlatformTypes.ios:
                sdkroot = 'iphoneos'

            if project.project_type is ProjectTypes.library:
                outputtype = 'com.apple.product-type.library.static'
            elif project.project_type is ProjectTypes.screensaver:
                outputtype = 'com.apple.product-type.bundle'
            elif project.project_type is ProjectTypes.app:
                outputtype = 'com.apple.product-type.application'
            else:
                outputtype = 'com.apple.product-type.tool'

            # For a normal project, attach the config to a native target and
            # we're done
            if not ioslibrary and outputfilereference:
                configlistref = self.addxcconfigurationlist(
                    'PBXNativeTarget', solution.name)
                install = False
                if project.project_type is ProjectTypes.app:
                    install = True
                for item in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            item.name, None, configlistref, sdkroot, install))
                if project.project_type is ProjectTypes.library:
                    finalname = solution.name
                else:
                    finalname = solution.name
                nativetarget1 = self.addnativeproject(
                    finalname, outputfilereference, solution.name, outputtype)
                nativetarget1.configlistref = configlistref
                rootproject.append(nativetarget1)
                nativetarget1.append(buildphase1.uuid, 'Sources')
                nativetarget1.append(framephase1.uuid, 'Frameworks')

            #
            # For fat binary iOS projects, it's a lot messier
            #

            elif outputfilereference:
                targetname = solution.name
                configlistref = self.addxcconfigurationlist(
                    'PBXNativeTarget', targetname)
                for item in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            item.name, None, configlistref, None, False))
                nativetarget1 = self.addnativeproject(
                    targetname, outputfilereference, solution.name, outputtype)
                nativetarget1.configlistref = configlistref
                rootproject.append(nativetarget1)

                targetname = solution.name + idecode + 'dev'
                configlistref = self.addxcconfigurationlist(
                    'PBXNativeTarget', targetname)
                for item in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            item.name, None, configlistref, 'iphoneos', False))
                nativeprojectdev = self.addnativeproject(
                    targetname, devfilereference, solution.name, outputtype)
                nativeprojectdev.configlistref = configlistref
                rootproject.append(nativeprojectdev)

                nativeprojectdev.append(buildphase1.uuid, 'Sources')
                nativeprojectdev.append(framephase1.uuid, 'Frameworks')
                devcontainer = self.addcontaineritemproxy(
                    nativeprojectdev, self.uuid)

                targetname = solution.name + idecode + 'sim'
                configlistref = self.addxcconfigurationlist(
                    'PBXNativeTarget', targetname)
                for item in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            item.name, None, configlistref, 'iphonesimulator', False))
                nativeprojectsim = self.addnativeproject(
                    targetname, simfilereference, solution.name, outputtype)
                nativeprojectsim.configlistref = configlistref
                rootproject.append(nativeprojectsim)

                nativeprojectsim.append(buildphase2.uuid, 'Sources')
                nativeprojectsim.append(framephase2.uuid, 'Frameworks')
                simcontainer = self.addcontaineritemproxy(
                    nativeprojectsim, self.uuid)

                nativetarget1.depend(self.adddependency(
                    devcontainer, nativeprojectdev).uuid, 'PBXTargetDependency')
                nativetarget1.depend(self.adddependency(
                    simcontainer, nativeprojectsim).uuid, 'PBXTargetDependency')

            # Add in a shell script build phase if needed
            # Is this an application?

            if project.platform is PlatformTypes.macosx:
                if project.project_type is ProjectTypes.tool:
                    input_data = [
                        '${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}']
                    output = '${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
                    command = 'if [ ! -d ${SRCROOT}/bin ]; then mkdir ${SRCROOT}/bin; fi\\n' \
                        '${CP} ${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME} ' \
                        '${SRCROOT}/bin/${EXECUTABLE_NAME}${IDESUFFIX}${SUFFIX}'
                    shellbuildphase = self.addshellscriptbuildphase(
                        input_data, output, command)
                    nativetarget1.append(shellbuildphase.uuid, 'ShellScript')
                elif project.project_type is ProjectTypes.app:
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
                    shellbuildphase = self.addshellscriptbuildphase(
                        input_data, output, command)
                    nativetarget1.append(shellbuildphase.uuid, 'ShellScript')

            # Is there a deployment folder?

            deploy_folder = None
            for configuration in project.configuration_list:
                if configuration.deploy_folder:
                    deploy_folder = configuration.deploy_folder

            if deploy_folder is not None:
                if ioslibrary is False:
                    input_data = [
                        '${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}']
                else:
                    input_data = [
                        '${BUILD_ROOT}/' + solution.name + idecode +
                        'dev${SUFFIX}/lib' + solution.name + idecode + 'dev.a',
                        '${BUILD_ROOT}/' + solution.name + idecode +
                        'sim${SUFFIX}/lib' +
                        solution.name + idecode + 'sim.a'
                    ]
                deploy_folder = deploy_folder.replace('(', '{')
                deploy_folder = deploy_folder.replace(')', '}')
                if ioslibrary is True:
                    command = 'p4 edit ' + deploy_folder + '${FINAL_OUTPUT}\\nlipo -output ' + \
                        deploy_folder + '${FINAL_OUTPUT} -create ${BUILD_ROOT}/' + \
                        solution.name + idecode + \
                        'dev${SUFFIX}/lib' + solution.name + idecode + \
                        'dev.a ${BUILD_ROOT}/' + \
                        solution.name + idecode + \
                        'sim${SUFFIX}/lib' + solution.name + \
                        idecode + 'sim.a\\n'
                elif project.project_type is ProjectTypes.library:
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
                shellbuildphase = self.addshellscriptbuildphase(
                    input_data, deploy_folder + '${FINAL_OUTPUT}', command)
                nativetarget1.append(shellbuildphase.uuid, 'ShellScript')

        if found_glsl:
            self.pbxbuildrules.append(PBXBuildRule(self))

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

    def addnativeproject(self, name, productreference,
                         productname, producttype):
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
        for item in self.xcbuildconfigurations:
            if item.uuid == entry.uuid:
                entry = item
                break
        else:
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

    def generate(self, line_list):
        """
        Dump out the entire file.

        Args:
            line_list: Line list to append new lines.
        Return:
            Non-zero on error.
        """

        # Write the XCode header
        line_list.append('// !$*UTF8*$!')
        line_list.append('{')

        # Always present in an XCode file
        line_list.append('\tarchiveVersion = 1;')
        line_list.append('\tclasses = {')
        line_list.append('\t};')
        line_list.append('\tobjectVersion = {};'.format(OBJECT_VERSIONS.get(self.solution.ide)[0]))
        line_list.append('\tobjects = {')

        # Write out each of the chunks
        writelist(self.pbxbuildfiles, line_list)
        writelist(self.pbxbuildrules, line_list)
        writelist(self.containeritemproxies, line_list)
        writelist(self.pbxfilereferences, line_list)
        writelist(self.framesworksbuildphases, line_list)
        writelist(self.pbxgroups, line_list)
        writelist(self.pbxnativetargets, line_list)
        writelist(self.pbxprojects, line_list)
        writelist(self.shellscriptbuildphases, line_list)
        writelist(self.sourcesbuildphases, line_list)
        writelist(self.targetdependencies, line_list)
        writelist(self.xcbuildconfigurations, line_list)
        writelist(self.xcconfigurationlists, line_list)

        # Close up the project file
        line_list.append('\t};')
        line_list.append(
            '\trootObject = ' +
            self.uuid +
            ' /* Project object */;')
        line_list.append('}')
        return 0

########################################


def generate(solution):
    """
    Create a project file for XCode file format version 3.1
    """

    # Failsafe
    if solution.ide not in SUPPORTED_IDES:
        return 10

    # Create the output filename and pass it to the generator
    # so it can reference itself in make targets
    solution.xcode_folder_name = '{}{}{}.xcodeproj'.format(
        solution.name, solution.ide_code, solution.platform_code)
    create_folder_if_needed(solution.xcode_folder_name)

    # Xcode requires configurations, if none are present, add some

    if not solution.project_list:
        project = CoreProject(name=solution.name, project_type=ProjectTypes.empty)
        project.source_folders_list = []
        solution.project_list.append(project)

    for project in solution.project_list:
        if not project.configuration_list:
            project.configuration_list.append(Configuration('Debug'))
            project.configuration_list.append(Configuration('Release'))

    exporter = Project(solution)

    # Output the actual project file
    xcode_lines = []
    error = exporter.generate(xcode_lines)
    if error:
        return error

    # Save the file if it changed
    xcode_filename = os.path.join(
        solution.working_directory,
        solution.xcode_folder_name,
        'project.pbxproj')

    error = 0
    save_text_file_if_newer(
        xcode_filename,
        xcode_lines,
        bom=False,
        perforce=solution.perforce,
        verbose=solution.verbose)

    return error
