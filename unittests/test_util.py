#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeproject util functions

Copyright 2021-2023 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

# pylint: disable=wrong-import-position

import sys
import unittest
import os

# Insert the location of makeprojects at the begining so it's the first
# to be processed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from makeprojects.util import validate_enum_type, regex_dict, validate_boolean, \
    validate_string, remove_ending_os_sep, was_processed
from makeprojects.enums import PlatformTypes, IDETypes, ProjectTypes

########################################


class TestUtil(unittest.TestCase):
    """
    Test util functions
    """

########################################

    def test_validate_enum_type(self):
        """
        Test makeprojects.util.validate_enum_type
        """

        # Test None
        self.assertIsNone(validate_enum_type(None, PlatformTypes))
        self.assertIsNone(validate_enum_type(None, IDETypes))
        self.assertIsNone(validate_enum_type(None, ProjectTypes))

        # Test conversion
        self.assertIs(validate_enum_type(
            "stadia", PlatformTypes), PlatformTypes.stadia)
        self.assertIs(validate_enum_type("Vs2022", IDETypes), IDETypes.vs2022)
        self.assertIs(validate_enum_type(ProjectTypes.library,
                      ProjectTypes), ProjectTypes.library)

        # Failure cases
        with self.assertRaises(ValueError):
            validate_enum_type(90, PlatformTypes)
        with self.assertRaises(ValueError):
            validate_enum_type(PlatformTypes, PlatformTypes)

        with self.assertRaises(AttributeError):
            validate_enum_type("stadia", 90)

########################################

    def test_regex_dict(self):
        """
        Test makeprojects.util.test_regex_dict
        """

        # Create wildcards for .h and .cpp only
        test = {
            "*.h": ".h",
            "*.cpp": ".cpp"
        }

        # Convert the dict
        result = regex_dict(test)

        # Only foo.hpp will not match
        samples = ("foo.h", "foo.hpp", "foo.cpp", "test.h")
        for sample in samples:

            # Make sure it hit only once
            hit = 0
            for item in result.items():

                # Regex match?
                if item[0](sample):

                    # Make sure the file extension is a match
                    data = item[1]
                    self.assertIs(sample.endswith(data), True)
                    hit = hit + 1

            # No hits?
            if not hit:
                # This is the only entry that should not hit
                self.assertEqual(sample, "foo.hpp")
            else:
                # Only 1 hit allowed
                self.assertEqual(hit, 1)

########################################

    def test_validate_boolean(self):
        """
        Test makeprojects.util.validate_boolean
        """

        self.assertTrue(validate_boolean(True))
        self.assertTrue(validate_boolean(str(1)))
        self.assertIsNone(validate_boolean(None))
        self.assertTrue(validate_boolean(90))
        self.assertFalse(validate_boolean("No"))

        with self.assertRaises(ValueError):
            validate_boolean({})
        with self.assertRaises(ValueError):
            validate_boolean(self)
        with self.assertRaises(ValueError):
            validate_boolean("fail")

########################################

    def test_validate_string(self):
        """
        Test makeprojects.util.validate_string
        """

        validate_string("sds")
        validate_string(str(90))
        validate_string(b"slk")

        with self.assertRaises(ValueError):
            validate_string(90)
        with self.assertRaises(ValueError):
            validate_string({})
        with self.assertRaises(ValueError):
            validate_string(self)
        with self.assertRaises(ValueError):
            validate_string(9.0)

########################################

    def test_remove_ending_os_sep(self):
        """
        Test remove_ending_os_sep()
        """

        # Test parent
        self.assertEqual(remove_ending_os_sep(None), [])
        if os.sep == "\\":
            before = ["c:\\a", "a\\a\\", "\\", "c:\\a\\a\\"]
            after = ["c:\\a", "a\\a", "\\", "c:\\a\\a"]
        else:
            before = ["/a", "a/a/", "/", "/a/a/"]
            after = ["/a", "a/a", "/", "/a/a"]
        self.assertEqual(remove_ending_os_sep(before), after)

        # Test failure cases
        with self.assertRaises(TypeError):
            remove_ending_os_sep(True)
        with self.assertRaises(TypeError):
            remove_ending_os_sep(1.0)
        with self.assertRaises(TypeError):
            remove_ending_os_sep(0)
        with self.assertRaises(TypeError):
            remove_ending_os_sep(False)


########################################

    def test_was_processed(self):
        """
        Test was_processed()
        """

        processed = set()

        self.assertFalse(was_processed(processed, "a", False))
        self.assertTrue(was_processed(processed, "a", False))
        self.assertFalse(was_processed(processed, "b", False))
        self.assertFalse(was_processed(processed, "c", False))
        self.assertFalse(was_processed(processed, "d", False))
        self.assertTrue(was_processed(processed, "a", False))
        self.assertTrue(was_processed(processed, "b", False))


########################################


if __name__ == "__main__":
    unittest.main()
