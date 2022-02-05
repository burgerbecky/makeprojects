#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Project file generator for Microsoft Visual Studio.

This module contains classes needed to generate
project files intended for use by
Microsoft's Visual Studio IDE
"""

## \package makeprojects.visual_studio_2010

# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

import os
from burger import save_text_file_if_newer, convert_to_windows_slashes, \
    delete_file, escape_xml_cdata, escape_xml_attribute, \
    packed_paths, truefalse

from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes
from .core import source_file_filter
from .visual_studio import get_uuid, create_deploy_script

SUPPORTED_IDES = (
    IDETypes.vs2010,
    IDETypes.vs2012,
    IDETypes.vs2013,
    IDETypes.vs2015,
    IDETypes.vs2017,
    IDETypes.vs2019,
    IDETypes.vs2022)

########################################


def test(ide, platform_type):
    """ Filter for supported platforms

    Args:
        ide: IDETypes
        platform_type: PlatformTypes
    Returns:
        True if supported, False if not
    """

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-return-statements

    if platform_type in (PlatformTypes.win32, PlatformTypes.win64):
        return True

    if ide is IDETypes.vs2010:
        if platform_type is PlatformTypes.xbox360:
            return True

    if ide >= IDETypes.vs2015:
        if platform_type is PlatformTypes.xboxone:
            return True

    if ide < IDETypes.vs2017:
        if platform_type in (PlatformTypes.ps3, PlatformTypes.vita):
            return True

    if ide >= IDETypes.vs2012:
        if platform_type in (PlatformTypes.ps4, PlatformTypes.wiiu):
            return True

    if ide >= IDETypes.vs2013:
        if platform_type in (PlatformTypes.tegra,
                             PlatformTypes.androidarm32,
                             PlatformTypes.androidarm64,
                             PlatformTypes.androidintel32,
                             PlatformTypes.androidintel64):
            return True

    if ide >= IDETypes.vs2015:
        if platform_type in (PlatformTypes.switch32, PlatformTypes.switch64):
            return True

    if ide >= IDETypes.vs2017:
        if platform_type in (PlatformTypes.winarm32, PlatformTypes.winarm64):
            return True

    return False


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
        IDETypes.vs2022: (
            '',
            'Microsoft Visual Studio Solution File, Format Version 12.00',
            '# Visual Studio Version 17',
            'VisualStudioVersion = 17.0.32112.339',
            'MinimumVisualStudioVersion = 10.0.40219.1')
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
                 project.name,
                 project.vs_output_filename,
                 project.vs_uuid))

        # Write out the dependencies, if any
        if project.project_list or solution.ide < IDETypes.vs2005:
            solution_lines.append(
                '\tProjectSection(ProjectDependencies) = postProject')
            for dependent in project.project_list:
                solution_lines.append(
                    '\t\t{{{0}}} = {{{0}}}'.format(
                        dependent.vs_uuid))
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
                entry = configuration.name
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
                        project.vs_uuid,
                        configuration.name,
                        configuration.vs_configuration_name))
                solution_lines.append(
                    '\t\t{{{0}}}.{1}.Build.0 = {2}'.format(
                        project.vs_uuid,
                        configuration.name,
                        configuration.vs_configuration_name))
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
                            configuration.vs_configuration_name))
            solution_lines.append('\tEndGlobalSection')

            # Write out the ProjectConfigurationPlatforms
            solution_lines.append(
                '\tGlobalSection(ProjectConfigurationPlatforms) = postSolution')

            for project in solution.project_list:
                for configuration in project.configuration_list:
                    solution_lines.append(
                        '\t\t{{{0}}}.{1}.ActiveCfg = {1}'.format(
                            project.vs_uuid,
                            configuration.vs_configuration_name))
                    solution_lines.append(
                        '\t\t{{{0}}}.{1}.Build.0 = {1}'.format(
                            project.vs_uuid,
                            configuration.vs_configuration_name))

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

        if solution.ide == IDETypes.vs2022:
            solution_lines.append(
                '\tGlobalSection(ExtensibilityGlobals) = postSolution')
            solution_lines.append(
                '\t\tSolutionGuid = {B6FA54F0-2622-4700-BD43-73EB0EBEFE41}')
            solution_lines.append('\tEndGlobalSection')

    # Close it up!
    solution_lines.append('EndGlobal')
    return 0


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
            if tag[1] is not None:
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

            # contents could be multi-line, deal with it.
            lines = escape_xml_cdata(self.contents).split('\n')
            line = line + lines.pop(0)
            if lines:
                line_list.append(line)
                line = lines.pop()
                line_list.extend(lines)

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
                    configuration.vs_configuration_name})

        self.add_tags((
            ('Configuration', configuration.name),
            ('Platform', configuration.vs_platform)))

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

        self.add_tags((
            ('NsightTegraProjectRevisionNumber', '11'),
        ))


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

        for props in project.vs_targets:
            props = convert_to_windows_slashes(props)
            self.add_element(
                VS2010XML(
                    'Import', {
                        'Project': props,
                        'Condition': "exists('{}')".format(props)}))


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

        ide = project.ide

        platform_version = None
        if ide >= IDETypes.vs2019:
            platform_version = '10.0'
        elif ide >= IDETypes.vs2015:

            # Special case if using the Xbox ONE toolset
            for configuration in project.configuration_list:
                if configuration.platform is PlatformTypes.xboxone:
                    platform_version = '8.1'
                    break
            else:
                platform_version = '10.0.18362.0'

        self.add_tags((
            ('ProjectName', project.name),
            ('ProjectGuid', '{{{}}}'.format(project.vs_uuid)),
            ('WindowsTargetPlatformVersion', platform_version)
        ))


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

        # pylint: disable=too-many-branches
        self.configuration = configuration

        vs_configuration_name = configuration.vs_configuration_name

        VS2010XML.__init__(
            self, 'PropertyGroup',
            {'Condition': "'$(Configuration)|$(Platform)'=='{}'".format(
                vs_configuration_name),
             'Label': 'Configuration'})

        platform = configuration.platform
        project_type = configuration.project_type

        # Set the configuration type
        if project_type in (ProjectTypes.app, ProjectTypes.tool):
            configuration_type = 'Application'
        elif project_type is ProjectTypes.sharedlibrary:
            configuration_type = 'DynamicLibrary'
        else:
            configuration_type = 'StaticLibrary'

        # Which toolset to use?
        platform_toolset = configuration.get_chained_value(
            'vs_platform_toolset')
        if not platform_toolset:
            if platform.is_windows():
                platformtoolsets = {
                    IDETypes.vs2010: 'v100',
                    IDETypes.vs2012: 'v110_xp',
                    IDETypes.vs2013: 'v120_xp',
                    IDETypes.vs2015: 'v140_xp',
                    IDETypes.vs2017: 'v141_xp',
                    IDETypes.vs2019: 'v142',
                    IDETypes.vs2022: 'v143'
                }
                platform_toolset = platformtoolsets.get(
                    configuration.ide, 'v141_xp')

                # ARM targets must use the non-xp toolset
                if platform_toolset.endswith('_xp'):
                    if platform in (PlatformTypes.winarm32,
                                    PlatformTypes.winarm64):
                        platform_toolset = platform_toolset[:-3]

            # Xbox ONE uses this tool chain
            elif platform is PlatformTypes.xboxone:
                platformtoolsets_one = {
                    IDETypes.vs2017: 'v141',
                    IDETypes.vs2019: 'v142',
                    IDETypes.vs2022: 'v143'
                }
                platform_toolset = platformtoolsets_one.get(
                    configuration.ide, 'v141')

        use_of_mfc = None
        use_of_atl = None
        clr_support = None
        android_min_api = None
        android_target_api = None
        nintendo_sdk_root = None

        if platform.is_windows():
            use_of_mfc = truefalse(configuration.use_mfc)
            use_of_atl = truefalse(configuration.use_atl)
            clr_support = truefalse(
                configuration.clr_support)

        # Handle android minimum tool set
        if platform.is_android():
            android_target_api = 'android-24'
            if platform in (PlatformTypes.androidintel64,
                            PlatformTypes.androidarm64):
                # 64 bit support was introduced in android 21
                # Lollipop 5.0
                android_min_api = 'android-21'
            else:
                android_min_api = 'android-9'

        # Nintendo Switch SDK location
        if platform.is_switch():
            nintendo_sdk_root = '$(NINTENDO_SDK_ROOT)\\'

        self.add_tags((
            ('ConfigurationType', configuration_type),
            # Enable debug libraries
            ('UseDebugLibraries', truefalse(
                configuration.debug)),
            ('PlatformToolset', platform_toolset),
            ('AndroidMinAPI', android_min_api),
            ('AndroidTargetAPI', android_target_api),
            ('WholeProgramOptimization', truefalse(
                configuration.link_time_code_generation)),
            ('CharacterSet', 'Unicode'),
            ('UseOfMfc', use_of_mfc),
            ('UseOfAtl', use_of_atl),
            ('CLRSupport', clr_support),
            ('NintendoSdkRoot', nintendo_sdk_root)
        ))

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

        for props in project.vs_props:
            props = convert_to_windows_slashes(props)
            self.add_element(
                VS2010XML(
                    'Import', {
                        'Project': props,
                        'Condition': "exists('{}')".format(props)}))

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

        vs_configuration_name = configuration.vs_configuration_name

        VS2010XML.__init__(
            self, 'PropertyGroup',
            {'Condition': "'$(Configuration)|$(Platform)'=='{}'".format(
                vs_configuration_name)})

        platform = configuration.platform
        remote_root = None
        image_xex_output = None
        run_code_analysis = None

        # Xbox 360 deployment file names
        if platform is PlatformTypes.xbox360:
            remote_root = 'xe:\\$(ProjectName)'
            image_xex_output = '$(OutDir)$(TargetName).xex'

        suffix = configuration.get_suffix()

        target_name = '$(ProjectName){}'.format(suffix)
        if platform.is_android():
            target_name = 'lib' + target_name

        int_dir = '$(ProjectDir)temp\\$(ProjectName){}\\'.format(suffix)

        if platform is PlatformTypes.win32:
            run_code_analysis = 'false'

        # Enable incremental linking
        self.add_tags((
            ('LinkIncremental', truefalse(
                not configuration.optimization)),
            ('TargetName', target_name),
            ('IntDir', int_dir),
            ('OutDir', '$(ProjectDir)bin\\'),
            ('RemoteRoot', remote_root),
            ('ImageXexOutput', image_xex_output),
            ('RunCodeAnalysis', run_code_analysis),
            ('CodeAnalysisRuleSet', 'AllRules.ruleset'),

            # This is needed for the Xbox 360
            ('OutputFile', '$(OutDir)$(TargetName)$(TargetExt)')
        ))

        # For the love of all that is holy, the Xbox ONE requires
        # these entries as is.
        if platform is PlatformTypes.xboxone:
            self.add_tags(
                (('ExecutablePath',
                  ('$(Console_SdkRoot)bin;$(VCInstallDir)bin\\x86_amd64;'
                   '$(VCInstallDir)bin;$(WindowsSDK_ExecutablePath_x86);'
                   '$(VSInstallDir)Common7\\Tools\\bin;'
                   '$(VSInstallDir)Common7\\tools;'
                   '$(VSInstallDir)Common7\\ide;'
                   '$(ProgramFiles)\\HTML Help Workshop;'
                   '$(MSBuildToolsPath32);$(FxCopDir);$(PATH);')),
                 ('IncludePath', '$(Console_SdkIncludeRoot)'),
                 ('ReferencePath',
                  '$(Console_SdkLibPath);$(Console_SdkWindowsMetadataPath)'),
                 ('LibraryPath', '$(Console_SdkLibPath)'),
                 ('LibraryWPath',
                  '$(Console_SdkLibPath);$(Console_SdkWindowsMetadataPath)'),
                 ('GenerateManifest', 'false')
                 ))

########################################


class VS2010ClCompile(VS2010XML):
    """
    Visual Studio 2010- ClCompile record
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        # Too many branches
        # Too many locals
        # Too many statements
        # pylint: disable=R0912,R0914,R0915

        ## Parent configuration
        self.configuration = configuration

        VS2010XML.__init__(self, 'ClCompile')

        platform = configuration.platform

        # Prepend $(ProjectDir) to all source folders
        include_folders = []
        for item in configuration.get_unique_chained_list(
                '_source_include_list'):
            include_folders.append('$(ProjectDir){}'.format(item))

        include_folders.extend(configuration.get_unique_chained_list(
            'include_folders_list'))

        if include_folders:
            include_folders = '{};%(AdditionalIncludeDirectories)'.format(
                packed_paths(include_folders, slashes='\\'))
        else:
            include_folders = None

        # Handle defines
        define_list = configuration.get_chained_list('define_list')
        if define_list:
            define_list = '{};%(PreprocessorDefinitions)'.format(
                packed_paths(define_list))
        else:
            define_list = None

        if configuration.debug:
            optimization = 'Disabled'
            if platform is PlatformTypes.xboxone:
                runtime_library = 'MultiThreadedDebugDLL'
            else:
                runtime_library = 'MultiThreadedDebug'
            omit_frame_pointers = 'false'
            basic_runtime_checks = 'EnableFastChecks'
            inline_function_expansion = 'OnlyExplicitInline'
            intrinic_functions = None
            buffer_security_check = None
            inline_assembly_optimization = None
        else:
            optimization = 'MinSpace'
            if platform is PlatformTypes.xboxone:
                runtime_library = 'MultiThreadedDLL'
            else:
                runtime_library = 'MultiThreaded'
            omit_frame_pointers = 'true'
            basic_runtime_checks = None
            inline_function_expansion = 'AnySuitable'
            intrinic_functions = 'true'
            buffer_security_check = 'false'
            inline_assembly_optimization = 'true'

        pre_fast = None
        call_cap = None
        # Not supported on the Xbox 360
        if platform is PlatformTypes.xbox360:
            omit_frame_pointers = None
            # Handle CodeAnalysis
            if configuration.analyze:
                pre_fast = 'Analyze'
            profile = configuration.get_chained_value('profile')
            if profile:
                call_cap = 'Callcap'
                if profile == 'fast':
                    call_cap = 'Fastcap'

        if platform is PlatformTypes.win32:
            calling_convention = 'FastCall'
        else:
            calling_convention = None
        optimization_level = None
        branchless = None
        cpp_language_std = None
        disable_specific_warnings = None
        set_message_to_silent = None
        additional_options = None
        omit_frame_pointer = None
        stack_protector = None
        strict_aliasing = None
        function_sections = None
        cpp_language_standard = None
        float_abi = None
        thumb_mode = None
        inline_functions = None
        char_unsigned = None

        if platform in (PlatformTypes.ps3, PlatformTypes.ps4):
            if configuration.optimization:
                optimization_level = 'Level2'
                if platform is PlatformTypes.ps3:
                    branchless = 'Branchless2'
            else:
                optimization_level = 'Level0'

        if platform in (PlatformTypes.vita, PlatformTypes.ps3):
            cpp_language_std = 'Cpp11'

        if platform is PlatformTypes.ps4:
            disable_specific_warnings = packed_paths(
                ['missing-braces',
                 'tautological-undefined-compare',
                 'unused-local-typedef'])

        if platform is PlatformTypes.wiiu:
            set_message_to_silent = '1795'
            additional_options = '--diag_suppress "1795"'

        if platform.is_android():
            if not configuration.debug:
                omit_frame_pointer = 'true'
                optimization_level = 'O3'
                stack_protector = 'false'
            strict_aliasing = 'true'
            function_sections = 'true'
            cpp_language_standard = 'gnu++11'

            # Disable these features when compiling Intel Android
            # to disable warnings from clang for intel complaining
            # about ARM specific commands
            if platform in (PlatformTypes.androidintel32,
                            PlatformTypes.androidintel64):
                float_abi = ''
                thumb_mode = ''

        # Switch
        if platform.is_switch():
            char_unsigned = 'false'
            if configuration.optimization:
                omit_frame_pointer = 'true'
                optimization_level = 'O3'
                inline_functions = 'true'

        self.add_tags((
            ('Optimization', optimization),
            ('RuntimeLibrary', runtime_library),
            ('OmitFramePointers', omit_frame_pointers),
            ('BasicRuntimeChecks', basic_runtime_checks),
            ('BufferSecurityCheck', buffer_security_check),
            ('InlineFunctionExpansion', inline_function_expansion),
            ('IntrinsicFunctions', intrinic_functions),
            ('InlineAssemblyOptimization', inline_assembly_optimization),
            ('MinimalRebuild', 'false'),
            ('GenerateDebugInformation', 'true'),
            ('AdditionalIncludeDirectories', include_folders),
            ('PreprocessorDefinitions', define_list),
            ('WarningLevel', 'Level4'),
            ('DebugInformationFormat', 'OldStyle'),
            ('ProgramDataBaseFileName', '$(OutDir)$(TargetName).pdb'),
            ('ExceptionHandling', 'false'),
            ('FloatingPointModel', 'Fast'),
            ('RuntimeTypeInfo', 'false'),
            ('StringPooling', 'true'),
            ('FunctionLevelLinking', 'true'),
            ('MultiProcessorCompilation', 'true'),
            ('EnableFiberSafeOptimizations', 'true'),
            ('PREfast', pre_fast),
            ('CallAttributedProfiling', call_cap),
            ('CallingConvention', calling_convention),
            ('OptimizationLevel', optimization_level),
            ('Branchless', branchless),
            ('CppLanguageStd', cpp_language_std),
            ('DisableSpecificWarnings', disable_specific_warnings),
            ('SetMessageToSilent', set_message_to_silent),
            ('StackProtector', stack_protector),
            ('OmitFramePointer', omit_frame_pointer),
            ('StrictAliasing', strict_aliasing),
            ('FunctionSections', function_sections),
            ('CppLanguageStandard', cpp_language_standard),
            ('FloatAbi', float_abi),
            ('ThumbMode', thumb_mode),
            ('Inlinefunctions', inline_functions),
            ('AdditionalOptions', additional_options),
            ('CharUnsigned', char_unsigned)
        ))


########################################


class VS2010Link(VS2010XML):
    """
    Visual Studio 2010- Link record
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        # Too many branches
        # pylint: disable=R0912

        ## Parent configuration
        self.configuration = configuration

        VS2010XML.__init__(self, 'Link')

        platform = configuration.platform
        project_type = configuration.project_type

        # Start with a copy (To prevent damaging the original list)
        library_folders = configuration.get_unique_chained_list(
            'library_folders_list')

        if library_folders:
            library_folders = '{};%(AdditionalLibraryDirectories)'.format(
                packed_paths(library_folders, slashes='\\'))
        else:
            library_folders = None

        additional_libraries = configuration.get_unique_chained_list(
            'libraries_list')
        if additional_libraries:
            if platform is PlatformTypes.xboxone:
                additional_libraries = '{}'.format(
                    packed_paths(additional_libraries))
            else:
                additional_libraries = '{};%(AdditionalDependencies)'.format(
                    packed_paths(additional_libraries))
        else:
            additional_libraries = None

        subsystem = None
        targetmachine = None
        data_stripping = None
        duplicate_stripping = None

        if platform.is_windows():
            if project_type is ProjectTypes.tool:
                subsystem = 'Console'
            else:
                subsystem = 'Windows'

            if platform is PlatformTypes.win32:
                targetmachine = 'MachineX86'
            elif platform is PlatformTypes.winarm32:
                targetmachine = 'MachineARM'
            elif platform is PlatformTypes.winarm64:
                targetmachine = 'MachineARM64'
            else:
                targetmachine = 'MachineX64'

        if platform is PlatformTypes.vita:
            if project_type in (ProjectTypes.tool, ProjectTypes.app):
                data_stripping = 'StripFuncsAndData'
                duplicate_stripping = 'true'

        if configuration.optimization:
            enable_comdat_folding = 'true'
            optimize_references = 'true'
        else:
            enable_comdat_folding = None
            optimize_references = 'false'

        if configuration.get_chained_value('profile'):
            profile = 'true'
        else:
            profile = None

        self.add_tags((
            ('AdditionalLibraryDirectories', library_folders),
            ('AdditionalDependencies', additional_libraries),
            ('SubSystem', subsystem),
            ('TargetMachine', targetmachine),
            ('DataStripping', data_stripping),
            ('DuplicateStripping', duplicate_stripping),
            ('OptimizeReferences', optimize_references),
            ('GenerateDebugInformation', 'true'),
            ('EnableCOMDATFolding', enable_comdat_folding),
            ('Profile', profile)
        ))

########################################


class VS2010Deploy(VS2010XML):
    """
    Visual Studio 2010- Deploy record
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        # Too many branches
        # pylint: disable=R0912

        ## Parent configuration
        self.configuration = configuration

        VS2010XML.__init__(self, 'Deploy')

        platform = configuration.platform
        project_type = configuration.project_type

        deployment_type = None
        dvd_emulation = None
        deployment_files = None

        if not project_type.is_library():
            if platform is PlatformTypes.xbox360:
                deployment_type = 'EmulateDvd'
                dvd_emulation = 'ZeroSeekTimes'
                deployment_files = '$(RemoteRoot)=$(ImagePath)'

        self.add_tags((
            ('DeploymentType', deployment_type),
            ('DvdEmulationType', dvd_emulation),
            ('DeploymentFiles', deployment_files)
        ))


########################################


class VS2010PostBuildEvent(VS2010XML):
    """
    Visual Studio 2010- PostBuildEvent record
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        # Too many branches
        # pylint: disable=R0912

        ## Parent configuration
        self.configuration = configuration

        VS2010XML.__init__(self, 'PostBuildEvent')

        vs_description, vs_cmd = create_deploy_script(configuration)

        self.add_tags((
            ('Message', vs_description),
            ('Command', vs_cmd)
        ))


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

        vs_configuration_name = configuration.vs_configuration_name

        VS2010XML.__init__(
            self, 'ItemDefinitionGroup',
            {'Condition': "'$(Configuration)|$(Platform)'=='{}'".format(
                vs_configuration_name)})

        ## ClCompile exporter
        self.compile = VS2010ClCompile(configuration)
        if self.compile.elements:
            self.add_element(self.compile)

        ## Link exporter
        self.link = VS2010Link(configuration)
        if self.link.elements:
            self.add_element(self.link)

        ## Deploy exporter
        self.deploy = VS2010Deploy(configuration)
        if self.deploy.elements:
            self.add_element(self.deploy)

        ## Post Build event
        self.postbuildevent = VS2010PostBuildEvent(configuration)
        if self.postbuildevent.elements:
            self.add_element(self.postbuildevent)

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
                ('TargetProfile', profile),
                ('HeaderFileName',
                 '%(RootDir)%(Directory)Generated\\%(FileName).h')))

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
                ('TargetProfile', profile),
                ('HeaderFileName',
                 '%(RootDir)%(Directory)Generated\\%(FileName).h')))

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
            element.add_element(
                VS2010XML(
                    'HeaderFileName',
                    contents='%(RootDir)%(Directory)Generated\\%(FileName).h'))

        for item in source_file_filter(project.codefiles, FileTypes.glsl):
            element = VS2010XML('GLSL', {'Include': convert_to_windows_slashes(
                item.relative_pathname)})
            self.add_element(element)
            element.add_tags(
                (('ObjectFileName',
                  '%(RootDir)%(Directory)Generated\\%(FileName).h'),))

        for item in source_file_filter(
            project.codefiles, FileTypes.appxmanifest):
            self.add_element(
                VS2010XML(
                    'AppxManifest', {
                        'Include': convert_to_windows_slashes(
                            item.relative_pathname)}))

        if self.project.ide >= IDETypes.vs2015:
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
        ide = project.ide
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
            if configuration.platform.is_android():
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
        ide = project.ide
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
        self.write_filter_group(FileTypes.appxmanifest, groups, 'AppxManifest')

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
                project.vs_output_filename + item)
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

    # Too many branches
    # Too many locals
    # pylint: disable=R0912,R0914

    # Failsafe
    if solution.ide not in SUPPORTED_IDES:
        return 10

    # For starters, generate the UUID and filenames for the solution file
    # for visual studio, since each solution and project file generate
    # seperately

    # Iterate over the project files and create the filenames
    for project in solution.project_list:

        project.vs_output_filename = '{}{}{}.vcxproj'.format(
            project.name, solution.ide_code, project.platform_code)
        project.vs_uuid = get_uuid(project.vs_output_filename)

        for configuration in project.configuration_list:
            vs_platform = configuration.platform.get_vs_platform()[0]
            configuration.vs_platform = vs_platform
            configuration.vs_configuration_name = '{}|{}'.format(
                configuration.name, vs_platform)

    # Write to memory for file comparison
    solution_lines = []
    error = generate_solution_file(solution_lines, solution)
    if error:
        return error

    # Get the output flags
    perforce = solution.perforce
    verbose = solution.verbose

    # Create the final filename for the Visual Studio Solution file
    solution_filename = '{}{}{}.sln'.format(
        solution.name, solution.ide_code, solution.platform_code)

    save_text_file_if_newer(
        os.path.join(solution.working_directory, solution_filename),
        solution_lines,
        bom=True,
        perforce=perforce,
        verbose=verbose)

    # Now that the solution file was generated, create the individual project
    # files using the format appropriate for the selected IDE

    for project in solution.project_list:
        project.get_file_list([FileTypes.h,
                               FileTypes.cpp,
                               FileTypes.c,
                               FileTypes.rc,
                               FileTypes.ico,
                               FileTypes.hlsl,
                               FileTypes.glsl,
                               FileTypes.x360sl,
                               FileTypes.vitacg,
                               FileTypes.appxmanifest])

        # Create the project file template
        exporter = VS2010vcproj(project)

        # Convert to a text file
        project_lines = []

        # Convert to a text file
        exporter.generate(project_lines)

        # Save the text
        save_text_file_if_newer(
            os.path.join(
                solution.working_directory,
                project.vs_output_filename),
            project_lines,
            bom=True,
            perforce=perforce,
            verbose=verbose)

        exporter = VS2010vcprojfilter(project)
        filter_lines = []
        exporter.generate(filter_lines)

        file_name = os.path.join(
            solution.working_directory,
            project.vs_output_filename + '.filters')
        if len(filter_lines) >= 4:
            save_text_file_if_newer(
                file_name,
                filter_lines,
                bom=True,
                perforce=perforce,
                verbose=verbose)
        else:
            delete_file(file_name)
    return 0
