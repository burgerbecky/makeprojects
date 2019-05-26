#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeprojects.visualstudio

Copyright 2013-2019 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

from burger import convert_to_array
from makeprojects.visualstudio import get_uuid, SemicolonArray

########################################


def test_get_uuid():
    """
    Test to see if empty Visual Studio solution files build.
    """

    tests = (
        ('testme', '7A67F5D4-50FD-36F7-BBEB-1C739AB40B8C'),
        ('helloworldvc7win.vcproj', 'D4B7B275-B4D2-3FEF-86CF-D2D640314544')
    )

    for test in tests:
        assert get_uuid(test[0]) == test[1]


########################################


def test_semi_colon_array():
    """
    Test to see if empty Visual Studio solution files build.
    """

    tests = (
        ('test','test'),
        (('foo','bar'), 'foo;bar'),
        (['a','b','c'], 'a;b;c')
    )

    for test in tests:
        array = SemicolonArray(test[0])
        assert str(array) == test[1]

    for test in tests:
        array = SemicolonArray()
        for item in convert_to_array(test[0]):
            array.append(item)
        assert str(array) == test[1]
