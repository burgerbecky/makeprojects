#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for empty projects / solutions

Copyright 2013-2022 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

# pylint: disable=wrong-import-position

import os
import sys
import unittest
import tempfile
import shutil
import burger

# Insert the location of makeprojects at the begining so it's the first
# to be processed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from makeprojects.enums import IDETypes
import makeprojects

########################################


class TestEmpty(unittest.TestCase):
    """
    Test empty projects and solutions.
    """


########################################

    def setUp(self):
        """
        Handle temporary directory
        """
        self.saved_cwd = os.getcwd()
        self.tmpdir = os.path.realpath(tempfile.mkdtemp())
        # Make sure anything left behind is removed
        self.addCleanup(shutil.rmtree, self.tmpdir)


########################################


    def tearDown(self):
        """
        Restore directory
        """

        # Restore the working directory, if the test did not.
        os.chdir(self.saved_cwd)

########################################

    def test_visual_studio(self):
        """
        Test to see if empty Visual Studio solution files build.
        """

        empty_tests = [
            (IDETypes.vs2003, 'emptyvc7.sln'),
            (IDETypes.vs2005, 'emptyvc8.sln'),
            (IDETypes.vs2008, 'emptyvc9.sln'),
            (IDETypes.vs2010, 'emptyv10.sln'),
            (IDETypes.vs2012, 'emptyv12.sln'),
            (IDETypes.vs2013, 'emptyv13.sln'),
            (IDETypes.vs2015, 'emptyv15.sln'),
            (IDETypes.vs2017, 'emptyv17.sln'),
            (IDETypes.vs2019, 'emptyv19.sln'),
            (IDETypes.vs2022, 'emptyv22.sln')
        ]

        for item in empty_tests:
            solution = makeprojects.Solution(name='empty')
            # Force the root directory
            solution.working_directory = self.tmpdir
            # Disable perforce support
            solution.perforce = False

            # Generate the solution
            self.assertFalse(solution.generate(ide=item[0]))

            empty_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'assets', 'empty', item[1])
            self.assertTrue(
                burger.compare_files(
                    empty_file,
                    os.path.join(
                        self.tmpdir,
                        item[1])))


########################################


if __name__ == '__main__':
    unittest.main()
