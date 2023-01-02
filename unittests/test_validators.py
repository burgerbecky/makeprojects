#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeprojects.validators

Copyright 2013-2023 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

# pylint: disable=wrong-import-position

import unittest
import os
import sys

# Insert the location of makeprojects at the begining so it's the first
# to be processed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from makeprojects.validators import lookup_enum_append_key, lookup_enum_value, \
    lookup_enum_append_keys, lookup_strings, lookup_string_list, \
    lookup_string_lists, lookup_booleans
from makeprojects.hlsl_support import HLSL_ENUMS

########################################


class TestValidators(unittest.TestCase):
    """
    Test validators
    """

    def test_lookup_enum_value(self):
        """
        Test makeprojects.validators.lookup_enum_value
        """

        enum_test1 = (
            ("key1", 0), ("barf", 66), ("key1", 66), ("barf", 2)
        )

        self.assertIs(lookup_enum_value(enum_test1, "key1", None), 0)
        self.assertIs(lookup_enum_value(enum_test1, "barf", None), 66)
        self.assertIs(lookup_enum_value(enum_test1, "foo", None), None)
        self.assertIs(lookup_enum_value(enum_test1, 0, None), None)


########################################

    def test_lookup_enum_append_key(self):
        """
        Test makeprojects.validators.lookup_enum_append_key
        """

        # The function returns the resulting list
        cmd = ["foo.exe"]
        enum_test1 = (
            ("/Zpr", 0), ("Row", 0), ("/Zpc", 1), ("Column", 1),
            (None, 2), ("Matrix", 2)
        )
        result1 = ["foo.exe"]

        # Test against input that should not modify the result
        self.assertListEqual(lookup_enum_append_key(
            cmd, enum_test1, None), result1)
        self.assertListEqual(lookup_enum_append_key(
            cmd, enum_test1, 67), result1)
        self.assertListEqual(lookup_enum_append_key(
            cmd, enum_test1, -1), result1)
        self.assertListEqual(lookup_enum_append_key(
            cmd, enum_test1, 3), result1)
        self.assertListEqual(lookup_enum_append_key(
            cmd, enum_test1, "3"), result1)

        # Failure cases
        with self.assertRaises(ValueError):
            lookup_enum_append_key(cmd, enum_test1, True)
        with self.assertRaises(ValueError):
            lookup_enum_append_key(cmd, enum_test1, False)
        with self.assertRaises(ValueError):
            lookup_enum_append_key(cmd, enum_test1, "Barf")

        # Append cases, note, this also tests that the first match
        # is used where there are multiple case matches
        result1.append("/Zpr")
        self.assertListEqual(lookup_enum_append_key(
            cmd, enum_test1, 0), result1)
        result1.append("/Zpc")
        self.assertListEqual(lookup_enum_append_key(
            cmd, enum_test1, 1), result1)
        result1.append("/Zpr")
        self.assertListEqual(lookup_enum_append_key(
            cmd, enum_test1, 0), result1)

        # Test for the case where None is the default
        self.assertListEqual(lookup_enum_append_key(
            cmd, enum_test1, 2), result1)

########################################

    def test_lookup_enum_append_keys(self):
        """
        Test makeprojects.validators.lookup_enum_append_keys
        """

        # The function returns the resulting list
        cmd = ["foo.exe"]

        # Override Optimization with 2, default is 4
        source_dict = {"Optimization": 2}
        result1 = ["foo.exe", "/O1", "/Zpc", "/Gfp", "/Tps_2_0"]
        lookup_enum_append_keys(cmd, HLSL_ENUMS, source_dict)
        self.assertListEqual(cmd, result1)

########################################

    def test_lookup_strings(self):
        """
        Test makeprojects.validators.lookup_strings
        """

        # The function modifies this list
        cmd = ["foo.exe"]

        string_entries = (
            ("Test1", (
                "Test1.h", "", True, True)),
            ("Test2", (
                "Test2.h", "/2 ", False, False)),
            ("Test3", (
                "Test3.h", "/3", True, False)),
            ("Test4", (
                "Test4.h", "/4", False, True)),
        )

        result = lookup_strings(cmd, string_entries, {})
        self.assertListEqual(
            cmd, ["foo.exe", "\"Test1.h\"", "/2 Test2.h", "/3\"Test3.h\"", "/4Test4.h"])
        self.assertListEqual(result, ["Test1.h", "Test4.h"])

        cmd = ["foo.exe"]
        result = lookup_strings(cmd, string_entries, {
            "Test1": "bar1.h",
            "Test2": "bar2.h",
            "Test3": "bar3.h",
            "Test4": "bar4.h"
        })
        self.assertListEqual(
            cmd, ["foo.exe", "\"bar1.h\"", "/2 bar2.h", "/3\"bar3.h\"", "/4bar4.h"])
        self.assertListEqual(result, ["bar1.h", "bar4.h"])

        cmd = ["foo.exe"]
        result = lookup_strings(cmd, string_entries, {
            "Test1": "",
            "Test2": "bar2.h",
            "Test3": None,
        })
        self.assertListEqual(
            cmd, ["foo.exe", "\"Test1.h\"", "/2 bar2.h", "/3\"Test3.h\"", "/4Test4.h"])
        self.assertListEqual(result, ["Test1.h", "Test4.h"])

########################################

    def test_lookup_string_list(self):
        """
        Test makeprojects.validators.lookup_string_list
        """

        cmd = ["foo.exe"]
        entry_list = ("bar.h", "barf.h", "temp.h")
        lookup_string_list(cmd, "/I ", entry_list, False)
        self.assertListEqual(
            cmd, ["foo.exe", "/I", "bar.h", "/I", "barf.h", "/I", "temp.h"])

        cmd = ["foo.exe"]
        lookup_string_list(cmd, "/I ", entry_list, True)
        self.assertListEqual(
            cmd, ["foo.exe", "/I", "\"bar.h\"", "/I", "\"barf.h\"", "/I", "\"temp.h\""])

        cmd = ["foo.exe"]
        lookup_string_list(cmd, "/T", entry_list, False)
        self.assertListEqual(
            cmd, ["foo.exe", "/Tbar.h", "/Tbarf.h", "/Ttemp.h"])

        cmd = ["foo.exe"]
        lookup_string_list(cmd, "/T", entry_list, True)
        self.assertListEqual(
            cmd, ["foo.exe", "/T\"bar.h\"", "/T\"barf.h\"", "/T\"temp.h\""])

########################################

    def test_lookup_string_lists(self):
        """
        Test makeprojects.validators.lookup_string_lists
        """

        cmd = ["foo.exe"]
        string_list = (
            ("Test1", ("/D", False)),
            ("Test2", ("/I ", True))
        )
        lookup_string_lists(cmd, string_list, {})
        self.assertListEqual(cmd, ["foo.exe"])

        lookup_string_lists(cmd, string_list, {
                            "Test1": "barf.h", "Test2": ("a", "b")})
        self.assertListEqual(
            cmd, ["foo.exe", "/Dbarf.h", "/I", "\"a\"", "/I", "\"b\""])

########################################

    def test_lookup_booleans(self):
        """
        Test makeprojects.validators.lookup_booleans
        """

        cmd = ["foo.exe"]
        boolean_list = (
            ("Test1", (None, "/T1", True)),
            ("Test2", (True, "/T2", True, "/F2", False)),
            ("Test3", (False, "/F3", False)),
        )
        lookup_booleans(cmd, boolean_list, {})
        self.assertListEqual(cmd, ["foo.exe", "/T2", "/F3"])

        cmd = ["foo.exe"]
        lookup_booleans(cmd, boolean_list, {
            "Test1": False,
            "Test2": False,
            "Test3": True
        })
        self.assertListEqual(cmd, ["foo.exe", "/F2"])

        cmd = ["foo.exe"]
        lookup_booleans(cmd, boolean_list, {
            "Test1": None,
            "Test2": None,
            "Test3": None
        })
        self.assertListEqual(cmd, ["foo.exe", "/T2", "/F3"])


########################################


if __name__ == "__main__":
    unittest.main()
