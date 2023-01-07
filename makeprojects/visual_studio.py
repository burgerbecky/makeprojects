#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Project file generator for Microsoft Visual Studio 2003-2008.

This module contains classes needed to generate project files intended for use
by Microsoft's Visual Studio 2003, 2005 and 2008.

@package makeprojects.visual_studio

@var makeprojects.visual_studio._SLNFILE_MATCH
Regex for matching files with *.sln

@var makeprojects.visual_studio.SUPPORTED_IDES
List of IDETypes the visual_studio module supports.

@var makeprojects.visual_studio._VS_VERSION_YEARS
Dict of version year strings to integers

@var makeprojects.visual_studio._VS_OLD_VERSION_YEARS
Dict of version year strings 2003-2012 to integers

@var makeprojects.visual_studio._VS_SDK_ENV_VARIABLE
Dict of environment variables for game consoles
"""

# pylint: disable=consider-using-f-string
# pylint: disable=invalid-name

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import operator
from uuid import NAMESPACE_DNS, UUID
from re import compile as re_compile
from hashlib import md5
from burger import save_text_file_if_newer, convert_to_windows_slashes, \
    escape_xml_cdata, escape_xml_attribute, is_string, where_is_visual_studio, \
    load_text_file

try:
    from wslwinreg import convert_to_windows_path
except ImportError:
    pass

from .validators import VSBooleanProperty, VSStringProperty, VSEnumProperty, \
    VSStringListProperty, VSIntegerProperty, lookup_enum_value
from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes
from .hlsl_support import HLSL_ENUMS, make_hlsl_command
from .glsl_support import make_glsl_command
from .build_objects import BuildObject, BuildError

SUPPORTED_IDES = (IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008)

_SLNFILE_MATCH = re_compile('(?is).*\\.sln\\Z')

_VS_VERSION_YEARS = {
    '2012': 2012,
    '2013': 2013,
    '14': 2015,
    '15': 2017,
    '16': 2019,
    '17': 2022
}

_VS_OLD_VERSION_YEARS = {
    '8.00': 2003,
    '9.00': 2005,
    '10.00': 2008,
    '11.00': 2010,
    '12.00': 2012
}

_VS_SDK_ENV_VARIABLE = {
    "PS3": "SCE_PS3_ROOT",          # PS3
    "ORBIS": "SCE_ORBIS_SDK_DIR",   # PS4
    "Prospero": "SCE_PROSPERO_SDK_DIR",  # PS5
    "PSP": "SCE_ROOT_DIR",          # PSP
    "PSVita": "SCE_PSP2_SDK_DIR",   # PS Vita
    "Xbox": "XDK",                  # Xbox classic
    "Xbox 360": "XEDK",             # Xbox 360
    "Xbox ONE": "DurangoXDK",       # Xbox ONE
    "Wii": "REVOLUTION_SDK_ROOT",   # Nintendo Wii
    "NX32": "NINTENDO_SDK_ROOT",    # Nintendo Switch
    "NX64": "NINTENDO_SDK_ROOT",    # Nintendo Switch
    "GGP": "GGP_SDK_PATH",          # Google Stadia
    "Android": "ANDROID_NDK_ROOT",  # Generic Android tools
    "ARM-Android-NVIDIA": "NVPACK_ROOT",        # nVidia android tools
    "AArch64-Android-NVIDIA": "NVPACK_ROOT",    # nVidia android tools
    "x86-Android-NVIDIA": "NVPACK_ROOT",        # nVidia android tools
    "x64-Android-NVIDIA": "NVPACK_ROOT",        # nVidia android tools
    "Tegra-Android": "NVPACK_ROOT"              # nVidia android tools
}

########################################


def parse_sln_file(full_pathname):
    """
    Find build targets in .sln file.

    Given a .sln file for Visual Studio 2003, 2005, 2008, 2010,
    2012, 2013, 2015, 2017 or 2019, locate and extract all of the build
    targets available and return the list.

    It will also determine which version of Visual
    Studio this solution file requires.

    Args:
        full_pathname: Pathname to the .sln file
    Returns:
        tuple(list of configuration strings, integer Visual Studio version year)
    See Also:
        build_visual_studio
    """

    # Load in the .sln file, it's a text file
    file_lines = load_text_file(full_pathname)

    # Version not known yet
    vs_version = 0

    # Start with an empty list
    target_list = []

    if file_lines:
        # Not looking for 'Visual Studio'
        looking_for_visual_studio = False

        # Not looking for EndGlobalSection
        looking_for_end_global_section = False

        # Parse
        for line in file_lines:

            # Scanning for 'EndGlobalSection'?

            if looking_for_end_global_section:

                # Once the end of the section is reached, end
                if 'EndGlobalSection' in line:
                    looking_for_end_global_section = False
                else:

                    # The line contains 'Debug|Win32 = Debug|Win32'
                    # Split it in half at the equals sign and then
                    # remove the whitespace and add to the list
                    target = line.split('=')[-1].strip()
                    if target not in target_list:
                        target_list.append(target)
                continue

            # Scanning for the secondary version number in Visual Studio 2012 or
            # higher

            if looking_for_visual_studio and '# Visual Studio' in line:
                # The line contains '# Visual Studio 15' or '# Visual Studio
                # Version 16'

                # Use the version number to determine which visual studio to
                # launch
                vs_version = _VS_VERSION_YEARS.get(line.rsplit()[-1], 0)
                looking_for_visual_studio = False
                continue

            # Get the version number
            if 'Microsoft Visual Studio Solution File' in line:
                # The line contains
                # 'Microsoft Visual Studio Solution File, Format Version 12.00'
                # The number is in the last part of the line
                # Use the version string to determine which visual studio to
                # launch
                vs_version = _VS_OLD_VERSION_YEARS.get(line.split()[-1], 0)
                if vs_version == 2012:
                    # 2012 or higher requires a second check
                    looking_for_visual_studio = True
                continue

            # Look for this section, it contains the configurations
            if '(SolutionConfigurationPlatforms)' in line or \
                    '(ProjectConfiguration)' in line:
                looking_for_end_global_section = True

    # Exit with the results
    if not vs_version:
        print(
            ('The visual studio solution file {} '
             'is corrupt or an unknown version!').format(full_pathname),
            file=sys.stderr)
    return (target_list, vs_version)

########################################


class BuildVisualStudioFile(BuildObject):
    """
    Class to build Visual Studio files

    Attributes:
        verbose: The verbose flag
        vs_version: The required version of Visual Studio
    """

    # pylint: disable=too-many-arguments
    def __init__(self, file_name, priority, configuration,
                 verbose=False, vs_version=0):
        """
        Class to handle Visual Studio solution files

        Args:
            file_name: Pathname to the *.sln to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
            vs_version: Integer Visual Studio version
        """

        super().__init__(file_name, priority, configuration=configuration)
        self.verbose = verbose
        self.vs_version = vs_version

    ########################################

    def build(self):
        """
        Build a visual studio .sln file.

        Supports Visual Studio 2005 - 2022. Supports platforms Win32, x64,
        Android, nVidia Tegra, PS3, ORBIS, PSP, PSVita, Xbox, Xbox 360,
        Xbox ONE, Switch, Wii

        Returns:
            List of BuildError objects
        See Also:
            parse_sln_file
        """

        # Locate the proper version of Visual Studio for this .sln file
        vstudiopath = where_is_visual_studio(self.vs_version)

        # Is Visual studio installed?
        if vstudiopath is None:
            msg = (
                '{} requires Visual Studio version {}'
                ' to be installed to build!').format(
                self.file_name, self.vs_version)
            print(msg, file=sys.stderr)
            return BuildError(0, self.file_name, msg=msg)

        # Certain targets require an installed SDK
        # verify that the SDK is installed before trying to build

        targettypes = self.configuration.rsplit('|')
        if len(targettypes) >= 2:
            test_env = _VS_SDK_ENV_VARIABLE.get(targettypes[1], None)
            if test_env:
                if os.getenv(test_env, default=None) is None:
                    msg = (
                        'Target {} was detected but the environment variable {}'
                        ' was not found.').format(
                        targettypes[1], test_env)
                    print(msg, file=sys.stderr)
                    return BuildError(
                        0,
                        self.file_name,
                        configuration=self.configuration,
                        msg=msg)

        # Create the build command
        # Note: Use the single line form, because Windows will not
        # process the target properly due to the presence of the | character
        # which causes piping.

        # Visual Studio 2003 doesn't support setting platforms, just use the
        # configuration name
        if self.vs_version == 2003:
            target = targettypes[0]
        else:
            target = self.configuration

        cmd = [vstudiopath, convert_to_windows_path(
            self.file_name), '/Build', target]
        if self.verbose:
            print(' '.join(cmd))
        sys.stdout.flush()

        return self.run_command(cmd, self.verbose)

    ########################################

    def clean(self):
        """
        Delete temporary files.

        This function is called by ``cleanme`` to remove temporary files.

        On exit, return 0 for no error, or a non zero error code if there was an
        error to report. None if not implemented or not applicable.

        Returns:
            None if not implemented, otherwise an integer error code.
        """

        # Locate the proper version of Visual Studio for this .sln file
        vstudiopath = where_is_visual_studio(self.vs_version)

        # Is Visual studio installed?
        if vstudiopath is None:
            msg = (
                '{} requires Visual Studio version {}'
                ' to be installed to build!').format(
                self.file_name, self.vs_version)
            print(msg, file=sys.stderr)
            return BuildError(0, self.file_name, msg=msg)

        # Certain targets require an installed SDK
        # verify that the SDK is installed before trying to build

        targettypes = self.configuration.rsplit('|')
        if len(targettypes) >= 2:
            test_env = _VS_SDK_ENV_VARIABLE.get(targettypes[1], None)
            if test_env:
                if os.getenv(test_env, default=None) is None:
                    msg = (
                        'Target {} was detected but the environment variable {}'
                        ' was not found.').format(
                        targettypes[1], test_env)
                    print(msg, file=sys.stderr)
                    return BuildError(
                        0,
                        self.file_name,
                        configuration=self.configuration,
                        msg=msg)

        # Create the build command
        # Note: Use the single line form, because Windows will not
        # process the target properly due to the presence of the | character
        # which causes piping.

        # Visual Studio 2003 doesn't support setting platforms, just use the
        # configuration name
        if self.vs_version == 2003:
            target = targettypes[0]
        else:
            target = self.configuration

        cmd = [vstudiopath, self.file_name, '/Clean', target]
        if self.verbose:
            print(' '.join(cmd))
        sys.stdout.flush()

        return self.run_command(cmd, self.verbose)


########################################


def match(filename):
    """
    Check if the filename is a type that this module supports

    Args:
        filename: Filename to match
    Returns:
        False if not a match, True if supported
    """

    return _SLNFILE_MATCH.match(filename)

########################################


def create_build_object(file_name, priority=50,
                 configurations=None, verbose=False):
    """
    Create BuildVisualStudioFile build records for every desired
    configuration

    Args:
        file_name: Pathname to the *.sln to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output
    Returns:
        list of BuildMakeFile classes
    """

    # Get the list of build targets
    targetlist, vs_version = parse_sln_file(file_name)

    # Was the file corrupted?
    if not vs_version:
        print(file_name + ' is corrupt!')
        return []

    results = []
    for target in targetlist:
        if configurations:
            targettypes = target.rsplit('|')
            if targettypes[0] not in configurations and \
                    targettypes[1] not in configurations:
                continue
        results.append(
            BuildVisualStudioFile(
                file_name,
                priority,
                target,
                verbose,
                vs_version))

    return results

########################################


def create_clean_object(file_name, priority=50,
                 configurations=None, verbose=False):
    """
    Create BuildVisualStudioFile clean records for every desired
    configuration

    Args:
        file_name: Pathname to the *.sln to build
        priority: Priority to clean this object
        configurations: Configuration list to clean
        verbose: True if verbose output
    Returns:
        list of BuildVisualStudioFile classes
    """

    # Get the list of build targets
    targetlist, vs_version = parse_sln_file(file_name)

    # Was the file corrupted?
    if not vs_version:
        print(file_name + ' is corrupt!')
        return []

    results = []
    for target in targetlist:
        if configurations:
            targettypes = target.rsplit('|')
            if targettypes[0] not in configurations and \
                    targettypes[1] not in configurations:
                continue
        results.append(
            BuildVisualStudioFile(
                file_name,
                priority,
                target,
                verbose,
                vs_version))

    return results

########################################


def test(ide, platform_type):
    """ Filter for supported platforms

    Args:
        ide: IDETypes
        platform_type: PlatformTypes
    Returns:
        True if supported, False if not
    """

    # Windows 32 is always supported
    if platform_type is PlatformTypes.win32:
        return True

    # Only vs 2003 supports xbox classic
    if ide is IDETypes.vs2003:
        return platform_type is PlatformTypes.xbox

    # Only vs 2005 and 2008 support Windows 64
    return platform_type is PlatformTypes.win64

########################################


def convert_file_name_vs2010(item):
    """ Convert macros from to Visual Studio 2003-2008
    Args:
        item: Filename string
    Returns:
        String with converted macros
    """
    if is_string(item):
        item = item.replace('%(RootDir)%(Directory)', '$(InputDir)')
        item = item.replace('%(FileName)', '$(InputName)')
        item = item.replace('%(Extension)', '$(InputExt)')
        item = item.replace('%(FullPath)', '$(InputPath)')
        item = item.replace('%(Identity)', '$(InputPath)')
    return item

########################################

# Boolean properties


def BoolUseUnicodeResponseFiles(configuration):
    """
    Entry for UseUnicodeResponseFiles

    Instructs the project system to generate UNICODE response files when
    spawning the librarian.  Set this property to True when files in the project
    have UNICODE paths.

    Note:
        Not available on Visual Studio 2003 and earlier.
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """

    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'UseUnicodeResponseFiles', configuration)
    return None


def BoolGlobalOptimizations(configuration):
    """ GlobalOptimizations

    Enables global optimizations incompatible with all 'Runtime Checks'
    options and edit and continue. Also known as WholeProgramOptimizations
    on other versions of Visual Studio.

    Compiler switch /Og

    Note:
        Only available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide is IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'GlobalOptimizations',
            configuration,
            default=configuration.optimization,
            options_key='compiler_options',
            options=(('/Og', True),))
    return None


def BoolRegisterOutput(configuration):
    """ RegisterOutput

    Specifies whether to register the primary output of this build to Windows.

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate('RegisterOutput', configuration)


def BoolPerUserRedirection(configuration):
    """ PerUserRedirection

    When Register Output is enabled, Per-user redirection forces registry
    writes to HKEY_CLASSES_ROOT to be redirected to HKEY_CURRENT_USER

    Note:
        Not available on Visual Studio 2005 and earlier
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2005:
        return VSBooleanProperty.vs_validate('PerUserRedirection', configuration)
    return None


def BoolIgnoreImportLibrary(configuration):
    """ IgnoreImportLibrary

    Specifies that the import library generated by this configuration should not
    be imported into dependent projects.

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate('IgnoreImportLibrary', configuration)


def BoolLinkLibraryDependencies(configuration):
    """ LinkLibraryDependencies

    Specifies whether or not library outputs from project dependencies are
    automatically linked in.

    Note:
        Not available on Visual Studio 2003 and earlier
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'LinkLibraryDependencies', configuration)
    return None


def BoolUseLibraryDependencyInputs(configuration):
    """ UseLibraryDependencyInputs

    Specifies whether or not the inputs to the librarian tool are used rather
    than the library file itself when linking in library outputs of project
    dependencies.

    Note:
        Not available on Visual Studio 2003 and earlier
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'UseLibraryDependencyInputs', configuration)
    return None


def BoolATLMinimizesCRunTimeLibraryUsage(configuration):
    """ ATLMinimizesCRunTimeLibraryUsage

    Tells ATL to link to the C runtime libraries statically to minimize
    dependencies; requires that 'Use of ATL' to be set.

    Note:
        Not available on Visual Studio 2008 or later
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide < IDETypes.vs2008:
        return VSBooleanProperty.vs_validate(
            'ATLMinimizesCRunTimeLibraryUsage', configuration)
    return None


def BoolEnableIntrinsicFunctions(configuration):
    """ EnableIntrinsicFunctions

    Enables intrinsic functions. Using intrinsic functions generates faster,
    but possibly larger, code.

    Compiler switch /Oi

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'EnableIntrinsicFunctions', configuration,
        default=configuration.optimization, options_key='compiler_options',
        options=(('/Oi', True),))


def BoolImproveFloatingPointConsistency(configuration):
    """ ImproveFloatingPointConsistency

    Enables intrinsic functions. Using intrinsic functions generates faster,
    but possibly larger, code.

    Compiler switch /Op

    Note:
        Only available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide is IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'ImproveFloatingPointConsistency', configuration,
            options_key='compiler_options',
            options=(('/Op', True),))
    return None


def BoolOmitFramePointers(configuration):
    """ OmitFramePointers

    Suppress frame pointers.

    Compiler switch /Oy

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'OmitFramePointers', configuration,
        configuration.optimization,
        options_key='compiler_options',
        options=(('/Oy', True),))


def BoolEnableFiberSafeOptimizations(configuration):
    """ EnableFiberSafeOptimizations

    Enables memory space optimization when using fibers and thread local
    torage access.

    Compiler switch /GT

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'EnableFiberSafeOptimizations', configuration,
        configuration.optimization,
        options_key='compiler_options',
        options=(('/GT', True),))


def BoolWholeProgramOptimization(configuration):
    """ WholeProgramOptimization

    Enables cross-module optimizations by delaying code generation to link
    time; requires that linker option 'Link Time Code Generation' be turned on.

    Compiler switch /GL

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'WholeProgramOptimization', configuration,
        configuration.link_time_code_generation,
        options_key='compiler_options',
        options=(('/GT', True),))


def BoolOptimizeForWindowsApplication(configuration):
    """ OptimizeForWindowsApplication

    Specify whether to optimize code in favor of Windows.EXE execution.

    Compiler switch /GA

    Note:
        Only available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide is IDETypes.vs2003:
        # Default to True because it's 2022.
        return VSBooleanProperty.vs_validate(
            'OptimizeForWindowsApplication', configuration,
            True,
            options_key='compiler_options',
            options=(('/GA', True),))
    return None


def BoolIgnoreStandardIncludePath(configuration):
    """ IgnoreStandardIncludePath

    Ignore standard include paths.

    Compiler switch /X

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'IgnoreStandardIncludePath', configuration,
        options_key='compiler_options',
        options=(('/X', True),))


def BoolKeepComments(configuration):
    """ KeepComments

    Suppresses comment strip from source code; requires that one of the
    'Preprocessing' options be set.

    Compiler switch /C

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'KeepComments', configuration,
        options_key='compiler_options',
        options=(('/C', True),))


def BoolStringPooling(configuration):
    """ StringPooling

    Enable read-only string pooling for generating smaller compiled code.

    Compiler switch /GF

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'StringPooling', configuration, True,
        options_key='compiler_options',
        options=(('/GF', True),))


def BoolMinimalRebuild(configuration):
    """ MinimalRebuild

    Detect changes to C++ class definitions and recompile only affected
    source files.

    Compiler switch /Gm

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'MinimalRebuild', configuration,
        options_key='compiler_options',
        options=(('/Gm', True),))


def BoolExceptionHandling(configuration):
    """ ExceptionHandling

    Calls destructors for automatic objects during a strack unwind caused
    by an exceptions being thrown.

    Compiler switches /EHsc, /EHa

    Note:
        A boolean on Visual Studio 2003, an enum on 2005/2008
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide is IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'ExceptionHandling', configuration,
            False,
            options_key='compiler_options',
            options=(('/EHsc', True), ('/EHa', True)))
    return None


def BoolSmallerTypeCheck(configuration):
    """ SmallerTypeCheck

    Enable checking for conversion to smaller types, incompatible with
    any optimization type other than debug.

    Compiler switch /RTCc

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'SmallerTypeCheck', configuration,
        None,
        options_key='compiler_options',
        options=(('/RTCc', True),))


def BoolBufferSecurityCheck(configuration):
    """ BufferSecurityCheck

    Check for buffer overruns; useful for closing hackable loopholes
    on internet servers; ignored for projects using managed extensions.

    Compiler switch /GS

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'BufferSecurityCheck', configuration,
        bool(configuration.debug),
        options_key='compiler_options',
        options=(('/GS', True),))


def BoolEnableFunctionLevelLinking(configuration):
    """ EnableFunctionLevelLinking

    Enables function-level linking; required for Edit and Continue to work.

    Compiler switch /Gy

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'EnableFunctionLevelLinking', configuration,
        True,
        options_key='compiler_options',
        options=(('/Gy', True),))


def BoolFloatingPointExceptions(configuration):
    """ FloatingPointExceptions

    Enable floating point exceptions when generating code.

    Compiler switch /fp:except

    Note:
        Not available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'FloatingPointExceptions', configuration,
            options_key='compiler_options',
            options=(('/fp:except', True),))
    return None


def BoolDisableLanguageExtensions(configuration):
    """ DisableLanguageExtensions

    Supresses or enables language extensions.

    Compiler switch /Za

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'DisableLanguageExtensions', configuration,
        options_key='compiler_options',
        options=(('/Za', True),))


def BoolDefaultCharIsUnsigned(configuration):
    """ DefaultCharIsUnsigned

    Sets the default char type to unsigned.

    Compiler switch /J

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'DefaultCharIsUnsigned', configuration,
        options_key='compiler_options',
        options=(('/J', True),))


def BoolTreatWChar_tAsBuiltInType(configuration):
    """ TreatWChar_tAsBuiltInType

    Treats wchar_t as a built-in type.

    Compiler switch /Zc:wchar_t

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'TreatWChar_tAsBuiltInType', configuration, True,
        options_key='compiler_options',
        options=(('/Zc:wchar_t', True),))


def BoolForceConformanceInForLoopScope(configuration):
    """ ForceConformanceInForLoopScope

    Forces the compiler to conform to the local scope in a for loop.

    Compiler switch /Zc:forScope

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'ForceConformanceInForLoopScope', configuration,
        options_key='compiler_options',
        options=(('/Zc:forScope', True),))


def BoolRuntimeTypeInfo(configuration):
    """ RuntimeTypeInfo

    Adds code for checking C++ object types at run time (runtime type
    information)

    Compiler switches /GR and /GR-

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'RuntimeTypeInfo', configuration, False,
        options_key='compiler_options',
        options=(('/GR', True), ('/GR-', False)))


def BoolOpenMP(configuration):
    """ OpenMP

    Enable OpenMP language extensions.

    Compiler switch /openmp

    Note:
        Not available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """

    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'OpenMP', configuration,
            options_key='compiler_options',
            options=(('/openmp', True),))
    return None


def BoolExpandAttributedSource(configuration):
    """ ExpandAttributedSource

    Create listing file with expanded attributes injected into source file.

    Compiler switch /Fx

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'ExpandAttributedSource', configuration,
        options_key='compiler_options',
        options=(('/Fx', True),))


def BoolGenerateXMLDocumentationFiles(configuration):
    """ GenerateXMLDocumentationFiles

    Specifies that the compiler should generate XML documentation comment files.

    Compiler switch /doc

    Note:
        Not available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'GenerateXMLDocumentationFiles', configuration,
            options_key='compiler_options',
            options=(('/doc', True),))
    return None


def BoolWarnAsError(configuration):
    """ WarnAsError

    Enables the compiler to treat all warnings as errors.

    Compiler switch /WX

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'WarnAsError', configuration,
        options_key='compiler_options',
        options=(('/WX', True),))


def BoolSuppressStartupBanner(configuration, options_key):
    """ SuppressStartupBanner

    Suppress the display of the startup banner and information messages.

    Compiler switch /nologo

    Args:
        configuration: Project configuration to scan for overrides.
        options_key: Options
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'SuppressStartupBanner', configuration,
        options_key=options_key,
        options=(('/nologo', True),))


def BoolDetect64BitPortabilityProblems(configuration):
    """ Detect64BitPortabilityProblems

    Tells the compiler to check for 64-bit portability issues.

    Compiler switch /Wp64

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'Detect64BitPortabilityProblems', configuration,
        options_key='compiler_options',
        options=(('/Wp64', True),))


def BoolShowIncludes(configuration):
    """ ShowIncludes

    Generates a list of include files with compiler output.

    Compiler switch /showIncludes

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'ShowIncludes', configuration,
        options_key='compiler_options',
        options=(('/showIncludes', True),))


def BoolUndefineAllPreprocessorDefinitions(configuration):
    """ UndefineAllPreprocessorDefinitions

    Undefine all previously defined preprocessor values.

    Compiler switch /u

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'UndefineAllPreprocessorDefinitions',
        configuration,
        options_key='compiler_options',
        options=(('/u', True),))


def BoolUseFullPaths(configuration):
    """ UseFullPaths

    Use full paths in diagnostic messages.

    Compiler switch /FC

    Note:
        Not available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'UseFullPaths',
            configuration,
            options_key='compiler_options',
            options=(('/FC', True),))
    return None


def BoolOmitDefaultLibName(configuration):
    """ OmitDefaultLibName

    Do not include default library names in .obj files.

    Compiler switch /Zl

    Note:
        Not available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'OmitDefaultLibName', configuration,
            options_key='compiler_options',
            options=(('/Zl', True),))
    return None


def BoolGenerateManifest(configuration):
    """ GenerateManifest

    Specifies if the linker should always generate a manifest file.

    Compiler switch /MANIFEST

    Note:
        Not available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'GenerateManifest', configuration,
            options_key='linker_options',
            options=(('/MANIFEST', True),))
    return None


def BoolEnableUAC(configuration):
    """ EnableUAC

    Specifies whether or not User Account Control is enabled.

    Compiler switches /MANIFESTUAC or /MANIFESTUAC:NO

    Note:
        Not available on Visual Studio 2003 or 2005
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2005:
        return VSBooleanProperty.vs_validate(
            'EnableUAC', configuration,
            options_key='linker_options',
            options=(('/MANIFESTUAC', True), ('/MANIFESTUAC:NO', False)))
    return None


def BoolUACUIAccess(configuration):
    """ UACUIAccess

    Specifies whether or not to bypass user interface protection levels for
    other windows on the desktop. Set this property to 'Yes' only for
    accessability applications.

    Compiler switches /MANIFESTUAC:uiAccess='true' or
    /MANIFESTUAC:uiAccess='false'

    Note:
        Not available on Visual Studio 2003 or 2005
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2005:
        return VSBooleanProperty.vs_validate(
            'UACUIAccess', configuration, options_key='linker_options',
            options=(("/MANIFESTUAC:uiAccess='true'", True),
                     ("/MANIFESTUAC:uiAccess='false'", False)))
    return None


def BoolIgnoreAllDefaultLibraries(configuration):
    """ IgnoreAllDefaultLibraries

    Ignore all default libraries during linking.

    Compiler switch /NODEFAULTLIB

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'IgnoreAllDefaultLibraries', configuration,
        options_key='linker_options', options=(('/NODEFAULTLIB', True),))


def BoolIgnoreEmbeddedIDL(configuration):
    """ IgnoreEmbeddedIDL

    Ignore embedded .idlsym sections of object files.

    Compiler switch /IGNOREIDL

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'IgnoreEmbeddedIDL', configuration,
        options_key='linker_options', options=(('/IGNOREIDL', True),))


def BoolGenerateDebugInformation(configuration):
    """ GenerateDebugInformation

    Enables generation of debug information.

    Compiler switch /DEBUG

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'GenerateDebugInformation', configuration, bool(configuration.debug),
        options_key='linker_options', options=(('/DEBUG', True),))


def BoolMapExports(configuration):
    """ MapExports

    Includes exported functions in map file information.

    Compiler switch /MAPINFO:EXPORTS

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'MapExports', configuration,
        options_key='linker_options', options=(('/MAPINFO:EXPORTS', True),))


def BoolGenerateMapFile(configuration):
    """ GenerateMapFile

    Enables generation of map file during linking.

    Compiler switch /MAP

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'GenerateMapFile', configuration,
        options_key='linker_options', options=(('/MAP', True),))


def BoolMapLines(configuration):
    """ MapLines

    Includes source code line number information in map file.

    Compiler switch /MAPINFO:LINES

    Note:
        Only available on Visual Studio 2003
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'MapLines', configuration,
            options_key='linker_options', options=(('/MAPINFO:LINES', True),))
    return None


def BoolSwapRunFromCD(configuration):
    """ SwapRunFromCD

    Run application from the swap location of the CD.

    Compiler switch /SWAPRUN:CD

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'SwapRunFromCD', configuration,
        options_key='linker_options', options=(('/SWAPRUN:CD', True),))


def BoolSwapRunFromNet(configuration):
    """ SwapRunFromNet

    Run application from the swap location of the Net.

    Compiler switch /SWAPRUN:NET

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'SwapRunFromNet', configuration,
        options_key='linker_options', options=(('/SWAPRUN:NET', True),))


def BoolResourceOnlyDLL(configuration):
    """ ResourceOnlyDLL

    Create DLL with no entry point; incompatible with setting the
    'Entry Point' option.

    Compiler switch /NOENTRY

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'ResourceOnlyDLL', configuration,
        options_key='linker_options', options=(('/NOENTRY', True),))


def BoolSetChecksum(configuration):
    """ SetChecksum

    Enables setting the checksum in the header of a .exe.

    Compiler switch /RELEASE

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'SetChecksum', configuration,
        options_key='linker_options', options=(('/RELEASE', True),))


def BoolTurnOffAssemblyGeneration(configuration):
    """ TurnOffAssemblyGeneration

    Specifies that no assembly will be generated even though common language
    runtime information is present in the object files.

    Compiler switch /NOASSEMBLY

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'TurnOffAssemblyGeneration', configuration,
        options_key='linker_options', options=(('/NOASSEMBLY', True),))


def BoolSupportUnloadOfDelayLoadedDLL(configuration):
    """ SupportUnloadOfDelayLoadedDLL

    Specifies allowing explicit unloading of the delayed load DLLs.

    Compiler switch /DELAY:UNLOAD

    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        'SupportUnloadOfDelayLoadedDLL', configuration,
        options_key='linker_options', options=(('/DELAY:UNLOAD', True),))


def BoolDelaySign(configuration):
    """ DelaySign

    Indicates whether the output assembly should be delay signed.

    Compiler switch /DELAYSIGN

    Note:
        Only available on Visual Studio 2005 or higher
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'DelaySign', configuration,
            options_key='linker_options', options=(('/DELAYSIGN', True),))
    return None


def BoolAllowIsolation(configuration):
    """ AllowIsolation

    Specifies manifest file lookup behavior for side-by-side assemblies.

    Compiler switch /ALLOWISOLATION:NO

    Note:
        Only available on Visual Studio 2005 or higher
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'AllowIsolation', configuration, options_key='linker_options',
            options=(('/ALLOWISOLATION:NO', False),))
    return None


def BoolProfile(configuration):
    """ Profile

    Produce an output file that can be used with the Enterprise Developer
    performance profiler.

    Compiler switch /PROFILE

    Note:
        Only available on Visual Studio 2005 or higher
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'Profile', configuration,
            options_key='linker_options', options=(('/PROFILE', True),))
    return None


def BoolCLRUnmanagedCodeCheck(configuration):
    """ CLRUnmanagedCodeCheck

    Specifies whether the linker will apply
    SuppressUnmanagedCodeSecurityAttribute to linker-generated PInvoke calls.

    Compiler switch /CLRUNMANAGEDCODECHECK

    Note:
        Only available on Visual Studio 2005 or higher
    Args:
        configuration: Project configuration to scan for overrides.
    Returns:
        None or VSBooleanProperty object.
    """
    if configuration.ide > IDETypes.vs2003:
        return VSBooleanProperty.vs_validate(
            'CLRUnmanagedCodeCheck', configuration,
            options_key='linker_options',
            options=(('/CLRUNMANAGEDCODECHECK', True),))
    return None


def BoolExcludedFromBuild(default=None):
    """ ExcludedFromBuild

    Ignore from build.

    Returns:
        None or VSBooleanProperty object.
    """
    return VSBooleanProperty('ExcludedFromBuild', default=default)

########################################

# Integer properties


def IntTypeLibraryResourceID():
    """ ID number of the library resource """
    return VSIntegerProperty("TypeLibraryResourceID", switch="/TLBID")


def IntHeapReserveSize():
    """ Amount of heap to reserve """
    return VSIntegerProperty("HeapReserveSize", switch="/HEAP")


def IntHeapCommitSize():
    """ Amount of heap to commit """
    return VSIntegerProperty("HeapCommitSize", switch="/HEAP:commit")


def IntStackReserveSize():
    """ Amount of stack to reserve """
    return VSIntegerProperty("StackReserveSize", switch="/STACK")


def IntStackCommitSize():
    """ Amount of stack to commit """
    return VSIntegerProperty("StackCommitSize", switch="/STACK:commit")

########################################

# String properties


def StringName(default):
    """ Name record """
    return VSStringProperty('Name', default=default)


def StringAdditionalOptions():
    """ List of custom compiler options as a single string """
    return VSStringProperty('AdditionalOptions')


def StringPrecompiledHeaderThrough():
    """ Text header file for precompilation """
    return VSStringProperty('PrecompiledHeaderThrough')


def StringPrecompiledHeaderFile():
    """ Binary header file for precompilation """
    return VSStringProperty('PrecompiledHeaderFile')


def StringAssemblerListingLocation():
    """ Output location for .asm file """
    return VSStringProperty('AssemblerListingLocation')


def StringObjectFile():
    """ Output location for .obj file """
    return VSStringProperty('ObjectFile')


def StringProgramDataBaseFileName(default):
    """ Output location of shared .pdb file """
    return VSStringProperty('ProgramDataBaseFileName', default=default)


def StringXMLDocumentationFileName():
    """ Name of the XML formatted documentation file """
    return VSStringProperty('XMLDocumentationFileName')


def StringBrowseInformationFile():
    """ Name of the browsing file """
    return VSStringProperty('BrowseInformationFile')


def StringDescription(default=None):
    """ Message to print in the console """
    return VSStringProperty('Description', default)


def StringCommandLine(default=None):
    """ Batch file contents """
    return VSStringProperty('CommandLine', default)


def StringOutputFile(default=None):
    """ Name of the output file """
    return VSStringProperty('OutputFile', default)

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


def create_copy_file_script(source_file, dest_file, perforce):
    """
    Create a batch file to copy a single file.

    Create a list of command lines to copy a file from source_file to
    dest_file with perforce support.

    This is an example of the Windows batch file. The lines for the
    tool 'p4' are added if perforce=True.

    @code
    p4 edit dest_file
    copy /Y source_file dest_file
    p4 revert -a dest_file
    @endcode

    Args:
        source_file: Pathname to the source file
        dest_file: Pathname to where to copy source file
        perforce: True if perforce commands should be generated.

    Returns:
        List of command strings for Windows Command shell.

    See Also:
        create_deploy_script
    """

    command_list = []

    # Check out the file
    if perforce:
        # Note, use ``cmd /c``` so if the call fails, the batch file will
        # continue
        command_list.append('cmd /c p4 edit "{}"'.format(dest_file))

    # Perform the copy
    command_list.append(
        ('copy /Y "{}" "{}"').format(source_file, dest_file))

    # Revert the file if it hasn't changed
    if perforce:
        command_list.append('cmd /c p4 revert -a "{}"'.format(dest_file))

    return command_list

########################################


def create_deploy_script(configuration):
    """
    Create a deployment batch file if needed.

    If an attribute of ``deploy_folder`` exists, a batch file
    will be returned that has the commands to copy the output file
    to the folder named in ``deploy_folder``.

    Two values are returned, the first is the command description
    suitable for Visual Studio Post Build and the second is the batch
    file string to perform the file copy. Both values are set to None
    if ``deploy_folder`` is empty.

    If a .pdb file exists, it's copied as well.

    Note:
        If the output is ``project_type`` of Tool, the folder will have
        x86 or x64 appended to it and any suffix stripped.

    @code
    mkdir final_folder
    p4 edit dest_file
    copy /Y source_file dest_file
    p4 revert -a dest_file
    p4 edit dest_file.pdb
    copy /Y source_file.pdb dest_file.pdb
    p4 revert -a dest_file.pdb
    @endcode

    Args:
        configuration: Configuration record.
    Returns:
        None, None or description and batch file string.

    See Also:
        create_copy_file_script
    """

    deploy_folder = configuration.deploy_folder

    # Don't deploy if no folder is requested.
    if not deploy_folder:
        return None, None

    # Ensure it's the correct slashes and end with a slash
    deploy_folder = convert_to_windows_slashes(deploy_folder, True)

    # Get the project and platform
    project_type = configuration.project_type
    platform = configuration.platform
    perforce = configuration.get_chained_value('perforce')

    # Determine where to copy and if pdb files are involved
    if project_type.is_library():
        deploy_name = '$(TargetName)'
    else:
        # For executables, use ProjectName to strip the suffix
        deploy_name = '$(ProjectName)'

        # Windows doesn't support fat files, so deploy to different
        # folders for tools
        if project_type is ProjectTypes.tool:
            if platform is PlatformTypes.win32:
                deploy_folder = deploy_folder + 'x86\\'
            elif platform is PlatformTypes.win64:
                deploy_folder = deploy_folder + 'x64\\'
            elif platform is PlatformTypes.winarm32:
                deploy_folder = deploy_folder + 'arm\\'
            elif platform is PlatformTypes.winarm64:
                deploy_folder = deploy_folder + 'arm64\\'
            elif platform is PlatformTypes.winitanium:
                deploy_folder = deploy_folder + 'ia64\\'

    # Create the batch file
    # Make sure the destination directory is present
    command_list = ['mkdir "{}" 2>nul'.format(deploy_folder)]

    # Copy the executable
    command_list.extend(
        create_copy_file_script(
            '$(TargetPath)',
            '{}{}$(TargetExt)'.format(deploy_folder, deploy_name),
            perforce))

    # Copy the symbols on Microsoft platforms
    # if platform.is_windows() or platform.is_xbox():
    #    if project_type.is_library() or configuration.debug:
    #       command_list.extend(
    #           create_copy_file_script(
    #              '$(TargetDir)$(TargetName).pdb',
    #               '{}{}.pdb'.format(deploy_folder, deploy_name),
    #               perforce))

    return 'Copying $(TargetFileName) to {}'.format(
        deploy_folder), '\n'.join(command_list)


########################################

def do_tree(xml_entry, filter_name, tree, groups):
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
        new_filter = VS2003Filter(item, xml_entry.project)
        xml_entry.add_element(new_filter)

        # See if this directory string creates a group?
        if merged in groups:
            # Found, add all the elements into this filter
            for fileitem in sorted(
                    groups[merged],
                    key=operator.attrgetter('vs_name')):
                new_filter.add_element(VS2003File(fileitem, xml_entry.project))

        tree_key = tree[item]
        # Recurse down the tree if there are sub entries
        if isinstance(tree_key, dict):
            do_tree(new_filter, merged, tree_key, groups)

########################################


def generate_solution_file(solution, solution_lines=None):
    """
    Serialize the solution file into a string array.

    This function generates SLN files for all versions of Visual Studio.
    It assumes the text file will be encoded using UTF-8 character encoding
    so the resulting file will be pre-pended with a UTF-8 Byte Order Mark (BOM)
    for Visual Studio 2005 or higher.

    Note:
        Byte Order Marks are not supplied by this function.

    Args:
        solution: Reference to the raw solution record
        solution_lines: List to insert string lines.
    Returns:
        Zero on success, non-zero on error.
    """

    # Save off the format header for the version of Visual Studio
    # being generated

    # Too many branches
    # Too many statements
    # pylint: disable=R0912,R0915

    if solution_lines is None:
        solution_lines = []

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

    # Close it up!
    solution_lines.append('EndGlobal')
    return 0, solution_lines


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

    Attributes:
        name: Name of this XML chunk.
        force_pair: Disable ``<foo/>`` syntax
        elements: List of elements in this element.
        attributes: List of valid attributes and defaults
    """

    def __init__(self, name, attributes=None, force_pair=False):
        """
        Set the defaults.
        Args:
            name: Name of the XML element
            attributes: dict of attributes to use as defaults.
            force_pair: If True, disable the use of /> XML suffix usage.
        """

        self.name = name
        self.force_pair = force_pair
        self.elements = []
        self.attributes = []
        if attributes:
            for item in attributes:
                if item is not None:
                    self.attributes.append(item)

    ########################################

    def add_default(self, attribute):
        """
        Add a dict of attribute defaults.
        @details
        If any defaults were already present, they will be overwritten
        with the new values.

        Args:
            attribute: A validator class instance
        """

        # Test for None
        if attribute is not None:
            # Does the item already exist?
            for index, value in enumerate(self.attributes):
                if value.name == attribute.name:
                    # Replace the item
                    self.attributes[index] = attribute
                    break
            else:
                # Append the item to the list
                self.attributes.append(attribute)

    ########################################

    def add_defaults(self, attributes):
        """
        Add a dict of attribute defaults.
        @details
        If any defaults were already present, they will be overwritten
        with the new values.

        Args:
            attributes: list of attribute names and default values.
        """

        # Test for None
        if attributes is not None:
            if not isinstance(attributes, list):
                self.add_default(attributes)
            else:
                # Update the list with the new entries
                for attribute in attributes:
                    self.add_default(attribute)

    ########################################

    def add_element(self, element):
        """
        Add an element to this XML element.

        Args:
            element: VS2003XML object
        """

        if element is not None:
            self.elements.append(element)

    ########################################

    def set_attribute(self, name, value):
        """
        Change existing attribute.
        @details
        If the attribute was not found, it will throw.

        Args:
            name: String of the entry to match
            value: Value to substitute
        """

        # Find the entry and update it.
        for attribute in self.attributes:
            if attribute.name == name:
                attribute.value = value
                break

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

        for index, value in enumerate(self.attributes):
            if value.name == name:
                # Replace the item
                del self.attributes[index]
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

        for validator in self.attributes:
            if validator.name == name:
                # Replace the item
                validator.value = validator.default
                return True
        return False

    ########################################

    def generate(self, line_list=None, indent=0, ide=None):
        """
        Generate the text lines for this XML element.

        There is a slight difference between Visual Studio 2003
        and 2005/2008 on how tags are closed. The argument ``ide``
        is used to flag with close format to use.

        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
            ide: IDE to target.
        Returns:
            line_list with all lines appended to it.
        """

        # Too many branches
        # Too many statements
        # pylint: disable=R0912,R0915

        # Create the default
        if line_list is None:
            line_list = []

        if ide is None:
            ide = IDETypes.vs2008

        # Determine the indentation
        # vs2003 uses tabs
        tabs = '\t' * indent

        # Special case, if no attributes, don't allow <foo/> XML
        # This is to duplicate the output of Visual Studio 2005-2008
        line_list.append('{0}<{1}'.format(tabs, escape_xml_cdata(self.name)))

        attributes = []
        for item in self.attributes:
            value = item.get_value()
            if value is not None:
                attributes.append((item.name, value))

        if attributes:

            # Output tag with attributes and support '/>' closing
            for attribute in attributes:
                value = attribute[1]

                # VS2003 has upper case booleans
                if ide is IDETypes.vs2003:
                    if value == 'true':
                        value = 'TRUE'
                    elif value == 'false':
                        value = 'FALSE'

                line_list.append(
                    '{0}\t{1}="{2}"'.format(
                        tabs,
                        escape_xml_cdata(attribute[0]),
                        escape_xml_attribute(value)))

            # Check if /> closing is disabled
            if not self.elements and not self.force_pair:
                if ide is IDETypes.vs2003:
                    line_list[-1] = line_list[-1] + '/>'
                else:
                    line_list.append('{}/>'.format(tabs))
                return line_list

            # Close the open tag
            if ide is IDETypes.vs2003:
                line_list[-1] = line_list[-1] + '>'
            else:
                line_list.append('{}\t>'.format(tabs))
        else:
            line_list[-1] = line_list[-1] + '>'

        # Output the embedded elements
        for element in self.elements:
            element.generate(line_list, indent=indent + 1, ide=ide)

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

    def __str__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return self.__repr__()


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

        VS2003XML.__init__(
            self, 'Tool', [VSStringProperty('Name', name)],
            force_pair=force_pair)

########################################


class VCCLCompilerTool(VS2003Tool):
    """
    Visual Studio 2003-2008 VCCLCompilerTool record.

    Attributes:
        configuration: Parent configuration
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

        self.configuration = configuration

        # Set the tag
        VS2003Tool.__init__(self, name='VCCLCompilerTool')

        # Values needed for defaults
        ide = configuration.ide
        optimization = configuration.optimization
        debug = configuration.debug
        project_type = configuration.project_type

        # Attributes are added in the same order they are written
        # in Visual Studio

        # List of custom compiler options as a single string
        self.add_default(StringAdditionalOptions())

        # Unicode response files
        self.add_default(BoolUseUnicodeResponseFiles(configuration))

        # Optimizations
        default = '/Ox' if optimization else '/Od'
        self.add_default(
            VSEnumProperty(
                'Optimization', default,
                (('/Od', 'Disabled'),
                 ('/O1', 'Minimize Size'),
                 ('/O2', 'Maximize Speed'),
                 ('/Ox', 'Full Optimization'),
                 'Custom')))

        # Global optimizations (2003 only)
        self.add_default(BoolGlobalOptimizations(configuration))

        # Inline functions
        default = '/Ob2' if optimization else None
        self.add_default(
            VSEnumProperty(
                'InlineFunctionExpansion', default,
                ('Disable',
                 ('/Ob1', 'Only __inline'),
                 ('/Ob2', 'Any Suitable'))))

        # Enable intrinsics
        self.add_default(BoolEnableIntrinsicFunctions(configuration))

        # True if floating point consistency is important
        self.add_default(BoolImproveFloatingPointConsistency(configuration))

        # Size or speed?
        self.add_default(
            VSEnumProperty(
                'FavorSizeOrSpeed', '/Ot',
                ('Neither', ('/Ot', 'Favor Fast Code'),
                 ('/Os', 'Favor Small Code'))))

        # Get rid of stack frame pointers for speed
        self.add_default(BoolOmitFramePointers(configuration))

        # Enable memory optimizations for fibers
        self.add_default(BoolEnableFiberSafeOptimizations(configuration))

        # Enable cross function optimizations
        self.add_default(
            BoolWholeProgramOptimization(configuration))

        # Build for Pentium, Pro, P4
        if ide is IDETypes.vs2003:
            self.add_default(
                VSEnumProperty(
                    'OptimizeForProcessor', '/G7',
                    ('Blended',
                     ('/G5', 'Pentium'),
                     ('/G6', 'Pentium Pro', 'Pentium II', 'Pentium III'),
                     ('/G7', 'Pentium IV', 'Pentium 4'))))

        # Optimize for Windows Applications
        self.add_default(BoolOptimizeForWindowsApplication(configuration))

        # Get the header includes
        default = configuration.get_unique_chained_list(
            '_source_include_list')
        default.extend(configuration.get_unique_chained_list(
            'include_folders_list'))
        self.add_default(VSStringListProperty(
            'AdditionalIncludeDirectories',
            default,
            slashes='\\'))

        # Directory for #using includes
        self.add_default(
            VSStringListProperty(
                'AdditionalUsingDirectories',
                [],
                slashes='\\'))

        # Get the defines
        define_list = configuration.get_chained_list('define_list')
        self.add_default(
            VSStringListProperty(
                'PreprocessorDefinitions',
                define_list))

        # Ignore standard include path if true
        self.add_default(BoolIgnoreStandardIncludePath(configuration))

        # Create a preprocessed file
        self.add_default(
            VSEnumProperty('GeneratePreprocessedFile', None,
                         ('No',
                          ('/P', 'With Line Numbers'),
                          ('/EP', '/EP /P', 'Without Line Numbers'))))

        # Keep comments in a preprocessed file
        self.add_default(BoolKeepComments(configuration))

        # Pool all constant strings
        self.add_default(BoolStringPooling(configuration))

        # Enable code analysis for minimal rebuild
        self.add_default(BoolMinimalRebuild(configuration))

        self.add_default(BoolExceptionHandling(configuration))

        if ide > IDETypes.vs2003:
            self.add_default(
                VSEnumProperty(
                    'ExceptionHandling', 'No',
                    ('No',
                     ('/EHsc', 'Yes'),
                     ('/EHa', 'Yes with SEH', 'Yes with SEH Exceptions'))))

        # Runtime checks (Only valid if no optimizations)
        default = None if optimization else 'Both'
        self.add_default(
            VSEnumProperty(
                'BasicRuntimeChecks', default,
                ('Default', ('/RTCs', 'Stack', 'Stack Frames'),
                 ('/RTCu', 'Uninitialzed', 'Uninitialized Variables'),
                 ('/RTCsu', '/RTC1', 'Both'))))

        # Test for data size shrinkage (Only valid if no optimizations)
        self.add_default(BoolSmallerTypeCheck(configuration))

        # Which run time library to use?
        default = '/MTd' if debug else '/MT'
        enum_list = [('/MT', 'Multi-Threaded'),
                     ('/MTd', 'Multi-Threaded Debug'),
                     ('/MD', 'Multi-Threaded DLL'),
                     ('/MDd', 'Multi-Threaded DLL Debug')]

        # Visual Studio 2003 support single threaded libraries
        if ide is IDETypes.vs2003:
            enum_list.extend([('/ML', 'Single-Threaded'),
                              ('/MLd', 'Single-Threaded Debug')])
        self.add_default(
            VSEnumProperty('RuntimeLibrary', default, enum_list))

        # Structure alignment
        self.add_default(
            VSEnumProperty(
                'StructMemberAlignment', '/Zp8',
                ('Default',
                 ('/Zp1', '1', '1 Byte'),
                 ('/Zp2', '2', '2 Bytes'),
                 ('/Zp4', '4', '4 Bytes'),
                 ('/Zp8', '8', '8 Bytes'),
                 ('/Zp16', '16', '16 Bytes'))))

        # Check for buffer overrun
        self.add_default(BoolBufferSecurityCheck(configuration))

        # Function level linking
        self.add_default(BoolEnableFunctionLevelLinking(configuration))

        # Enhanced instruction set
        default = None
        self.add_default(
            VSEnumProperty(
                'EnableEnhancedInstructionSet', default,
                ('Default',
                 ('/arch:SSE', 'SSE'),
                 ('/arch:SSE2', 'SSE2'))))

        # Floating point precision
        if ide > IDETypes.vs2003:
            default = '/fp:fast'
            self.add_default(
                VSEnumProperty(
                    'FloatingPointModel', default,
                    (('/fp:precise', 'Precise'),
                     ('/fp:strict', 'Strict'),
                     ('/fp:fast', 'Fast'))))

        # Floating point exception support
        self.add_default(BoolFloatingPointExceptions(configuration))

        # Enable Microsoft specific extensions
        self.add_default(BoolDisableLanguageExtensions(configuration))

        # "char" is unsigned
        self.add_default(BoolDefaultCharIsUnsigned(configuration))

        # Enable wchar_t
        self.add_default(BoolTreatWChar_tAsBuiltInType(configuration))

        # for (int i) "i" stays in the loop
        self.add_default(BoolForceConformanceInForLoopScope(configuration))

        # Enable run time type info
        self.add_default(BoolRuntimeTypeInfo(configuration))

        # OpenMP support
        self.add_default(BoolOpenMP(configuration))

        # Enable precompiled headers
        default = None
        enum_list = [('No', 'Not using'),
                     ('/Yc', 'Create'),
                     ('/Yu', 'Use')]

        # Visual Studio 2003 supports automatic generation
        if ide is IDETypes.vs2003:
            enum_list.insert(-1, ('/YX', 'Automatic'))
        self.add_default(
            VSEnumProperty('UsePrecompiledHeader', default, enum_list))

        # Text header file for precompilation
        self.add_default(StringPrecompiledHeaderThrough())

        # Binary header file for precompilation
        self.add_default(StringPrecompiledHeaderFile())

        # Add extended attributes to .asm output
        self.add_default(BoolExpandAttributedSource(configuration))

        # Format of the assembly output
        default = None
        self.add_default(
            VSEnumProperty(
                'AssemblerOutput', default,
                (('No', 'No Listing'),
                 ('/FA', 'Assembly', 'Asm', 'Assembly-Only'),
                 ('/FAcs', 'Assembly, Machine Code and Source'),
                 ('/FAc', 'Assembly With Machine Code'),
                 ('/FAs', 'Assembly With Source'))))

        # Output location for .asm file
        self.add_default(StringAssemblerListingLocation())

        # Output location for .obj file
        self.add_default(StringObjectFile())

        # Output location of shared .pdb file
        self.add_default(StringProgramDataBaseFileName(
            '"$(OutDir)$(TargetName).pdb"'))

        if ide > IDETypes.vs2003:
            # Generate XML formatted documentation
            self.add_default(BoolGenerateXMLDocumentationFiles(configuration))

            # Name of the XML formatted documentation file
            self.add_default(StringXMLDocumentationFileName())

        # Type of source browsing information
        default = None
        self.add_default(
            VSEnumProperty('BrowseInformation', default,
                         (('None', 'No'),
                          ('/FR', 'All'),
                          ('/Fr', 'No Local Symbols', 'No Locals'))))

        # Name of the browsing file
        self.add_default(StringBrowseInformationFile())

        # Warning level
        default = 'All'
        self.add_default(
            VSEnumProperty('WarningLevel', default,
                         (('/W0', 'Off', 'No', 'None'),
                          ('/W1', 'Level 1'),
                          ('/W2', 'Level 2'),
                          ('/W3', 'Level 3'),
                          ('/W4', 'Level 4', 'All'))))

        # Warnings are errors
        self.add_default(BoolWarnAsError(configuration))

        # Don't show startup banner
        self.add_default(
            BoolSuppressStartupBanner(
                configuration,
                'compiler_options'))

        # Warnings for 64 bit code issues
        self.add_default(BoolDetect64BitPortabilityProblems(configuration))

        # Debug information type
        enum_list = [('Off', 'No', 'None', 'Disabled'),
                     ('/C7', 'C7 Compatible'),
                     # Hidden in 2005/2008 (maps to C7)
                     ('/Zd', 'Line Numbers', 'Line Numbers Only'),
                     ('/Zi', 'Program Database'),
                     ('/ZI', 'Edit and Continue')]

        default = None
        if debug or project_type.is_library():
            default = '/C7'
        self.add_default(
            VSEnumProperty('DebugInformationFormat', default, enum_list))

        # Code calling convention
        default = None
        if configuration.fastcall:
            default = '__fastcall'
        self.add_default(
            VSEnumProperty('CallingConvention', default,
                         (('/Gd', '__cdecl'),
                          ('/Gr', '__fastcall'),
                          ('/Gz', '__stdcall'))))

        # C or C++
        default = None
        self.add_default(
            VSEnumProperty('CompileAs', default,
                         (('No', 'Default'),
                          ('/TC', 'C'),
                          ('/TP', 'C++'))))

        # Get the defines
        default = ['4201']
        self.add_default(VSStringListProperty(
            'DisableSpecificWarnings', default))

        # List of include files to force inclusion
        default = []
        self.add_default(VSStringListProperty('ForcedIncludeFile', default))

        # List of using files to force inclusion
        default = []
        self.add_default(VSStringListProperty('ForcedUsingFiles', default))

        # Show include file list
        self.add_default(BoolShowIncludes(configuration))

        # List of defines to remove
        default = []
        self.add_default(
            VSStringListProperty(
                'UndefinePreprocessorDefinitions',
                default))

        # Remove all compiler definitions
        self.add_default(BoolUndefineAllPreprocessorDefinitions(configuration))

        # Use full pathnames in error messages
        self.add_default(BoolUseFullPaths(configuration))

        # Remove default library names
        self.add_default(BoolOmitDefaultLibName(configuration))

        if ide > IDETypes.vs2003:
            # Error reporting style
            default = None
            self.add_default(
                VSEnumProperty('ErrorReporting', default,
                             (('Default'),
                              ('/errorReport:prompt', 'Immediate'),
                              ('/errorReport:queue', 'Queue'))))

########################################


class VCCLCompilerToolFile(VS2003Tool):
    """
    Visual Studio 2003-2008 VCCLCompilerTool record for file

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration

        # Set the tag
        VS2003Tool.__init__(self, name='VCCLCompilerTool')

########################################


class VCCustomBuildTool(VS2003Tool):
    """
    Visual Studio 2003-2008 VCCustomBuildTool record.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration

        VS2003Tool.__init__(self, name='VCCustomBuildTool')

        # Describe the build step
        self.add_default(StringDescription())

        # Command line to perform the build
        self.add_default(StringCommandLine())

        # List of files this step depends on
        self.add_default(VSStringListProperty('AdditionalDependencies', []))

        # List of files created by this build step
        self.add_default(VSStringListProperty('Outputs', []))


########################################

class VCLinkerTool(VS2003Tool):
    """
    Visual Studio 2003-2008 VCLinkerTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        # Too many branches
        # Too many statements
        # pylint: disable=R0912,R0915

        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCLinkerTool')

        # Values needed for defaults
        ide = configuration.ide
        optimization = configuration.optimization
        project_type = configuration.project_type
        link_time_code_generation = configuration.link_time_code_generation

        # Register the output on completion
        self.add_default(BoolRegisterOutput(configuration))

        # Register per user instead of for everyone
        self.add_default(BoolPerUserRedirection(configuration))

        # Don't allow this library generated be imported by dependent projects
        self.add_default(BoolIgnoreImportLibrary(configuration))

        # Link in libraries from dependent projects
        self.add_default(BoolLinkLibraryDependencies(configuration))

        # Use the librarian for input
        self.add_default(BoolUseLibraryDependencyInputs(configuration))

        # Allow unicode filenames in response files
        self.add_default(BoolUseUnicodeResponseFiles(configuration))

        # Additional commands
        self.add_default(StringAdditionalOptions())

        # Additional libraries
        default = configuration.get_unique_chained_list(
            'libraries_list')
        self.add_default(
            VSStringListProperty(
                'AdditionalDependencies',
                default,
                separator=' '))

        # Show progress in linking
        default = None
        self.add_default(
            VSEnumProperty('ShowProgress', default,
                         (('Default', 'No', 'None'),
                          ('/VERBOSE', 'All'),
                          ('/VERBOSE:LIB', 'Lib'))))

        # Output file name
        # Don't use $(TargetExt)
        default = '"$(OutDir){}{}.exe"'.format(
            configuration.project.name,
            configuration.get_suffix())
        self.add_default(StringOutputFile(default))

        # Version number
        self.add_default(VSStringProperty('Version', None))

       # Show progress in linking
        default = 'No' if optimization else 'Yes'
        self.add_default(
            VSEnumProperty('LinkIncremental', default,
                         ('Default',
                          ('/INCREMENTAL:NO', 'No'),
                          ('/INCREMENTAL', 'Yes'))))

        # Turn off startup banner
        self.add_default(
            BoolSuppressStartupBanner(
                configuration,
                'linker_options'))

        # Library folders
        default = configuration.get_unique_chained_list('library_folders_list')
        self.add_default(
            VSStringListProperty(
                'AdditionalLibraryDirectories',
                default,
                slashes='\\'))

        # Generate a manifest file
        self.add_default(BoolGenerateManifest(configuration))

        if ide > IDETypes.vs2003:
            # Name of the manifest file
            self.add_default(VSStringProperty('ManifestFile', None))

            # Manifests this one is dependent on
            self.add_default(
                VSStringListProperty(
                    'AdditionalManifestDependencies', []))

        # Enable User Access Control
        self.add_default(BoolEnableUAC(configuration))

        if ide > IDETypes.vs2005:
            # Generate a manifest file
            default = None
            self.add_default(
                VSEnumProperty('UACExecutionLevel', None,
                             ('asInvoker',
                              'highestAvailable',
                              'requireAdministrator')))

        # Enable UI bypass for User Access Control
        self.add_default(BoolUACUIAccess(configuration))

        # Ignore default libraries
        self.add_default(BoolIgnoreAllDefaultLibraries(configuration))

        # Manifests this one is dependent on
        self.add_default(VSStringListProperty('IgnoreDefaultLibraryNames', []))

        # Module definition file, if one exists
        self.add_default(VSStringProperty('ModuleDefinitionFile', None))

        # Add these modules to the C# assembly
        self.add_default(VSStringListProperty('AddModuleNamesToAssembly', []))

        # Embed these resource fildes
        self.add_default(VSStringListProperty('EmbedManagedResourceFile', []))

        # Force these symbols
        self.add_default(VSStringListProperty('ForceSymbolReferences', []))

        # Load these DLLs only when called.
        self.add_default(VSStringListProperty('DelayLoadDLLs', []))

        if ide > IDETypes.vs2003:
            # Link in these assemblies
            self.add_default(VSStringListProperty('AssemblyLinkResource', []))

        # Contents of a Midl comment file (Actual commands)
        self.add_default(VSStringProperty('MidlCommandFile', None))

        # Ignore embedded .idlsym sections
        self.add_default(BoolIgnoreEmbeddedIDL(configuration))

        # Filename the contains the contents of the merged idl
        self.add_default(VSStringProperty('MergedIDLBaseFileName', None))

        # Name of the type library
        self.add_default(VSStringProperty('TypeLibraryFile', None))

        # ID number of the library resource
        self.add_default(IntTypeLibraryResourceID())

        # Generate debugging information
        self.add_default(BoolGenerateDebugInformation(configuration))

        # Add debugging infromation in assembly
        default = None
        self.add_default(
            VSEnumProperty(
                'AssemblyDebug', default,
                (('No', 'None'),
                 ('/ASSEMBLYDEBUG', 'Runtime Tracking'),
                 ('/ASSEMBLYDEBUG:DISABLE', 'No Runtime Tracking'))))

        # Name of the program database file
        default = '"$(OutDir)$(TargetName).pdb"'
        self.add_default(VSStringProperty('ProgramDatabaseFile', default))

        # Do not put private symboles in this program database file
        self.add_default(VSStringProperty('StripPrivateSymbols', None))

        # Generate the map file
        self.add_default(BoolGenerateMapFile(configuration))

        # Name of the map file
        self.add_default(VSStringProperty('MapFileName', None))

        # Include exported symbols in the map file
        self.add_default(BoolMapExports(configuration))

        # Include source code line numbers in the map file
        self.add_default(BoolMapLines(configuration))

        # Subsystem to link to
        default = 'Console' if project_type is ProjectTypes.tool else 'Windows'
        enum_list = [('No', 'None'),
                     ('/SUBSYSTEM:CONSOLE', 'Console'),
                     ('/SUBSYSTEM:WINDOWS', 'Windows')]

        if ide > IDETypes.vs2003:
            enum_list.extend([
                ('/SUBSYSTEM:NATIVE', 'Native'),
                ('/SUBSYSTEM:EFI_APPLICATION', 'EFI Application'),
                ('/SUBSYSTEM:EFI_BOOT_SERVICE_DRIVER',
                 'EFI Boot Service Driver'),
                ('/SUBSYSTEM:EFI_ROM', 'EFI ROM'),
                ('/SUBSYSTEM:EFI_RUNTIME_DRIVER', 'EFI Runtime'),
                ('/SUBSYSTEM:WINDOWSCE', 'WindowsCE'),
            ])

            # Only Visual Studio 2005 supported Posix
            if ide is IDETypes.vs2005:
                enum_list.insert(-1, ('/SUBSYSTEM:POSIX', 'Posix'))

        self.add_default(
            VSEnumProperty('SubSystem', default, enum_list))

        # Amount of heap to reserve
        self.add_default(IntHeapReserveSize())

        # Amount of heap to commit
        self.add_default(IntHeapCommitSize())

        # Amount of stack to reserve
        self.add_default(IntStackReserveSize())

        # Amount of stack to commit
        self.add_default(IntStackCommitSize())

        # Large address space aware?
        default = None
        self.add_default(
            VSEnumProperty('LargeAddressAware', default,
                         ('Default',
                          ('/LARGEADDRESSAWARE:NO', 'Disable'),
                          ('/LARGEADDRESSAWARE', 'Enable'))))

        # Terminal server aware?
        default = None
        self.add_default(
            VSEnumProperty('TerminalServerAware', default,
                         ('Default',
                          ('/TSAWARE:NO', 'Disable'),
                          ('/TSAWARE', 'Enable'))))

        # Run the file from swap location on CD
        self.add_default(BoolSwapRunFromCD(configuration))

        # Run the file from swap location for network
        self.add_default(BoolSwapRunFromNet(configuration))

        # Device driver?
        if ide > IDETypes.vs2003:
            default = None
            self.add_default(
                VSEnumProperty('Driver', default,
                             (('No', 'Not Set'),
                              ('/DRIVER:NO', 'Driver'),
                              ('/DRIVER:UPONLY', 'Up Only'),
                              ('/DRIVER:WDM', 'WDM'))))

        # Remove unreferenced code
        default = '/OPT:REF'
        self.add_default(
            VSEnumProperty('OptimizeReferences', default,
                         ('Default',
                          ('/OPT:NOREF', 'Disable'),
                          ('/OPT:REF', 'Enable'))))

        # Remove redundant COMDAT symbols
        default = '/OPT:ICF' if optimization else None
        self.add_default(
            VSEnumProperty('EnableCOMDATFolding', default,
                         ('Default',
                          ('/OPT:NOICF', 'Disable'),
                          ('/OPT:ICF', 'Enable'))))

        # Align code on 4K boundaries for Windows 98
        default = None
        self.add_default(
            VSEnumProperty('OptimizeForWindows98', default,
                         ('Default',
                          ('/OPT:NOWIN98', 'Disable'),
                          ('/OPT:WIN98', 'Enable'))))

        # Name of file containing the function link order
        self.add_default(VSStringProperty('FunctionOrder', None))

        if ide > IDETypes.vs2003:

            # Link using link time code generation
            default = 'Enable' if link_time_code_generation else None
            self.add_default(
                VSEnumProperty('LinkTimeCodeGeneration', default,
                             ('Default',
                              ('/ltcg', 'Enable'),
                              ('/ltcg:pginstrument', 'Instrument'),
                              ('/ltcg:pgoptimize', 'Optimize'),
                              ('/ltcg:pgupdate', 'Update'))))

            # Database file for profile based optimizations
            self.add_default(VSStringProperty('ProfileGuidedDatabase', None))

        # Code entry point symbol
        self.add_default(VSStringProperty('EntryPointSymbol', None))

        # No entry point (Resource only DLL)
        self.add_default(BoolResourceOnlyDLL(configuration))

        # Create a checksum in the header of the exe file
        self.add_default(BoolSetChecksum(configuration))

        # Base address for execution
        self.add_default(VSStringProperty('BaseAddress', None))

        if ide > IDETypes.vs2005:

            # Enable base address randomization
            default = None
            self.add_default(
                VSEnumProperty('RandomizedBaseAddress', default,
                             ('Default',
                              ('/DYNAMICBASE:NO', 'Disable'),
                              ('/DYNAMICBASE', 'Enable'))))

            # Enable fixed address code generation
            default = None
            self.add_default(
                VSEnumProperty('FixedBaseAddress', default,
                             ('Default',
                              ('/FIXED:NO', 'Relocatable'),
                              ('/FIXED', 'Fixed'))))

            # Enable Data execution protection
            default = None
            self.add_default(
                VSEnumProperty('DataExecutionPrevention', default,
                             ('Default',
                              ('/NXCOMPAT:NO', 'Disable'),
                              ('/NXCOMPAT', 'Enable'))))

        # Don't output assembly for C#
        self.add_default(BoolTurnOffAssemblyGeneration(configuration))

        # Disable unloading of delayed load DLLs
        self.add_default(BoolSupportUnloadOfDelayLoadedDLL(configuration))

        # Name of the import library to generate
        self.add_default(VSStringProperty('ImportLibrary', None))

        # Sections to merge on link
        self.add_default(VSStringProperty('MergeSections', None))

        # Target machine to build data for.
        default = None
        enum_list = [('Default', 'Not Set'),
                     ('/MACHINE:X86', 'X86')]

        # Visual Studio 2005 and 2008 support other CPUs
        if ide > IDETypes.vs2003:
            enum_list.extend([
                ('/MACHINE:AM33', 'AM33'),
                ('/MACHINE:ARM', 'ARM'),
                ('/MACHINE:EBC', 'EBC'),
                ('/MACHINE:IA64', 'IA64'),
                ('/MACHINE:M32R', 'M32R'),
                ('/MACHINE:MIPS', 'MIPS'),
                ('/MACHINE:MIPS16', 'MIPS16'),
                ('/MACHINE:MIPSFPU', 'MIPSFPU'),
                ('/MACHINE:MIPSFPU16', 'MIPSFPU16'),
                ('/MACHINE:MIPSR41XX', 'MIPSR41XX'),
                ('/MACHINE:SH3', 'SH3'),
                ('/MACHINE:SH3DSP', 'SH3DSP'),
                ('/MACHINE:SH4', 'SH4'),
                ('/MACHINE:SH5', 'SH5'),
                ('/MACHINE:THUMB', 'THUMB'),
                ('/MACHINE:X64', 'X64')
            ])

        self.add_default(VSStringListProperty('TargetMachine', None, enum_list))

        # This is a duplication of what is in 2008 for sorting
        if ide < IDETypes.vs2008:
            # Enable fixed address code generation
            default = None
            self.add_default(
                VSEnumProperty('FixedBaseAddress', default,
                             ('Default',
                              ('/FIXED:NO', 'Relocatable'),
                              ('/FIXED', 'Fixed'))))

        # New entries for Visual Studio 2005 and 2008
        if ide > IDETypes.vs2003:

            # File with key for signing
            self.add_default(VSStringProperty('KeyFile', None))

            # Name of the container of the key
            self.add_default(VSStringProperty('KeyContainer', None))

        # Output should be delay signed
        self.add_default(BoolDelaySign(configuration))

        # Allow assemblies to be isolated in the manifest
        self.add_default(BoolAllowIsolation(configuration))

        # Enable profiling
        self.add_default(BoolProfile(configuration))

        # New entries for Visual Studio 2005 and 2008
        if ide > IDETypes.vs2003:
            # CLR Thread attribute
            default = None
            self.add_default(
                VSEnumProperty('CLRThreadAttribute', default,
                             ('Default',
                              ('/CLRTHREADATTRIBUTE:MTA', 'MTA'),
                              ('/CLRTHREADATTRIBUTE:STA', 'STA'))))

            # CLR data image type
            default = None
            self.add_default(
                VSEnumProperty('CLRImageType', default,
                             ('Default',
                              ('/CLRIMAGETYPE:IJW', 'IJW'),
                              ('/CLRIMAGETYPE:PURE', 'RelPureocatable'),
                              ('/CLRIMAGETYPE:SAFE', 'Safe'))))

            # Error reporting
            default = None
            self.add_default(
                VSEnumProperty('ErrorReporting', default,
                             ('Default',
                              ('/ERRORREPORT:PROMPT', 'Prompt'),
                              ('/ERRORREPORT:QUEUE', 'Queue'))))

        # Check for unmanaged code
        self.add_default(BoolCLRUnmanagedCodeCheck(configuration))

########################################


class VCLibrarianTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCLibrarianTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCLibrarianTool')

        # Use unicode for responses
        self.add_default(BoolUseUnicodeResponseFiles(configuration))

        # Link in library dependencies
        self.add_default(BoolLinkLibraryDependencies(configuration))

        # Additional command lines
        self.add_default(StringAdditionalOptions())

        # Libaries to link in
        default = []
        self.add_default(
            VSStringListProperty(
                'AdditionalDependencies',
                default,
                separator=' '))

        # Name of the output file
        # Don't use $(TargetExt)
        default = '"$(OutDir){}{}.lib"'.format(
            configuration.project.name,
            configuration.get_suffix())
        self.add_default(StringOutputFile(default))

        # Library folders
        default = configuration.get_unique_chained_list('library_folders_list')
        self.add_default(
            VSStringListProperty(
                'AdditionalLibraryDirectories',
                default,
                slashes='\\'))

        # Suppress the startup banner
        self.add_default(
            BoolSuppressStartupBanner(
                configuration,
                'linker_options'))

        # Name of the module file name
        self.add_default(VSStringProperty('ModuleDefinitionFile', None))

        # Ignore the default libraries
        self.add_default(BoolIgnoreAllDefaultLibraries(configuration))

        # Ignore these libraries
        default = []
        self.add_default(
            VSStringListProperty(
                'IgnoreDefaultLibraryNames',
                default))

        # Export these functions
        default = []
        self.add_default(
            VSStringListProperty(
                'ExportNamedFunctions',
                default))

        # Force linking to these symbols
        default = []
        self.add_default(
            VSStringListProperty(
                'ForceSymbolReferences',
                default))


########################################


class VCMIDLTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for the MIDL tool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCMIDLTool')

########################################


class VCALinkTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCALinkTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCALinkTool')


########################################


class VCManifestTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCManifestTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCManifestTool')


########################################


class VCXDCMakeTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCXDCMakeTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCXDCMakeTool')

########################################


class VCBscMakeTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCBscMakeTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCBscMakeTool')

########################################


class VCFxCopTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCFxCopTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCFxCopTool')

########################################


class VCAppVerifierTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCAppVerifierTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCAppVerifierTool')

########################################


class VCManagedResourceCompilerTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCManagedResourceCompilerTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCManagedResourceCompilerTool')

########################################


class VCPostBuildEventTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCPostBuildEventTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCPostBuildEventTool')

        vs_description, vs_cmd = create_deploy_script(configuration)

        # Message to print in the console
        self.add_default(StringDescription(vs_description))

        # Batch file contents
        self.add_default(StringCommandLine(vs_cmd))

        # Ignore from build
        self.add_default(BoolExcludedFromBuild())


########################################


class VCPreBuildEventTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCPreBuildEventTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCPreBuildEventTool')

        # Message to print in the console
        self.add_default(StringDescription())

        # Batch file contents
        self.add_default(StringCommandLine())

        # Ignore from build
        self.add_default(BoolExcludedFromBuild())


########################################


class VCPreLinkEventTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCPreLinkEventTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCPreLinkEventTool')

        # Message to print in the console
        self.add_default(StringDescription())

        # Batch file contents
        self.add_default(StringCommandLine())

        # Ignore from build
        self.add_default(BoolExcludedFromBuild())

########################################


class VCResourceCompilerTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCResourceCompilerTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCResourceCompilerTool')

        # Language
        self.add_default(VSStringProperty('Culture', '1033'))

########################################


class XboxDeploymentTool(VS2003Tool):
    """
    XboxDeploymentTool for Xbox Classic.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'XboxDeploymentTool')

########################################


class XboxImageTool(VS2003Tool):
    """
    XboxImageTool for Xbox Classic.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'XboxImageTool')

########################################


class VCWebServiceProxyGeneratorTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCWebServiceProxyGeneratorTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCWebServiceProxyGeneratorTool')

########################################


class VCXMLDataGeneratorTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCXMLDataGeneratorTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration

        VS2003Tool.__init__(self, 'VCXMLDataGeneratorTool')

########################################


class VCWebDeploymentTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCWebDeploymentTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCWebDeploymentTool')

########################################


class VCManagedWrapperGeneratorTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCManagedWrapperGeneratorTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCManagedWrapperGeneratorTool')

########################################


class VCAuxiliaryManagedWrapperGeneratorTool(VS2003Tool):
    """
    Visual Studio 2003-2008 for VCAuxiliaryManagedWrapperGeneratorTool.

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        self.configuration = configuration
        VS2003Tool.__init__(self, 'VCAuxiliaryManagedWrapperGeneratorTool')


########################################


class VS2003Platform(VS2003XML):
    """
    Visual Studio 2003-2008 Platform record.

    Attributes:
        platform: PlatformTypes
    """

    def __init__(self, platform):
        """
        Init defaults.

        Args:
            platform: PlatformTypes of the platform to build
        """

        self.platform = platform

        VS2003XML.__init__(
            self, 'Platform', [
                VSStringProperty(
                    'Name', platform.get_vs_platform()[0])])

########################################


class VS2003Platforms(VS2003XML):
    """
    Visual Studio 2003-2008 Platforms record

    Attributes:
        project: Parent project
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        self.project = project
        VS2003XML.__init__(self, 'Platforms')

        # Get the list of platforms
        platforms = set()
        for configuration in project.configuration_list:
            platforms.add(configuration.platform)

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


class VS2003DefaultToolFile(VS2003XML):
    """
    Visual Studio 2003-2008 References record
    """

    def __init__(self, rules):
        """
        Set the defaults.
        """

        VS2003XML.__init__(
            self, 'DefaultToolFile', [
                VSStringProperty(
                    'FileName', rules)])

########################################


class VS2003ToolFiles(VS2003XML):
    """
    Visual Studio 2003-2008 ToolFiles record

    Attributes:
        platform: Parent project
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        self.platform = project
        VS2003XML.__init__(self, 'ToolFiles')

        for rules in project.vs_rules:
            rules = convert_to_windows_slashes(rules)
            self.add_element(VS2003DefaultToolFile(rules))

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

    Attributes:
        configuration: Parent configuration
        vcprebuildeventtool: Pre build settings
        vcpostbuildeventtool: Post build settings
        vcprelinkeventtool: Pre link custom settings
        vccustombuildtool: Custom build settings
        vcclcompilertool: C++ compiler settings
        vcmidltool: Midl tool settings
        vcmanagedresourcecompilertool: Managed resource settings
        vcresourcecompilertool: Resource compiler settings
        vcxmldatageneratortool: XML data generator settings
        vcwebserviceproxygeneratortool: Web service proxy settings
        vcwebdeploymenttool: Web deployment settings
        vcmanagedwrappergeneratortool: Managed wrapper settings
        vcauxiliarymanagedwrappedgeneratortool: Aux Managed Wrapper settings
        xboxdeploymenttool: Xbox deployment settings
        xboximagetool: Xbox game imaging settings
        vclinkertool: Linker settings
    """

    # Too many instance attributes
    # pylint: disable=too-many-instance-attributes
    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        # Too many branches
        # Too many statements
        # pylint: disable=R0912,R0915

        self.configuration = configuration

        ide = configuration.ide
        platform = configuration.platform
        project_type = configuration.project_type

        vs_intdirectory = 'temp\\{}{}\\'.format(
            configuration.project.name,
            configuration.get_suffix())

        if project_type is ProjectTypes.library:
            vs_configuration_type = '4'
        elif project_type is ProjectTypes.sharedlibrary:
            vs_configuration_type = '2'
        else:
            vs_configuration_type = '1'

        if configuration.link_time_code_generation:
            if ide > IDETypes.vs2003:
                vs_link_time_code_generation = '1'
            else:
                vs_link_time_code_generation = 'true'
        else:
            vs_link_time_code_generation = None

        VS2003XML.__init__(self, 'Configuration', [
            StringName(configuration.vs_configuration_name),
            VSStringProperty('OutputDirectory', 'bin\\'),
            VSStringProperty('IntermediateDirectory', vs_intdirectory),
            VSStringProperty('ConfigurationType', vs_configuration_type),
            VSStringProperty('UseOfMFC', '0'),
            BoolATLMinimizesCRunTimeLibraryUsage(configuration),
            VSStringProperty('CharacterSet', '1'),
            VSStringProperty('DeleteExtensionsOnClean', None),
            VSStringProperty('ManagedExtensions', None),
            VSStringProperty('WholeProgramOptimization',
                           vs_link_time_code_generation),
            VSStringProperty('ReferencesPath', None)
        ])

        # Include all the data chunks
        self.vcprebuildeventtool = VCPreBuildEventTool(configuration)
        self.vcpostbuildeventtool = VCPostBuildEventTool(configuration)
        self.vcprelinkeventtool = VCPreLinkEventTool(configuration)
        self.vccustombuildtool = VCCustomBuildTool(configuration)
        self.vcclcompilertool = VCCLCompilerTool(configuration)

        self.vcmidltool = None
        self.vcmanagedresourcecompilertool = None
        self.vcresourcecompilertool = None
        self.vcxmldatageneratortool = None
        self.vcwebserviceproxygeneratortool = None
        self.vcwebdeploymenttool = None
        self.vcmanagedwrappergeneratortool = None
        self.vcauxiliarymanagedwrappedgeneratortool = None

        if platform.is_windows():
            self.vcmidltool = VCMIDLTool(configuration)
            self.vcmanagedresourcecompilertool = VCManagedResourceCompilerTool(
                configuration)
            self.vcresourcecompilertool = VCResourceCompilerTool(configuration)
            self.vcxmldatageneratortool = VCXMLDataGeneratorTool(configuration)
            self.vcwebserviceproxygeneratortool = \
                VCWebServiceProxyGeneratorTool(configuration)
            if ide < IDETypes.vs2008:
                self.vcwebdeploymenttool = VCWebDeploymentTool(configuration)
            if ide is IDETypes.vs2003:
                self.vcmanagedwrappergeneratortool = \
                    VCManagedWrapperGeneratorTool(configuration)
                self.vcauxiliarymanagedwrappedgeneratortool = \
                    VCAuxiliaryManagedWrapperGeneratorTool(configuration)

        self.xboxdeploymenttool = None
        self.xboximagetool = None
        if platform is PlatformTypes.xbox:
            self.xboxdeploymenttool = XboxDeploymentTool(configuration)
            self.xboximagetool = XboxImageTool(configuration)

        if project_type.is_library():
            self.vclinkertool = VCLibrarianTool(configuration)
        else:
            self.vclinkertool = VCLinkerTool(configuration)

        # Add elements in the order expected by Visual Studio 2003.
        if ide is IDETypes.vs2003:
            self.add_element(self.vcclcompilertool)
            self.add_element(self.vccustombuildtool)
            self.add_element(self.vclinkertool)
            self.add_element(self.vcmidltool)
            self.add_element(self.vcpostbuildeventtool)
            self.add_element(self.vcprebuildeventtool)
            self.add_element(self.vcprelinkeventtool)
            self.add_element(self.vcresourcecompilertool)
            self.add_element(self.vcwebserviceproxygeneratortool)
            self.add_element(self.vcxmldatageneratortool)
            self.add_element(self.vcwebdeploymenttool)
            self.add_element(self.vcmanagedwrappergeneratortool)
            self.add_element(self.vcauxiliarymanagedwrappedgeneratortool)

        else:
            self.add_element(self.vcprebuildeventtool)
            self.add_element(self.vccustombuildtool)
            self.add_element(self.vcxmldatageneratortool)
            self.add_element(self.vcwebserviceproxygeneratortool)
            self.add_element(self.vcmidltool)
            self.add_element(self.vcclcompilertool)
            self.add_element(self.vcmanagedresourcecompilertool)
            self.add_element(self.vcresourcecompilertool)
            self.add_element(self.vcprelinkeventtool)
            self.add_element(self.vclinkertool)
            self.add_element(self.xboxdeploymenttool)
            self.add_element(self.xboximagetool)
            self.add_element(VCALinkTool(configuration))
            self.add_element(VCManifestTool(configuration))
            self.add_element(VCXDCMakeTool(configuration))
            self.add_element(VCBscMakeTool(configuration))
            self.add_element(VCFxCopTool(configuration))
            self.add_element(VCAppVerifierTool(configuration))
            self.add_element(self.vcwebdeploymenttool)
            self.add_element(self.vcpostbuildeventtool)

########################################


class VS2003Configurations(VS2003XML):
    """
    Visual Studio 2003-2008 Configurations record

    Attributes:
        project: Parent project
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        self.project = project

        VS2003XML.__init__(self, 'Configurations')
        for configuration in project.configuration_list:
            self.add_element(VS2003Configuration(configuration))

########################################


class VS2003FileConfiguration(VS2003XML):
    """
    Visual Studio 2003-2008 Configurations record

    Attributes:
        configuration: Parent configuration
    """

    def __init__(self, configuration, base_name, source_file):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
            base_name: Base filename
            source_file: SourceFile reference
        """

        # pylint: disable=too-many-locals
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        self.configuration = configuration

        VS2003XML.__init__(self, 'FileConfiguration', [
            StringName(configuration.vs_configuration_name)])

        # Check if it's excluded
        for exclude in configuration.exclude_list_regex:
            if exclude(base_name):
                self.add_default(BoolExcludedFromBuild(True))

        # Set up the element
        tool_name = None
        tool_enums = {}

        if source_file.type in (FileTypes.cpp, FileTypes.c):
            tool_name = 'VCCLCompilerTool'
        elif source_file.type is FileTypes.hlsl:
            tool_name = 'HLSL'
            tool_enums = HLSL_ENUMS
        elif source_file.type is FileTypes.glsl:
            tool_name = 'GLSL'

        # pylint: disable:
        if not tool_name:
            return

        rule_list = (
            configuration.custom_rules,
            configuration.parent.custom_rules,
            configuration.parent.parent.custom_rules)

        if configuration.ide is IDETypes.vs2003 \
                and tool_name != 'VCCLCompilerTool':

            if tool_name == 'HLSL':
                make_command = make_hlsl_command
            elif tool_name == 'GLSL':
                make_command = make_glsl_command
            else:
                return

            element_dict = {}
            for rule in rule_list:
                for key in rule:
                    if key(base_name):
                        record = rule[key]
                        for item in record:
                            value = record[item]
                            enum_table = lookup_enum_value(tool_enums, item, None)
                            if enum_table:
                                new_value = lookup_enum_value(
                                    enum_table[1], value, None)
                                if new_value is not None:
                                    value = str(new_value)

                            element_dict[item] = value

            if element_dict:
                cmd, description, outputs = make_command(element_dict)
                if cmd:
                    element = VS2003Tool('VCCustomBuildTool')
                    self.add_element(element)

                    # Describe the build step
                    element.add_default(
                        StringDescription(
                            convert_file_name_vs2010(description)))

                    # Command line to perform the build
                    element.add_default(
                        StringCommandLine(
                            convert_file_name_vs2010(cmd)))

                    # List of files created by this build step
                    element.add_default(
                        VSStringListProperty(
                            'Outputs',
                            [convert_file_name_vs2010(x)
                             for x in outputs]))

        else:
            element = None
            for rule in rule_list:
                for key in rule:
                    if key(base_name):
                        record = rule[key]
                        for item in record:
                            if element is None:
                                element = VS2003Tool(tool_name)
                                self.add_element(element)

                            value = record[item]
                            enum_table = lookup_enum_value(tool_enums, item, None)
                            if enum_table:
                                new_value = lookup_enum_value(
                                    enum_table[1], value, None)
                                if new_value is not None:
                                    value = str(new_value)

                            element.add_default(
                                VSStringProperty(
                                    item,
                                    convert_file_name_vs2010(value)))


########################################


class VS2003File(VS2003XML):
    """
    Visual Studio 2003-2008 File record

    Attributes:
        source_file: SourceFile record
        project: Parent project
    """

    def __init__(self, source_file, project):
        """
        Init defaults.

        Args:
            source_file: SourceFile record to extract defaults.
            project: parent Project
        """

        self.source_file = source_file
        self.project = project
        vs_name = source_file.vs_name
        VS2003XML.__init__(
            self, 'File', [
                VSStringProperty('RelativePath',
                               vs_name)], force_pair=True)

        # Add in the file customizations

        # Get the base name for comparison
        index = vs_name.rfind('\\')
        base_name = vs_name if index == -1 else vs_name[index + 1:]

        # Perform all of the customizations
        for configuration in project.configuration_list:
            file_config = VS2003FileConfiguration(
                configuration, base_name, source_file)
            # Only add if it has anything inside
            if file_config.elements or len(file_config.attributes) > 1:
                self.elements.append(file_config)

########################################


class VS2003Filter(VS2003XML):
    """
    Visual Studio 2003-2008 File record

    Attributes:
        name: Name of the filter
        project: Parent project
    """

    def __init__(self, name, project):
        """
        Init defaults.

        Args:
            name: name of the filter.
            project: Parent Project
        """

        self.name = name
        self.project = project
        VS2003XML.__init__(self, 'Filter', [VSStringProperty('Name', name)])


class VS2003Files(VS2003XML):
    """
    Visual Studio 2003-2008 Files record

    Attributes:
        project: Parent project
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        self.project = project
        VS2003XML.__init__(self, 'Files')

        # Create group names and attach all files that belong to that group
        groups = {}
        for item in project.codefiles:
            groupname = item.get_group_name()

            # Put each filename in its proper group
            item.vs_name = convert_to_windows_slashes(item.relative_pathname)
            group = groups.get(groupname, None)
            if group is None:
                groups[groupname] = [item]
            else:
                group.append(item)

        # Convert from a flat tree into a hierarchical tree
        tree = {}
        for group in groups:

            # Get the depth of the tree needed
            parts = group.split('\\')
            nexttree = tree

            # Iterate over every part
            for item, _ in enumerate(parts):
                # Already declared?
                if not parts[item] in nexttree:
                    nexttree[parts[item]] = {}
                # Step into the tree
                nexttree = nexttree[parts[item]]

        # Generate the file tree
        do_tree(self, '', tree, groups)

########################################


class VS2003vcproj(VS2003XML):
    """
    Visual Studio 2003-2008 formatter.

    This record instructs how to write a Visual Studio 2003-2008 format
    vcproj file.

    Attributes:
        project: Parent project
        platforms: VS2003Platforms
        toolfiles: VS2003ToolFiles
        configuration_list: VS2003Configurations
        references: VS2003References
        files: VS2003Files
        globals: VS2003Globals
    """

    def __init__(self, project):
        """
        Init defaults.

        Args:
            project: Project record to extract defaults.
        """

        self.project = project

        # Which project type?
        ide = project.ide
        if ide is IDETypes.vs2003:
            version = '7.10'
        elif ide is IDETypes.vs2005:
            version = '8.00'
        else:
            version = '9.00'

        name = project.name

        VS2003XML.__init__(
            self, 'VisualStudioProject',
            [VSStringProperty('ProjectType', 'Visual C++'),
             VSStringProperty('Version', version),
             VSStringProperty('Name', name),
             VSStringProperty('ProjectGUID',
                            '{' + project.vs_uuid + '}')])

        self.add_default(
            VSStringProperty('RootNamespace', name))

        self.add_default(VSStringProperty('Keyword', 'Win32Proj'))
        if ide is IDETypes.vs2008:
            self.add_default(
                VSStringProperty('TargetFrameworkVersion', '196613'))

        # Add all the sub chunks
        self.platforms = VS2003Platforms(project)
        self.add_element(self.platforms)

        self.toolfiles = VS2003ToolFiles(project)
        if ide is not IDETypes.vs2003:
            self.add_element(self.toolfiles)

        self.configuration_list = VS2003Configurations(project)
        self.add_element(self.configuration_list)

        self.references = VS2003References()
        self.add_element(self.references)

        self.files = VS2003Files(project)
        self.add_element(self.files)

        self.globals = VS2003Globals()
        self.add_element(self.globals)

    ########################################

    def generate(self, line_list=None, indent=0, ide=None):
        """
        Write out the VisualStudioProject record.

        Args:
            line_list: string list to save the XML text
            indent: Level of indentation to begin with.
            ide: IDE to generate for.
        """

        if line_list is None:
            line_list = []

        if ide is None:
            ide = IDETypes.vs2008

        # XML is utf-8 only
        line_list.append('<?xml version="1.0" encoding="UTF-8"?>')
        return VS2003XML.generate(
            self, line_list=line_list, indent=indent, ide=ide)


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

    for project in solution.get_project_list():
        project.vs_output_filename = '{}{}{}.vcproj'.format(
            project.name, project.solution.ide_code, project.platform_code)
        project.vs_uuid = get_uuid(project.vs_output_filename)

        for configuration in project.configuration_list:
            vs_platform = configuration.platform.get_vs_platform()[0]
            configuration.vs_platform = vs_platform
            configuration.vs_configuration_name = '{}|{}'.format(
                configuration.name, vs_platform)

    # Write to memory for file comparison
    error, solution_lines = generate_solution_file(solution)
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
        bom=solution.ide != IDETypes.vs2003,
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
                               FileTypes.glsl])

        # Create the project file template
        exporter = VS2003vcproj(project)

        # Convert to a text file
        project_lines = exporter.generate(ide=solution.ide)

        # Save the text
        save_text_file_if_newer(
            os.path.join(
                solution.working_directory,
                project.vs_output_filename),
            project_lines,
            bom=True,
            perforce=perforce,
            verbose=verbose)

    return 0
