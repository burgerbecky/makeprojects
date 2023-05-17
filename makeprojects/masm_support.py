#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data and code to support MASM targets

This module contains data, classes and functions to support
building MASM files

@package makeprojects.masm_support

@var makeprojects.masm_support.MASM_BOOLEANS
Boolean list for MASM, Name, Default, switches

@var makeprojects.masm_support.MASM_STRINGS
Name, default, switch, generates output, quote parameters
"""

from __future__ import absolute_import, print_function, unicode_literals

from .validators import lookup_booleans, lookup_strings, lookup_enum_append_keys
from .util import convert_file_name

# Enumerations for MASM warning levels
MASM_WARNINGLEVEL = (
    ("/W0", 0), ("/W1", 1), ("/W2", 2), ("/W3", 3)
)

# Not supported with MASM for VC 2003
# MASM_ERROR_REPORT = (
#    ("/errorReport:prompt", 0), ("/errorReport:queue", 1),
#    ("/errorReport:send", 2), ("/errorReport:none", 3)
# )

# Names, default, lookup tables for MASM enums
MASM_ENUMS = (
    ("WarningLevel", (3, MASM_WARNINGLEVEL)),
    # ("ErrorReporting", (0, MASM_ERROR_REPORT))
)

# Boolean list for MASM, Name, Default, switches
MASM_BOOLEANS = (
    ("NoLogo", (True, "/nologo", True)),
    ("TinyMemoryModelSupport", (False, "/AT", True)),
    ("GenerateDebugInformation", (True, "/Zi", True))
)

# String entries for MASM, Name, default, switch, generates output, quote
# parameter
MASM_STRINGS = (
    ("ObjectFileName", (
        "$(IntDir)%(FileName).obj", "/Fo", True, True)),
)


########################################


def make_masm_command(command_dict, source_file):
    """
    Create MASM command line

    Args:
        command_dict: Dict with command overrides
    Returns:
        Command line, Description, Output list
    """

    # Create the initial command line
    # /c = Assemble without linking
    cmd = ["ml.exe", "/c"]

    # /errorReport:prompt  /Ta &quot;$(InputPath)&quot;
    lookup_booleans(cmd, MASM_BOOLEANS, command_dict)
    lookup_enum_append_keys(cmd, MASM_ENUMS, command_dict)
    outputs = lookup_strings(cmd, MASM_STRINGS, command_dict)
    cmd.append("/Ta\"%(FullPath)\"")

    cmd = convert_file_name(" ".join(cmd), source_file)
    description = convert_file_name(
        "Assembling %(FileName)%(Extension)...", source_file)
    outputs = [convert_file_name(x, source_file) for x in outputs]    

    return cmd, description, outputs
