#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeproject IDETypes

Copyright 2013-2019 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

from makeprojects.enums import IDETypes

########################################


def test_is_visual_studio():
    """
    Test IDETypes.is_visual_studio().
    """

    for item in IDETypes:
        if item in (IDETypes.vs2003, IDETypes.vs2005, IDETypes.vs2008, IDETypes.vs2010,
                    IDETypes.vs2012, IDETypes.vs2013, IDETypes.vs2015, IDETypes.vs2017,
                    IDETypes.vs2019):
            assert item.is_visual_studio()
        else:
            assert not item.is_visual_studio()


########################################


def test_is_xcode():
    """
    Test IDETypes.is_xcode().
    """

    for item in IDETypes:
        if item in (IDETypes.xcode3, IDETypes.xcode4, IDETypes.xcode5, IDETypes.xcode6,
                    IDETypes.xcode7, IDETypes.xcode8, IDETypes.xcode9, IDETypes.xcode10):
            assert item.is_xcode()
        else:
            assert not item.is_xcode()


########################################


def test_is_codewarrior():
    """
    Test IDETypes.is_codewarrior().
    """

    for item in IDETypes:
        if item in (IDETypes.codewarrior50, IDETypes.codewarrior58, IDETypes.codewarrior59):
            assert item.is_codewarrior()
        else:
            assert not item.is_codewarrior()
