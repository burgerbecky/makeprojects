#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains the code to generate defaults.

@package makeprojects.defaults

@var makeprojects.defaults._CONFIGURATION_DEFAULTS
Default settings for each configuration type
"""

# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

import os

from .enums import IDETypes, PlatformTypes, ProjectTypes
from .util import getattr_build_rules_list


# Each key must be lower case for case insensitive
# matching
_CONFIGURATION_DEFAULTS = {
    "debug": {
        "short_code": "dbg",
        "debug": True},
    "internal": {
        "short_code": "int",
        "debug": True,
        "optimization": 4},
    "release": {
        "short_code": "rel",
        "debug": False,
        "optimization": 4},
    "release_ltcg": {
        "short_code": "ltc",
        "debug": False,
        "optimization": 4,
        "link_time_code_generation": True},
    "profile": {
        "short_code": "pro",
        "debug": False,
        "optimization": 4,
        "profile": True},
    "profile_fastcap": {
        "short_code": "fas",
        "debug": False,
        "optimization": 4,
        "profile": "fast"},
    "codeanalysis": {
        "short_code": "cod",
        "debug": False,
        "analyze": True}
}

########################################


def settings_from_name(configuration):
    """
    Given a configuration name, set default settings.

    Default names are Debug, Internal, Release, Release_LTCG,
    Profile, Profile_FastCap and CodeAnalysis. If the setting name is
    one of these, or a variant, settings like debug, optimization,
    short_code, or profile are preset.

    Args:
        configuration: Configuration to update
    Returns:
        configuration
    """

    # Case insensitive test
    test_lower = configuration.name.lower()

    # Try the easy way
    settings = _CONFIGURATION_DEFAULTS.get(test_lower, None)

    # If not a direct name, try partial name
    if not settings:
        for item in _CONFIGURATION_DEFAULTS.items():
            if item[0] in test_lower:
                settings = item[1]
                break
        else:
            # Special case for Link Time Code Generation
            if "ltcg" in test_lower:
                settings = _CONFIGURATION_DEFAULTS["release_ltcg"]

    # The configuration name is known, so preset the values
    # in the configuration
    if settings:
        for item in settings.items():
            setattr(configuration, item[0], item[1])
    return configuration


########################################


def configuration_presets(configuration):
    """
    Set the default settings for a configuration.

    Scan a configuration for a platform and an ide and set up compiler macros
    and other settings that are default for the specific platform.

    Args:
        configuration: Configuration record to update.
    """

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    # Save the #defines
    define_list = []

    # If not None, add in _DEBUG or NDEBUG
    if configuration.debug is not None:
        define_list.append("_DEBUG" if configuration.debug else "NDEBUG")

    # Init the list of libraries to load
    libraries_list = []

    # Sanity check for missing platform
    platform = configuration.platform
    if platform is not None:

        ide = configuration.project.ide

        # Force a test for the WATCOM environment variable
        # for Watcom for Windows or DOS
        if ide is IDETypes.watcom:
            if platform.is_windows() or platform.is_msdos():
                configuration.env_variable_list = ["WATCOM"]

        # Windows specific defines
        if platform.is_windows():

            if ide.is_codewarrior():
                configuration.library_folders_list = [
                    "$(CodeWarrior)/MSL", "$(CodeWarrior)/Win32-x86 Support"]
                if configuration.debug:
                    libraries_list.append("MSL_All_x86_D.lib")
                else:
                    libraries_list.append("MSL_All_x86.lib")

            libraries_list.extend(
                ["Kernel32.lib", "Gdi32.lib", "Shell32.lib", "Ole32.lib",
                 "User32.lib", "Advapi32.lib", "version.lib", "Ws2_32.lib",
                 "Comctl32.lib", "WinMM.lib"])

            define_list.extend(["_WINDOWS", "WIN32_LEAN_AND_MEAN"])
            if platform in (PlatformTypes.win64,
                            PlatformTypes.winarm64, PlatformTypes.winitanium):
                define_list.append("WIN64")
            else:
                define_list.append("WIN32")

            # Command line tools need this define
            if configuration.project_type is ProjectTypes.tool:
                define_list.append("_CONSOLE")

        # MSDos with DOS4GW extender
        if platform is PlatformTypes.msdos4gw:
            define_list.append("__DOS4G__")

        # MSDos with X32 extender
        if platform is PlatformTypes.msdosx32:
            define_list.append("__X32__")

        # Playstation 4
        if platform is PlatformTypes.ps4:
            define_list.append("__ORBIS2__")

            # Include default libraries
            libraries_list.extend(("SceSysmodule_stub_weak", "ScePosix_stub_weak",
                                  "SceVideoOut_stub_weak", "ScePad_stub_weak",
                                  "SceVideodec2_stub_weak", "SceAudiodec_stub_weak",
                                  "SceAudioOut_stub_weak", "SceGnmDriver_stub_weak",
                                  "SceGnm", "SceGnmx", "SceGpuAddress"))

        # Playstation 5 (Not needed)
        # if platform is PlatformTypes.ps5:
        #    define_list.append("__PROSPERO__")

        # Playstation Vita
        if platform is PlatformTypes.vita:
            define_list.append("SN_TARGET_PSP2")

        # Google Stadia
        if platform is PlatformTypes.stadia:
            define_list.append("_GNU_SOURCE")
            define_list.append("VK_USE_PLATFORM_GGP")

        # Android targets
        if platform.is_android():
            define_list.append("DISABLE_IMPORTGL")
            libraries_list.extend(["android", "EGL", "GLESv1_CM"])

        # Xbox 360
        if platform is PlatformTypes.xbox360:
            define_list.extend(["_XBOX", "XBOX"])
            libraries_list.extend(["xbdm.lib", "xboxkrnl.lib"])
            if configuration.get_chained_value("profile"):
                libraries_list.extend(
                    ["d3d9i.lib", "d3dx9i.lib", "xgraphics.lib", "xapilibi.lib",
                     "xaudio2.lib", "x3daudioi.lib", "xmcorei.lib"])
            elif configuration.debug:
                libraries_list.extend(
                    ["d3d9d.lib", "d3dx9d.lib", "xgraphicsd.lib",
                     "xapilibd.lib", "xaudiod2.lib", "x3daudiod.lib",
                     "xmcored.lib"])
            else:
                libraries_list.extend(
                    ["d3d9ltcg.lib", "d3dx9.lib", "xgraphics.lib",
                     "xapilib.lib", "xaudio2.lib", "x3daudioltcg.lib",
                     "xmcoreltcg.lib"])

        # Xbox ONE
        if platform is PlatformTypes.xboxone:
            libraries_list.extend(
                ["pixEvt.lib", "d3d11_x.lib", "combase.lib", "kernelx.lib",
                 "uuid.lib", "%(XboxExtensionsDependencies)"])

        # Nintendo DSI specific defines
        if platform is PlatformTypes.dsi:
            define_list.extend([
                "NN_BUILD_DEBUG",
                "NN_COMPILER_RVCT",
                "NN_COMPILER_RVCT_VERSION_MAJOR=$(CTRSDK_RVCT_VER_MAJOR)",
                "NN_PROCESSOR_ARM",
                "NN_PROCESSOR_ARM11MPCORE",
                "NN_PROCESSOR_ARM_V6",
                "NN_PROCESSOR_ARM_VFP_V2",
                "NN_HARDWARE_CTR",
                "NN_PLATFORM_CTR",
                "NN_HARDWARE_CTR_TS",
                "NN_SYSTEM_PROCESS",
                "NN_SWITCH_ENABLE_HOST_IO=1",
                "NN_BUILD_VERBOSE",
                "NN_BUILD_NOOPT",
                "NN_DEBUGGER_KMC_PARTNER"])

        # Nintendo WiiU
        if platform is PlatformTypes.wiiu:
            configuration.include_folders_list.append(
                "$(CAFE_ROOT_DOS)\\system\\src\\tool\\gfx\\include")
            configuration.include_folders_list.append(
                "$(CAFE_ROOT_DOS)\\system\\include")

        # Nintendo Switch
        if platform.is_switch():
            configuration.include_folders_list.append(
                "$(NINTENDO_SDK_ROOT)\\include")

            if platform is PlatformTypes.switch32:
                configuration.include_folders_list.append(
                    "$(NINTENDO_SDK_ROOT)\\TargetSpecificInclude\\"
                    "NX-NXFP2-a32")
            else:
                configuration.include_folders_list.append(
                    "$(NINTENDO_SDK_ROOT)\\TargetSpecificInclude\\"
                    "NX-NXFP2-a64")

            define_list.append("NN_NINTENDO_SDK")
            if configuration.debug:
                define_list.append("NN_ENABLE_ASSERT")
                define_list.append("NN_ENABLE_ABORT_MESSAGE")
                if configuration.optimization:
                    define_list.append("NN_SDK_BUILD_DEVELOP")
                else:
                    define_list.append("NN_SDK_BUILD_DEBUG")
            else:
                define_list.append("NN_SDK_BUILD_RELEASE")
                define_list.append("NN_DISABLE_ASSERT")
                define_list.append("NN_DISABLE_ABORT_MESSAGE")

        # Linux platform
        if platform is PlatformTypes.linux:
            define_list.append("__LINUX__")

        # Mac Carbon
        if platform.is_macos_carbon():
            define_list.append("TARGET_API_MAC_CARBON=1")

        # macOS X platform frameworks
        if platform.is_macosx():
            if not configuration.project_type.is_library():
                configuration.frameworks_list = [
                    "AppKit.framework", "AudioToolbox.framework",
                    "AudioUnit.framework", "Carbon.framework",
                    "Cocoa.framework", "CoreAudio.framework",
                    "IOKit.framework", "OpenGL.framework",
                    "QuartzCore.framework", "SystemConfiguration.framework"
                ]

        # iOS platform frameworks
        if platform.is_ios():
            if not configuration.project_type.is_library():
                configuration.frameworks_list = [
                    "AVFoundation.framework", "CoreGraphics.framework",
                    "CoreLocation.framework", "Foundation.framework",
                    "QuartzCore.framework", "UIKit.framework"
                ]

    # Save the macros
    configuration.define_list = define_list

    # Only link libraries for executables.
    project_type = configuration.project_type
    if project_type is not None:
        if not project_type.is_library():
            configuration.libraries_list = libraries_list

########################################


def get_project_name(build_rules_list, working_directory, verbose=False, project_name=None):
    """
    Determine the project name.

    Scan the build_rules.py file for the variable PROJECT_NAME,
    and if found use that string for the project name. Otherwise,
    use the name of the working folder.

    Args:
        build_rules_list: List of build_rules to iterate over.
        working_directory: Full path name of the build_rules.py to load.
        verbose: Boolean, True if name is to be printed
        project_name: String, project name override

    Returns:
        Name of the project.
    """

    if not project_name:
        # Check build_rules.py
        project_name = getattr_build_rules_list(
            build_rules_list, "PROJECT_NAME", None)
        if not project_name:
            project_name = os.path.basename(working_directory)

    # Print if needed.
    if verbose:
        print("Project name is {}".format(project_name))
    return project_name

########################################


def get_project_type(build_rules_list, verbose=False, project_type=None):
    """
    Determine the project type.

    Scan the build_rules.py file for the variable PROJECT_TYPE,
    and if found use that string for the project type. Otherwise,
    assume it's a command line tool.

    Args:
        build_rules_list: List of build_rules to iterate over.
        verbose: Boolean, True for verbose output
        project_type: Proposed project type.

    Returns:
        ProjectTypes enumeration.
    """

    # Make sure the input is ProjectTypes
    if project_type:
        project_type = ProjectTypes.lookup(project_type)

    # If it's not, search the build_rules for it
    if not isinstance(project_type, ProjectTypes):

        # Check build_rules.py
        project_type = getattr_build_rules_list(
            build_rules_list, "PROJECT_TYPE", None)

        # Is it not a ProjectTypes?
        if not isinstance(project_type, ProjectTypes):
            item = ProjectTypes.lookup(project_type)
            if not isinstance(item, ProjectTypes):
                print("Project Type \"{}\" is not supported, using \"tool\".".format(
                    project_type))
                project_type = ProjectTypes.tool
            else:
                project_type = item

    # Print if needed.
    if verbose:
        print("Project type is {}".format(str(project_type)))
    return project_type

########################################


def get_platform(build_rules_list, verbose=False, platform=None):
    """
    Determine the platforms to generate projects for.

    Scan the build_rules.py file for the variable PROJECT_PLATFORM,
    and if found use that list of PlatformTypes or strings to lookup with
    PlatformTypes.lookup().

    Args:
        build_rules_list: List to append a valid build_rules file instance.
        verbose: Boolean, True for verbose output
        platform: Proposed platform type.

    Returns:
        Platform to generate project for.
    """

    # Make sure the input is PlatformTypes
    if platform:
        platform = PlatformTypes.lookup(platform)

    # If it's not, search the build_rules for it
    if not isinstance(platform, PlatformTypes):

        # Check build_rules.py
        platform = getattr_build_rules_list(
            build_rules_list, "PROJECT_PLATFORM", None)

        # Is it not a PlatformTypes?
        if not isinstance(platform, PlatformTypes):
            item = PlatformTypes.lookup(platform)
            if not isinstance(item, PlatformTypes):
                print("Platform Type \"{}\" is not supported, using a default.".format(
                    platform))
                platform = PlatformTypes.default()
            else:
                platform = item

    # Print if needed.
    if verbose:
        print("Platform name {}".format(platform))
    return platform


########################################


def guess_ide(platform):
    """
    Guess the IDE for a specific platform.
    In cases where the platform is known, but the IDE is not, return the most
    likely IDE to use for building the platform.

    Args:
        platform: Platform to build for.
    Returns:
        IDETypes of the recommended IDE, or None if not known.
    """

    # pylint: disable=too-many-return-statements

    # Platform without an IDE is tricky, because video game platforms
    # are picky.

    if platform is PlatformTypes.xbox:
        return IDETypes.vs2003

    if platform is PlatformTypes.xbox360:
        return IDETypes.vs2010

    if platform is PlatformTypes.wiiu:
        return IDETypes.vs2013

    if platform in (PlatformTypes.ps3, PlatformTypes.vita, PlatformTypes.shield):
        return IDETypes.vs2015

    if platform in (PlatformTypes.xboxone, PlatformTypes.switch):
        return IDETypes.vs2017

    if platform in (PlatformTypes.xboxgdk, PlatformTypes.xboxonex):
        return IDETypes.vs2022

    if platform in (PlatformTypes.ps4, PlatformTypes.ps5,
            PlatformTypes.stadia, PlatformTypes.android):
        return IDETypes.vs2022

    if platform is PlatformTypes.linux:
        return IDETypes.make

    # Unknown, punt on the IDE
    return None


########################################


def get_ide(build_rules_list, verbose=False, ide=None, platform=None):
    """
    Determine the IDEs to generate projects for.

    Scan the build_rules.py file for the variable PROJECT_IDE,
    and if found use that IDETypes or string to lookup with
    IDETypes.lookup().

    Args:
        build_rules_list: List to append a valid build_rules file instance.
        verbose: Boolean, True for verbose output
        ide: Proposed ide type.
        platform: Platform to build for, used for guess_ide

    Returns:
        IDE to generate project for.
    """

    # Make sure the input is IDETypes
    if ide:
        ide = IDETypes.lookup(ide)

    # If it's not, search the build_rules for it
    if not isinstance(ide, IDETypes):

        # Check build_rules.py
        ide = getattr_build_rules_list(
            build_rules_list, "PROJECT_IDE", None)

        # Is it not a IDETypes?
        if not isinstance(ide, IDETypes):
            item = IDETypes.lookup(ide)
            if not isinstance(item, IDETypes):
                ide = guess_ide(platform)
                if not ide:
                    print("IDE Type \"{}\" is not supported, using a default.".format(
                        ide))
                    ide = IDETypes.default()
            else:
                ide = item

    # Print if needed.
    if verbose:
        print("IDE name {}".format(ide))
    return ide

########################################


def default_configuration_list(platform, ide):
    """
    Create the default configurations.

    Args:
        platform: platform being built.
        ide: IDE being generated for.
    Returns:
        List strings with names of configurations.
    """

    # All platforms support this format.
    results = ["Debug", "Internal", "Release"]

    # Xbox and Windows support link time code generation
    # as a platform
    if ide.is_visual_studio() and platform.is_windows() or platform in (PlatformTypes.xbox360,):
        results.append("Release_LTCG")

    # Configurations specific to the Xbox 360
    if platform is PlatformTypes.xbox360:
        results.extend(["Profile", "Profile_FastCap", "CodeAnalysis"])
    return results

########################################


def get_configuration_list(
        build_rules_list, configurations, platform, ide):
    """
    Determine the configurations to generate projects for.

    Scan the build_rules.py file for the command "configuration_list"
    and if found, use that list of strings to create configurations.

    Args:
        build_rules_list: List to append a valid build_rules file instance.
        configurations: List of configuration names
        platform: Platform building.
        ide: IDETypes for the ide generating for.

    Returns:
        List of configuration strings to generate projects for.
    """

    # Create the configurations for this platform
    if not configurations:
        for build_rules in build_rules_list:
            configuration_list = getattr(
                build_rules, "configuration_list", None)
            if not configuration_list:
                continue
            configurations = configuration_list(platform=platform, ide=ide)
            if configurations:
                break
        else:
            configurations = default_configuration_list(
                platform=platform, ide=ide)

    return configurations
