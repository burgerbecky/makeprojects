#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration types for makeprojects

All enumerations are stored in this package

"""

## \package makeprojects.enums

# Copyright 2013-2022 by Rebecca Ann Heineman becky@burgerbecky.com
#
# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

from __future__ import absolute_import, print_function, unicode_literals
from enum import IntEnum
import os
from burger import get_mac_host_type, get_windows_host_type, \
    where_is_visual_studio, where_is_codeblocks, where_is_watcom, where_is_xcode

# pylint: disable=invalid-name
# pylint: disable=consider-using-f-string

########################################


class FileTypes(IntEnum):
    """
    Enumeration of supported file types for project input

    Each file that is to be added to a project has specific build rules,
    this enumeration helps determine which compiler to invoke to build the file
    if a build step is necessary.
    """

    ## User file type (Unknown)
    user = 0
    ## Non compiling file type
    generic = 1
    ## Compile as C
    c = 2
    ## Compile as C++
    cpp = 3
    ## C/C++ header
    h = 4
    ## Objective-C
    m = 5
    ## XML text file
    xml = 6
    ## Windows resource file
    rc = 7
    ## Mac OS resource file
    r = 8
    ## HLSL DirectX Shader
    hlsl = 9
    ## GLSL OpenGL Shader
    glsl = 10
    ## Xbox 360 DirectX Shader
    x360sl = 11
    ## Playstation Vita CG Shader
    vitacg = 12
    ## Mac OSX Framework
    frameworks = 13
    ## Static libary
    library = 14
    ## Object code
    object = 15
    ## Executable file
    exe = 16
    ## XCode configuration file
    xcconfig = 17
    ## X86 assembly source
    x86 = 18
    ## X64 assembly source
    x64 = 19
    ## 6502/65812 assembly source
    a65 = 20
    ## PowerPC assembly source
    ppc = 21
    ## 680x0 assembly source
    a68 = 22
    ## Image files
    image = 23
    ## Windows icon files
    ico = 24
    ## MacOSX icon files
    icns = 25
    ## Windows AppXManifest files
    appxmanifest = 26

    @staticmethod
    def lookup(test_name):
        """
        Look up a file name extension and return the type.
        @details
        Parse the filename extension and match it to a table of known
        extensions and return the enumeration for the file type. The
        test is case insensitive.

        Args:
            test_name: Filename to test
        Returns:
            A @ref FileTypes member or None on failure
        See Also:
            makeprojects.enums._FILETYPES_LOOKUP
        """

        return _FILETYPES_LOOKUP.get(
            os.path.splitext(test_name)[1][1:].strip().lower(), None)

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description

        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._FILETYPES_READABLE
        """

        return _FILETYPES_READABLE.get(self, None)

    ## Allow str() to work.
    __str__ = __repr__


## Dictionary of default file extensions and mapped types
#
# When the directory is scanned for input files, the files will be tested
# against this list with a forced lowercase filename and determine the type of
# compiler to assign to an input file
#
# This list can be appended or modified to allow other file types to be
# processed
#
# @sa makeprojects.enums.FileTypes.lookup()

_FILETYPES_LOOKUP = {
    'c': FileTypes.c,                   # C/C++ source code
    'cc': FileTypes.cpp,
    'cpp': FileTypes.cpp,
    'c++': FileTypes.cpp,
    'hpp': FileTypes.h,                 # C/C++ header files
    'h': FileTypes.h,
    'hh': FileTypes.h,
    'i': FileTypes.h,
    'inc': FileTypes.h,
    'm': FileTypes.m,                   # MacOSX / iOS Objective-C
    'mm': FileTypes.m,                  # MacOSX / iOS Objective-C++
    'plist': FileTypes.xml,             # MacOSX / iOS plist files
    'rc': FileTypes.rc,                 # Windows resources
    'r': FileTypes.r,                   # MacOS classic resources
    'rsrc': FileTypes.r,
    'hlsl': FileTypes.hlsl,             # DirectX shader files
    'vsh': FileTypes.glsl,              # OpenGL shader files
    'fsh': FileTypes.glsl,
    'glsl': FileTypes.glsl,
    'x360sl': FileTypes.x360sl,         # Xbox 360 shader files
    'vitacg': FileTypes.vitacg,         # PS Vita shader files
    'lib': FileTypes.library,           # Static library
    'a': FileTypes.library,
    'obj': FileTypes.object,            # .obj object code
    'o': FileTypes.object,
    'xml': FileTypes.xml,               # XML data files
    'x86': FileTypes.x86,               # Intel ASM 80x86 source code
    'x64': FileTypes.x64,               # AMD 64 bit source code
    'a65': FileTypes.a65,               # 6502/65816 source code
    'ppc': FileTypes.ppc,               # PowerPC source code
    'a68': FileTypes.a68,               # 680x0 source code
    'ico': FileTypes.ico,               # Windows icon file
    'icns': FileTypes.icns,             # Mac OSX Icon file
    'png': FileTypes.image,             # Art files
    'jpg': FileTypes.image,
    'bmp': FileTypes.image,
    'txt': FileTypes.generic,           # Text files
    'rtf': FileTypes.generic,
    'rst': FileTypes.generic,
    'md': FileTypes.generic,
    'pdf': FileTypes.generic,
    'sh': FileTypes.generic,
    'cmd': FileTypes.generic,
    'bat': FileTypes.generic,
    'appxmanifest': FileTypes.appxmanifest
}

## List of human readable strings
#
# Dictionary to map FileTypes enumerations into an human readable string
#
# @sa makeprojects.enums.FileTypes.__repr__()

_FILETYPES_READABLE = {
    FileTypes.user: 'User',
    FileTypes.generic: 'Generic',
    FileTypes.c: 'C source file',
    FileTypes.cpp: 'C++ source file',
    FileTypes.h: 'C header file',
    FileTypes.m: 'Objective-C file',
    FileTypes.xml: 'Xml file',
    FileTypes.rc: 'Windows Resource file',
    FileTypes.r: 'MacOS Resource file',
    FileTypes.hlsl: 'DirectX shader file',
    FileTypes.glsl: 'OpenGL shader file',
    FileTypes.x360sl: 'Xbox 360 shader file',
    FileTypes.vitacg: 'Playstation Vita shader file',
    FileTypes.frameworks: 'macOS Framework',
    FileTypes.library: 'Statically linked library',
    FileTypes.object: 'Object code',
    FileTypes.exe: 'Executable file',
    FileTypes.xcconfig: 'Apple XCode config file',
    FileTypes.x86: 'X86 assembly file',
    FileTypes.x64: 'X64 assembly file',
    FileTypes.a65: '6502/65816 assembly file',
    FileTypes.ppc: 'PowerPC assembly file',
    FileTypes.a68: '680x0 assembly file',
    FileTypes.image: 'Image file',
    FileTypes.ico: 'Windows Icon file',
    FileTypes.icns: 'macOS Icon file',
    FileTypes.appxmanifest: 'Windows AppX Manifest file'
}

########################################


class ProjectTypes(IntEnum):
    """
    Enumeration of supported project types

    Each configuration can build a specific type of file, this enumeration
    lists out the types of files that can be built.
    """

    ## Code library
    library = 0
    ## Command line tool
    tool = 1
    ## Application
    app = 2
    ## Screen saver
    screensaver = 3
    ## Shared library (DLL)
    sharedlibrary = 4
    ## Empty project
    empty = 5

    def is_library(self):
        """
        Determine if the project is a library.

        Returns:
            True if the project is a static or dynamic library.
        """

        return self in (ProjectTypes.library, ProjectTypes.sharedlibrary)

    @staticmethod
    def lookup(project_type_name):
        """
        Look up a ProjectTypes based on name.
        @details
        For maximum compatiblity, the name will be scanned from several
        look up tables to attempt to cover all premutations of an input string.

        Note:
            String comparisons are case insensitive.

        Args:
            project_type_name: Project type string to test.
        Returns:
            A @ref ProjectTypes member or None on failure.
        """

        # Already a ProjectTypes?
        if isinstance(project_type_name, ProjectTypes):
            return project_type_name

        if project_type_name:
            # Try the member name as is.
            test_name = project_type_name.lower()
            if hasattr(ProjectTypes, project_type_name):
                return ProjectTypes[project_type_name]

            # Try a number of ways to find a match
            for item in _PROJECTTYPES_READABLE:
                # Verbose name?
                if test_name == str(item).lower():
                    return item

            specials = {
                'lib': ProjectTypes.library,
                'game': ProjectTypes.app,
                'dll': ProjectTypes.sharedlibrary,
                'console': ProjectTypes.tool,
                'scr': ProjectTypes.screensaver
            }
            return specials.get(test_name, None)

        return None

    @staticmethod
    def default():
        """
        Determine the ProjectTypes default.
        """
        return ProjectTypes.tool

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description

        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._PROJECTTYPES_READABLE
        """

        return _PROJECTTYPES_READABLE.get(self, None)

    ## Allow str() to work.
    __str__ = __repr__

## List of human readable strings
#
# Dictionary to map ProjectTypes enumerations into an human readable string
#
# @sa makeprojects.enums.ProjectTypes.__repr__()


_PROJECTTYPES_READABLE = {
    ProjectTypes.library: 'Library',
    ProjectTypes.tool: 'Tool',
    ProjectTypes.app: 'Application',
    ProjectTypes.screensaver: 'ScreenSaver',
    ProjectTypes.sharedlibrary: 'Dynamic Library',
    ProjectTypes.empty: 'Empty'
}


########################################


class IDETypes(IntEnum):
    """
    Enumeration of supported IDEs

    All supported IDEs and makefile formats are enumerated here.
    """

    ## Visual studio 2003
    vs2003 = 0
    ## Visual studio 2005
    vs2005 = 1
    ## Visual studio 2008
    vs2008 = 2
    ## Visual studio 2010
    vs2010 = 3
    ## Visual studio 2012
    vs2012 = 4
    ## Visual studio 2013
    vs2013 = 5
    ## Visual studio 2015
    vs2015 = 6
    ## Visual studio 2017
    vs2017 = 7
    ## Visual studio 2019
    vs2019 = 8
    ## Visual studio 2022
    vs2022 = 9

    ## Open Watcom 1.9 or later
    watcom = 10

    ## Metrowerks Codewarrior 9 / 5.0 (Windows/Mac OS)
    codewarrior50 = 11
    ## Metrowerks Codewarrior 10 / 5.8 (Mac OS Carbon)
    codewarrior58 = 12
    ## Freescale Codewarrior 5.9 (Nintendo DSi)
    codewarrior59 = 13

    ## XCode 3 (PowerPC 3.1.4 is the target version)
    xcode3 = 14
    ## XCode 4
    xcode4 = 15
    ## XCode 5
    xcode5 = 16
    ## XCode 6
    xcode6 = 17
    ## XCode 7
    xcode7 = 18
    ## XCode 8
    xcode8 = 19
    ## XCode 9
    xcode9 = 20
    ## XCode 10
    xcode10 = 21
    ## XCode 11
    xcode11 = 22

    ## Codeblocks
    codeblocks = 23

    ## nmake
    nmake = 24

    ## make
    make = 25

    ## bazel
    bazel = 26

    ## MPW
    mpw = 27

    def get_short_code(self):
        """
        Create the ide code from the ide type.
        @details
        Return the three letter code that determines the specfic IDE
        version that the project file is meant for.

        Returns:
            Three letter code specific to the IDE version or None.
        See Also:
            makeprojects.enums._IDETYPES_CODES
        """

        return _IDETYPES_CODES.get(self, None)

    def is_visual_studio(self):
        """
        Determine if the IDE is Microsoft Visual Studio.

        Returns:
            True if the platform is Microsoft Visual Studio.
        """

        return self in (
            IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008, IDETypes.vs2010,
            IDETypes.vs2012, IDETypes.vs2013, IDETypes.vs2015, IDETypes.vs2017,
            IDETypes.vs2019, IDETypes.vs2022)

    def is_xcode(self):
        """
        Determine if the IDE is Apple XCode.

        Returns:
            True if the platform is Apple XCode.
        """

        return self in (
            IDETypes.xcode3, IDETypes.xcode4, IDETypes.xcode5, IDETypes.xcode6,
            IDETypes.xcode7, IDETypes.xcode8, IDETypes.xcode9, IDETypes.xcode10,
            IDETypes.xcode11)

    def is_codewarrior(self):
        """
        Determine if the IDE is Metrowerks / Freescale Codewarrior.

        Returns:
            True if the platform is Metrowerks / Freescale Codewarrior.
        """

        return self in (IDETypes.codewarrior50,
                        IDETypes.codewarrior58, IDETypes.codewarrior59)

    @staticmethod
    def lookup(ide_name):
        """
        Look up a IDETypes based on name.
        @details
        For maximum compatiblity, the name will be scanned from several
        look up tables to attempt to cover all premutations of an input string.

        Note:
            String comparisons are case insensitive.

        Args:
            ide_name: Platform string to test.
        Returns:
            A @ref IDETypes member or None on failure.
        """

        # Too many return statements
        # pylint: disable=R0911

        # Already a IDETypes?
        if isinstance(ide_name, IDETypes):
            return ide_name

        if ide_name:
            # Try the member name as is.
            test_name = ide_name.lower()
            if hasattr(IDETypes, test_name):
                return IDETypes[test_name]

            # Try a number of ways to find a match
            for item in _IDETYPES_READABLE:
                # Verbose name? File name short code?
                if test_name == str(item).lower(
                ) or test_name == _IDETYPES_CODES[item]:
                    return item

            # Try some generic names and perform magic to figure out the IDE
            if ide_name in ('vs', 'visualstudio',
                            'visual_studio', 'visual studio'):
                return get_installed_visual_studio()

            if ide_name in ('xcode',):
                return get_installed_xcode()

            if ide_name in ('codewarrior', 'metrowerks', 'cw', 'freescale'):
                return IDETypes.codewarrior50

        return None

    @staticmethod
    def default():
        """
        Determine the default IDETypes from the currently running platform.
        """

        # Windows host?
        if get_windows_host_type():
            result = get_installed_visual_studio()
            if result is not None:
                return result

        # Mac host?
        elif get_mac_host_type():
            result = get_installed_xcode()
            if result is not None:
                return result

        # Unknown platforms default to Linux
        if where_is_codeblocks():
            return IDETypes.codeblocks

        if where_is_watcom():
            return IDETypes.watcom
        return IDETypes.make

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description.

        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._IDETYPES_READABLE
        """

        return _IDETYPES_READABLE.get(self, None)

    ## Allow str() to work.
    __str__ = __repr__


## List of IDE short codes
#
# Dictionary to map IDETypes enumerations into a
# three letter code to append to a project filename
#
# @sa makeprojects.enums.IDETypes.get_short_code()

_IDETYPES_CODES = {
    IDETypes.vs2003: 'vc7',                 # Microsoft Visual Studio
    IDETypes.vs2005: 'vc8',
    IDETypes.vs2008: 'vc9',
    IDETypes.vs2010: 'v10',
    IDETypes.vs2012: 'v12',
    IDETypes.vs2013: 'v13',
    IDETypes.vs2015: 'v15',
    IDETypes.vs2017: 'v17',
    IDETypes.vs2019: 'v19',
    IDETypes.vs2022: 'v22',
    IDETypes.watcom: 'wat',                 # Watcom MAKEFILE
    IDETypes.codewarrior50: 'c50',          # Metrowerks / Freescale CodeWarrior
    IDETypes.codewarrior58: 'c58',
    IDETypes.codewarrior59: 'c59',
    IDETypes.xcode3: 'xc3',                 # Apple XCode
    IDETypes.xcode4: 'xc4',
    IDETypes.xcode5: 'xc5',
    IDETypes.xcode6: 'xc6',
    IDETypes.xcode7: 'xc7',
    IDETypes.xcode8: 'xc8',
    IDETypes.xcode9: 'xc9',
    IDETypes.xcode10: 'x10',
    IDETypes.xcode11: 'x11',
    IDETypes.codeblocks: 'cdb',             # Codeblocks
    IDETypes.nmake: 'nmk',                  # nmake
    IDETypes.make: 'mak',                   # make
    IDETypes.bazel: 'bzl',                  # Bazel
    IDETypes.mpw: 'mpw'                     # MPW Make
}

## List of human readable strings
#
# Dictionary to map IDETypes enumerations into an human readable string
#
# @sa makeprojects.enums.IDETypes.__repr__()

_IDETYPES_READABLE = {
    IDETypes.vs2003: 'Visual Studio 2003',
    IDETypes.vs2005: 'Visual Studio 2005',
    IDETypes.vs2008: 'Visual Studio 2008',
    IDETypes.vs2010: 'Visual Studio 2010',
    IDETypes.vs2012: 'Visual Studio 2012',
    IDETypes.vs2013: 'Visual Studio 2013',
    IDETypes.vs2015: 'Visual Studio 2015',
    IDETypes.vs2017: 'Visual Studio 2017',
    IDETypes.vs2019: 'Visual Studio 2019',
    IDETypes.vs2022: 'Visual Studio 2022',
    IDETypes.watcom: 'Open Watcom 1.9 wmake',
    IDETypes.codewarrior50: 'CodeWarrior 9',
    IDETypes.codewarrior58: 'CodeWarrior 10',
    IDETypes.codewarrior59: 'Freescale CodeWarrior 5.9',
    IDETypes.xcode3: 'XCode 3.1.4',
    IDETypes.xcode4: 'XCode 4',
    IDETypes.xcode5: 'XCode 5',
    IDETypes.xcode6: 'XCode 6',
    IDETypes.xcode7: 'XCode 7',
    IDETypes.xcode8: 'XCode 8',
    IDETypes.xcode9: 'XCode 9',
    IDETypes.xcode10: 'XCode 10',
    IDETypes.xcode11: 'XCode 11',
    IDETypes.codeblocks: 'CodeBlocks 13.12',
    IDETypes.nmake: 'GNU make',
    IDETypes.make: 'Linux make',
    IDETypes.bazel: 'Bazel build',
    IDETypes.mpw: 'Apple MPW make'
}

########################################


def get_installed_visual_studio():
    """
    Find installed Visual Studio version.

    Scan the host computer and return the IDETypes for the most
    recent version of Visual Studio that's installed.

    Returns:
        IDETypes value or None
    """

    vs_studio_table = (
        (2022, IDETypes.vs2022),
        (2019, IDETypes.vs2019),
        (2017, IDETypes.vs2017),
        (2015, IDETypes.vs2015),
        (2013, IDETypes.vs2013),
        (2012, IDETypes.vs2012),
        (2010, IDETypes.vs2010),
        (2008, IDETypes.vs2008),
        (2005, IDETypes.vs2005),
        (2003, IDETypes.vs2003)
    )
    for item in vs_studio_table:
        if where_is_visual_studio(item[0]):
            return item[1]
    return None


########################################


def get_installed_xcode():
    """
    Find installed Xcode version.

    Scan the host computer and return the IDETypes for the most
    recent version of XCode that's installed.

    Returns:
        IDETypes value or None
    """

    xcode_table = (
        (11, IDETypes.xcode11),
        (10, IDETypes.xcode10),
        (9, IDETypes.xcode9),
        (8, IDETypes.xcode8),
        (7, IDETypes.xcode7),
        (6, IDETypes.xcode6),
        (5, IDETypes.xcode5),
        (4, IDETypes.xcode4),
        (3, IDETypes.xcode3)
    )
    for item in xcode_table:
        if where_is_xcode(item[0]):
            return item[1]
    return None

########################################


class PlatformTypes(IntEnum):
    """
    Enumeration of supported target platforms.

    All supported tool chains for specific platforms are enumerated here.
    """

    ## Windows 32 and 64 bit Intel and arm64
    windows = 0
    ## Windows 32 and 64 bit Intel
    windowsintel = 1
    ## Windows 32 and 64 bit arm
    windowsarm = 2
    ## Windows 32 bit intel only
    win32 = 3
    ## Window 64 bit intel only
    win64 = 4
    ## Windows 32 bit arm only
    winarm32 = 5
    ## Windows 64 bit arm only
    winarm64 = 6
    ## Windows 64 bit itanium only
    winitanium = 7

    ## Mac OSX, all CPUs
    macosx = 8
    ## Mac OSX PowerPC 32 bit only
    macosxppc32 = 9
    ## Mac OSX PowerPC 64 bit only
    macosxppc64 = 10
    ## Mac OSX Intel 32 bit only
    macosxintel32 = 11
    ## Mac OSX Intel 64 bit only
    macosxintel64 = 12

    ## Mac OS 9, all CPUs
    macos9 = 13
    ## Mac OS 9 680x0 only
    macos968k = 14
    ## Mac OS 9 PowerPC 32 bit only
    macos9ppc = 15
    ## Mac OS Carbon, all CPUs
    maccarbon = 16
    ## Mac OS Carbon 680x0 only (CFM)
    maccarbon68k = 17
    ## Mac OS Carbon PowerPC 32 bit only
    maccarbonppc = 18

    ## iOS, all CPUs
    ios = 19
    ## iOS 32 bit ARM only
    ios32 = 20
    ## iOS 64 bit ARM only
    ios64 = 21
    ## iOS emulator, all CPUs
    iosemu = 22
    ## iOS emulator 32 bit Intel only
    iosemu32 = 23
    ## iOS emulator 64 bit Intel only
    iosemu64 = 24

    ## Microsoft Xbox classic
    xbox = 25
    ## Microsoft Xbox 360
    xbox360 = 26
    ## Microsoft Xbox ONE
    xboxone = 27

    ## Sony PS1
    ps1 = 28
    ## Sony PS2
    ps2 = 29
    ## Sony PS3
    ps3 = 30
    ## Sony PS4
    ps4 = 31
    ## Sony Playstation portable
    psp = 32
    ## Sony Playstation VITA
    vita = 33

    ## Nintendi Wii
    wii = 34
    ## Nintendo WiiU
    wiiu = 35
    ## Nintendo Switch
    switch = 36
    ## Nintendo Switch 32 bit only
    switch32 = 37
    ## Nintendo Switch 64 bit only
    switch64 = 38

    ## Nintendo 3DS
    dsi = 39
    ## Nintendo DS
    ds = 40

    ## Generic Android
    android = 41
    ## nVidia SHIELD
    shield = 42
    ## Intellivision Amico
    amico = 43
    ## Ouya (Now Razor)
    ouya = 44
    ## Android Tegra
    tegra = 45
    ## Android Arm32
    androidarm32 = 46
    ## Android Arm64
    androidarm64 = 47
    ## Android Intel x32
    androidintel32 = 48
    ## Android Intel / AMD 64
    androidintel64 = 49

    ## Generic Linux
    linux = 50

    ## MSDOS
    msdos = 51
    ## MSDOS Dos4GW
    msdos4gw = 52
    ## MSDOS DosX32
    msdosx32 = 53

    ## BeOS
    beos = 54
    ## Apple IIgs
    iigs = 55

    def get_short_code(self):
        """
        Convert the enumeration to a 3 letter code for filename suffix.
        @details
        Create a three letter code for the target platform for the final
        filename for the project. For platforms that support multiple
        CPU architectures, the code will be six letters long with the CPU
        appended to the three letter platform code.

        Returns:
            A three or six letter code for the platform.

        See Also:
            makeprojects.enums._PLATFORMTYPES_CODES
        """

        return _PLATFORMTYPES_CODES.get(self, None)

    def is_windows(self):
        """
        Determine if the platform is windows.

        Returns:
            True if the platform is for Microsoft windows.
        """

        return self in (PlatformTypes.windows, PlatformTypes.windowsintel,
                        PlatformTypes.windowsarm, PlatformTypes.win32,
                        PlatformTypes.win64, PlatformTypes.winarm32,
                        PlatformTypes.winarm64, PlatformTypes.winitanium)

    def is_xbox(self):
        """
        Determine if the platform is a version of the Xbox.

        Returns:
            True if the platform is for Xbox, Xbox 360, or Xbox ONE.
        """

        return self in (PlatformTypes.xbox,
                        PlatformTypes.xbox360, PlatformTypes.xboxone)

    def is_macosx(self):
        """
        Determine if the platform is macOS.

        Returns:
            True if the platform is Apple macOS.
        """

        return self in (PlatformTypes.macosx, PlatformTypes.macosxppc32,
                        PlatformTypes.macosxppc64, PlatformTypes.macosxintel32,
                        PlatformTypes.macosxintel64)

    def is_ios(self):
        """
        Determine if the platform is iOS.

        Returns:
            True if the platform is Apple iOS.
        """

        return self in (PlatformTypes.ios, PlatformTypes.ios32,
                        PlatformTypes.ios64, PlatformTypes.iosemu,
                        PlatformTypes.iosemu32, PlatformTypes.iosemu64)

    def is_macos(self):
        """
        Determine if the platform is MacOS classic or Carbon.

        Returns:
            True if Apple MacOS 1.0 through 9.2.2 or the Carbon API.
        """

        return self.is_macos_classic() or self.is_macos_carbon()

    def is_macos_carbon(self):
        """
        Determine if the platform is MacOS Carbon.

        Returns:
            True if the platform is Apple MacOS Carbon API.
        """
        return self in (PlatformTypes.maccarbon, PlatformTypes.maccarbon68k,
                        PlatformTypes.maccarbonppc)

    def is_macos_classic(self):
        """
        Determine if the platform is MacOS classic (MacOS 1.0 to 9.2.2).

        Returns:
            True if the platform is Apple MacOS 1.0 through 9.2.2.
        """
        return self in (PlatformTypes.macos9,
                        PlatformTypes.macos968k, PlatformTypes.macos9ppc)

    def is_msdos(self):
        """
        Determine if the platform is MSDos.

        Returns:
            True if the platform is MSDos
        """
        return self in (PlatformTypes.msdos,
                        PlatformTypes.msdos4gw, PlatformTypes.msdosx32)

    def is_android(self):
        """
        Determine if the platform is Android.

        Returns:
            True if the platform is Android
        """
        return self in (
            PlatformTypes.android, PlatformTypes.shield, PlatformTypes.ouya,
            PlatformTypes.amico, PlatformTypes.tegra,
            PlatformTypes.androidarm32, PlatformTypes.androidarm64,
            PlatformTypes.androidintel32, PlatformTypes.androidintel64)

    def is_switch(self):
        """
        Determine if the platform is Nintendo Switch.

        Returns:
            True if the platform is Nintendo Switch
        """
        return self in (PlatformTypes.switch,
                        PlatformTypes.switch32, PlatformTypes.switch64)

    def get_platform_folder(self):
        """
        Return the name of a folder that would hold platform specific files.
        """

        table = {
            PlatformTypes.iigs: 'iigs',
            PlatformTypes.beos: 'beos',
            PlatformTypes.ps1: 'ps1',
            PlatformTypes.ps2: 'ps2',
            PlatformTypes.ps3: 'ps3',
            PlatformTypes.ps4: 'ps4',
            PlatformTypes.psp: 'psp',
            PlatformTypes.vita: 'vita',
            PlatformTypes.xbox: 'xbox',
            PlatformTypes.xbox360: 'xbox360',
            PlatformTypes.xboxone: 'xboxone',
            PlatformTypes.ds: 'ds',
            PlatformTypes.dsi: 'dsi',
            PlatformTypes.wii: 'wii',
            PlatformTypes.wiiu: 'wiiu'
        }

        # Try the simple ones
        platform_folder = table.get(self, None)
        if platform_folder is None:
            if self.is_windows():
                platform_folder = 'windows'
            elif self.is_msdos():
                platform_folder = 'dos'
            elif self.is_macosx():
                platform_folder = 'macosx'
            elif self.is_ios():
                platform_folder = 'ios'
            elif self.is_macos():
                platform_folder = 'mac'
            elif self.is_android():
                platform_folder = 'shield'
            elif self.is_switch():
                platform_folder = 'switch'
            elif self is PlatformTypes.ouya:
                platform_folder = 'ouya'
            else:
                platform_folder = 'linux'
        return platform_folder

    def match(self, second):
        """
        Test if two platform types are a match.
        @details
        If two platform types are similar, this function will return True. An
        example would be a windows 32 bit and a windows 64 bit platform would
        match.

        Returns:
            True if the types are compatible.
        """

        # Too many return statements
        # Too many branches
        # pylint: disable=R0911, R0912
        if self == second:
            return True

        # Test using the windows wildcard
        if self == PlatformTypes.windows or second == PlatformTypes.windows:
            return self.is_windows() == second.is_windows()

        # Test macosx
        if self == PlatformTypes.macosx or second == PlatformTypes.macosx:
            return self.is_macosx() == second.is_macosx()

        # Test macos 1.0 - 9.2.2
        if self == PlatformTypes.macos9 or second == PlatformTypes.macos9:
            return self.is_macos_classic() == second.is_macos_classic()

        # Test macos Carbon
        if self == PlatformTypes.maccarbon or second == PlatformTypes.maccarbon:
            return self.is_macos_carbon() == second.is_macos_carbon()

        # Test iOS
        if self == PlatformTypes.ios or second == PlatformTypes.ios:
            return self.is_ios() == second.is_ios()

        # Test MSDos
        if self == PlatformTypes.msdos or second == PlatformTypes.msdos:
            return self.is_msdos() == second.is_msdos()

        # Test Android
        if self == PlatformTypes.android or second == PlatformTypes.android:
            return self.is_android() == second.is_android()
        return False

    def get_vs_platform(self):
        """
        Create the platform codes from the platform type for Visual Studio.
        @details
        Visual Studio uses specific codes for tool chains used for
        video game consoles or CPUs. This function returns a list of
        codes needed to support the requested platform.

        Returns:
            A list of Visual Studio platforms for target.
        See Also:
            makeprojects.enums._PLATFORMTYPES_VS
        """

        return _PLATFORMTYPES_VS.get(self, [])

    def get_expanded(self):
        """
        Return a list of platforms from a platform that is a group.
        """

        return _PLATFORMTYPES_EXPANDED.get(self, [self])

    def is_expandable(self):
        """
        Return True if the platform defines other platforms.
        """

        return self in _PLATFORMTYPES_EXPANDED

    @staticmethod
    def lookup(platform_name):
        """
        Look up a PlatformType based on name.
        @details
        For maximum compatiblity, the name will be scanned from several
        look up tables to attempt to cover all premutations of an input string.

        Note:
            String comparisons are case insensitive.

        Args:
            platform_name: Platform string to test.
        Returns:
            A @ref PlatformTypes member or None on failure.
        See Also:
            makeprojects.enums._PLATFORMTYPES_READABLE
        """

        if isinstance(platform_name, PlatformTypes):
            return platform_name

        # Already a PlatformTypes?
        if platform_name:
            # Try the member name as is.
            test_name = platform_name.lower()
            if hasattr(PlatformTypes, test_name):
                return PlatformTypes[test_name]

            # Try a number of ways to find a match
            for item in _PLATFORMTYPES_READABLE:
                # Verbose name? File name short code?
                if test_name == str(item).lower(
                ) or test_name == _PLATFORMTYPES_CODES[item]:
                    return item

                # Visual studio target type?
                if not item.is_expandable():
                    for vs_name in _PLATFORMTYPES_VS.get(item, ()):
                        if test_name == vs_name.lower():
                            return item

            specials = {
                'macos': PlatformTypes.macos9,
                'carbon': PlatformTypes.maccarbon
            }
            return specials.get(test_name, None)
        return None

    @staticmethod
    def default():
        """
        Determine the PlatformTypes from the currently running platform.
        """

        # Windows host?
        temp = get_windows_host_type()
        if temp:
            win_table = {
                'x86': PlatformTypes.win32,
                'x64': PlatformTypes.win64,
                'arm': PlatformTypes.winarm32,
                'arm64': PlatformTypes.winarm64,
                'ia64': PlatformTypes.winitanium}
            return win_table.get(temp, PlatformTypes.win32)

        # Mac host?
        temp = get_mac_host_type()
        if temp:
            mac_table = {
                'ppc': PlatformTypes.macosxppc32,
                'ppc64': PlatformTypes.macosxppc64,
                'x32': PlatformTypes.macosxintel32,
                'x64': PlatformTypes.macosxintel64}
            return mac_table.get(temp, PlatformTypes.macosxintel64)

        # Unknown platforms default to Linux
        return PlatformTypes.linux

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description.

        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._PLATFORMTYPES_READABLE
        """

        return _PLATFORMTYPES_READABLE.get(self, None)

    ## Allow str() to work.
    __str__ = __repr__


## List of platform short codes.
#
# Dictionary to map PlatformTypes enumerations into a
# three or six letter code to append to a project filename
#
# @sa makeprojects.enums.PlatformTypes.get_short_code

_PLATFORMTYPES_CODES = {
    PlatformTypes.windows: 'win10',         # Windows targets
    PlatformTypes.windowsintel: 'win',
    PlatformTypes.windowsarm: 'winarm',
    PlatformTypes.win32: 'w32',
    PlatformTypes.win64: 'w64',
    PlatformTypes.winarm32: 'wina32',
    PlatformTypes.winarm64: 'wina64',
    PlatformTypes.winitanium: 'winita',
    PlatformTypes.macosx: 'osx',            # Mac OSX targets
    PlatformTypes.macosxppc32: 'osxp32',
    PlatformTypes.macosxppc64: 'osxp64',
    PlatformTypes.macosxintel32: 'osxx86',
    PlatformTypes.macosxintel64: 'osxx64',
    PlatformTypes.macos9: 'mac',            # Mac OS targets (Pre-OSX)
    PlatformTypes.macos968k: 'mac68k',
    PlatformTypes.macos9ppc: 'macppc',
    PlatformTypes.maccarbon: 'car',
    PlatformTypes.maccarbon68k: 'car68k',
    PlatformTypes.maccarbonppc: 'carppc',
    PlatformTypes.ios: 'ios',               # iOS targets
    PlatformTypes.ios32: 'iosa32',
    PlatformTypes.ios64: 'iosa64',
    PlatformTypes.iosemu: 'ioe',
    PlatformTypes.iosemu32: 'ioex86',
    PlatformTypes.iosemu64: 'ioex64',
    PlatformTypes.xbox: 'xbx',              # Microsoft Xbox versions
    PlatformTypes.xbox360: 'x36',
    PlatformTypes.xboxone: 'one',
    PlatformTypes.ps1: 'ps1',               # Sony platforms
    PlatformTypes.ps2: 'ps2',
    PlatformTypes.ps3: 'ps3',
    PlatformTypes.ps4: 'ps4',
    PlatformTypes.psp: 'psp',
    PlatformTypes.vita: 'vit',
    PlatformTypes.ds: '2ds',                 # Nintendo platforms
    PlatformTypes.dsi: 'dsi',
    PlatformTypes.wii: 'wii',
    PlatformTypes.wiiu: 'wiu',
    PlatformTypes.switch: 'swi',
    PlatformTypes.switch32: 'swia32',
    PlatformTypes.switch64: 'swia64',
    PlatformTypes.android: 'and',           # Google platforms
    PlatformTypes.shield: 'shi',
    PlatformTypes.amico: 'ami',
    PlatformTypes.ouya: 'oya',
    PlatformTypes.tegra: 'teg',
    PlatformTypes.androidarm32: 'anda32',
    PlatformTypes.androidarm64: 'anda64',
    PlatformTypes.androidintel32: 'andx32',
    PlatformTypes.androidintel64: 'andx64',
    PlatformTypes.linux: 'lnx',             # Linux platforms
    PlatformTypes.msdos: 'dos',             # MSDOS (Watcom or Codeblocks)
    PlatformTypes.msdos4gw: 'dos4gw',
    PlatformTypes.msdosx32: 'dosx32',
    PlatformTypes.beos: 'beo',              # BeOS
    PlatformTypes.iigs: '2gs'               # Apple IIgs
}

## List of Visual Studio platform codes
#
# Visual Studio uses specific codes for tool chains used for
# video game consoles or CPUs
#
# @sa makeprojects.enums.PlatformTypes.get_vs_platform

_PLATFORMTYPES_VS = {
    # Windows targets
    PlatformTypes.windows: ('Win32', 'x64', 'ARM', 'ARM64'),
    PlatformTypes.windowsintel: ('Win32', 'x64'),
    PlatformTypes.windowsarm: ('ARM', 'ARM64'),
    PlatformTypes.win32: ('Win32',),
    PlatformTypes.win64: ('x64',),
    PlatformTypes.winarm32: ('ARM',),
    PlatformTypes.winarm64: ('ARM64',),
    PlatformTypes.winitanium: ('IA64',),

    # Microsoft Xbox versions
    PlatformTypes.xbox: ('Xbox',),
    PlatformTypes.xbox360: ('Xbox 360',),
    PlatformTypes.xboxone: ('Durango',),

    # Sony platforms
    PlatformTypes.ps3: ('PS3',),
    PlatformTypes.ps4: ('ORBIS',),
    PlatformTypes.vita: ('PSVita',),

    # Nintendo platforms
    PlatformTypes.wiiu: ('Cafe',),
    PlatformTypes.dsi: ('CTR',),
    PlatformTypes.switch: ('NX32', 'NX64'),
    PlatformTypes.switch32: ('NX32',),
    PlatformTypes.switch64: ('NX64',),

    # Google platforms
    PlatformTypes.android: ('Android',),
    PlatformTypes.shield: (
        'Tegra-Android',
        'ARM-Android-NVIDIA',
        'AArch64-Android-NVIDIA',
        'x86-Android-NVIDIA',
        'x64-Android-NVIDIA'),
    PlatformTypes.tegra: ('Tegra-Android',),
    PlatformTypes.androidarm32: ('ARM-Android-NVIDIA',),
    PlatformTypes.androidarm64: ('AArch64-Android-NVIDIA',),
    PlatformTypes.androidintel32: ('x86-Android-NVIDIA',),
    PlatformTypes.androidintel64: ('x64-Android-NVIDIA',)
}

## List of human readable strings
#
# Dictionary to map PlatformTypes enumerations into an human readable string
#
# @sa makeprojects.enums.PlatformTypes.__repr__

_PLATFORMTYPES_READABLE = {
    # Windows targets
    PlatformTypes.windows: 'Microsoft Windows x86, x64, ARM, and ARM64',
    PlatformTypes.windowsintel: 'Microsoft Windows x86 and x64',
    PlatformTypes.windowsarm: 'Microsoft Windows ARM 32 and 64',
    PlatformTypes.win32: 'Microsoft Windows x86',
    PlatformTypes.win64: 'Microsoft Windows x64',
    PlatformTypes.winarm32: 'Microsoft Windows ARM 32',
    PlatformTypes.winarm64: 'Microsoft Windows ARM 64',
    PlatformTypes.winitanium: 'Microsoft Windows Itanium',

    # Mac OSX targets
    PlatformTypes.macosx: 'Apple macOS all CPUs',
    PlatformTypes.macosxppc32: 'Apple macOS PowerPC 32',
    PlatformTypes.macosxppc64: 'Apple macOS PowerPC 64',
    PlatformTypes.macosxintel32: 'Apple macOS x86',
    PlatformTypes.macosxintel64: 'Apple macOS x64',

    # Mac OS targets (Pre-OSX)
    PlatformTypes.macos9: 'Apple MacOS 9 PPC and 68k',
    PlatformTypes.macos968k: 'Apple MacOS 9 68k',
    PlatformTypes.macos9ppc: 'Apple MacOS 9 PowerPC 32',
    PlatformTypes.maccarbon: 'Apple MacOS Carbon',
    PlatformTypes.maccarbon68k: 'Apple MacOS Carbon 68k',
    PlatformTypes.maccarbonppc: 'Apple MacOS Carbon PowerPC 32',

    # iOS targets
    PlatformTypes.ios: 'Apple iOS',
    PlatformTypes.ios32: 'Apple iOS ARM 32',
    PlatformTypes.ios64: 'Apple iOS ARM 64',
    PlatformTypes.iosemu: 'Apple iOS Emulator',
    PlatformTypes.iosemu32: 'Apple iOS Emulator x86',
    PlatformTypes.iosemu64: 'Apple iOS Emulator x64',

    # Microsoft Xbox versions
    PlatformTypes.xbox: 'Microsoft Xbox',
    PlatformTypes.xbox360: 'Microsoft Xbox 360',
    PlatformTypes.xboxone: 'Microsoft Xbox ONE',
    # Sony platforms
    PlatformTypes.ps1: 'Sony PS1',
    PlatformTypes.ps2: 'Sony PS2',
    PlatformTypes.ps3: 'Sony PS3',
    PlatformTypes.ps4: 'Sony PS4',
    PlatformTypes.psp: 'Sony Playstation Portable',
    PlatformTypes.vita: 'Sony Playstation Vita',

    # Nintendo platforms
    PlatformTypes.ds: 'Nintendo 2DS',
    PlatformTypes.dsi: 'Nintendo DSI',
    PlatformTypes.wii: 'Nintendo Wii',
    PlatformTypes.wiiu: 'Nintendo WiiU',
    PlatformTypes.switch: 'Nintendo Switch',
    PlatformTypes.switch32: 'Nintendo Switch 32 bit',
    PlatformTypes.switch64: 'Nintendo Switch 64 bit',

    # Google platforms
    PlatformTypes.android: 'Google Android',
    PlatformTypes.shield: 'nVidia Shield',
    PlatformTypes.amico: 'Intellivision Amico',
    PlatformTypes.ouya: 'Ouya',
    PlatformTypes.tegra: 'nVidia Android Tegra',
    PlatformTypes.androidarm32: 'Android ARM 32',
    PlatformTypes.androidarm64: 'Android ARM 64',
    PlatformTypes.androidintel32: 'Android x86',
    PlatformTypes.androidintel64: 'Android x64',

    # Linux platforms
    PlatformTypes.linux: 'Linux',

    # MSDOS (Watcom or Codeblocks)
    PlatformTypes.msdos: 'MSDos DOS4GW and X32',
    PlatformTypes.msdos4gw: 'MSDos DOS4GW',
    PlatformTypes.msdosx32: 'MSDos X32',

    # BeOS
    PlatformTypes.beos: 'BeOS',
    # Apple IIgs
    PlatformTypes.iigs: 'Apple IIgs'
}

## List of platforms that expand to multiple targets.
#
# Dictionary to map generic PlatformTypes enumerations into lists.
#
# @sa makeprojects.enums.PlatformTypes.get_expanded

_PLATFORMTYPES_EXPANDED = {
    PlatformTypes.windows: (
        PlatformTypes.win32,
        PlatformTypes.win64,
        PlatformTypes.winarm32,
        PlatformTypes.winarm64),
    PlatformTypes.windowsintel: (
        PlatformTypes.win32,
        PlatformTypes.win64),
    PlatformTypes.windowsarm: (
        PlatformTypes.winarm32,
        PlatformTypes.winarm64),
    PlatformTypes.msdos: (
        PlatformTypes.msdosx32,
        PlatformTypes.msdos4gw),
    PlatformTypes.macosx: (
        PlatformTypes.macosxppc32,
        PlatformTypes.macosxppc64,
        PlatformTypes.macosxintel32,
        PlatformTypes.macosxintel64),
    PlatformTypes.macos9: (
        PlatformTypes.macos968k,
        PlatformTypes.macos9ppc),
    PlatformTypes.maccarbon: (
        PlatformTypes.maccarbon68k,
        PlatformTypes.maccarbonppc),
    PlatformTypes.ios: (
        PlatformTypes.ios32,
        PlatformTypes.ios64),
    PlatformTypes.iosemu: (
        PlatformTypes.iosemu32,
        PlatformTypes.iosemu64),
    PlatformTypes.shield: (
        PlatformTypes.tegra,
        PlatformTypes.androidarm32,
        PlatformTypes.androidarm64,
        PlatformTypes.androidintel32,
        PlatformTypes.androidintel64),
    PlatformTypes.android: (
        PlatformTypes.androidarm32,
        PlatformTypes.androidarm64,
        PlatformTypes.androidintel32,
        PlatformTypes.androidintel64),
    PlatformTypes.switch: (
        PlatformTypes.switch32,
        PlatformTypes.switch64
    )
}


########################################

def platformtype_short_code(configurations):
    """
    Iterate over a list of Configurations to determine the short code.

    For files that create multiple platforms, determine if it matches
    a known expandable PlatformType

    Args:
        configurations: List of configurations to scan
    Returns:
        Either '' or the generic short code of the group
        or the first code in the configuration list.
    """

    # None?
    if not configurations:
        return ''

    # Extract the platform codes from all configurations
    codes = []
    for configuration in configurations:
        codes.append(configuration.platform)

    for item in _PLATFORMTYPES_EXPANDED:
        if all(x in codes for x in _PLATFORMTYPES_EXPANDED[item]):
            return item.get_short_code()

    # Return the first entry's short code.
    return codes[0].get_short_code()

########################################


def add_burgerlib(command, **kargs):
    """
    Add burgerlib to a project.

    In a build_rules.py file, the function rules() can call
    this function to add burgerlib to the project.

    Args:
        command: command parameter from rules()
        kargs: kargs parameter from rules()
    Return:
        Zero

    """

    if command == 'configuration_settings':
        # Return the settings for a specific configuation
        configuration = kargs['configuration']

        platform = configuration.platform

        force_short = platform.is_macosx() or platform.is_ios()
        lib_name = 'burger{}'.format(
            configuration.get_suffix(
                force_short=force_short))
        if platform.is_android() or force_short:
            lib_name = 'lib{}.a'.format(lib_name)
        else:
            lib_name = '{}.lib'.format(lib_name)
        configuration.libraries_list.append(lib_name)

        # Linux requires linking in OpenGL
        if platform is PlatformTypes.linux:
            configuration.libraries_list.append('GL')

        lib_dir = '$(BURGER_SDKS)/{}/burgerlib'.format(
            platform.get_platform_folder())
        configuration.library_folders_list.append(lib_dir)

        # Include burger.h, however Codewarrior uses the library folder
        if not configuration.project.solution.ide.is_codewarrior():
            lib_dir = '$(BURGER_SDKS)/{}/burgerlib'.format(
                platform.get_platform_folder())
            configuration.include_folders_list.append(lib_dir)

    return 0
