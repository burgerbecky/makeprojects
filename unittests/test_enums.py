#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit tests for makeproject IDETypes

Copyright 2013-2025 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!
"""

import sys
import unittest
import os

# Insert the location of makeprojects at the begining so it's the first
# to be processed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# pylint: disable=wrong-import-position
from makeprojects.enums import IDETypes, FileTypes, ProjectTypes, PlatformTypes

########################################


class TestEnums(unittest.TestCase):
    """
    Test enums
    """

########################################

    def test_filetypes_lookup(self):
        """
        Test FileTypes.lookup().
        """
        tests = (
            ("foo.c", FileTypes.c),
            ("foo", None),
            ("foo.txt", FileTypes.generic),
            (".txt", None),
            ("shader.hlsl", FileTypes.hlsl),
            ("fun.ico", FileTypes.ico),
            ("burger.lib", FileTypes.library),
            ("libburger.a", FileTypes.library),
            ("sound.obj", FileTypes.object),
            ("sound.o", FileTypes.object)
        )

        for test in tests:
            self.assertEqual(FileTypes.lookup(test[0]), test[1])

########################################

    def test_projecttypes_is_library(self):
        """
        Test ProjectTypes.is_library().
        """

        for item in ProjectTypes:
            if item in (ProjectTypes.library, ProjectTypes.sharedlibrary):
                self.assertTrue(item.is_library())
            else:
                self.assertFalse(item.is_library())

########################################

    def test_projecttypes_lookup(self):
        """
        Test ProjectTypes.lookup().
        """
        tests = (
            ("dll", ProjectTypes.sharedlibrary),
            ("scr", ProjectTypes.screensaver),
            ("app", ProjectTypes.app),
            ("game", ProjectTypes.app),
            ("tool", ProjectTypes.tool),
            ("console", ProjectTypes.tool),
            ("library", ProjectTypes.library),
            ("lib", ProjectTypes.library)
        )

        for test in tests:
            self.assertEqual(ProjectTypes.lookup(test[0]), test[1])

########################################

    def test_idetypes_is_visual_studio(self):
        """
        Test IDETypes.is_visual_studio().
        """

        for item in IDETypes:
            if item in (
                    IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008,
                    IDETypes.vs2010, IDETypes.vs2012, IDETypes.vs2013,
                    IDETypes.vs2015, IDETypes.vs2017, IDETypes.vs2019,
                    IDETypes.vs2022):
                self.assertTrue(item.is_visual_studio())
            else:
                self.assertFalse(item.is_visual_studio())

########################################

    def test_idetypes_is_xcode(self):
        """
        Test IDETypes.is_xcode().
        """

        for item in IDETypes:
            if item in (IDETypes.xcode3, IDETypes.xcode4, IDETypes.xcode5,
                        IDETypes.xcode6, IDETypes.xcode7, IDETypes.xcode8,
                        IDETypes.xcode9, IDETypes.xcode10, IDETypes.xcode11,
                        IDETypes.xcode12, IDETypes.xcode13, IDETypes.xcode14):
                self.assertTrue(item.is_xcode())
            else:
                self.assertFalse(item.is_xcode())

########################################

    def test_idetypes_is_codewarrior(self):
        """
        Test IDETypes.is_codewarrior().
        """

        for item in IDETypes:
            if item in (IDETypes.codewarrior50, IDETypes.codewarrior58,
                        IDETypes.codewarrior59):
                self.assertTrue(item.is_codewarrior())
            else:
                self.assertFalse(item.is_codewarrior())

########################################

    def test_idetypes_lookup(self):
        """
        Test IDETypes.lookup().
        """

        tests = (
            ("vc7", IDETypes.vs2003),
            ("vs2003", IDETypes.vs2003),
            ("vs2019", IDETypes.vs2019),
            ("vs2022", IDETypes.vs2022),
            ("codewarrior", IDETypes.codewarrior50),
            ("watcom", IDETypes.watcom)
        )

        for test in tests:
            self.assertEqual(IDETypes.lookup(test[0]), test[1])

########################################

    def test_platformtypes_is_windows(self):
        """
        Test IDETypes.is_windows().
        """

        for item in PlatformTypes:
            if item in (
                    PlatformTypes.windows,
                    PlatformTypes.windowsarm, PlatformTypes.windowsintel,
                    PlatformTypes.winitanium,
                    PlatformTypes.win32, PlatformTypes.win64,
                    PlatformTypes.winarm32, PlatformTypes.winarm64):
                self.assertTrue(item.is_windows())
            else:
                self.assertFalse(item.is_windows())

########################################

    def test_platformtypes_is_macosx(self):
        """
        Test IDETypes.is_macosx().
        """

        for item in PlatformTypes:
            if item in (PlatformTypes.macosx, PlatformTypes.macosxppc32,
                        PlatformTypes.macosxppc64, PlatformTypes.macosxintel32,
                        PlatformTypes.macosxintel64, PlatformTypes.macosxarm64):
                self.assertTrue(item.is_macosx())
            else:
                self.assertFalse(item.is_macosx())

########################################

    def test_platformtypes_is_ios(self):
        """
        Test IDETypes.is_ios().
        """

        for item in PlatformTypes:
            if item in (PlatformTypes.ios, PlatformTypes.ios32,
                        PlatformTypes.ios64,
                        PlatformTypes.iosemu, PlatformTypes.iosemu32,
                        PlatformTypes.iosemu64):
                self.assertTrue(item.is_ios())
            else:
                self.assertFalse(item.is_ios())

########################################

    def test_platformtypes_is_macos(self):
        """
        Test IDETypes.is_macos().
        """

        for item in PlatformTypes:
            if item in (
                    PlatformTypes.mac, PlatformTypes.mac68k,
                    PlatformTypes.macppc,
                    PlatformTypes.macclassic, PlatformTypes.maccarbon,
                    PlatformTypes.mac68knear, PlatformTypes.mac68knearfp,
                    PlatformTypes.mac68kfar, PlatformTypes.mac68kfarfp,
                    PlatformTypes.mac68kcarbon, PlatformTypes.macppcclassic,
                    PlatformTypes.macppccarbon):
                self.assertTrue(item.is_macos())
            else:
                self.assertFalse(item.is_macos())

########################################

    def test_platformtypes_is_macos_carbon(self):
        """
        Test IDETypes.is_macos_carbon().
        """

        for item in PlatformTypes:
            if item in (PlatformTypes.maccarbon, PlatformTypes.mac68kcarbon,
                        PlatformTypes.macppccarbon):
                self.assertTrue(item.is_macos_carbon())
            else:
                self.assertFalse(item.is_macos_carbon())

########################################

    def test_platformtypes_is_macos_classic(self):
        """
        Test IDETypes.is_macos_classic().
        """

        for item in PlatformTypes:
            if item in (PlatformTypes.mac, PlatformTypes.mac68k,
                        PlatformTypes.macppc, PlatformTypes.macclassic,
                        PlatformTypes.mac68knear, PlatformTypes.mac68knearfp,
                        PlatformTypes.mac68kfar, PlatformTypes.mac68kfarfp,
                        PlatformTypes.macppcclassic):
                self.assertTrue(item.is_macos_classic())
            else:
                self.assertFalse(item.is_macos_classic())

########################################

    def test_platformtypes_lookup(self):
        """
        Test PlatformTypes.lookup().
        """
        tests = (
            ("windows", PlatformTypes.windows),
            ("win32", PlatformTypes.win32),
            ("w64", PlatformTypes.win64),
            ("macos", PlatformTypes.macosx),
            ("macos9", PlatformTypes.macppc),
            ("macosx", PlatformTypes.macosx),
            ("carbon", PlatformTypes.maccarbon),
            ("ouya", PlatformTypes.ouya),
            ("switch", PlatformTypes.switch),
            ("xboxone", PlatformTypes.xboxone),
            ("scarlett", PlatformTypes.xboxonex),
            ("stadia", PlatformTypes.stadia),
            ("ps5", PlatformTypes.ps5)
        )

        for test in tests:
            self.assertEqual(PlatformTypes.lookup(test[0]), test[1])

########################################


if __name__ == "__main__":
    unittest.main()
