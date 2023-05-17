#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Project file generator subroutines for Microsoft Visual Studio 2003-2008.

This module contains classes needed to generate project files intended for use
by Microsoft's Visual Studio 2003, 2005 and 2008.

@package makeprojects.visual_studio_utils

"""

from __future__ import absolute_import, print_function, unicode_literals

from burger import is_string

from .validators import VSStringProperty

########################################


def get_path_property(pathname):
    """
    If a path is relative, return the proper object

    Check if a pathname starts with a ".", which means it's relative to the
    project. If so, return a RelativePath string, otherwise retirn a FileName
    string.

    Args:
        pathname: Pathname to test

    Returns VSStringProperty of type RelativePath or FileName
    """

    if pathname.startswith("."):
        return VSStringProperty("RelativePath", pathname)
    return VSStringProperty("FileName", pathname)


########################################


def convert_file_name_vs2010(item):
    """
    Convert macros from to Visual Studio 2003-2008

    Args:
        item: Filename string
    Returns:
        String with converted macros
    """

    if is_string(item):
        item = item.replace("%(RootDir)%(Directory)", "$(InputDir)")
        item = item.replace("%(FileName)", "$(InputName)")
        item = item.replace("%(Extension)", "$(InputExt)")
        item = item.replace("%(FullPath)", "$(InputPath)")
        item = item.replace("%(Identity)", "$(InputPath)")
    return item
