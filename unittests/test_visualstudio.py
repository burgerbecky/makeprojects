#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeprojects.visualstudio

Copyright 2013-2019 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

import os
import burger
import makeprojects.visualstudio

########################################


def test_get_uuid():
    """
    Test to see if empty Visual Studio solution files build.
    """

    tests = [
        ('testme', '7A67F5D4-50FD-36F7-BBEB-1C739AB40B8C'),
        ('helloworldvc7win.vcproj', 'D4B7B275-B4D2-3FEF-86CF-D2D640314544')
    ]

    for test in tests:
        assert makeprojects.visualstudio.get_uuid(test[0]) == test[1]
