#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for empty projects / solutions

Copyright 2013-2019 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

import os
import burger
import makeprojects
from makeprojects.enums import IDETypes

########################################


def test_visual_studio(tmpdir):
    """
    Test to see if cleanme loads build_rules.py.
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
        (IDETypes.vs2019, 'emptyv19.sln')
    ]

    for item in empty_tests:
        solution = makeprojects.new_solution(name='empty', working_directory=str(tmpdir))
        assert not solution.generate(ide=item[0])

        empty_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests', item[1])
        assert burger.compare_files(empty_file, str(tmpdir.join(item[1])))

    # Cleanup
    #tmpdir.remove()


########################################


def test_cleanme_root(tmpdir):
    """
    Test to see if cleanme handles root=True.
    """
    pass
