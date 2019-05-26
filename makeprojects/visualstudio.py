#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sub file for makeprojects.
Handler for Microsoft Visual Studio projects
"""

# Copyright 1995-8 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

from __future__ import absolute_import, print_function, unicode_literals

import os
from uuid import NAMESPACE_DNS, UUID
import io
from io import StringIO
from enum import Enum
from hashlib import md5
from burger import PY2, save_text_file_if_newer, convert_to_windows_slashes, delete_file
from burger import perforce_edit, escape_xml_cdata, escape_xml_attribute
import makeprojects.core
from .enums import platformtype_short_code
from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes

if not PY2:
    # pylint: disable=C0103
    unicode = str

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

DEFAULT_FINAL_FOLDER = '$(BURGER_SDKS)/windows/bin/'

########################################


def get_uuid(input_str):
    """
    Convert a string to a UUUD.

    Given a project name string, create a 128 bit unique hash for
    Visual Studio.

    Args:
        input_str: Unicode string of the filename to convert into a hash
    Returns:
        A string in the format of CF994A05-58B3-3EF5-8539-E7753D89E84F
    """

    # Generate using md5 with NAMESPACE_DNS as salt
    temp_md5 = md5(NAMESPACE_DNS.bytes + input_str.encode('utf-8')).digest()
    return str(UUID(bytes=temp_md5[:16], version=3)).upper()


class SemicolonArray(object):
    """
    Helper class to hold an array of strings that are joined
    by semicolons
    """

    def __init__(self, entries=None):
        if entries is None:
            entries = []
        self.entries = entries

    #
    ## Output the string as unicode
    #

    def __unicode__(self):
        # Output nothing if there is no data
        if self.entries is None:
            return ''

        # Output the entries seperated by semicolons
        return u';'.join(self.entries)

    def __str__(self):
        """
        Output the string with UTF-8 encoding.
        """
        return unicode(self).encode('utf-8')

    def append(self, entry):
        """
        Add a string to the array.
        """
        self.entries.append(entry)


########################################

class VS2003XML():
    """
    Visual Studio 2003-2008 XML formatter.

    Output XML elements in the format of Visual Studio 2003-2008
    """

    def __init__(self, name):
        """
        Set the defaults.
        Args:
            name: Name of the XML element
        """

        ## Name of this XML chunk.
        self.name = name

        ## XML attributes.
        self.attributes = []

        ## List of elements in this element.
        self.elements = []

    def add_attribute(self, name, data):
        """
        Add an attribute to this XML element.

        Args:
            name: Name of the attribute
            data: Attribute data
        """
        self.attributes.append((name, data))

    def add_element(self, element):
        """
        Add an element to this XML element.

        Args:
            element: VS2003XML object
        """
        self.elements.append(element)

    def generate(self, line_list, indent=0):
        """
        Generate the text lines for this XML element.
        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
        """

        tabs = '\t' * indent
        if self.attributes:
            line_list.append('{0}<{1}'.format(tabs, escape_xml_cdata(self.name)))
            for attribute in self.attributes:
                line_list.append(
                    '\t{0}{1}="{2}"'.format(
                        tabs, escape_xml_cdata(
                            attribute[0]), escape_xml_attribute(attribute[1])))
            if not self.elements:
                line_list.append('{0}/>'.format(tabs))
                return
            line_list.append('\t{0}>'.format(tabs))
        else:
            line_list.append('{0}<{1}>'.format(tabs, escape_xml_cdata(self.name)))

        for element in self.elements:
            element.generate(line_list, indent=indent + 1)
        line_list.append('{0}</{1}>'.format(tabs, escape_xml_cdata(self.name)))

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        line_list = []
        self.generate(line_list)
        return '\n'.join(line_list)

    ## Allow str() to work.
    __str__ = __repr__









class Tool2003(object):
    """
    Helper class to output a Tool record for Visual Studio 2003-2008

    In Visual Studio project files from version 2003 to 2008, Tool
    XML records were used for settings for each and every compiler tool
    """
    #
    ## Initialize the record with the entries and the name of the tool
    #
    # /param name A string of the Visual Studio 2003 or later Tool
    # /param entries Array of string / operands
    # /param tabs Number of tabs printed before each line
    #

    def __init__(self, name, entries=None, tabs=3):
        if entries is None:
            entries = []
        self.name = name
        self.entries = entries
        self.tabstring = u'\t' * tabs

    #
    ## Output the string as unicode
    #

    def __unicode__(self):

        # Save off the opening of the XML
        output = self.tabstring + '<Tool\n' + self.tabstring + '\tName="' + self.name + '"'

        # Save off the entries, if any
        for item in self.entries:
            # Ignore entries without data
            if item[1] is not None:
                output += '\n' + self.tabstring + '\t' + item[0] + '="' + unicode(item[1]) + '"'

        # Close off the XML and return the final string
        return output + '/>\n'

    def __str__(self):
        """
        Output the string with UTF-8 encoding
        """
        return unicode(self).encode('utf-8')

    def setvalue(self, name, newvalue):
        """
        Scan the list of entries and set the value to the new
        value

        If the value was not found, it will be appended to the list

        Args:
            name: String of the entry to match
            newvalue: Value to substitute
        """
        for item in self.entries:
            if item[0] == name:
                item[1] = newvalue
                return

        # Not found? Add the entry and then exit
        self.entries.append([name, newvalue])

    def removeentry(self, name):
        """
        Remove an entry

        If the value is in the list, remove it.

        Args:
            name: String of the entry to remove
        """
        i = 0
        while i < len(self.entries):
            # Match?
            if self.entries[i][0] == name:
                # Remove the entry and exit
                del self.entries[i]
                return

            # Next entry
            i += 1


class VCCLCompilerTool(Tool2003):
    """
    Visual Studio 2003 VCCLCompilerTool record
    """

    def __init__(self):
        """
        """
        entries = [
            # General menu
            ['AdditionalIncludeDirectories', SemicolonArray()],
            ['AdditionalUsingDirectories', None],
            ['SuppressStartupBanner', 'TRUE'],
            ['DebugInformationFormat', '3'],
            ['WarningLevel', '4'],
            ['Detect64BitPortabilityProblems', 'TRUE'],
            ['WarnAsError', None],

            # Optimization menu
            ['Optimization', '2'],
            ['GlobalOptimizations', None],
            ['InlineFunctionExpansion', '2'],
            ['EnableIntrinsicFunctions', 'TRUE'],
            ['ImproveFloatingPointConsistency', 'TRUE'],
            ['FavorSizeOrSpeed', '1'],
            ['OmitFramePointers', 'TRUE'],
            ['EnableFiberSafeOptimizations', 'TRUE'],
            ['OptimizeForProcessor', None],
            ['OptimizeForWindowsApplication', None],

            # Preprocess menu
            ['PreprocessorDefinitions', None],
            ['IgnoreStandardIncludePath', None],
            ['GeneratePreprocessedFile', None],
            ['KeepComments', None],

            # Code generation menu
            ['StringPooling', 'TRUE'],
            ['MinimalRebuild', 'TRUE'],
            ['ExceptionHandling', '0'],
            ['SmallerTypeCheck', None],
            ['BasicRuntimeChecks', None],
            ['RuntimeLibrary', '1'],
            ['StructMemberAlignment', '4'],
            ['BufferSecurityCheck', 'FALSE'],
            ['EnableFunctionLevelLinking', 'TRUE'],
            ['EnableEnhancedInstructionSet', None],

            # Language extensions menu
            ['DisableLanguageExtensions', None],
            ['DefaultCharIsUnsigned', None],
            ['TreatWChar_tAsBuiltInType', None],
            ['ForceConformanceInForLoopScope', None],
            ['RuntimeTypeInfo', 'FALSE'],

            # Precompiled header menu
            ['UsePrecompiledHeader', None],
            ['PrecompiledHeaderThrough', None],
            ['PrecompiledHeaderFile', None],

            # Output files menu
            ['ExpandAttributedSource', None],
            ['AssemblerOutput', None],
            ['AssemblerListingLocation', None],
            ['ObjectFile', None],
            ['ProgramDataBaseFileName', '$(OutDir)\\$(TargetName).pdb'],

            # Browse information menu
            ['BrowseInformation', None],
            ['BrowseInformationFile', None],

            # Advanced menu
            ['CallingConvention', '1'],
            ['CompileAs', '2'],
            ['DisableSpecificWarnings', '4201'],
            ['ForcedIncludeFile', None],
            ['ForcedUsingFiles', None],
            ['ShowIncludes', None],
            ['UndefinePreprocessorDefinitions', None],
            ['UndefineAllPreprocessorDefinitions', None],

            # Command line menu
            ['AdditionalOptions', None]
        ]
        Tool2003.__init__(self, name='VCCLCompilerTool', entries=entries)


class VCCustomBuildTool(Tool2003):
    """
    Visual Studio 2003 VCCustomBuildTool record
    """

    def __init__(self):
        """
        """
        entries = [
            # General menu
            ['Description', None],
            ['CommandLine', None],
            ['AdditionalDependencies', None],
            ['Outputs', None]
        ]
        Tool2003.__init__(self, name='VCCustomBuildTool', entries=entries)


class VCLinkerTool(Tool2003):
    """
    Visual Studio 2003 VCLinkerTool
    """

    def __init__(self):
        entries = [
            # General menu
            ['OutputFile', '&quot;$(OutDir)unittestsvc8w32dbg.exe&quot;'],
            ['ShowProgress', None],
            ['Version', None],
            ['LinkIncremental', 'TRUE'],
            ['SuppressStartupBanner', None],
            ['IgnoreImportLibrary', None],
            ['RegisterOutput', None],
            ['AdditionalLibraryDirectories', SemicolonArray(
                [
                    '$(BURGER_SDKS)\\windows\\perforce',
                    '$(BURGER_SDKS)\\windows\\burgerlib',
                    '$(BURGER_SDKS)\\windows\\opengl'
                ]
            )],

            # Input menu
            ['AdditionalDependencies', 'burgerlibvc8w32dbg.lib'],
            ['IgnoreAllDefaultLibraries', None],
            ['IgnoreDefaultLibraryNames', None],
            ['ModuleDefinitionFile', None],
            ['AddModuleNamesToAssembly', None],
            ['EmbedManagedResourceFile', None],
            ['ForceSymbolReferences', None],
            ['DelayLoadDLLs', None],

            # Debugging menu
            ['GenerateDebugInformation', 'TRUE'],
            ['ProgramDatabaseFile', None],
            ['StripPrivateSymbols', None],
            ['GenerateMapFile', None],
            ['MapFileName', None],
            ['MapExports', None],
            ['MapLines', None],
            ['AssemblyDebug', None],

            # System menu
            ['SubSystem', '1'],
            ['HeapReserveSize', None],
            ['HeapCommitSize', None],
            ['StackReserveSize', None],
            ['StackCommitSize', None],
            ['LargeAddressAware', None],
            ['TerminalServerAware', None],
            ['SwapRunFromCD', None],
            ['SwapRunFromNet', None],

            # Optimization
            ['OptimizeReferences', '2'],
            ['EnableCOMDATFolding', '2'],
            ['OptimizeForWindows98', None],
            ['FunctionOrder', None],

            # Embedded MIDL menu
            ['MidlCommandFile', None],
            ['IgnoreEmbeddedIDL', None],
            ['MergedIDLBaseFileName', None],
            ['TypeLibraryFile', None],
            ['TypeLibraryResourceID', None],

            # Advanced menu
            ['EntryPointSymbol', None],
            ['ResourceOnlyDLL', None],
            ['SetChecksum', None],
            ['BaseAddress', None],
            ['FixedBaseAddress', None],
            ['TurnOffAssemblyGeneration', None],
            ['SupportUnloadOfDelayLoadedDLL', None],
            ['ImportLibrary', None],
            ['MergeSections', None],
            ['TargetMachine', '1'],

            # Command line menu
            ['AdditionalOptions', None]
        ]
        Tool2003.__init__(self, name='VCLinkerTool', entries=entries)


class VCMIDLTool(Tool2003):
    """
    Visual Studio 2003 for the MIDL tool
    """

    def __init__(self):
        """
        """
        Tool2003.__init__(self, name='VCMIDLTool')


class VCPostBuildEventTool(Tool2003):
    """
    VCPostBuildEventTool
    """

    def __init__(self):
        """
        """
        entries = [
            # General menu
            ['Description', None],
            ['CommandLine', None],
            ['ExcludedFromBuild', None]
        ]
        Tool2003.__init__(self, name='VCPostBuildEventTool', entries=entries)


class VCPreBuildEventTool(Tool2003):
    """
    VCPreBuildEventTool
    """

    def __init__(self):
        """
        Init
        """
        entries = [
            # General menu
            ['Description', None],
            ['CommandLine', None],
            ['ExcludedFromBuild', None]
        ]
        Tool2003.__init__(self, name='VCPreBuildEventTool', entries=entries)


class VCPreLinkEventTool(Tool2003):
    """
    VCPreLinkEventTool
    """

    def __init__(self):
        """
        Init
        """
        entries = [
            # General menu
            ['Description', None],
            ['CommandLine', None],
            ['ExcludedFromBuild', None]
        ]
        Tool2003.__init__(self, name='VCPreLinkEventTool', entries=entries)


class VCResourceCompilerTool(Tool2003):
    """
    VCResourceCompilerTool
    """

    def __init__(self):
        """
        Init
        """
        Tool2003.__init__(self, name='VCResourceCompilerTool')


class VCWebServiceProxyGeneratorTool(Tool2003):
    """
    VCWebServiceProxyGeneratorTool
    """

    def __init__(self):
        """
        Init
        """
        Tool2003.__init__(self, name='VCWebServiceProxyGeneratorTool')


class VCXMLDataGeneratorTool(Tool2003):
    """
    VCXMLDataGeneratorTool
    """

    def __init__(self):
        """
        Init
        """
        Tool2003.__init__(self, name='VCXMLDataGeneratorTool')


class VCWebDeploymentTool(Tool2003):
    """
    VCWebDeploymentTool
    """

    def __init__(self):
        """
        Init
        """
        Tool2003.__init__(self, name='VCWebDeploymentTool')


class VCManagedWrapperGeneratorTool(Tool2003):
    """
    VCManagedWrapperGeneratorTool
    """

    def __init__(self):
        """
        Init
        """
        Tool2003.__init__(self, name='VCManagedWrapperGeneratorTool')


class VCAuxiliaryManagedWrapperGeneratorTool(Tool2003):
    """
    VCAuxiliaryManagedWrapperGeneratorTool
    """

    def __init__(self):
        """
        Init
        """
        Tool2003.__init__(self, name='VCAuxiliaryManagedWrapperGeneratorTool')


class XboxDeploymentTool(Tool2003):
    """
    XboxDeploymentTool
    """

    def __init__(self):
        """
        Init
        """
        Tool2003.__init__(self, name='XboxDeploymentTool')


class XboxImageTool(Tool2003):
    """
    XboxImageTool
    """

    def __init__(self):
        """
        Init
        """
        Tool2003.__init__(self, name='XboxImageTool')


class VS2003Configuration(object):
    """
    Configuration records
    """

    def __init__(self, project, configuration, vsplatform):
        """
        Initialize a Visual Studio 2003 configuration record
        """
        self.project = project
        self.configuration = configuration
        self.vsplatform = vsplatform

        self.entries = [
            ['OutputDirectory', 'bin\\'],
            ['IntermediateDirectory', 'temp\\'],
            ['ConfigurationType', '1'],
            ['UseOfMFC', '0'],
            ['ATLMinimizesCRunTimeLibraryUsage', 'false'],
            ['CharacterSet', '1'],
            ['DeleteExtensionsOnClean', None],
            ['ManagedExtensions', None],
            ['WholeProgramOptimization', None],
            ['ReferencesPath', None]
        ]

        self.tools = []

        self.tools.append(VCCLCompilerTool())
        self.tools.append(VCCustomBuildTool())
        self.tools.append(VCLinkerTool())

        if vsplatform == 'Win32' or vsplatform == 'x64':
            self.tools.append(VCMIDLTool())

        self.tools.append(VCPostBuildEventTool())
        self.tools.append(VCPreBuildEventTool())
        self.tools.append(VCPreLinkEventTool())

        if vsplatform == 'Xbox':
            self.tools.append(XboxDeploymentTool())
            self.tools.append(XboxImageTool())
        else:
            self.tools.append(VCResourceCompilerTool())
            self.tools.append(VCWebServiceProxyGeneratorTool())
            self.tools.append(VCXMLDataGeneratorTool())
            self.tools.append(VCWebDeploymentTool())
            self.tools.append(VCManagedWrapperGeneratorTool())
            self.tools.append(VCAuxiliaryManagedWrapperGeneratorTool())

    def write(self, fileref):
        """
        Write
        """
        return
        fileref.write(u'\t\t<Configuration')
        fileref.write(u'\n\t\t\tName="' + self.configuration + '|' + self.vsplatform + '"')

        for item in self.entries:
            if item[1] is not None:
                fileref.write(u'\n\t\t\t' + item[0] + '="' + item[1] + '"')

        fileref.write(u'>\n')

        for tool in self.tools:
            fileref.write(unicode(tool))

        fileref.write(u'\t\t</Configuration>\n')


class FileVersions(Enum):
    """
    Enumeration of supported file types for input
    """

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
    ## Visual Studio 2017
    vs2017 = 7
    ## Visual Studio 2019
    vs2019 = 8

#
## Solution (.sln) file version number to encode
#


formatversion = [
    '8.00',         # 2003
    '9.00',         # 2005
    '10.00',        # 2008
    '11.00',        # 2010
    '12.00',        # 2012
    '12.00',        # 2013
    '12.00',        # 2015
    '12.00',        # 2017
    '12.00'         # 2019
]

#
## Solution (.sln) year version number to encode
#

yearversion = [
    '2003',         # 2003
    '2005',         # 2005
    '2008',         # 2008
    '2010',         # 2010
    '2012',         # 2012
    '2013',         # 2013
    '14',           # 2015
    '15',           # 2017
    'Version 16'    # 2019
]

#
## Project file suffix to append to the name (It changed after vs2008)
#

projectsuffix = [
    '.vcproj',      # 2003
    '.vcproj',      # 2005
    '.vcproj',      # 2008
    '.vcxproj',     # 2010
    '.vcxproj',     # 2012
    '.vcxproj',     # 2013
    '.vcxproj',     # 2015
    '.vcxproj',     # 2017
    '.vcxproj'      # 2019
]

#
## Tool chain for each platform
#

platformtoolsets = [
    'v70',          # 2003
    'v80',          # 2005
    'v90',          # 2008
    'v100',         # 2010
    'v110_xp',      # 2012
    'v120_xp',      # 2013
    'v140_xp',      # 2015
    'v141_xp',      # 2017
    'v142'          # 2019
]

#
# Subroutine for saving out a group of filenames based on compiler used
# Used by the filter exporter
#


def writefiltergroup(fileref, filelist, groups, compilername):

    # Iterate over the list
    for item in filelist:
        # Get the Visual Studio group name
        groupname = item.extractgroupname()
        if groupname != '':
            # Add to the list of groups found
            groups.append(groupname)
            # Write out the record
            fileref.write(u'\t\t<' + compilername + ' Include="' +
                          convert_to_windows_slashes(item.filename) + '">\n')
            fileref.write(u'\t\t\t<Filter>' + groupname + '</Filter>\n')
            fileref.write(u'\t\t</' + compilername + '>\n')

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


def comparefiletostring(filename, string):

    #
    # Do a data compare as a text file
    #

    f1 = None
    try:
        f1 = io.open(filename, 'r')
        fileOneLines = f1.readlines()
        f1.close()

    except BaseException:
        if f1 is not None:
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

class Defaults(object):

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
        self.outputfilename = None
        # List of acceptable file types
        self.acceptable = []

        ## File version to encode (Default vs2010)
        self.fileversion = FileVersions.vs2010

    #
    # The solution has been set up, perform setup
    # based on the type of project being created
    #

    def defaults(self, solution):

        #
        # Determine settings for the generated solution file
        #

        if solution.ide == IDETypes.vs2003:
            self.fileversion = FileVersions.vs2003

        elif solution.ide == IDETypes.vs2005:
            self.fileversion = FileVersions.vs2005

        elif solution.ide == IDETypes.vs2008:
            self.fileversion = FileVersions.vs2008

        elif solution.ide == IDETypes.vs2010:
            self.fileversion = FileVersions.vs2010

        elif solution.ide == IDETypes.vs2012:
            self.fileversion = FileVersions.vs2012

        elif solution.ide == IDETypes.vs2013:
            self.fileversion = FileVersions.vs2013

        elif solution.ide == IDETypes.vs2015:
            self.fileversion = FileVersions.vs2015

        elif solution.ide == IDETypes.vs2017:
            self.fileversion = FileVersions.vs2017

        elif solution.ide == IDETypes.vs2019:
            self.fileversion = FileVersions.vs2019
        else:
            # Not supported yet
            return 10

        #
        # Get the config file name and default frameworks
        #

        self.idecode = solution.ide.get_short_code()
        self.platformcode = solution.projects[0].platform.get_short_code()
        self.outputfilename = str(solution.name + self.idecode + self.platformcode)
        self.uuid = get_uuid(self.outputfilename)

        #
        # Create a list of acceptable files that can be included in the project
        #

        self.acceptable = [FileTypes.h, FileTypes.cpp, FileTypes.c]
        if self.platformcode == 'win':
            self.acceptable.extend([FileTypes.rc, FileTypes.ico])
            # 2010 or higher supports hlsl and glsl files
            if self.fileversion.value >= FileVersions.vs2010.value:
                self.acceptable.extend([FileTypes.hlsl, FileTypes.glsl])

        # Xbox 360 shaders are supported
        elif self.platformcode == 'x36' and \
                self.fileversion == FileVersions.vs2010:
            self.acceptable.append(FileTypes.x360sl)

        # PS Vita shaders are supported
        elif self.platformcode == 'vit' and \
                self.fileversion == FileVersions.vs2010:
            self.acceptable.append(FileTypes.vitacg)

        return 0

    #
    # A json file had the key "visualstudio" with a dictionary.
    # Parse the dictionary for extra control
    #

    def loadjson(self, myjson):
        error = 0
        for key in myjson.keys():
            print('Unknown keyword "' + str(key) + '" with data "' +
                  str(myjson[key]) + '" found in loadjson')
            error = 1
        return error

#
# The classes below support the .sln file
#


#
# Class to manage a solution file's nested class
#

class NestedProjects(object):
    def __init__(self, name):
        self.name = name
        self.uuid = get_uuid(name + 'NestedProjects')
        self.uuidlist = []

    #
    # Add a uuid to track for this nested project list
    #

    def adduuid(self, input_uuid):
        self.uuidlist.append(input_uuid)

    #
    # Write the record into project record
    #

    def write(self, fileref):
        fileref.write(
            u'Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "' +
            self.name +
            '", "' +
            self.name +
            '", "{' +
            self.uuid +
            '}"\n')
        fileref.write(u'EndProject\n')

    #
    # Inside the GlobalSection(NestedProjects) = preSolution record, output
    # the uuid list this item controls
    #

    def writeGlobalSection(self, fileref):
        for item in self.uuidlist:
            fileref.write(u'\t\t{' + item + '} = {' + self.uuid + '}\n')


#
## Object that contains constants for specific versions of Visual Studio
#
# Most data is shared from different versions of Visual Studio
# but for the contants that differ, they are stored in
# this class
#

class SolutionFile(object):

    def __init__(self, fileversion, solution):
        self.fileversion = fileversion
        self.solution = solution
        self.nestedprojects = []

    #
    ## Add a nested project entry
    #

    def addnestedprojects(self, name):
        entry = NestedProjects(name)
        self.nestedprojects.append(entry)
        return entry

    #
    # Serialize the solution file (Requires UTF-8 encoding)
    #

    def write(self, fp):
        #
        # Save off the UTF-8 header marker
        #
        fp.write(u'\xef\xbb\xbf\n')

        #
        # Save off the format header
        #
        fp.write(u'Microsoft Visual Studio Solution File, Format Version ' +
                 formatversion[self.fileversion.value] + '\n')

        #
        # Save the version of Visual Studio requested
        #

        fp.write(u'# Visual Studio ' + yearversion[self.fileversion.value] + '\n')

        #
        # New lines added for Visual Studio 2013 and 2015 for file versioning
        #

        if self.fileversion == FileVersions.vs2019:
            fp.write(u'VisualStudioVersion = 16.0.28803.202\n')
            fp.write(u'MinimumVisualStudioVersion = 10.0.40219.1\n')

        if self.fileversion == FileVersions.vs2017:
            fp.write(u'VisualStudioVersion = 15.0.26430.15\n')
            fp.write(u'MinimumVisualStudioVersion = 10.0.40219.1\n')

        if self.fileversion == FileVersions.vs2015:
            fp.write(u'VisualStudioVersion = 14.0.25123.0\n')
            fp.write(u'MinimumVisualStudioVersion = 10.0.40219.1\n')

        if self.fileversion == FileVersions.vs2013:
            fp.write(u'VisualStudioVersion = 12.0.31101.0\n')
            fp.write(u'MinimumVisualStudioVersion = 10.0.40219.1\n')

        #
        # If there were any nested projects, output the master list
        #

        for item in self.nestedprojects:
            item.write(fp)

        #
        # Save off the project record
        #

        fp.write(
            u'Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "' + self.solution.name + '", "' +
            self.solution.visualstudio.outputfilename + projectsuffix[self.fileversion.value] +
            '", "{' + self.solution.visualstudio.uuid + '}"\n')
        fp.write(u'EndProject\n')

        #
        # Begin the Global record
        #

        fp.write(u'Global\n')

        #
        # Write out the SolutionConfigurationPlatforms
        #

        fp.write(u'\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n')
        vsplatforms = self.solution.projects[0].platform.get_vs_platform()
        for target in self.solution.projects[0].configurations:
            for item in vsplatforms:
                token = target.name + '|' + item
                fp.write(u'\t\t' + token + ' = ' + token + '\n')
        fp.write(u'\tEndGlobalSection\n')

        #
        # Write out the ProjectConfigurationPlatforms
        #

        fp.write(u'\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n')
        for target in self.solution.projects[0].configurations:
            for item in vsplatforms:
                token = target.name + '|' + item
                fp.write(u'\t\t{' + self.solution.visualstudio.uuid + '}.' + token +
                         '.ActiveCfg = ' + token + '\n')
                fp.write(u'\t\t{' + self.solution.visualstudio.uuid + '}.' + token +
                         '.Build.0 = ' + token + '\n')
        fp.write(u'\tEndGlobalSection\n')

        #
        # Hide nodes section
        #

        fp.write(u'\tGlobalSection(SolutionProperties) = preSolution\n')
        fp.write(u'\t\tHideSolutionNode = FALSE\n')
        fp.write(u'\tEndGlobalSection\n')

        if self.nestedprojects:
            fp.write(u'\tGlobalSection(NestedProjects) = preSolution\n')
            for item in self.nestedprojects:
                item.writeGlobalSection(fp)
            fp.write(u'\tEndGlobalSection\n')

        # Added for 3rd party extensions after 2017 version 3
        if self.fileversion == FileVersions.vs2017:
            fp.write(u'\tGlobalSection(ExtensibilityGlobals) = postSolution\n')
            fp.write(u'\t\tSolutionGuid = {7DEC4DAA-9DC0-4A41-B9C7-01CC0179FDCB}\n')
            fp.write(u'\tEndGlobalSection\n')

        if self.fileversion == FileVersions.vs2019:
            fp.write(u'\tGlobalSection(ExtensibilityGlobals) = postSolution\n')
            fp.write(u'\t\tSolutionGuid = {4E9AC1D3-6227-410D-87DF-35A3C19B79ED}\n')
            fp.write(u'\tEndGlobalSection\n')

        #
        # Close it up!
        #

        fp.write(u'EndGlobal\n')
        return 0

#
# Project file generator (Generates main project file and the filter file)
#


class vsProject(object):

    #
    # Create a project file
    #
    def __init__(self, defaults, codefiles, includedirectories):
        self.defaults = defaults
        # Directories to use for file inclusion
        self.includedirectories = includedirectories
        # Seperate all the files to the types to be generated with
        self.listh = makeprojects.core.pickfromfilelist(codefiles, FileTypes.h)
        self.listcpp = makeprojects.core.pickfromfilelist(codefiles, FileTypes.cpp)
        self.listcpp.extend(makeprojects.core.pickfromfilelist(codefiles, FileTypes.c))
        self.listwindowsresource = makeprojects.core.pickfromfilelist(codefiles, FileTypes.rc)
        self.listhlsl = makeprojects.core.pickfromfilelist(codefiles, FileTypes.hlsl)
        self.listglsl = makeprojects.core.pickfromfilelist(codefiles, FileTypes.glsl)
        self.listx360sl = makeprojects.core.pickfromfilelist(codefiles, FileTypes.x360sl)
        self.listvitacg = makeprojects.core.pickfromfilelist(codefiles, FileTypes.vitacg)
        self.listico = makeprojects.core.pickfromfilelist(codefiles, FileTypes.ico)

    #
    # Write out the project file in the 2010 format
    #

    def writeproject2010(self, fp, solution):
        #
        # Save off the xml header
        #

        fp.write(u'<?xml version="1.0" encoding="utf-8"?>\n')
        if self.defaults.fileversion.value >= FileVersions.vs2015.value:
            toolsversion = '14.0'
        else:
            toolsversion = '4.0'
        fp.write(u'<Project DefaultTargets="Build" ToolsVersion="' + toolsversion +
                 '" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">\n')

        #
        # nVidia Shield projects have a version header
        #

        if self.defaults.platformcode == 'shi':
            fp.write(u'\t<PropertyGroup Label="NsightTegraProject">\n')
            fp.write(u'\t\t<NsightTegraProjectRevisionNumber>11</NsightTegraProjectRevisionNumber>\n')
            fp.write(u'\t</PropertyGroup>\n')

        #
        # Write the project configurations
        #

        fp.write(u'\t<ItemGroup Label="ProjectConfigurations">\n')
        for target in solution.projects[0].configurations:
            for vsplatform in solution.projects[0].platform.get_vs_platform():
                token = target.name + '|' + vsplatform
                fp.write(u'\t\t<ProjectConfiguration Include="' + token + '">\n')
                fp.write(u'\t\t\t<Configuration>' + target.name + '</Configuration>\n')
                fp.write(u'\t\t\t<Platform>' + vsplatform + '</Platform>\n')
                fp.write(u'\t\t</ProjectConfiguration>\n')
        fp.write(u'\t</ItemGroup>\n')

        #
        # Write the project globals
        #

        fp.write(u'\t<PropertyGroup Label="Globals">\n')
        fp.write(u'\t\t<ProjectName>' + solution.name + '</ProjectName>\n')
        deploy_folder = None
        for configuration in solution.projects[0].configurations:
            if configuration.attributes.get('deploy_folder'):
                deploy_folder = configuration.attributes.get('deploy_folder')

        if deploy_folder is not None:
            final = convert_to_windows_slashes(deploy_folder, True)
            fp.write(u'\t\t<FinalFolder>' + final + '</FinalFolder>\n')
        fp.write(u'\t\t<ProjectGuid>{' + self.defaults.uuid + '}</ProjectGuid>\n')
        if self.defaults.fileversion.value >= FileVersions.vs2015.value:
            fp.write(u'\t\t<WindowsTargetPlatformVersion>8.1</WindowsTargetPlatformVersion>\n')
        fp.write(u'\t</PropertyGroup>\n')

        #
        # Default properties
        #

        fp.write(u'\t<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.Default.props" />\n')

        #
        # Add in the platform tool set for Windows targets
        #

        if self.defaults.platformcode == 'win':
            fp.write(u'\t<PropertyGroup Label="Configuration">\n')
            fp.write(u'\t\t<PlatformToolset>' + platformtoolsets[self.defaults.fileversion.value] +
                     '</PlatformToolset>\n')
            fp.write(u'\t</PropertyGroup>\n')

        #
        # Add in the burgerlib includes
        #

        if solution.projects[0].projecttype == ProjectTypes.library:
            fp.write(u'\t<Import Project="$(BURGER_SDKS)\\visualstudio\\burger.libv10.props" Condition="exists(\'$(BURGER_SDKS)\\visualstudio\\burger.libv10.props\')" />\n')
        elif solution.projects[0].projecttype == ProjectTypes.tool:
            fp.write(u'\t<Import Project="$(BURGER_SDKS)\\visualstudio\\burger.toolv10.props" Condition="exists(\'$(BURGER_SDKS)\\visualstudio\\burger.toolv10.props\')" />\n')
        else:
            fp.write(u'\t<Import Project="$(BURGER_SDKS)\\visualstudio\\burger.gamev10.props" Condition="exists(\'$(BURGER_SDKS)\\visualstudio\\burger.gamev10.props\')" />\n')

        fp.write(u'\t<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.props" />\n')

        if self.defaults.platformcode == 'dsi':
            fp.write(u'\t<ImportGroup Label="ExtensionSettings">\n')
            fp.write(u'\t\t<Import Project="$(VCTargetsPath)\\BuildCustomizations\\ctr2_asm.props" Condition="exists(\'$(VCTargetsPath)\\BuildCustomizations\\ctr2_asm.props\')" />\n')
            fp.write(u'\t</ImportGroup>\n')
        else:
            fp.write(u'\t<ImportGroup Label="ExtensionSettings" />\n')

        fp.write(u'\t<ImportGroup Label="PropertySheets">\n')
        fp.write(u'\t\t<Import Project="$(UserRootDir)\\Microsoft.Cpp.$(Platform).user.props" Condition="exists(\'$(UserRootDir)\\Microsoft.Cpp.$(Platform).user.props\')" Label="LocalAppDataPlatform" />\n')
        fp.write(u'\t</ImportGroup>\n')

        fp.write(u'\t<PropertyGroup Label="UserMacros" />\n')

        #
        # Insert compiler settings
        #

        linkerdirectories = list(solution.projects[0].includefolders)
        if self.defaults.platformcode == 'dsi':
            linkerdirectories += [u'$(BURGER_SDKS)\\dsi\\burgerlib']

        if self.includedirectories or \
                linkerdirectories or \
                solution.projects[0].defines:
            fp.write(u'\t<ItemDefinitionGroup>\n')

            #
            # Handle global compiler defines
            #

            if self.includedirectories or \
                    linkerdirectories or \
                    solution.projects[0].defines:
                fp.write(u'\t\t<ClCompile>\n')

                # Include directories
                if self.includedirectories or linkerdirectories:
                    fp.write(u'\t\t\t<AdditionalIncludeDirectories>')
                    for item in self.includedirectories:
                        fp.write(u'$(ProjectDir)' + convert_to_windows_slashes(item) + ';')
                    for item in linkerdirectories:
                        fp.write(convert_to_windows_slashes(item) + ';')
                    fp.write(u'%(AdditionalIncludeDirectories)</AdditionalIncludeDirectories>\n')

                # Global defines
                if solution.projects[0].defines:
                    fp.write(u'\t\t\t<PreprocessorDefinitions>')
                    for define in solution.projects[0].defines:
                        fp.write(define + ';')
                    fp.write(u'%(PreprocessorDefinitions)</PreprocessorDefinitions>\n')

                fp.write(u'\t\t</ClCompile>\n')

            #
            # Handle global linker defines
            #

            if linkerdirectories:
                fp.write(u'\t\t<Link>\n')

                # Include directories
                if linkerdirectories:
                    fp.write(u'\t\t\t<AdditionalLibraryDirectories>')
                    for item in linkerdirectories:
                        fp.write(convert_to_windows_slashes(item) + ';')
                    fp.write(u'%(AdditionalLibraryDirectories)</AdditionalLibraryDirectories>\n')

                fp.write(u'\t\t</Link>\n')

            fp.write(u'\t</ItemDefinitionGroup>\n')

        #
        # This is needed for the PS3 and PS4 targets :(
        #

        if self.defaults.platformcode == 'ps3' or self.defaults.platformcode == 'ps4':
            fp.write(u'\t<ItemDefinitionGroup Condition="\'$(BurgerConfiguration)\'!=\'Release\'">\n')
            fp.write(u'\t\t<ClCompile>\n')
            fp.write(
                u'\t\t\t<PreprocessorDefinitions>_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n')
            fp.write(u'\t\t</ClCompile>\n')
            fp.write(u'\t</ItemDefinitionGroup>\n')
            fp.write(u'\t<ItemDefinitionGroup Condition="\'$(BurgerConfiguration)\'==\'Release\'">\n')
            fp.write(u'\t\t<ClCompile>\n')
            fp.write(
                u'\t\t\t<PreprocessorDefinitions>NDEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n')
            fp.write(u'\t\t</ClCompile>\n')
            fp.write(u'\t</ItemDefinitionGroup>\n')

        #
        # This is needed for Nintendo DSI and 3DS targets :(
        #

        if self.defaults.platformcode == 'dsi':
            fp.write(u'\t<ItemDefinitionGroup>\n')
            fp.write(u'\t<ProjectReference>\n')
            fp.write(u'\t\t<LinkLibraryDependencies>true</LinkLibraryDependencies>\n')
            fp.write(u'\t</ProjectReference>\n')
            fp.write(u'\t\t<ClCompile>\n')
            fp.write(u'\t\t\t<GNU_Extensions>true</GNU_Extensions>\n')
            fp.write(u'\t\t</ClCompile>\n')
            fp.write(u'\t\t<ASM>\n')
            fp.write(u'\t\t\t<GNU_Extensions>true</GNU_Extensions>\n')
            fp.write(u'\t\t</ASM>\n')
            fp.write(u'\t</ItemDefinitionGroup>\n')

            fp.write(u'\t<ItemDefinitionGroup Condition="\'$(BurgerConfiguration)\'==\'Debug\'">\n')
            fp.write(u'\t\t<ClCompile>\n')
            fp.write(u'\t\t\t<PreprocessorDefinitions>_DEBUG;NN_BUILD_DEBUG;NN_COMPILER_RVCT;NN_COMPILER_RVCT_VERSION_MAJOR=$(CTRSDK_RVCT_VER_MAJOR);NN_PROCESSOR_ARM;NN_PROCESSOR_ARM11MPCORE;NN_PROCESSOR_ARM_V6;NN_PROCESSOR_ARM_VFP_V2;NN_HARDWARE_CTR;NN_PLATFORM_CTR;NN_HARDWARE_CTR_TS;NN_SYSTEM_PROCESS;NN_SWITCH_ENABLE_HOST_IO=1;NN_BUILD_VERBOSE;NN_BUILD_NOOPT;NN_DEBUGGER_KMC_PARTNER;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n')
            fp.write(u'\t\t\t<OptimizeLevel>0</OptimizeLevel>\n')
            fp.write(u'\t\t\t<OptimizeRetain>calls</OptimizeRetain>\n')
            fp.write(u'\t\t</ClCompile>\n')
            fp.write(u'\t\t<ASM>\n')
            fp.write(u'\t\t\t<PreprocessorDefinitions>_DEBUG;NN_BUILD_DEBUG;NN_COMPILER_RVCT;NN_COMPILER_RVCT_VERSION_MAJOR=$(CTRSDK_RVCT_VER_MAJOR);NN_PROCESSOR_ARM;NN_PROCESSOR_ARM11MPCORE;NN_PROCESSOR_ARM_V6;NN_PROCESSOR_ARM_VFP_V2;NN_HARDWARE_CTR;NN_PLATFORM_CTR;NN_HARDWARE_CTR_TS;NN_SYSTEM_PROCESS;NN_SWITCH_ENABLE_HOST_IO=1;NN_BUILD_VERBOSE;NN_BUILD_NOOPT;NN_DEBUGGER_KMC_PARTNER;%(PreprocessorDefinitions)</PreprocessorDefinitions>\n')
            fp.write(u'\t\t\t<OptimizeLevel>0</OptimizeLevel>\n')
            fp.write(u'\t\t\t<OptimizeRetain>calls</OptimizeRetain>\n')
            fp.write(u'\t\t</ASM>\n')
            fp.write(u'\t</ItemDefinitionGroup>\n')

            fp.write(u'\t<ItemDefinitionGroup Condition="\'$(BurgerConfiguration)\'!=\'Debug\'">\n')
            fp.write(u'\t\t<ClCompile>\n')
            fp.write(u'\t\t\t<PreprocessorDefinitions Condition="\'$(BurgerConfiguration)\'!=\'Release\'">_DEBUG;NN_BUILD_DEVELOPMENT;NN_COMPILER_RVCT;NN_COMPILER_RVCT_VERSION_MAJOR=$(CTRSDK_RVCT_VER_MAJOR);NN_PROCESSOR_ARM;NN_PROCESSOR_ARM11MPCORE;NN_PROCESSOR_ARM_V6;NN_PROCESSOR_ARM_VFP_V2;NN_HARDWARE_CTR;NN_PLATFORM_CTR;NN_HARDWARE_CTR_TS;NN_SYSTEM_PROCESS;NN_SWITCH_ENABLE_HOST_IO=1;NN_BUILD_VERBOSE;NN_DEBUGGER_KMC_PARTNER</PreprocessorDefinitions>\n')
            fp.write(u'\t\t\t<PreprocessorDefinitions Condition="\'$(BurgerConfiguration)\'==\'Release\'">NDEBUG;NN_BUILD_RELEASE;NN_COMPILER_RVCT;NN_COMPILER_RVCT_VERSION_MAJOR=$(CTRSDK_RVCT_VER_MAJOR);NN_PROCESSOR_ARM;NN_PROCESSOR_ARM11MPCORE;NN_PROCESSOR_ARM_V6;NN_PROCESSOR_ARM_VFP_V2;NN_HARDWARE_CTR;NN_PLATFORM_CTR;NN_HARDWARE_CTR_TS;NN_SYSTEM_PROCESS;NN_SWITCH_DISABLE_DEBUG_PRINT=1;NN_SWITCH_DISABLE_DEBUG_PRINT_FOR_SDK=1;NN_SWITCH_DISABLE_ASSERT_WARNING=1;NN_SWITCH_DISABLE_ASSERT_WARNING_FOR_SDK=1;NN_DEBUGGER_KMC_PARTNER</PreprocessorDefinitions>\n')
            fp.write(u'\t\t\t<OptimizeLevel>3</OptimizeLevel>\n')
            fp.write(u'\t\t\t<OptimizeRetain>none</OptimizeRetain>\n')
            fp.write(u'\t\t</ClCompile>\n')
            fp.write(u'\t\t<ASM>\n')
            fp.write(u'\t\t\t<PreprocessorDefinitions Condition="\'$(BurgerConfiguration)\'!=\'Release\'">_DEBUG;NN_BUILD_DEVELOPMENT;NN_COMPILER_RVCT;NN_COMPILER_RVCT_VERSION_MAJOR=$(CTRSDK_RVCT_VER_MAJOR);NN_PROCESSOR_ARM;NN_PROCESSOR_ARM11MPCORE;NN_PROCESSOR_ARM_V6;NN_PROCESSOR_ARM_VFP_V2;NN_HARDWARE_CTR;NN_PLATFORM_CTR;NN_HARDWARE_CTR_TS;NN_SYSTEM_PROCESS;NN_SWITCH_ENABLE_HOST_IO=1;NN_BUILD_VERBOSE;NN_DEBUGGER_KMC_PARTNER</PreprocessorDefinitions>\n')
            fp.write(u'\t\t\t<PreprocessorDefinitions Condition="\'$(BurgerConfiguration)\'==\'Release\'">NDEBUG;NN_BUILD_RELEASE;NN_COMPILER_RVCT;NN_COMPILER_RVCT_VERSION_MAJOR=$(CTRSDK_RVCT_VER_MAJOR);NN_PROCESSOR_ARM;NN_PROCESSOR_ARM11MPCORE;NN_PROCESSOR_ARM_V6;NN_PROCESSOR_ARM_VFP_V2;NN_HARDWARE_CTR;NN_PLATFORM_CTR;NN_HARDWARE_CTR_TS;NN_SYSTEM_PROCESS;NN_SWITCH_DISABLE_DEBUG_PRINT=1;NN_SWITCH_DISABLE_DEBUG_PRINT_FOR_SDK=1;NN_SWITCH_DISABLE_ASSERT_WARNING=1;NN_SWITCH_DISABLE_ASSERT_WARNING_FOR_SDK=1;NN_DEBUGGER_KMC_PARTNER</PreprocessorDefinitions>\n')
            fp.write(u'\t\t\t<OptimizeLevel>3</OptimizeLevel>\n')
            fp.write(u'\t\t\t<OptimizeRetain>none</OptimizeRetain>\n')
            fp.write(u'\t\t</ASM>\n')
            fp.write(u'\t</ItemDefinitionGroup>\n')

        #
        # Any source files for the item groups?
        #

        if self.listh or self.listcpp or self.listwindowsresource or self.listhlsl or self.listglsl or self.listx360sl or self.listvitacg or self.listico:

            fp.write(u'\t<ItemGroup>\n')

            for item in self.listh:
                fp.write(
                    u'\t\t<ClInclude Include="' +
                    convert_to_windows_slashes(
                        item.filename) +
                    '" />\n')

            for item in self.listcpp:
                fp.write(
                    u'\t\t<ClCompile Include="' +
                    convert_to_windows_slashes(
                        item.filename) +
                    '" />\n')

            for item in self.listwindowsresource:
                fp.write(
                    u'\t\t<ResourceCompile Include="' +
                    convert_to_windows_slashes(
                        item.filename) +
                    '" />\n')

            for item in self.listhlsl:
                fp.write(
                    u'\t\t<HLSL Include="' +
                    convert_to_windows_slashes(
                        item.filename) +
                    '">\n')
                # Cross platform way in splitting the path (MacOS doesn't like windows slashes)
                basename = convert_to_windows_slashes(
                    item.filename).lower().rsplit('\\', 1)[1]
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
                fp.write(
                    u'\t\t<X360SL Include="' +
                    convert_to_windows_slashes(
                        item.filename) +
                    '">\n')
                # Cross platform way in splitting the path (MacOS doesn't like windows slashes)
                basename = item.filename.lower().rsplit('\\', 1)[1]
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
                fp.write(u'\t\t<VitaCGCompile Include="' +
                         convert_to_windows_slashes(item.filename) + '">\n')
                # Cross platform way in splitting the path
                # (MacOS doesn't like windows slashes)
                basename = item.filename.lower().rsplit('\\', 1)[1]
                splitname = os.path.splitext(basename)
                if splitname[0].startswith('vs'):
                    profile = 'sce_vp_psp2'
                else:
                    profile = 'sce_fp_psp2'
                fp.write(u'\t\t\t<TargetProfile>' + profile + '</TargetProfile>\n')
                fp.write(u'\t\t</VitaCGCompile>\n')

            for item in self.listglsl:
                fp.write(
                    u'\t\t<GLSL Include="' +
                    convert_to_windows_slashes(
                        item.filename) +
                    '" />\n')

            if self.defaults.fileversion.value >= FileVersions.vs2015.value:
                chunkname = 'Image'
            else:
                chunkname = 'None'
            for item in self.listico:
                fp.write(
                    u'\t\t<' +
                    chunkname +
                    ' Include="' +
                    convert_to_windows_slashes(
                        item.filename) +
                    '" />\n')

            fp.write(u'\t</ItemGroup>\n')

        #
        # Close up the project file!
        #

        fp.write(u'\t<Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />\n')

        if self.defaults.platformcode == 'dsi':
            fp.write(u'\t<ImportGroup Label="ExtensionTargets">\n')
            fp.write(u'\t\t<Import Project="$(VCTargetsPath)\\BuildCustomizations\\ctr2_asm.targets" Condition="exists(\'$(VCTargetsPath)\\BuildCustomizations\\ctr2_asm.targets\')" />\n')
            fp.write(u'\t\t<Import Project="$(VCTargetsPath)\\BuildCustomizations\\ctr2_items.targets" Condition="exists(\'$(VCTargetsPath)\\BuildCustomizations\\ctr2_items.targets\')" />\n')

            fp.write(u'\t</ImportGroup>\n')
        else:
            fp.write(u'\t<ImportGroup Label="ExtensionTargets" />\n')

        fp.write(u'</Project>\n')
        return 0

    def writefilter(self, fileref):
        """
        Write out the filter file
        """

        #
        # Stock header for the filter
        #

        fileref.write('<?xml version="1.0" encoding="utf-8"?>\n')
        fileref.write('<Project ToolsVersion="4.0" '
                      'xmlns="http://schemas.microsoft.com/developer/msbuild/2003">\n')
        fileref.write('\t<ItemGroup>\n')

        groups = []
        writefiltergroup(fileref, self.listh, groups, u'ClInclude')
        writefiltergroup(fileref, self.listcpp, groups, u'ClCompile')
        writefiltergroup(fileref, self.listwindowsresource, groups,
                         u'ResourceCompile')
        writefiltergroup(fileref, self.listhlsl, groups, u'HLSL')
        writefiltergroup(fileref, self.listx360sl, groups, u'X360SL')
        writefiltergroup(fileref, self.listvitacg, groups, u'VitaCGCompile')
        writefiltergroup(fileref, self.listglsl, groups, u'GLSL')
        # Visual Studio 2015 and later have a "compiler" for ico files
        if self.defaults.fileversion.value >= FileVersions.vs2015.value:
            writefiltergroup(fileref, self.listico, groups, u'Image')
        else:
            writefiltergroup(fileref, self.listico, groups, u'None')

        # Remove all duplicate in the groups
        groupset = sorted(set(groups))

        # Output the group list
        for item in groupset:
            item = convert_to_windows_slashes(item)
            groupuuid = get_uuid(self.defaults.outputfilename + item)
            fileref.write(u'\t\t<Filter Include="' + item + '">\n')
            fileref.write(u'\t\t\t<UniqueIdentifier>{' + groupuuid +
                          '}</UniqueIdentifier>\n')
            fileref.write(u'\t\t</Filter>\n')

        fileref.write(u'\t</ItemGroup>\n')
        fileref.write(u'</Project>\n')

        return len(groupset)


class Project(object):
    """
    Root object for a Visual Studio Code IDE project file
    Created with the name of the project, the IDE code (vc8, v10)
    the platform code (win, ps4)
    """

    def __init__(self, defaults, solution):
        """
        """
        self.defaults = defaults
        self.slnfile = SolutionFile(defaults.fileversion, solution)
        self.projects = []

    def addnestedprojects(self, name):
        """
        Add a nested project into the solution
        """
        return self.slnfile.addnestedprojects(name)

    def writesln(self, fileref):
        """
        Generate a .sln file for Visual Studio
        """
        return self.slnfile.write(fileref)

    def writeproject2010(self, fileref, solution):
        """
        Generate a .vcxproj.filters file for Visual Studio 2010 or higher
        """
        error = 0
        if self.projects:
            for item in self.projects:
                error = item.writeproject2010(fileref, solution)
                break
        return error

    def writefilter(self, fileref):
        """
        Generate a .vcxproj.filters file for Visual Studio 2010 or higher
        """
        count = 0
        if self.projects:
            for item in self.projects:
                count = count + item.writefilter(fileref)
        return count


def generateold(solution, ide):
    """
    Old way
    """
    #
    # Configure the Visual Studio writer to the type
    # of solution requested
    #

    error = solution.visualstudio.defaults(solution)
    if error != 0:
        return error

    #
    # Obtain the list of files of interest to include in
    # the project
    #

    codefiles, includedirectories = solution.getfilelist(
        solution.visualstudio.acceptable)

    #
    # Create a blank project
    #

    project = Project(solution.visualstudio, solution)
    project.projects.append(vsProject(solution.visualstudio, codefiles,
                                      includedirectories))

    #
    # Serialize the solution file and write if changed
    #

    fileref = StringIO()
    project.writesln(fileref)
    filename = os.path.join(solution.working_directory,
                            solution.visualstudio.outputfilename + '.sln')
    if comparefiletostring(filename, fileref):
        if solution.verbose is True:
            print(filename + ' was not changed')
    else:
        perforce_edit(filename)
        fp2 = io.open(filename, 'w')
        fp2.write(fileref.getvalue())
        fp2.close()
    fileref.close()

    #
    # Create the project file
    #

    fileref = StringIO()
    if solution.visualstudio.fileversion.value >= FileVersions.vs2010.value:
        project.writeproject2010(fileref, solution)
        filename = os.path.join(solution.working_directory,
                                solution.visualstudio.outputfilename +
                                projectsuffix[solution.visualstudio.fileversion.value])
        if comparefiletostring(filename, fileref):
            if solution.verbose is True:
                print(filename + ' was not changed')
        else:
            perforce_edit(filename)
            fp2 = io.open(filename, 'w')
            fp2.write(fileref.getvalue())
            fp2.close()
    fileref.close()

    #
    # If it's visual studio 2010 or higher, output the filter file if needed
    #

    if solution.visualstudio.fileversion.value >= FileVersions.vs2010.value:

        fileref = StringIO()
        count = project.writefilter(fileref)
        filename = os.path.join(solution.working_directory,
                                solution.visualstudio.outputfilename + '.vcxproj.filters')

        # No groups found?
        if count == 0:
            # Just delete the file
            delete_file(filename)
        else:
            # Did it change?
            if comparefiletostring(filename, fileref):
                if solution.verbose is True:
                    print(filename + ' was not changed')
            else:
                # Update the file
                perforce_edit(filename)
                fp2 = io.open(filename, 'w')
                fp2.write(fileref.getvalue())
                fp2.close()
        fileref.close()

    return 0

########################################


def generate_solution_file(solution_lines, solution):
    """
    Serialize the solution file into a string array.

    This function generates SLN files for all versions of Visual Studio.
    It assumes the text file will be encoded using UTF-8 character encoding
    so the resulting file will be pre-pended with a UTF-8 Byte Order Mark (BOM)
    for Visual Studio 2005 or higher.

    Note:
        Byte Order Marks are not supplied by this function.

    Args:
        solution_lines: List to insert string lines.
        solution: Reference to the raw solution record
    Returns:
        Zero on success, non-zero on error.
    """

    # Save off the format header for the version of Visual Studio being generated

    headers = {
        IDETypes.vs2003: (
            'Microsoft Visual Studio Solution File, Format Version 8.00',
        ),
        IDETypes.vs2005: (
            '',
            'Microsoft Visual Studio Solution File, Format Version 9.00',
            '# Visual Studio 2005'),
        IDETypes.vs2008: (
            '',
            'Microsoft Visual Studio Solution File, Format Version 10.00',
            '# Visual Studio 2008'),
        IDETypes.vs2010: (
            '',
            'Microsoft Visual Studio Solution File, Format Version 11.00',
            '# Visual Studio 2010'),
        IDETypes.vs2012: (
            '',
            'Microsoft Visual Studio Solution File, Format Version 12.00',
            '# Visual Studio 2012'),
        IDETypes.vs2013: (
            '',
            'Microsoft Visual Studio Solution File, Format Version 12.00',
            '# Visual Studio 2013',
            'VisualStudioVersion = 12.0.31101.0',
            'MinimumVisualStudioVersion = 10.0.40219.1'),
        IDETypes.vs2015: (
            '',
            'Microsoft Visual Studio Solution File, Format Version 12.00',
            '# Visual Studio 14',
            'VisualStudioVersion = 14.0.25123.0',
            'MinimumVisualStudioVersion = 10.0.40219.1'),
        IDETypes.vs2017: (
            '',
            'Microsoft Visual Studio Solution File, Format Version 12.00',
            '# Visual Studio 15',
            'VisualStudioVersion = 15.0.28307.645',
            'MinimumVisualStudioVersion = 10.0.40219.1'),
        IDETypes.vs2019: (
            '',
            'Microsoft Visual Studio Solution File, Format Version 12.00',
            '# Visual Studio Version 16',
            'VisualStudioVersion = 16.0.28803.452',
            'MinimumVisualStudioVersion = 10.0.40219.1'),
    }

    # Insert the header to the output stream
    header = headers.get(solution.ide)
    solution_lines.extend(header)

    # Output each project file included in the solution
    # This hasn't changed since Visual Studio 2003
    for project in solution.projects:

        # Save off the project record
        solution_lines.append(
            'Project("{{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}}") = "{}", "{}", "{{{}}}"'.format(
                project.name,
                project.attributes['vs_output_filename'],
                project.attributes['vs_uuid']))

        # Write out the dependencies, if any
        solution_lines.append('\tProjectSection(ProjectDependencies) = postProject')
        for dependent in project.projects:
            solution_lines.append('\t\t{{{0}}} = {{{0}}}'.format(dependent.attributes['vs_uuid']))
        solution_lines.append('\tEndProjectSection')
        solution_lines.append('EndProject')

    # Begin the Global record
    solution_lines.append('Global')

    # Visual Studio 2003 format is unique, write it out in its
    # own exporter
    if solution.ide == IDETypes.vs2003:

        # Only output if there are attached projects, if there are
        # no projects, there is no need to output platforms
        config_list = []
        for project in solution.projects:
            for configuration in project.configurations:
                # Visual Studio 2003 doesn't support 64 bit compilers, so ignore
                # x64 platforms
                if configuration.platform == PlatformTypes.win64:
                    continue
                entry = configuration.name
                # Ignore duplicates
                if entry not in config_list:
                    config_list.append(entry)

        # List the configuration pairs (Like Xbox and Win32)
        solution_lines.append('\tGlobalSection(SolutionConfiguration) = preSolution')
        for entry in config_list:
            # Since Visual Studio 2003 doesn't support Platform/Configuration pairing,
            # it's faked with a space
            solution_lines.append('\t\t{0} = {0}'.format(entry))
        solution_lines.append('\tEndGlobalSection')

        # List all of the projects/configurations
        solution_lines.append('\tGlobalSection(ProjectConfiguration) = postSolution')
        for project in solution.projects:
            for configuration in project.configurations:
                # Visual Studio 2003 doesn't support 64 bit compilers, so ignore
                # x64 platforms
                if configuration.platform == PlatformTypes.win64:
                    if solution.verbose:
                        print('Visual Studio 2003 does not support platform Win64, skipped')
                    continue
                # Using the faked Platform/Configuration pair used above, create the appropriate
                # pairs here and match them up.
                platform = configuration.platform.get_vs_platform()[0]
                solution_lines.append(
                    '\t\t{{{0}}}.{1}.ActiveCfg = {1}|{2}'.format(
                        project.attributes['vs_uuid'],
                        configuration.name, platform))
                solution_lines.append('\t\t{{{0}}}.{1}.Build.0 = {1}|{2}'.format(
                    project.attributes['vs_uuid'], configuration.name, platform))
        solution_lines.append('\tEndGlobalSection')

        # Put in stubs for these records.
        solution_lines.append('\tGlobalSection(ExtensibilityGlobals) = postSolution')
        solution_lines.append('\tEndGlobalSection')

        solution_lines.append('\tGlobalSection(ExtensibilityAddIns) = postSolution')
        solution_lines.append('\tEndGlobalSection')

    # All other versions of Visual Studio 2005 and later use this format
    # for the configurations
    else:

        if solution.projects:
            # Write out the SolutionConfigurationPlatforms for all other versions of
            # Visual Studio

            solution_lines.append('\tGlobalSection(SolutionConfigurationPlatforms) = preSolution')
            for project in solution.projects:
                for configuration in project.configurations:
                    solution_lines.append(
                        '\t\t{0}|{1} = {0}|{1}'.format(
                            configuration.name,
                            configuration.platform.get_vs_platform()[0]))
            solution_lines.append('\tEndGlobalSection')

            # Write out the ProjectConfigurationPlatforms
            solution_lines.append('\tGlobalSection(ProjectConfigurationPlatforms) = postSolution')

            for project in solution.projects:
                for configuration in project.configurations:
                    solution_lines.append(
                        '\t\t{{{0}}}.{1}|{2}.ActiveCfg = {1}|{2}'.format(
                            project.attributes['vs_uuid'],
                            configuration.name,
                            configuration.platform.get_vs_platform()[0]))
                    solution_lines.append(
                        '\t\t{{{0}}}.{1}|{2}.Build.0 = {1}|{2}'.format(
                            project.attributes['vs_uuid'],
                            configuration.name,
                            configuration.platform.get_vs_platform()[0]))

            solution_lines.append('\tEndGlobalSections')

        # Hide nodes section
        solution_lines.append('\tGlobalSection(SolutionProperties) = preSolution')
        solution_lines.append('\t\tHideSolutionNode = FALSE')
        solution_lines.append('\tEndGlobalSection')

        if solution.ide == IDETypes.vs2017:
            solution_lines.append('\tGlobalSection(ExtensibilityGlobals) = postSolution')
            solution_lines.append('\t\tSolutionGuid = {DD9C6A72-2C1C-45F2-9450-8BE7001FEE33}')
            solution_lines.append('\tEndGlobalSection')

        if solution.ide == IDETypes.vs2019:
            solution_lines.append('\tGlobalSection(ExtensibilityGlobals) = postSolution')
            solution_lines.append('\t\tSolutionGuid = {6B996D51-9872-4B32-A08B-EBDBC2A3151F}')
            solution_lines.append('\tEndGlobalSection')

    # Close it up!
    solution_lines.append('EndGlobal')
    return 0

########################################


class VS2003VisualStudioProject():
    def __init__(self, project):
        """
        Init
        """

        self.project_type = 'Visual C++'
        if project.solution.ide == IDETypes.vs2003:
            version = '7.10'
        elif project.solution.ide == IDETypes.vs2005:
            version = '8.00'
        else:
            version = '9.00'
        self.version = version
        self.name = project.name
        self.guid = project.attributes['vs_uuid']
        self.keyword = 'Win32Proj'

    def generate(self, project_lines):
        project_lines.extend(VS2003XML('VisualStudioProject'))



########################################


class VS2003vcproj():
    """
    Visual Studio 2003-2008 formatter
    This record instructs how to write a Visual 2003-2008 format vcproj file
    """

    def __init__(self, project):
        """
        Set the defaults
        """
        self.project = project
        self.project_type = 'Visual C++'
        self.version = '7.10'
        self.keyword = 'Win32Proj'
        self.configurations = []
        self.references = []
        self.files = []
        self.globals = []
        for vsplatform in project.platform.get_vs_platform():

            #
            # Visual Studio 2003 doesn't support 64 bit compilers, so ignore
            # x64 platforms
            #

            if vsplatform == 'x64':
                continue

            #
            # Create the configuration records
            #

            for configuration in project.configurations:
                self.configurations.append(
                    VS2003Configuration(
                        project,
                        configuration.name,
                        vsplatform))

    def generate(self, project_lines):
        """
        Write
        """

        # Save off the UTF-8 header marker (Needed for 2003 only)
        project_lines.append('<?xml version="1.0" encoding="UTF-8"?>')

        # Write out the enclosing XML for the project
        project_lines.append('<VisualStudioProject')

        if self.project_type:
            project_lines.append('\tProjectType="' + self.project_type + '"')

        if self.version:
            project_lines.append('\tVersion="' + self.version + '"')

        project_lines.append('\tName="' + self.project.name + '"')
        project_lines.append('\tProjectGUID="{' + self.project.attributes['vs_uuid'] + '}"')
        project_lines.append('\tKeyword="' + self.keyword + '">')

        # Write the project platforms
        project_lines.append('\t<Platforms>')
        for vsplatform in self.project.platform.get_vs_platform()[0]:

            # Ignore x64 platforms on Visual Studio 2003
            if vsplatform == 'x64':
                continue

            project_lines.append('\t\t<Platform Name="' + vsplatform + '"/>')
        project_lines.append('\t</Platforms>')

        # Write out the Configuration records
        project_lines.append('\t<Configurations>')
        for configuration in self.configurations:
            configuration.write(project_lines)
        project_lines.append('\t</Configurations>')

        # Write out the Reference records
        project_lines.append('\t<References>')
        project_lines.append('\t</References>')

        # Write out the files references
        project_lines.append('\t<Files>')
        project_lines.append('\t</Files>')

        # Write out the Globals records
        project_lines.append('\t<Globals>')
        project_lines.append('\t</Globals>')

        # Wrap up with the closing of the XML token
        project_lines.append('</VisualStudioProject>')

########################################


def generate(solution, perforce=False, verbose=False):
    """
    Create a solution and project(s) file for Visual Studio.

    Given a Solution object, create an appropriate Visual Studio solution
    and project files to allow this project to build.

    Args:
        solution: Solution instance.
        perforce: True if perforce source control is active
        verbose: True if verbose output is desired

    Returns:
        Zero if no error, non-zero on error.
    """

    # For starters, generate the UUID and filenames for the solution file
    # for visual studio, since each solution and project file generate
    # seperately

    # Get the IDE name code
    idecode = solution.ide.get_short_code()

    # Get the platform code
    temp_list = []
    for project in solution.projects:
        temp_list.extend(project.configurations)
    platformcode = platformtype_short_code(temp_list)

    # Create the final filename for the Visual Studio Solution file
    solution_filename = ''.join((solution.name, idecode, platformcode, '.sln'))

    # Older versions of Visual studio use the .vcproj extension
    # instead of the .vcxproj extension

    project_filename_suffix = '.vcxproj'
    if solution.ide in (IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008):
        project_filename_suffix = '.vcproj'

    # Iterate over the project files and create the filenames
    for project in solution.projects:
        platformcode = platformtype_short_code(project.configurations)
        project.attributes['vs_output_filename'] = ''.join((
            project.name, idecode, platformcode, project_filename_suffix))
        project.attributes['vs_uuid'] = get_uuid(project.attributes['vs_output_filename'])

    # Write to memory for file comparison
    solution_lines = []
    error = generate_solution_file(solution_lines, solution)
    if error:
        return error

    save_text_file_if_newer(
        os.path.join(solution.working_directory, solution_filename),
        solution_lines,
        bom=solution.ide != IDETypes.vs2003,
        perforce=perforce,
        verbose=verbose)

    # Now that the solution file was generated, create the individual project
    # files using the format appropriate for the selected IDE

    if solution.ide == IDETypes.vs2003:
        for item in solution.projects:
            exporter = VS2003vcproj(item)
            project_lines = []
            exporter.generate(project_lines)
            save_text_file_if_newer(
                os.path.join(solution.working_directory, item.attributes['vs_output_filename']),
                project_lines,
                perforce=perforce,
                verbose=verbose)
    return 0
