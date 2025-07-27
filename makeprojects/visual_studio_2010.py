#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Project file generator for Microsoft Visual Studio.

This module contains classes needed to generate
project files intended for use by
Microsoft's Visual Studio IDE

@package makeprojects.visual_studio_2010

"""

# pylint: disable=consider-using-f-string
# pylint: disable=too-many-lines

from __future__ import absolute_import, print_function, unicode_literals

import os
from burger import convert_to_windows_slashes, escape_xml_cdata, \
    escape_xml_attribute, packed_paths, truefalse
from ide_gen import vs_calcguid

from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes, \
    source_file_filter
from .visual_studio_utils import get_toolset_version, \
    create_deploy_script

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

    def add_tag(self, tag_name, tag_value):
        """
        Add a XML tag to this XML element.

        Args:
            tag_name: Name of the tag
            tag_value: Value to assign to the tag
        """

        if tag_value is not None:
            self.add_element(VS2010XML(tag_name, contents=tag_value))

    ########################################

    def add_tags(self, tag_list):
        """
        Add an array of XML tags to this XML element.

        Args:
            tag_list: List of name/content pairs
        """

        for tag in tag_list:
            self.add_tag(tag[0], tag[1])

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
        tabs = "  " * indent

        # Output the tag
        line = "{0}<{1}".format(tabs, escape_xml_cdata(self.name))

        # Output tag with attributes and support "/>" closing
        for attribute in self.attributes:
            line = "{0} {1}=\"{2}\"".format(line,
                                          escape_xml_cdata(attribute[0]),
                                          escape_xml_attribute(attribute[1]))

        if not self.elements and not self.contents:
            line_list.append(line + " />")
            return line_list

        # Close the open tag
        line = line + ">"
        if self.contents:

            # contents could be multi-line, deal with it.
            lines = escape_xml_cdata(self.contents).split("\n")
            line = line + lines.pop(0)
            if lines:
                line_list.append(line)
                line = lines.pop()
                line_list.extend(lines)

        if not self.elements:
            line_list.append(
                "{0}</{1}>".format(line, escape_xml_cdata(self.name)))
            return line_list

        line_list.append(line)
        # Output the embedded elements
        for element in self.elements:
            element.generate(line_list, indent=indent + 1)
        # Close the current element
        line_list.append("{0}</{1}>".format(tabs, escape_xml_cdata(self.name)))
        return line_list

    ########################################

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return "\n".join(self.generate())

    def __str__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return self.__repr__()


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
            self, "ProjectConfiguration", {
                "Include":
                    configuration.vs_configuration_name})

        self.add_tag("Configuration", configuration.name)
        self.add_tag("Platform", configuration.vs_platform)

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

        VS2010XML.__init__(self, "ItemGroup", {
            "Label": "ProjectConfigurations"})

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

        VS2010XML.__init__(self, "PropertyGroup", {
            "Label": "NsightTegraProject"})

        self.add_tag("NsightTegraProjectRevisionNumber", "11")


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

        VS2010XML.__init__(self, "ImportGroup", {"Label": "ExtensionTargets"})

        for props in project.vs_targets:
            props = convert_to_windows_slashes(props)
            self.add_element(
                VS2010XML(
                    "Import", {
                        "Project": props,
                        "Condition": "exists('{}')".format(props)}))


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

        # pylint: disable=too-many-branches
        # pylint: disable=too-many-nested-blocks

        ## Parent project
        self.project = project
        VS2010XML.__init__(self, "PropertyGroup", {"Label": "Globals"})

        ide = project.ide

        # Check for the special case of Xbox ONE
        found_xbox = False
        if ide >= IDETypes.vs2017:
            for configuration in project.configuration_list:
                if configuration.platform.is_xbox():
                    found_xbox = True
                    break

        # Xbox ONE needs this entry
        if found_xbox:
            self.add_tag("ApplicationEnvironment", "title")

        # Name of the project
        self.add_tag("ProjectName", project.name)

        # Set the language
        if found_xbox:
            self.add_tag("DefaultLanguage", "en-US")

        self.add_tag("ProjectGuid", "{{{}}}".format(project.vs_uuid))

        # Check for the special case of Android for VS2022
        found_android = False
        if ide >= IDETypes.vs2022:
            for configuration in project.configuration_list:
                if configuration.platform.is_android():
                    found_android = True
                    break

        if found_android:
            self.add_tags((
                ("Keyword", "Android"),
                ("MinimumVisualStudioVersion", "14.0"),
                ("ApplicationType", "Android"),
                ("ApplicationTypeRevision", "3.0")
            ))
        else:

            # Test if WindowsTargetPlatformVersion is needed
            for configuration in project.configuration_list:
                if configuration.platform.is_switch():
                    break

            else:
                # Was there an override?
                platform_version = project.vs_platform_version

                # Create a default
                if platform_version is None:

                    # Visual Studio 2019 and higher allows using "Latest"
                    # SDK
                    if ide in (IDETypes.vs2019, IDETypes.vs2022):
                        platform_version = "10.0"

                    # Visual Studio 2015-2017 require explicit SDK
                    elif ide in (IDETypes.vs2015, IDETypes.vs2017):

                        # Special case if using the Xbox ONE toolset
                        # The Xbox ONE XDK requires 8.1, the GDK does not
                        for configuration in project.configuration_list:
                            if configuration.platform is PlatformTypes.xboxone:
                                platform_version = "8.1"
                                break
                        else:
                            # Set to the latest installed with 2017
                            platform_version = "10.0.17763.0"

                self.add_tag(
                    "WindowsTargetPlatformVersion",
                    platform_version)

        # The Xbox GDK requires to be declared as "C"
        if ide >= IDETypes.vs2017:
            for configuration in project.configuration_list:
                if configuration.platform in (
                        PlatformTypes.xboxgdk, PlatformTypes.xboxonex):
                    self.add_tag(
                        "GDKExtLibNames",
                        "Xbox.Services.API.C")
                    break


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
        # pylint: disable=too-many-statements

        self.configuration = configuration

        vs_configuration_name = configuration.vs_configuration_name

        VS2010XML.__init__(
            self, "PropertyGroup",
            {"Condition": "'$(Configuration)|$(Platform)'=='{}'".format(
                vs_configuration_name),
             "Label": "Configuration"})

        platform = configuration.platform
        project_type = configuration.project_type

        # Set the configuration type
        if project_type in (ProjectTypes.app, ProjectTypes.tool):
            configuration_type = "Application"
        elif project_type is ProjectTypes.sharedlibrary:
            configuration_type = "DynamicLibrary"
        else:
            configuration_type = "StaticLibrary"

        # Which toolset to use?
        platform_toolset = configuration.get_chained_value(
            "vs_platform_toolset")
        if not platform_toolset:
            if platform.is_windows():
                platformtoolsets = {
                    IDETypes.vs2010: "v100",
                    IDETypes.vs2012: "v110_xp",
                    IDETypes.vs2013: "v120_xp",
                    IDETypes.vs2015: "v140_xp",
                    IDETypes.vs2017: "v141_xp",
                    IDETypes.vs2019: "v142",
                    IDETypes.vs2022: "v143"
                }
                platform_toolset = platformtoolsets.get(
                    configuration.ide, "v141_xp")

                # ARM targets must use the non-xp toolset
                if platform_toolset.endswith("_xp"):
                    if platform in (PlatformTypes.winarm32,
                                    PlatformTypes.winarm64):
                        platform_toolset = platform_toolset[:-3]

            # Xbox ONE uses this tool chain
            elif platform.is_xboxone():
                platformtoolsets_one = {
                    IDETypes.vs2017: "v141",
                    IDETypes.vs2019: "v142",
                    IDETypes.vs2022: "v143"
                }
                platform_toolset = platformtoolsets_one.get(
                    configuration.ide, "v141")

            # The default is 5.0, but currently the Android plug in is
            # causing warnings with __ANDROID_API__. Fall back to 3.8
            elif platform.is_android():
                platform_toolset = "Clang_3_8"

        self.add_tags((
            ("ConfigurationType", configuration_type),
            # Enable debug libraries
            ("UseDebugLibraries", truefalse(
                configuration.debug)),
            ("PlatformToolset", platform_toolset)
        ))

        # Handle android minimum tool set
        if platform.is_android():
            if platform in (PlatformTypes.androidintel64,
                            PlatformTypes.androidarm64):
                # 64 bit support was introduced in android 21
                # Lollipop 5.0
                android_min_api = "android-21"
            else:
                android_min_api = "android-9"
            self.add_tag("AndroidMinAPI", android_min_api)
            self.add_tag("AndroidTargetAPI", "android-24")

        self.add_tag("WholeProgramOptimization", truefalse(
            configuration.link_time_code_generation))

        item = configuration.get_chained_value("vs_CharacterSet")
        if item:
            self.add_tag("CharacterSet", item)

        if platform.is_windows():
            if configuration.use_mfc is not None:
                self.add_tag("UseOfMfc", truefalse(configuration.use_mfc))
            if configuration.use_atl is not None:
                self.add_tag("UseOfAtl", truefalse(configuration.use_atl))
            if configuration.clr_support is not None:
                self.add_tag("CLRSupport", truefalse(
                    configuration.clr_support))

        # Nintendo Switch SDK location
        if platform.is_switch():
            self.add_tag("NintendoSdkRoot", "$(NINTENDO_SDK_ROOT)\\")
            self.add_tag("NintendoSdkSpec", "NX")
            item = getattr(configuration, "switch_build_type", "Debug")
            self.add_tag("NintendoSdkBuildType", item)

        # If Visual Studio 2022 for Windows or Xbox, use the 64 bit tools
        if configuration.ide >= IDETypes.vs2022:
            if platform.is_xbox() or platform.is_windows():
                self.add_tag("PreferredToolArchitecture", "x64")


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
        VS2010XML.__init__(self, "ImportGroup", {"Label": "ExtensionSettings"})

        for props in project.vs_props:
            props = convert_to_windows_slashes(props)
            self.add_element(
                VS2010XML(
                    "Import", {
                        "Project": props,
                        "Condition": "exists('{}')".format(props)}))

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
        VS2010XML.__init__(self, "PropertyGroup", {"Label": "UserMacros"})

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

        VS2010XML.__init__(self, "ImportGroup", {"Label": "PropertySheets"})

        self.add_element(
            VS2010XML(
                "Import",
                {"Project":
                 "$(UserRootDir)\\Microsoft.Cpp.$(Platform).user.props",
                 "Condition":
                 "exists('$(UserRootDir)\\Microsoft.Cpp."
                 "$(Platform).user.props')",
                 "Label":
                 "LocalAppDataPlatform"}))

        # Switch requires projects settings from the Nintendo SDK
        for configuration in project.configuration_list:
            if configuration.platform.is_switch():
                self.add_element(
                    VS2010XML(
                        "Import",
                        {"Project":
                        "$(NINTENDO_SDK_ROOT)\\Build\\VcProjectUtility\\"
                        "ImportNintendoSdk.props",
                        "Condition":
                        "exists('$(NINTENDO_SDK_ROOT)\\Build\\"
                        "VcProjectUtility\\ImportNintendoSdk.props')"}))
                break


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
            self, "PropertyGroup",
            {"Condition": "'$(Configuration)|$(Platform)'=='{}'".format(
                vs_configuration_name)})

        platform = configuration.platform
        remote_root = None
        image_xex_output = None
        run_code_analysis = None

        # Xbox 360 deployment file names
        if platform is PlatformTypes.xbox360:
            remote_root = "xe:\\$(ProjectName)"
            image_xex_output = "$(OutDir)$(TargetName).xex"

        suffix = configuration.get_suffix()

        target_name = "$(ProjectName){}".format(suffix)
        if platform.is_android():
            target_name = "lib" + target_name

        int_dir = "$(ProjectDir)temp\\$(ProjectName){}\\".format(suffix)

        if platform is PlatformTypes.win32:
            run_code_analysis = "false"

        # Enable incremental linking
        self.add_tags((
            ("LinkIncremental", truefalse(
                not configuration.optimization)),
            ("TargetName", target_name),
            ("IntDir", int_dir),
            ("OutDir", "$(ProjectDir)bin\\"),
            ("RemoteRoot", remote_root),
            ("ImageXexOutput", image_xex_output),
            ("RunCodeAnalysis", run_code_analysis),
            ("CodeAnalysisRuleSet", "AllRules.ruleset")
        ))

        # This is needed for the Xbox 360
        self.add_tag("OutputFile", "$(OutDir)$(TargetName)$(TargetExt)")

        # For the love of all that is holy, the Xbox ONE requires
        # these entries as is.
        if platform is PlatformTypes.xboxone:
            self.add_tag("ExecutablePath", (
                "$(DurangoXdkTools);"
                "$(DurangoXdkInstallPath)bin;"
                "$(FXCToolPath);"
                "$(VCInstallDir)bin\\x86_amd64;"
                "$(VCInstallDir)bin;$(WindowsSDK_ExecutablePath_x86);"
                "$(VSInstallDir)Common7\\Tools\\bin;"
                "$(VSInstallDir)Common7\\tools;"
                "$(VSInstallDir)Common7\\ide;"
                "$(ProgramFiles)\\HTML Help Workshop;"
                "$(MSBuildToolsPath32);"
                "$(FxCopDir);"
                "$(PATH)"))

            self.add_tag("ReferencePath", (
                "$(Console_SdkLibPath);"
                "$(Console_SdkWindowsMetadataPath)"))

            self.add_tag("LibraryPath", "$(Console_SdkLibPath)")

            self.add_tag("LibraryWPath", (
                "$(Console_SdkLibPath);"
                "$(Console_SdkWindowsMetadataPath)"))

            self.add_tag("IncludePath", (
                "$(Console_SdkIncludeRoot)\\um;"
                "$(Console_SdkIncludeRoot)\\shared;"
                "$(Console_SdkIncludeRoot)\\winrt"))

            self.add_tag("NativeExecutablePath", (
                "$(DurangoXdkTools);"
                "$(DurangoXdkInstallPath)bin;"
                "$(FXCToolPath);"
                "$(NativeExecutablePath)"))

            self.add_tag("SlashAI", (
                "$(Console_SdkWindowsMetadataPath);"
                "$(VCInstallDir)vcpackages;"
                "$(AdditionalUsingDirectories)"))

            self.add_tag("RemoveExtraDeployFiles", "true")

            self.add_tag("IsolateConfigurationsOnDeploy", "true")

        # The Xbox GDK has its own fun
        elif platform.is_xboxone():
            self.add_tag("ExecutablePath", (
                "$(Console_SdkRoot)bin;"
                "$(Console_SdkToolPath);"
                "$(ExecutablePath)"))

            self.add_tag("IncludePath", "$(Console_SdkIncludeRoot)")

            self.add_tag("ReferencePath", (
                "$(Console_SdkLibPath);"
                "$(Console_SdkWindowsMetadataPath)"))

            self.add_tag("LibraryPath", "$(Console_SdkLibPath)")

            self.add_tag("LibraryWPath", (
                "$(Console_SdkLibPath);"
                "$(Console_SdkWindowsMetadataPath)"))

        # Visual Studio Android puts multi-processor compilation here
        if platform.is_android() and configuration.ide >= IDETypes.vs2022:
            self.add_tag("UseMultiToolTask", "true")

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

        # I don't care
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        ## Parent configuration
        self.configuration = configuration

        VS2010XML.__init__(self, "ClCompile")

        platform = configuration.platform

        # Xbox ONE XDK is Windows RT
        if platform is PlatformTypes.xboxone and \
                not configuration.project_type.is_library():
            self.add_tag("CompileAsWinRT", "true")

        # Get the optimization setting
        if configuration.debug:
            item = "Disabled"
        elif platform is PlatformTypes.stadia:
            item = "Full"
        elif platform.is_android() and configuration.ide >= IDETypes.vs2022:
            item = "Full"
        else:
            item = "MinSpace"
        self.add_tag("Optimization", item)

        # Get the required run time library
        if configuration.debug:
            if platform.is_xboxone():
                item = "MultiThreadedDebugDLL"
            else:
                item = "MultiThreadedDebug"
        elif platform.is_xboxone():
            item = "MultiThreadedDLL"
        else:
            item = "MultiThreaded"
        self.add_tag("RuntimeLibrary", item)

        # Xbox has AVX, so use it
        if platform.is_xboxone():
            self.add_tag(
                "EnableEnhancedInstructionSet",
                "AdvancedVectorExtensions")

        # Not supported on the Xbox 360
        if platform is not PlatformTypes.xbox360:

            # Omit the frame pointers?
            if configuration.debug:
                item = "false"
            else:
                item = "true"
            self.add_tag("OmitFramePointers", item)

        # Add runtime checks on debug
        if configuration.debug:
            self.add_tag("BasicRuntimeChecks", "EnableFastChecks")

        # Don't do buffer checks on release builds
        if not configuration.debug:
            self.add_tag("BufferSecurityCheck", "false")

        # Inline functions
        # This is a hack, it appears that VS2022 for Windows ARM64
        # generates bad code on AnySuitable
        if configuration.debug or (
            configuration.ide >= IDETypes.vs2022 and \
                platform is PlatformTypes.winarm64):
            item = "OnlyExplicitInline"
        else:
            item = "AnySuitable"
        self.add_tag("InlineFunctionExpansion", item)

        # Intrinsic functions
        if not configuration.debug:
            self.add_tag("IntrinsicFunctions", "true")

        # Inline assembly interleaving and optimizations
        if not configuration.debug and platform is not PlatformTypes.xbox360:
            self.add_tag("InlineAssemblyOptimization", "true")

        # Always do a minimal rebuild
        self.add_tag("MinimalRebuild", "false")

        # Always include debugging information
        self.add_tag("GenerateDebugInformation", "true")

        # Prepend $(ProjectDir) to all source folders
        temp_list = []
        for item in configuration.get_unique_chained_list(
                "_source_include_list"):
            temp_list.append("$(ProjectDir){}".format(item))

        temp_list.extend(configuration.get_unique_chained_list(
            "include_folders_list"))

        if temp_list:
            temp_list = "{};%(AdditionalIncludeDirectories)".format(
                packed_paths(temp_list, slashes="\\"))
            self.add_tag("AdditionalIncludeDirectories", temp_list)

        # Handle preprocessor defines
        temp_list = configuration.get_chained_list("define_list")
        if temp_list:
            temp_list = "{};%(PreprocessorDefinitions)".format(
                packed_paths(temp_list))
            self.add_tag("PreprocessorDefinitions", temp_list)

        # Warning level for errors
        if platform is PlatformTypes.stadia or (
                platform.is_android() and configuration.ide >= IDETypes.vs2022):
            item = "EnableAllWarnings"
        else:
            item = "Level4"
        self.add_tag("WarningLevel", item)

        # Type of debug information
        item = "OldStyle"
        if platform.is_android() and configuration.ide >= IDETypes.vs2022:
            item = None

        # Handle Stadia
        if platform is PlatformTypes.stadia:
            item = None
            if configuration.debug:
                item = "FullDebug"
        self.add_tag("DebugInformationFormat", item)

        # Program database name
        self.add_tag("ProgramDataBaseFileName", "$(OutDir)$(TargetName).pdb")

        # Exception handling
        item = configuration.get_chained_value("vs_ExceptionHandling")
        if not item:
            if configuration.exceptions:
                item = "Sync"
                if (platform.is_android() and \
                        configuration.ide >= IDETypes.vs2022) \
                        or platform is PlatformTypes.stadia:
                    item = "Enabled"
            else:
                item = "false"
                if (platform.is_android() and \
                        configuration.ide >= IDETypes.vs2022) \
                        or platform is PlatformTypes.stadia:
                    item = "Disabled"
        self.add_tag("ExceptionHandling", item)

        # Floating point model
        self.add_tag("FloatingPointModel", "Fast")

        # Run time type info
        self.add_tag("RuntimeTypeInfo", "false")

        # Enable string pooling
        self.add_tag("StringPooling", "true")

        # Function level linking
        self.add_tag("FunctionLevelLinking", "true")

        omit_frame_pointer = None
        stack_protector = None
        strict_aliasing = None

        if platform.is_android():
            if not configuration.debug:
                omit_frame_pointer = "true"
                stack_protector = "false"
            strict_aliasing = "true"

        # Switch
        if platform.is_switch():
            if configuration.optimization:
                omit_frame_pointer = "true"

        # Stadia multiprocessor compilation
        if platform is PlatformTypes.stadia:
            self.add_tag("UseMultiToolTask", "true")
        # nVidia codeworks multiprocessor compilation
        elif platform.is_android() and configuration.ide < IDETypes.vs2017:
            self.add_tag("ProcessMax", "24")
        # All others
        elif not platform.is_android() \
                or configuration.ide < IDETypes.vs2022:
            self.add_tag("MultiProcessorCompilation", "true")

        self.add_tag("EnableFiberSafeOptimizations", "true")

        # Xbox ONE has using directories to the tool chain
        if platform.is_xboxone():
            self.add_tag("AdditionalUsingDirectories", "$(SlashAI)")
            if platform is not PlatformTypes.xboxone:
                self.add_tag("SupportJustMyCode", "false")

        # Profiling on the xbox 360
        if platform is PlatformTypes.xbox360:

            # Handle CodeAnalysis
            if configuration.analyze:
                self.add_tag("PREfast", "Analyze")

            profile = configuration.get_chained_value("profile")
            if profile:
                call_cap = "Callcap"
                if profile == "fast":
                    call_cap = "Fastcap"
                self.add_tag("CallAttributedProfiling", call_cap)

            # C or C++ for Xbox 360
            self.add_tag("CompileAs", "Default")

        # Set the x86 windows calling convention
        if platform is PlatformTypes.win32:
            if configuration.fastcall:
                self.add_tag("CallingConvention", "FastCall")

        # Set the optimization level
        item = None
        if platform in (PlatformTypes.ps3, PlatformTypes.ps4,
                PlatformTypes.ps5):
            if configuration.optimization:
                item = "Level2"
            else:
                item = "Level0"
        if platform.is_android() and configuration.optimization:
            item = "O3"

        if platform.is_switch() and configuration.optimization:
            # Don't use O3, it generates bad code
            item = "O2"
        self.add_tag("OptimizationLevel", item)

        # PS3 Branchless mode
        if platform is PlatformTypes.ps3 and configuration.optimization:
            self.add_tag("Branchless", "Branchless2")

        # PS3 and Vita allow CPP 11
        if platform in (PlatformTypes.vita, PlatformTypes.ps3):
            self.add_tag("CppLanguageStd", "Cpp11")

        if platform in (PlatformTypes.ps4, PlatformTypes.ps5):
            self.add_tag("DisableSpecificWarnings", packed_paths(
                ("missing-braces",
                 "tautological-undefined-compare",
                 "unused-local-typedef")))

        # Disable this warning on WiiU
        if platform is PlatformTypes.wiiu:
            self.add_tag("SetMessageToSilent", "1795")

        self.add_tags((
            ("StackProtector", stack_protector),
            ("OmitFramePointer", omit_frame_pointer),
            ("StrictAliasing", strict_aliasing)
        ))

        # nVidia android has CPP11
        if platform.is_android():
            self.add_tag("FunctionSections", "true")
            self.add_tag("CppLanguageStandard", "gnu++11")

        # Disable these features when compiling Intel Android
        # to disable warnings from clang for intel complaining
        # about ARM specific commands
        if platform in (PlatformTypes.androidintel32,
                PlatformTypes.androidintel64):
            self.add_tag("FloatAbi", "")
            self.add_tag("ThumbMode", "")

        # Switch has inline functions when optimizing
        if platform.is_switch() and configuration.optimization:
            self.add_tag("Inlinefunctions", "true")

        # Ensure that on the switch chars are signed
        if platform.is_switch():
            self.add_tag("CharUnsigned", "false")

        # WiiU needs this suppressed
        if platform is PlatformTypes.wiiu:
            self.add_tag("AdditionalOptions", "--diag_suppress \"1795\"")


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

        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        ## Parent configuration
        self.configuration = configuration

        VS2010XML.__init__(self, "Link")

        platform = configuration.platform
        project_type = configuration.project_type

        # Get the additional folders for libaries
        item = configuration.get_unique_chained_list(
            "library_folders_list")
        if item:
            item = "{};%(AdditionalLibraryDirectories)".format(
                packed_paths(item, slashes="\\"))
            self.add_tag("AdditionalLibraryDirectories", item)

        # Are there any additional library binaries to add?
        item = configuration.get_unique_chained_list(
            "libraries_list")
        if item:

            # Xbox ONE only has the paths, nothing more
            if platform.is_xboxone():
                item = "{}".format(packed_paths(item))
            else:
                # Playstation needs them converted to -l commands
                if platform in (PlatformTypes.ps4, PlatformTypes.ps5):
                    libs = []
                    for lib in item:
                        if lib.startswith("-l"):
                            libs.append(lib)
                        else:
                            libs.append("-l" + lib)
                    item = libs

                item = "{};%(AdditionalDependencies)".format(
                    packed_paths(item))

            # Add the tag
            self.add_tag("AdditionalDependencies", item)

        # Is there a subsystem needed?
        if platform.is_xboxone():
            self.add_tag("SubSystem", "Console")

        if platform.is_windows():
            if project_type is ProjectTypes.tool:
                item = "Console"
            else:
                item = "Windows"
            self.add_tag("SubSystem", item)

        targetmachine = None
        data_stripping = None
        duplicate_stripping = None

        if platform.is_windows():
            if platform is PlatformTypes.win32:
                targetmachine = "MachineX86"
            elif platform is PlatformTypes.winarm32:
                targetmachine = "MachineARM"
            elif platform is PlatformTypes.winarm64:
                targetmachine = "MachineARM64"
            else:
                targetmachine = "MachineX64"

        if platform is PlatformTypes.vita:
            if project_type in (ProjectTypes.tool, ProjectTypes.app):
                data_stripping = "StripFuncsAndData"
                duplicate_stripping = "true"

        self.add_tags((
            ("TargetMachine", targetmachine),
            ("DataStripping", data_stripping),
            ("DuplicateStripping", duplicate_stripping)
        ))

        # Optimize the references?
        if configuration.optimization:
            item = "true"
        else:
            item = "false"
        self.add_tag("OptimizeReferences", item)

        # Always add debug info
        self.add_tag("GenerateDebugInformation", "true")

        # Should common data/code be folded together?
        if configuration.optimization:
            self.add_tag("EnableCOMDATFolding", "true")

        # Switch may have meta data for the final build
        item = getattr(configuration, "switch_meta_source", None)
        if item:
            self.add_tag("FinalizeMetaSource", item)

        if configuration.get_chained_value("profile"):
            self.add_tag("Profile", "true")

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

        VS2010XML.__init__(self, "Deploy")

        platform = configuration.platform
        project_type = configuration.project_type

        deployment_type = None
        dvd_emulation = None
        deployment_files = None

        if not project_type.is_library():
            if platform is PlatformTypes.xbox360:
                deployment_type = "EmulateDvd"
                dvd_emulation = "ZeroSeekTimes"
                deployment_files = "$(RemoteRoot)=$(ImagePath)"

        self.add_tags((
            ("DeploymentType", deployment_type),
            ("DvdEmulationType", dvd_emulation),
            ("DeploymentFiles", deployment_files)
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

        VS2010XML.__init__(self, "PostBuildEvent")

        vs_description, vs_cmd = create_deploy_script(configuration)

        self.add_tags((
            ("Message", vs_description),
            ("Command", vs_cmd)
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
            self, "ItemDefinitionGroup",
            {"Condition": "'$(Configuration)|$(Platform)'=='{}'".format(
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

        VS2010XML.__init__(self, "ItemGroup")

        # Add in C++ headers, C files, etc
        self.addfiles(FileTypes.h, "ClInclude")
        self.addfiles((FileTypes.cpp, FileTypes.c), "ClCompile")
        self.addfiles((FileTypes.x86, FileTypes.x64), "MASM")
        self.addfiles((FileTypes.arm, FileTypes.arm64), "MARMASM")

        # Resource files
        self.addfiles(FileTypes.rc, "ResourceCompile")

        # WiiU assembly
        if project.platform_code == "wiu":
            self.addfiles(FileTypes.s, "ASM")

        # PS3 assembly
        if project.platform_code in (
                "ps3", "ps4", "ps5", "vit", "swi", "swia32", "swia64"):
            self.addfiles(FileTypes.s, "ClCompile")

        for item in source_file_filter(project.codefiles, FileTypes.hlsl):
            name = convert_to_windows_slashes(item.relative_pathname)
            element = VS2010XML("HLSL", {"Include": name})
            self.add_element(element)

            # Cross platform way in splitting the path (MacOS doesn't like
            # windows slashes)
            basename = name.lower().rsplit("\\", 1)[1]
            splitname = os.path.splitext(basename)
            if splitname[0].startswith("vs41"):
                profile = "vs_4_1"
            elif splitname[0].startswith("vs4"):
                profile = "vs_4_0"
            elif splitname[0].startswith("vs3"):
                profile = "vs_3_0"
            elif splitname[0].startswith("vs2"):
                profile = "vs_2_0"
            elif splitname[0].startswith("vs1"):
                profile = "vs_1_1"
            elif splitname[0].startswith("vs"):
                profile = "vs_2_0"
            elif splitname[0].startswith("ps41"):
                profile = "ps_4_1"
            elif splitname[0].startswith("ps4"):
                profile = "ps_4_0"
            elif splitname[0].startswith("ps3"):
                profile = "ps_3_0"
            elif splitname[0].startswith("ps2"):
                profile = "ps_2_0"
            elif splitname[0].startswith("ps"):
                profile = "ps_2_0"
            elif splitname[0].startswith("tx"):
                profile = "tx_1_0"
            elif splitname[0].startswith("gs41"):
                profile = "gs_4_1"
            elif splitname[0].startswith("gs"):
                profile = "gs_4_0"
            else:
                profile = "fx_2_0"

            element.add_tags((
                ("VariableName", "g_" + splitname[0]),
                ("TargetProfile", profile),
                ("HeaderFileName",
                 "%(RootDir)%(Directory)Generated\\%(FileName).h")))

        for item in source_file_filter(project.codefiles, FileTypes.x360sl):
            name = convert_to_windows_slashes(item.relative_pathname)
            element = VS2010XML("X360SL", {"Include": name})
            self.add_element(element)

            # Cross platform way in splitting the path (MacOS doesn't like
            # windows slashes)
            basename = name.lower().rsplit("\\", 1)[1]
            splitname = os.path.splitext(basename)
            if splitname[0].startswith("vs3"):
                profile = "vs_3_0"
            elif splitname[0].startswith("vs2"):
                profile = "vs_2_0"
            elif splitname[0].startswith("vs1"):
                profile = "vs_1_1"
            elif splitname[0].startswith("vs"):
                profile = "vs_2_0"
            elif splitname[0].startswith("ps3"):
                profile = "ps_3_0"
            elif splitname[0].startswith("ps2"):
                profile = "ps_2_0"
            elif splitname[0].startswith("ps"):
                profile = "ps_2_0"
            elif splitname[0].startswith("tx"):
                profile = "tx_1_0"
            else:
                profile = "fx_2_0"

            element.add_tags((
                ("VariableName", "g_" + splitname[0]),
                ("TargetProfile", profile),
                ("HeaderFileName",
                 "%(RootDir)%(Directory)Generated\\%(FileName).h")))

        for item in source_file_filter(project.codefiles, FileTypes.vitacg):
            name = convert_to_windows_slashes(item.relative_pathname)
            element = VS2010XML("VitaCGCompile", {"Include": name})
            self.add_element(element)

            # Cross platform way in splitting the path
            # (MacOS doesn't like windows slashes)
            basename = item.relative_pathname.lower().rsplit("\\", 1)[1]
            splitname = os.path.splitext(basename)
            if splitname[0].startswith("vs"):
                profile = "sce_vp_psp2"
            else:
                profile = "sce_fp_psp2"
            element.add_element(VS2010XML("TargetProfile", contents=profile))
            element.add_element(
                VS2010XML(
                    "HeaderFileName",
                    contents="%(RootDir)%(Directory)Generated\\%(FileName).h"))

        for item in source_file_filter(project.codefiles, FileTypes.glsl):
            element = VS2010XML("GLSL", {"Include": convert_to_windows_slashes(
                item.relative_pathname)})
            self.add_element(element)
            element.add_tags(
                (("ObjectFileName",
                  "%(RootDir)%(Directory)Generated\\%(FileName).h"),))

        # Appx manifest
        self.addfiles(FileTypes.appxmanifest, "AppxManifest")

        # Ico files
        if self.project.ide >= IDETypes.vs2015:
            chunkname = "Image"
        else:
            chunkname = "None"
        self.addfiles(FileTypes.ico, chunkname)
        self.addfiles(FileTypes.image, chunkname)

########################################

    def addfiles(self, file_types, xml_name):
        """
        Scan codefiles for a specific file type

        Args:
            file_types: FileTypes of interest
            xml_name: Visual Studio XML name
        """

        for item in source_file_filter(self.project.codefiles, file_types):

            # Create the file object
            new_xml = VS2010XML(
                xml_name, {
                    "Include": convert_to_windows_slashes(
                        item.relative_pathname)})

            # Add it to the chain
            self.add_element(new_xml)

            # Check if needs to be marked as "Not part of build"
            if xml_name in ("MASM", "MARMASM"):

                # Required for Visual Studio 2015 and higher, but present in all
                # versions
                for configuration in self.project.configuration_list:
                    if configuration.platform.is_xboxone():
                        break
                else:
                    element = VS2010XML(
                        "UseSafeExceptionHandlers", contents="true")
                    new_xml.add_element(element)
                    element.add_attribute("Condition", "'$(Platform)'=='Win32'")

                # Determine which target is acceptable
                acceptable = {
                    FileTypes.x86: ("Win32",),
                    FileTypes.x64: ("x64",
                                    "Durango",
                                    "Gaming.Xbox.XboxOne.x64",
                                    "Gaming.Xbox.Scarlett.x64"),
                    FileTypes.arm: ("ARM",),
                    FileTypes.arm64: ("ARM64",)
                }.get(item.type, [])

                # For early out
                processed = set()

                # Check if there are other platforms that this file
                # cannot be built on
                for configuration in self.project.configuration_list:
                    vs_platform = configuration.platform.get_vs_platform()[0]
                    if vs_platform in processed:
                        continue

                    processed.add(vs_platform)
                    if vs_platform not in acceptable:
                        new_xml.add_element(
                            VS2010XML(
                                "ExcludedFromBuild", {
                                    "Condition":
                                        "'$(Platform)'=='" + vs_platform + "'"},
                                "true"))

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

        # Which toolset version to use
        ide = project.ide
        version = get_toolset_version(ide)

        VS2010XML.__init__(
            self, "Project",
            {"DefaultTargets": "Build", "ToolsVersion": version,
             "xmlns": "http://schemas.microsoft.com/developer/msbuild/2003"})

        # Add all the sub chunks

        # Special case if using the nVidia Tegra toolset
        if ide < IDETypes.vs2022:
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
                "Import",
                {"Project": "$(VCTargetsPath)\\Microsoft.Cpp.Default.props"}))

        for configuration in project.configuration_list:
            self.add_element(VS2010Configuration(configuration))

        self.add_element(
            VS2010XML(
                "Import",
                {"Project": "$(VCTargetsPath)\\Microsoft.Cpp.props"}))

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
                "Import",
                {"Project": "$(VCTargetsPath)\\Microsoft.Cpp.targets"}))

        ## VS2010ExtensionTargets
        self.extensiontargets = VS2010ExtensionTargets(project)
        self.add_element(self.extensiontargets)

    ########################################

    def generate(self, line_list=None, indent=0, ide=None):
        """
        Write out the VisualStudioProject record.

        Args:
            line_list: string list to save the XML text
            indent: Level of indentation to begin with.
            ide: Version of Visual Studio to build for
        """

        # pylint: disable=unused-argument

        if line_list is None:
            line_list = []
        # XML is utf-8 only
        line_list.append('<?xml version="1.0" encoding="utf-8"?>')
        return VS2010XML.generate(
            self, line_list, indent)

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
            version = "4.0"
        else:
            version = "14.0"

        VS2010XML.__init__(
            self, "Project",
            {"ToolsVersion": version,
             "xmlns": "http://schemas.microsoft.com/developer/msbuild/2003"})

        ## Main ItemGroup
        self.main_element = VS2010XML("ItemGroup")
        self.add_element(self.main_element)

        groups = []
        self.write_filter_group(FileTypes.h, groups, "ClInclude")
        self.write_filter_group((FileTypes.cpp, FileTypes.c),
                                groups, "ClCompile")
        self.write_filter_group((FileTypes.x86, FileTypes.x64),
                                groups, "MASM")
        self.write_filter_group((FileTypes.arm, FileTypes.arm64),
                                groups, "MARMASM")

        # Generic assembly is assumed to be PowerPC for PS3
        if project.platform_code in (
                "ps3", "ps4", "ps5", "vit", "swi", "swia32", "swia64"):
            self.write_filter_group(FileTypes.s, groups, "ClCompile")

        self.write_filter_group(FileTypes.rc, groups, "ResourceCompile")
        self.write_filter_group(FileTypes.ppc, groups, "ASM")

        # Generic assembly is assumed to be PowerPC for WiiU
        if project.platform_code == "wiu":
            self.write_filter_group(FileTypes.s, groups, "ASM")

        self.write_filter_group(FileTypes.hlsl, groups, "HLSL")
        self.write_filter_group(FileTypes.x360sl, groups, "X360SL")
        self.write_filter_group(FileTypes.vitacg, groups, "VitaCGCompile")
        self.write_filter_group(FileTypes.glsl, groups, "GLSL")
        self.write_filter_group(FileTypes.appxmanifest, groups, "AppxManifest")

        # Visual Studio 2015 and later have a "compiler" for ico files
        if ide >= IDETypes.vs2015:
            self.write_filter_group(FileTypes.ico, groups, "Image")
            self.write_filter_group(FileTypes.image, groups, "Image")
        else:
            self.write_filter_group(FileTypes.ico, groups, "None")
            self.write_filter_group(FileTypes.image, groups, "None")

        # Remove all duplicate in the groups
        groupset = set(groups)

        # In the edge case that empty, intermediate groups need to be created
        # create them here
        for item in list(groupset):
            chunk = None
            while True:
                # Scan for directory delimiter
                index = item.find("\\")
                if index == -1:
                    break

                # Got the first entry?
                if chunk is None:
                    chunk = item[:index]
                else:
                    # Sub directory
                    chunk = chunk + "\\" + item[:index]

                # Check if the intermediate entry is not already in the list
                groupset.add(chunk)

                # Remove the chunk
                item = item[index + 1:]

        # Sort them
        groupset = sorted(groupset)

        # Output the group list
        for item in groupset:
            item = convert_to_windows_slashes(item)
            groupuuid = vs_calcguid(
                project.vs_output_filename + item)
            filterxml = VS2010XML("Filter", {"Include": item})
            self.main_element.add_element(filterxml)
            filterxml.add_element(
                VS2010XML(
                    "UniqueIdentifier",
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
            if groupname != "":

                # Add to the list of groups found
                groups.append(groupname)

                # Write out the record
                element = VS2010XML(
                    compilername, {
                        "Include": convert_to_windows_slashes(
                            item.relative_pathname)})
                self.main_element.add_element(element)
                element.add_element(VS2010XML("Filter", contents=groupname))

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
        line_list.append("<?xml version=\"1.0\" encoding=\"utf-8\"?>")
        return VS2010XML.generate(
            self, line_list, indent=indent)
