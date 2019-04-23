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
import uuid
import io
from io import StringIO
from enum import Enum
import makeprojects.core
import burger
from makeprojects import AutoIntEnum, FileTypes, ProjectTypes, \
    ConfigurationTypes, IDETypes

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

#
## Convert a string to a UUUD
#
# Given a project name string, create a 128 bit unique hash for
# Visual Studio
#
# \param input_str Unicode string of the filename to convert into a hash
#
# \return A string in the format of CF994A05-58B3-3EF5-8539-E7753D89E84F
#


def calcuuid(input_str):
    if burger.PY2:
        return unicode(uuid.uuid3(uuid.NAMESPACE_DNS, input_str.encode('utf-8'))).upper()
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, input_str)).upper()

#
## Helper class to hold an array of strings that are joined
# by semicolons
#

class SemicolonArray(object):
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

    #
    ## Output the string with UTF-8 encoding
    #

    def __str__(self):
        return unicode(self).encode('utf-8')

    #
    ## Add a string to the array
    #

    def append(self, entry):
        self.entries.append(entry)





#
## Helper class to output a Tool record for Visual Studio 2003-2008
#
# In Visual Studio project files from version 2003 to 2008, Tool
# XML records were used for settings for each and every compiler tool
#

class Tool2003(object):

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
            if item[1] != None:
                output += '\n' + self.tabstring + '\t' + item[0] + '="' + unicode(item[1]) + '"'

        # Close off the XML and return the final string
        return output + '/>\n'

    #
    ## Output the string with UTF-8 encoding
    #

    def __str__(self):
        return unicode(self).encode('utf-8')

    #
    ## Scan the list of entries and set the value to the new
    # value
    #
    # If the value was not found, it will be appended to the list
    #
    # \param name String of the entry to match
    # \param newvalue Value to substitute
    #

    def setvalue(self, name, newvalue):
        for item in self.entries:
            if item[0] == name:
                item[1] = newvalue
                return

        # Not found? Add the entry and then exit
        self.entries.append([name, newvalue])

    #
    ## Remove an entry
    #
    # If the value is in the list, remove it.
    #
    # \param name String of the entry to remove
    #

    def removeentry(self, name):
        i = 0
        while i < len(self.entries):
            # Match?
            if self.entries[i][0] == name:
                # Remove the entry and exit
                del self.entries[i]
                return

            # Next entry
            i += 1





#
# Visual Studio 2003 VCCLCompilerTool record
#

class VCCLCompilerTool(Tool2003):
    def __init__(self):
        entries = [""" General menu """ \
            ['AdditionalIncludeDirectories', SemicolonArray()], \
            ['AdditionalUsingDirectories', None], \
            ['SuppressStartupBanner', 'TRUE'], \
            ['DebugInformationFormat', '3'], \
            ['WarningLevel', '4'], \
            ['Detect64BitPortabilityProblems', 'TRUE'], \
            ['WarnAsError', None], \

            """ Optimization menu """ \
            ['Optimization', '2'], \
            ['GlobalOptimizations', None], \
            ['InlineFunctionExpansion', '2'], \
            ['EnableIntrinsicFunctions', 'TRUE'], \
            ['ImproveFloatingPointConsistency', 'TRUE'], \
            ['FavorSizeOrSpeed', '1'], \
            ['OmitFramePointers', 'TRUE'], \
            ['EnableFiberSafeOptimizations', 'TRUE'], \
            ['OptimizeForProcessor', None], \
            ['OptimizeForWindowsApplication', None], \

            """ Preprocess menu """ \
            ['PreprocessorDefinitions', None], \
            ['IgnoreStandardIncludePath', None], \
            ['GeneratePreprocessedFile', None], \
            ['KeepComments', None], \

            """ Code generation menu  """ \
            ['StringPooling', 'TRUE'], \
            ['MinimalRebuild', 'TRUE'], \
            ['ExceptionHandling', '0'], \
            ['SmallerTypeCheck', None], \
            ['BasicRuntimeChecks', None], \
            ['RuntimeLibrary', '1'], \
            ['StructMemberAlignment', '4'], \
            ['BufferSecurityCheck', 'FALSE'], \
            ['EnableFunctionLevelLinking', 'TRUE'], \
            ['EnableEnhancedInstructionSet', None], \

            """ Language extensions menu """ \
            ['DisableLanguageExtensions', None], \
            ['DefaultCharIsUnsigned', None], \
            ['TreatWChar_tAsBuiltInType', None], \
            ['ForceConformanceInForLoopScope', None], \
            ['RuntimeTypeInfo', 'FALSE'], \

            """ Precompiled header menu """ \
            ['UsePrecompiledHeader', None], \
            ['PrecompiledHeaderThrough', None], \
            ['PrecompiledHeaderFile', None], \

            """ Output files menu """ \
            ['ExpandAttributedSource', None], \
            ['AssemblerOutput', None], \
            ['AssemblerListingLocation', None], \
            ['ObjectFile', None], \
            ['ProgramDataBaseFileName', '$(OutDir)\\$(TargetName).pdb'], \

            """ Browse information menu """ \
            ['BrowseInformation', None], \
            ['BrowseInformationFile', None], \

            """ Advanced menu """ \
            ['CallingConvention', '1'], \
            ['CompileAs', '2'], \
            ['DisableSpecificWarnings', '4201'], \
            ['ForcedIncludeFile', None], \
            ['ForcedUsingFiles', None], \
            ['ShowIncludes', None], \
            ['UndefinePreprocessorDefinitions', None], \
            ['UndefineAllPreprocessorDefinitions', None], \

            """ Command line menu """ \
            ['AdditionalOptions', None] \
        ]
        Tool2003.__init__(self, name='VCCLCompilerTool', entries=entries)



#
# Visual Studio 2003 VCCustomBuildTool record
#

class VCCustomBuildTool(Tool2003):
    def __init__(self):
        entries = [ \
            """ General menu """ \
            ['Description', None], \
            ['CommandLine', None], \
            ['AdditionalDependencies', None], \
            ['Outputs', None] \
        ]
        Tool2003.__init__(self, name='VCCustomBuildTool', entries=entries)

#
# Visual Studio 2003 VCLinkerTool
#

class VCLinkerTool(Tool2003):
    def __init__(self):
        entries = [ \
            """ General menu """ \
            ['OutputFile', '&quot;$(OutDir)unittestsvc8w32dbg.exe&quot;'], \
            ['ShowProgress', None], \
            ['Version', None], \
            ['LinkIncremental', 'TRUE'], \
            ['SuppressStartupBanner', None], \
            ['IgnoreImportLibrary', None], \
            ['RegisterOutput', None], \
            ['AdditionalLibraryDirectories', SemicolonArray( \
                [ \
                    '$(BURGER_SDKS)\\windows\\perforce', \
                    '$(BURGER_SDKS)\\windows\\burgerlib', \
                    '$(BURGER_SDKS)\\windows\\opengl' \
                ] \
            )], \

            """ Input menu """ \
            ['AdditionalDependencies', 'burgerlibvc8w32dbg.lib'], \
            ['IgnoreAllDefaultLibraries', None], \
            ['IgnoreDefaultLibraryNames', None], \
            ['ModuleDefinitionFile', None], \
            ['AddModuleNamesToAssembly', None], \
            ['EmbedManagedResourceFile', None], \
            ['ForceSymbolReferences', None], \
            ['DelayLoadDLLs', None], \

            """ Debugging menu """ \
            ['GenerateDebugInformation', 'TRUE'], \
            ['ProgramDatabaseFile', None], \
            ['StripPrivateSymbols', None], \
            ['GenerateMapFile', None], \
            ['MapFileName', None], \
            ['MapExports', None], \
            ['MapLines', None], \
            ['AssemblyDebug', None], \

            """ System menu """ \
            ['SubSystem', '1'], \
            ['HeapReserveSize', None], \
            ['HeapCommitSize', None], \
            ['StackReserveSize', None], \
            ['StackCommitSize', None], \
            ['LargeAddressAware', None], \
            ['TerminalServerAware', None], \
            ['SwapRunFromCD', None], \
            ['SwapRunFromNet', None], \

            """ Optimization """ \
            ['OptimizeReferences', '2'], \
            ['EnableCOMDATFolding', '2'], \
            ['OptimizeForWindows98', None], \
            ['FunctionOrder', None], \

            """ Embedded MIDL menu """ \
            ['MidlCommandFile', None], \
            ['IgnoreEmbeddedIDL', None], \
            ['MergedIDLBaseFileName', None], \
            ['TypeLibraryFile', None], \
            ['TypeLibraryResourceID', None], \

            """ Advanced menu """ \
            ['EntryPointSymbol', None], \
            ['ResourceOnlyDLL', None], \
            ['SetChecksum', None], \
            ['BaseAddress', None], \
            ['FixedBaseAddress', None], \
            ['TurnOffAssemblyGeneration', None], \
            ['SupportUnloadOfDelayLoadedDLL', None], \
            ['ImportLibrary', None], \
            ['MergeSections', None], \
            ['TargetMachine', '1'], \

            """ Command line menu """ \
            ['AdditionalOptions', None] \
        ]
        Tool2003.__init__(self, name='VCLinkerTool', entries=entries)


#
## Visual Studio 2003 for the MIDL tool
#

class VCMIDLTool(Tool2003):
    def __init__(self):
        Tool2003.__init__(self, name='VCMIDLTool')



class VCPostBuildEventTool(Tool2003):
    def __init__(self):
        entries = [ \
            """ General menu """ \
            ['Description', None], \
            ['CommandLine', None], \
            ['ExcludedFromBuild', None] \
        ]
        Tool2003.__init__(self, name='VCPostBuildEventTool', entries=entries)



class VCPreBuildEventTool(Tool2003):
    def __init__(self):
        entries = [ \
            """ General menu """ \
            ['Description', None], \
            ['CommandLine', None], \
            ['ExcludedFromBuild', None] \
        ]
        Tool2003.__init__(self, name='VCPreBuildEventTool', entries=entries)


class VCPreLinkEventTool(Tool2003):
    def __init__(self):
        entries = [ \
            """ General menu """ \
            ['Description', None], \
            ['CommandLine', None], \
            ['ExcludedFromBuild', None] \
        ]
        Tool2003.__init__(self, name='VCPreLinkEventTool', entries=entries)


class VCResourceCompilerTool(Tool2003):
    def __init__(self):
        Tool2003.__init__(self, name='VCResourceCompilerTool')


class VCWebServiceProxyGeneratorTool(Tool2003):
    def __init__(self):
        Tool2003.__init__(self, name='VCWebServiceProxyGeneratorTool')


class VCXMLDataGeneratorTool(Tool2003):
    def __init__(self):
        Tool2003.__init__(self, name='VCXMLDataGeneratorTool')


class VCWebDeploymentTool(Tool2003):
    def __init__(self):
        Tool2003.__init__(self, name='VCWebDeploymentTool')

class VCManagedWrapperGeneratorTool(Tool2003):
    def __init__(self):
        Tool2003.__init__(self, name='VCManagedWrapperGeneratorTool')

class VCAuxiliaryManagedWrapperGeneratorTool(Tool2003):
    def __init__(self):
        Tool2003.__init__(self, name='VCAuxiliaryManagedWrapperGeneratorTool')

class XboxDeploymentTool(Tool2003):
    def __init__(self):
        Tool2003.__init__(self, name='XboxDeploymentTool')

class XboxImageTool(Tool2003):
    def __init__(self):
        Tool2003.__init__(self, name='XboxImageTool')



#
# Configuration records
#

class VS2003Configuration(object):

    #
    # Initialize a Visual Studio 2003 configuration record
    #

    def __init__(self, project, configuration, vsplatform):
        self.project = project
        self.configuration = configuration
        self.vsplatform = vsplatform

        self.entries = [ \
            ['OutputDirectory', 'bin\\'], \
            ['IntermediateDirectory', 'temp\\'], \
            ['ConfigurationType', '1'], \
            ['UseOfMFC', '0'], \
            ['ATLMinimizesCRunTimeLibraryUsage', 'false'], \
            ['CharacterSet', '1'], \
            ['DeleteExtensionsOnClean', None], \
            ['ManagedExtensions', None], \
            ['WholeProgramOptimization', None], \
            ['ReferencesPath', None] \
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

        fileref.write(u'\t\t<Configuration')
        fileref.write(u'\n\t\t\tName="' + self.configuration + '|' + self.vsplatform + '"')

        for item in self.entries:
            if item[1] != None:
                fileref.write(u'\n\t\t\t' + item[0] + '="' + item[1] + '"')

        fileref.write(u'>\n')

        for tool in self.tools:
            fileref.write(unicode(tool))

        fileref.write(u'\t\t</Configuration>\n')

#
# Visual Studio 2003 formatter
# This record instructs how to write a Visual 2003 format vcproj file
#

class VS2003vcproj(object):

    #
    # Set the defaults
    #

    def __init__(self, project):
        self.project = project
        self.ProjectType = 'Visual C++'
        self.Version = '7.10'
        self.Keyword = 'Win32Proj'
        self.configurations = []

        for vsplatform in project.platform.getvsplatform():

            #
            # Visual Studio 2003 doesn't support 64 bit compilers, so ignore
            # x64 platforms
            #

            if vsplatform == 'x64':
                continue

            #
            # Create the configuration records
            #

            for configuration in project.solution.configurations:
                self.configurations.append(VS2003Configuration(project, configuration, vsplatform))


    def write(self, fp):

        #
        # Save off the UTF-8 header marker (Needed for 2003 only)
        #

        fp.write(u'\xef\xbb\xbf')
        fp.write(u'<?xml version="1.0" encoding="UTF-8"?>\n')

        #
        # Write out the enclosing XML for the project
        #

        fp.write(u'<VisualStudioProject')

        if self.ProjectType != None:
            fp.write(u'\n\tProjectType="' + self.ProjectType + '"')

        if self.Version != None:
            fp.write(u'\n\tVersion="' + self.Version + '"')

        fp.write(u'\n\tName="' + self.project.projectname + '"')
        fp.write(u'\n\tProjectGUID="{' + self.project.visualstudio.uuid + '}"')

        if self.Keyword != None:
            fp.write(u'\n\tKeyword="' + self.Keyword + '"')

        #
        # Close the XML token
        #
        fp.write(u'>\n')

        #
        # Write the project platforms
        #

        fp.write(u'\t<Platforms>\n')
        for vsplatform in self.project.platform.getvsplatform():

            # Ignore x64 platforms on Visual Studio 2003
            if vsplatform == 'x64':
                continue

            fp.write(u'\t\t<Platform Name="' + vsplatform + '"/>\n')
        fp.write(u'\t</Platforms>\n')

        #
        # Write out the Configuration records
        #

        fp.write(u'\t<Configurations>\n')

        for configuration in self.configurations:
            configuration.write(fp)

        fp.write(u'\t</Configurations>\n')

        #
        # Write out the Reference records
        #

        fp.write(u'\t<References>\n')
        fp.write(u'\t</References>\n')

        #
        # Write out the files references
        #

        fp.write(u'\t<Files>\n')
        fp.write(u'\t</Files>\n')

        #
        # Write out the Globals records
        #

        fp.write(u'\t<Globals>\n')
        fp.write(u'\t</Globals>\n')

        #
        # Wrap up with the closing of the XML token
        #

        fp.write(u'</VisualStudioProject>\n')

#
## Serialize the solution file (Requires UTF-8 encoding)
#
# This function generates SLN files for all versions of Visual Studio.
# It assumes the text file will be encoded using UTF-8 character encoding
# so the resulting file will be pre-pended with a UTF-8 Byte Order Mark (BOM)
#
# \param fp File record to stream out the output
# \param solution Reference to the raw solution record
# \param ide IDE enumeration of IDETypes which determine which version
#         of Visual Studio this solution file will be made for.
#

def generatesolutionfile(fp, solution, ide):

    #
    # Use UTF 8 encoding, so start with a UTF-8 byte mark
    #

    fp.write(u'\xef\xbb\xbf\n')

    #
    # Save off the format header for the version of Visual Studio being generated
    #

    if ide == IDETypes.vs2003:
        fp.write(u'Microsoft Visual Studio Solution File, Format Version 8.00\n')

    elif ide == IDETypes.vs2005:
        fp.write(u'Microsoft Visual Studio Solution File, Format Version 9.00\n# Visual Studio 2005\n')

    elif ide == IDETypes.vs2008:
        fp.write(u'Microsoft Visual Studio Solution File, Format Version 10.00\n# Visual Studio 2008\n')

    elif ide == IDETypes.vs2010:
        fp.write(u'Microsoft Visual Studio Solution File, Format Version 11.00\n# Visual Studio 2010\n')

    else:

        # All other version use a standarded solution file (About damn time)

        fp.write(u'Microsoft Visual Studio Solution File, Format Version 12.00\n# Visual Studio ')
        if ide == IDETypes.vs2012:
            fp.write(u'2012\n')

        # Versions later than 2012 have mininum and recommended version information
        # (About damn time!)

        elif ide == IDETypes.vs2013:
            fp.write(u'2013\nVisualStudioVersion = 12.0.31101.0\n')
            fp.write(u'MinimumVisualStudioVersion = 10.0.40219.1\n')
        elif ide == IDETypes.vs2015:
            # Visual studio 2015
            fp.write(u'14\nVisualStudioVersion = 14.0.25123.0\n')
            fp.write(u'MinimumVisualStudioVersion = 10.0.40219.1\n')
        elif ide == IDETypes.vs2017:
            # Visual studio 2017
            fp.write(u'15\nVisualStudioVersion = 15.0.26430.15\n')
            fp.write(u'MinimumVisualStudioVersion = 10.0.40219.1\n')
        else:
            # Visual studio 2019 or later
            fp.write(u'Version 16\nVisualStudioVersion = 16.0.28803.202\n')
            fp.write(u'MinimumVisualStudioVersion = 10.0.40219.1\n')

    #
    # Output each project file included in the solution
    #
    # This hasn't changed since Visual Studio 2003
    #

    for project in solution.projects:

        #
        # Save off the project record
        #

        fp.write(u'Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "' + project.projectname + \
            '", "' + project.visualstudio.outputfilename + '", "{' + project.visualstudio.uuid + '}"\n')

        # Write out the dependencies, if any
        fp.write(u'\tProjectSection(ProjectDependencies) = postProject\n')
        for dependent in project.dependentprojects:
            fp.write(u'\t\t{' + dependent.visualstudio.uuid + '} = {' + dependent.visualstudio.uuid + '}\n')
        fp.write(u'\tEndProjectSection\n')
        fp.write(u'EndProject\n')

    #
    # Begin the Global record
    #

    fp.write(u'Global\n')

    #
    # Visual Studio 2003 format is unique, write it out in its
    # own exporter
    #

    if ide == IDETypes.vs2003:

        #
        # List the configuration pairs (Like Xbox and Win32)
        #

        fp.write(u'\tGlobalSection(SolutionConfiguration) = preSolution\n')

        #
        # Only output if there are attached projects, if there are
        # no projects, there is no need to output platforms
        #

        if solution.projects:
            for platform in solution.platform.getvsplatform():

                #
                # Visual Studio 2003 doesn't support 64 bit compilers, so ignore
                # x64 platforms
                #

                if platform == 'x64':
                    continue

                #
                # Since Visual Studio 2003 doesn't support Platform/Configuration pairing,
                # it's faked with a space
                #

                for configuration in solution.configurations:
                    fp.write(u'\t\t' + configuration + ' ' + platform + ' = ' + configuration + \
                        ' ' + platform + '\n')

        fp.write(u'\tEndGlobalSection\n')

        #
        # List all of the projects/configurations
        #

        fp.write(u'\tGlobalSection(ProjectConfiguration) = postSolution\n')

        for project in solution.projects:
            for platform in solution.platform.getvsplatform():

                #
                # Visual Studio 2003 doesn't support 64 bit compilers
                #

                if platform == 'x64':
                    continue

                #
                # Using the faked Platform/Configuration pair used above, create the appropriate
                # pairs here and match them up.
                #

                for configuration in solution.configurations:
                    tokenwithspace = configuration + ' ' + platform
                    token = configuration + '|' + platform
                    fp.write(u'\t\t\t{' + project.visualstudio.uuid + '}.' + tokenwithspace + \
                        '.ActiveCfg = ' + token + '\n')
                    fp.write(u'\t\t\t{' + project.visualstudio.uuid + '}.' + tokenwithspace + \
                        '.Build.0 = ' + token + '\n')

        fp.write(u'\tEndGlobalSection\n')

        #
        # Put in stubs for these records.
        #

        fp.write(u'\tGlobalSection(ExtensibilityGlobals) = postSolution\n')
        fp.write(u'\tEndGlobalSection\n')

        fp.write(u'\tGlobalSection(ExtensibilityAddIns) = postSolution\n')
        fp.write(u'\tEndGlobalSection\n')

    #
    # All other versions of Visual Studio 2005 and later use this format
    # for the configurations
    #

    else:

        if solution.projects:
            #
            # Write out the SolutionConfigurationPlatforms for all other versions of
            # Visual Studio
            #

            fp.write(u'\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n')

            for configuration in solution.configurations:
                for platform in solution.platform.getvsplatform():
                    token = configuration + '|' + platform
                    fp.write(u'\t\t' + token + ' = ' + token + '\n')

            fp.write(u'\tEndGlobalSection\n')

            #
            # Write out the ProjectConfigurationPlatforms
            #

            fp.write(u'\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n')

            for project in solution.projects:
                for configuration in solution.configurations:
                    for platform in solution.platform.getvsplatform():
                        token = configuration + '|' + platform
                        fp.write(u'\t\t{' + project.visualstudio.uuid + '}.' + token + '.ActiveCfg = ' + token + '\n')
                        fp.write(u'\t\t{' + project.visualstudio.uuid + '}.' + token + '.Build.0 = ' + token + '\n')

            fp.write(u'\tEndGlobalSections\n')


        #
        # Hide nodes section
        #

        fp.write(u'\tGlobalSection(SolutionProperties) = preSolution\n')
        fp.write(u'\t\tHideSolutionNode = FALSE\n')
        fp.write(u'\tEndGlobalSection\n')

        if ide == IDETypes.vs2017:
            fp.write(u'\tGlobalSection(ExtensibilityGlobals) = postSolution\n')
            fp.write(u'\t\tSolutionGuid = {7DEC4DAA-9DC0-4A41-B9C7-01CC0179FDCB}\n')
            fp.write(u'\tEndGlobalSection\n')

        if ide == IDETypes.vs2019:
            fp.write(u'\tGlobalSection(ExtensibilityGlobals) = postSolution\n')
            fp.write(u'\t\tSolutionGuid = {4E9AC1D3-6227-410D-87DF-35A3C19B79ED}\n')
            fp.write(u'\tEndGlobalSection\n')

    #
    # Close it up!
    #

    fp.write(u'EndGlobal\n')
    return 0






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
            fileref.write(u'\t\t<' + compilername + ' Include="' + \
                burger.convert_to_windows_slashes(item.filename) + '">\n')
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

    except:
        if f1 != None:
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

        self.idecode = solution.ide.getshortcode()
        self.platformcode = solution.platform.getshortcode()
        self.outputfilename = str(solution.projectname + self.idecode + self.platformcode)
        self.uuid = calcuuid(self.outputfilename)

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
            print('Unknown keyword "' + str(key) + '" with data "' + \
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
        self.uuid = calcuuid(name + 'NestedProjects')
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
        fileref.write(u'Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "' + self.name + '", "' + \
            self.name + '", "{' + self.uuid + '}"\n')
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
        fp.write(u'Microsoft Visual Studio Solution File, Format Version ' + \
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

        fp.write(u'Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "' + self.solution.projectname + \
            '", "' + self.solution.visualstudio.outputfilename + projectsuffix[self.fileversion.value] + \
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
        vsplatforms = self.solution.platform.getvsplatform()
        for target in self.solution.configurations:
            for item in vsplatforms:
                token = str(target) + '|' + item
                fp.write(u'\t\t' + token + ' = ' + token + '\n')
        fp.write(u'\tEndGlobalSection\n')

        #
        # Write out the ProjectConfigurationPlatforms
        #

        fp.write(u'\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n')
        for target in self.solution.configurations:
            for item in vsplatforms:
                token = str(target) + '|' + item
                fp.write(u'\t\t{' + self.solution.visualstudio.uuid + '}.' + token + \
                    '.ActiveCfg = ' + token + '\n')
                fp.write(u'\t\t{' + self.solution.visualstudio.uuid + '}.' + token + \
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
        fp.write(u'<Project DefaultTargets="Build" ToolsVersion="' + toolsversion + \
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
        for target in solution.configurations:
            for vsplatform in solution.platform.getvsplatform():
                token = str(target) + '|' + vsplatform
                fp.write(u'\t\t<ProjectConfiguration Include="' + token + '">\n')
                fp.write(u'\t\t\t<Configuration>' + str(target) + '</Configuration>\n')
                fp.write(u'\t\t\t<Platform>' + vsplatform + '</Platform>\n')
                fp.write(u'\t\t</ProjectConfiguration>\n')
        fp.write(u'\t</ItemGroup>\n')

        #
        # Write the project globals
        #

        fp.write(u'\t<PropertyGroup Label="Globals">\n')
        fp.write(u'\t\t<ProjectName>' + solution.projectname + '</ProjectName>\n')
        if solution.finalfolder is not None:
            final = burger.convert_to_windows_slashes(solution.finalfolder, True)
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
            fp.write(u'\t\t<PlatformToolset>' + platformtoolsets[self.defaults.fileversion.value] + \
                '</PlatformToolset>\n')
            fp.write(u'\t</PropertyGroup>\n')

        #
        # Add in the burgerlib includes
        #

        if solution.projecttype == ProjectTypes.library:
            fp.write(u'\t<Import Project="$(BURGER_SDKS)\\visualstudio\\burger.libv10.props" Condition="exists(\'$(BURGER_SDKS)\\visualstudio\\burger.libv10.props\')" />\n')
        elif solution.projecttype == ProjectTypes.tool:
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

        linkerdirectories = list(solution.includefolders)
        if self.defaults.platformcode == 'dsi':
            linkerdirectories += [u'$(BURGER_SDKS)\\dsi\\burgerlib']

        if self.includedirectories or \
            linkerdirectories or \
            solution.defines:
            fp.write(u'\t<ItemDefinitionGroup>\n')

            #
            # Handle global compiler defines
            #

            if self.includedirectories or \
                linkerdirectories or \
                solution.defines:
                fp.write(u'\t\t<ClCompile>\n')

                # Include directories
                if self.includedirectories or linkerdirectories:
                    fp.write(u'\t\t\t<AdditionalIncludeDirectories>')
                    for item in self.includedirectories:
                        fp.write(u'$(ProjectDir)' + burger.convert_to_windows_slashes(item) + ';')
                    for item in linkerdirectories:
                        fp.write(burger.convert_to_windows_slashes(item) + ';')
                    fp.write(u'%(AdditionalIncludeDirectories)</AdditionalIncludeDirectories>\n')

                # Global defines
                if solution.defines:
                    fp.write(u'\t\t\t<PreprocessorDefinitions>')
                    for define in solution.defines:
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
                        fp.write(burger.convert_to_windows_slashes(item) + ';')
                    fp.write(u'%(AdditionalLibraryDirectories)</AdditionalLibraryDirectories>\n')

                fp.write(u'\t\t</Link>\n')

            fp.write(u'\t</ItemDefinitionGroup>\n')

        #
        # This is needed for the PS3 and PS4 targets :(
        #

        if self.defaults.platformcode == 'ps3' or self.defaults.platformcode == 'ps4':
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

        if self.listh or \
            self.listcpp or \
            self.listwindowsresource or \
            self.listhlsl or \
            self.listglsl or \
            self.listx360sl or \
            self.listvitacg or \
            self.listico:

            fp.write(u'\t<ItemGroup>\n')

            for item in self.listh:
                fp.write(u'\t\t<ClInclude Include="' + burger.convert_to_windows_slashes(item.filename) + '" />\n')

            for item in self.listcpp:
                fp.write(u'\t\t<ClCompile Include="' + burger.convert_to_windows_slashes(item.filename) + '" />\n')

            for item in self.listwindowsresource:
                fp.write(u'\t\t<ResourceCompile Include="' + burger.convert_to_windows_slashes(item.filename) + '" />\n')

            for item in self.listhlsl:
                fp.write(u'\t\t<HLSL Include="' + burger.convert_to_windows_slashes(item.filename) + '">\n')
                # Cross platform way in splitting the path (MacOS doesn't like windows slashes)
                basename = burger.convert_to_windows_slashes(item.filename).lower().rsplit('\\', 1)[1]
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
                fp.write(u'\t\t<X360SL Include="' + burger.convert_to_windows_slashes(item.filename) + '">\n')
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
                fp.write(u'\t\t<VitaCGCompile Include="' + \
                    burger.convert_to_windows_slashes(item.filename) + '">\n')
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
                fp.write(u'\t\t<GLSL Include="' + burger.convert_to_windows_slashes(item.filename) + '" />\n')

            if self.defaults.fileversion.value >= FileVersions.vs2015.value:
                chunkname = 'Image'
            else:
                chunkname = 'None'
            for item in self.listico:
                fp.write(u'\t\t<' + chunkname + ' Include="' + burger.convert_to_windows_slashes(item.filename) + '" />\n')

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

    #
    # Write out the filter file
    #

    def writefilter(self, fileref):

        #
        # Stock header for the filter
        #

        fileref.write('<?xml version="1.0" encoding="utf-8"?>\n')
        fileref.write('<Project ToolsVersion="4.0" ' \
            'xmlns="http://schemas.microsoft.com/developer/msbuild/2003">\n')
        fileref.write('\t<ItemGroup>\n')

        groups = []
        writefiltergroup(fileref, self.listh, groups, u'ClInclude')
        writefiltergroup(fileref, self.listcpp, groups, u'ClCompile')
        writefiltergroup(fileref, self.listwindowsresource, groups, \
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
            item = burger.convert_to_windows_slashes(item)
            groupuuid = calcuuid(self.defaults.outputfilename + item)
            fileref.write(u'\t\t<Filter Include="' + item + '">\n')
            fileref.write(u'\t\t\t<UniqueIdentifier>{' + groupuuid + \
                '}</UniqueIdentifier>\n')
            fileref.write(u'\t\t</Filter>\n')

        fileref.write(u'\t</ItemGroup>\n')
        fileref.write(u'</Project>\n')

        return len(groupset)

#
# Root object for a Visual Studio Code IDE project file
# Created with the name of the project, the IDE code (vc8, v10)
# the platform code (win, ps4)
#


class Project(object):
    def __init__(self, defaults, solution):
        self.defaults = defaults
        self.slnfile = SolutionFile(defaults.fileversion, solution)
        self.projects = []

    #
    # Add a nested project into the solution
    #

    def addnestedprojects(self, name):
        return self.slnfile.addnestedprojects(name)

    #
    # Generate a .sln file for Visual Studio
    #

    def writesln(self, fileref):
        return self.slnfile.write(fileref)

    #
    # Generate a .vcxproj.filters file for Visual Studio 2010 or higher
    #

    def writeproject2010(self, fileref, solution):
        error = 0
        if self.projects:
            for item in self.projects:
                error = item.writeproject2010(fileref, solution)
                break
        return error

    #
    # Generate a .vcxproj.filters file for Visual Studio 2010 or higher
    #

    def writefilter(self, fileref):
        count = 0
        if self.projects:
            for item in self.projects:
                count = count + item.writefilter(fileref)
        return count

#
# Visual Studio 2003, 2005, 2008
# 2010, 2012 and 2015 support
#

#
# Create a project file for Visual Studio (All supported flavors)
#


def generate(solution, ide, perforce=False, verbose=False):

    #
    # For starters, generate the UUID and filenames for the solution file
    # for visual studio, since each solution and project file generate
    # seperately
    #

    #
    # Check for overrides, otherwise use the defaults
    #

    if solution.visualstudio.idecode is not None:
        idecode = solution.visualstudio.idecode
    else:
        idecode = ide.getshortcode()

    #
    # Set the visual studio platform code
    #

    if solution.visualstudio.platformcode is not None:
        platformcode = solution.visualstudio.platformcode
    else:
        platformcode = solution.platform.getshortcode()

    #
    # Save the final filename for the Visual Studio Solution file
    #

    solution.visualstudio.outputfilename = str(solution.projectname + idecode \
        + platformcode + '.sln')

    #
    # Older versions of Visual studio use the .vcproj extension
    # instead of the .vcxproj extension
    #

    projectfilenamesuffix = '.vcxproj'
    if ide == IDETypes.vs2003 or \
        ide == IDETypes.vs2005 or \
        ide == IDETypes.vs2008:
        projectfilenamesuffix = '.vcproj'

    #
    # Iterate over the project files and create the filenames
    #

    for item in solution.projects:
        item.visualstudio.outputfilename = str(item.projectname + idecode + \
            platformcode + projectfilenamesuffix)
        item.visualstudio.uuid = calcuuid(item.visualstudio.outputfilename)

    # Write to memory for file comparison
    fileref = StringIO()
    error = generatesolutionfile(fileref, solution, ide)
    if error != 0:
        fileref.close()
        return error

    filename = os.path.join(solution.workingDir, \
        solution.visualstudio.outputfilename)
    if comparefiletostring(filename, fileref):
        if verbose is True:
            print(filename + ' was not changed')
    else:
        if perforce is True:
            burger.perforce_edit(filename)
        fp2 = io.open(filename, 'w')
        fp2.write(fileref.getvalue())
        fp2.close()

    #
    # Now that the solution file was generated, create the individual project
    # files using the format appropriate for the selected IDE
    #

    if ide == IDETypes.vs2003:
        for item in solution.projects:
            exporter = VS2003vcproj(item)
            fileref = StringIO()
            exporter.write(fileref)

            filename = os.path.join(solution.workingDir, \
                item.visualstudio.outputfilename)
            if comparefiletostring(filename, fileref):
                if verbose is True:
                    print(filename + ' was not changed')
            else:
                if perforce is True:
                    burger.perforce_edit(filename)
                fp2 = io.open(filename, 'w')
                fp2.write(fileref.getvalue())
                fp2.close()
    return 0


def generateold(solution, ide):

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

    codefiles, includedirectories = solution.getfilelist( \
        solution.visualstudio.acceptable)

    #
    # Create a blank project
    #

    project = Project(solution.visualstudio, solution)
    project.projects.append(vsProject(solution.visualstudio, codefiles, \
        includedirectories))

    #
    # Serialize the solution file and write if changed
    #

    fileref = StringIO()
    project.writesln(fileref)
    filename = os.path.join(solution.workingDir, \
        solution.visualstudio.outputfilename + '.sln')
    if comparefiletostring(filename, fileref):
        if solution.verbose is True:
            print(filename + ' was not changed')
    else:
        burger.perforce_edit(filename)
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
        filename = os.path.join(solution.workingDir, \
            solution.visualstudio.outputfilename + \
            projectsuffix[solution.visualstudio.fileversion.value])
        if comparefiletostring(filename, fileref):
            if solution.verbose is True:
                print(filename + ' was not changed')
        else:
            burger.perforce_edit(filename)
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
        filename = os.path.join(solution.workingDir, \
            solution.visualstudio.outputfilename + '.vcxproj.filters')

        # No groups found?
        if count == 0:
            # Just delete the file
            burger.delete_file(filename)
        else:
            # Did it change?
            if comparefiletostring(filename, fileref):
                if solution.verbose is True:
                    print(filename + ' was not changed')
            else:
                # Update the file
                burger.perforce_edit(filename)
                fp2 = io.open(filename, 'w')
                fp2.write(fileref.getvalue())
                fp2.close()
        fileref.close()

    return 0
