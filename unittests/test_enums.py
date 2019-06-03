#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeproject IDETypes

Copyright 2013-2019 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

from makeprojects.enums import IDETypes, FileTypes, ProjectTypes, PlatformTypes


########################################


def test_filetypes_lookup():
    """
    Test FileTypes.lookup().
    """
    tests = (
        ('foo.c', FileTypes.c),
        ('foo', None),
        ('foo.txt', FileTypes.generic),
        ('.txt', None),
        ('shader.hlsl', FileTypes.hlsl),
        ('fun.ico', FileTypes.ico),
        ('burger.lib', FileTypes.library),
        ('libburger.a', FileTypes.library),
        ('sound.obj', FileTypes.object),
        ('sound.o', FileTypes.object)
    )

    for test in tests:
        assert FileTypes.lookup(test[0]) == test[1]

########################################


def test_projecttypes_is_library():
    """
    Test ProjectTypes.is_library().
    """

    for item in ProjectTypes:
        if item in (ProjectTypes.library, ProjectTypes.sharedlibrary):
            assert item.is_library()
        else:
            assert not item.is_library()

########################################


def test_projecttypes_lookup():
    """
    Test ProjectTypes.lookup().
    """
    tests = (
        ('dll', ProjectTypes.sharedlibrary),
        ('scr', ProjectTypes.screensaver),
        ('app', ProjectTypes.app),
        ('game', ProjectTypes.app),
        ('tool', ProjectTypes.tool),
        ('console', ProjectTypes.tool),
        ('library', ProjectTypes.library),
        ('lib', ProjectTypes.library)
    )

    for test in tests:
        assert ProjectTypes.lookup(test[0]) == test[1]


########################################


def test_idetypes_is_visual_studio():
    """
    Test IDETypes.is_visual_studio().
    """

    for item in IDETypes:
        if item in (
                IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008,
                IDETypes.vs2010, IDETypes.vs2012, IDETypes.vs2013,
                IDETypes.vs2015, IDETypes.vs2017, IDETypes.vs2019):
            assert item.is_visual_studio()
        else:
            assert not item.is_visual_studio()


########################################


def test_idetypes_is_xcode():
    """
    Test IDETypes.is_xcode().
    """

    for item in IDETypes:
        if item in (IDETypes.xcode3, IDETypes.xcode4, IDETypes.xcode5,
                    IDETypes.xcode6, IDETypes.xcode7, IDETypes.xcode8,
                    IDETypes.xcode9, IDETypes.xcode10):
            assert item.is_xcode()
        else:
            assert not item.is_xcode()


########################################


def test_idetypes_is_codewarrior():
    """
    Test IDETypes.is_codewarrior().
    """

    for item in IDETypes:
        if item in (IDETypes.codewarrior50, IDETypes.codewarrior58,
                    IDETypes.codewarrior59):
            assert item.is_codewarrior()
        else:
            assert not item.is_codewarrior()


########################################


def test_idetypes_lookup():
    """
    Test IDETypes.lookup().
    """

    tests = (
        ('vc7', IDETypes.vs2003),
        ('vs2003', IDETypes.vs2003),
        ('vs2019', IDETypes.vs2019),
        ('codewarrior', IDETypes.codewarrior50),
        ('watcom', IDETypes.watcom)
    )

    for test in tests:
        assert IDETypes.lookup(test[0]) == test[1]

########################################


def test_platformtypes_is_windows():
    """
    Test IDETypes.is_windows().
    """

    for item in PlatformTypes:
        if item in (PlatformTypes.windows, PlatformTypes.win32,
                    PlatformTypes.win64):
            assert item.is_windows()
        else:
            assert not item.is_windows()

########################################


def test_platformtypes_is_macosx():
    """
    Test IDETypes.is_macosx().
    """

    for item in PlatformTypes:
        if item in (PlatformTypes.macosx, PlatformTypes.macosxppc32,
                    PlatformTypes.macosxppc64, PlatformTypes.macosxintel32,
                    PlatformTypes.macosxintel64):
            assert item.is_macosx()
        else:
            assert not item.is_macosx()

########################################


def test_platformtypes_is_ios():
    """
    Test IDETypes.is_ios().
    """

    for item in PlatformTypes:
        if item in (PlatformTypes.ios, PlatformTypes.ios32, PlatformTypes.ios64,
                    PlatformTypes.iosemu, PlatformTypes.iosemu32,
                    PlatformTypes.iosemu64):
            assert item.is_ios()
        else:
            assert not item.is_ios()

########################################


def test_platformtypes_is_macos():
    """
    Test IDETypes.is_macos().
    """

    for item in PlatformTypes:
        if item in (PlatformTypes.macos9, PlatformTypes.macos968k,
                    PlatformTypes.macos9ppc, PlatformTypes.maccarbon,
                    PlatformTypes.maccarbon68k, PlatformTypes.maccarbonppc):
            assert item.is_macos()
        else:
            assert not item.is_macos()

########################################


def test_platformtypes_is_macos_carbon():
    """
    Test IDETypes.is_macos_carbon().
    """

    for item in PlatformTypes:
        if item in (PlatformTypes.maccarbon, PlatformTypes.maccarbon68k,
                    PlatformTypes.maccarbonppc):
            assert item.is_macos_carbon()
        else:
            assert not item.is_macos_carbon()

########################################


def test_platformtypes_is_macos_classic():
    """
    Test IDETypes.is_macos_classic().
    """

    for item in PlatformTypes:
        if item in (PlatformTypes.macos9, PlatformTypes.macos968k,
                    PlatformTypes.macos9ppc):
            assert item.is_macos_classic()
        else:
            assert not item.is_macos_classic()


########################################


def test_platformtypes_lookup():
    """
    Test PlatformTypes.lookup().
    """
    tests = (
        ('windows', PlatformTypes.windows),
        ('win32', PlatformTypes.win32),
        ('w64', PlatformTypes.win64),
        ('macos', PlatformTypes.macos9),
        ('macosx', PlatformTypes.macosx),
        ('carbon', PlatformTypes.maccarbon),
        ('ouya', PlatformTypes.ouya),
        ('switch', PlatformTypes.switch),
        ('xbox one', PlatformTypes.xboxone)
    )

    for test in tests:
        assert PlatformTypes.lookup(test[0]) == test[1]
