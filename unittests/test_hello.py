#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for empty projects / solutions

Copyright 2013-2022 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

import os
from shutil import copyfile
from burger import compare_files
import makeprojects
from makeprojects.enums import IDETypes

########################################


def test_visual_studio(tmpdir):
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
    source_dir = tmpdir.mkdir('source')
    asset_base = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'assets', 'hello', 'source')
    copyfile(
        os.path.join(
            asset_base, 'helloworld.cpp'), os.path.join(
                str(source_dir), 'helloworld.cpp'))

    for item in empty_tests:
        solution = makeprojects.new_solution(
            name='hello', working_directory=str(tmpdir),
            perforce=False, project_type='Tool')
        project = makeprojects.new_project(
            name='helloworld', working_directory=str(tmpdir))
        solution.add_project(project)
        configuration = makeprojects.new_configuration(
            {'name': 'Debug', 'platform': 'windows'})
        project.add_configuration(configuration)
        configuration = makeprojects.new_configuration(
            {'name': 'Internal', 'platform': 'windows'})
        project.add_configuration(configuration)
        configuration = makeprojects.new_configuration(
            {'name': 'Release', 'platform': 'windows'})
        project.add_configuration(configuration)

        # TODO: Redo this unit test
        # assert not solution.generate(ide=item[0])

        #empty_file = os.path.join(
        #    os.path.dirname(os.path.abspath(__file__)),
        #    'assets', 'hello', item[1])
        #assert compare_files(empty_file, str(tmpdir.join(item[1])))

    # Cleanup
    # tmpdir.remove()
