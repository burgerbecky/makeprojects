#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2023 by Rebecca Ann Heineman becky@burgerbecky.com
#
# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

"""
Enumeration types for makeprojects

All enumerations are stored in this package

@package makeprojects.enums


@var makeprojects.enums._FILETYPES_LOOKUP
Dictionary of default file extensions and mapped types

When the directory is scanned for input files, the files will be tested
against this list with a forced lowercase filename and determine the type of
compiler to assign to an input file

This list can be appended or modified to allow other file types to be
processed

@sa makeprojects.enums.FileTypes.lookup()


@var makeprojects.enums._FILETYPES_READABLE
List of human readable strings

Dictionary to map FileTypes enumerations into an human readable string

@sa makeprojects.enums.FileTypes.__repr__()


@var makeprojects.enums._PROJECTTYPES_READABLE
List of human readable strings

Dictionary to map ProjectTypes enumerations into an human readable string

@sa makeprojects.enums.ProjectTypes.__repr__()


@var makeprojects.enums._IDETYPES_CODES
List of IDE short codes

Dictionary to map IDETypes enumerations into a
three letter code to append to a project filename

@sa makeprojects.enums.IDETypes.get_short_code()


@var makeprojects.enums._IDETYPES_READABLE
List of human readable strings

Dictionary to map IDETypes enumerations into an human readable string

@sa makeprojects.enums.IDETypes.__repr__()


@var makeprojects.enums._PLATFORMTYPES_CODES
List of platform short codes.

Dictionary to map PlatformTypes enumerations into a
three or six letter code to append to a project filename

@sa makeprojects.enums.PlatformTypes.get_short_code


@var makeprojects.enums._PLATFORMTYPES_VS
List of Visual Studio platform codes

Visual Studio uses specific codes for tool chains used for
video game consoles or CPUs

@sa makeprojects.enums.PlatformTypes.get_vs_platform


@var makeprojects.enums._PLATFORMTYPES_READABLE
List of human readable strings

Dictionary to map PlatformTypes enumerations into an human readable string

@sa makeprojects.enums.PlatformTypes.__repr__


@var makeprojects.enums._PLATFORMTYPES_EXPANDED
List of platforms that expand to multiple targets.

Dictionary to map generic PlatformTypes enumerations into lists.

@sa makeprojects.enums.PlatformTypes.get_expanded
"""

# pylint: disable=too-many-lines
# pylint: disable=invalid-name
# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals
from enum import IntEnum
import os
from burger import get_mac_host_type, get_windows_host_type, \
    where_is_visual_studio, where_is_codeblocks, where_is_watcom, \
    where_is_xcode

from .util import validate_string

########################################


class FileTypes(IntEnum):
    """
    Enumeration of supported file types for project input

    Each file that is to be added to a project has specific build rules,
    this enumeration helps determine which compiler to invoke to build the file
    if a build step is necessary.

    Attributes:
        user: User file type (Unknown)
        generic: Non compiling file type
        c: Compile as C
        cpp: Compile as C++
        h: C/C++ header
        m: Objective-C
        mm: Objective-C++
        xml: XML text file
        rc: Windows resource file
        r: Mac OS resource file
        hlsl: HLSL DirectX Shader
        glsl: GLSL OpenGL Shader
        x360sl: Xbox 360 DirectX Shader
        vitacg: Playstation Vita CG Shader
        frameworks: Mac OSX Framework
        library: Static libary
        object: Object code
        exe: Executable file
        xcconfig: XCode configuration file
        x86: X86 assembly source
        x64: X64 assembly source
        a65: 6502/65812 assembly source
        ppc: PowerPC assembly source
        a68: 680x0 assembly source
        image: Image files
        ico: Windows icon files
        icns: MacOSX icon files
        appxmanifest: Windows AppXManifest files
    """

    user = 0
    generic = 1
    c = 2
    cpp = 3
    h = 4
    m = 5
    mm = 6
    xml = 7
    rc = 8
    r = 9
    hlsl = 10
    glsl = 11
    x360sl = 12
    vitacg = 13
    frameworks = 14
    library = 15
    object = 16
    exe = 17
    xcconfig = 18
    x86 = 19
    x64 = 20
    a65 = 21
    ppc = 22
    a68 = 23
    image = 24
    ico = 25
    icns = 26
    appxmanifest = 27

    @staticmethod
    def lookup(test_name):
        """
        Look up a file name extension and return the type.
        Parse the filename extension and match it to a table of known
        extensions and return the enumeration for the file type. The
        test is case insensitive.

        Args:
            test_name: Filename to test
        Returns:
            A @ref makeprojects.enums.FileTypes member or None on failure
        See Also:
            makeprojects.enums._FILETYPES_LOOKUP
        """

        # Sanity check
        validate_string(test_name)

        return _FILETYPES_LOOKUP.get(
            os.path.splitext(test_name)[1][1:].strip().lower(), None)

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description

        Args:
            self: FileTypes instance
        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._FILETYPES_READABLE
        """

        return _FILETYPES_READABLE.get(self, None)

    def __str__(self):
        """
        Convert the enumeration into a human readable file description

        Args:
            self: FileTypes instance
        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._FILETYPES_READABLE
        """

        return self.__repr__()


_FILETYPES_LOOKUP = {
    "c": FileTypes.c,                   # C/C++ source code
    "cc": FileTypes.cpp,
    "cpp": FileTypes.cpp,
    "c++": FileTypes.cpp,
    "hpp": FileTypes.h,                 # C/C++ header files
    "h": FileTypes.h,
    "hh": FileTypes.h,
    "i": FileTypes.h,
    "inc": FileTypes.h,
    "m": FileTypes.m,                   # MacOSX / iOS Objective-C
    "mm": FileTypes.mm,                 # MacOSX / iOS Objective-C++
    "plist": FileTypes.xml,             # MacOSX / iOS plist files
    "rc": FileTypes.rc,                 # Windows resources
    "r": FileTypes.r,                   # MacOS classic resources
    "rsrc": FileTypes.r,
    "hlsl": FileTypes.hlsl,             # DirectX shader files
    "vsh": FileTypes.glsl,              # OpenGL shader files
    "fsh": FileTypes.glsl,
    "glsl": FileTypes.glsl,
    "x360sl": FileTypes.x360sl,         # Xbox 360 shader files
    "vitacg": FileTypes.vitacg,         # PS Vita shader files
    "lib": FileTypes.library,           # Static library
    "a": FileTypes.library,
    "obj": FileTypes.object,            # .obj object code
    "o": FileTypes.object,
    "xml": FileTypes.xml,               # XML data files
    "x86": FileTypes.x86,               # Intel ASM 80x86 source code
    "x64": FileTypes.x64,               # AMD 64 bit source code
    "a65": FileTypes.a65,               # 6502/65816 source code
    "ppc": FileTypes.ppc,               # PowerPC source code
    "a68": FileTypes.a68,               # 680x0 source code
    "ico": FileTypes.ico,               # Windows icon file
    "icns": FileTypes.icns,             # Mac OSX Icon file
    "png": FileTypes.image,             # Art files
    "jpg": FileTypes.image,
    "bmp": FileTypes.image,
    "txt": FileTypes.generic,           # Text files
    "rtf": FileTypes.generic,
    "rst": FileTypes.generic,
    "md": FileTypes.generic,
    "pdf": FileTypes.generic,
    "sh": FileTypes.generic,
    "cmd": FileTypes.generic,
    "bat": FileTypes.generic,
    "appxmanifest": FileTypes.appxmanifest
}

_FILETYPES_READABLE = {
    FileTypes.user: "User",
    FileTypes.generic: "Generic",
    FileTypes.c: "C source file",
    FileTypes.cpp: "C++ source file",
    FileTypes.h: "C header file",
    FileTypes.m: "Objective-C file",
    FileTypes.mm: "Objective-C++ file",
    FileTypes.xml: "Xml file",
    FileTypes.rc: "Windows Resource file",
    FileTypes.r: "MacOS Resource file",
    FileTypes.hlsl: "DirectX shader file",
    FileTypes.glsl: "OpenGL shader file",
    FileTypes.x360sl: "Xbox 360 shader file",
    FileTypes.vitacg: "Playstation Vita shader file",
    FileTypes.frameworks: "macOS Framework",
    FileTypes.library: "Statically linked library",
    FileTypes.object: "Object code",
    FileTypes.exe: "Executable file",
    FileTypes.xcconfig: "Apple XCode config file",
    FileTypes.x86: "X86 assembly file",
    FileTypes.x64: "X64 assembly file",
    FileTypes.a65: "6502/65816 assembly file",
    FileTypes.ppc: "PowerPC assembly file",
    FileTypes.a68: "680x0 assembly file",
    FileTypes.image: "Image file",
    FileTypes.ico: "Windows Icon file",
    FileTypes.icns: "macOS Icon file",
    FileTypes.appxmanifest: "Windows AppX Manifest file"
}

########################################


def source_file_filter(file_list, file_type_list):
    """
    Prune the file list for a specific type.

    Note: file_type_list can either be a single enums.FileTypes enum or an
        iterable list of enums.FileTypes

    Args:
        file_list: list of core.SourceFile entries.
        file_type_list: enums.FileTypes to match.
    Returns:
        list of matching core.SourceFile entries.
    """

    result_list = []

    # If a single item was passed, use a simple loop
    if isinstance(file_type_list, FileTypes):
        for item in file_list:
            if item.type is file_type_list:
                result_list.append(item)
    else:
        # A list was passed, so test against the list
        for item in file_list:
            if item.type in file_type_list:
                result_list.append(item)
    return result_list

########################################


class ProjectTypes(IntEnum):
    """
    Enumeration of supported project types

    Each configuration can build a specific type of file, this enumeration
    lists out the types of files that can be built.

    Attributes:
        library: Code library
        tool: Command line tool
        app: Application
        screensaver: Screen saver
        sharedlibrary: Shared library (DLL)
        empty: Empty project
    """

    library = 0
    tool = 1
    app = 2
    screensaver = 3
    sharedlibrary = 4
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
            A @ref makeprojects.enums.ProjectTypes member or None on failure.
        """

        # Already a ProjectTypes?
        if isinstance(project_type_name, ProjectTypes):
            return project_type_name

        if project_type_name:

            # Sanity check
            validate_string(project_type_name)

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
                "lib": ProjectTypes.library,
                "game": ProjectTypes.app,
                "dll": ProjectTypes.sharedlibrary,
                "console": ProjectTypes.tool,
                "scr": ProjectTypes.screensaver
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

    def __str__(self):
        """
        Convert the enumeration into a human readable file description

        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._PROJECTTYPES_READABLE
        """

        return self.__repr__()


_PROJECTTYPES_READABLE = {
    ProjectTypes.library: "Library",
    ProjectTypes.tool: "Tool",
    ProjectTypes.app: "Application",
    ProjectTypes.screensaver: "ScreenSaver",
    ProjectTypes.sharedlibrary: "Dynamic Library",
    ProjectTypes.empty: "Empty"
}


########################################


class IDETypes(IntEnum):
    """
    Enumeration of supported IDEs

    All supported IDEs and makefile formats are enumerated here.

    Attributes:
        vs2003: Visual studio 2003
        vs2005: Visual studio 2005
        vs2008: Visual studio 2008
        vs2010: Visual studio 2010
        vs2012: Visual studio 2012
        vs2013: Visual studio 2013
        vs2015: Visual studio 2015
        vs2017: Visual studio 2017
        vs2019: Visual studio 2019
        vs2022: Visual studio 2022

        watcom: Open Watcom 1.9 or later

        codewarrior50: Metrowerks Codewarrior 9 / 5.0 (Windows/Mac OS)
        codewarrior58: Metrowerks Codewarrior 10 / 5.8 (Mac OS Carbon)
        codewarrior59: Freescale Codewarrior 5.9 (Nintendo DSi)

        xcode3: XCode 3 (PowerPC 3.1.4 is the target version)
        xcode4: XCode 4
        xcode5: XCode 5
        xcode6: XCode 6
        xcode7: XCode 7
        xcode8: XCode 8
        xcode9: XCode 9
        xcode10: XCode 10
        xcode11: XCode 11
        xcode12: XCode 12
        xcode13: XCode 13
        xcode14: XCode 14

        codeblocks: Codeblocks

        nmake: nmake

        make: Linux/GNU make

        bazel: Bazel build

        mpw: Apple MPW

        buck: Buck builder

        ninja: Google ninja
    """

    vs2003 = 0
    vs2005 = 1
    vs2008 = 2
    vs2010 = 3
    vs2012 = 4
    vs2013 = 5
    vs2015 = 6
    vs2017 = 7
    vs2019 = 8
    vs2022 = 9

    watcom = 10

    codewarrior50 = 11
    codewarrior58 = 12
    codewarrior59 = 13

    xcode3 = 14
    xcode4 = 15
    xcode5 = 16
    xcode6 = 17
    xcode7 = 18
    xcode8 = 19
    xcode9 = 20
    xcode10 = 21
    xcode11 = 22
    xcode12 = 23
    xcode13 = 24
    xcode14 = 25

    codeblocks = 26

    nmake = 27

    make = 28

    bazel = 29

    mpw = 30

    buck = 31

    ninja = 32

    ########################################

    def get_short_code(self):
        """
        Create the ide code from the ide type.
        Return the three letter code that determines the specfic IDE
        version that the project file is meant for.

        Returns:
            Three letter code specific to the IDE version or None.
        See Also:
            makeprojects.enums._IDETYPES_CODES
        """

        return _IDETYPES_CODES.get(self, None)

    ########################################

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

    ########################################

    def is_xcode(self):
        """
        Determine if the IDE is Apple XCode.

        Returns:
            True if the platform is Apple XCode.
        """

        return self in (
            IDETypes.xcode3, IDETypes.xcode4, IDETypes.xcode5, IDETypes.xcode6,
            IDETypes.xcode7, IDETypes.xcode8, IDETypes.xcode9, IDETypes.xcode10,
            IDETypes.xcode11, IDETypes.xcode12, IDETypes.xcode13, IDETypes.xcode14)

    ########################################

    def is_codewarrior(self):
        """
        Determine if the IDE is Metrowerks / Freescale Codewarrior.

        Returns:
            True if the platform is Metrowerks / Freescale Codewarrior.
        """

        return self in (IDETypes.codewarrior50,
                        IDETypes.codewarrior58, IDETypes.codewarrior59)

    ########################################

    @staticmethod
    def lookup(ide_name):
        """
        Look up a IDETypes based on name.
        For maximum compatiblity, the name will be scanned from several
        look up tables to attempt to cover all premutations of an input string.

        Note:
            String comparisons are case insensitive.

        Args:
            ide_name: Platform string to test.
        Returns:
            A @ref makeprojects.enums.IDETypes member or None on failure.
        """

        # pylint: disable=too-many-return-statements

        # Already a IDETypes?
        if isinstance(ide_name, IDETypes):
            return ide_name

        # Sanity check
        validate_string(ide_name)

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
            if ide_name in ("vs", "visualstudio",
                            "visual_studio", "visual studio"):
                return get_installed_visual_studio()

            if ide_name in ("xcode",):
                return get_installed_xcode()

            if ide_name in ("codewarrior", "metrowerks", "cw", "freescale"):
                return IDETypes.codewarrior50

        return None

    ########################################

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

    ########################################

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description.

        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._IDETYPES_READABLE
        """

        return _IDETYPES_READABLE.get(self, None)

    def __str__(self):
        """
        Convert the enumeration into a human readable file description.

        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._IDETYPES_READABLE
        """

        return self.__repr__()


_IDETYPES_CODES = {
    IDETypes.vs2003: "vc7",                 # Microsoft Visual Studio
    IDETypes.vs2005: "vc8",
    IDETypes.vs2008: "vc9",
    IDETypes.vs2010: "v10",
    IDETypes.vs2012: "v12",
    IDETypes.vs2013: "v13",
    IDETypes.vs2015: "v15",
    IDETypes.vs2017: "v17",
    IDETypes.vs2019: "v19",
    IDETypes.vs2022: "v22",
    IDETypes.watcom: "wat",                 # Watcom MAKEFILE
    IDETypes.codewarrior50: "c50",          # Metrowerks / Freescale CodeWarrior
    IDETypes.codewarrior58: "c58",
    IDETypes.codewarrior59: "c59",
    IDETypes.xcode3: "xc3",                 # Apple XCode
    IDETypes.xcode4: "xc4",
    IDETypes.xcode5: "xc5",
    IDETypes.xcode6: "xc6",
    IDETypes.xcode7: "xc7",
    IDETypes.xcode8: "xc8",
    IDETypes.xcode9: "xc9",
    IDETypes.xcode10: "x10",
    IDETypes.xcode11: "x11",
    IDETypes.xcode12: "x12",
    IDETypes.xcode13: "x13",
    IDETypes.xcode14: "x14",
    IDETypes.codeblocks: "cdb",             # Codeblocks
    IDETypes.nmake: "nmk",                  # nmake
    IDETypes.make: "mak",                   # make
    IDETypes.bazel: "bzl",                  # Bazel
    IDETypes.mpw: "mpw",                    # Apple MPW Make
    IDETypes.buck: "bck",                   # Facebook buck
    IDETypes.ninja: "nin"                   # Google ninja
}

_IDETYPES_READABLE = {
    IDETypes.vs2003: "Visual Studio 2003",
    IDETypes.vs2005: "Visual Studio 2005",
    IDETypes.vs2008: "Visual Studio 2008",
    IDETypes.vs2010: "Visual Studio 2010",
    IDETypes.vs2012: "Visual Studio 2012",
    IDETypes.vs2013: "Visual Studio 2013",
    IDETypes.vs2015: "Visual Studio 2015",
    IDETypes.vs2017: "Visual Studio 2017",
    IDETypes.vs2019: "Visual Studio 2019",
    IDETypes.vs2022: "Visual Studio 2022",
    IDETypes.watcom: "Open Watcom 1.9 wmake",
    IDETypes.codewarrior50: "CodeWarrior 9",
    IDETypes.codewarrior58: "CodeWarrior 10",
    IDETypes.codewarrior59: "Freescale CodeWarrior 5.9",
    IDETypes.xcode3: "XCode 3.1.4",
    IDETypes.xcode4: "XCode 4",
    IDETypes.xcode5: "XCode 5",
    IDETypes.xcode6: "XCode 6",
    IDETypes.xcode7: "XCode 7",
    IDETypes.xcode8: "XCode 8",
    IDETypes.xcode9: "XCode 9",
    IDETypes.xcode10: "XCode 10",
    IDETypes.xcode11: "XCode 11",
    IDETypes.xcode12: "XCode 12",
    IDETypes.xcode13: "XCode 13",
    IDETypes.xcode14: "XCode 14",
    IDETypes.codeblocks: "CodeBlocks 13.12",
    IDETypes.nmake: "GNU make",
    IDETypes.make: "Linux make",
    IDETypes.bazel: "Bazel build",
    IDETypes.mpw: "Apple MPW make",
    IDETypes.buck: "Facebook buck",
    IDETypes.ninja: "Google ninja"
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
        (14, IDETypes.xcode14),
        (13, IDETypes.xcode13),
        (12, IDETypes.xcode12),
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

    Attributes:
        windows: Windows 32 and 64 bit Intel and arm64
        windowsintel: Windows 32 and 64 bit Intel
        windowsarm: Windows 32 and 64 bit arm
        win32: Windows 32 bit intel only
        win64: Window 64 bit intel only
        winarm32: Windows 32 bit arm only
        winarm64: Windows 64 bit arm only
        winitanium: Windows 64 bit itanium only

        macosx: Mac OSX, all CPUs
        macosxppc32: Mac OSX PowerPC 32 bit only
        macosxppc64: Mac OSX PowerPC 64 bit only
        macosxintel32: Mac OSX Intel 32 bit only
        macosxintel64: Mac OSX Intel 64 bit only
        macosxarm64: Mac OSX ARM 64 bit only

        macos9: Mac OS 9, all CPUs
        macos968k: Mac OS 9 680x0 only
        macos9ppc: Mac OS 9 PowerPC 32 bit only
        maccarbon: Mac OS Carbon, all CPUs
        maccarbon68k: Mac OS Carbon 680x0 only (CFM)
        maccarbonppc: Mac OS Carbon PowerPC 32 bit only

        ios: iOS, all CPUs
        ios32: iOS 32 bit ARM only
        ios64: iOS 64 bit ARM only
        iosemu: iOS emulator, all CPUs
        iosemu32: iOS emulator 32 bit Intel only
        iosemu64: iOS emulator 64 bit Intel only

        xbox: Microsoft Xbox classic
        xbox360: Microsoft Xbox 360
        xboxone: Microsoft Xbox ONE
        xboxgdk: Microsoft Xbox ONE GDK
        xboxonex: Microsoft Xbox ONE Series X GDK

        ps1: Sony PS1
        ps2: Sony PS2
        ps3: Sony PS3
        ps4: Sony PS4
        ps5: Sony PS5
        psp: Sony Playstation portable
        vita: Sony Playstation VITA

        wii: Nintendi Wii
        wiiu: Nintendo WiiU
        switch: Nintendo Switch
        switch32: Nintendo Switch 32 bit only
        switch64: Nintendo Switch 64 bit only

        dsi: Nintendo 3DS
        ds: Nintendo DS

        stadia: Google Stadia
        android: Generic Android
        shield: nVidia SHIELD
        amico: Intellivision Amico
        ouya: Ouya (Now Razor)
        tegra: Android Tegra
        androidarm32: Android Arm32
        androidarm64: Android Arm64
        androidintel32: Android Intel x32
        androidintel64: Android Intel / AMD 64

        linux: Generic Linux

        msdos: MSDOS
        msdos4gw: MSDOS Dos4GW
        msdosx32: MSDOS DosX32

        beos: BeOS
        iigs: Apple IIgs
    """

    # pylint: disable=too-many-public-methods

    windows = 0
    windowsintel = 1
    windowsarm = 2
    win32 = 3
    win64 = 4
    winarm32 = 5
    winarm64 = 6
    winitanium = 7

    macosx = 8
    macosxppc32 = 9
    macosxppc64 = 10
    macosxintel32 = 11
    macosxintel64 = 12
    macosxarm64 = 13

    macos9 = 14
    macos968k = 15
    macos9ppc = 16
    maccarbon = 17
    maccarbon68k = 18
    maccarbonppc = 19

    ios = 20
    ios32 = 21
    ios64 = 22
    iosemu = 23
    iosemu32 = 24
    iosemu64 = 25

    xbox = 26
    xbox360 = 27
    xboxone = 28
    xboxgdk = 29
    xboxonex = 30

    ps1 = 31
    ps2 = 32
    ps3 = 33
    ps4 = 34
    ps5 = 35
    psp = 36
    vita = 37

    wii = 38
    wiiu = 39
    switch = 40
    switch32 = 41
    switch64 = 42

    dsi = 43
    ds = 44

    stadia = 45
    android = 46
    shield = 47
    amico = 48
    ouya = 49
    tegra = 50
    androidarm32 = 51
    androidarm64 = 52
    androidintel32 = 53
    androidintel64 = 54

    linux = 55

    msdos = 56
    msdos4gw = 57
    msdosx32 = 58

    beos = 59

    iigs = 60

    def get_short_code(self):
        """
        Convert the enumeration to a 3 letter code for filename suffix.
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

        return self in (PlatformTypes.xbox, PlatformTypes.xbox360,
                        PlatformTypes.xboxone, PlatformTypes.xboxgdk, PlatformTypes.xboxonex)

    def is_xboxone(self):
        """
        Determine if the platform is a version of the Xbox ONE.

        Returns:
            True if the platform is for Xbox ONE.
        """

        return self in (PlatformTypes.xboxone, PlatformTypes.xboxgdk, PlatformTypes.xboxonex)

    def is_microsoft(self):
        """
        Determine if the platform is a Microsoft platform.

        Returns:
            True if the platform is for Xbox, or Windows.
        """

        return self.is_windows() or self.is_xbox() or self.is_msdos()

    def is_macosx(self):
        """
        Determine if the platform is macOS.

        Returns:
            True if the platform is Apple macOS.
        """

        return self in (PlatformTypes.macosx, PlatformTypes.macosxppc32,
                        PlatformTypes.macosxppc64, PlatformTypes.macosxintel32,
                        PlatformTypes.macosxintel64, PlatformTypes.macosxarm64)

    def is_ios(self):
        """
        Determine if the platform is iOS.

        Returns:
            True if the platform is Apple iOS.
        """

        return self in (PlatformTypes.ios, PlatformTypes.ios32,
                        PlatformTypes.ios64, PlatformTypes.iosemu,
                        PlatformTypes.iosemu32, PlatformTypes.iosemu64)

    def is_darwin(self):
        """
        Determine if the platform supports Darwin.

        Returns:
            True if the platform is Apple iOS or macOS X.
        """

        return self.is_ios() or self.is_macosx()

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

    def is_nintendo(self):
        """
        Determine if the platform is from Nintendo.

        Returns:
            True if it's a Nintendo platform
        """
        return self.is_switch() or self in (PlatformTypes.wii, PlatformTypes.wiiu,
            PlatformTypes.ds, PlatformTypes.dsi)

    def is_sony(self):
        """
        Determine if it is a Sony platform.

        Returns:
            True if the platform is one from Sony
        """
        return self in (PlatformTypes.ps1, PlatformTypes.ps2, PlatformTypes.ps3,
            PlatformTypes.ps4, PlatformTypes.ps5, PlatformTypes.vita)

    def get_platform_folder(self):
        """
        Return the name of a folder that would hold platform specific files.

        Returns:
            String of the name of the folder name, or None if not found.
        """

        # pylint: disable=too-many-return-statements

        table = {
            PlatformTypes.iigs: "iigs",
            PlatformTypes.beos: "beos",
            PlatformTypes.ps1: "ps1",
            PlatformTypes.ps2: "ps2",
            PlatformTypes.ps3: "ps3",
            PlatformTypes.ps4: "ps4",
            PlatformTypes.ps5: "ps5",
            PlatformTypes.psp: "psp",
            PlatformTypes.vita: "psvita",
            PlatformTypes.xbox: "xbox",
            PlatformTypes.xbox360: "xbox360",
            PlatformTypes.ds: "ds",
            PlatformTypes.dsi: "dsi",
            PlatformTypes.wii: "wii",
            PlatformTypes.wiiu: "wiiu",
            PlatformTypes.stadia: "stadia"
        }

        # Try the simple ones
        platform_folder = table.get(self, None)
        if platform_folder is not None:
            return platform_folder
        if self.is_windows():
            return "windows"
        if self.is_xboxone():
            return "xboxone"
        if self.is_msdos():
            return "msdos"
        if self.is_macosx():
            return "macosx"
        if self.is_ios():
            return "ios"
        if self.is_macos():
            return "mac"
        if self is PlatformTypes.ouya:
            return "ouya"
        if self is PlatformTypes.shield:
            return "shield"
        if self.is_android():
            return "android"
        if self.is_switch():
            return "switch"
        return "linux"

    def match(self, second):
        """
        Test if two platform types are a match.
        If two platform types are similar, this function will return True. An
        example would be a windows 32 bit and a windows 64 bit platform would
        match.

        Returns:
            True if the types are compatible.
        """

        # pylint: disable=too-many-return-statements

        if self == second:
            return True

        # Test using the windows wildcard
        if PlatformTypes.windows in (self, second):
            return self.is_windows() == second.is_windows()

        # Test macosx
        if PlatformTypes.macosx in (self, second):
            return self.is_macosx() == second.is_macosx()

        # Test macos 1.0 - 9.2.2
        if PlatformTypes.macos9 in (self, second):
            return self.is_macos_classic() == second.is_macos_classic()

        # Test macos Carbon
        if PlatformTypes.maccarbon in (self, second):
            return self.is_macos_carbon() == second.is_macos_carbon()

        # Test iOS
        if PlatformTypes.ios in (self, second):
            return self.is_ios() == second.is_ios()

        # Test MSDos
        if PlatformTypes.msdos in (self, second):
            return self.is_msdos() == second.is_msdos()

        # Test Android
        if PlatformTypes.android in (self, second):
            return self.is_android() == second.is_android()
        return False

    def get_vs_platform(self):
        """
        Create the platform codes from the platform type for Visual Studio.
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

        Returns:
            A tuple of PlatformTypes
        """

        return _PLATFORMTYPES_EXPANDED.get(self, [self])

    def is_expandable(self):
        """
        Return True if the platform defines other platforms.

        Returns:
            True or False
        """

        return self in _PLATFORMTYPES_EXPANDED

    @staticmethod
    def lookup(platform_name):
        """
        Look up a PlatformType based on name.
        For maximum compatiblity, the name will be scanned from several
        look up tables to attempt to cover all premutations of an input string.

        Note:
            String comparisons are case insensitive.

        Args:
            platform_name: Platform string to test.
        Returns:
            A @ref makeprojects.enums.PlatformTypes member or None on failure.
        See Also:
            makeprojects.enums._PLATFORMTYPES_READABLE
        """

        if isinstance(platform_name, PlatformTypes):
            return platform_name

        # Already a PlatformTypes?
        if platform_name:

            # Sanity check
            validate_string(platform_name)

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
                "macos": PlatformTypes.macos9,
                "carbon": PlatformTypes.maccarbon,
                "scarlett": PlatformTypes.xboxonex
            }
            return specials.get(test_name, None)
        return None

    @staticmethod
    def default():
        """
        Determine the PlatformTypes from the currently running platform.

        Returns:
            PlatformTypes.windows, PlatformTypes.macosx, or PlatformTypes.linux
        """

        # Windows host?
        if get_windows_host_type():
            return PlatformTypes.windows

        # Mac host?
        if get_mac_host_type():
            return PlatformTypes.macosx

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

    def __str__(self):
        """
        Convert the enumeration into a human readable file description.

        Returns:
            Human readable string or None if the enumeration is invalid
        See Also:
            makeprojects.enums._PLATFORMTYPES_READABLE
        """

        return self.__repr__()


_PLATFORMTYPES_CODES = {
    PlatformTypes.windows: "win10",         # Windows targets
    PlatformTypes.windowsintel: "win",
    PlatformTypes.windowsarm: "winarm",
    PlatformTypes.win32: "w32",
    PlatformTypes.win64: "w64",
    PlatformTypes.winarm32: "wina32",
    PlatformTypes.winarm64: "wina64",
    PlatformTypes.winitanium: "winita",
    PlatformTypes.macosx: "osx",            # Mac OSX targets
    PlatformTypes.macosxppc32: "osxp32",
    PlatformTypes.macosxppc64: "osxp64",
    PlatformTypes.macosxintel32: "osxx86",
    PlatformTypes.macosxintel64: "osxx64",
    PlatformTypes.macosxarm64: "osxa64",
    PlatformTypes.macos9: "mac",            # Mac OS targets (Pre-OSX)
    PlatformTypes.macos968k: "mac68k",
    PlatformTypes.macos9ppc: "macppc",
    PlatformTypes.maccarbon: "car",
    PlatformTypes.maccarbon68k: "car68k",
    PlatformTypes.maccarbonppc: "carppc",
    PlatformTypes.ios: "ios",               # iOS targets
    PlatformTypes.ios32: "iosa32",
    PlatformTypes.ios64: "iosa64",
    PlatformTypes.iosemu: "ioe",
    PlatformTypes.iosemu32: "ioex86",
    PlatformTypes.iosemu64: "ioex64",
    PlatformTypes.xbox: "xbx",              # Microsoft Xbox versions
    PlatformTypes.xbox360: "x36",
    PlatformTypes.xboxone: "one",
    PlatformTypes.xboxgdk: "gdk",
    PlatformTypes.xboxonex: "gdx",
    PlatformTypes.ps1: "ps1",               # Sony platforms
    PlatformTypes.ps2: "ps2",
    PlatformTypes.ps3: "ps3",
    PlatformTypes.ps4: "ps4",
    PlatformTypes.ps5: "ps5",
    PlatformTypes.psp: "psp",
    PlatformTypes.vita: "vit",
    PlatformTypes.ds: "2ds",                 # Nintendo platforms
    PlatformTypes.dsi: "dsi",
    PlatformTypes.wii: "wii",
    PlatformTypes.wiiu: "wiu",
    PlatformTypes.switch: "swi",
    PlatformTypes.switch32: "swia32",
    PlatformTypes.switch64: "swia64",
    PlatformTypes.stadia: "sta",            # Google platforms
    PlatformTypes.android: "and",
    PlatformTypes.shield: "shi",
    PlatformTypes.amico: "ami",
    PlatformTypes.ouya: "oya",
    PlatformTypes.tegra: "teg",
    PlatformTypes.androidarm32: "anda32",
    PlatformTypes.androidarm64: "anda64",
    PlatformTypes.androidintel32: "andx32",
    PlatformTypes.androidintel64: "andx64",
    PlatformTypes.linux: "lnx",             # Linux platforms
    PlatformTypes.msdos: "dos",             # MSDOS (Watcom or Codeblocks)
    PlatformTypes.msdos4gw: "dos4gw",
    PlatformTypes.msdosx32: "dosx32",
    PlatformTypes.beos: "beo",              # BeOS
    PlatformTypes.iigs: "2gs"               # Apple IIgs
}

_PLATFORMTYPES_VS = {
    # Windows targets
    PlatformTypes.windows: ("Win32", "x64", "ARM", "ARM64"),
    PlatformTypes.windowsintel: ("Win32", "x64"),
    PlatformTypes.windowsarm: ("ARM", "ARM64"),
    PlatformTypes.win32: ("Win32",),
    PlatformTypes.win64: ("x64",),
    PlatformTypes.winarm32: ("ARM",),
    PlatformTypes.winarm64: ("ARM64",),
    PlatformTypes.winitanium: ("IA64",),

    # Microsoft Xbox versions
    PlatformTypes.xbox: ("Xbox",),
    PlatformTypes.xbox360: ("Xbox 360",),
    PlatformTypes.xboxone: ("Durango",),
    PlatformTypes.xboxgdk: ("Gaming.Xbox.XboxOne.x64",),
    PlatformTypes.xboxonex: ("Gaming.Xbox.Scarlett.x64",),

    # Sony platforms
    PlatformTypes.ps3: ("PS3",),
    PlatformTypes.ps4: ("ORBIS",),
    PlatformTypes.ps5: ("Prospero",),
    PlatformTypes.vita: ("PSVita",),

    # Nintendo platforms
    PlatformTypes.wiiu: ("Cafe",),
    PlatformTypes.dsi: ("CTR",),
    PlatformTypes.switch: ("NX32", "NX64"),
    PlatformTypes.switch32: ("NX32",),
    PlatformTypes.switch64: ("NX64",),

    # Google platforms
    PlatformTypes.stadia: ("GGP",),
    PlatformTypes.android: ("Android",),
    PlatformTypes.shield: (
        "Tegra-Android",
        "ARM-Android-NVIDIA",
        "AArch64-Android-NVIDIA",
        "x86-Android-NVIDIA",
        "x64-Android-NVIDIA"),
    PlatformTypes.tegra: ("Tegra-Android",),
    PlatformTypes.androidarm32: ("ARM-Android-NVIDIA",),
    PlatformTypes.androidarm64: ("AArch64-Android-NVIDIA",),
    PlatformTypes.androidintel32: ("x86-Android-NVIDIA",),
    PlatformTypes.androidintel64: ("x64-Android-NVIDIA",)
}

_PLATFORMTYPES_READABLE = {
    # Windows targets
    PlatformTypes.windows: "Microsoft Windows x86, x64, ARM, and ARM64",
    PlatformTypes.windowsintel: "Microsoft Windows x86 and x64",
    PlatformTypes.windowsarm: "Microsoft Windows ARM 32 and 64",
    PlatformTypes.win32: "Microsoft Windows x86",
    PlatformTypes.win64: "Microsoft Windows x64",
    PlatformTypes.winarm32: "Microsoft Windows ARM 32",
    PlatformTypes.winarm64: "Microsoft Windows ARM 64",
    PlatformTypes.winitanium: "Microsoft Windows Itanium",

    # Mac OSX targets
    PlatformTypes.macosx: "Apple macOS all CPUs",
    PlatformTypes.macosxppc32: "Apple macOS PowerPC 32",
    PlatformTypes.macosxppc64: "Apple macOS PowerPC 64",
    PlatformTypes.macosxintel32: "Apple macOS x86",
    PlatformTypes.macosxintel64: "Apple macOS x64",
    PlatformTypes.macosxarm64: "Apple macOS ARM 64",

    # Mac OS targets (Pre-OSX)
    PlatformTypes.macos9: "Apple MacOS 9 PPC and 68k",
    PlatformTypes.macos968k: "Apple MacOS 9 68k",
    PlatformTypes.macos9ppc: "Apple MacOS 9 PowerPC 32",
    PlatformTypes.maccarbon: "Apple MacOS Carbon",
    PlatformTypes.maccarbon68k: "Apple MacOS Carbon 68k",
    PlatformTypes.maccarbonppc: "Apple MacOS Carbon PowerPC 32",

    # iOS targets
    PlatformTypes.ios: "Apple iOS",
    PlatformTypes.ios32: "Apple iOS ARM 32",
    PlatformTypes.ios64: "Apple iOS ARM 64",
    PlatformTypes.iosemu: "Apple iOS Emulator",
    PlatformTypes.iosemu32: "Apple iOS Emulator x86",
    PlatformTypes.iosemu64: "Apple iOS Emulator x64",

    # Microsoft Xbox versions
    PlatformTypes.xbox: "Microsoft Xbox",
    PlatformTypes.xbox360: "Microsoft Xbox 360",
    PlatformTypes.xboxone: "Microsoft Xbox ONE",
    PlatformTypes.xboxgdk: "Microsoft Xbox ONE GDK",
    PlatformTypes.xboxonex: "Microsoft Xbox ONE Series X GDK",

    # Sony platforms
    PlatformTypes.ps1: "Sony PS1",
    PlatformTypes.ps2: "Sony PS2",
    PlatformTypes.ps3: "Sony PS3",
    PlatformTypes.ps4: "Sony PS4",
    PlatformTypes.ps5: "Sony PS5",
    PlatformTypes.psp: "Sony Playstation Portable",
    PlatformTypes.vita: "Sony Playstation Vita",

    # Nintendo platforms
    PlatformTypes.ds: "Nintendo 2DS",
    PlatformTypes.dsi: "Nintendo DSI",
    PlatformTypes.wii: "Nintendo Wii",
    PlatformTypes.wiiu: "Nintendo WiiU",
    PlatformTypes.switch: "Nintendo Switch",
    PlatformTypes.switch32: "Nintendo Switch 32 bit",
    PlatformTypes.switch64: "Nintendo Switch 64 bit",

    # Google platforms
    PlatformTypes.stadia: "Google Stadia",
    PlatformTypes.android: "Google Android",
    PlatformTypes.shield: "nVidia Shield",
    PlatformTypes.amico: "Intellivision Amico",
    PlatformTypes.ouya: "Ouya",
    PlatformTypes.tegra: "nVidia Android Tegra",
    PlatformTypes.androidarm32: "Android ARM 32",
    PlatformTypes.androidarm64: "Android ARM 64",
    PlatformTypes.androidintel32: "Android x86",
    PlatformTypes.androidintel64: "Android x64",

    # Linux platforms
    PlatformTypes.linux: "Linux",

    # MSDOS (Watcom or Codeblocks)
    PlatformTypes.msdos: "MSDos DOS4GW and X32",
    PlatformTypes.msdos4gw: "MSDos DOS4GW",
    PlatformTypes.msdosx32: "MSDos X32",

    # BeOS
    PlatformTypes.beos: "BeOS",
    # Apple IIgs
    PlatformTypes.iigs: "Apple IIgs"
}

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
        PlatformTypes.macosxintel64,
        PlatformTypes.macosxarm64),
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
        return ""

    # Extract the platform codes from all configurations
    codes = []
    for configuration in configurations:
        codes.append(configuration.platform)

    for item in _PLATFORMTYPES_EXPANDED.items():
        if all(x in codes for x in item[1]):
            return item[0].get_short_code()

    # Return the first entry's short code.
    return codes[0].get_short_code()

########################################


def get_output_template(project_type, platform):
    """
    Determine the file prefix and suffix for the binary.

    Using the project type and platform, determine if the final binary name
    template so that if the output was used with format(), it will create the
    binary filename appropriate for the platform.

    Args:
        project_type: ProjectTypes enum
        platform: PlatformTypes enum

    Returns:
        String to be used with format() to create the final name.
    """

    # pylint: disable=too-many-return-statements

    # Empty projects don't need processing
    if project_type is ProjectTypes.empty:
        return "{}"

    # Handle static libraries
    if project_type is ProjectTypes.library:

        # Microsoft platforms use .lib
        if platform.is_microsoft():
            return "{}.lib"

        return "lib{}.a"

    # Handle shared libraries
    # Seems no one can agree to naming convention
    if project_type is ProjectTypes.sharedlibrary:
        if platform.is_switch():
            return "lib{}.nro"

        if platform.is_sony():
            return "lib{}.prx"

        if platform.is_darwin():
            return "lib{}.dylib"

        if platform.is_microsoft():
            return "{}.dll"

        return "lib{}.so"

    # Handle executables

    if platform.is_switch():
        return "{}.nso"

    if platform.is_windows() or platform.is_msdos():
        return "{}.exe"

    if platform.is_xbox():
        return "{}.xex"

    # All other cases
    return "{}"


########################################


def add_burgerlib(configuration):
    """
    Add burgerlib to a project.

    In a build_rules.py file, the function rules() can call
    this function to add burgerlib to the project.

    Args:
        configuration: Configuration to modify
    Returns:
        Zero

    """

    # Return the settings for a specific configuation

    platform = configuration.platform

    force_short = platform.is_darwin()
    lib_name = "burger{}".format(
        configuration.get_suffix(
            force_short=force_short))
    if platform.is_android() or platform is PlatformTypes.linux or force_short:
        lib_name = "lib{}.a".format(lib_name)
    else:
        lib_name = "{}.lib".format(lib_name)
    configuration.libraries_list.append(lib_name)

    # Linux requires linking in OpenGL
    if platform is PlatformTypes.linux:
        configuration.libraries_list.append("GL")

    lib_dir = "$(BURGER_SDKS)/{}/burgerlib".format(
        platform.get_platform_folder())
    configuration.library_folders_list.append(lib_dir)

    # Include burger.h, however Codewarrior uses the library folder
    if not configuration.project.solution.ide.is_codewarrior():
        lib_dir = "$(BURGER_SDKS)/{}/burgerlib".format(
            platform.get_platform_folder())
        configuration.include_folders_list.append(lib_dir)

    return 0
