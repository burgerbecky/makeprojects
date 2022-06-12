#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that enumerates all of the builder modules.

See Also:
    makeprojects.cleanme, makeprojects.rebuildme

@package makeprojects.modules

@var makeprojects.modules.MODULES
List of build modules

"""

from __future__ import absolute_import, print_function, unicode_literals

from . import makerez, slicer, doxygen, watcom, makefile, ninja, \
    visual_studio, codewarrior, codeblocks, xcode

# List of modules for building and cleaning
MODULES = [
    slicer,
    makerez,
    watcom,
    makefile,
    ninja,
    visual_studio,
    codewarrior,
    codeblocks,
    xcode]

########################################


def add_documentation_modules():
    """
    Add the modules that process documentation to the MODULES list.

    See Also:
        makeprojects.doxygen
    """

    if doxygen not in MODULES:
        MODULES.append(doxygen)
