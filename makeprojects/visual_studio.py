#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Project file generator for Microsoft Visual Studio 2003-2008.

This module contains classes needed to generate project files intended for use
by Microsoft's Visual Studio 2003, 2005 and 2008.

@package makeprojects.visual_studio

@var makeprojects.visual_studio.SUPPORTED_IDES
List of IDETypes the visual_studio module supports.

@var makeprojects.visual_studio._SLNFILE_MATCH
Regex for matching files with *.sln

@var makeprojects.visual_studio._VS_VERSION_YEARS
Dict of version year strings to integers 2012-2022

@var makeprojects.visual_studio._VS_OLD_VERSION_YEARS
Dict of version year strings 2003-2012 to integers

@var makeprojects.visual_studio._VS_SDK_ENV_VARIABLE
Dict of environment variables for game consoles

@var makeprojects.visual_studio._VS_SLOW_MSBUILD
Tuple of Visual Studio targets that build slowly with msbuild

@var makeprojects.visual_studio._VS_PLATFORM_HACK
Dict of android targets to remap from nVidia to Microsoft tool chains
"""

# pylint: disable=consider-using-f-string
# pylint: disable=invalid-name
# pylint: disable=too-many-lines

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import operator
from re import compile as re_compile
from burger import save_text_file_if_newer, convert_to_windows_slashes, \
    escape_xml_cdata, escape_xml_attribute, where_is_visual_studio, \
    load_text_file, string_to_bool, delete_file
from ide_gen import vs_calcguid

try:
    from wslwinreg import convert_to_windows_path
except ImportError:
    pass

from .validators import VSBooleanProperty, VSStringProperty, VSEnumProperty, \
    VSStringListProperty, VSIntegerProperty, lookup_enum_value
from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes, \
    source_file_detect
from .hlsl_support import HLSL_ENUMS, make_hlsl_command
from .glsl_support import make_glsl_command
from .masm_support import MASM_ENUMS, make_masm_command
from .build_objects import BuildObject, BuildError
from .visual_studio_utils import get_path_property, \
    convert_file_name_vs2010, add_masm_support, create_deploy_script, \
    generate_solution_file, wiiu_props
from .visual_studio_2010 import VS2010vcproj, VS2010vcprojfilter
from .core import Configuration

########################################

# List of all Visual Studio versions supported
SUPPORTED_IDES = (
    IDETypes.vs2003,
    IDETypes.vs2005,
    IDETypes.vs2008,
    IDETypes.vs2010,
    IDETypes.vs2012,
    IDETypes.vs2013,
    IDETypes.vs2015,
    IDETypes.vs2017,
    IDETypes.vs2019,
    IDETypes.vs2022)

# Match .sln files
_SLNFILE_MATCH = re_compile("(?is).*\\.sln\\Z")

# All version years
_VS_VERSION_YEARS = {
    "2012": 2012,
    "2013": 2013,
    "14": 2015,
    "15": 2017,
    "16": 2019,
    "17": 2022
}

# Previous version years
_VS_OLD_VERSION_YEARS = {
    "8.00": 2003,
    "9.00": 2005,
    "10.00": 2008,
    "11.00": 2010,
    "12.00": 2012
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
    "Cafe": "CAFE_ROOT_DOS",        # Nintendo WiiU
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

# List of visual studio targets that are slower using msbuild
_VS_SLOW_MSBUILD = (
    "PS3",                      # PS3
    "ORBIS",                    # PS4
    "Prospero",                 # PS5
    "PSP",                      # PSP
    "PSVita",                   # PS Vita
    "ARM-Android-NVIDIA",       # nVidia android tools
    "AArch64-Android-NVIDIA",   # nVidia android tools
    "x86-Android-NVIDIA",       # nVidia android tools
    "x64-Android-NVIDIA",       # nVidia android tools
    "Tegra-Android"
)

# Dict of android targets to remap to Microsoft tool chain
_VS_PLATFORM_HACK = {
    "x86-Android-NVIDIA": "x86",
    "x64-Android-NVIDIA": "x64",
    "ARM-Android-NVIDIA": "ARM",
    "AArch64-Android-NVIDIA": "ARM64"}

########################################


def parse_sln_file(full_pathname):
    """
    Find build targets in .sln file.

    Given a .sln file for Visual Studio 2003 through 2022, locate and extract
    all of the build targets available and return the list.

    It will also determine which version of Visual Studio this solution
    file requires.

    Args:
        full_pathname: Pathname to the .sln file

    Returns:
        tuple(list of configuration strings, integer Visual Studio version year)
    """

    # Load in the .sln file, it's a text file (Can be UTF-8)
    file_lines = load_text_file(full_pathname)

    # Version not known yet
    vs_version = 0

    # Start with an empty set
    target_set = set()

    if file_lines:
        # Not looking for "Visual Studio"
        looking_for_visual_studio = False

        # Not looking for EndGlobalSection
        looking_for_end_global_section = False

        # Parse
        for line in file_lines:

            # Scanning for "EndGlobalSection"?

            if looking_for_end_global_section:

                # Once the end of the section is reached, end
                if "EndGlobalSection" in line:
                    looking_for_end_global_section = False
                else:

                    # The line contains "Debug|Win32 = Debug|Win32"
                    # Split it in half at the equals sign and then
                    # remove the whitespace and add to the list
                    target = line.split("=")[-1].strip()
                    target_set.add(target)
                continue

            # Scanning for the secondary version number in Visual Studio 2012 or
            # higher

            if looking_for_visual_studio and "# Visual Studio" in line:
                # The line contains "# Visual Studio 15" or "# Visual Studio
                # Version 16"

                # Use the version number to determine which visual studio to
                # launch
                vs_version = _VS_VERSION_YEARS.get(line.rsplit()[-1], 0)
                looking_for_visual_studio = False
                continue

            # Get the version number
            if "Microsoft Visual Studio Solution File" in line:
                # The line contains
                # "Microsoft Visual Studio Solution File, Format Version 12.00"
                # The number is in the last part of the line
                # Use the version string to determine which visual studio to
                # launch
                vs_version = _VS_OLD_VERSION_YEARS.get(line.split()[-1], 0)
                if vs_version == 2012:
                    # 2012 or higher requires a second check
                    looking_for_visual_studio = True
                continue

            # Look for this section, it contains the configurations
            if "(SolutionConfigurationPlatforms)" in line or \
                    "(ProjectConfiguration)" in line:
                looking_for_end_global_section = True

    # Exit with the results
    if not vs_version:
        print(
            ("The visual studio solution file {} "
             "is corrupt or an unknown version!").format(full_pathname),
            file=sys.stderr)

    # Return the set as a list
    return (list(target_set), vs_version)

########################################


class BuildVisualStudioFile(BuildObject):
    """
    Class to build Visual Studio files.

    This builds files from Visual Studio 2003-2022.

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

    def build_clean(self, build=True):
        """
        Build or clean a visual studio .sln file.
        @details
        Supports Visual Studio 2003 - 2022. Supports platforms Win32, x64,
        Android, nVidia Tegra, PS3, ORBIS, PSP, PSVita, Xbox, Xbox 360,
        Xbox ONE, Switch, Wii

        Args:
            build: If true, build, otherwise clean

        Returns:
            List of BuildError objects

        See Also:
            parse_sln_file
        """

        # Get the target
        targettypes = self.configuration.rsplit("|")

        # Locate the proper version of Visual Studio for this .sln file
        # Note, some platforms, like the Sony ones, build really slowly
        # if invoked directly with MSBUILD.

        vstudiopath = None
        if len(targettypes) >= 2:

            # Is it a platform that supports 64 bit msbuild?
            if targettypes[1] not in _VS_SLOW_MSBUILD:
                vstudiopath = where_is_visual_studio(
                    self.vs_version, "msbuild.exe")

        # MSBUILD not found? Use the IDE instead.
        if vstudiopath is None:
            vstudiopath = where_is_visual_studio(self.vs_version, "devenv.com")

        # Is Visual studio installed? Abort if not.
        file_name = self.file_name
        if vstudiopath is None:
            msg = (
                "{} requires Visual Studio version {}"
                " to be installed to build!").format(
                file_name, self.vs_version)
            print(msg, file=sys.stderr)
            return BuildError(0, file_name, msg=msg)

        # Certain targets require an installed SDK
        # verify that the SDK is installed before trying to build

        if len(targettypes) >= 2:
            test_env = _VS_SDK_ENV_VARIABLE.get(targettypes[1], None)
            if test_env:
                if os.getenv(test_env, default=None) is None:
                    msg = (
                        "Target {} was detected but the environment variable {}"
                        " was not found.").format(
                        targettypes[1], test_env)
                    print(msg, file=sys.stderr)
                    return BuildError(
                        0,
                        file_name,
                        configuration=self.configuration,
                        msg=msg)

        # Create the build or clean command
        # Note: Use the single line form, because Windows will not
        # process the target properly due to the presence of the | character
        # which causes piping.

        if vstudiopath.endswith(".com"):

            # Use IDE
            # Visual Studio 2003 doesn't support setting platforms, just use the
            # configuration name
            if self.vs_version == 2003:
                target = targettypes[0]
            else:
                target = self.configuration

            option = "/Build" if build else "/Clean"
            cmd = [vstudiopath, convert_to_windows_path(
                file_name), option, target]
        else:
            option = "-t:Build" if build else "-t:Clean"

            # Use MSBuild
            cmd = [vstudiopath, option, "-v:m", "-noLogo", "-m",
                "-p:Configuration={0};Platform={1}".format(
                    targettypes[0], targettypes[1]), convert_to_windows_path(
                    file_name)]

        # Show the command immediately
        if self.verbose:
            print(" ".join(cmd))
        sys.stdout.flush()

        # Invoke Visual Studio
        return self.run_command(cmd, self.verbose)

    ########################################

    def build(self):
        """
        Build a visual studio .sln file.
        @details
        Supports Visual Studio 2003 - 2022. Supports platforms Win32, x64,
        Android, nVidia Tegra, PS3, ORBIS, PSP, PSVita, Xbox, Xbox 360,
        Xbox ONE, Switch, Wii

        Returns:
            List of BuildError objects
        See Also:
            parse_sln_file
        """

        return self.build_clean(True)

    ########################################

    def clean(self):
        """
        Delete temporary files.
        @details
        This function is called by ``cleanme`` to remove temporary files.

        On exit, return 0 for no error, or a non zero error code if there was an
        error to report. None if not implemented or not applicable.

        Returns:
            None if not implemented, otherwise an integer error code.
        """

        return self.build_clean(False)


########################################


def match(filename):
    """
    Check if the filename is a type that this module supports

    Match if the filename ends with .sln.

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
        list of BuildVisualStudioFile classes
    """

    # Get the list of build targets
    targetlist, vs_version = parse_sln_file(file_name)

    # Was the file corrupted?
    if not vs_version:
        print(file_name + " is corrupt!")
        return []

    results = []
    for target in targetlist:
        if configurations:
            targettypes = target.rsplit("|")
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
        print(file_name + " is corrupt!")
        return []

    results = []
    for target in targetlist:
        if configurations:
            targettypes = target.rsplit("|")
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
    """
    Filter for supported platforms

    Test for classic xbox that can be built with
    Visual Studio 2003. Windows on all versions.

    Game consoles, are a long list...

    Args:
        ide: enums.IDETypes
        platform_type: enums.PlatformTypes

    Returns:
        True if supported, False if not
    """

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-return-statements

    # Windows 32 is always supported
    if platform_type is PlatformTypes.win32:
        return True

    # VS 2003 only supports Xbox Classic or Windows 32
    # so early out
    if ide is IDETypes.vs2003:
        return platform_type is PlatformTypes.xbox

    # Everyone else supports AMD 64
    if platform_type is PlatformTypes.win64:
        return True

    # Windows for ARM only shows up on Visual Studio 2017 and higher
    if platform_type in (PlatformTypes.winarm32, PlatformTypes.winarm64):
        return ide >= IDETypes.vs2017

    # Xbox platforms
    if platform_type is PlatformTypes.xbox360:
        return IDETypes.vs2010 <= ide <= IDETypes.vs2017

    if platform_type.is_xboxone():
        return ide >= IDETypes.vs2015

    # Sony platforms
    if ide < IDETypes.vs2017:
        if platform_type in (PlatformTypes.ps3, PlatformTypes.vita):
            return True

    if ide >= IDETypes.vs2017:
        if platform_type in (PlatformTypes.ps4, PlatformTypes.ps5):
            return True

    # Google platforms
    if ide >= IDETypes.vs2017:
        if platform_type is PlatformTypes.stadia:
            return True

    # Nintendo platforms
    if ide >= IDETypes.vs2012:
        if platform_type is PlatformTypes.wiiu:
            return True

    if ide >= IDETypes.vs2015:
        if platform_type in (PlatformTypes.switch32, PlatformTypes.switch64):
            return True

    # Android
    if ide >= IDETypes.vs2013:
        if platform_type in (PlatformTypes.tegra,
                             PlatformTypes.androidarm32,
                             PlatformTypes.androidarm64,
                             PlatformTypes.androidintel32,
                             PlatformTypes.androidintel64):
            return True

    return False

########################################

# Entries set internally

########################################


def ExcludedFromBuild(fallback=None):
    """
    Create ``ExcludedFromBuild`` property.

    Ignore from build if True.

    Args:
        fallback: Boolean for the value
    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty("ExcludedFromBuild", fallback=fallback)

########################################


def Name(fallback):
    """
    Create ``Name`` property.

    Simple string with the ``Name`` keyword

    No external overrides

    Args:
        fallback: String for the value
    Returns:
        validators.VSStringProperty object.
    """

    return VSStringProperty("Name", fallback)

########################################

# Entries usually found in VS2003Configuration

########################################


def OutputDirectory(configuration, fallback=None):
    """
    Create ``OutputDirectory`` property.

    Directory to store the final exe/lib file output. Will remap to OutDir

    Can be overridden with configuration attribute
    ``vs_OutputDirectory`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    # Convert to string object
    result = VSStringProperty.vs_validate(
        "OutputDirectory",
        configuration,
        fallback)

    # Post sanity check. Make sure it's terminated with a slash and in Windows
    # format
    fallback = result.get_value()
    if fallback:
        result.value = convert_to_windows_slashes(
            fallback,
            force_ending_slash=True)

    return result

########################################


def IntermediateDirectory(configuration, fallback=None):
    """
    Create ``IntermediateDirectory`` property.

    Directory to store the intermediate outputs such as .obj and .res files

    Can be overridden with configuration attribute
    ``vs_IntermediateDirectory`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    # Convert to string object
    result = VSStringProperty.vs_validate(
        "IntermediateDirectory",
        configuration,
        fallback)

    # Post sanity check. Make sure it's terminated with a slash and in Windows
    # format
    fallback = result.get_value()
    if fallback:
        result.value = convert_to_windows_slashes(
            fallback,
            force_ending_slash=True)

    return result

########################################


def ConfigurationType(configuration, fallback=None):
    """
    Create ``ConfigurationType`` property.

    Type of project generated, dll, static lib, executable.

    No external overrides

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSIntegerProperty object.
    """

    # If not overridden, map it out.
    if fallback is None:

        # The numbers don't map to an enum, since Utility is 10
        # So manually map to the supported project types
        project_type = configuration.project_type
        if project_type is ProjectTypes.library:
            fallback = 4
        elif project_type is ProjectTypes.sharedlibrary:
            fallback = 2
        else:
            fallback = 1

    # Xbox doesn't support shared libraries, convert to library
    if fallback == 2 and configuration.platform is PlatformTypes.xbox:
        fallback = 4

    return VSIntegerProperty("ConfigurationType", fallback)


########################################

def UseOfMFC(configuration, fallback=None):
    """
    Create ``UseOfMFC`` property.

    Enable the use of MFC, static or dynamic library.

    Can be overridden with configuration attribute
    ``vs_UseOfMFC`` for the C compiler.

    * "Default" / "None" / "No"
    * "Static"
    * "Dynamic" / "DLL"
    * 0 through 2

    Note:
        Only available on Windows platforms

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    # Only available on Windows
    if not configuration.platform.is_windows():
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_UseOfMFC")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "UseOfMFC",
        fallback,
        (("Default", "None", "No"),
         ("Static", "Yes"),
         ("Dynamic", "DLL")))

########################################


def UseOfATL(configuration, fallback=None):
    """
    Create ``UseOfATL`` property.

    Enable the use of Advanced Template Library, static or dynamic.

    Can be overridden with configuration attribute
    ``vs_UseOfATL`` for the C compiler.

    * "Default" / "None" / "No"
    * "Static"
    * "Dynamic" / "DLL"
    * 0 through 2

    Note:
        Only available on Windows platforms

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    # Only available on Windows
    if not configuration.platform.is_windows():
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_UseOfATL")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "UseOfATL",
        fallback,
        (("Default", "None", "No"),
         ("Static", "Yes"),
         ("Dynamic", "DLL")))

########################################


def ATLMinimizesCRunTimeLibraryUsage(configuration, fallback=None):
    """
    Create ``ATLMinimizesCRunTimeLibraryUsage`` property.

    Tells ATL to link to the C runtime libraries statically to minimize
    dependencies; requires that ``Use of ATL`` to be set.

    Can be overridden with configuration attribute
    ``vs_ATLMinimizesCRunTimeLibraryUsage`` for the C compiler.

    Note:
        Not available on Visual Studio 2008 or later and only available on
        Windows platforms

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # Only available on Windows
    if not configuration.platform.is_windows():
        return None

    # VS2003/2005 only
    if configuration.ide is IDETypes.vs2008:
        return None

    return VSBooleanProperty.vs_validate(
        "ATLMinimizesCRunTimeLibraryUsage",
        configuration,
        fallback)

########################################


def CharacterSet(configuration, fallback=None):
    """
    Create ``CharacterSet`` property.

    Choose if Unicode or ASCII defaults are used during Windows compilation.

    Can be overridden with configuration attribute
    ``vs_CharacterSet`` for the C compiler.

    * "Default"
    * "Unicode"
    * "MultiByte" / "ASCII"
    * 0 through 2

    Note:
        Only available on Windows platforms

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    # Only available on Windows
    if not configuration.platform.is_windows():
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_CharacterSet")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "CharacterSet",
        fallback,
        ("Default",
         "Unicode",
         ("MultiByte", "ASCII")))

########################################


def ManagedExtensions(configuration, fallback=None):
    """
    Create ``ManagedExtensions`` property.

    Enable the level of Common Language Runtime support

    Compiler switches /clr, /clr:pure, /clr:safe, /clr:oldSyntax

    Can be overridden with configuration attribute
    ``vs_ManagedExtensions`` for the C compiler.

    * "No", "Default"
    * "/clr" / "CLR" / "Yes"
    * "/clr:pure" / "Pure MISL" / "MISL" / "Pure"
    * "/clr:safe" / "Safe MISL" / "Safe"
    * "/clr:oldSyntax" / "Old MISL" / "Old"
    * 0 through 4

    Note:
        A boolean on Visual Studio 2003, an enum on 2005/2008

    Note:
        Only available on Windows platforms

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty or validators.VSBooleanProperty object.
    """

    # Only available on Windows
    if not configuration.platform.is_windows():
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_ManagedExtensions")
    if value is not None:
        fallback = value

    # Visual Studio 2003 only has "Yes" or "No"
    # So, convert the value into a boolean
    if configuration.ide is IDETypes.vs2003:

        if fallback is not None:
            # Is there a value?
            # Try the easy way first, is it a number, "Yes", "True"?
            try:
                fallback = string_to_bool(fallback)

            # Assume exceptions are requested
            except ValueError:
                fallback = True

        # Enable/Disable Common Language Runtime
        return VSBooleanProperty(
            "ManagedExtensions",
            fallback)

    # Visual Studio 2005, 2008 version uses enums

    # If a bool, use /clr if True
    if isinstance(fallback, bool):
        fallback = "Yes" if fallback else "No"

    return VSEnumProperty(
        "ManagedExtensions",
        fallback,
        (("No", "Default"),
        ("/clr", "CLR", "Yes"),
        ("/clr:pure", "Pure MISL", "MISL", "Pure"),
        ("/clr:safe", "Safe MISL", "Safe"),
        ("/clr:oldSyntax", "Old MISL", "Old")))

########################################


def DeleteExtensionsOnClean(configuration, fallback=None):
    """
    Create ``DeleteExtensionsOnClean`` property.

    List of file extensions to remove on clean.

    Can be overridden with configuration attribute
    ``vs_DeleteExtensionsOnClean`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_unique_chained_list(
        "vs_DeleteExtensionsOnClean")
    if value:
        fallback = value

    return VSStringListProperty(
        "DeleteExtensionsOnClean",
        fallback,
        slashes="\\")

########################################


def WholeProgramOptimization(configuration, fallback=None):
    """
    Create ``WholeProgramOptimization`` property.

    Enable the type of link time code generation

    Can be overridden with configuration attribute
    ``vs_WholeProgramOptimization`` for the C compiler.

    * "No", "Default"
    * "Yes", "On"
    * "Instrument"
    * "Optimize"
    * "Update"
    * 0 through 4

    Note:
        A boolean on Visual Studio 2003, an enum on 2005/2008

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty or validators.VSBooleanProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_WholeProgramOptimization")
    if value is not None:
        fallback = value

    # Visual Studio 2003 only has "Yes" or "No"
    # So, convert the value into a boolean
    if configuration.ide is IDETypes.vs2003:

        if fallback is not None:
            # Is there a value?
            # Try the easy way first, is it a number, "Yes", "True"?
            try:
                fallback = string_to_bool(fallback)

            # Assume exceptions are requested
            except ValueError:
                fallback = True

        # Enable/Disable link time code generation
        return VSBooleanProperty(
            "WholeProgramOptimization",
            fallback)

    # Visual Studio 2005, 2008 version uses enums

    # If a bool, use LTCG if True
    if isinstance(fallback, bool):
        fallback = "Yes" if fallback else "No"

    return VSEnumProperty(
        "WholeProgramOptimization",
        fallback,
        (("No", "Default"),
        ("Yes", "On"),
         "Instrument",
        "Optimize",
        "Update"))

########################################


def ReferencesPath(configuration, fallback=None):
    """
    Create ``ReferencesPath`` property.

    List of folders for file references.

    Can be overridden with configuration attribute
    ``vs_ReferencesPath`` for the C compiler.

    Note:
        Only available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       None or validators.VSStringListProperty object.
    """

    # Visual Studio 2003 only
    if configuration.ide is not IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_unique_chained_list(
        "vs_ReferencesPath")
    if value:
        fallback = value

    return VSStringListProperty(
        "ReferencesPath",
        fallback,
        slashes="\\")

########################################

# Entries usually found in VCCLCompilerTool


def UseUnicodeResponseFiles(configuration, prefix=None):
    """
    Create ``UseUnicodeResponseFiles`` property.

    Instructs the project system to generate UNICODE response files when
    spawning the librarian.  Set this property to True when files in the project
    have UNICODE paths.

    Can be overridden with configuration attributes:

    * ``vs_UseUnicodeResponseFiles`` for the C compiler.
    * ``vs_LinkerUseUnicodeResponseFiles`` for the exe/lib linker.

    Note:
        Not available on Visual Studio 2003 and earlier. Overrides do nothing.

    Args:
        configuration: Project configuration to scan for overrides.
        prefix: Prefix string for override

    Returns:
        validators.VSBooleanProperty object.
    """

    # Only 2005 / 2008
    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "UseUnicodeResponseFiles",
        configuration,
        prefix=prefix)


########################################


def AdditionalOptions(configuration, fallback=None, prefix=None):
    """
    Create ``AdditionalOptions`` property.

    List of custom compiler options as a single string. The default is an empty
    string. Will not generate this attribute if the string is empty.

    Can be overridden with configuration attributes:

    * ``vs_AdditionalOptions`` for the C compiler.
    * ``vs_LinkerAdditionalOptions`` for the exe/lib linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use
        prefix: Prefix string for override

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "AdditionalOptions",
        configuration,
        fallback,
        prefix=prefix)

########################################


def Optimization(configuration, fallback=None):
    """
    Create ``Optimization`` property.

    Set the level of code optimization for the C compiler.

    Compiler switches /Od, /O1, /O2, /Ox

    Can be overridden with configuration attribute
    ``vs_Optimization`` for the C compiler.

    Acceptable inputs are:

    * "/Od" / "-Od" / "Disabled"
    * "/O1" / "-O1" / "Minimize Size"
    * "/O2" / "-O2" / "Maximize Speed"
    * "/Ox" / "-Ox" / "Full Optimization" / "x"
    * "Custom" (This disables emitting a command switch)
    * 0 through 4

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use
    Returns:
       validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_Optimization")
    if value is not None:
        fallback = value

    # The settings are the same on 2003, 2005, and 2008
    return VSEnumProperty(
        "Optimization",
        fallback,
        (("/Od", "-Od", "Disabled"),
         ("/O1", "-O1", "Minimize Size"),
         ("/O2", "-O2", "Maximize Speed"),
         ("/Ox", "-Ox", "Full Optimization", "x"),
         "Custom"))

########################################


def GlobalOptimizations(configuration, fallback=None):
    """
    Create ``GlobalOptimizations`` property.

    Enables global optimizations incompatible with all ``Runtime Checks``
    options and edit and continue. Also known as ``WholeProgramOptimizations``
    on other versions of Visual Studio.

    Compiler switch /Og

    Can be overridden with configuration attribute
    ``vs_GlobalOptimizations`` for the C compiler.

    Note:
        Only available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # Only 2003
    if configuration.ide is not IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "GlobalOptimizations",
        configuration,
        fallback)


########################################


def InlineFunctionExpansion(configuration, fallback=None):
    """
    Create ``InlineFunctionExpansion`` property.

    Determine how aggressive to inline code during C compilation.

    Compiler switches /Ob1, /Ob2

    Can be overridden with configuration attribute
    ``vs_InlineFunctionExpansion`` for the C compiler.

    Acceptable inputs are:

    * "Disable"
    * "/Ob1" / "Only __inline"
    * "/Ob2" / "Any Suitable"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_InlineFunctionExpansion")
    if value is not None:
        fallback = value

    # The settings are the same on 2003, 2005, and 2008
    return VSEnumProperty(
        "InlineFunctionExpansion",
        fallback,
        ("Disable",
         ("/Ob1", "Only __inline"),
         ("/Ob2", "Any Suitable")))

########################################


def EnableIntrinsicFunctions(configuration, fallback=None):
    """
    Create ``EnableIntrinsicFunctions`` property.

    Enables intrinsic functions. Using intrinsic functions generates faster,
    but possibly larger, code.

    Compiler switch /Oi

    Can be overridden with configuration attribute
    ``vs_EnableIntrinsicFunctions`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "EnableIntrinsicFunctions",
        configuration,
        fallback)

########################################


def ImproveFloatingPointConsistency(configuration, fallback=None):
    """
    Create ``ImproveFloatingPointConsistency`` property.

    Enables intrinsic functions. Using intrinsic functions generates faster,
    but possibly larger, code.

    Compiler switch /Op

    Can be overridden with configuration attribute
    ``vs_ImproveFloatingPointConsistency`` for the C compiler.

    Note:
        Only available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # Only 2003
    if configuration.ide is not IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "ImproveFloatingPointConsistency",
        configuration,
        fallback)


########################################


def FavorSizeOrSpeed(configuration, fallback=None):
    """
    Create ``FavorSizeOrSpeed`` property.

    Determine if optimizations should focus on saving space vs unrolling loops.

    Compiler switches /Ot, /Os

    Can be overridden with configuration attribute
    ``vs_FavorSizeOrSpeed`` for the C compiler.

    Acceptable inputs are:

    * "Neither"
    * "/Ot" / "Favor Fast Code"
    * "/Os" / "Favor Small Code"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_FavorSizeOrSpeed")
    if value is not None:
        fallback = value

    # The settings are the same on 2003, 2005, and 2008
    return VSEnumProperty(
        "FavorSizeOrSpeed",
        fallback,
        ("Neither",
         ("/Ot", "Favor Fast Code"),
         ("/Os", "Favor Small Code")))

########################################


def OmitFramePointers(configuration, fallback=None):
    """
    Create ``OmitFramePointers`` property.

    Suppress frame pointers.

    Compiler switch /Oy

    Can be overridden with configuration attribute
    ``vs_OmitFramePointers`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "OmitFramePointers",
        configuration,
        fallback)

########################################


def EnableFiberSafeOptimizations(configuration, fallback=None):
    """
    Create ``EnableFiberSafeOptimizations`` property.

    Enables memory space optimization when using fibers and thread local
    torage access.

    Compiler switch /GT

    Can be overridden with configuration attribute
    ``vs_EnableFiberSafeOptimizations`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "EnableFiberSafeOptimizations",
        configuration,
        fallback)

########################################


def OptimizeForProcessor(configuration, fallback=None):
    """
    Create ``OptimizeForProcessor`` property.

    Determine if optimizations should focus on specific Pentium processors.

    Compiler switches /G5, /G6, /G7

    Can be overridden with configuration attribute
    ``vs_OptimizeForProcessor`` for the C compiler.

    Acceptable inputs are:

    * "Blended"
    * "/G5" / "Pentium"
    * "/G6" / "Pentium Pro" / "Pentium II" / "Pentium III"
    * "/G7" / "Pentium IV" / "Pentium 4"
    * 0 through 3

    Note:
        Only available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    # Only 2003
    if configuration.ide is not IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_OptimizeForProcessor")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "OptimizeForProcessor",
        fallback,
        ("Blended",
        ("/G5", "Pentium"),
        ("/G6", "Pentium Pro", "Pentium II", "Pentium III"),
        ("/G7", "Pentium IV", "Pentium 4")))


########################################


def OptimizeForWindowsApplication(configuration, fallback=None):
    """
    Create ``OptimizeForWindowsApplication`` property.

    Specify whether to optimize code in favor of Windows.EXE execution.

    Compiler switch /GA

    Can be overridden with configuration attribute
    ``vs_OptimizeForWindowsApplication`` for the C compiler.

    Note:
        Only available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # Only 2003
    if configuration.ide is not IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "OptimizeForWindowsApplication",
        configuration,
        fallback)


########################################


def WholeProgramOptimization2003(configuration, fallback=None):
    """
    Create ``WholeProgramOptimization`` property for VS 2003.

    Enables cross-module optimizations by delaying code generation to link
    time; requires that linker option ``Link Time Code Generation`` be turned
    on.

    Compiler switch /GL

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # Only 2005 / 2008
    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty(
        "WholeProgramOptimization",
        fallback)

########################################


def AdditionalIncludeDirectories(configuration, fallback=None):
    """
    Create ``AdditionalIncludeDirectories`` property.

    List of include folders for the C compiler

    Can be overridden with configuration attribute
    ``vs_AdditionalIncludeDirectories`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_unique_chained_list(
        "vs_AdditionalIncludeDirectories")
    if value:
        fallback = value

    return VSStringListProperty(
        "AdditionalIncludeDirectories",
        fallback,
        slashes="\\")

########################################


def AdditionalUsingDirectories(configuration, fallback=None):
    """
    Create ``AdditionalUsingDirectories`` property.

    List of include folders for the # using operation.

    Can be overridden with configuration attribute
    ``vs_AdditionalUsingDirectories`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_unique_chained_list(
        "vs_AdditionalUsingDirectories")
    if value:
        fallback = value

    return VSStringListProperty(
        "AdditionalUsingDirectories",
        fallback,
        slashes="\\")

########################################


def PreprocessorDefinitions(configuration, fallback=None):
    """
    Create ``PreprocessorDefinitions`` property.

    List of defines to pass to the C compiler

    Can be overridden with configuration attribute
    ``vs_PreprocessorDefinitions`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list(
        "vs_PreprocessorDefinitions")
    if value:
        fallback = value

    return VSStringListProperty(
        "PreprocessorDefinitions",
        fallback)

########################################


def IgnoreStandardIncludePath(configuration, fallback=None):
    """
    Create ``IgnoreStandardIncludePath`` property.

    Ignore standard include paths.

    Compiler switch /X

    Can be overridden with configuration attribute
    ``vs_IgnoreStandardIncludePath`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "IgnoreStandardIncludePath",
        configuration,
        fallback)

########################################


def GeneratePreprocessedFile(configuration, fallback=None):
    """
    Create ``GeneratePreprocessedFile`` property.

    Determine if a preprocessed file is to be generated.

    Compiler switches /P, /EP

    Can be overridden with configuration attribute
    ``vs_GeneratePreprocessedFile`` for the C compiler.

    Acceptable inputs are:

    * "No"
    * "/P" / "With Line Numbers"
    * "/EP" / "Without Line Numbers"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_GeneratePreprocessedFile")
    if value is not None:
        fallback = value

    # The settings are the same on 2003, 2005, and 2008
    return VSEnumProperty(
        "GeneratePreprocessedFile",
        fallback,
        ("No",
         ("/P", "With Line Numbers"),
         ("/EP", "/EP /P", "Without Line Numbers")))

########################################


def KeepComments(configuration, fallback=None):
    """
    Create ``KeepComments`` property.

    Suppresses comment strip from source code; requires that one of the
    ``Preprocessing`` options be set.

    Compiler switch /C

    Can be overridden with configuration attribute
    ``vs_KeepComments`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "KeepComments",
        configuration,
        fallback)

########################################


def StringPooling(configuration, fallback=None):
    """
    Create ``StringPooling`` property.

    Enable read-only string pooling for generating smaller compiled code.

    Compiler switch /GF

    Can be overridden with configuration attribute
    ``vs_StringPooling`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "StringPooling",
        configuration,
        fallback)

########################################


def MinimalRebuild(configuration, fallback=None):
    """
    Create ``MinimalRebuild`` property.

    Detect changes to C++ class definitions and recompile only affected
    source files.

    Compiler switch /Gm

    Can be overridden with configuration attribute
    ``vs_MinimalRebuild`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "MinimalRebuild",
        configuration,
        fallback)

########################################


def ExceptionHandling(configuration, fallback=None):
    """
    Create ``ExceptionHandling`` property.

    Calls destructors for automatic objects during a strack unwind caused
    by an exceptions being thrown.

    Compiler switches /EHsc, /EHa

    Can be overridden with configuration attribute
    ``vs_ExceptionHandling`` for the C compiler.

    * "No"
    * "/EHsc" / "Yes"
    * "/EHa" / "Yes with SEH" / "Yes with SEH Exceptions" / "SEH"
    * 0 through 2

    Note:
        A boolean on Visual Studio 2003, an enum on 2005/2008

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty or validators.VSBooleanProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_ExceptionHandling")
    if value is not None:
        fallback = value

    # Visual Studio 2003 only has "Yes" or "No"
    # So, convert the value into a boolean
    if configuration.ide is IDETypes.vs2003:

        # Is there a value?
        # Try the easy way first, is it a number, "Yes", "True"?
        try:
            fallback = string_to_bool(fallback)

        # Assume exceptions are requested
        except ValueError:
            fallback = True

        # Enable/Disable exceptions
        return VSBooleanProperty(
            "ExceptionHandling",
            fallback)

    # Visual Studio 2005, 2008 version uses enums

    # If a bool, use /EHsc if True
    if isinstance(fallback, bool):
        fallback = "Yes" if fallback else "No"

    # If none, turn off Exceptions
    if fallback is None:
        fallback = "No"

    return VSEnumProperty(
        "ExceptionHandling",
        fallback,
        ("No",
        ("/EHsc", "Yes"),
        ("/EHa", "Yes with SEH", "Yes with SEH Exceptions", "SEH")))

########################################


def BasicRuntimeChecks(configuration, fallback=None):
    """
    Create ``BasicRuntimeChecks`` property.

    Generate runtime code to verify the stack and uninitialized variables.

    Compiler switches /RTCs, /RTCu, /RTC1

    Can be overridden with configuration attribute
    ``vs_BasicRuntimeChecks`` for the C compiler.

    * "Default"
    * "/RTCs" / "Stack" / "Stack Frames"
    * "/RTCu" / "Uninitialzed" / "Uninitialized Variables"
    * "/RTCsu" / "/RTC1" / "Both"
    * 0 through 3

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_BasicRuntimeChecks")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "BasicRuntimeChecks",
        fallback,
        ("Default",
         ("/RTCs", "Stack", "Stack Frames"),
         ("/RTCu", "Uninitialzed", "Uninitialized Variables"),
         ("/RTCsu", "/RTC1", "Both")))

########################################


def SmallerTypeCheck(configuration, fallback=None):
    """
    Create ``SmallerTypeCheck`` property.

    Enable checking for conversion to smaller types, incompatible with
    any optimization type other than debug.

    Compiler switch /RTCc

    Can be overridden with configuration attribute
    ``vs_SmallerTypeCheck`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "SmallerTypeCheck",
        configuration,
        fallback)

########################################


def RuntimeLibrary(configuration, fallback=None):
    """
    Create ``RuntimeLibrary`` property.

    Select runtime standard library to link with this code module.

    Compiler switches /MT, /MTd, /MD, /MDd, /ML, /MLd

    Can be overridden with configuration attribute
    ``vs_RuntimeLibrary`` for the C compiler.

    * "/MT" / "Multi-Threaded"
    * "/MTd" / "Multi-Threaded Debug"
    * "/MD" / "Multi-Threaded DLL"
    * "/MDd" / "Multi-Threaded DLL Debug"
    * "/ML" / "Single-Threaded"
    * "/MLd" / "Single-Threaded Debug"
    * 0 through 5

    Note: The Single Threaded libraries are only available on Visual
        Studio 2003. If 2005 or 2008 is generated, the Multi-Threaded
        version is substituted.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_RuntimeLibrary")
    if value is not None:
        fallback = value

    enum_list = [
        ("/MT", "Multi-Threaded"),
        ("/MTd", "Multi-Threaded Debug"),
        ("/MD", "Multi-Threaded DLL"),
        ("/MDd", "Multi-Threaded DLL Debug")]

    # Visual Studio 2003 support single threaded libraries
    if configuration.ide is IDETypes.vs2003:
        enum_list.extend([
            ("/ML", "Single-Threaded"),
            ("/MLd", "Single-Threaded Debug")])
    else:
        # Perform substitution from single threaded
        # to multi-threaded
        sub_dict = {
            "/ML": "/MT",
            "Single-Threaded": "/MT",
            4: 2,
            "/MLd": "/MTd",
            "Single-Threaded Debug": "/MTd",
            5: 3
        }
        fallback = sub_dict.get(fallback, fallback)

    return VSEnumProperty(
        "RuntimeLibrary",
        fallback,
        enum_list)

########################################


def StructMemberAlignment(configuration, fallback=None):
    """
    Create ``StructMemberAlignment`` property.

    Set the default structure byte alignment.

    Compiler switches /Zp1, /Zp2, /Zp4, /Zp8, /Zp16

    Can be overridden with configuration attribute
    ``vs_StructMemberAlignment`` for the C compiler.

    * "Default"
    * "/Zp1" / "1" / "1 Byte"
    * "/Zp2" / "2" / "2 Bytes"
    * "/Zp4" / "4" / "4 Bytes"
    * "/Zp8" / "8" / "8 Bytes"
    * "/Zp16" / "16" / "16 Bytes"
    * 0 through 5

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_StructMemberAlignment")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "StructMemberAlignment",
        fallback,
        ("Default",
         ("/Zp1", "1", "1 Byte"),
         ("/Zp2", "2", "2 Bytes"),
         ("/Zp4", "4", "4 Bytes"),
         ("/Zp8", "8", "8 Bytes"),
         ("/Zp16", "16", "16 Bytes")))

########################################


def BufferSecurityCheck(configuration, fallback=None):
    """
    Create ``BufferSecurityCheck`` property.

    Check for buffer overruns; useful for closing hackable loopholes
    on internet servers; ignored for projects using managed extensions.

    Compiler switch /GS

    Can be overridden with configuration attribute
    ``vs_BufferSecurityCheck`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "BufferSecurityCheck",
        configuration,
        fallback)

########################################


def EnableFunctionLevelLinking(configuration, fallback=None):
    """
    Create ``EnableFunctionLevelLinking`` property.

    Enables function-level linking; required for Edit and Continue to work.

    Compiler switch /Gy

    Can be overridden with configuration attribute
    ``vs_EnableFunctionLevelLinking`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "EnableFunctionLevelLinking",
        configuration,
        fallback)

########################################


def EnableEnhancedInstructionSet(configuration, fallback=None):
    """
    Create ``EnableEnhancedInstructionSet`` property.

    Set the instruction set extensions allowed.

    Compiler switches /arch:SSE, /arch:SSE2

    Can be overridden with configuration attribute
    ``vs_EnableEnhancedInstructionSet`` for the C compiler.

    * "Default"
    * "/arch:SSE" / "SSE"
    * "/arch:SSE2" / "SSE2"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_EnableEnhancedInstructionSet")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "EnableEnhancedInstructionSet",
        fallback,
        ("Default",
        ("/arch:SSE", "SSE"),
        ("/arch:SSE2", "SSE2")))

########################################


def FloatingPointModel(configuration, fallback=None):
    """
    Create ``FloatingPointModel`` property.

    Set the allowable precision for floating point math for speed.

    Compiler switches /fp:precise, /fp:strict, /fp:fast

    Can be overridden with configuration attribute
    ``vs_FloatingPointModel`` for the C compiler.

    * "/fp:precise" / "Precise"
    * "/fp:strict" / "Strict"
    * "/fp:fast" / "Fast"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    # Only 2003
    if configuration.ide is IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_FloatingPointModel")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "FloatingPointModel",
        fallback,
        (("/fp:precise", "Precise"),
         ("/fp:strict", "Strict"),
         ("/fp:fast", "Fast")))

########################################


def FloatingPointExceptions(configuration, fallback=None):
    """
    Create ``FloatingPointExceptions`` property.

    Enable floating point exceptions when generating code.

    Compiler switch /fp:except

    Can be overridden with configuration attribute
    ``vs_FloatingPointExceptions`` for the C compiler.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # Only 2005/2008
    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "FloatingPointExceptions",
        configuration,
        fallback)

########################################


def DisableLanguageExtensions(configuration, fallback=None):
    """
    Create ``DisableLanguageExtensions`` property.

    Supresses or enables language extensions.

    Compiler switch /Za

    Can be overridden with configuration attribute
    ``vs_DisableLanguageExtensions`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "DisableLanguageExtensions",
        configuration,
        fallback)

########################################


def DefaultCharIsUnsigned(configuration, fallback=None):
    """
    Create ``DefaultCharIsUnsigned`` property.

    Sets the default char type to unsigned.

    Compiler switch /J

    Can be overridden with configuration attribute
    ``vs_DefaultCharIsUnsigned`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "DefaultCharIsUnsigned",
        configuration,
        fallback)

########################################


def TreatWChar_tAsBuiltInType(configuration, fallback=None):
    """
    Create ``TreatWChar_tAsBuiltInType`` property.

    Treats wchar_t as a built-in type.

    Compiler switch /Zc:wchar_t

    Can be overridden with configuration attribute
    ``vs_TreatWChar_tAsBuiltInType`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "TreatWChar_tAsBuiltInType",
        configuration,
        fallback)

########################################


def ForceConformanceInForLoopScope(configuration, fallback=None):
    """
    Create ``ForceConformanceInForLoopScope`` property.

    Forces the compiler to conform to the local scope in a for loop.

    Compiler switch /Zc:forScope

    Can be overridden with configuration attribute
    ``vs_ForceConformanceInForLoopScope`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "ForceConformanceInForLoopScope",
        configuration,
        fallback)

########################################


def RuntimeTypeInfo(configuration, fallback=None):
    """
    Create ``RuntimeTypeInfo`` property.

    Adds code for checking C++ object types at run time (runtime type
    information)

    Compiler switches /GR and /GR-

    Can be overridden with configuration attribute
    ``vs_RuntimeTypeInfo`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "RuntimeTypeInfo",
        configuration,
        fallback)

########################################


def OpenMP(configuration, fallback=None):
    """
    Create ``OpenMP`` property.

    Enable OpenMP language extensions.

    Compiler switch /openmp

    Can be overridden with configuration attribute
    ``vs_OpenMP`` for the C compiler.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # Only 2005/2008
    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "OpenMP",
        configuration,
        fallback)

########################################


def UsePrecompiledHeader(configuration, fallback=None):
    """
    Create ``UsePrecompiledHeader`` property.

    Enable use of a precompiled header.

    Compiler switches /Yc, /Yu, /YX

    Can be overridden with configuration attribute
    ``vs_UsePrecompiledHeader`` for the C compiler.

    * "No" / "Not using"
    * "/Yc" / "Create"
    * "/YX" / "Automatic" (Only 2003)
    * "/Yu" / "Use" (2 on 2005/2008, 3 on 2003)
    * 0 through 3

    Note:
        /YX is only available on Visual Studio 2003, on 2005/2008
        it is swapped with /Yu / "Use"

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_UsePrecompiledHeader")
    if value is not None:
        fallback = value

    # Create the list for 2005/2008
    enum_list = [
        ("No", "Not using"),
        ("/Yc", "Create"),
        ("/Yu", "Use")]

    # Visual Studio 2003 supports automatic generation
    if configuration.ide is IDETypes.vs2003:
        # Insert before "/Yu"
        enum_list.insert(-1, ("/YX", "Automatic"))
    else:
        # Remap /YX to /Yu
        if fallback in ("/YX", "Automatic", 3):
            fallback = 2

    return VSEnumProperty(
        "UsePrecompiledHeader",
        fallback,
        enum_list)

########################################


def PrecompiledHeaderThrough(configuration, fallback=None):
    """
    Create ``AdditionalOptions`` property.

    Text header file for precompilation

    Can be overridden with configuration attribute
    ``vs_PrecompiledHeaderThrough`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "PrecompiledHeaderThrough",
        configuration,
        fallback)

########################################


def PrecompiledHeaderFile(configuration, fallback=None):
    """
    Create ``AdditionalOptions`` property.

    Binary header file for precompilation

    Can be overridden with configuration attribute
    ``vs_PrecompiledHeaderFile`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "PrecompiledHeaderFile",
        configuration,
        fallback)

########################################


def ExpandAttributedSource(configuration, fallback=None):
    """
    Create ``ExpandAttributedSource`` property.

    Create listing file with expanded attributes injected into source file.

    Compiler switch /Fx

    Can be overridden with configuration attribute
    ``vs_ExpandAttributedSource`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "ExpandAttributedSource",
        configuration,
        fallback)

########################################


def AssemblerOutput(configuration, fallback=None):
    """
    Create ``AssemblerOutput`` property.

    Set the format of the assembly output

    Compiler switches /FA, /FAcs, /FAc, /FAs

    Can be overridden with configuration attribute
    ``vs_AssemblerOutput`` for the C compiler.

    * "No" / "No Listing"
    * "/FA" / "Assembly" / "Asm" / "Assembly-Only"
    * "/FAcs" / "Assembly, Machine Code and Source"
    * "/FAc" / "Assembly With Machine Code"
    * "/FAs" / "Assembly With Source"
    * 0 through 4

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_AssemblerOutput")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "AssemblerOutput",
        fallback,
        (("No", "No Listing"),
         ("/FA", "Assembly", "Asm", "Assembly-Only"),
         ("/FAcs", "Assembly, Machine Code and Source"),
         ("/FAc", "Assembly With Machine Code"),
         ("/FAs", "Assembly With Source")))

########################################


def AssemblerListingLocation(configuration, fallback=None):
    """
    Create ``AssemblerListingLocation`` property.

    Output location for .asm file

    Can be overridden with configuration attribute
    ``vs_AssemblerListingLocation`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "AssemblerListingLocation",
        configuration,
        fallback)

########################################


def ObjectFile(configuration, fallback=None):
    """
    Create ``ObjectFile`` property.

    Output location for .obj file

    Can be overridden with configuration attribute
    ``vs_ObjectFile`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "ObjectFile",
        configuration,
        fallback)

########################################


def ProgramDataBaseFileName(configuration, fallback=None):
    """
    Create ``ProgramDataBaseFileName`` property.

    Output location of shared .pdb file

    Can be overridden with configuration attribute
    ``vs_ProgramDataBaseFileName`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "ProgramDataBaseFileName",
        configuration,
        fallback)

########################################


def GenerateXMLDocumentationFiles(configuration, fallback=None):
    """
    Create ``GenerateXMLDocumentationFiles`` property.

    Specifies that the compiler should generate XML documentation comment
    files.

    Compiler switch /doc

    Can be overridden with configuration attribute
    ``vs_GenerateXMLDocumentationFiles`` for the C compiler.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # 2005/2008 only
    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "GenerateXMLDocumentationFiles",
        configuration,
        fallback)

########################################


def XMLDocumentationFileName(configuration, fallback=None):
    """
    Create ``XMLDocumentationFileName`` property.

    Name of the XML formatted documentation file.

    Can be overridden with configuration attribute
    ``vs_XMLDocumentationFileName`` for the C compiler.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       None or validators.VSStringProperty object.
    """

    # 2005/2008 only
    if configuration.ide is IDETypes.vs2003:
        return None

    return VSStringProperty.vs_validate(
        "XMLDocumentationFileName",
        configuration,
        fallback)

########################################


def BrowseInformation(configuration, fallback=None):
    """
    Create ``BrowseInformation`` property.

    What browser information to generate?

    Compiler switches /FR, /Fr

    Can be overridden with configuration attribute
    ``vs_BrowseInformation`` for the C compiler.

    * "None" / "No"
    * "/FR" / "All"
    * "/Fr" / "No Local Symbols" / "No Locals"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_BrowseInformation")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "BrowseInformation",
        fallback,
        (("None", "No"),
        ("/FR", "All"),
        ("/Fr", "No Local Symbols", "No Locals")))

########################################


def BrowseInformationFile(configuration, fallback=None):
    """
    Create ``BrowseInformationFile`` property.

    Name of the browsing file.

    Can be overridden with configuration attribute
    ``vs_BrowseInformationFile`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "BrowseInformationFile",
        configuration,
        fallback)

########################################


def WarningLevel(configuration, fallback=None):
    """
    Create ``WarningLevel`` property.

    Set the warning level.

    Compiler switches /W0, /W1, /W2, /W3, /W4

    Can be overridden with configuration attribute
    ``vs_WarningLevel`` for the C compiler.

    * "/W0" / "Off" / "No" / "None"
    * "/W1" / "Level 1"
    * "/W2" / "Level 2"
    * "/W3" / "Level 3"
    * "/W4" / "Level 4"
    * 0 through 4

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_WarningLevel")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "WarningLevel",
        fallback,
        (("/W0", "Off", "No", "None"),
        ("/W1", "Level 1"),
        ("/W2", "Level 2"),
        ("/W3", "Level 3"),
        ("/W4", "Level 4", "All")))

########################################


def WarnAsError(configuration, fallback=None):
    """
    Create ``WarnAsError`` property.

    Enables the compiler to treat all warnings as errors.

    Compiler switch /WX

    Can be overridden with configuration attribute
    ``vs_WarnAsError`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "WarnAsError",
        configuration,
        fallback)

########################################


def SuppressStartupBanner(configuration, fallback=None, prefix=None):
    """
    Create ``SuppressStartupBanner`` property.

    Suppress the display of the startup banner and information messages.

    Compiler switch /nologo

    Can be overridden with configuration attributes:

    * ``vs_SuppressStartupBanner`` for the C compiler.
    * ``vs_LinkerSuppressStartupBanner`` for the exe/lib linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use
        prefix: Prefix string for override

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "SuppressStartupBanner",
        configuration,
        fallback,
        prefix=prefix)

########################################


def Detect64BitPortabilityProblems(configuration, fallback=None):
    """
    Create ``Detect64BitPortabilityProblems`` property.

    Tells the compiler to check for 64-bit portability issues.

    Compiler switch /Wp64

    Can be overridden with configuration attribute
    ``vs_Detect64BitPortabilityProblems`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "Detect64BitPortabilityProblems",
        configuration,
        fallback)

########################################


def DebugInformationFormat(configuration, fallback=None):
    """
    Create ``DebugInformationFormat`` property.

    Sets the type of debugging information to embed in the obj file.

    Compiler switches /C7, /Zd, /Zi, /ZI

    Can be overridden with configuration attribute
    ``vs_DebugInformationFormat`` for the C compiler.

    * "Off" / "No" / "None" / "Disabled"
    * "/C7" / "C7 Compatible"
    * "/Zd" / "Line Numbers" / "Line Numbers Only"
    * "/Zi" / "Program Database"
    * "/ZI" / "Edit and Continue"
    * 0 through 4

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_DebugInformationFormat")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "DebugInformationFormat",
        fallback,
        (("Off", "No", "None", "Disabled"),
        ("/C7", "C7 Compatible"),
        # Hidden in 2005/2008 (maps to C7)
        ("/Zd", "Line Numbers", "Line Numbers Only"),
        ("/Zi", "Program Database"),
        ("/ZI", "Edit and Continue")))


########################################


def CallingConvention(configuration, fallback=None):
    """
    Create ``CallingConvention`` property.

    Sets the type of default calling convention to use. Usually only
    meaningful for X86.

    Compiler switches /Gd, /Gr, /Gz

    Can be overridden with configuration attribute
    ``vs_CallingConvention`` for the C compiler.

    * "/Gd" / "__cdecl"
    * "/Gr" / "__fastcall"
    * "/Gz" / "__stdcall"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_CallingConvention")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "CallingConvention",
        fallback,
        (("/Gd", "__cdecl"),
        ("/Gr", "__fastcall"),
        ("/Gz", "__stdcall")))

########################################


def CompileAs(configuration, fallback=None):
    """
    Create ``CompileAs`` property.

    Forces C or C++ compilation. Normally the file extension determines the
    choice of compiler.

    Compiler switches /TC, /TP

    Can be overridden with configuration attribute
    ``vs_CompileAs`` for the C compiler.

    * "No" / "Default"
    * "/TC" / "C"
    * "/TP" / "C++" / "CPP"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_CompileAs")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "CompileAs",
        fallback,
        (("No", "Default"),
        ("/TC", "C"),
        ("/TP", "C++", "CPP")))

########################################


def DisableSpecificWarnings(configuration, fallback=None):
    """
    Create ``DisableSpecificWarnings`` property.

    List of warnings to disable during C compilation

    Can be overridden with configuration attribute
    ``vs_DisableSpecificWarnings`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list(
        "vs_DisableSpecificWarnings")
    if value:
        fallback = value

    return VSStringListProperty(
        "DisableSpecificWarnings",
        fallback)

########################################


def ForcedIncludeFiles(configuration, fallback=None):
    """
    Create ``ForcedIncludeFiles`` property.

    List of header files to force including before compilation.

    Can be overridden with configuration attribute
    ``vs_ForcedIncludeFiles`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list(
        "vs_ForcedIncludeFiles")
    if value:
        fallback = value

    return VSStringListProperty(
        "ForcedIncludeFiles",
        fallback)

########################################


def ForcedUsingFiles(configuration, fallback=None):
    """
    Create ``ForcedUsingFiles`` property.

    List of header files to force using before compilation.

    Can be overridden with configuration attribute
    ``vs_ForcedUsingFiles`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list(
        "vs_ForcedUsingFiles")
    if value:
        fallback = value

    return VSStringListProperty(
        "ForcedUsingFiles",
        fallback)


########################################

def ShowIncludes(configuration, fallback=None):
    """
    Create ``ShowIncludes`` property.

    Generates a list of include files with compiler output.

    Compiler switch /showIncludes

    Can be overridden with configuration attribute
    ``vs_ShowIncludes`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "ShowIncludes",
        configuration,
        fallback)

########################################


def UndefinePreprocessorDefinitions(configuration, fallback=None):
    """
    Create ``UndefinePreprocessorDefinitions`` property.

    List of defines to remove from compilation

    Can be overridden with configuration attribute
    ``vs_UndefinePreprocessorDefinitions`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list(
        "vs_UndefinePreprocessorDefinitions")
    if value:
        fallback = value

    return VSStringListProperty(
        "UndefinePreprocessorDefinitions",
        fallback)

########################################


def UndefineAllPreprocessorDefinitions(configuration, fallback=None):
    """
    Create ``UndefineAllPreprocessorDefinitions`` property.

    Undefine all previously defined preprocessor values.

    Compiler switch /u

    Can be overridden with configuration attribute
    ``vs_UndefineAllPreprocessorDefinitions`` for the C compiler.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "UndefineAllPreprocessorDefinitions",
        configuration,
        fallback)

########################################


def UseFullPaths(configuration, fallback=None):
    """
    Create ``UseFullPaths`` property.

    Use full paths in diagnostic messages.

    Compiler switch /FC

    Can be overridden with configuration attribute
    ``vs_UseFullPaths`` for the C compiler.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # 2005/2008 only
    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "UseFullPaths",
        configuration,
        fallback)

########################################


def OmitDefaultLibName(configuration, fallback=None):
    """
    Create ``OmitDefaultLibName`` property.

    Do not include default library names in .obj files.

    Compiler switch /Zl

    Can be overridden with configuration attribute
    ``vs_OmitDefaultLibName`` for the C compiler.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # 2005/2008 only
    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "OmitDefaultLibName",
        configuration,
        fallback)

########################################


def ErrorReporting(configuration, fallback=None):
    """
    Create ``ErrorReporting`` property.

    Is error reporting queued or immediate?

    Compiler switches /errorReport:prompt, /errorReport:queue

    Can be overridden with configuration attribute
    ``vs_ErrorReporting`` for the C compiler.

    * "Default"
    * "/errorReport:prompt" / "Immediate"
    * "/errorReport:queue" / "Queue"
    * 0 through 2

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    # 2005/2008 only
    if configuration.ide is IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_ErrorReporting")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "ErrorReporting",
        fallback,
        ("Default",
        ("/errorReport:prompt", "Immediate", "Prompt"),
        ("/errorReport:queue", "Queue")))

########################################

# Entries usually found in VCCustomBuildTool

########################################


def Description(configuration, fallback=None, prefix=None):
    """
    Create ``Description`` property.

    Message to print in the console

    Can be overridden with configuration attributes:

    * ``vs_Description`` for CustomBuild
    * ``vs_PreBuildDescription`` for PreBuild
    * ``vs_PostBuildDescription`` for PostBuild
    * ``vs_PreLinkDescription`` for PreLink

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use
        prefix: Prefix string for override

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "Description",
        configuration,
        fallback,
        prefix=prefix)

########################################


def CommandLine(configuration, fallback=None, prefix=None):
    """
    Create ``CommandLine`` property.

    Batch file contents

    Can be overridden with configuration attributes:

    * ``vs_CommandLine`` for CustomBuild
    * ``vs_PreBuildCommandLine`` for PreBuild
    * ``vs_PostBuildCommandLine`` for PostBuild
    * ``vs_PreLinkCommandLine`` for PreLink

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use
        prefix: Prefix string for override

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "CommandLine",
        configuration,
        fallback,
        prefix=prefix)

########################################


def AdditionalDependencies(configuration, fallback=None, prefix=None):
    """
    Create ``AdditionalDependencies`` property.

    List of files this build object depends on. If custom build, it's a list
    of input files for the build script. If it's a linker, it's a list of
    library files to link into the final output.

    Can be overridden with configuration attributes:

    * ``vs_AdditionalDependencies`` for Linkers
    * ``vs_CustomAdditionalDependencies`` for CustomBuild

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use
        prefix: Prefix string for override

    Returns:
       validators.VSStringListProperty object.
    """

    # Insert the optional prefix
    new_key = "vs_"

    # Assume space for libraries
    separator = " "
    if prefix:
        new_key = new_key + prefix
        # Custom build separates with ';'
        separator = ";"
    new_key = new_key + "AdditionalDependencies"

    # Was there an override?
    value = configuration.get_chained_list(new_key)
    if value:
        fallback = value

    return VSStringListProperty(
        "AdditionalDependencies",
        fallback,
        separator=separator)

########################################


def Outputs(configuration, fallback=None):
    """
    Create ``Outputs`` property.

    List of files this custom build command generates

    Can be overridden with configuration attribute
    ``vs_Outputs`` for the custom builder.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list("vs_Outputs")
    if value:
        fallback = value

    return VSStringListProperty(
        "Outputs",
        fallback)

########################################

# Entries usually found in VCLinkerTool

########################################


def RegisterOutput(configuration, fallback=None):
    """
    Create ``RegisterOutput`` property.

    Specifies whether to register the primary output of this build to Windows.

    Can be overridden with configuration attribute
    ``vs_RegisterOutput`` for the Linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "RegisterOutput",
        configuration, fallback)

########################################


def PerUserRedirection(configuration, fallback=None):
    """
    Create ``PerUserRedirection`` property.

    When Register Output is enabled, Per-user redirection forces registry
    writes to HKEY_CLASSES_ROOT to be redirected to HKEY_CURRENT_USER

    Can be overridden with configuration attribute
    ``vs_PerUserRedirection`` for the Linker.

    Note:
        Not available on Visual Studio 2005 and earlier

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # VS2008 only
    if configuration.ide is not IDETypes.vs2008:
        return None

    return VSBooleanProperty.vs_validate(
        "PerUserRedirection",
        configuration,
        fallback)

########################################


def IgnoreImportLibrary(configuration, fallback=None):
    """
    Create ``IgnoreImportLibrary`` property.

    Specifies that the import library generated by this configuration should not
    be imported into dependent projects.

    Can be overridden with configuration attribute
    ``vs_IgnoreImportLibrary`` for the Linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "IgnoreImportLibrary",
        configuration,
        fallback)

########################################


def LinkLibraryDependencies(configuration, fallback=None):
    """
    Create ``LinkLibraryDependencies`` property.

    Specifies whether or not library outputs from project dependencies are
    automatically linked in.

    Can be overridden with configuration attribute
    ``vs_LinkLibraryDependencies`` for the Linker.

    Note:
        Not available on Visual Studio 2003 and earlier

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "LinkLibraryDependencies",
        configuration,
        fallback)

########################################


def UseLibraryDependencyInputs(configuration, fallback=None):
    """
    Create ``UseLibraryDependencyInputs`` property.

    Specifies whether or not the inputs to the librarian tool are used rather
    than the library file itself when linking in library outputs of project
    dependencies.

    Can be overridden with configuration attribute
    ``vs_UseLibraryDependencyInputs`` for the Linker.

    Note:
        Not available on Visual Studio 2003 and earlier

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "UseLibraryDependencyInputs",
        configuration,
        fallback)

########################################


def ShowProgress(configuration, fallback=None):
    """
    Create ``ShowProgress`` property.

    Show progress in linking?

    Compiler switches /VERBOSE, /VERBOSE:LIB

    Can be overridden with configuration attribute
    ``vs_ShowProgress`` for the linker.

    * "Default" / "No" / "None"
    * "/VERBOSE" / "All"
    * "/VERBOSE:LIB" / "Lib"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_ShowProgress")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "ShowProgress",
        fallback,
        (("Default", "No", "None"),
        ("/VERBOSE", "All"),
        ("/VERBOSE:LIB", "Lib")))

########################################


def OutputFile(configuration, fallback=None):
    """
    Create ``OutputFile`` property.

    Name of the output file

    Can be overridden with configuration attribute
    ``vs_OutputFile`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "OutputFile",
        configuration,
        fallback)

########################################


def Version(configuration, fallback=None):
    """
    Create ``Version`` property.

    Version string for linking

    Can be overridden with configuration attribute
    ``vs_Version`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "Version",
        configuration,
        fallback)

########################################


def LinkIncremental(configuration, fallback=None):
    """
    Create ``LinkIncremental`` property.

    Enable incremental linking.

    Compiler switches /INCREMENTAL:NO, /INCREMENTAL

    Can be overridden with configuration attribute
    ``vs_LinkIncremental`` for the linker.

    * "Default" / "No" / "None"
    * "/INCREMENTAL:NO" / "No"
    * "/INCREMENTAL" / "Yes"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_LinkIncremental")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "LinkIncremental",
        fallback,
        ("Default",
        ("/INCREMENTAL:NO", "No"),
        ("/INCREMENTAL", "Yes")))

########################################


def GenerateManifest(configuration, fallback=None):
    """
    Create ``GenerateManifest`` property.

    Specifies if the linker should always generate a manifest file.

    Can be overridden with configuration attribute
    ``vs_GenerateManifest`` for the Linker.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "GenerateManifest",
        configuration,
        fallback)

########################################


def ManifestFile(configuration, fallback=None):
    """
    Create ``ManifestFile`` property.

    Name of the manifest file.

    Can be overridden with configuration attribute
    ``vs_ManifestFile`` for the linker.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       None or validators.VSStringProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSStringProperty.vs_validate(
        "ManifestFile",
        configuration,
        fallback)

########################################


def AdditionalManifestDependencies(configuration, fallback=None):
    """
    Create ``AdditionalManifestDependencies`` property.

    List of manifests this one is dependent on

    Can be overridden with configuration attribute
    ``vs_AdditionalManifestDependencies`` for the custom builder.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       None or validators.VSStringListProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_chained_list("vs_AdditionalManifestDependencies")
    if value:
        fallback = value

    return VSStringListProperty(
        "AdditionalManifestDependencies",
        fallback)

########################################


def EnableUAC(configuration, fallback=None):
    """
    Create ``EnableUAC`` property.

    Specifies whether or not User Account Control is enabled.

    Note:
        Not available on Visual Studio 2003 or 2005

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use
            Returns:
        None or VSBooleanProperty object.
    """

    if configuration.ide is not IDETypes.vs2008:
        return None

    return VSBooleanProperty.vs_validate(
        "EnableUAC", configuration, fallback)

########################################


def UACExecutionLevel(configuration, fallback=None):
    """
    Create ``UACExecutionLevel`` property.

    Set the UAC level

    Compiler switches /MANIFESTUAC:level=asInvoker

    Can be overridden with configuration attribute
    ``vs_UACExecutionLevel`` for the linker.

    * "Default" / "asInvoker"
    * "highestAvailable"
    * "requireAdministrator"
    * 0 through 2

    Note:
        Not available on Visual Studio 2003 or 2005

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    if configuration.ide is not IDETypes.vs2008:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_UACExecutionLevel")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "UACExecutionLevel",
        fallback,
        (("asInvoker", "Default"),
        "highestAvailable",
        "requireAdministrator"))

########################################


def UACUIAccess(configuration, fallback=None):
    """
    Create ``UACUIAccess`` property.

    Specifies whether or not to bypass user interface protection levels for
    other windows on the desktop. Set this property to ``Yes`` only for
    accessability applications.

    Compiler switches /MANIFESTUAC:uiAccess=``true`` or
    /MANIFESTUAC:uiAccess=``false``

    Note:
        Not available on Visual Studio 2003 or 2005

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    if configuration.ide is not IDETypes.vs2008:
        return None

    return VSBooleanProperty.vs_validate(
        "UACUIAccess", configuration, fallback)

########################################


def IgnoreAllDefaultLibraries(configuration, fallback=None):
    """
    Create ``IgnoreAllDefaultLibraries`` property.

    Ignore all default libraries during linking.

    Compiler switch /NODEFAULTLIB

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "IgnoreAllDefaultLibraries", configuration, fallback)

########################################


def IgnoreDefaultLibraryNames(configuration, fallback=None):
    """
    Create ``IgnoreDefaultLibraryNames`` property.

    List of libraries to ignore

    Can be overridden with configuration attribute
    ``vs_IgnoreDefaultLibraryNames`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list("vs_IgnoreDefaultLibraryNames")
    if value:
        fallback = value

    return VSStringListProperty(
        "IgnoreDefaultLibraryNames",
        fallback)

########################################


def ModuleDefinitionFile(configuration, fallback=None):
    """
    Create ``ModuleDefinitionFile`` property.

    Name of the module definition file

    Can be overridden with configuration attribute
    ``vs_ModuleDefinitionFile`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "ModuleDefinitionFile", configuration, fallback)

########################################


def AddModuleNamesToAssembly(configuration, fallback=None):
    """
    Create ``AddModuleNamesToAssembly`` property.

    Add these modules to C# assembly

    Can be overridden with configuration attribute
    ``vs_AddModuleNamesToAssembly`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list("vs_AddModuleNamesToAssembly")
    if value:
        fallback = value

    return VSStringListProperty(
        "AddModuleNamesToAssembly",
        fallback)

########################################


def EmbedManagedResourceFile(configuration, fallback=None):
    """
    Create ``EmbedManagedResourceFile`` property.

    Embed the listed resource files.

    Can be overridden with configuration attribute
    ``vs_EmbedManagedResourceFile`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list("vs_EmbedManagedResourceFile")
    if value:
        fallback = value

    return VSStringListProperty(
        "EmbedManagedResourceFile",
        fallback)

########################################


def ForceSymbolReferences(configuration, fallback=None):
    """
    Create ``ForceSymbolReferences`` property.

    Force these symbols to be public

    Can be overridden with configuration attribute
    ``vs_ForceSymbolReferences`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list("vs_ForceSymbolReferences")
    if value:
        fallback = value

    return VSStringListProperty(
        "ForceSymbolReferences",
        fallback)

########################################


def DelayLoadDLLs(configuration, fallback=None):
    """
    Create ``DelayLoadDLLs`` property.

    Only load these DLLs if functions within are called.

    Can be overridden with configuration attribute
    ``vs_DelayLoadDLLs`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list("vs_DelayLoadDLLs")
    if value:
        fallback = value

    return VSStringListProperty(
        "DelayLoadDLLs",
        fallback)

########################################


def AssemblyLinkResource(configuration, fallback=None):
    """
    Create ``AssemblyLinkResource`` property.

    Link in these assemblies

    Can be overridden with configuration attribute
    ``vs_AssemblyLinkResource`` for the linker.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       None or validators.VSStringListProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_chained_list("vs_AssemblyLinkResource")
    if value:
        fallback = value

    return VSStringListProperty(
        "AssemblyLinkResource",
        fallback)

########################################


def MidlCommandFile(configuration, fallback=None):
    """
    Create ``MidlCommandFile`` property.

    Midl command file to execute.

    Can be overridden with configuration attribute
    ``vs_MidlCommandFile`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "MidlCommandFile", configuration, fallback)

########################################


def IgnoreEmbeddedIDL(configuration, fallback=None):
    """
    Create ``IgnoreEmbeddedIDL`` property.

    Ignore embedded .idlsym sections of object files.

    Compiler switch /IGNOREIDL

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """
    return VSBooleanProperty.vs_validate(
        "IgnoreEmbeddedIDL", configuration, fallback)

########################################


def MergedIDLBaseFileName(configuration, fallback=None):
    """
    Create ``MergedIDLBaseFileName`` property.

    Filename to contain the merged IDL file

    Can be overridden with configuration attribute
    ``vs_MergedIDLBaseFileName`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "MergedIDLBaseFileName", configuration, fallback)

########################################


def TypeLibraryFile(configuration, fallback=None):
    """
    Create ``TypeLibraryFile`` property.

    Name of the type library.

    Can be overridden with configuration attribute
    ``vs_TypeLibraryFile`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "TypeLibraryFile", configuration, fallback)

########################################


def TypeLibraryResourceID(configuration, fallback=None):
    """
    Create ``TypeLibraryResourceID`` property.

    ID number of the library resource

    Can be overridden with configuration attribute
    ``vs_TypeLibraryResourceID`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSIntegerProperty object.
    """

    return VSIntegerProperty.vs_validate(
        "TypeLibraryResourceID", configuration, fallback)

########################################


def GenerateDebugInformation(configuration, fallback=None):
    """
    Create ``GenerateDebugInformation`` property.

    Enables generation of debug information.

    Compiler switch /DEBUG

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "GenerateDebugInformation", configuration, fallback)

########################################


def AssemblyDebug(configuration, fallback=None):
    """
    Create ``AssemblyDebug`` property.

    Add debugging information in assembly

    Compiler switches /ASSEMBLYDEBUG, /ASSEMBLYDEBUG:DISABLE

    Can be overridden with configuration attribute
    ``vs_AssemblyDebug`` for the linker.

    * "No" / "None"
    * "/ASSEMBLYDEBUG" / "Runtime Tracking"
    * "/ASSEMBLYDEBUG:DISABLE" / "No Runtime Tracking"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_AssemblyDebug")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "AssemblyDebug",
        fallback,
        (("No", "None"),
        ("/ASSEMBLYDEBUG", "Runtime Tracking"),
        ("/ASSEMBLYDEBUG:DISABLE", "No Runtime Tracking")))

########################################


def ProgramDatabaseFile(configuration, fallback=None):
    """
    Create ``ProgramDatabaseFile`` property.

    Name of the program database file

    Can be overridden with configuration attribute
    ``vs_ProgramDatabaseFile`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "ProgramDatabaseFile", configuration, fallback)

########################################


def StripPrivateSymbols(configuration, fallback=None):
    """
    Create ``StripPrivateSymbols`` property.

    Do not put symbols in the named file

    Can be overridden with configuration attribute
    ``vs_StripPrivateSymbols`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "StripPrivateSymbols", configuration, fallback)

########################################


def GenerateMapFile(configuration, fallback=None):
    """
    Create ``GenerateMapFile`` property.

    Enables generation of map file during linking.

    Compiler switch /MAP

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "GenerateMapFile", configuration, fallback)

########################################


def MapFileName(configuration, fallback=None):
    """
    Create ``MapFileName`` property.

    Name of the symbol map file

    Can be overridden with configuration attribute
    ``vs_MapFileName`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "MapFileName", configuration, fallback)

########################################


def MapExports(configuration, fallback=None):
    """
    Create ``MapExports`` property.

    Includes exported functions in map file information.

    Compiler switch /MAPINFO:EXPORTS

    Can be overridden with configuration attribute
    ``vs_MapExports`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "MapExports", configuration, fallback)

########################################


def MapLines(configuration, fallback=None):
    """
    Create ``MapLines`` property.

    Includes source code line number information in map file.

    Compiler switch /MAPINFO:LINES

    Can be overridden with configuration attribute
    ``vs_MapLines`` for the linker.

    Note:
        Only available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    if configuration.ide is not IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "MapLines", configuration, fallback)

########################################


def SubSystem(configuration, fallback=None):
    """
    Create ``SubSystem`` property.

    Subsystem to link to.

    Compiler switches /SUBSYSTEM:CONSOLE, /SUBSYSTEM:WINDOWS

    Can be overridden with configuration attribute
    ``vs_AssemblyDebug`` for the linker.

    * "No" / "None"
    * "/SUBSYSTEM:CONSOLE" / "Console"
    * "/SUBSYSTEM:WINDOWS" / "Windows"
    * "/SUBSYSTEM:NATIVE" / "Native" 2005-2008
    * "/SUBSYSTEM:EFI_APPLICATION" / "EFI Application" 2005-2008
    * "/SUBSYSTEM:EFI_BOOT_SERVICE_DRIVER" / "EFI Boot Service Driver" 2005-2008
    * "/SUBSYSTEM:EFI_ROM" / "EFI ROM" 2005-2008
    * "/SUBSYSTEM:EFI_RUNTIME_DRIVER" / "EFI Runtime" 2005-2008
    * "/SUBSYSTEM:POSIX" / "Posix" 2005
    * "/SUBSYSTEM:WINDOWSCE" / "WindowsCE" 2005-2008
    * 0 through 2 2003, 10 - 2005, 9 - 2008

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_SubSystem")
    if value is not None:
        fallback = value

    enum_list = [
        ("No", "None"),
        ("/SUBSYSTEM:CONSOLE", "Console"),
        ("/SUBSYSTEM:WINDOWS", "Windows")
    ]

    if configuration.ide is not IDETypes.vs2003:
        enum_list.extend([
            ("/SUBSYSTEM:NATIVE", "Native"),
            ("/SUBSYSTEM:EFI_APPLICATION", "EFI Application"),
            ("/SUBSYSTEM:EFI_BOOT_SERVICE_DRIVER",
                "EFI Boot Service Driver"),
            ("/SUBSYSTEM:EFI_ROM", "EFI ROM"),
            ("/SUBSYSTEM:EFI_RUNTIME_DRIVER", "EFI Runtime"),
            ("/SUBSYSTEM:WINDOWSCE", "WindowsCE")
        ])

        # Only Visual Studio 2005 supported Posix
        if configuration.ide is IDETypes.vs2005:
            enum_list.insert(-1, ("/SUBSYSTEM:POSIX", "Posix"))

    return VSEnumProperty("SubSystem", fallback, enum_list)

########################################


def HeapReserveSize(configuration, fallback=None):
    """
    Create ``SubSystem`` property.

    Amount of heap to reserve

    Can be overridden with configuration attribute
    ``vs_HeapReserveSize`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSIntegerProperty object.
    """

    return VSIntegerProperty.vs_validate(
        "HeapReserveSize", configuration, fallback)

########################################


def HeapCommitSize(configuration, fallback=None):
    """
    Create ``SubSystem`` property.

    Amount of heap to commit

    Can be overridden with configuration attribute
    ``vs_HeapCommitSize`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSIntegerProperty object.
    """

    return VSIntegerProperty.vs_validate(
        "HeapCommitSize", configuration, fallback)

########################################


def StackReserveSize(configuration, fallback=None):
    """
    Create ``SubSystem`` property.

    Amount of stack to reserve

    Can be overridden with configuration attribute
    ``vs_StackReserveSize`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSIntegerProperty object.
    """

    return VSIntegerProperty.vs_validate(
        "StackReserveSize", configuration, fallback)

########################################


def StackCommitSize(configuration, fallback=None):
    """
    Create ``SubSystem`` property.

    Amount of stack to commit

    Can be overridden with configuration attribute
    ``vs_StackCommitSize`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSIntegerProperty object.
    """

    return VSIntegerProperty.vs_validate(
        "StackCommitSize", configuration, fallback)

########################################


def LargeAddressAware(configuration, fallback=None):
    """
    Create ``LargeAddressAware`` property.

    Notifies Windows the application is 32 bit clean.

    Compiler switches /LARGEADDRESSAWARE:NO, /LARGEADDRESSAWARE

    Can be overridden with configuration attribute
    ``vs_LargeAddressAware`` for the linker.

    * "Default"
    * "/LARGEADDRESSAWARE:NO" / "Disable"
    * "/LARGEADDRESSAWARE" / "Enable"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_LargeAddressAware")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "LargeAddressAware",
        fallback,
        ("Default",
         ("/LARGEADDRESSAWARE:NO", "Disable"),
         ("/LARGEADDRESSAWARE", "Enable")))

########################################


def TerminalServerAware(configuration, fallback=None):
    """
    Create ``TerminalServerAware`` property.

    Notify Windows that the application is aware of the Terminal Server.

    Compiler switches /TSAWARE:NO, /TSAWARE

    Can be overridden with configuration attribute
    ``vs_TerminalServerAware`` for the linker.

    * "Default"
    * "/TSAWARE:NO" / "Disable"
    * "/TSAWARE" / "Enable"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_TerminalServerAware")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "TerminalServerAware",
        fallback,
        ("Default",
         ("/TSAWARE:NO", "Disable"),
         ("/TSAWARE", "Enable")))


########################################

def SwapRunFromCD(configuration, fallback=None):
    """
    Create ``SwapRunFromCD`` property.

    Run application from the swap location of the CD.

    Compiler switch /SWAPRUN:CD

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "SwapRunFromCD", configuration, fallback)

########################################


def SwapRunFromNet(configuration, fallback=None):
    """
    Create ``SwapRunFromNet`` property.

    Run application from the swap location of the Net.

    Compiler switch /SWAPRUN:NET

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "SwapRunFromNet", configuration, fallback)

########################################


def Driver(configuration, fallback=None):
    """
    Create ``Driver`` property.

    Set the flags if this is a device driver.

    Compiler switches /DRIVER:NO, /DRIVER:UPONLY, /DRIVER:WDM

    Can be overridden with configuration attribute
    ``vs_Driver`` for the linker.

    * "No" / "Not Set"
    * "/DRIVER:NO" / "Driver"
    * "/DRIVER:UPONLY" / "UPONLY" / "Up Only"
    * "/DRIVER:WDM" / "WDM"
    * 0 through 3

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_Driver")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "Driver",
        fallback,
        (("No", "Not Set"),
        ("/DRIVER:NO", "Driver"),
        ("/DRIVER:UPONLY", "UPONLY", "Up Only"),
        ("/DRIVER:WDM", "WDM")))

########################################


def OptimizeReferences(configuration, fallback=None):
    """
    Create ``OptimizeReferences`` property.

    Remove unreferenced code

    Compiler switches /OPT:NOREF, /OPT:REF

    Can be overridden with configuration attribute
    ``vs_OptimizeReferences`` for the linker.

    * "Default"
    * "/OPT:NOREF" / "Disable"
    * "/OPT:REF" / "Enable"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_OptimizeReferences")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "OptimizeReferences",
        fallback,
        ("Default",
        ("/OPT:NOREF", "Disable"),
        ("/OPT:REF", "Enable")))

########################################


def EnableCOMDATFolding(configuration, fallback=None):
    """
    Create ``EnableCOMDATFolding`` property.

    Remove redundant COMDAT symbols

    Compiler switches /OPT:NOICF, /OPT:ICF

    Can be overridden with configuration attribute
    ``vs_EnableCOMDATFolding`` for the linker.

    * "Default"
    * "/OPT:NOICF" / "Disable"
    * "/OPT:ICF" / "Enable"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_EnableCOMDATFolding")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "EnableCOMDATFolding",
        fallback,
        ("Default",
        ("/OPT:NOREF", "Disable"),
        ("/OPT:REF", "Enable")))

########################################


def OptimizeForWindows98(configuration, fallback=None):
    """
    Create ``OptimizeForWindows98`` property.

    Align code on 4K boundaries for Windows 98

    Compiler switches /OPT:NOWIN98, /OPT:WIN98

    Can be overridden with configuration attribute
    ``vs_OptimizeForWindows98`` for the linker.

    * "Default"
    * "/OPT:NOWIN98" / "Disable"
    * "/OPT:WIN98" / "Enable"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_OptimizeForWindows98")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "OptimizeForWindows98",
        fallback,
        ("Default",
        ("/OPT:NOWIN98", "Disable"),
        ("/OPT:WIN98", "Enable")))

########################################


def FunctionOrder(configuration, fallback=None):
    """
    Create ``FunctionOrder`` property.

    Text file with function names to link in order.

    Can be overridden with configuration attribute
    ``vs_FunctionOrder`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "FunctionOrder",
        configuration,
        fallback)

########################################


def LinkTimeCodeGeneration(configuration, fallback=None):
    """
    Create ``LinkTimeCodeGeneration`` property.

    Link using link time code generation

    Compiler switches /ltcg, /ltcg:pginstrument

    Can be overridden with configuration attribute
    ``vs_LinkTimeCodeGeneration`` for the linker.

    * "Default"
    * "/ltcg" / "Enable"
    * "/ltcg:pginstrument" / "Instrument"
    * "/ltcg:pgoptimize" / "Optimize"
    * "/ltcg:pgupdate" / "Update"
    * 0 through 4

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_LinkTimeCodeGeneration")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "LinkTimeCodeGeneration",
        fallback,
        ("Default",
        ("/ltcg", "Enable"),
        ("/ltcg:pginstrument", "Instrument"),
        ("/ltcg:pgoptimize", "Optimize"),
        ("/ltcg:pgupdate", "Update")))

########################################


def ProfileGuidedDatabase(configuration, fallback=None):
    """
    Create ``ProfileGuidedDatabase`` property.

    Database file for profile based optimizations.

    Can be overridden with configuration attribute
    ``vs_ProfileGuidedDatabase`` for the linker.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       None or validators.VSStringProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSStringProperty.vs_validate(
        "ProfileGuidedDatabase",
        configuration,
        fallback)

########################################


def EntryPointSymbol(configuration, fallback=None):
    """
    Create ``EntryPointSymbol`` property.

    Code entry point symbol.

    Can be overridden with configuration attribute
    ``vs_EntryPointSymbol`` for tshe linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "EntryPointSymbol",
        configuration,
        fallback)

########################################


def ResourceOnlyDLL(configuration, fallback=None):
    """
    Create ``ResourceOnlyDLL`` property.

    Create DLL with no entry point; incompatible with setting the
    ``Entry Point`` option.

    Compiler switch /NOENTRY

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "ResourceOnlyDLL", configuration, fallback)

########################################


def SetChecksum(configuration, fallback=None):
    """
    Create ``SetChecksum`` property.

    Enables setting the checksum in the header of a .exe.

    Compiler switch /RELEASE

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "SetChecksum", configuration, fallback)

########################################


def BaseAddress(configuration, fallback=None):
    """
    Create ``BaseAddress`` property.

    Base address for execution.

    Can be overridden with configuration attribute
    ``vs_BaseAddress`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "BaseAddress", configuration, fallback)

########################################


def RandomizedBaseAddress(configuration, fallback=None):
    """
    Create ``RandomizedBaseAddress`` property.

    Enable base address randomization

    Compiler switches /DYNAMICBASE:NO, /DYNAMICBASE

    Can be overridden with configuration attribute
    ``vs_RandomizedBaseAddress`` for the linker.

    * "Default"
    * "/DYNAMICBASE:NO" / "Disable"
    * "/DYNAMICBASE" / "Enable"
    * 0 through 2

    Note:
        Not available on Visual Studio 2003 or 2005

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    if configuration.ide is not IDETypes.vs2008:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_RandomizedBaseAddress")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "RandomizedBaseAddress",
        fallback,
        ("Default",
         ("/DYNAMICBASE:NO", "Disable"),
         ("/DYNAMICBASE", "Enable")))

########################################


def FixedBaseAddress(configuration, fallback=None):
    """
    Create ``FixedBaseAddress`` property.

    Enable fixed address code generation

    Compiler switches /FIXED:NO, /FIXED

    Can be overridden with configuration attribute
    ``vs_FixedBaseAddress`` for the linker.

    * "Default"
    * "/FIXED:NO" / "Relocatable"
    * "/FIXED" / "Fixed"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_FixedBaseAddress")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "FixedBaseAddress",
        fallback,
        ("Default",
         ("/FIXED:NO", "Relocatable"),
         ("/FIXED", "Fixed")))

########################################


def DataExecutionPrevention(configuration, fallback=None):
    """
    Create ``DataExecutionPrevention`` property.

    Enable Data execution protection

    Compiler switches /NXCOMPAT:NO, /NXCOMPAT

    Can be overridden with configuration attribute
    ``vs_DataExecutionPrevention`` for the linker.

    * "Default"
    * "/NXCOMPAT:NO" / "Disable"
    * "/NXCOMPAT" / "Enable"
    * 0 through 2

    Note:
        Not available on Visual Studio 2003 or 2005

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    if configuration.ide is not IDETypes.vs2008:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_DataExecutionPrevention")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "DataExecutionPrevention",
        fallback,
        ("Default",
         ("/NXCOMPAT:NO", "Disable"),
         ("/NXCOMPAT", "Enable")))


########################################

def TurnOffAssemblyGeneration(configuration, fallback=None):
    """
    Create ``TurnOffAssemblyGeneration`` property.

    Specifies that no assembly will be generated even though common language
    runtime information is present in the object files.

    Compiler switch /NOASSEMBLY

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "TurnOffAssemblyGeneration", configuration, fallback)

########################################


def SupportUnloadOfDelayLoadedDLL(configuration, fallback=None):
    """
    Create ``SupportUnloadOfDelayLoadedDLL`` property.

    Specifies allowing explicit unloading of the delayed load DLLs.

    Compiler switch /DELAY:UNLOAD

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSBooleanProperty object.
    """

    return VSBooleanProperty.vs_validate(
        "SupportUnloadOfDelayLoadedDLL", configuration, fallback)

########################################


def ImportLibrary(configuration, fallback=None):
    """
    Create ``ImportLibrary`` property.

    Name of the import library to generate.

    Can be overridden with configuration attribute
    ``vs_ImportLibrary`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "ImportLibrary", configuration, fallback)

########################################


def MergeSections(configuration, fallback=None):
    """
    Create ``MergeSections`` property.

    Sections to merge on link.

    Can be overridden with configuration attribute
    ``vs_MergeSections`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringProperty object.
    """

    return VSStringProperty.vs_validate(
        "MergeSections", configuration, fallback)

########################################


def TargetMachine(configuration, fallback=None):
    """
    Create ``TargetMachine`` property.

    Target machine to build data for

    Compiler switches /MACHINE:X86, /MACHINE:X64

    Can be overridden with configuration attribute
    ``vs_TargetMachine`` for the linker.

    * "Default"
    * "/MACHINE:X86" / "Disable"
    * "/NXCOMPAT" / "Enable"
    * 0 through 2

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        validators.VSEnumProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_value("vs_TargetMachine")
    if value is not None:
        fallback = value

    enum_list = [
        ("Default", "Not Set"),
        ("/MACHINE:X86", "X86")
    ]

    # Visual Studio 2005 and 2008 support other CPUs
    if configuration.ide is not IDETypes.vs2003:
        enum_list.extend([
            ("/MACHINE:AM33", "AM33"),
            ("/MACHINE:ARM", "ARM"),
            ("/MACHINE:EBC", "EBC"),
            ("/MACHINE:IA64", "IA64"),
            ("/MACHINE:M32R", "M32R"),
            ("/MACHINE:MIPS", "MIPS"),
            ("/MACHINE:MIPS16", "MIPS16"),
            ("/MACHINE:MIPSFPU", "MIPSFPU"),
            ("/MACHINE:MIPSFPU16", "MIPSFPU16"),
            ("/MACHINE:MIPSR41XX", "MIPSR41XX"),
            ("/MACHINE:SH3", "SH3"),
            ("/MACHINE:SH3DSP", "SH3DSP"),
            ("/MACHINE:SH4", "SH4"),
            ("/MACHINE:SH5", "SH5"),
            ("/MACHINE:THUMB", "THUMB"),
            ("/MACHINE:X64", "X64")
        ])

    return VSEnumProperty(
        "TargetMachine",
        fallback,
        enum_list)

########################################


def KeyFile(configuration, fallback=None):
    """
    Create ``KeyFile`` property.

    File with key for signing.

    Can be overridden with configuration attribute
    ``vs_KeyFile`` for the linker.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       None or validators.VSStringProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSStringProperty.vs_validate(
        "KeyFile", configuration, fallback)

########################################


def KeyContainer(configuration, fallback=None):
    """
    Create ``KeyContainer`` property.

    Name of the container of the key.

    Can be overridden with configuration attribute
    ``vs_KeyContainer`` for the linker.

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       None or validators.VSStringProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSStringProperty.vs_validate(
        "KeyContainer", configuration, fallback)

########################################


def DelaySign(configuration, fallback=None):
    """
    Create ``DelaySign`` property.

    Indicates whether the output assembly should be delay signed.

    Compiler switch /DELAYSIGN

    Note:
        Only available on Visual Studio 2005 or higher

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "DelaySign", configuration, fallback)


########################################


def AllowIsolation(configuration, fallback=None):
    """
    Create ``AllowIsolation`` property.

    Specifies manifest file lookup behavior for side-by-side assemblies.

    Compiler switch /ALLOWISOLATION:NO

    Note:
        Only available on Visual Studio 2005 or higher

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "AllowIsolation", configuration, fallback)


########################################


def Profile(configuration, fallback=None):
    """
    Create ``Profile`` property.

    Produce an output file that can be used with the Enterprise Developer
    performance profiler.

    Compiler switch /PROFILE

    Note:
        Only available on Visual Studio 2005 or higher

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "Profile", configuration, fallback)

########################################


def CLRThreadAttribute(configuration, fallback=None):
    """
    Create ``CLRThreadAttribute`` property.

    CLR Thread attribute

    Compiler switches /CLRTHREADATTRIBUTE:MTA, /CLRTHREADATTRIBUTE:STA

    Can be overridden with configuration attribute
    ``vs_CLRThreadAttribute`` for the linker.

    * "Default"
    * "/CLRTHREADATTRIBUTE:MTA" / "MTA"
    * "/CLRTHREADATTRIBUTE:STA" / "STA"
    * 0 through 2

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    # 2005/2008 only
    if configuration.ide is IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_CLRThreadAttribute")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "CLRThreadAttribute",
        fallback,
        ("Default",
         ("/CLRTHREADATTRIBUTE:MTA", "MTA"),
         ("/CLRTHREADATTRIBUTE:STA", "STA")))

########################################


def CLRImageType(configuration, fallback=None):
    """
    Create ``CLRImageType`` property.

    CLR data image type

    Compiler switches /CLRIMAGETYPE:IJW, /CLRIMAGETYPE:PURE

    Can be overridden with configuration attribute
    ``vs_CLRImageType`` for the linker.

    * "Default"
    * "/CLRIMAGETYPE:IJW" / "IJW"
    * "/CLRIMAGETYPE:PURE" / "RelPureocatable"
    * "/CLRIMAGETYPE:SAFE" / "Safe"
    * 0 through 3

    Note:
        Not available on Visual Studio 2003

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSEnumProperty object.
    """

    # 2005/2008 only
    if configuration.ide is IDETypes.vs2003:
        return None

    # Was there an override?
    value = configuration.get_chained_value("vs_CLRImageType")
    if value is not None:
        fallback = value

    return VSEnumProperty(
        "CLRImageType",
        fallback,
        ("Default",
         ("/CLRIMAGETYPE:IJW", "IJW"),
         ("/CLRIMAGETYPE:PURE", "RelPureocatable"),
         ("/CLRIMAGETYPE:SAFE", "Safe")))


def CLRUnmanagedCodeCheck(configuration, fallback=None):
    """
    Create ``CLRUnmanagedCodeCheck`` property.

    Specifies whether the linker will apply
    SuppressUnmanagedCodeSecurityAttribute to linker-generated PInvoke calls.

    Compiler switch /CLRUNMANAGEDCODECHECK

    Note:
        Only available on Visual Studio 2005 or higher

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
        None or validators.VSBooleanProperty object.
    """

    # 2005/2008 only
    if configuration.ide is IDETypes.vs2003:
        return None

    return VSBooleanProperty.vs_validate(
        "CLRUnmanagedCodeCheck", configuration, fallback)


########################################


def ExportNamedFunctions(configuration, fallback=None):
    """
    Create ``ExportNamedFunctions`` property.

    Export these functions

    Can be overridden with configuration attribute
    ``vs_ExportNamedFunctions`` for the linker.

    Args:
        configuration: Project configuration to scan for overrides.
        fallback: Default value to use

    Returns:
       validators.VSStringListProperty object.
    """

    # Was there an override?
    value = configuration.get_chained_list(
        "vs_ExportNamedFunctions")
    if value:
        fallback = value

    return VSStringListProperty(
        "ExportNamedFunctions",
        fallback)


########################################


def do_filter_tree(xml_entry, filter_name, tree, groups):
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
        if filter_name == "":
            merged = item
        else:
            merged = filter_name + "\\" + item

        # Create the filter entry
        new_filter = VS2003Filter(item, xml_entry.project)
        xml_entry.add_element(new_filter)

        # See if this directory string creates a group?
        if merged in groups:
            # Found, add all the elements into this filter
            for fileitem in sorted(
                    groups[merged],
                    key=operator.attrgetter("vs_name")):
                new_filter.add_element(VS2003File(fileitem, xml_entry.project))

        tree_key = tree[item]
        # Recurse down the tree if there are sub entries
        if isinstance(tree_key, dict):
            do_filter_tree(new_filter, merged, tree_key, groups)

########################################


class VS2003XML():
    r"""
    Visual Studio 2003-2008 XML formatter.

    Output XML elements in the format of Visual Studio 2003-2008.

    Visual Studio 2003-2008 only supports XML tags and attributes.
    There is no support for text between tags.

    Theses are examples of XML fragments this class exports.

    ```xml
    <Platforms>
        <Platform
            Name="Win32"/>
    </Platforms>

    <Tool
        Name="VCMIDLTool"/>

    <-- force_pair disables support for "/>" closure -->
    <File
        RelativePath=".\\source\\Win32Console.cpp">
    </File>
    ```

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

    def add_attribute(self, attribute):
        """
        Add an attribute object.
        @details
        Append the passed attribute to the end of the attribute list
        for this XML element.

        Args:
            attribute: A validator class instance
        """

        # Test for None
        if attribute is not None:
            # Append the item to the list
            self.attributes.append(attribute)

    ########################################

    def add_attributes(self, attributes):
        """
        Add a list of attribute objects.
        @details
        Iterate over the list of attribute objects and append them
        to the end of the attribute list.

        Args:
            attributes: list of attribute objects.
        """

        # Test for None
        if attributes is not None:
            if not isinstance(attributes, list):
                self.add_attribute(attributes)
            else:
                # Update the list with the new entries
                for attribute in attributes:
                    self.add_attribute(attribute)

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
        @details
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

        # pylint: disable=too-many-branches

        # Create the default
        if line_list is None:
            line_list = []

        if ide is None:
            ide = IDETypes.vs2008

        # Determine the indentation
        # VS2003 uses tabs
        tabs = "\t" * indent

        # Special case, if no attributes, don't allow <foo/> XML
        # This is to duplicate the output of Visual Studio 2005-2008
        line_list.append("{0}<{1}".format(tabs, escape_xml_cdata(self.name)))

        attributes = []
        for item in self.attributes:
            value = item.get_value()
            if value is not None:
                attributes.append((item.name, value))

        elements = self.elements
        if attributes:

            # Output tag with attributes and support "/>" closing
            for attribute in attributes:
                value = attribute[1]

                # VS2003 has upper case booleans
                if ide is IDETypes.vs2003:
                    if value in ("true", "false"):
                        value = value.upper()

                # If the string has CR, VS2003 doesn't xml encode it,
                # so it's in the string literally
                # VS2005 and VS2008 use &#x0D;&#x0A;

                # Encode special characters
                value = escape_xml_attribute(value)

                # If there's a CR, it's &#10;, so convert it
                cr_fixup = "\n" if ide is IDETypes.vs2003 else "&#x0D;&#x0A;"
                value = value.replace("&#10;", cr_fixup)

                # Create the line (Might have line feeds)
                item = "{0}\t{1}=\"{2}\"".format(
                    tabs,
                    escape_xml_cdata(attribute[0]),
                    value)

                # Convert to line(s) and append
                # This only happens on VS2003, the others always have one line
                line_list.extend(item.split("\n"))

            # Check if /> closing is disabled
            force_pair = self.force_pair
            if not elements and not force_pair:
                # 2003 closes on the current line, which makes the xml
                # compact, where 2005 and 2008 are on the next line
                if ide is IDETypes.vs2003:
                    line_list[-1] = line_list[-1] + "/>"
                else:
                    line_list.append(tabs + "/>")
                return line_list

            # Close the open tag on the same line with 2003,
            # next line on 2005/2008
            if ide is IDETypes.vs2003:
                line_list[-1] = line_list[-1] + ">"
            else:
                line_list.append(tabs + "\t>")
        else:

            # No elements? Close on the same line
            line_list[-1] = line_list[-1] + ">"

        # Output the embedded elements
        for element in elements:
            element.generate(line_list, indent=indent + 1, ide=ide)

        # Close the current element
        line_list.append(tabs + "</" + escape_xml_cdata(self.name) + ">")
        return line_list

    def __repr__(self):
        """
        Convert the solution record into a human readable description

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
            self, "Tool", force_pair=force_pair)

        self.add_attribute(Name(name))

########################################


class VCGLSLTool(VS2003Tool):
    """
    Visual Studio 2005-2008 GLSL record.

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
        VS2003Tool.__init__(self, name="GLSL")

########################################


class VCHLSLTool(VS2003Tool):
    """
    Visual Studio 2005-2008 HLSL record.

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
        VS2003Tool.__init__(self, name="HLSL")

########################################


class VCMASMTool(VS2003Tool):
    """
    Visual Studio 2005-2008 MASM record.

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
        VS2003Tool.__init__(self, name="MASM")

########################################


class VCMASM64Tool(VS2003Tool):
    """
    Visual Studio 2005-2008 MASM64 record.

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
        VS2003Tool.__init__(self, name="MASM64")

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

        # pylint: disable=too-many-statements

        self.configuration = configuration

        # Set the tag
        VS2003Tool.__init__(self, name="VCCLCompilerTool")

        # Values needed for defaults
        optimization = configuration.optimization
        debug = configuration.debug
        project_type = configuration.project_type

        # Attributes are added in the same order they are written
        # in Visual Studio

        # Unicode response files (Only on 2005/2008)
        self.add_attribute(UseUnicodeResponseFiles(configuration))

        # List of custom compiler options as a single string
        self.add_attribute(AdditionalOptions(configuration))

        # Optimizations
        item = "Full Optimization" if optimization else "Disabled"
        self.add_attribute(Optimization(configuration, item))

        # Global optimizations (2003 only)
        self.add_attribute(
            GlobalOptimizations(configuration, optimization))

        # Inline functions
        item = "Any Suitable" if optimization else None
        self.add_attribute(InlineFunctionExpansion(configuration, item))

        # Enable intrinsics
        self.add_attribute(
            EnableIntrinsicFunctions(configuration, optimization))

        # True if floating point consistency is important (2003 only)
        self.add_attribute(ImproveFloatingPointConsistency(configuration))

        # Size or speed?
        self.add_attribute(FavorSizeOrSpeed(configuration, "Favor Fast Code"))

        # Get rid of stack frame pointers for speed
        self.add_attribute(
            OmitFramePointers(configuration, optimization))

        # Enable memory optimizations for fibers
        self.add_attribute(
            EnableFiberSafeOptimizations(configuration, optimization))

        # Build for Pentium, Pro, P4
        self.add_attribute(
            OptimizeForProcessor(configuration, "Pentium 4"))

        # Optimize for Windows Applications
        # Default to True because it's the 21st century.
        self.add_attribute(
            OptimizeForWindowsApplication(configuration, True))

        # Enable cross function optimizations
        self.add_attribute(
            WholeProgramOptimization2003(
                configuration,
                configuration.link_time_code_generation))

        # Get the header includes
        item = configuration.get_unique_chained_list(
            "_source_include_list")
        item.extend(configuration.get_unique_chained_list(
            "include_folders_list"))
        self.add_attribute(
            AdditionalIncludeDirectories(configuration, item))

        # Directory for #using includes
        self.add_attribute(
            AdditionalUsingDirectories(configuration))

        # Get the defines
        item = configuration.get_chained_list("define_list")
        self.add_attribute(
            PreprocessorDefinitions(configuration, item))

        # Ignore standard include path if true
        self.add_attribute(IgnoreStandardIncludePath(configuration))

        # Create a preprocessed file
        self.add_attribute(GeneratePreprocessedFile(configuration))

        # Keep comments in a preprocessed file
        self.add_attribute(KeepComments(configuration))

        # Pool all constant strings
        self.add_attribute(StringPooling(configuration, True))

        # Enable code analysis for minimal rebuild
        self.add_attribute(MinimalRebuild(configuration))

        # Set up exceptions
        self.add_attribute(
            ExceptionHandling(
                configuration,
                configuration.exceptions))

        # Runtime checks (Only valid if no optimizations)
        item = None if optimization else "Both"
        self.add_attribute(BasicRuntimeChecks(configuration, item))

        # Test for data size shrinkage (Only valid if no optimizations)
        self.add_attribute(SmallerTypeCheck(configuration))

        # Which run time library to use?
        item = "Multi-Threaded Debug" if debug else "Multi-Threaded"
        self.add_attribute(RuntimeLibrary(configuration, item))

        # Structure alignment
        self.add_attribute(StructMemberAlignment(configuration, "8 Bytes"))

        # Check for buffer overrun
        self.add_attribute(BufferSecurityCheck(configuration, bool(debug)))

        # Function level linking
        self.add_attribute(EnableFunctionLevelLinking(configuration, True))

        # Enhanced instruction set
        self.add_attribute(EnableEnhancedInstructionSet(configuration))

        # Floating point precision (2005/2008 only)
        self.add_attribute(FloatingPointModel(configuration, "Fast"))

        # Floating point exception support (2005/2008 only)
        self.add_attribute(FloatingPointExceptions(configuration))

        # Enable Microsoft specific extensions
        self.add_attribute(DisableLanguageExtensions(configuration))

        # "char" is unsigned
        self.add_attribute(DefaultCharIsUnsigned(configuration))

        # Enable wchar_t
        self.add_attribute(TreatWChar_tAsBuiltInType(configuration, True))

        # for (int i) "i" stays in the loop
        self.add_attribute(ForceConformanceInForLoopScope(configuration))

        # Enable run time type info
        self.add_attribute(RuntimeTypeInfo(configuration, False))

        # OpenMP support (2005/2008 only)
        self.add_attribute(OpenMP(configuration))

        # Enable precompiled headers
        self.add_attribute(UsePrecompiledHeader(configuration))

        # Text header file for precompilation
        self.add_attribute(PrecompiledHeaderThrough(configuration))

        # Binary header file for precompilation
        self.add_attribute(PrecompiledHeaderFile(configuration))

        # Add extended attributes to .asm output
        self.add_attribute(ExpandAttributedSource(configuration))

        # Format of the assembly output
        self.add_attribute(AssemblerOutput(configuration))

        # Output location for .asm file
        self.add_attribute(AssemblerListingLocation(configuration))

        # Output location for .obj file
        self.add_attribute(ObjectFile(configuration))

        # Output location of shared .pdb file
        self.add_attribute(ProgramDataBaseFileName(configuration,
            "\"$(OutDir)$(TargetName).pdb\""))

        # Generate XML formatted documentation (2005/2008 only)
        self.add_attribute(GenerateXMLDocumentationFiles(configuration))

        # Name of the XML formatted documentation file (2005/2008 only)
        self.add_attribute(XMLDocumentationFileName(configuration))

        # Type of source browsing information
        self.add_attribute(BrowseInformation(configuration))

        # Name of the browsing file
        self.add_attribute(BrowseInformationFile(configuration))

        # Warning level
        self.add_attribute(WarningLevel(configuration, "All"))

        # Warnings are errors
        self.add_attribute(WarnAsError(configuration))

        # Don't show startup banner
        self.add_attribute(SuppressStartupBanner(configuration))

        # Warnings for 64 bit code issues
        self.add_attribute(Detect64BitPortabilityProblems(configuration))

        # Debug information type
        item = "/C7" if debug or project_type.is_library() else None
        self.add_attribute(DebugInformationFormat(configuration, item))

        # Code calling convention
        item = "__fastcall" if configuration.fastcall else None
        self.add_attribute(CallingConvention(configuration, item))

        # C or C++
        self.add_attribute(CompileAs(configuration))

        # Disable these warnings
        self.add_attribute(DisableSpecificWarnings(configuration, ["4201"]))

        # List of include files to force inclusion
        self.add_attribute(ForcedIncludeFiles(configuration))

        # List of using files to force inclusion
        self.add_attribute(ForcedUsingFiles(configuration))

        # Show include file list
        self.add_attribute(ShowIncludes(configuration))

        # List of defines to remove
        self.add_attribute(UndefinePreprocessorDefinitions(configuration))

        # Remove all compiler definitions
        self.add_attribute(UndefineAllPreprocessorDefinitions(configuration))

        # Use full pathnames in error messages (2005/2008 only)
        self.add_attribute(UseFullPaths(configuration))

        # Remove default library names (2005/2008 only)
        self.add_attribute(OmitDefaultLibName(configuration))

        # Error reporting style (2005/2008 only)
        self.add_attribute(ErrorReporting(configuration))

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
        VS2003Tool.__init__(self, name="VCCLCompilerTool")

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

        VS2003Tool.__init__(self, name="VCCustomBuildTool")

        # Describe the build step
        self.add_attribute(Description(configuration))

        # Command line to perform the build
        self.add_attribute(CommandLine(configuration))

        # List of files this step depends on
        self.add_attribute(
            AdditionalDependencies(configuration, prefix="Custom"))

        # List of files created by this build step
        self.add_attribute(Outputs(configuration))


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

        VS2003Tool.__init__(self, "VCLinkerTool")

        # Values needed for defaults
        ide = configuration.ide
        optimization = configuration.optimization
        project_type = configuration.project_type
        link_time_code_generation = configuration.link_time_code_generation

        # Register the output on completion
        self.add_attribute(RegisterOutput(configuration))

        # Register per user instead of for everyone
        self.add_attribute(PerUserRedirection(configuration))

        # Don't allow this library generated be imported by dependent projects
        self.add_attribute(IgnoreImportLibrary(configuration))

        # Link in libraries from dependent projects
        self.add_attribute(LinkLibraryDependencies(configuration))

        # Use the librarian for input
        self.add_attribute(UseLibraryDependencyInputs(configuration))

        # Unicode response files (Only on 2005/2008)
        self.add_attribute(UseUnicodeResponseFiles(configuration, "Linker"))

        # Additional commands
        self.add_attribute(AdditionalOptions(configuration, prefix="Linker"))

        # Additional libraries
        default = configuration.get_unique_chained_list(
            "libraries_list")

        # Check if the MFC library is already present
        # This is a hack since if this library is not first, it will cause
        # link errors
        if configuration.use_mfc:
            for item in default:
                temp = item.lower()
                if temp in ("nafxcw.lib", "nafxcwd.lib"):
                    break
            else:
                # Insert the library first
                item = "nafxcwd.lib" if configuration.debug else "nafxcw.lib"
                default.insert(0, item)

        self.add_attribute(AdditionalDependencies(configuration, default))

        # Show progress in linking
        self.add_attribute(ShowProgress(configuration))

        # Output file name
        # Don't use $(TargetExt)
        item = "\"$(OutDir){}{}.exe\"".format(
            configuration.project.name,
            configuration.get_suffix())
        self.add_attribute(OutputFile(configuration, item))

        # Version number
        self.add_attribute(Version(configuration))

        # Enable incremental linking
        self.add_attribute(LinkIncremental(configuration))

        # Turn off startup banner
        self.add_attribute(
            SuppressStartupBanner(configuration, prefix="Linker"))

        # Library folders
        item = configuration.get_unique_chained_list("library_folders_list")
        self.add_attribute(
            VSStringListProperty(
                "AdditionalLibraryDirectories",
                item,
                slashes="\\"))

        # Generate a manifest file (2005/2008 only)
        self.add_attribute(GenerateManifest(configuration))

        # Name of the manifest file (2005/2008 only)
        self.add_attribute(ManifestFile(configuration))

        # Manifests this one is dependent on (2005/2008 only)
        self.add_attribute(
            AdditionalManifestDependencies(configuration))

        # Enable User Access Control
        self.add_attribute(EnableUAC(configuration))

        # Set the UAC Execution level
        self.add_attribute(UACExecutionLevel(configuration))

        # Enable UI bypass for User Access Control
        self.add_attribute(UACUIAccess(configuration))

        # Ignore default libraries
        self.add_attribute(IgnoreAllDefaultLibraries(configuration))

        # Ignore these libraries
        self.add_attribute(IgnoreDefaultLibraryNames(configuration))

        # Module definition file, if one exists
        self.add_attribute(ModuleDefinitionFile(configuration))

        # Add these modules to the C# assembly
        self.add_attribute(AddModuleNamesToAssembly(configuration))

        # Embed these resource fildes
        self.add_attribute(EmbedManagedResourceFile(configuration))

        # Force these symbols
        self.add_attribute(ForceSymbolReferences(configuration))

        # Load these DLLs only when called.
        self.add_attribute(DelayLoadDLLs(configuration))

        # Link in these assemblies (2005/2008 only)
        self.add_attribute(AssemblyLinkResource(configuration))

        # Contents of a Midl comment file (Actual commands)
        self.add_attribute(MidlCommandFile(configuration))

        # Ignore embedded .idlsym sections
        self.add_attribute(IgnoreEmbeddedIDL(configuration))

        # Filename the contains the contents of the merged idl
        self.add_attribute(MergedIDLBaseFileName(configuration))

        # Name of the type library
        self.add_attribute(TypeLibraryFile(configuration))

        # ID number of the library resource
        self.add_attribute(TypeLibraryResourceID(configuration))

        # Generate debugging information
        self.add_attribute(
            GenerateDebugInformation(configuration, bool(configuration.debug)))

        # Add debugging information in assembly
        self.add_attribute(AssemblyDebug(configuration))

        # Name of the program database file
        self.add_attribute(
            ProgramDatabaseFile(
                configuration, "\"$(OutDir)$(TargetName).pdb\""))

        # Do not put private symboles in this program database file
        self.add_attribute(StripPrivateSymbols(configuration))

        # Generate the map file
        self.add_attribute(GenerateMapFile(configuration))

        # Name of the map file
        self.add_attribute(MapFileName(configuration))

        # Include exported symbols in the map file
        self.add_attribute(MapExports(configuration))

        # Include source code line numbers in the map file
        self.add_attribute(MapLines(configuration))

        # Subsystem to link to
        item = "Console" if project_type is ProjectTypes.tool else "Windows"
        self.add_attribute(SubSystem(configuration, item))

        # Amount of heap to reserve
        self.add_attribute(HeapReserveSize(configuration))

        # Amount of heap to commit
        self.add_attribute(HeapCommitSize(configuration))

        # Amount of stack to reserve
        self.add_attribute(StackReserveSize(configuration))

        # Amount of stack to commit
        self.add_attribute(StackCommitSize(configuration))

        # Large address space aware?
        self.add_attribute(LargeAddressAware(configuration))

        # Terminal server aware?
        self.add_attribute(TerminalServerAware(configuration))

        # Run the file from swap location on CD
        self.add_attribute(SwapRunFromCD(configuration))

        # Run the file from swap location for network
        self.add_attribute(SwapRunFromNet(configuration))

        # Device driver?
        self.add_attribute(Driver(configuration))

        # Remove unreferenced code
        self.add_attribute(OptimizeReferences(configuration, "Enable"))

        # Remove redundant COMDAT symbols
        item = "Enable" if optimization else None
        self.add_attribute(EnableCOMDATFolding(configuration, item))

        # Align code on 4K boundaries for Windows 98
        self.add_attribute(OptimizeForWindows98(configuration))

        # Name of file containing the function link order
        self.add_attribute(FunctionOrder(configuration))

        # Link using link time code generation
        item = "Enable" if link_time_code_generation else None
        self.add_attribute(LinkTimeCodeGeneration(configuration, item))

        # Database file for profile based optimizations
        self.add_attribute(ProfileGuidedDatabase(configuration))

        # Code entry point symbol
        self.add_attribute(EntryPointSymbol(configuration))

        # No entry point (Resource only DLL)
        self.add_attribute(ResourceOnlyDLL(configuration))

        # Create a checksum in the header of the exe file
        self.add_attribute(SetChecksum(configuration))

        # Base address for execution
        self.add_attribute(BaseAddress(configuration))

        # Enable base address randomization
        self.add_attribute(RandomizedBaseAddress(configuration))

        # Enable fixed address code generation
        if ide is IDETypes.vs2008:
            self.add_attribute(FixedBaseAddress(configuration))

        # Enable Data execution protection
        self.add_attribute(DataExecutionPrevention(configuration))

        # Don't output assembly for C#
        self.add_attribute(TurnOffAssemblyGeneration(configuration))

        # Disable unloading of delayed load DLLs
        self.add_attribute(SupportUnloadOfDelayLoadedDLL(configuration))

        # Name of the import library to generate
        self.add_attribute(ImportLibrary(configuration))

        # Sections to merge on link
        self.add_attribute(MergeSections(configuration))

        # Target machine to build data for.
        self.add_attribute(TargetMachine(configuration))

        # This is a duplication of what is in 2008 for sorting
        if ide is not IDETypes.vs2008:
            self.add_attribute(FixedBaseAddress(configuration))

        # File with key for signing
        self.add_attribute(KeyFile(configuration))

        # Name of the container of the key
        self.add_attribute(KeyContainer(configuration))

        # Output should be delay signed
        self.add_attribute(DelaySign(configuration))

        # Allow assemblies to be isolated in the manifest
        self.add_attribute(AllowIsolation(configuration))

        # Enable profiling
        self.add_attribute(Profile(configuration))

        # CLR Thread attribute
        self.add_attribute(CLRThreadAttribute(configuration))

        # CLR data image type
        self.add_attribute(CLRImageType(configuration))

        # Error reporting
        self.add_attribute(ErrorReporting(configuration))

        # Check for unmanaged code
        self.add_attribute(CLRUnmanagedCodeCheck(configuration))

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

        VS2003Tool.__init__(self, "VCLibrarianTool")

        # Unicode response files (Only on 2005/2008)
        self.add_attribute(UseUnicodeResponseFiles(configuration, "Linker"))

        # Link in library dependencies
        self.add_attribute(LinkLibraryDependencies(configuration))

        # Additional command lines
        self.add_attribute(AdditionalOptions(configuration, prefix="Linker"))

        # Libaries to link in
        self.add_attribute(AdditionalDependencies(configuration))

        # Name of the output file
        # Don't use $(TargetExt)
        default = "\"$(OutDir){}{}.lib\"".format(
            configuration.project.name,
            configuration.get_suffix())
        self.add_attribute(OutputFile(configuration, default))

        # Library folders
        default = configuration.get_unique_chained_list("library_folders_list")
        self.add_attribute(
            VSStringListProperty(
                "AdditionalLibraryDirectories",
                default,
                slashes="\\"))

        # Suppress the startup banner
        self.add_attribute(
            SuppressStartupBanner(configuration, prefix="Linker"))

        # Name of the module file name
        self.add_attribute(ModuleDefinitionFile(configuration))

        # Ignore the default libraries
        self.add_attribute(IgnoreAllDefaultLibraries(configuration))

        # Ignore these libraries
        self.add_attribute(IgnoreDefaultLibraryNames(configuration))

        # Export these functions
        self.add_attribute(ExportNamedFunctions(configuration))

        # Force linking to these symbols
        self.add_attribute(ForceSymbolReferences(configuration))


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
        VS2003Tool.__init__(self, "VCMIDLTool")

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
        VS2003Tool.__init__(self, "VCALinkTool")


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
        VS2003Tool.__init__(self, "VCManifestTool")


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
        VS2003Tool.__init__(self, "VCXDCMakeTool")

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
        VS2003Tool.__init__(self, "VCBscMakeTool")

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
        VS2003Tool.__init__(self, "VCFxCopTool")

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
        VS2003Tool.__init__(self, "VCAppVerifierTool")

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
        VS2003Tool.__init__(self, "VCManagedResourceCompilerTool")

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

        VS2003Tool.__init__(self, "VCPostBuildEventTool")

        vs_description, vs_cmd = create_deploy_script(configuration)

        # Message to print in the console
        self.add_attribute(
            Description(
                configuration,
                vs_description,
                prefix="PostBuild"))

        # Batch file contents
        self.add_attribute(
            CommandLine(
                configuration,
                vs_cmd,
                prefix="PostBuild"))

        # Ignore from build
        self.add_attribute(ExcludedFromBuild())


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
        VS2003Tool.__init__(self, "VCPreBuildEventTool")

        # Message to print in the console
        self.add_attribute(Description(configuration, prefix="PreBuild"))

        # Batch file contents
        self.add_attribute(CommandLine(configuration, prefix="PreBuild"))

        # Ignore from build
        self.add_attribute(ExcludedFromBuild())


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

        VS2003Tool.__init__(self, "VCPreLinkEventTool")

        # Message to print in the console
        self.add_attribute(Description(configuration, prefix="PreLink"))

        # Batch file contents
        self.add_attribute(CommandLine(configuration, prefix="PreLink"))

        # Ignore from build
        self.add_attribute(ExcludedFromBuild())

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

        VS2003Tool.__init__(self, "VCResourceCompilerTool")

        # Language
        self.add_attribute(VSStringProperty("Culture", "1033"))

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
        VS2003Tool.__init__(self, "XboxDeploymentTool")

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
        VS2003Tool.__init__(self, "XboxImageTool")

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
        VS2003Tool.__init__(self, "VCWebServiceProxyGeneratorTool")

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

        VS2003Tool.__init__(self, "VCXMLDataGeneratorTool")

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
        VS2003Tool.__init__(self, "VCWebDeploymentTool")

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
        VS2003Tool.__init__(self, "VCManagedWrapperGeneratorTool")

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
        VS2003Tool.__init__(self, "VCAuxiliaryManagedWrapperGeneratorTool")


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
        VS2003XML.__init__(self, "Platform")

        # Only one entry, the target platform
        self.add_attribute(Name(platform.get_vs_platform()[0]))

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
        VS2003XML.__init__(self, "Platforms")

        # Get the list of platforms
        platforms = set()
        for configuration in project.configuration_list:
            platforms.add(configuration.platform)

        # Sort function
        def key_test(x):
            return x.get_vs_platform()[0]

        # Add the sorted records
        for platform in sorted(platforms, key=key_test):
            self.add_element(VS2003Platform(platform))

########################################


class VS2003ToolFile(VS2003XML):
    """
    Visual Studio 2005-2008 Tool record
    """

    def __init__(self, rules, project):
        """
        Set the defaults.
        """

        # Is the file local to the project? If so, declare as a ToolFile,
        # otherwise it's a rules file found in the IDE's folders
        rule_path = os.path.join(
            project.working_directory, rules.replace("\\", os.sep))
        item = "ToolFile" if os.path.isfile(rule_path) else "DefaultToolFile"
        VS2003XML.__init__(self, item)

        # Is this a RelativePath or FileName object?
        self.add_attribute(get_path_property(project.ide, rules))

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
        VS2003XML.__init__(self, "ToolFiles")

        for rules in project.vs_rules:
            rules = convert_to_windows_slashes(rules)
            self.add_element(VS2003ToolFile(rules, project))


########################################


class VS2003Configuration(VS2003XML):
    """
    Visual Studio 2003-2008 Configuration record

    Attributes:
        configuration: Parent configuration
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, configuration):
        """
        Init defaults.

        Args:
            configuration: Configuration record to extract defaults.
        """

        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        self.configuration = configuration
        VS2003XML.__init__(self, "Configuration")

        ide = configuration.ide
        platform = configuration.platform
        project_type = configuration.project_type

        # Add attributes

        # Name of the configuration
        self.add_attribute(Name(configuration.vs_configuration_name))

        # Set the output directory for final binaries
        self.add_attribute(OutputDirectory(configuration, "$(ProjectDir)bin"))

        # Set the directory for temp files
        item = "$(ProjectDir)temp\\" + configuration.project.name + \
            configuration.get_suffix()
        self.add_attribute(IntermediateDirectory(configuration, item))

        # Set the configuration type
        self.add_attribute(ConfigurationType(configuration))

        # Enable/disable MFC
        self.add_attribute(UseOfMFC(configuration, configuration.use_mfc))

        # Enable/disable ATL
        self.add_attribute(UseOfATL(configuration, configuration.use_atl))

        # Enable/disable ATL linkage at runtime (2003/2005 only)
        self.add_attribute(ATLMinimizesCRunTimeLibraryUsage(configuration))

        # Set whether it's ASCII or Unicode compilation
        self.add_attribute(CharacterSet(configuration))

        # Is CLR support enabled?
        self.add_attribute(
            ManagedExtensions(configuration, configuration.clr_support))

        # List of file extensions to delete on clean
        self.add_attribute(DeleteExtensionsOnClean(configuration))

        # Enable link time code generation
        self.add_attribute(
            WholeProgramOptimization(
                configuration,
                configuration.link_time_code_generation))

        # Paths for file references (2003 only)
        self.add_attribute(ReferencesPath(configuration))

        # The data chunks are in different orders on 2003 vs
        # 2005/2008, so break it into two paths
        if ide is IDETypes.vs2003:
            self.add_element(VCCLCompilerTool(configuration))
            self.add_element(VCCustomBuildTool(configuration))

            if project_type.is_library():
                self.add_element(VCLibrarianTool(configuration))
            else:
                self.add_element(VCLinkerTool(configuration))

            if platform.is_windows():
                self.add_element(VCMIDLTool(configuration))

            self.add_element(VCPostBuildEventTool(configuration))
            self.add_element(VCPreBuildEventTool(configuration))
            self.add_element(VCPreLinkEventTool(configuration))

            # Add in the windows specific records
            if platform.is_windows():
                self.add_element(VCResourceCompilerTool(configuration))
                self.add_element(VCWebServiceProxyGeneratorTool(
                    configuration))
                self.add_element(VCXMLDataGeneratorTool(configuration))
                self.add_element(VCWebDeploymentTool(configuration))
                self.add_element(VCManagedWrapperGeneratorTool(
                    configuration))
                self.add_element(VCAuxiliaryManagedWrapperGeneratorTool(
                    configuration))

            # Add in the Xbox specific records
            if platform is PlatformTypes.xbox and \
                    not project_type.is_library():
                self.add_element(XboxDeploymentTool(configuration))
                self.add_element(XboxImageTool(configuration))

        # Add elements in the order expected by Visual Studio 2005/2008.
        else:

            # Add in special elements
            if source_file_detect(
                    configuration.project.codefiles, FileTypes.glsl):
                self.add_element(VCGLSLTool(configuration))

            if source_file_detect(
                    configuration.project.codefiles, FileTypes.hlsl):
                self.add_element(VCHLSLTool(configuration))

            if source_file_detect(
                    configuration.project.codefiles, FileTypes.x64):
                self.add_element(VCMASM64Tool(configuration))

            if source_file_detect(
                    configuration.project.codefiles, FileTypes.x86):
                self.add_element(VCMASMTool(configuration))

            self.add_element(VCPreBuildEventTool(configuration))
            self.add_element(VCCustomBuildTool(configuration))

            if platform.is_windows():
                self.add_element(VCXMLDataGeneratorTool(configuration))
                self.add_element(VCWebServiceProxyGeneratorTool(
                    configuration))
                self.add_element(VCMIDLTool(configuration))

            self.add_element(VCCLCompilerTool(configuration))

            if platform.is_windows():
                self.add_element(VCManagedResourceCompilerTool(
                    configuration))
                self.add_element(VCResourceCompilerTool(configuration))

            self.add_element(VCPreLinkEventTool(configuration))

            if project_type.is_library():
                self.add_element(VCLibrarianTool(configuration))
            else:
                self.add_element(VCLinkerTool(configuration))

            self.add_element(VCALinkTool(configuration))
            self.add_element(VCManifestTool(configuration))
            self.add_element(VCXDCMakeTool(configuration))
            self.add_element(VCBscMakeTool(configuration))
            self.add_element(VCFxCopTool(configuration))
            self.add_element(VCAppVerifierTool(configuration))

            # Only available on 2005
            if ide is IDETypes.vs2005:
                self.add_element(VCWebDeploymentTool(configuration))

            self.add_element(VCPostBuildEventTool(configuration))

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

        VS2003XML.__init__(self, "Configurations")
        for configuration in project.configuration_list:
            self.add_element(VS2003Configuration(configuration))

########################################


class VS2003References(VS2003XML):
    """
    Visual Studio 2003-2008 References record
    """

    def __init__(self):
        """
        Set the defaults.
        """

        VS2003XML.__init__(self, "References")


########################################


class VS2003FileConfiguration(VS2003XML):
    """
    Visual Studio 2003-2008 Configurations record

    Attributes:
        configuration: Parent configuration
        source_file: Source code file
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
        self.source_file = source_file

        VS2003XML.__init__(self, "FileConfiguration")

        self.add_attribute(Name(configuration.vs_configuration_name))

        self.check_for_exclusion(base_name)

        # Set up the element
        tool_name = None
        tool_enums = {}

        if source_file.type in (FileTypes.cpp, FileTypes.c):
            tool_name = "VCCLCompilerTool"
        elif source_file.type is FileTypes.hlsl:
            tool_name = "HLSL"
            tool_enums = HLSL_ENUMS
        elif source_file.type is FileTypes.glsl:
            tool_name = "GLSL"
        elif source_file.type is FileTypes.x86:
            tool_name = "MASM"
            tool_enums = MASM_ENUMS
        elif source_file.type is FileTypes.x64:
            tool_name = "MASM64"
            tool_enums = MASM_ENUMS
        if not tool_name:
            return

        # Get all the rules to apply
        rule_list = (
            configuration.custom_rules,
            configuration.parent.custom_rules,
            configuration.parent.parent.custom_rules)

        if configuration.ide is IDETypes.vs2003 \
                and tool_name != "VCCLCompilerTool":

            self.handle_vs2003_rules(
                rule_list, base_name, tool_name, tool_enums)
        else:
            self.handle_vs2005_rules(
                rule_list, base_name, tool_name, tool_enums)

    ########################################

    def check_for_exclusion(self, base_name):
        """
        Given a filename, check if it's excluded from the build

        If the source file is in the exclusion list, or it's an assembly
        file for the wrong build target, mark it as excluded from the build

        Args:
            base_name: Base name of the file to check
        """

        configuration = self.configuration
        source_file = self.source_file

        # Check if it's excluded from the discard regex
        for exclude_regex in configuration.exclude_list_regex:
            if exclude_regex(base_name):
                self.add_attribute(ExcludedFromBuild(True))
                return

        # Special case, only build assembly files on the proper cpu
        if source_file.type is FileTypes.x86:
            if configuration.platform not in (
                    PlatformTypes.win32, PlatformTypes.xbox):
                self.add_attribute(ExcludedFromBuild(True))
                return

        # X64 only builds on Windows64
        if source_file.type is FileTypes.x64:
            if configuration.platform is not PlatformTypes.win64:
                self.add_attribute(ExcludedFromBuild(True))

    ########################################

    def handle_vs2003_rules(self, rule_list, base_name, tool_name, tool_enums):
        """
        Since 2003 doesn't use rule files, do it all manually

        Args:
            rule_list: Tuple of dicts for all rules to apply
            base_name: Name of the file to check
            tool_name: Name of the build tool
            tool_enums: Enumeration lookup for the specific tool
        """

        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-locals

        if tool_name == "HLSL":
            make_command = make_hlsl_command
        elif tool_name == "GLSL":
            make_command = make_glsl_command
        elif tool_name == "MASM":
            make_command = make_masm_command
        # Don't worry about MASM64, since it's not available on VS 2003
        else:
            return

        # Dictionary of commands
        element_dict = {}

        # Iterate over the rule list tuple
        for rule in rule_list:

            # The key is a regex
            for key in rule:

                # Match the filename?
                if key(base_name):

                    # Get the list of records
                    records = rule[key]
                    for item in records:
                        value = records[item]

                        # Is it an enumeration?
                        enum_table = lookup_enum_value(
                            tool_enums, item, None)

                        # Look it up from the table
                        if enum_table:
                            new_value = lookup_enum_value(
                                enum_table[1], value, None)
                            if new_value is not None:
                                value = str(new_value)

                        # Set the command line switch
                        element_dict[item] = value

        # Were there any overrides?
        source_file = self.source_file
        cmd, description, outputs = make_command(
            element_dict, source_file)
        if cmd:

            # Create a temp configuration
            configuration = self.configuration
            c = Configuration(configuration.name, configuration.platform)

            # Generate a VCCustomBuildTool record and attach it to this file.
            c.vs_Description = description
            c.vs_CommandLine = cmd + "\n"
            c.vs_Outputs = outputs
            self.add_element(VCCustomBuildTool(c))

    ########################################

    def handle_vs2005_rules(self, rule_list, base_name, tool_name, tool_enums):
        """
        Check if there are rules or records specific to a configuration

        Args:
            rule_list: Tuple of dicts for all rules to apply
            base_name: Name of the file to check
            tool_name: Name of the build tool
            tool_enums: Enumeration lookup for the specific tool
        """

        # No elements yet
        tool_root = None

        # Hack, since the x86 file extension is not used by the masm plug in,
        # force its existance so the file extension is mapped
        if tool_name == "MASM" or len(self.attributes) > 1:
            tool_root = VS2003Tool(tool_name)
            self.add_element(tool_root)

        # pylint: disable=too-many-nested-blocks

        # Iterate over the list of dicts
        for rule in rule_list:

            # Found a dict, get the key, it's a regex
            for key in rule:

                # Match?
                if key(base_name):

                    # Get the dict of rules to set
                    records = rule[key]
                    for item in records:

                        # Make sure the tool is created
                        if tool_root is None:
                            tool_root = VS2003Tool(tool_name)
                            self.add_element(tool_root)

                        # Get the keyword
                        value = records[item]

                        # If an enumeration, look up the table
                        enum_table = lookup_enum_value(
                            tool_enums, item, None)

                        # Table found, remap
                        if enum_table:
                            new_value = lookup_enum_value(
                                enum_table[1], value, None)
                            if new_value is not None:
                                value = str(new_value)

                        # Add the rule
                        tool_root.add_attribute(
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

        # Record name is File
        VS2003XML.__init__(self, "File", force_pair=True)

        # Add the RelativePath record
        # Pass IDETypes.vs2003 to force RelativePath
        self.add_attribute(get_path_property(IDETypes.vs2003, vs_name))

        # Add in the file customizations

        # Get the base name for comparison
        item = vs_name.rfind("\\")
        base_name = vs_name if item == -1 else vs_name[item + 1:]

        # Perform all of the customizations
        # Most cases, there are none
        for configuration in project.configuration_list:
            item = VS2003FileConfiguration(
                configuration, base_name, source_file)

            # Only add if it has anything inside
            if item.elements or len(item.attributes) > 1:
                self.elements.append(item)

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

        # Object is Filter
        VS2003XML.__init__(self, "Filter")

        # Add the name attribute
        self.add_attribute(Name(name))

########################################


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

        # Save the project
        self.project = project

        # This is a Files record
        VS2003XML.__init__(self, "Files")

        # Arrange all the files by their directory tree

        # Create group names and attach all files that belong to that group
        groups = {}

        # List of files that have no filter
        root_group = []

        for item in project.codefiles:

            # Visual Studio requires Windows slashes
            item.vs_name = convert_to_windows_slashes(item.relative_pathname)

            # Get the group name (Can be "")
            groupname = item.get_group_name()

            # Special case for groups without filter
            if not groupname:
                root_group.append(item)
            else:
                # Put each filename in its proper group
                group = groups.get(groupname, None)
                if group is None:
                    groups[groupname] = [item]
                else:
                    group.append(item)

        # Convert from a flat tree into a hierarchical tree
        tree = {}
        for group in groups:

            # Get the depth of the tree needed
            parts = group.split("\\")
            nexttree = tree

            # Iterate over every part
            for item, _ in enumerate(parts):
                # Already declared?
                if not parts[item] in nexttree:
                    nexttree[parts[item]] = {}
                # Step into the tree
                nexttree = nexttree[parts[item]]

        # Generate the entries
        # Create the filter tree first
        do_filter_tree(self, "", tree, groups)

        # Then append all the file objects for the root folder last
        for item in sorted(
                root_group,
                key=operator.attrgetter("vs_name")):
            self.add_element(VS2003File(item, project))

########################################


class VS2003Globals(VS2003XML):
    """
    Visual Studio 2003-2008 Globals record
    """

    def __init__(self):
        """
        Init defaults.
        """

        # Make projects doesn't do anything for Globals, maybe in the future
        VS2003XML.__init__(self, "Globals")


########################################


class VS2003vcproj(VS2003XML):
    """
    Visual Studio 2003-2008 formatter.

    This record instructs how to write a Visual Studio 2003-2008 format
    vcproj file.

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

        # Root XML object
        VS2003XML.__init__(
            self, "VisualStudioProject")

        # Always C++ for makeprojects
        self.add_attribute(
            VSStringProperty("ProjectType", "Visual C++"))

        # Which project version?
        ide = project.ide
        if ide is IDETypes.vs2003:
            item = "7.10"
        elif ide is IDETypes.vs2005:
            item = "8.00"
        else:
            item = "9.00"
        self.add_attribute(
            VSStringProperty("Version", item))

        # Name of the project
        self.add_attribute(Name(project.name))

        # Set the GUID
        self.add_attribute(
            VSStringProperty("ProjectGUID",
                            "{" + project.vs_uuid + "}"))

        # Set the root namespace to the same name as the project
        self.add_attribute(
            VSStringProperty("RootNamespace", project.name))

        # Hard coded for VC projects, not C#
        self.add_attribute(
            VSStringProperty("Keyword", "Win32Proj"))

        # VS 2008 sets the framework version
        if ide is IDETypes.vs2008:
            self.add_attribute(
                VSStringProperty("TargetFrameworkVersion", "196613"))

        # Add all of the elements in the order they need to appear
        self.add_element(VS2003Platforms(project))

        # Tool files exists in VS 2005 and 2008
        if ide is not IDETypes.vs2003:
            self.add_element(VS2003ToolFiles(project))

        self.add_element(VS2003Configurations(project))
        self.add_element(VS2003References())
        self.add_element(VS2003Files(project))
        self.add_element(VS2003Globals())

    ########################################

    def generate(self, line_list=None, indent=0, ide=None):
        """
        Write out the VS2003vcproj record.

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
        line_list.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
        return VS2003XML.generate(
            self, line_list, indent=indent, ide=ide)


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

    # pylint: disable=too-many-branches

    # Failsafe, return error if not supported
    if solution.ide not in SUPPORTED_IDES:
        return 10

    # For starters, generate the UUID and filenames for the solution file
    # for visual studio, since each solution and project file generate
    # seperately

    # Iterate over the project files and create the filenames
    for project in solution.get_project_list():

        # Set the project filename
        item = getattr(project, "vs_output_filename", None)
        if not item:

            # Visual Studio 2003-2008 uses the vcproj extension, where
            # 2010 or higher uses vcxproj
            item = ".vcproj" if solution.ide < IDETypes.vs2010 else ".vcxproj"
            project.vs_output_filename = project.name + solution.ide_code + \
                project.platform_code + item

        # Set the project UUID
        item = getattr(project, "vs_uuid", None)
        if not item:
            project.vs_uuid = vs_calcguid(project.vs_output_filename)

        for configuration in project.configuration_list:

            # Get the Visual Studio platform code
            item = configuration.platform.get_vs_platform()[0]

            # A hack is applied to map NVidia Android types to
            # Microsoft Android types
            if solution.ide >= IDETypes.vs2022:
                item = _VS_PLATFORM_HACK.get(item, item)
            configuration.vs_platform = item

            # Create the merged configuration/platform code
            configuration.vs_configuration_name = configuration.name + "|" + \
                item

    # Write to memory for file comparison
    solution_lines = []
    error = generate_solution_file(solution_lines, solution)
    if error:
        return error

    # Get the output flags
    perforce = solution.perforce
    verbose = solution.verbose

    # Create the final filename for the Visual Studio Solution file
    item = getattr(solution, "vs_output_filename", None)
    if not item:
        item = solution.name + solution.ide_code + \
            solution.platform_code + ".sln"

    # Save out the solution file
    save_text_file_if_newer(
        os.path.join(solution.working_directory, item),
        solution_lines,
        bom=solution.ide != IDETypes.vs2003,
        perforce=perforce,
        verbose=verbose)

    # Now that the solution file was generated, create the individual project
    # files using the format appropriate for the selected IDE

    for project in solution.project_list:
        project.get_file_list(
            [FileTypes.h, FileTypes.cpp, FileTypes.c, FileTypes.rc,
             FileTypes.x86, FileTypes.x64, FileTypes.ppc, FileTypes.arm,
             FileTypes.arm64, FileTypes.s,
             FileTypes.hlsl, FileTypes.glsl, FileTypes.x360sl, FileTypes.vitacg,
             FileTypes.ico, FileTypes.appxmanifest, FileTypes.image])

        # Handle WiiU extensions based on found files
        wiiu_props(project)

        # Check if masm.rules needs to be added
        add_masm_support(project)

        # Create the project file template
        if solution.ide >= IDETypes.vs2010:
            exporter = VS2010vcproj(project)
        else:
            exporter = VS2003vcproj(project)

        # Convert to a text file
        project_lines = []

        # Convert to a text file
        exporter.generate(project_lines, ide=solution.ide)

        # Handle any post processing
        project_lines = solution.post_process(project_lines)

        # Save the text
        save_text_file_if_newer(
            os.path.join(
                solution.working_directory,
                project.vs_output_filename),
            project_lines,
            bom=True,
            perforce=perforce,
            verbose=verbose)

        # Visual Studio 2010 and higher has a 3rd file, filters
        if solution.ide >= IDETypes.vs2010:

            # Generate the filter
            exporter = VS2010vcprojfilter(project)

            # Create the file
            filter_lines = []
            exporter.generate(filter_lines)

            # Save it out
            item = os.path.join(
                solution.working_directory,
                project.vs_output_filename + ".filters")

            # Is there any data besides the header?
            if len(filter_lines) >= 4:

                # Save it
                save_text_file_if_newer(
                    item,
                    filter_lines,
                    bom=True,
                    perforce=perforce,
                    verbose=verbose)
            else:

                # File is not needed, remove it.
                delete_file(item)
    return 0
