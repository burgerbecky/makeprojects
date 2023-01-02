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
from makeprojects.validators import lookup_enum

########################################


class TestValidators(unittest.TestCase):
    """
    Test validators
    """

########################################

    def test_lookup_enum(self):
        """
        Test makeprojects.validators.lookup_enum
        """

        # The function returns the resulting list
        cmd = ["foo.exe"]
        enum_test1 = (
            ("/Zpr", 0), ("Row", 0), ("/Zpc", 1), ("Column", 1),
            (None, 2), ("Matrix", 2)
        )
        result1 = ["foo.exe"]

        # Test against input that should not modify the result
        self.assertListEqual(lookup_enum(cmd, enum_test1, None), result1)
        self.assertListEqual(lookup_enum(cmd, enum_test1, 67), result1)
        self.assertListEqual(lookup_enum(cmd, enum_test1, -1), result1)
        self.assertListEqual(lookup_enum(cmd, enum_test1, 3), result1)
        self.assertListEqual(lookup_enum(cmd, enum_test1, "3"), result1)

        # Failure cases
        with self.assertRaises(ValueError):
            lookup_enum(cmd, enum_test1, True)
        with self.assertRaises(ValueError):
            lookup_enum(cmd, enum_test1, False)
        with self.assertRaises(ValueError):
            lookup_enum(cmd, enum_test1, "Barf")

        # Append cases, note, this also tests that the first match
        # is used where there are multiple case matches
        result1.append("/Zpr")
        self.assertListEqual(lookup_enum(cmd, enum_test1, 0), result1)
        result1.append("/Zpc")
        self.assertListEqual(lookup_enum(cmd, enum_test1, 1), result1)
        result1.append("/Zpr")
        self.assertListEqual(lookup_enum(cmd, enum_test1, 0), result1)

        # Test for the case where None is the default
        self.assertListEqual(lookup_enum(cmd, enum_test1, 2), result1)

########################################


if __name__ == '__main__':
    unittest.main()
