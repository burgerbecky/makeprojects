#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data and code to support GLSL targets

This module contains data, classes and functions to support
building GLSL files

@package makeprojects.glsl_support

@var makeprojects.glsl_support.GLSL_BOOLEANS
Boolean list for GLSL, Name, Default, switches
"""

from __future__ import absolute_import, print_function, unicode_literals

from .validators import lookup_booleans, lookup_strings

# Boolean list for GLSL, Name, Default, switches
GLSL_BOOLEANS = {
    "CPP": (True, {"/c": True})
}

# String entries for GLSL, Name, default, switch, generates output, quote
# parameter
GLSL_STRINGS = (
    ("ObjectFileName", (
        "%(RootDir)%(Directory)%(FileName).h", "", True, True)),
    ("VariableName", (
        "g_%(FileName)", "/l ", False, False))
)


########################################


def make_glsl_command(command_dict):
    """ Create GLSL command line
    Args:
        command_dict: Dict with command overrides
    Returns:
        Command line, Description, Output list
    """

    # Create the initial command line
    cmd = [
        ("\"$(VS71COMNTOOLS)..\\..\\..\\Microsoft Visual Studio 8\\"
         "vc\\bin\\stripcomments.exe\""),
        "\"%(FullPath)\""]

    lookup_booleans(cmd, GLSL_BOOLEANS, command_dict)
    outputs = lookup_strings(cmd, GLSL_STRINGS, command_dict)

    description = "Stripcomments %(FileName)%(Extension)..."
    return " ".join(cmd), description, outputs
