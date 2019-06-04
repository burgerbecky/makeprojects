#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Project file generator for Microsoft Visual Studio.

This module contains classes needed to generate
project files intended for use by
Microsoft's Visual Studio IDE
"""

## \package makeprojects.visualstudio

from __future__ import absolute_import, print_function, unicode_literals

import os
from uuid import NAMESPACE_DNS, UUID
from hashlib import md5
from burger import save_text_file_if_newer, convert_to_windows_slashes, \
    delete_file, escape_xml_cdata, escape_xml_attribute, \
    packed_paths, truefalse

from .enums import platformtype_short_code
from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes
from .core import source_file_filter

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


def vs2003_do_tree(xml_entry, filter_name, tree, groups):
    """
    Recursively create a Filter/File tree.

    Dump out a recursive tree of files to reconstruct a
    directory hiearchy for a file list with XML Filter
    records.

    Args:
        xml_entry: Root entry to attach records to.
        filter_name: Name of the current filter
        tree: dict() containing the file list
        groups: List of filter entries to match to the tree
    """

    # Process the tree in sorted order for consistency
    for item in sorted(tree):
        # Root entry has no slash.
        if filter_name == '':
            merged = item
        else:
            merged = filter_name + '\\' + item

        # Create the filter entry
        new_filter = VS2003Filter(item)
        xml_entry.add_element(new_filter)

        # See if this directory string creates a group?
        if merged in groups:
            # Found, add all the elements into this filter
            for fileitem in sorted(groups[merged]):
                new_filter.add_element(VS2003File(fileitem))

        tree_key = tree[item]
        # Recurse down the tree if there are sub entries
        if isinstance(tree_key, dict):
            vs2003_do_tree(new_filter, merged, tree_key, groups)

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

    # Save off the format header for the version of Visual Studio
    # being generated

    # Too many branches
    # Too many statements
    # pylint: disable=R0912,R0915

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
    for project in solution.project_list:

        # Save off the project record
        solution_lines.append(
            ('Project("{{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}}") '
             '= "{}", "{}", "{{{}}}"').format(
                 project.get_attribute('name'),
                 project.attributes['vs_output_filename'],
                 project.attributes['vs_uuid']))

        # Write out the dependencies, if any
        if project.project_list or solution.ide < IDETypes.vs2005:
            solution_lines.append(
                '\tProjectSection(ProjectDependencies) = postProject')
            for dependent in project.project_list:
                solution_lines.append(
                    '\t\t{{{0}}} = {{{0}}}'.format(
                        dependent.attributes['vs_uuid']))
            solution_lines.append('\tEndProjectSection')
        solution_lines.append('EndProject')

    # Begin the Global record
    solution_lines.append('Global')

    # Visual Studio 2003 format is unique, write it out in its
    # own exporter

    if solution.ide is IDETypes.vs2003:

        # Only output if there are attached projects, if there are
        # no projects, there is no need to output platforms
        config_list = []
        for project in solution.project_list:
            for configuration in project.configuration_list:
                entry = configuration.attributes['name']
                # Ignore duplicates
                if entry not in config_list:
                    config_list.append(entry)

        # List the configuration pairs (Like Xbox and Win32)
        solution_lines.append(
            '\tGlobalSection(SolutionConfiguration) = preSolution')
        for entry in config_list:
            # Since Visual Studio 2003 doesn't support
            # Platform/Configuration pairing,
            # it's faked with a space
            solution_lines.append('\t\t{0} = {0}'.format(entry))
        solution_lines.append('\tEndGlobalSection')

        # List all of the projects/configurations
        solution_lines.append(
            '\tGlobalSection(ProjectConfiguration) = postSolution')
        for project in solution.project_list:
            for configuration in project.configuration_list:
                # Using the faked Platform/Configuration pair used above,
                # create the appropriate pairs here and match them up.
                solution_lines.append(
                    '\t\t{{{0}}}.{1}.ActiveCfg = {2}'.format(
                        project.attributes['vs_uuid'],
                        configuration.attributes['name'],
                        configuration.attributes['vs_configuration_name']))
                solution_lines.append(
                    '\t\t{{{0}}}.{1}.Build.0 = {2}'.format(
                        project.attributes['vs_uuid'],
                        configuration.attributes['name'],
                        configuration.attributes['vs_configuration_name']))
        solution_lines.append('\tEndGlobalSection')

        # Put in stubs for these records.
        solution_lines.append(
            '\tGlobalSection(ExtensibilityGlobals) = postSolution')
        solution_lines.append('\tEndGlobalSection')

        solution_lines.append(
            '\tGlobalSection(ExtensibilityAddIns) = postSolution')
        solution_lines.append('\tEndGlobalSection')

    # All other versions of Visual Studio 2005 and later use this format
    # for the configurations
    else:

        if solution.project_list:
            # Write out the SolutionConfigurationPlatforms for all other
            # versions of Visual Studio

            solution_lines.append(
                '\tGlobalSection(SolutionConfigurationPlatforms) = preSolution')
            for project in solution.project_list:
                for configuration in project.configuration_list:
                    solution_lines.append(
                        '\t\t{0} = {0}'.format(
                            configuration.attributes['vs_configuration_name']))
            solution_lines.append('\tEndGlobalSection')

            # Write out the ProjectConfigurationPlatforms
            solution_lines.append(
                '\tGlobalSection(ProjectConfigurationPlatforms) = postSolution')

            for project in solution.project_list:
                for configuration in project.configuration_list:
                    solution_lines.append(
                        '\t\t{{{0}}}.{1}.ActiveCfg = {1}'.format(
                            project.attributes['vs_uuid'],
                            configuration.attributes['vs_configuration_name']))
                    solution_lines.append(
                        '\t\t{{{0}}}.{1}.Build.0 = {1}'.format(
                            project.attributes['vs_uuid'],
                            configuration.attributes['vs_configuration_name']))

            solution_lines.append('\tEndGlobalSection')

        # Hide nodes section
        solution_lines.append(
            '\tGlobalSection(SolutionProperties) = preSolution')
        solution_lines.append('\t\tHideSolutionNode = FALSE')
        solution_lines.append('\tEndGlobalSection')

        if solution.ide == IDETypes.vs2017:
            solution_lines.append(
                '\tGlobalSection(ExtensibilityGlobals) = postSolution')
            solution_lines.append(
                '\t\tSolutionGuid = {DD9C6A72-2C1C-45F2-9450-8BE7001FEE33}')
            solution_lines.append('\tEndGlobalSection')

        if solution.ide == IDETypes.vs2019:
            solution_lines.append(
                '\tGlobalSection(ExtensibilityGlobals) = postSolution')
            solution_lines.append(
                '\t\tSolutionGuid = {6B996D51-9872-4B32-A08B-EBDBC2A3151F}')
            solution_lines.append('\tEndGlobalSection')

    # Close it up!
    solution_lines.append('EndGlobal')
    return 0


########################################


class VS2003XML():
    r"""
    Visual Studio 2003-2008 XML formatter.

    Output XML elements in the format of Visual Studio 2003-2008.

    Visual Studio 2003-2008 only supports XML tags and attributes.
    There is no support for text between tags.

    Theses are examples of XML fragments this class exports.

    @code{.unparsed}
        <Platforms>
            <Platform
                Name="Win32"/>
        </Platforms>

    <Tool
        Name="VCMIDLTool"/>

    <-- force_pair disables support for "/>" closure -->
    <File
        RelativePath=".\source\Win32Console.cpp">
    </File>
    @endcode
    """

    def __init__(self, name, attribute_defaults=None, force_pair=False):
        """
        Set the defaults.
        Args:
            name: Name of the XML element
            attribute_defaults: dict of attributes to use as defaults.
            force_pair: If True, disable the use of /> XML suffix usage.
        """

        ## Name of this XML chunk.
        self.name = name

        ## Disable ``<foo/>`` syntax
        self.force_pair = force_pair

        ## List of name/data pairs
        self.attributes = []

        ## List of elements in this element.
        self.elements = []

        ## List of valid attributes and defaults
        self.attribute_defaults = {}

        # Add the defaults, if any
        self.add_defaults(attribute_defaults)

    ########################################

    def add_defaults(self, attribute_defaults):
        """
        Add a dict of attribute defaults.
        @details
        If any defaults were already present, they will be overwritten
        with the new values.

        Args:
            attribute_defaults: dict of attribute names and default values.
        """

        # Test for None
        if attribute_defaults:
            # Update the dictionary with the new defaults
            self.attribute_defaults.update(attribute_defaults)

            # Update the list of valid attributes to include
            # non None entries
            for item in attribute_defaults.items():
                if item[1] is not None:
                    self.set_attribute(item[0], item[1])

    ########################################

    def add_attribute(self, name, value):
        """
        Add an attribute to this XML element.

        Args:
            name: Name of the attribute
            value: Attribute data
        """
        self.attributes.append([name, value])

    ########################################

    def add_element(self, element):
        """
        Add an element to this XML element.

        Args:
            element: VS2003XML object
        """
        self.elements.append(element)

    ########################################

    def set_attribute(self, name, value):
        """
        Either change existing attribute or create a new one.
        @details
        If the attribute was not found, it will be appended to the list

        Args:
            name: String of the entry to match
            value: Value to substitute
        """

        # Iterate over the name/value pairs for a name match.
        for attribute in self.attributes:
            if attribute[0] == name:

                # Update the data
                attribute[1] = value
                break
        else:
            # Not found? Append the entry and then exit
            self.attributes.append([name, value])

    ########################################

    def remove_attribute(self, name):
        """
        Remove an attribute.
        @details
        If the value is in the list, remove it.

        Args:
            name: String of the entry to remove
        Returns:
            True if found and removed, False if not present.
        """

        for item in self.attributes:
            # Match? Kill it.
            if item[0] == name:
                self.attributes.remove(item)
                return True
        return False

    ########################################

    def reset_attribute(self, name):
        """
        Reset an attribute to default.
        @details
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

    ########################################

    def generate(self, line_list=None, indent=0):
        """
        Generate the text lines for this XML element.

        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
        Returns:
            line_list with all lines appended to it.
        """

        # Create the default
        if line_list is None:
            line_list = []

        # Determine the indentation
        # vs2003 uses tabs
        tabs = '\t' * indent

        # Special case, if no attributes, don't allow <foo/> XML
        # This is to duplicate the output of Visual Studio 2003-2008
        line_list.append('{0}<{1}'.format(tabs, escape_xml_cdata(self.name)))
        if self.attributes:

            # Output tag with attributes and support '/>' closing
            for attribute in self.attributes:
                line_list.append(
                    '{0}\t{1}="{2}"'.format(
                        tabs, escape_xml_cdata(
                            attribute[0]), escape_xml_attribute(attribute[1])))

            # Check if /> closing is disabled
            if not self.elements and not self.force_pair:
                line_list.append('{}/>'.format(tabs))
                return line_list
            # Close the open tag
            line_list.append('{}\t>'.format(tabs))
        else:
            line_list[-1] = line_list[-1] + '>'

        # Output the embedded elements
        for element in self.elements:
            element.generate(line_list, indent=indent + 1)

        # Close the current element
        line_list.append('{0}</{1}>'.format(tabs, escape_xml_cdata(self.name)))
        return line_list

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return '\n'.join(self.generate())

    ## Allow str() to work.
    __str__ = __repr__


########################################


class VS2003Tool(VS2003XML):
    """
    Helper class to output a Tool record for Visual Studio 2003-2008.

    In Visual Studio project files from version 2003 to 2008, Tool
    XML records were used for settings for each and every compiler tool
    """

    def __init__(self, name, force_pair=False):
        """
        Init a tool record with the tool name.
        Args:
            name: Name of the tool.
            force_pair: If True, disable the use of /> XML suffix usage.
        """
        VS2003XML.__init__(self, 'Tool', {'Name': name}, force_pair=force_pair)

########################################


class VCCLCompilerTool(VS2003Tool):
    """
    Visual Studio 2003-2008 VCCLCompilerTool record.
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration

        # Set the tag
        VS2003Tool.__init__(self, name='VCCLCompilerTool')

        # Create the defaults using the generic flags
        if configuration.get_attribute('optimization'):
            vs_optimization = '3'
            vs_inlinefunctionexpansion = '2'
            vs_enableintrinsicfunctions = 'true'
            vs_omitframepointers = 'true'
            vs_enablefibersafe = 'true'
        else:
            vs_optimization = '0'
            vs_inlinefunctionexpansion = None
            vs_enableintrinsicfunctions = None
            vs_omitframepointers = None
            vs_enablefibersafe = None

        if configuration.get_attribute('link_time_code_generation'):
            vs_link_time_code_generation = 'true'
        else:
            vs_link_time_code_generation = None

        if configuration.get_attribute('debug'):
            vs_buffersecuritychecks = 'true'
            vs_runtimelibrary = '1'
        else:
            vs_buffersecuritychecks = 'false'
            vs_runtimelibrary = '0'

        # Libaries have symbols
        if configuration.get_attribute('project_type').is_library() \
                or configuration.get_attribute('debug'):
            vs_debuginformationformat = '3'
            vs_programdatabasefilename = '"$(OutDir)$(TargetName).pdb"'
        else:
            vs_debuginformationformat = '0'
            vs_programdatabasefilename = None

        # Get the header includes
        include_folders = configuration.get_attribute_list(
            '_source_include_list')
        include_folders.extend(configuration.get_attribute_list(
            'include_folders_list'))

        # Get the defines
        define_list = configuration.get_attribute_list('define_list')

        self.add_defaults({
            # Optimization menu
            'Optimization': vs_optimization,
            'GlobalOptimizations': None,
            'InlineFunctionExpansion': vs_inlinefunctionexpansion,
            'EnableIntrinsicFunctions': vs_enableintrinsicfunctions,
            'ImproveFloatingPointConsistency': None,
            'FavorSizeOrSpeed': '1',
            'OmitFramePointers': vs_omitframepointers,
            'WholeProgramOptimization': vs_link_time_code_generation,
            'EnableFiberSafeOptimizations': vs_enablefibersafe,
            'OptimizeForProcessor': None,
            'OptimizeForWindowsApplication': None,

            # General menu
            'AdditionalIncludeDirectories':
                packed_paths(include_folders, slashes='\\'),
            'AdditionalUsingDirectories': None,
            'Detect64BitPortabilityProblems': None,
            'WarnAsError': None,

            # Preprocess menu
            'PreprocessorDefinitions': packed_paths(define_list),
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
            'FloatingPointModel': '2',
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
            'CompileAs': None,
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
    Visual Studio 2003-2008 VCCustomBuildTool record.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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
    Visual Studio 2003-2008 VCLinkerTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCLinkerTool')

        # Don't use $(TargetExt)
        vs_output = '"$(OutDir){}{}{}{}.exe"'.format(
            configuration.project.get_attribute('name'),
            configuration.project.solution.ide.get_short_code(),
            configuration.attributes['platform'].get_short_code(),
            configuration.attributes['short_code'])

        # Start with a copy (To prevent damaging the original list)
        library_folders = configuration.get_attribute_list(
            'library_folders_list')

        if configuration.get_attribute('project_type') == ProjectTypes.tool:
            # Console
            vs_subsystem = '1'
        else:
            # Application
            vs_subsystem = '2'

        # Link incremental if no optimizations
        if configuration.get_attribute('optimization'):
            vs_linkincremental = None
        else:
            vs_linkincremental = 'true'

        self.add_defaults({
            # General menu
            'OutputFile': vs_output,
            'ShowProgress': None,
            'Version': None,
            'LinkIncremental': vs_linkincremental,
            'SuppressStartupBanner': None,
            'IgnoreImportLibrary': None,
            'RegisterOutput': None,
            'AdditionalLibraryDirectories':
                packed_paths(library_folders, slashes='\\'),

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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCLibrarianTool')

        # Don't use $(TargetExt)
        vs_output = '"$(OutDir){}{}{}{}.lib"'.format(
            configuration.project.get_attribute('name'),
            configuration.project.solution.ide.get_short_code(),
            configuration.attributes['platform'].get_short_code(),
            configuration.attributes['short_code'])

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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCPostBuildEventTool')

        if configuration.get_attribute('deploy_folder') is not None:

            deploy_folder = convert_to_windows_slashes(
                configuration.get_attribute('deploy_folder'), True)

            project_type = configuration.get_attribute('project_type')
            platform = configuration.get_attribute('platform')

            # For windows, 64 bit and 32 bit tools go into seperate folders.

            if not project_type.is_library():
                if platform is PlatformTypes.win32:
                    deploy_folder = deploy_folder + 'x86\\'
                elif platform is PlatformTypes.win64:
                    deploy_folder = deploy_folder + 'x64\\'

            perforce = configuration.get_attribute('perforce')
            vs_description = 'Copying $(TargetName)$(TargetExt) to {}'.format(
                deploy_folder)

            vs_cmd = 'mkdir "{0}" 2>nul\r\n'.format(deploy_folder)

            if perforce:
                vs_cmd = ('{0}p4 edit "{1}$(TargetName)$(TargetExt)"\r\n'
                          'p4 edit "{1}$(TargetName).pdb"\r\n').format(
                              vs_cmd, deploy_folder)

            vs_cmd = ('{0}copy /Y "$(OutDir)$(TargetName)$(TargetExt)" '
                      '"{1}$(TargetName)$(TargetExt)"\r\n'
                      'copy /Y "$(OutDir)$(TargetName).pdb" '
                      '"{1}$(TargetName).pdb"\r\n').format(
                          vs_cmd, deploy_folder)
            if perforce:
                vs_cmd = ('{0}p4 revert -a "{1}$(TargetName)$(TargetExt)"\r\n'
                          'p4 revert -a "{1}$(TargetName).pdb"\r\n').format(
                              vs_cmd, deploy_folder)
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
    Visual Studio 2003-2008 for VCPreBuildEventTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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
    Visual Studio 2003-2008 for VCPreLinkEventTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
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
    Visual Studio 2003-2008 for VCResourceCompilerTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCResourceCompilerTool')
        self.add_defaults({
            'Culture': '1033'
        })

########################################


class XboxDeploymentTool(VS2003Tool):
    """
    XboxDeploymentTool for Xbox Classic.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration
        VS2003Tool.__init__(self, 'XboxDeploymentTool')

########################################


class XboxImageTool(VS2003Tool):
    """
    XboxImageTool for Xbox Classic.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration
        VS2003Tool.__init__(self, 'XboxImageTool')

########################################


class VCWebServiceProxyGeneratorTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCWebServiceProxyGeneratorTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCWebServiceProxyGeneratorTool')

########################################


class VCXMLDataGeneratorTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCXMLDataGeneratorTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCXMLDataGeneratorTool')

########################################


class VCWebDeploymentTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCWebDeploymentTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCWebDeploymentTool')

########################################


class VCManagedWrapperGeneratorTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCManagedWrapperGeneratorTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCManagedWrapperGeneratorTool')

########################################


class VCAuxiliaryManagedWrapperGeneratorTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCAuxiliaryManagedWrapperGeneratorTool.
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCAuxiliaryManagedWrapperGeneratorTool')

########################################


class VS2003Platform(VS2003XML):
    """
    Visual Studio 2003-2008 Platform record.
    """

    def __init__(self, platform):
        """
        Init defaults.

        Args:
            platform: PlatformTypes of the platform to build
        """

        ## PlatformTypes
        self.platform = platform

        VS2003XML.__init__(
            self, 'Platform', {
                'Name': platform.get_vs_platform()[0]})

########################################


class VS2003Platforms(VS2003XML):
    """
    Visual Studio 2003-2008 Platforms record
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        ## Parent platform
        self.project = project
        VS2003XML.__init__(self, 'Platforms')

        # Get the list of platforms
        platforms = set()
        for configuration in project.configuration_list:
            platforms.add(configuration.attributes['platform'])

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
        Set the defaults.
        """

        VS2003XML.__init__(self, 'References')

########################################


class VS2003ToolFiles(VS2003XML):
    """
    Visual Studio 2003-2008 ToolFiles record
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.platform = project
        VS2003XML.__init__(self, 'ToolFiles')

########################################


class VS2003Globals(VS2003XML):
    """
    Visual Studio 2003-2008 Globals record
    """

    def __init__(self):
        """
        Init defaults.
        """

        VS2003XML.__init__(self, 'Globals')

########################################


class VS2003Configuration(VS2003XML):
    """
    Visual Studio 2003-2008 Configuration record
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        # Too many branches
        # pylint: disable=R0912

        ## Parent configuration
        self.configuration = configuration

        ide = configuration.project.solution.ide
        platform = configuration.get_attribute('platform')
        project_type = configuration.get_attribute('project_type')

        vs_name = configuration.attributes['vs_configuration_name']
        vs_intdirectory = 'temp\\{}{}{}{}\\'.format(
            configuration.project.get_attribute('name'),
            configuration.project.solution.ide.get_short_code(),
            platform.get_short_code(),
            configuration.attributes['short_code'])

        if project_type is ProjectTypes.library:
            vs_configuration_type = '4'
        elif project_type is ProjectTypes.sharedlibrary:
            vs_configuration_type = '2'
        else:
            vs_configuration_type = '1'

        if configuration.get_attribute('link_time_code_generation'):
            vs_link_time_code_generation = '1'
        else:
            vs_link_time_code_generation = None

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
            'WholeProgramOptimization': vs_link_time_code_generation,
            'ReferencesPath': None
        })

        # Include all the data chunks
        self.add_element(VCPreBuildEventTool(configuration))
        self.add_element(VCCustomBuildTool(configuration))

        if platform is not PlatformTypes.xbox:
            self.add_element(VCXMLDataGeneratorTool(configuration))
            self.add_element(VCWebServiceProxyGeneratorTool(configuration))

        if platform.is_windows():
            self.add_element(VCMIDLTool(configuration))

        self.add_element(VCCLCompilerTool(configuration))

        if platform.is_windows():
            self.add_element(VCManagedResourceCompilerTool(configuration))
            self.add_element(VCResourceCompilerTool(configuration))

        self.add_element(VCPreLinkEventTool(configuration))

        if project_type.is_library():
            self.add_element(VCLibrarianTool(configuration))
        else:
            self.add_element(VCLinkerTool(configuration))

        if platform is PlatformTypes.xbox:
            self.add_element(XboxDeploymentTool(configuration))
            self.add_element(XboxImageTool(configuration))

        # add_element(VCManagedWrapperGeneratorTool(configuration))
        # add_element(VCAuxiliaryManagedWrapperGeneratorTool(configuration))

        self.add_element(VCALinkTool(configuration))
        self.add_element(VCManifestTool(configuration))
        self.add_element(VCXDCMakeTool(configuration))
        self.add_element(VCBscMakeTool(configuration))
        self.add_element(VCFxCopTool(configuration))
        self.add_element(VCAppVerifierTool(configuration))

        if ide is not IDETypes.vs2008:
            if platform is not PlatformTypes.xbox:
                self.add_element(VCWebDeploymentTool(configuration))

        self.add_element(VCPostBuildEventTool(configuration))

########################################


class VS2003Configurations(VS2003XML):
    """
    Visual Studio 2003-2008 Configurations record
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project

        VS2003XML.__init__(self, 'Configurations')
        for configuration in project.configuration_list:
            self.add_element(VS2003Configuration(configuration))


########################################


class VS2003File(VS2003XML):
    """
    Visual Studio 2003-2008 File record
    """

    def __init__(self, source_file):
        """
        Init defaults.

        Args:
            source_file: SourceFile record to extract defaults.
        """

        ## SourceFile record
        self.source_file = source_file
        VS2003XML.__init__(
            self, 'File', {'RelativePath': source_file}, force_pair=True)

########################################


class VS2003Filter(VS2003XML):
    """
    Visual Studio 2003-2008 File record
    """

    def __init__(self, name):
        """
        Init defaults.

        Args:
            name: name of the filter.
        """

        ## Name of the filter
        self.name = name

        VS2003XML.__init__(self, 'Filter', {'Name': name})


class VS2003Files(VS2003XML):
    """
    Visual Studio 2003-2008 Files record
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project
        VS2003XML.__init__(self, 'Files')

        # Create group names and attach all files that belong to that group
        groups = dict()
        for item in project.codefiles:
            groupname = item.get_group_name()

            # Put each filename in its proper group
            name = convert_to_windows_slashes(item.relative_pathname)
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
        vs2003_do_tree(self, '', tree, groups)

########################################


class VS2003vcproj(VS2003XML):
    """
    Visual Studio 2003-2008 formatter.

    This record instructs how to write a Visual Studio 2003-2008 format
    vcproj file.
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project

        # Which project type?
        ide = project.solution.ide
        if ide is IDETypes.vs2003:
            version = '7.10'
        elif ide is IDETypes.vs2005:
            version = '8.00'
        else:
            version = '9.00'

        VS2003XML.__init__(
            self, 'VisualStudioProject',
            {'ProjectType': 'Visual C++',
             'Version': version,
             'Name': project.get_attribute('name'),
             'ProjectGUID': '{' + project.attributes['vs_uuid'] + '}'})

        if ide is not IDETypes.vs2003:
            self.add_defaults({'RootNamespace': project.get_attribute('name')})

        self.add_defaults({'Keyword': 'Win32Proj'})
        if ide is IDETypes.vs2008:
            self.add_defaults({'TargetFrameworkVersion': '196613'})

        # Add all the sub chunks

        ## VS2003Platforms
        self.platforms = VS2003Platforms(project)
        self.add_element(self.platforms)

        ## VS2003ToolFiles
        self.toolfiles = VS2003ToolFiles(project)
        if ide is not IDETypes.vs2003:
            self.add_element(self.toolfiles)

        ## VS2003Configurations
        self.configuration_list = VS2003Configurations(project)
        self.add_element(self.configuration_list)

        ## VS2003References
        self.references = VS2003References()
        self.add_element(self.references)

        ## VS2003Files
        self.files = VS2003Files(project)
        self.add_element(self.files)

        ## VS2003Globals
        self.globals = VS2003Globals()
        self.add_element(self.globals)

    ########################################

    def generate(self, line_list=None, indent=0):
        """
        Write out the VisualStudioProject record.

        Args:
            line_list: string list to save the XML text
            indent: Level of indentation to begin with.
        """

        if line_list is None:
            line_list = []

        # XML is utf-8 only
        line_list.append('<?xml version="1.0" encoding="UTF-8"?>')
        return VS2003XML.generate(self, line_list=line_list, indent=indent)


########################################


class VS2010XML():
    """
    Visual Studio 2010- XML formatter.

    Output XML elements in the format of Visual Studio 2010-
    """

    def __init__(self, name, attribute_defaults=None, contents=None):
        """
        Set the defaults.
        Args:
            name: Name of the XML element
            attribute_defaults: dict of attributes to use as defaults.
            contents: String to insert between xml name tags.
        """

        ## Name of this XML chunk.
        self.name = name

        ## List of name/data attributes
        self.attributes = []

        ## List of elements in this element.
        self.elements = []

        ## List of valid attributes and defaults
        self.attribute_defaults = {}

        ## String contained in this XML chunk
        self.contents = contents

        # Add the defaults, if any
        self.add_defaults(attribute_defaults)

    ########################################

    def add_defaults(self, attribute_defaults):
        """
        Add a dict of attribute defaults.

        Args:
            attribute_defaults: dict of attribute names and default values.
        """

        # Test for None
        if attribute_defaults:
            # Update the dictionary with the new defaults
            self.attribute_defaults.update(attribute_defaults)

            # Update the list of valid attributes to include
            # non None entries
            for item in attribute_defaults.items():
                if item[1] is not None:
                    self.set_attribute(item[0], item[1])

    ########################################

    def add_attribute(self, name, value):
        """
        Add an attribute to this XML element.

        Args:
            name: Name of the attribute
            value: Attribute data
        """
        self.attributes.append([name, value])

    ########################################

    def add_element(self, element):
        """
        Add an element to this XML element.

        Args:
            element: VS2010XML object
        """
        self.elements.append(element)

    ########################################

    def add_tags(self, tag_list):
        """
        Add an earray of XML tags to this XML element.

        Args:
            tag_list: List of name/content pairs
        """

        for tag in tag_list:
            self.add_element(VS2010XML(tag[0], contents=tag[1]))

    ########################################

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

    ########################################

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

    ########################################

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

    ########################################

    def generate(self, line_list=None, indent=0):
        """
        Generate the text lines for this XML element.
        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
        """

        if line_list is None:
            line_list = []

        # Determine the indentation
        tabs = '  ' * indent

        # Output the tag
        line = '{0}<{1}'.format(tabs, escape_xml_cdata(self.name))

        # Output tag with attributes and support '/>' closing
        for attribute in self.attributes:
            line = '{0} {1}="{2}"'.format(line,
                                          escape_xml_cdata(attribute[0]),
                                          escape_xml_attribute(attribute[1]))

        if not self.elements and not self.contents:
            line_list.append(line + ' />')
            return line_list

        # Close the open tag
        line = line + '>'
        if self.contents:
            line = line + self.contents

        if not self.elements:
            line_list.append(
                '{0}</{1}>'.format(line, escape_xml_cdata(self.name)))
            return line_list

        line_list.append(line)
        # Output the embedded elements
        for element in self.elements:
            element.generate(line_list, indent=indent + 1)
        # Close the current element
        line_list.append('{0}</{1}>'.format(tabs, escape_xml_cdata(self.name)))
        return line_list

    ########################################

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return '\n'.join(self.generate())

    ## Allow str() to work.
    __str__ = __repr__


########################################


class VS2010ProjectConfiguration(VS2010XML):
    """
    Visual Studio 2010- ProjectConfiguration record
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration

        VS2010XML.__init__(
            self, 'ProjectConfiguration', {
                'Include':
                    configuration.get_attribute('vs_configuration_name')})

        self.add_tags((
            ('Configuration', configuration.get_attribute('name')),
            ('Platform', configuration.get_attribute('vs_platform'))))

########################################


class VS2010ProjectConfigurations(VS2010XML):
    """
    Visual Studio 2010- ProjectConfigurations record
    """

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project

        VS2010XML.__init__(self, 'ItemGroup', {
            'Label': 'ProjectConfigurations'})

        for configuration in project.configuration_list:
            self.add_element(VS2010ProjectConfiguration(configuration))

########################################


class VS2010NsightTegraProject(VS2010XML):
    """
    Visual Studio 2010- NsightTegraProject record
    """

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project

        VS2010XML.__init__(self, 'PropertyGroup', {
            'Label': 'NsightTegraProject'})
        self.add_tags((('NsightTegraProjectRevisionNumber', '11'),))


########################################


class VS2010ExtensionTargets(VS2010XML):
    """
    Visual Studio 2010- ExtensionTargets record
    """

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project

        VS2010XML.__init__(self, 'ImportGroup', {'Label': 'ExtensionTargets'})


########################################


class VS2010Globals(VS2010XML):
    """
    Visual Studio 2010- ProjectConfiguration record
    """

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project
        VS2010XML.__init__(self, 'PropertyGroup', {'Label': 'Globals'})

        tag_list = [
            ('ProjectName', project.get_attribute('name'))
        ]

        deploy_folder = project.get_attribute('deploy_folder')
        if deploy_folder:
            tag_list.append(
                ('FinalFolder',
                 convert_to_windows_slashes(
                     deploy_folder,
                     True)))
        tag_list.append(('ProjectGuid', '{{{}}}'.format(
            project.get_attribute('vs_uuid'))))

        if project.solution.ide >= IDETypes.vs2015:
            tag_list.append(('WindowsTargetPlatformVersion', '8.1'))

        self.add_tags(tag_list)


########################################


class VS2010Configuration(VS2010XML):
    """
    Visual Studio 2010- Configuration record
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration

        vs_configuration_name = configuration.get_attribute(
            'vs_configuration_name')

        VS2010XML.__init__(
            self, 'PropertyGroup',
            {'Condition': "'$(Configuration)|$(Platform)'=='{}'".format(
                vs_configuration_name),
             'Label': 'Configuration'})

        platform = configuration.get_attribute('platform')
        project_type = configuration.get_attribute('project_type')

        # Set the configuration type
        if project_type in (ProjectTypes.app, ProjectTypes.tool):
            configuration_type = 'Application'
        elif project_type is ProjectTypes.sharedlibrary:
            configuration_type = 'DynamicLibrary'
        else:
            configuration_type = 'StaticLibrary'

        tag_list = [
            ('ConfigurationType', configuration_type),
            # Enable debug libraries
            ('UseDebugLibraries', truefalse(
                configuration.get_attribute('debug')))
        ]

        # Which toolset to use?
        platform_toolset = configuration.get_attribute('vs_platform_toolset')
        if not platform_toolset:
            if platform.is_windows():
                platformtoolsets = {
                    IDETypes.vs2010: 'v100',
                    IDETypes.vs2012: 'v110_xp',
                    IDETypes.vs2013: 'v120_xp',
                    IDETypes.vs2015: 'v140_xp',
                    IDETypes.vs2017: 'v141_xp',
                    IDETypes.vs2019: 'v142'
                }
                platform_toolset = platformtoolsets.get(
                    configuration.project.solution.ide, 'v141_xp')

        if platform_toolset:
            tag_list.append(('PlatformToolset', platform_toolset))

        # Link time code generation
        tag_list.append(('WholeProgramOptimization', truefalse(
            configuration.get_attribute('link_time_code_generation'))))

        tag_list.append(('CharacterSet', 'Unicode'))

        self.add_tags(tag_list)

########################################


class VS2010ExtensionSettings(VS2010XML):
    """
    Visual Studio 2010- ExtensionSettings record
    """

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project
        VS2010XML.__init__(self, 'ImportGroup', {'Label': 'ExtensionSettings'})

########################################


class VS2010UserMacros(VS2010XML):
    """
    Visual Studio 2010- UserMacros record
    """

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project
        VS2010XML.__init__(self, 'PropertyGroup', {'Label': 'UserMacros'})

########################################


class VS2010PropertySheets(VS2010XML):
    """
    Visual Studio 2010- PropertySheets record
    """

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project

        VS2010XML.__init__(self, 'ImportGroup', {'Label': 'PropertySheets'})

        self.add_element(
            VS2010XML(
                'Import',
                {'Project':
                 '$(UserRootDir)\\Microsoft.Cpp.$(Platform).user.props',
                 'Condition':
                 "exists('$(UserRootDir)\\Microsoft.Cpp."
                 "$(Platform).user.props')",
                 'Label':
                 'LocalAppDataPlatform'}))


########################################


class VS2010PropertyGroup(VS2010XML):
    """
    Visual Studio 2010- PropertyGroup record
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        ## Parent configuration
        self.configuration = configuration

        vs_configuration_name = configuration.get_attribute(
            'vs_configuration_name')

        VS2010XML.__init__(
            self, 'PropertyGroup',
            {'Condition': "'$(Configuration)|$(Platform)'=='{}'".format(
                vs_configuration_name)})

        # Enable incremental linking
        self.add_element(
            VS2010XML(
                'LinkIncremental',
                contents=truefalse(
                    not configuration.get_attribute('optimization'))))


########################################


class VS2010ItemDefinitionGroup(VS2010XML):
    """
    Visual Studio 2010- ItemDefinitionGroup record
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        # Too many branches
        # Too many statements
        # pylint: disable=R0912,R0915

        ## Parent configuration
        self.configuration = configuration

        vs_configuration_name = configuration.get_attribute(
            'vs_configuration_name')

        VS2010XML.__init__(
            self, 'ItemDefinitionGroup',
            {'Condition': "'$(Configuration)|$(Platform)'=='{}'".format(
                vs_configuration_name)})

        self.compile = VS2010XML('ClCompile')
        self.link = VS2010XML('Link')

        # Prepend $(ProjectDir) to all source folders
        include_folders = []

        for item in configuration.get_attribute_list('_source_include_list'):
            include_folders.append('$(ProjectDir){}'.format(item))

        include_folders.extend(configuration.get_attribute_list(
            'include_folders_list'))

        if include_folders:
            include_folders.append('%(AdditionalIncludeDirectories)')
            self.compile.add_element(
                VS2010XML(
                    'AdditionalIncludeDirectories',
                    contents=packed_paths(
                        include_folders,
                        slashes='\\')))

        # Handle defines
        defines = configuration.get_attribute_list('define_list')
        if defines:
            defines.append('%(PreprocessorDefinitions)')
            self.compile.add_element(VS2010XML(
                'PreprocessorDefinitions', contents=packed_paths(defines)))

        # Start with a copy (To prevent damaging the original list)
        library_folders = configuration.get_attribute_list(
            'library_folders_list')

        if library_folders:
            library_folders.append('%(AdditionalLibraryDirectories)')
            self.link.add_element(
                VS2010XML(
                    'AdditionalLibraryDirectories',
                    contents=packed_paths(
                        library_folders,
                        slashes='\\')))

        self.compile.add_tags((
            ('WarningLevel', 'Level4'),
            ('DebugInformationFormat', 'ProgramDatabase'),
            ('ExceptionHandling', 'false'),
            ('FloatingPointModel', 'Fast'),
            ('RuntimeTypeInfo', 'false'),
            ('StringPooling', 'true'),
            ('FunctionLevelLinking', 'true'),
            ('MultiProcessorCompilation', 'true'),
            ('EnableFiberSafeOptimizations', 'true')
        ))

        platform = configuration.get_attribute('platform')
        project_type = configuration.get_attribute('project_type')
        if platform.is_windows():
            self.compile.add_element(
                VS2010XML(
                    'CallingConvention',
                    contents='FastCall'))

            if project_type is ProjectTypes.tool:
                subsystem = 'Console'
            else:
                subsystem = 'Windows'
            self.link.add_element(VS2010XML('SubSystem', contents=subsystem))

            if platform is PlatformTypes.win32:
                targetmachine = 'MachineX86'
            else:
                targetmachine = 'MachineX64'
            self.link.add_element(
                VS2010XML(
                    'TargetMachine',
                    contents=targetmachine))

        if platform in (PlatformTypes.ps3, PlatformTypes.ps4):
            if configuration.get_attribute('optimization'):
                self.compile.add_element(
                    VS2010XML(
                        'OptimizationLevel',
                        contents='Level2'))
                if platform is PlatformTypes.ps3:
                    self.compile.add_element(
                        VS2010XML(
                            'Branchless',
                            contents='Branchless2'))
            else:
                self.compile.add_element(
                    VS2010XML(
                        'OptimizationLevel',
                        contents='Level0'))

        if platform is PlatformTypes.vita:
            if project_type in (ProjectTypes.tool, ProjectTypes.app):
                self.link.add_tags((
                    ('DataStripping', 'StripFuncsAndData'),
                    ('DuplicateStripping', 'true')))

        if platform in (PlatformTypes.vita, PlatformTypes.ps3):
            self.compile.add_element(
                VS2010XML(
                    'CppLanguageStd',
                    contents='Cpp11'))

        self.link.add_tags((
            ('OptimizeReferences', 'true'),
            ('GenerateDebugInformation', 'true')))

        # Add the entries if they have elements
        if self.compile.elements:
            self.add_element(self.compile)
        if self.link.elements:
            self.add_element(self.link)

########################################


class VS2010Files(VS2010XML):
    """
    Visual Studio 2010- ItemGroup files record
    """

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        # Too many branches
        # Too many statements
        # pylint: disable=R0912,R0915

        ## Parent project
        self.project = project

        VS2010XML.__init__(self, 'ItemGroup')

        for item in source_file_filter(project.codefiles, FileTypes.h):
            self.add_element(
                VS2010XML(
                    'ClInclude', {
                        'Include': convert_to_windows_slashes(
                            item.relative_pathname)}))

        for item in source_file_filter(project.codefiles, FileTypes.cpp):
            self.add_element(
                VS2010XML(
                    'ClCompile', {
                        'Include': convert_to_windows_slashes(
                            item.relative_pathname)}))

        for item in source_file_filter(project.codefiles, FileTypes.rc):
            self.add_element(
                VS2010XML(
                    'ResourceCompile', {
                        'Include': convert_to_windows_slashes(
                            item.relative_pathname)}))

        for item in source_file_filter(project.codefiles, FileTypes.hlsl):
            name = convert_to_windows_slashes(item.relative_pathname)
            element = VS2010XML('HLSL', {'Include': name})
            self.add_element(element)

            # Cross platform way in splitting the path (MacOS doesn't like
            # windows slashes)
            basename = name.lower().rsplit('\\', 1)[1]
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

            element.add_tags((
                ('VariableName', 'g_' + splitname[0]),
                ('TargetProfile', profile)))

        for item in source_file_filter(project.codefiles, FileTypes.x360sl):
            name = convert_to_windows_slashes(item.relative_pathname)
            element = VS2010XML('X360SL', {'Include': name})
            self.add_element(element)

            # Cross platform way in splitting the path (MacOS doesn't like
            # windows slashes)
            basename = name.lower().rsplit('\\', 1)[1]
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

            element.add_tags((
                ('VariableName', 'g_' + splitname[0]),
                ('TargetProfile', profile)))

        for item in source_file_filter(project.codefiles, FileTypes.vitacg):
            name = convert_to_windows_slashes(item.relative_pathname)
            element = VS2010XML('VitaCGCompile', {'Include': name})
            self.add_element(element)

            # Cross platform way in splitting the path
            # (MacOS doesn't like windows slashes)
            basename = item.relative_pathname.lower().rsplit('\\', 1)[1]
            splitname = os.path.splitext(basename)
            if splitname[0].startswith('vs'):
                profile = 'sce_vp_psp2'
            else:
                profile = 'sce_fp_psp2'
            element.add_element(VS2010XML('TargetProfile', contents=profile))

        for item in source_file_filter(project.codefiles, FileTypes.glsl):
            self.add_element(
                VS2010XML(
                    'GLSL', {
                        'Include': convert_to_windows_slashes(
                            item.relative_pathname)}))

        if self.project.solution.ide >= IDETypes.vs2015:
            chunkname = 'Image'
        else:
            chunkname = 'None'
        for item in source_file_filter(project.codefiles, FileTypes.ico):
            self.add_element(
                VS2010XML(
                    chunkname, {
                        'Include': convert_to_windows_slashes(
                            item.relative_pathname)}))

########################################


class VS2010vcproj(VS2010XML):
    """
    Visual Studio 2010- formatter.

    This record instructs how to write a Visual Studio 2010- format vcproj file
    """

    # Too many instance attributes
    # pylint: disable=too-many-instance-attributes

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project

        # Which project type?
        ide = project.solution.ide
        if ide < IDETypes.vs2015:
            version = '4.0'
        else:
            version = '14.0'

        VS2010XML.__init__(
            self, 'Project',
            {'DefaultTargets': 'Build', 'ToolsVersion': version,
             'xmlns': 'http://schemas.microsoft.com/developer/msbuild/2003'})

        # Add all the sub chunks

        # Special case if using the nVidia Tegra toolset
        for configuration in project.configuration_list:
            if configuration.get_attribute('platform').is_android():
                self.add_element(VS2010NsightTegraProject(project))
                break

        ## VS2010ProjectConfigurations
        self.projectconfigurations = VS2010ProjectConfigurations(project)
        self.add_element(self.projectconfigurations)

        ## VS2010Globals
        self.globals = VS2010Globals(project)
        self.add_element(self.globals)

        self.add_element(
            VS2010XML(
                'Import',
                {'Project': '$(VCTargetsPath)\\Microsoft.Cpp.Default.props'}))

        for configuration in project.configuration_list:
            self.add_element(VS2010Configuration(configuration))

        vs_props = project.get_attribute('vs_props')
        if vs_props:
            for props in vs_props:
                props = convert_to_windows_slashes(props)
                self.add_element(
                    VS2010XML(
                        'Import', {
                            'Project':
                            props,
                            'Condition': "exists('{}')".format(props)}))

        self.add_element(
            VS2010XML(
                'Import',
                {'Project': '$(VCTargetsPath)\\Microsoft.Cpp.props'}))

        ## VS2010ExtensionSettings
        self.extensionsettings = VS2010ExtensionSettings(project)
        self.add_element(self.extensionsettings)

        ## VS2010PropertySheets
        self.propertysheets = VS2010PropertySheets(project)
        self.add_element(self.propertysheets)

        ## VS2010UserMacros
        self.usermacros = VS2010UserMacros(project)
        self.add_element(self.usermacros)

        for configuration in project.configuration_list:
            self.add_element(VS2010PropertyGroup(configuration))

        for configuration in project.configuration_list:
            self.add_element(VS2010ItemDefinitionGroup(configuration))

        ## VS2010Files
        self.files = VS2010Files(project)
        self.add_element(self.files)

        self.add_element(
            VS2010XML(
                'Import',
                {'Project': '$(VCTargetsPath)\\Microsoft.Cpp.targets'}))

        ## VS2010ExtensionTargets
        self.extensiontargets = VS2010ExtensionTargets(project)
        self.add_element(self.extensiontargets)

    ########################################

    def generate(self, line_list=None, indent=0):
        """
        Write out the VisualStudioProject record.

        Args:
            line_list: string list to save the XML text
            indent: Level of indentation to begin with.
        """

        if line_list is None:
            line_list = []
        # XML is utf-8 only
        line_list.append('<?xml version="1.0" encoding="utf-8"?>')
        return VS2010XML.generate(self, line_list=line_list, indent=indent)

########################################


class VS2010vcprojfilter(VS2010XML):
    """
    Visual Studio 2010- filter.

    This record instructs how to write a Visual Studio 2010- format vcproj file
    """

    def __init__(self, project):
        """
        Init defaults

        Args:
            project: Project record to extract defaults.
        """

        ## Parent project
        self.project = project

        # Which project type?
        ide = project.solution.ide
        if ide < IDETypes.vs2015:
            version = '4.0'
        else:
            version = '14.0'

        VS2010XML.__init__(
            self, 'Project',
            {'ToolsVersion': version,
             'xmlns': 'http://schemas.microsoft.com/developer/msbuild/2003'})

        ## Main ItemGroup
        self.main_element = VS2010XML('ItemGroup')
        self.add_element(self.main_element)

        groups = []
        self.write_filter_group(FileTypes.h, groups, 'ClInclude')
        self.write_filter_group(FileTypes.cpp, groups, 'ClCompile')
        self.write_filter_group(FileTypes.rc, groups, 'ResourceCompile')
        self.write_filter_group(FileTypes.hlsl, groups, 'HLSL')
        self.write_filter_group(FileTypes.x360sl, groups, 'X360SL')
        self.write_filter_group(FileTypes.vitacg, groups, 'VitaCGCompile')
        self.write_filter_group(FileTypes.glsl, groups, 'GLSL')

        # Visual Studio 2015 and later have a "compiler" for ico files
        if ide >= IDETypes.vs2015:
            self.write_filter_group(FileTypes.ico, groups, 'Image')
        else:
            self.write_filter_group(FileTypes.ico, groups, 'None')

        # Remove all duplicate in the groups
        groupset = sorted(set(groups))

        # Output the group list
        for item in groupset:
            item = convert_to_windows_slashes(item)
            groupuuid = get_uuid(
                project.attributes['vs_output_filename'] + item)
            filterxml = VS2010XML('Filter', {'Include': item})
            self.main_element.add_element(filterxml)
            filterxml.add_element(
                VS2010XML(
                    'UniqueIdentifier',
                    contents=groupuuid))

    ########################################

    def write_filter_group(self, file_type, groups, compilername):
        """
        Subroutine for saving out a group of filenames.

        Based based on compiler used.
        """

        # Iterate over the list
        for item in source_file_filter(self.project.codefiles, file_type):
            # Get the Visual Studio group name
            groupname = item.get_group_name()
            if groupname != '':
                # Add to the list of groups found
                groups.append(groupname)
                # Write out the record
                element = VS2010XML(
                    compilername, {
                        'Include': convert_to_windows_slashes(
                            item.relative_pathname)})
                self.main_element.add_element(element)
                element.add_element(VS2010XML('Filter', contents=groupname))

    ########################################

    def generate(self, line_list=None, indent=0):
        """
        Write out the VisualStudioProject record.

        Args:
            line_list: string list to save the XML text
            indent: Level of indentation to begin with.
        """

        if line_list is None:
            line_list = []

        # XML is utf-8 only
        line_list.append('<?xml version="1.0" encoding="utf-8"?>')
        return VS2010XML.generate(self, line_list, indent=indent)


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

    # Too many branches
    # Too many locals
    # pylint: disable=R0912,R0914

    # Since visual Studio 2003 and earlier doesn't support
    # x64 build targets, remove them before invoking the
    # XML generators

    if solution.ide < IDETypes.vs2005:
        for project in solution.project_list:
            configuration_list = []
            for configuration in project.configuration_list:
                if configuration.attributes['platform'] != PlatformTypes.win64:
                    configuration_list.append(configuration)
            project.configuration_list = configuration_list

    # Get the IDE name code
    idecode = solution.ide.get_short_code()

    # Get the platform code
    temp_list = []
    for project in solution.project_list:
        temp_list.extend(project.configuration_list)
    platformcode = platformtype_short_code(temp_list)

    # Create the final filename for the Visual Studio Solution file
    solution_filename = ''.join(
        (solution.get_attribute('name'), idecode, platformcode, '.sln'))

    # Older versions of Visual studio use the .vcproj extension
    # instead of the .vcxproj extension

    project_filename_suffix = '.vcxproj'
    if solution.ide in (IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008):
        project_filename_suffix = '.vcproj'

    # Iterate over the project files and create the filenames
    for project in solution.project_list:
        platformcode = platformtype_short_code(project.configuration_list)
        project.attributes['vs_output_filename'] = ''.join(
            (project.get_attribute('name'), idecode, platformcode,
             project_filename_suffix))
        project.attributes['vs_uuid'] = get_uuid(
            project.attributes['vs_output_filename'])
        for configuration in project.configuration_list:
            vs_platform = configuration.get_attribute(
                'platform').get_vs_platform()[0]
            configuration.attributes['vs_platform'] = vs_platform
            configuration.attributes['vs_configuration_name'] = '{}|{}'.format(
                configuration.get_attribute('name'), vs_platform)

    # Write to memory for file comparison
    solution_lines = []
    error = generate_solution_file(solution_lines, solution)
    if error:
        return error

    save_text_file_if_newer(
        os.path.join(solution.get_attribute(
            'working_directory'), solution_filename),
        solution_lines,
        bom=solution.ide != IDETypes.vs2003,
        perforce=solution.get_attribute('perforce'),
        verbose=solution.get_attribute('verbose'))

    # Now that the solution file was generated, create the individual project
    # files using the format appropriate for the selected IDE

    if solution.ide in (IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008):
        generator = VS2003vcproj
    else:
        generator = VS2010vcproj

    for project in solution.project_list:
        project.get_file_list([FileTypes.h,
                               FileTypes.cpp,
                               FileTypes.c,
                               FileTypes.rc,
                               FileTypes.ico,
                               FileTypes.hlsl,
                               FileTypes.glsl,
                               FileTypes.x360sl,
                               FileTypes.vitacg])
        exporter = generator(project)
        project_lines = []
        exporter.generate(project_lines)
        save_text_file_if_newer(
            os.path.join(
                solution.get_attribute('working_directory'),
                project.attributes['vs_output_filename']),
            project_lines,
            bom=solution.ide != IDETypes.vs2003,
            perforce=solution.get_attribute('perforce'),
            verbose=solution.get_attribute('verbose'))

        if solution.ide >= IDETypes.vs2010:
            exporter = VS2010vcprojfilter(project)
            filter_lines = []
            exporter.generate(filter_lines)

            file_name = os.path.join(
                solution.get_attribute('working_directory'),
                project.attributes['vs_output_filename'] + '.filters')
            if len(filter_lines) >= 4:
                save_text_file_if_newer(
                    file_name,
                    filter_lines,
                    bom=True,
                    perforce=solution.get_attribute('perforce'),
                    verbose=solution.get_attribute('verbose'))
            else:
                delete_file(file_name)
    return 0
