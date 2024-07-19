#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeproject core classes

Copyright 2013-2024 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

# pylint: disable=wrong-import-position
# pylint: disable=invalid-name
# pylint: disable=too-many-statements

import sys
import unittest
import os

# Insert the location of makeprojects at the begining so it's the first
# to be processed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from makeprojects.core import Attributes, Configuration, Project, Solution
from makeprojects.enums import PlatformTypes, ProjectTypes, IDETypes

########################################


class TestCore(unittest.TestCase):
    """
    Test core classes
    """

########################################

    def test_attributes(self):
        """
        Test Attributes class.
        """

        a = Attributes()

        # Test parent
        self.assertIsNone(a.parent)

        # Test define_list

        # Must be empty on start
        self.assertEqual(a.define_list, [])
        a.define_list = "a"
        self.assertEqual(a.define_list, ["a"])
        a.define_list = ["a", "b", "c"]
        self.assertEqual(a.define_list, ["a", "b", "c"])
        a.define_list = 1
        self.assertEqual(a.define_list, ["1"])
        a.define_list = [1, 2, 3]
        self.assertEqual(a.define_list, ["1", "2", "3"])
        a.define_list.extend(["a", "b"])
        self.assertEqual(a.define_list, ["1", "2", "3", "a", "b"])

        # Test platform
        self.assertIsNone(a.platform)
        a.platform = "windows"
        self.assertIs(a.platform, PlatformTypes.windows)
        a.platform = PlatformTypes.maccarbon
        self.assertIs(a.platform, PlatformTypes.maccarbon)
        a.platform = "carbon"
        self.assertIs(a.platform, PlatformTypes.maccarbon)
        with self.assertRaises(ValueError):
            a.platform = 1
        with self.assertRaises(TypeError):
            a.platform = "myplatform"
        a.platform = None
        self.assertIsNone(a.platform)

        # Test project_type
        self.assertIsNone(a.project_type)
        a.project_type = "dll"
        self.assertIs(a.project_type, ProjectTypes.sharedlibrary)
        a.project_type = ProjectTypes.app
        self.assertIs(a.project_type, ProjectTypes.app)
        a.project_type = "lib"
        self.assertIs(a.project_type, ProjectTypes.library)
        with self.assertRaises(ValueError):
            a.project_type = 1
        with self.assertRaises(TypeError):
            a.project_type = "myproject_type"
        a.project_type = None
        self.assertIsNone(a.project_type)

        # Test debug (Tests validate_boolean)
        self.assertIsNone(a.debug)
        a.debug = "true"
        self.assertIs(a.debug, True)
        a.debug = "f"
        self.assertIs(a.debug, False)
        a.debug = False
        self.assertIs(a.debug, False)
        a.debug = 1
        self.assertIs(a.debug, True)
        a.debug = 0.0
        self.assertIs(a.debug, False)
        with self.assertRaises(ValueError):
            a.debug = "myproject_type"
        with self.assertRaises(ValueError):
            a.debug = self
        a.debug = None
        self.assertIsNone(a.debug)

        # test link_time_code_generation
        self.assertIsNone(a.link_time_code_generation)
        a.link_time_code_generation = "true"
        self.assertIs(a.link_time_code_generation, True)
        a.link_time_code_generation = "f"
        self.assertIs(a.link_time_code_generation, False)
        a.link_time_code_generation = False
        self.assertIs(a.link_time_code_generation, False)
        with self.assertRaises(ValueError):
            a.link_time_code_generation = "crappy"
        with self.assertRaises(ValueError):
            a.link_time_code_generation = self
        a.link_time_code_generation = None
        self.assertIsNone(a.link_time_code_generation)

        # test optimization
        self.assertIsNone(a.optimization)
        a.optimization = "true"
        self.assertIs(a.optimization, True)
        a.optimization = "f"
        self.assertIs(a.optimization, False)
        a.optimization = False
        self.assertIs(a.optimization, False)
        with self.assertRaises(ValueError):
            a.optimization = "garbage"
        with self.assertRaises(ValueError):
            a.optimization = self
        a.optimization = None
        self.assertIsNone(a.optimization)

        # test analyze
        self.assertIsNone(a.analyze)
        a.analyze = "true"
        self.assertIs(a.analyze, True)
        a.analyze = "false"
        self.assertIs(a.analyze, False)
        a.analyze = False
        self.assertIs(a.analyze, False)
        with self.assertRaises(ValueError):
            a.analyze = "chasm"
        with self.assertRaises(ValueError):
            a.analyze = self
        a.analyze = None
        self.assertIsNone(a.analyze)

        # test use_mfc
        self.assertIsNone(a.use_mfc)
        a.use_mfc = "true"
        self.assertIs(a.use_mfc, True)
        a.use_mfc = "false"
        self.assertIs(a.use_mfc, False)
        a.use_mfc = False
        self.assertIs(a.use_mfc, False)
        with self.assertRaises(ValueError):
            a.use_mfc = "anchovy"
        with self.assertRaises(ValueError):
            a.use_mfc = self
        a.use_mfc = None
        self.assertIsNone(a.use_mfc)

        # test use_mfc
        self.assertIsNone(a.use_atl)
        a.use_atl = "true"
        self.assertIs(a.use_atl, True)
        a.use_atl = "false"
        self.assertIs(a.use_atl, False)
        a.use_atl = False
        self.assertIs(a.use_atl, False)
        with self.assertRaises(ValueError):
            a.use_atl = "garden"
        with self.assertRaises(ValueError):
            a.use_atl = self
        a.use_atl = None
        self.assertIsNone(a.use_atl)

        # test clr_support
        self.assertIsNone(a.clr_support)
        a.clr_support = "true"
        self.assertIs(a.clr_support, True)
        a.clr_support = "n"
        self.assertIs(a.clr_support, False)
        a.clr_support = False
        self.assertIs(a.clr_support, False)
        with self.assertRaises(ValueError):
            a.clr_support = "elvis"
        with self.assertRaises(ValueError):
            a.clr_support = self
        a.clr_support = None
        self.assertIsNone(a.clr_support)

        # test name
        self.assertIsNone(a.name)
        a.name = "projectname"
        self.assertEqual(a.name, "projectname")
        a.name = "new"
        self.assertEqual(a.name, "new")
        with self.assertRaises(ValueError):
            a.name = False
        with self.assertRaises(ValueError):
            a.name = 1
        with self.assertRaises(ValueError):
            a.name = self
        a.name = None
        self.assertIsNone(a.name)

        # test working_directory
        self.assertIsNone(a.working_directory)
        a.working_directory = "c:\\directory"
        self.assertEqual(a.working_directory, "c:\\directory")
        a.working_directory = "temp"
        self.assertEqual(a.working_directory, "temp")
        with self.assertRaises(ValueError):
            a.working_directory = False
        with self.assertRaises(ValueError):
            a.working_directory = 5.0
        with self.assertRaises(ValueError):
            a.working_directory = self
        a.working_directory = None
        self.assertIsNone(a.working_directory)

        # test deploy_folder
        self.assertIsNone(a.deploy_folder)
        a.deploy_folder = "/usr/local/bin"
        self.assertEqual(a.deploy_folder, "/usr/local/bin")
        a.deploy_folder = "temp"
        self.assertEqual(a.deploy_folder, "temp")
        with self.assertRaises(ValueError):
            a.deploy_folder = True
        with self.assertRaises(ValueError):
            a.deploy_folder = 666
        with self.assertRaises(ValueError):
            a.deploy_folder = ValueError
        a.deploy_folder = None
        self.assertIsNone(a.deploy_folder)

        # test fastcall
        self.assertIsNone(a.fastcall)
        a.fastcall = "true"
        self.assertIs(a.fastcall, True)
        a.fastcall = "n"
        self.assertIs(a.fastcall, False)
        a.fastcall = False
        self.assertIs(a.fastcall, False)
        with self.assertRaises(ValueError):
            a.fastcall = "elvis"
        with self.assertRaises(ValueError):
            a.fastcall = self
        a.fastcall = None
        self.assertIsNone(a.fastcall)

########################################

    def test_configuration(self):
        """
        Test Configuration class.
        """

        # Must have a name
        with self.assertRaises(TypeError):
            c = Configuration()

        # Create a configuration
        c = Configuration("Release", None)

        # Test parent
        self.assertIsNone(c.parent)

        # Test ide
        self.assertIsNone(c.ide)
        with self.assertRaises(AttributeError):
            c.ide = False
        with self.assertRaises(AttributeError):
            c.ide = 5.0
        with self.assertRaises(AttributeError):
            c.ide = self
        with self.assertRaises(AttributeError):
            c.ide = None

        # test short_code
        self.assertEqual(c.short_code, "rel")
        c.short_code = "/usr/local/bin"
        self.assertEqual(c.short_code, "/usr/local/bin")
        c.short_code = "temp"
        self.assertEqual(c.short_code, "temp")
        with self.assertRaises(ValueError):
            c.short_code = True
        with self.assertRaises(ValueError):
            c.short_code = 666
        with self.assertRaises(ValueError):
            c.short_code = ValueError
        c.short_code = None
        self.assertEqual(c.short_code, "Release")

########################################

    def test_project(self):
        """
        Test Project class.
        """

        # Create a project
        p = Project()

        # Test ide
        self.assertIsNone(p.ide)
        with self.assertRaises(AttributeError):
            p.ide = False
        with self.assertRaises(AttributeError):
            p.ide = 5.0
        with self.assertRaises(AttributeError):
            p.ide = self
        with self.assertRaises(AttributeError):
            p.ide = None

########################################

    def test_solution(self):
        """
        Test Solution class.
        """

        # Create a solution
        s = Solution()

        # Test ide
        self.assertIsNone(s.ide)
        s.ide = "vs2022"
        self.assertIs(s.ide, IDETypes.vs2022)
        s.ide = IDETypes.xcode11
        self.assertIs(s.ide, IDETypes.xcode11)
        s.ide = "codeblocks"
        self.assertIs(s.ide, IDETypes.codeblocks)
        with self.assertRaises(ValueError):
            s.ide = False
        with self.assertRaises(ValueError):
            s.ide = 5.0
        with self.assertRaises(ValueError):
            s.ide = self
        s.ide = None
        self.assertIsNone(s.ide)


########################################

if __name__ == "__main__":
    unittest.main()
