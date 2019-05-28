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
from copy import deepcopy
from burger import PY2, save_text_file_if_newer, convert_to_windows_slashes, delete_file
from burger import perforce_edit, escape_xml_cdata, escape_xml_attribute, convert_to_array
from burger import packed_paths
import makeprojects.core
from .enums import platformtype_short_code
from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes
from .core import configuration_short_code

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
    Convert a string to a UUID.

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
                project.get_attribute('name'),
                project.attributes['vs_output_filename'],
                project.attributes['vs_uuid']))

        # Write out the dependencies, if any
        solution_lines.append('\tProjectSection(ProjectDependencies) = postProject')
        for dependent in project.projects:
            solution_lines.append(
                '\t\t{{{0}}} = {{{0}}}'.format(
                    dependent.attributes['vs_uuid']))
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
                if configuration.attributes['platform'] == PlatformTypes.win64:
                    continue
                entry = configuration.attributes['name']
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
                if configuration.attributes['platform'] == PlatformTypes.win64:
                    if solution.get_attribute('verbose'):
                        print('Visual Studio 2003 does not support platform Win64, skipped')
                    continue
                # Using the faked Platform/Configuration pair used above, create the appropriate
                # pairs here and match them up.
                platform = configuration.attributes['platform'].get_vs_platform()[0]
                solution_lines.append(
                    '\t\t{{{0}}}.{1}.ActiveCfg = {1}|{2}'.format(
                        project.attributes['vs_uuid'],
                        configuration.attributes['name'], platform))
                solution_lines.append('\t\t{{{0}}}.{1}.Build.0 = {1}|{2}'.format(
                    project.attributes['vs_uuid'], configuration.attributes['name'], platform))
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
                            configuration.attributes['name'],
                            configuration.attributes['platform'].get_vs_platform()[0]))
            solution_lines.append('\tEndGlobalSection')

            # Write out the ProjectConfigurationPlatforms
            solution_lines.append('\tGlobalSection(ProjectConfigurationPlatforms) = postSolution')

            for project in solution.projects:
                for configuration in project.configurations:
                    solution_lines.append(
                        '\t\t{{{0}}}.{1}|{2}.ActiveCfg = {1}|{2}'.format(
                            project.attributes['vs_uuid'],
                            configuration.attributes['name'],
                            configuration.attributes['platform'].get_vs_platform()[0]))
                    solution_lines.append(
                        '\t\t{{{0}}}.{1}|{2}.Build.0 = {1}|{2}'.format(
                            project.attributes['vs_uuid'],
                            configuration.attributes['name'],
                            configuration.attributes['platform'].get_vs_platform()[0]))

            solution_lines.append('\tEndGlobalSection')

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


class VS2003XML():
    """
    Visual Studio 2003-2008 XML formatter.

    Output XML elements in the format of Visual Studio 2003-2008
    """

    def __init__(self, name, attribute_defaults=None, force_pair=False):
        """
        Set the defaults.
        Args:
            name: Name of the XML element
        """

        ## Name of this XML chunk.
        self.name = name

        ## Disable <foo/> syntax
        self.force_pair = force_pair

        ## XML attributes.
        self.attributes = []

        ## List of elements in this element.
        self.elements = []

        ## List of valid attributes and defaults
        self.attribute_defaults = {}

        # Add the defaults, if any
        self.add_defaults(attribute_defaults)

    def add_defaults(self, attribute_defaults):
        """
        Add a dict of attribute defaults.

        Args:
            attribute_defaults: dict of attribute names and default values.
        """
        if attribute_defaults:
            for attribute in attribute_defaults:
                self.attribute_defaults[attribute] = attribute_defaults[attribute]
                if attribute_defaults[attribute] is not None:
                    self.set_attribute(attribute, attribute_defaults[attribute])

    def add_attribute(self, name, value):
        """
        Add an attribute to this XML element.

        Args:
            name: Name of the attribute
            value: Attribute data
        """
        self.attributes.append([name, value])

    def add_element(self, element):
        """
        Add an element to this XML element.

        Args:
            element: VS2003XML object
        """
        self.elements.append(element)

    def set_attribute(self, name, value):
        """
        Either change existing attribute or create a new one.

        If the attribute was not found, it will be appended to the list

        Args:
            name: String of the entry to match
            value: Value to substitute
        """
        for attribute in self.attributes:
            if attribute[0] == name:
                attribute[1] = value
                break
        else:
            # Not found? Add the entry and then exit
            self.attributes.append([name, value])

    def remove_attribute(self, name):
        """
        Remove an attribute.

        If the value is in the list, remove it.

        Args:
            name: String of the entry to remove
        """

        for item in self.attributes:
            # Match? Kill it.
            if item[0] == name:
                self.attributes.remove(item)
                break

    def reset_attribute(self, name):
        """
        Reset an attribute to default.

        If the attribute is in the attribute_defaults list, set
        it to the default, which can include the attribute removal.

        Args:
            name: String of the entry to reset
        """

        value = self.attribute_defaults.get(name)
        if value is not None:
            self.set_attribute(name, value)
        else:
            self.remove_attribute(name)

    def generate(self, line_list, indent=0):
        """
        Generate the text lines for this XML element.
        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
        """

        # Determine the indentation
        tabs = '\t' * indent

        # Special case, if no attributes, don't allow <foo/> XML
        # This is to duplicate the output of Visual Studio 2003-2008
        line_list.append('{0}<{1}'.format(tabs, escape_xml_cdata(self.name)))
        if self.attributes:
            # Output tag with attributes and support '/>' closing

            for attribute in self.attributes:
                line_list.append(
                    '\t{0}{1}="{2}"'.format(
                        tabs, escape_xml_cdata(
                            attribute[0]), escape_xml_attribute(attribute[1])))
            if not self.elements and not self.force_pair:
                line_list.append('{}/>'.format(tabs))
                return
            # Close the open tag
            line_list.append('\t{}>'.format(tabs))
        else:
            line_list[-1] = line_list[-1] + '>'

        # Output the embedded elements
        for element in self.elements:
            element.generate(line_list, indent=indent + 1)
        # Close the current element
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


########################################


class VS2003Tool(VS2003XML):
    """
    Helper class to output a Tool record for Visual Studio 2003-2008

    In Visual Studio project files from version 2003 to 2008, Tool
    XML records were used for settings for each and every compiler tool
    """

    def __init__(self, name, force_pair=False):
        """
        Init a tool record with the tool name.
        Args:
            name: Name of the tool.
        """
        VS2003XML.__init__(self, 'Tool', {'Name': name}, force_pair=force_pair)

########################################


class VCCLCompilerTool(VS2003Tool):
    """
    Visual Studio 2003-2008 VCCLCompilerTool record
    """

    def __init__(self, configuration):
        """
        Init defaults
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, name='VCCLCompilerTool')
        if configuration.attributes['name'] == 'Debug':
            vs_optimization = '0'
            vs_inlinefunctionexpansion = None
            vs_enableintrinsicfunctions = None
            vs_omitframepointers = None
        else:
            vs_optimization = '2'
            vs_inlinefunctionexpansion = '2'
            vs_enableintrinsicfunctions = 'true'
            vs_omitframepointers = 'true'

        if configuration.attributes['name'] == 'Release':
            vs_buffersecuritychecks = 'false'
            vs_runtimelibrary = '0'
        else:
            vs_buffersecuritychecks = 'true'
            vs_runtimelibrary = '1'

        if configuration.get_attribute('project_type') == ProjectTypes.library or \
                configuration.attributes['name'] != 'Release':
            vs_debuginformationformat = '3'
            vs_programdatabasefilename = '"$(OutDir)$(TargetName).pdb"'
        else:
            vs_debuginformationformat = '0'
            vs_programdatabasefilename = None

        # Start with a copy (To prevent damaging the original list)
        include_folders = list(convert_to_array(
            configuration.project.attributes.get(
                'extra_include', [])))
        include_folders.extend(
            convert_to_array(
                configuration.attributes.get(
                    'include_folders', [])))
        include_folders.extend(
            convert_to_array(
                configuration.project.attributes.get(
                    'include_folders', [])))
        include_folders.extend(
            convert_to_array(
                configuration.project.solution.attributes.get(
                    'include_folders', [])))

        self.add_defaults({
            # Optimization menu
            'Optimization': vs_optimization,
            'GlobalOptimizations': None,
            'InlineFunctionExpansion': vs_inlinefunctionexpansion,
            'EnableIntrinsicFunctions': vs_enableintrinsicfunctions,
            'ImproveFloatingPointConsistency': None,
            'FavorSizeOrSpeed': '1',
            'OmitFramePointers': vs_omitframepointers,
            'EnableFiberSafeOptimizations': None,
            'OptimizeForProcessor': None,
            'OptimizeForWindowsApplication': None,

            # General menu
            'AdditionalIncludeDirectories': packed_paths(include_folders, slashes='\\'),
            'AdditionalUsingDirectories': None,
            'Detect64BitPortabilityProblems': None,
            'WarnAsError': None,

            # Preprocess menu
            'PreprocessorDefinitions': packed_paths(configuration.get_attribute('defines')),
            'IgnoreStandardIncludePath': None,
            'GeneratePreprocessedFile': None,
            'KeepComments': None,

            # Code generation menu
            'StringPooling': 'true',
            'MinimalRebuild': None,
            'ExceptionHandling': '0',
            'SmallerTypeCheck': None,
            'BasicRuntimeChecks': None,
            'RuntimeLibrary': vs_runtimelibrary,
            'StructMemberAlignment': '4',
            'BufferSecurityCheck': vs_buffersecuritychecks,
            'EnableFunctionLevelLinking': 'true',
            'FloatingPointModel': '2',              # 2008
            'EnableEnhancedInstructionSet': None,

            # Language extensions menu
            'DisableLanguageExtensions': None,
            'DefaultCharIsUnsigned': None,
            'TreatWChar_tAsBuiltInType': None,
            'ForceConformanceInForLoopScope': None,
            'RuntimeTypeInfo': 'false',

            # Precompiled header menu
            'UsePrecompiledHeader': None,
            'PrecompiledHeaderThrough': None,
            'PrecompiledHeaderFile': None,

            # Output files menu
            'ExpandAttributedSource': None,
            'AssemblerOutput': None,
            'AssemblerListingLocation': None,
            'ObjectFile': None,
            'ProgramDataBaseFileName': vs_programdatabasefilename,
            'WarningLevel': '4',
            'SuppressStartupBanner': 'true',
            'DebugInformationFormat': vs_debuginformationformat,

            # Browse information menu
            'BrowseInformation': None,
            'BrowseInformationFile': None,

            # Advanced menu
            'CallingConvention': '1',
            'CompileAs': '2',
            'DisableSpecificWarnings': '4201',
            'ForcedIncludeFile': None,
            'ForcedUsingFiles': None,
            'ShowIncludes': None,
            'UndefinePreprocessorDefinitions': None,
            'UndefineAllPreprocessorDefinitions': None,

            # Command line menu
            'AdditionalOptions': None
        })

########################################


class VCCustomBuildTool(VS2003Tool):
    """
    Visual Studio 2003-2008 VCCustomBuildTool record
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, name='VCCustomBuildTool')
        self.add_defaults({
            # General menu
            'Description': None,
            'CommandLine': None,
            'AdditionalDependencies': None,
            'Outputs': None
        })


########################################

class VCLinkerTool(VS2003Tool):
    """
    Visual Studio 2003-2008 VCLinkerTool
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """

        self.configuration = configuration
        ide = configuration.project.solution.ide
        VS2003Tool.__init__(self, 'VCLinkerTool')
        vs_output = '"$(OutDir){}{}{}{}.exe"'.format(
            configuration.project.get_attribute('name'),
            configuration.project.solution.ide.get_short_code(),
            configuration.attributes['platform'].get_short_code(),
            configuration_short_code(configuration.attributes['name']))

        # Start with a copy (To prevent damaging the original list)
        library_folders = list(
            convert_to_array(
                configuration.attributes.get(
                    'library_folders', [])))
        library_folders.extend(
            convert_to_array(
                configuration.project.attributes.get(
                    'library_folders', [])))
        library_folders.extend(
            convert_to_array(
                configuration.project.solution.attributes.get(
                    'library_folders', [])))

        if configuration.get_attribute('project_type') == ProjectTypes.tool:
            # Console
            vs_subsystem = '1'
        else:
            # Application
            vs_subsystem = '2'

        if ide == IDETypes.vs2003:
            vs_linkincremental = 'true'
        else:
            vs_linkincremental = None

        self.add_defaults({
            # General menu
            'OutputFile': vs_output,
            'ShowProgress': None,
            'Version': None,
            'LinkIncremental': vs_linkincremental,
            'SuppressStartupBanner': None,
            'IgnoreImportLibrary': None,
            'RegisterOutput': None,
            'AdditionalLibraryDirectories': packed_paths(library_folders, slashes='\\'),

            # Input menu
            'AdditionalDependencies': None,
            'IgnoreAllDefaultLibraries': None,
            'IgnoreDefaultLibraryNames': None,
            'ModuleDefinitionFile': None,
            'AddModuleNamesToAssembly': None,
            'EmbedManagedResourceFile': None,
            'ForceSymbolReferences': None,
            'DelayLoadDLLs': None,

            # Debugging menu
            'GenerateDebugInformation': 'true',
            'ProgramDatabaseFile': None,
            'StripPrivateSymbols': None,
            'GenerateMapFile': None,
            'MapFileName': None,
            'MapExports': None,
            'MapLines': None,
            'AssemblyDebug': None,

            # System menu
            'SubSystem': vs_subsystem,
            'HeapReserveSize': None,
            'HeapCommitSize': None,
            'StackReserveSize': None,
            'StackCommitSize': None,
            'LargeAddressAware': None,
            'TerminalServerAware': None,
            'SwapRunFromCD': None,
            'SwapRunFromNet': None,

            # Optimization
            'OptimizeReferences': '2',
            'EnableCOMDATFolding': '2',
            'OptimizeForWindows98': None,
            'FunctionOrder': None,

            # Embedded MIDL menu
            'MidlCommandFile': None,
            'IgnoreEmbeddedIDL': None,
            'MergedIDLBaseFileName': None,
            'TypeLibraryFile': None,
            'TypeLibraryResourceID': None,

            # Advanced menu
            'EntryPointSymbol': None,
            'ResourceOnlyDLL': None,
            'SetChecksum': None,
            'BaseAddress': None,
            'FixedBaseAddress': None,
            'TurnOffAssemblyGeneration': None,
            'SupportUnloadOfDelayLoadedDLL': None,
            'ImportLibrary': None,
            'MergeSections': None,
            'TargetMachine': None,

            # Command line menu
            'AdditionalOptions': None
        })

########################################


class VCLibrarianTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCLibrarianTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCLibrarianTool')

        vs_output = '"$(OutDir){}{}{}{}.lib"'.format(
            configuration.project.get_attribute('name'),
            configuration.project.solution.ide.get_short_code(),
            configuration.attributes['platform'].get_short_code(),
            configuration_short_code(configuration.attributes['name']))

        self.add_defaults({
            # General menu
            'OutputFile': vs_output,
            'SuppressStartupBanner': 'true'
        })

########################################


class VCMIDLTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for the MIDL tool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCMIDLTool')

########################################


class VCALinkTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCALinkTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCALinkTool')


########################################


class VCManifestTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCManifestTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCManifestTool')


########################################


class VCXDCMakeTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCXDCMakeTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCXDCMakeTool')

########################################


class VCBscMakeTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCBscMakeTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCBscMakeTool')

########################################


class VCFxCopTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCFxCopTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCFxCopTool')

########################################


class VCAppVerifierTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCAppVerifierTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCAppVerifierTool')

########################################


class VCManagedResourceCompilerTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCManagedResourceCompilerTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCManagedResourceCompilerTool')

########################################


class VCPostBuildEventTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCPostBuildEventTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCPostBuildEventTool')
        if configuration.get_attribute('deploy_folder') is not None:
            deploy_folder = convert_to_windows_slashes(
                configuration.get_attribute('deploy_folder'), True)
            vs_description = 'Copying $(TargetName)$(TargetExt) to {}'.format(deploy_folder)
            vs_cmd = (
                '"$(perforce)\\p4" edit "{0}$(TargetName)$(TargetExt)"\r\n'
                '"$(perforce)\\p4" edit "{0}$(TargetName).pdb"\r\n'
                'copy /Y "$(OutDir)$(TargetName)$(TargetExt)" "{0}$(TargetName)$(TargetExt)"\r\n'
                'copy /Y "$(OutDir)$(TargetName).pdb" "{0}$(TargetName).pdb"\r\n'
                '"$(perforce)\\p4" revert -a "{0}$(TargetName)$(TargetExt)"\r\n'
                '"$(perforce)\\p4" revert -a "{0}$(TargetName).pdb"\r\n').format(deploy_folder)
        else:
            vs_description = None
            vs_cmd = None

        self.add_defaults({
            # General menu
            'Description': vs_description,
            'CommandLine': vs_cmd,
            'ExcludedFromBuild': None
        })


########################################


class VCPreBuildEventTool(VS2003Tool):
    """
    VCPreBuildEventTool
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCPreBuildEventTool')
        self.add_defaults({
            # General menu
            'Description': None,
            'CommandLine': None,
            'ExcludedFromBuild': None
        })


########################################


class VCPreLinkEventTool(VS2003Tool):
    """
    VCPreLinkEventTool
    """

    def __init__(self, configuration):
        """
        Init defaults.
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCPreLinkEventTool')
        self.add_defaults({
            # General menu
            'Description': None,
            'CommandLine': None,
            'ExcludedFromBuild': None
        })

########################################


class VCResourceCompilerTool(VS2003Tool):
    """
    VCResourceCompilerTool
    """

    def __init__(self, configuration):
        """
        Init
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCResourceCompilerTool')
        self.add_defaults({
            'Culture': '1033'
        })

########################################


class XboxDeploymentTool(VS2003Tool):
    """
    XboxDeploymentTool for Xbox Classic
    """

    def __init__(self, configuration):
        """
        Init defaults
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'XboxDeploymentTool')

########################################


class XboxImageTool(VS2003Tool):
    """
    XboxImageTool
    """

    def __init__(self, configuration):
        """
        Init defaults
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'XboxImageTool')

########################################


class VCWebServiceProxyGeneratorTool(VS2003Tool):
    """
    VCWebServiceProxyGeneratorTool
    """

    def __init__(self, configuration):
        """
        Init
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCWebServiceProxyGeneratorTool')

########################################


class VCXMLDataGeneratorTool(VS2003Tool):
    """
    VCXMLDataGeneratorTool
    """

    def __init__(self, configuration):
        """
        Init
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCXMLDataGeneratorTool')

########################################


class VCWebDeploymentTool(VS2003Tool):
    """
    VCWebDeploymentTool
    """

    def __init__(self, configuration):
        """
        Init
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCWebDeploymentTool')

########################################


class VCManagedWrapperGeneratorTool(VS2003Tool):
    """
    VCManagedWrapperGeneratorTool
    """

    def __init__(self, configuration):
        """
        Init
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCManagedWrapperGeneratorTool')

########################################


class VCAuxiliaryManagedWrapperGeneratorTool(VS2003Tool):
    """
    VCAuxiliaryManagedWrapperGeneratorTool
    """

    def __init__(self, configuration):
        """
        Init
        """
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCAuxiliaryManagedWrapperGeneratorTool')

########################################


class VS2003Platform(VS2003XML):
    """
    Visual Studio 2003-2008 Platform record
    """

    def __init__(self, platform):
        """
        Set the defaults
        """
        self.platform = platform
        VS2003XML.__init__(self, 'Platform', {'Name': platform.get_vs_platform()[0]})

########################################


class VS2003Platforms(VS2003XML):
    """
    Visual Studio 2003-2008 Platforms record
    """

    def __init__(self, project):
        """
        Set the defaults
        """

        VS2003XML.__init__(self, 'Platforms')
        self.project = project

        # Get the list of platforms
        platforms = []
        for configuration in project.configurations:
            platforms.append(configuration.attributes['platform'])

        # Remove duplicates
        platforms = set(platforms)

        # Add the records
        for platform in sorted(platforms):
            self.add_element(VS2003Platform(platform))


########################################


class VS2003References(VS2003XML):
    """
    Visual Studio 2003-2008 References record
    """

    def __init__(self):
        """
        Set the defaults
        """

        VS2003XML.__init__(self, 'References')

########################################


class VS2003ToolFiles(VS2003XML):
    """
    Visual Studio 2003-2008 ToolFiles record
    """

    def __init__(self, platform):
        """
        Set the defaults
        """
        self.platform = platform
        VS2003XML.__init__(self, 'ToolFiles')

########################################


class VS2003Globals(VS2003XML):
    """
    Visual Studio 2003-2008 Globals record
    """

    def __init__(self):
        """
        Set the defaults
        """

        VS2003XML.__init__(self, 'Globals')

########################################


class VS2003Configuration(VS2003XML):
    """
    Visual Studio 2003-2008 Configuration record
    """

    def __init__(self, configuration):
        """
        Set the defaults
        """

        self.configuration = configuration
        ide = configuration.project.solution.ide

        vs_name = configuration.attributes['name'] + '|' + \
            configuration.attributes['platform'].get_vs_platform()[0]
        vs_intdirectory = 'temp\\{}{}{}{}\\'.format(
            configuration.project.get_attribute('name'),
            configuration.project.solution.ide.get_short_code(),
            configuration.attributes['platform'].get_short_code(),
            configuration_short_code(configuration.attributes['name']))

        if configuration.get_attribute('project_type') == ProjectTypes.library:
            vs_configuration_type = '4'
        else:
            vs_configuration_type = '1'
        VS2003XML.__init__(self, 'Configuration', {
            'Name': vs_name,
            'OutputDirectory': 'bin\\',
            'IntermediateDirectory': vs_intdirectory,
            'ConfigurationType': vs_configuration_type,
            'UseOfMFC': '0',
            'ATLMinimizesCRunTimeLibraryUsage': 'false',
            'CharacterSet': '1',
            'DeleteExtensionsOnClean': None,
            'ManagedExtensions': None,
            'WholeProgramOptimization': None,
            'ReferencesPath': None
        })

        self.add_element(VCPreBuildEventTool(configuration))
        self.add_element(VCCustomBuildTool(configuration))

        if configuration.get_attribute('platform') != PlatformTypes.xbox:
            self.add_element(VCXMLDataGeneratorTool(configuration))
            self.add_element(VCWebServiceProxyGeneratorTool(configuration))

        if configuration.get_attribute('platform').is_windows():
            self.add_element(VCMIDLTool(configuration))

        self.add_element(VCCLCompilerTool(configuration))

        if configuration.get_attribute('platform').is_windows():
            self.add_element(VCManagedResourceCompilerTool(configuration))
            self.add_element(VCResourceCompilerTool(configuration))

        self.add_element(VCPreLinkEventTool(configuration))

        if configuration.get_attribute('project_type') in (
                ProjectTypes.library, ProjectTypes.sharedlibrary):
            self.add_element(VCLibrarianTool(configuration))
        else:
            self.add_element(VCLinkerTool(configuration))

        if configuration.get_attribute('platform') == PlatformTypes.xbox:
            self.add_element(XboxDeploymentTool(configuration))
            self.add_element(XboxImageTool(configuration))

        #self.add_element(VCManagedWrapperGeneratorTool(configuration))
        #self.add_element(VCAuxiliaryManagedWrapperGeneratorTool(configuration))

        self.add_element(VCALinkTool(configuration))
        self.add_element(VCManifestTool(configuration))
        self.add_element(VCXDCMakeTool(configuration))
        self.add_element(VCBscMakeTool(configuration))
        self.add_element(VCFxCopTool(configuration))
        self.add_element(VCAppVerifierTool(configuration))

        if ide != IDETypes.vs2008:
            if configuration.get_attribute('platform') != PlatformTypes.xbox:
                self.add_element(VCWebDeploymentTool(configuration))

        self.add_element(VCPostBuildEventTool(configuration))

########################################


class VS2003Configurations(VS2003XML):
    """
    Visual Studio 2003-2008 Configurations record
    """

    def __init__(self, project):
        """
        Set the defaults
        """

        VS2003XML.__init__(self, 'Configurations')
        for configuration in project.configurations:
            self.add_element(VS2003Configuration(configuration))


########################################


class VS2003File(VS2003XML):
    """
    Visual Studio 2003-2008 File record
    """

    def __init__(self, source_file):
        """
        Set the defaults
        """

        self.source_file = source_file
        VS2003XML.__init__(self, 'File', {'RelativePath': source_file}, force_pair=True)

########################################


class VS2003Filter(VS2003XML):
    """
    Visual Studio 2003-2008 File record
    """

    def __init__(self, name):
        """
        Set the defaults
        """

        self.name = name
        VS2003XML.__init__(self, 'Filter', {'Name': name})


########################################

def do_tree(xml_entry, filter_name, tree, groups):
    """
    Dump out a recursive tree of files to reconstruct a
    directory hiearchy for a file list
    """

    for item in sorted(tree):
        if filter_name == '':
            merged = item
        else:
            merged = filter_name + '\\' + item

        new_filter = VS2003Filter(item)
        xml_entry.add_element(new_filter)

        # See if this directory string creates a group?
        if merged in groups:
            # Found, add all the elements into this filter
            for fileitem in sorted(groups[merged]):
                new_filter.add_element(VS2003File(fileitem))

        tree_key = tree[item]
        # Recurse down the tree
        if isinstance(tree_key, dict):
            do_tree(new_filter, merged, tree_key, groups)


class VS2003Files(VS2003XML):
    """
    Visual Studio 2003-2008 Files record
    """

    def __init__(self, project):
        """
        Set the defaults
        """

        self.project = project
        VS2003XML.__init__(self, 'Files')

        # Create group names and attach all files that belong to that group
        groups = dict()
        for item in project.codefiles:
            groupname = item.extractgroupname()
            # Put each filename in its proper group
            name = convert_to_windows_slashes(item.filename)
            group = groups.get(groupname, None)
            if group is None:
                groups[groupname] = [name]
            else:
                group.append(name)

        # Convert from a flat tree into a hierarchical tree
        tree = dict()
        for group in groups:

            # Get the depth of the tree needed
            parts = group.split('\\')
            nexttree = tree

            # Iterate over every part
            for item, _ in enumerate(parts):
                # Already declared?
                if not parts[item] in nexttree:
                    nexttree[parts[item]] = dict()
                # Step into the tree
                nexttree = nexttree[parts[item]]

        # Generate the file tree
        do_tree(self, '', tree, groups)

########################################


class VS2003vcproj(VS2003XML):
    """
    Visual Studio 2003-2008 formatter
    This record instructs how to write a Visual 2003-2008 format vcproj file
    """

    def __init__(self, project):
        """
        Set the defaults
        """

        self.project = project

        # Which project type?
        ide = project.solution.ide
        if ide == IDETypes.vs2003:
            version = '7.10'
        elif ide == IDETypes.vs2005:
            version = '8.00'
        else:
            version = '9.00'

        VS2003XML.__init__(self, 'VisualStudioProject',
                           {'ProjectType': 'Visual C++',
                            'Version': version,
                            'Name': project.get_attribute('name'),
                            'ProjectGUID': '{' + project.attributes['vs_uuid'] + '}'})
        if ide != IDETypes.vs2003:
            self.add_defaults({'RootNamespace': project.get_attribute('name')})
        self.add_defaults({'Keyword': 'Win32Proj'})
        if ide == IDETypes.vs2008:
            self.add_defaults({'TargetFrameworkVersion': '196613'})

        # Add all the sub chunks
        self.platforms = VS2003Platforms(project)
        self.add_element(self.platforms)

        self.toolfiles = VS2003ToolFiles(project)
        if ide != IDETypes.vs2003:
            self.add_element(self.toolfiles)

        self.configurations = VS2003Configurations(project)
        self.add_element(self.configurations)
        self.references = VS2003References()
        self.add_element(self.references)
        self.files = VS2003Files(project)
        self.add_element(self.files)
        self.globals = VS2003Globals()
        self.add_element(self.globals)

    def generate(self, line_list, indent=0):
        """
        Write out the VisualStudioProject record.
        Args:
            line_list: string list to save the XML text
        """

        # XML is utf-8 only
        line_list.append('<?xml version="1.0" encoding="UTF-8"?>')
        VS2003XML.generate(self, line_list, indent=indent)

########################################


def generate(solution):
    """
    Create a solution and project(s) file for Visual Studio.

    Given a Solution object, create an appropriate Visual Studio solution
    and project files to allow this project to build.

    Args:
        solution: Solution instance.

    Returns:
        Zero if no error, non-zero on error.
    """

    # For starters, generate the UUID and filenames for the solution file
    # for visual studio, since each solution and project file generate
    # seperately

    solution = deepcopy(solution)

    # Visual Studio doesn't support x64
    if solution.ide == IDETypes.vs2003:
        for project in solution.projects:
            configs = []
            for configuration in project.configurations:
                if configuration.attributes['platform'] != PlatformTypes.win64:
                    configs.append(configuration)
            project.configurations = configs

    # Get the IDE name code
    idecode = solution.ide.get_short_code()

    # Get the platform code
    temp_list = []
    for project in solution.projects:
        temp_list.extend(project.configurations)
    platformcode = platformtype_short_code(temp_list)

    # Create the final filename for the Visual Studio Solution file
    solution_filename = ''.join((solution.get_attribute('name'), idecode, platformcode, '.sln'))

    # Older versions of Visual studio use the .vcproj extension
    # instead of the .vcxproj extension

    project_filename_suffix = '.vcxproj'
    if solution.ide in (IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008):
        project_filename_suffix = '.vcproj'

    # Iterate over the project files and create the filenames
    for project in solution.projects:
        platformcode = platformtype_short_code(project.configurations)
        project.attributes['vs_output_filename'] = ''.join((
            project.get_attribute('name'), idecode, platformcode, project_filename_suffix))
        project.attributes['vs_uuid'] = get_uuid(project.attributes['vs_output_filename'])

    # Write to memory for file comparison
    solution_lines = []
    error = generate_solution_file(solution_lines, solution)
    if error:
        return error

    save_text_file_if_newer(
        os.path.join(solution.get_attribute('working_directory'), solution_filename),
        solution_lines,
        bom=solution.ide != IDETypes.vs2003,
        perforce=solution.get_attribute('perforce'),
        verbose=solution.get_attribute('verbose'))

    # Now that the solution file was generated, create the individual project
    # files using the format appropriate for the selected IDE

    if solution.ide in (IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008):
        for item in solution.projects:
            item.get_file_list([FileTypes.h, FileTypes.cpp, FileTypes.rc, FileTypes.ico])
            exporter = VS2003vcproj(item)
            project_lines = []
            exporter.generate(project_lines)
            save_text_file_if_newer(
                os.path.join(
                    solution.get_attribute('working_directory'),
                    item.attributes['vs_output_filename']),
                project_lines,
                bom=solution.ide != IDETypes.vs2003,
                perforce=solution.get_attribute('perforce'),
                verbose=solution.get_attribute('verbose'))
    return 0


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


class Defaults(object):
    """
    Class to hold the defaults and settings to output a visualstudio
    compatible project file.
    json keyword "visualstudio" for dictionary of overrides
    """

    def __init__(self):
        """
        Power up defaults
        """
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
        self.platformcode = solution.projects[0].get_attribute('platform').get_short_code()
        self.outputfilename = str(solution.attributes['name'] + self.idecode + self.platformcode)
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
            u'Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "' + self.solution.attributes
            ['name'] + '", "' + self.solution.visualstudio.outputfilename +
            projectsuffix[self.fileversion.value] + '", "{' + self.solution.visualstudio.uuid + '}"\n')
        fp.write(u'EndProject\n')

        #
        # Begin the Global record
        #

        fp.write(u'Global\n')

        #
        # Write out the SolutionConfigurationPlatforms
        #

        fp.write(u'\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n')
        vsplatforms = self.solution.projects[0].get_attribute('platform').get_vs_platform()
        for target in self.solution.projects[0].configurations:
            for item in vsplatforms:
                token = target.attributes['name'] + '|' + item
                fp.write(u'\t\t' + token + ' = ' + token + '\n')
        fp.write(u'\tEndGlobalSection\n')

        #
        # Write out the ProjectConfigurationPlatforms
        #

        fp.write(u'\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n')
        for target in self.solution.projects[0].configurations:
            for item in vsplatforms:
                token = target.attributes['name'] + '|' + item
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
            for vsplatform in solution.projects[0].get_attribute('platform').get_vs_platform():
                token = target.attributes['name'] + '|' + vsplatform
                fp.write(u'\t\t<ProjectConfiguration Include="' + token + '">\n')
                fp.write(
                    u'\t\t\t<Configuration>' +
                    target.attributes['name'] +
                    '</Configuration>\n')
                fp.write(u'\t\t\t<Platform>' + vsplatform + '</Platform>\n')
                fp.write(u'\t\t</ProjectConfiguration>\n')
        fp.write(u'\t</ItemGroup>\n')

        #
        # Write the project globals
        #

        fp.write(u'\t<PropertyGroup Label="Globals">\n')
        fp.write(u'\t\t<ProjectName>' + solution.attributes['name'] + '</ProjectName>\n')
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

        if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
            fp.write(u'\t<Import Project="$(BURGER_SDKS)\\visualstudio\\burger.libv10.props" Condition="exists(\'$(BURGER_SDKS)\\visualstudio\\burger.libv10.props\')" />\n')
        elif solution.projects[0].get_attribute('project_type') == ProjectTypes.tool:
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

        linkerdirectories = list(solution.projects[0].get_attribute('include_folders'))
        if self.defaults.platformcode == 'dsi':
            linkerdirectories += [u'$(BURGER_SDKS)\\dsi\\burgerlib']

        if self.includedirectories or \
                linkerdirectories or \
                solution.projects[0].get_attribute('defines'):
            fp.write(u'\t<ItemDefinitionGroup>\n')

            #
            # Handle global compiler defines
            #

            if self.includedirectories or \
                    linkerdirectories or \
                    solution.projects[0].get_attribute('defines'):
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
                if solution.projects[0].get_attribute('defines'):
                    fp.write(u'\t\t\t<PreprocessorDefinitions>')
                    for define in solution.projects[0].get_attribute('defines'):
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


def generateold(solution):
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
    filename = os.path.join(solution.attributes['working_directory'],
                            solution.visualstudio.outputfilename + '.sln')
    if comparefiletostring(filename, fileref):
        if solution.get_attribute('verbose'):
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
        filename = os.path.join(solution.attributes['working_directory'],
                                solution.visualstudio.outputfilename +
                                projectsuffix[solution.visualstudio.fileversion.value])
        if comparefiletostring(filename, fileref):
            if solution.get_attribute('verbose'):
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
        filename = os.path.join(solution.attributes['working_directory'],
                                solution.visualstudio.outputfilename + '.vcxproj.filters')

        # No groups found?
        if count == 0:
            # Just delete the file
            delete_file(filename)
        else:
            # Did it change?
            if comparefiletostring(filename, fileref):
                if solution.get_attribute('verbose'):
                    print(filename + ' was not changed')
            else:
                # Update the file
                perforce_edit(filename)
                fp2 = io.open(filename, 'w')
                fp2.write(fileref.getvalue())
                fp2.close()
        fileref.close()

    return 0
