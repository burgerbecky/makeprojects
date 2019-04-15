#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration types for makeprojects

All enumerations are stored in this package

"""

## \package makeprojects.enums

# Copyright 2013-2019 by Rebecca Ann Heineman becky@burgerbecky.com
#
# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

from __future__ import absolute_import, print_function, unicode_literals
from enum import IntEnum, EnumMeta, _EnumDict
import os

########################################


class AutoEnum(EnumMeta):
    """
    Class to allow auto generation of enumerations

    Using an empty tuple as a value stepper, create the equivalent of a
    C++ enum type. It is derived from enum.EnumMeta.

    See:
        makeprojects.enums.AutoIntEnum

    """

    def __new__(mcs, cls, bases, classdict):
        """
        Create a new instance of this class

        Given an instance of the parent class and a dictionary
        off all entries to be enumerated, go through every entry
        of the dictionary, and find those who have values set to an
        empty tuple and replace those entries with an auto incremented
        value to simulate a C++ style enumeration.

        Args:
            mcs: metaclass instance
            cls: string with the name of this class
            bases: tuple of enum classes to derive from
            classdict: Starting dictionary
        """

        # pylint: disable=W0212
        original_dict = classdict
        classdict = _EnumDict()
        for k, item in original_dict.items():
            classdict[k] = item

        temp = type(classdict)()
        names = set(classdict._member_names)

        # Start the enumeration with this value
        i = 0
        for k in classdict._member_names:

            # Does this entry need assignment?
            # Test by checking for the initial value
            # being set to ().
            item = classdict[k]

            # If not an empty tuple, use the assigned value
            if item != ():
                i = item
            temp[k] = i

            # Increment for the next assigned value
            i += 1

        # Update the dictionary by adding new entries
        for k, item in classdict.items():
            if k not in names:
                temp[k] = item

        # Pass the dictionary up
        return super(AutoEnum, mcs).__new__(mcs, cls, bases, temp)


## @var makeprojects.enums.AutoIntEnum
#
# Integer enumerator
#
# If a class derives from this object, it will become the equivalent of
# a C++ enum class. Every variable declared using an empty tuple as a value
# will be placed in a dict() record with an incremented value assignment
# starting with 0.
#
#
# @code
# class MyEnum(AutoIntEnum):
#    entry = ()
#    another = ()
#
# print("test {}, {}", MyEnum.entry, MyEnum.another)
# @endcode
#
# The above code will print "test 0,1"
#
# @sa makeprojects.enums.AutoEnum

AutoIntEnum = AutoEnum(str('AutoIntEnum'), (IntEnum,), {})


########################################


class FileTypes(AutoIntEnum):
    """
    Enumeration of supported file types for project input

    Each file that is to be added to a project has specific build rules,
    this enumeration helps determine which compiler to invoke to build the file
    if a build step is necessary.
    """

    ## User file type (Unknown)
    user = ()
    ## Non compiling file type
    generic = ()
    ## Compile as C
    c = ()
    ## Compile as C++
    cpp = ()
    ## C/C++ header
    h = ()
    ## Objective-C
    m = ()
    ## XML text file
    xml = ()
    ## Windows resource file
    rc = ()
    ## Mac OS resource file
    r = ()
    ## HLSL DirectX Shader
    hlsl = ()
    ## GLSL OpenGL Shader
    glsl = ()
    ## Xbox 360 DirectX Shader
    x360sl = ()
    ## Playstation Vita CG Shader
    vitacg = ()
    ## Mac OSX Framework
    frameworks = ()
    ## Static libary
    library = ()
    ## Executable file
    exe = ()
    ## XCode configuration file
    xcconfig = ()
    ## X86 assembly source
    x86 = ()
    ## X64 assembly source
    x64 = ()
    ## 6502/65812 assembly source
    a65 = ()
    ## PowerPC assembly source
    ppc = ()
    ## 680x0 assembly source
    a68 = ()
    ## Image files
    image = ()
    ## Windows icon files
    ico = ()
    ## MacOSX icon files
    icns = ()

    @staticmethod
    def lookup(test_name):
        """
        Look up a file name extension and return the type

        Parse the filename extension and match it to a table of known
        extensions and return the enumeration for the file type. The
        test is case insensitive.

        Args:
            test_name: Filename to test
        Returns:
            A @ref FileTypes member or None on failure
        See:
            makeprojects.enums._FILETYPES_LOOKUP
        """

        return _FILETYPES_LOOKUP.get( \
            os.path.splitext(test_name)[1][1:].strip().lower(), None)

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description

        Returns:
            Human readable string or None if the enumeration is invalid
        See:
            makeprojects.enums._FILETYPES_READABLE
        """

        return _FILETYPES_READABLE.get(self, None)

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
    'c': FileTypes.c,                # C/C++ source code
    'cc': FileTypes.cpp,
    'cpp': FileTypes.cpp,
    'c++': FileTypes.cpp,
    'hpp': FileTypes.h,                # C/C++ header files
    'h': FileTypes.h,
    'hh': FileTypes.h,
    'i': FileTypes.h,
    'inc': FileTypes.h,
    'm': FileTypes.m,                # MacOSX / iOS Objective-C
    'plist': FileTypes.xml,            # MacOSX / iOS plist files
    'rc': FileTypes.rc,                # Windows resources
    'r': FileTypes.r,                # MacOS classic resources
    'rsrc': FileTypes.r,
    'hlsl': FileTypes.hlsl,            # DirectX shader files
    'vsh': FileTypes.glsl,            # OpenGL shader files
    'fsh': FileTypes.glsl,
    'glsl': FileTypes.glsl,
    'x360sl': FileTypes.x360sl,        # Xbox 360 shader files
    'vitacg': FileTypes.vitacg,        # PS Vita shader files
    'xml': FileTypes.xml,            # XML data files
    'x86': FileTypes.x86,            # Intel ASM 80x86 source code
    'x64': FileTypes.x64,            # AMD 64 bit source code
    'a65': FileTypes.a65,            # 6502/65816 source code
    'ppc': FileTypes.ppc,            # PowerPC source code
    'a68': FileTypes.a68,            # 680x0 source code
    'ico': FileTypes.ico,            # Windows icon file
    'icns': FileTypes.icns,            # Mac OSX Icon file
    'png': FileTypes.image,            # Art files
    'jpg': FileTypes.image,
    'bmp': FileTypes.image
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
    FileTypes.exe: 'Executable file',
    FileTypes.xcconfig: 'Apple XCode config file',
    FileTypes.x86: 'X86 assembly file',
    FileTypes.x64: 'X64 assembly file',
    FileTypes.a65: '6502/65816 assembly file',
    FileTypes.ppc: 'PowerPC assembly file',
    FileTypes.a68: '680x0 assembly file',
    FileTypes.image: 'Image file',
    FileTypes.ico: 'Windows Icon file',
    FileTypes.icns: 'macOS Icon file'
}

########################################


class ProjectTypes(AutoIntEnum):
    """
    Enumeration of supported project types

    Each configuration can build a specific type of file, this enumeration
    lists out the types of files that can be built.
    """

    ## Code library
    library = ()
    ## Command line tool
    tool = ()
    ## Application
    app = ()
    ## Screen saver
    screensaver = ()
    ## Shared library (DLL)
    sharedlibrary = ()
    ## Empty project
    empty = ()

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description

        Returns:
            Human readable string or None if the enumeration is invalid
        See:
            makeprojects.enums._PROJECTTYPES_READABLE
        """

        return _PROJECTTYPES_READABLE.get(self, None)

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


class ConfigurationTypes(AutoIntEnum):

    """
    Enumeration of supported configuration types

    This is the list of supported default configuration types. All
    custom configurations must derive from these types.
    """

    ## Debug
    debug = ()
    ## Release builds
    release = ()
    ## Internal builds (Debug enabled, full optimizations)
    internal = ()
    ## Profile builds
    profile = ()
    ## Release Link Time Code Generation
    ltcg = ()
    ## Code Analysis
    codeanalysis = ()
    ## Fast cap
    fastcap = ()

    def getshortcode(self):
        """
        Create the platform codes from the platform type for Visual Studio

        Returns:
            A three character platform code or None if not supported.
        See:
            makeprojects.enums._CONFIGURATIONTYPES_CODES
        """

        return _CONFIGURATIONTYPES_CODES.get(self, None)

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description

        Returns:
            Human readable string or None if the enumeration is invalid
        See:
            makeprojects.enums._CONFIGURATIONTYPES_READABLE
        """

        return _CONFIGURATIONTYPES_READABLE.get(self, None)

    __str__ = __repr__

## List of project filename short codes
#
# Dictionary to map ConfigurationTypes enumerations into an
# three letter code to append to a project filename
#
# @sa makeprojects.enums.ConfigurationTypes.getshortcode()


_CONFIGURATIONTYPES_CODES = {
    ConfigurationTypes.debug: 'dbg',
    ConfigurationTypes.release: 'rel',
    ConfigurationTypes.internal: 'int',
    ConfigurationTypes.profile: 'pro',
    ConfigurationTypes.ltcg: 'ltc',
    ConfigurationTypes.codeanalysis: 'cod',
    ConfigurationTypes.fastcap: 'fas'
}


## List of human readable strings
#
# Dictionary to map ConfigurationTypes enumerations into an human readable
# string
#
# @sa makeprojects.enums.ConfigurationTypes.__repr__()

_CONFIGURATIONTYPES_READABLE = {
    ConfigurationTypes.debug: 'Debug',
    ConfigurationTypes.release: 'Release',
    ConfigurationTypes.internal: 'Internal',
    ConfigurationTypes.profile: 'Profile',
    ConfigurationTypes.ltcg: 'Release_LTCG',
    ConfigurationTypes.codeanalysis: 'CodeAnalysis',
    ConfigurationTypes.fastcap: 'Profile_FastCap'
}

########################################


class IDETypes(AutoIntEnum):
    """
    Enumeration of supported IDEs

    All supported IDEs and makefile formats are enumerated here.
    """

    ## Visual studio 2003
    vs2003 = ()
    ## Visual studio 2005
    vs2005 = ()
    ## Visual studio 2008
    vs2008 = ()
    ## Visual studio 2010
    vs2010 = ()
    ## Visual studio 2012
    vs2012 = ()
    ## Visual studio 2013
    vs2013 = ()
    ## Visual studio 2015
    vs2015 = ()
    ## Visual studio 2017
    vs2017 = ()

    ## Open Watcom 1.9 or later
    watcom = ()

    ## Metrowerks Codewarrior 9 / 5.0 (Windows/Mac OS)
    codewarrior50 = ()
    ## Metrowerks Codewarrior 10 / 5.8 (Mac OS Carbon)
    codewarrior58 = ()
    ## Freescale Codewarrior 5.9 (Nintendo DSi)
    codewarrior59 = ()

    ## XCode 3 (PowerPC 3.1.4 is the target version)
    xcode3 = ()
    ## XCode 4
    xcode4 = ()
    ## XCode 5
    xcode5 = ()
    ## XCode 6
    xcode6 = ()
    ## XCode 7
    xcode7 = ()
    ## XCode 8
    xcode8 = ()
    ## XCode 9
    xcode9 = ()

    ## Codeblocks
    codeblocks = ()

    ## nmake
    nmake = ()

    ## make
    make = ()

    ## bazel
    bazel = ()

    def getshortcode(self):
        """
        Create the ide code from the ide type

        Return the three letter code that determines the specfic IDE
        version that the project file is meant for.

        Returns:
            Three letter code specific to the IDE version or None if not supported.
        See:
            makeprojects.enums._IDETYPES_CODES
        """

        return _IDETYPES_CODES.get(self, None)

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description

        Returns:
            Human readable string or None if the enumeration is invalid
        See:
            makeprojects.enums._IDETYPES_READABLE
        """

        return _IDETYPES_READABLE.get(self, None)

    __str__ = __repr__


## List of IDE short codes
#
# Dictionary to map IDETypes enumerations into a
# three letter code to append to a project filename
#
# @sa makeprojects.enums.IDETypes.getshortcode()

_IDETYPES_CODES = {
    IDETypes.vs2003: 'vc7',                # Microsoft Visual Studio
    IDETypes.vs2005: 'vc8',
    IDETypes.vs2008: 'vc9',
    IDETypes.vs2010: 'v10',
    IDETypes.vs2012: 'v12',
    IDETypes.vs2013: 'v13',
    IDETypes.vs2015: 'v15',
    IDETypes.vs2017: 'v17',
    IDETypes.watcom: 'wat',                # Watcom MAKEFILE
    IDETypes.codewarrior50: 'c50',        # Metrowerks / Freescale CodeWarrior
    IDETypes.codewarrior58: 'c58',
    IDETypes.codewarrior59: 'c59',
    IDETypes.xcode3: 'xc3',                # Apple XCode
    IDETypes.xcode4: 'xc4',
    IDETypes.xcode5: 'xc5',
    IDETypes.xcode6: 'xc6',
    IDETypes.xcode7: 'xc7',
    IDETypes.xcode8: 'xc8',
    IDETypes.xcode9: 'xc9',
    IDETypes.codeblocks: 'cdb',            # Codeblocks
    IDETypes.nmake: 'nmk',                # nmake
    IDETypes.make: 'mak',                # make
    IDETypes.bazel: 'bzl'                # Bazel
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
    IDETypes.codeblocks: 'CodeBlocks 13.12',
    IDETypes.nmake: 'GNU make',
    IDETypes.make: 'Linux make',
    IDETypes.bazel: 'Bazel build'
}

########################################


class PlatformTypes(AutoIntEnum):
    """
    Enumeration of supported target platforms

    All supported tool chains for specific platforms are enumerated here.
    """

    ## Windows 32 and 64 bit Intel
    windows = ()
    ## Windows 32 bit intel only
    win32 = ()
    ## Window 64 bit intel only
    win64 = ()

    ## Mac OSX, all CPUs
    macosx = ()
    ## Mac OSX PowerPC 32 bit only
    macosxppc32 = ()
    ## Mac OSX PowerPC 64 bit only
    macosxppc64 = ()
    ## Mac OSX Intel 32 bit only
    macosxintel32 = ()
    ## Mac OSX Intel 64 bit only
    macosxintel64 = ()

    ## Mac OS 9, all CPUs
    macos9 = ()
    ## Mac OS 9 680x0 only
    macos968k = ()
    ## Mac OS 9 PowerPC 32 bit only
    macos9ppc = ()
    ## Mac OS Carbon, all CPUs
    maccarbon = ()
    ## Mac OS Carbon 680x0 only (CFM)
    maccarbon68k = ()
    ## Mac OS Carbon PowerPC 32 bit only
    maccarbonppc = ()

    ## iOS, all CPUs
    ios = ()
    ## iOS 32 bit ARM only
    ios32 = ()
    ## iOS 64 bit ARM only
    ios64 = ()
    ## iOS emulator, all CPUs
    iosemu = ()
    ## iOS emulator 32 bit Intel only
    iosemu32 = ()
    ## iOS emulator 64 bit Intel only
    iosemu64 = ()

    ## Microsoft Xbox classic
    xbox = ()
    ## Microsoft Xbox 360
    xbox360 = ()
    ## Microsoft Xbox ONE
    xboxone = ()

    ## Sony PS3
    ps3 = ()
    ## Sony PS4
    ps4 = ()
    ## Sony Playstation VITA
    vita = ()

    ## Nintendo WiiU
    wiiu = ()
    ## Nintendo Switch
    switch = ()
    ## Nintendo 3DS
    dsi = ()
    ## Nintendo DS
    ds = ()

    ## Generic Android
    android = ()
    ## nVidia SHIELD
    shield = ()
    ## Ouya (Now Razor)
    ouya = ()
    ## Generic Linux
    linux = ()

    ## MSDOS
    msdos = ()
    ## MSDOS Dos4GW
    msdos4gw = ()
    ## MSDOS DosX32
    msdosx32 = ()

    ## BeOS
    beos = ()
    ## Apple IIgs
    iigs = ()

    def getshortcode(self):
        """
        Convert the enumeration to a 3 letter code for filename suffix

        Create a three letter code for the target platform for the final
        filename for the project. For platforms that support multiple
        CPU architectures, the code will be six letters long with the CPU
        appended to the three letter platform code.

        Returns:
            A three or six letter code for the platform.
        See:
            makeprojects.enums._PLATFORMTYPES_CODES
        """

        return _PLATFORMTYPES_CODES.get(self, None)

    def iswindows(self):
        """
        Determine if the platform is windows.

        Returns:
            True if the platform is for Microsoft windows
        """

        return self == self.windows or self == self.win32 or self == self.win64

    def ismacosx(self):
        """
        Determine if the platform is macOS.

        Returns:
            True if the platform is Apple macOS
        """

        return self == self.macosx or self == self.macosxppc32 or \
            self == self.macosxppc64 or \
            self == self.macosxintel32 or self == self.macosxintel64

    def ismacos(self):
        """
        Determine if the platform is MacOS classic or Carbon.

        Returns:
            True if the platform is Apple MacOS 1.0 through 9.2.2 or the Carbon API.
        """

        return self.ismacosclassic() or self.ismacoscarbon()

    def ismacoscarbon(self):
        """
        Determine if the platform is MacOS Carbon.

        Returns:
            True if the platform is Apple MacOS Carbon API.
        """
        return self == self.maccarbon or self == self.maccarbon68k or \
            self == self.maccarbonppc

    def ismacosclassic(self):
        """
        Determine if the platform is MacOS classic (MacOS 1.0 to 9.2.2)

        Returns:
            True if the platform is Apple MacOS 1.0 through 9.2.2.
        """
        return self == self.macos9 or self == self.macos968k or \
            self == self.macos9ppc

    def ismsdos(self):
        """
        Determine if the platform is MSDos

        Returns:
            True if the platform is MSDos
        """
        return self == self.msdos or self == self.msdos4gw or \
            self == self.msdosx32

    @staticmethod
    def match(first, second):
        """
        Test if two platform types are a match

        If two platform types are similar, this function will return True. An
        example would be a windows 32 bit and a windows 64 bit platform would match.

        Returns:
            True if the types are compatible.
        """

        if first == second:
            return True

        # Test using the windows wildcard
        if first == PlatformTypes.windows or second == PlatformTypes.windows:
            if first.iswindows() == second.iswindows():
                return True
        return False

    def getvsplatform(self):
        """
        Create the platform codes from the platform type for Visual Studio

        Visual Studio uses specific codes for tool chains used for
        video game consoles or CPUs. This function returns a list of
        codes needed to support the requested platform.

        Returns:
            A list of Visual Studio platforms for target.
        See:
            makeprojects.enums._PLATFORMTYPES_VS
        """

        return _PLATFORMTYPES_VS.get(self, [])

    def getexpanded(self):
        """
        Return a list of platforms from a platform that's a group
        """

        if self == self.windows:
            return [self.win32, self.win64]
        if self == self.msdos:
            return [self.msdosx32, self.msdos4gw]
        if self == self.macosx:
            return [self.macosxppc32, self.macosxppc64, self.macosxintel32, self.macosxintel64]
        if self == self.macos9:
            return [self.macos968k, self.macos9ppc]
        if self == self.maccarbon:
            return [self.maccarbon68k, self.maccarbonppc]
        if self == self.ios:
            return [self.ios32, self.ios64]
        if self == self.iosemu:
            return [self.iosemu32, self.iosemu64]
        return [self]

    def __repr__(self):
        """
        Convert the enumeration into a human readable file description

        Returns:
            Human readable string or None if the enumeration is invalid
        See:
            makeprojects.enums._PLATFORMTYPES_READABLE
        """

        return _PLATFORMTYPES_READABLE.get(self, None)

    __str__ = __repr__


## List of platform short codes
#
# Dictionary to map PlatformTypes enumerations into a
# three or six letter code to append to a project filename
#
# @sa makeprojects.enums.PlatformTypes.getshortcode()

_PLATFORMTYPES_CODES = {
    PlatformTypes.windows: 'win',        # Windows targets
    PlatformTypes.win32: 'w32',
    PlatformTypes.win64: 'w64',
    PlatformTypes.macosx: 'osx',        # Mac OSX targets
    PlatformTypes.macosxppc32: 'osxp32',
    PlatformTypes.macosxppc64: 'osxp64',
    PlatformTypes.macosxintel32: 'osxx86',
    PlatformTypes.macosxintel64: 'osxx64',
    PlatformTypes.macos9: 'mac',        # Mac OS targets (Pre-OSX)
    PlatformTypes.macos968k: 'mac68k',
    PlatformTypes.macos9ppc: 'macppc',
    PlatformTypes.maccarbon: 'car',
    PlatformTypes.maccarbon68k: 'car68k',
    PlatformTypes.maccarbonppc: 'carppc',
    PlatformTypes.ios: 'ios',            # iOS targets
    PlatformTypes.ios32: 'iosa32',
    PlatformTypes.ios64: 'iosa64',
    PlatformTypes.iosemu: 'ioe',
    PlatformTypes.iosemu32: 'ioex86',
    PlatformTypes.iosemu64: 'ioex64',
    PlatformTypes.xbox: 'xbx',            # Microsoft Xbox versions
    PlatformTypes.xbox360: 'x36',
    PlatformTypes.xboxone: 'one',
    PlatformTypes.ps3: 'ps3',            # Sony platforms
    PlatformTypes.ps4: 'ps4',
    PlatformTypes.vita: 'vit',
    PlatformTypes.wiiu: 'wiu',            # Nintendo platforms
    PlatformTypes.switch: 'swi',
    PlatformTypes.dsi: 'dsi',
    PlatformTypes.ds: '2ds',
    PlatformTypes.android: 'and',        # Google platforms
    PlatformTypes.shield: 'shi',
    PlatformTypes.ouya: 'oya',
    PlatformTypes.linux: 'lnx',            # Linux platforms
    PlatformTypes.msdos: 'dos',            # MSDOS (Watcom or Codeblocks)
    PlatformTypes.msdos4gw: 'dos4gw',
    PlatformTypes.msdosx32: 'dosx32',
    PlatformTypes.beos: 'bos',            # BeOS
    PlatformTypes.iigs: '2gs'            # Apple IIgs
}

## List of Visual Studio platform codes
#
# Visual Studio uses specific codes for tool chains used for
# video game consoles or CPUs
#
# @sa makeprojects.enums.PlatformTypes.getvsplatform()

_PLATFORMTYPES_VS = {
    PlatformTypes.windows: ['Win32', 'x64'],        # Windows targets
    PlatformTypes.win32: ['Win32'],
    PlatformTypes.win64: ['x64'],
    PlatformTypes.xbox: ['Xbox'],                    # Microsoft Xbox versions
    PlatformTypes.xbox360: ['Xbox 360'],
    PlatformTypes.xboxone: ['Xbox ONE'],
    PlatformTypes.ps3: ['PS3'],                        # Sony platforms
    PlatformTypes.ps4: ['ORBIS'],
    PlatformTypes.vita: ['PSVita'],
    PlatformTypes.wiiu: ['Cafe'],                    # Nintendo platforms
    PlatformTypes.dsi: ['CTR'],
    PlatformTypes.switch: ['Switch'],
    PlatformTypes.android: ['Android'],                # Google platforms
    PlatformTypes.shield: ['Tegra-Android', 'ARM-Android-NVIDIA', \
        'AArch64-Android-NVIDIA', 'x86-Android-NVIDIA', 'x64-Android-NVIDIA']
}

## List of human readable strings
#
# Dictionary to map PlatformTypes enumerations into an human readable string
#
# @sa makeprojects.enums.PlatformTypes.__repr__()

_PLATFORMTYPES_READABLE = {
    PlatformTypes.windows: 'Microsoft Windows x86 and x64',        # Windows targets
    PlatformTypes.win32: 'Microsoft Windows x86',
    PlatformTypes.win64: 'Microsoft Windows x64',
    PlatformTypes.macosx: 'Apple macOS all CPUs',        # Mac OSX targets
    PlatformTypes.macosxppc32: 'Apple macOS PowerPC 32',
    PlatformTypes.macosxppc64: 'Apple macOS PowerPC 64',
    PlatformTypes.macosxintel32: 'Apple macOS x86',
    PlatformTypes.macosxintel64: 'Apple macOS x64',
    PlatformTypes.macos9: 'Apple MacOS 9 PPC and 68k',        # Mac OS targets (Pre-OSX)
    PlatformTypes.macos968k: 'Apple MacOS 9 68k',
    PlatformTypes.macos9ppc: 'Apple MacOS 9 PowerPC 32',
    PlatformTypes.maccarbon: 'Apple MacOS Carbon',
    PlatformTypes.maccarbon68k: 'Apple MacOS Carbon 68k',
    PlatformTypes.maccarbonppc: 'Apple MacOS Carbon PowerPC 32',
    PlatformTypes.ios: 'Apple iOS',                    # iOS targets
    PlatformTypes.ios32: 'Apple iOS ARM 32',
    PlatformTypes.ios64: 'Apple iOS ARM 64',
    PlatformTypes.iosemu: 'Apple iOS Emulator',
    PlatformTypes.iosemu32: 'Apple iOS Emulator x86',
    PlatformTypes.iosemu64: 'Apple iOS Emulator x64',
    PlatformTypes.xbox: 'Microsoft Xbox',            # Microsoft Xbox versions
    PlatformTypes.xbox360: 'Microsoft Xbox 360',
    PlatformTypes.xboxone: 'Microsoft Xbox ONE',
    PlatformTypes.ps3: 'Sony PS3',                    # Sony platforms
    PlatformTypes.ps4: 'Sony PS4',
    PlatformTypes.vita: 'Sony Playstation Vita',
    PlatformTypes.wiiu: 'Nintendo WiiU',            # Nintendo platforms
    PlatformTypes.switch: 'Nintendo Switch',
    PlatformTypes.dsi: 'Nintendo DSI',
    PlatformTypes.ds: 'Nintendo 2DS',
    PlatformTypes.android: 'Google Android',        # Google platforms
    PlatformTypes.shield: 'nVidia Shield',
    PlatformTypes.ouya: 'Ouya',
    PlatformTypes.linux: 'Linux',                    # Linux platforms
    PlatformTypes.msdos: 'MSDos DOS4GW and X32',    # MSDOS (Watcom or Codeblocks)
    PlatformTypes.msdos4gw: 'MSDos DOS4GW',
    PlatformTypes.msdosx32: 'MSDos X32',
    PlatformTypes.beos: 'BeOS',                        # BeOS
    PlatformTypes.iigs: 'Apple IIgs'                # Apple IIgs
}
