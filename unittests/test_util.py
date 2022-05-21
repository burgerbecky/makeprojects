#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeproject util functions

Copyright 2021-2022 by Rebecca Ann Heineman becky@burgerbecky.com

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
from makeprojects.util import remove_ending_os_sep, was_processed

########################################


class TestUtil(unittest.TestCase):
    """
    Test util functions
    """

########################################

    def test_remove_ending_os_sep(self):
        """
        Test remove_ending_os_sep()
        """

        # Test parent
        self.assertEqual(remove_ending_os_sep(None), [])
        if os.sep == '\\':
            before = ['c:\\a', 'a\\a\\', '\\', 'c:\\a\\a\\']
            after = ['c:\\a', 'a\\a', '\\', 'c:\\a\\a']
        else:
            before = ['/a', 'a/a/', '/', '/a/a/']
            after = ['/a', 'a/a', '/', '/a/a']
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


if __name__ == '__main__':
    unittest.main()
