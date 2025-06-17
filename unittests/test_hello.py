#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for empty projects / solutions

Copyright 2013-2025 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

import os
import sys
import unittest
import tempfile
import shutil
from burger import compare_files

# Insert the location of makeprojects at the begining so it's the first
# to be processed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import makeprojects
from makeprojects.enums import IDETypes

########################################


class TestHello(unittest.TestCase):
    """
    Test hello world project generation
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
        Test to see if simple Visual Studio projects build.
        """

        empty_tests = [
            (IDETypes.vs2003, 'hellovc7w32.sln'),
            (IDETypes.vs2005, 'hellovc8win.sln'),
            (IDETypes.vs2008, 'hellovc9win.sln'),
            (IDETypes.vs2010, 'hellov10win.sln'),
            (IDETypes.vs2012, 'hellov12win.sln'),
            (IDETypes.vs2013, 'hellov13win.sln'),
            (IDETypes.vs2015, 'hellov15win.sln'),
            (IDETypes.vs2017, 'hellov17win.sln'),
            (IDETypes.vs2019, 'hellov19win.sln'),
            (IDETypes.vs2022, 'hellov22win.sln')
        ]

        # Create a source code folder

        source_dir = os.path.join(self.tmpdir, 'source')
        os.mkdir(source_dir)
        asset_base = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'assets', 'hello', 'source')
        shutil.copyfile(
            os.path.join(
                asset_base, 'helloworld.cpp'), os.path.join(
                    str(source_dir), 'helloworld.cpp'))

        for item in empty_tests:
            solution = makeprojects.Solution(
                name='hello', project_type='Tool')
            solution.perforce = False
            solution.working_directory = self.tmpdir

            project = makeprojects.Project(name='helloworld')
            project.working_directory = self.tmpdir

            solution.add_project(project)

            configuration = makeprojects.Configuration(
                'Debug', platform='windows')
            project.add_configuration(configuration)
            configuration = makeprojects.Configuration(
                'Internal', platform='windows')
            project.add_configuration(configuration)
            configuration = makeprojects.Configuration(
                'Release', platform='windows')
            project.add_configuration(configuration)

            # TODO: Redo this unit test
            # assert not solution.generate(ide=item[0])

            # empty_file = os.path.join(
            #    os.path.dirname(os.path.abspath(__file__)),
            #    'assets', 'hello', item[1])
            #assert compare_files(empty_file, str(tmpdir.join(item[1])))

########################################


if __name__ == '__main__':
    unittest.main()
