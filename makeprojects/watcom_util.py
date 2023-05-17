#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Project file generator subroutines for Open Watcom 1.9

This module contains classes needed to generate project files intended for use
by Open Watcom 1.9

@package makeprojects.watcom_util
"""

from __future__ import absolute_import, print_function, unicode_literals

from burger import is_string, convert_to_linux_slashes

from .validators import lookup_enum_value
from .enums import FileTypes
from .hlsl_support import HLSL_ENUMS, make_hlsl_command
from .glsl_support import make_glsl_command

########################################


def fixup_env(item):
    """
    Check if a path has an environment variable.
    If an pathname starts with $(XXX), then it needs to be invoking
    and environment variable. Watcom uses the form $(%XXX) so insert a
    percent sign to convert if needed

    Args:
        item: String to check

    Returns:
        Updated pathname using $(%XXX) format
    """

    # Convert the macros
    item = item.replace("$(", "$(%")

    # In case there were already $(%) entries, fix them
    return item.replace("$(%%", "$(%")


########################################


def convert_file_name_watcom(item):
    """
    Convert macros from Visual Studio to Open Watcom

    Args:
        item: Filename string
    Returns:
        String with converted macros
    """

    if is_string(item):
        item = item.replace("%(RootDir)%(Directory)", "$[:")
        item = item.replace("%(FileName)", "$[&")
        item = item.replace("%(FullPath)", "$[@")
        item = item.replace("%(Identity)", "$[@")
    return item

########################################


def get_element_dict(rule_list, base_name, tool_enums):
    """
    Create Visual Studio style element list

    Given a list of rules, the base name of the source file, and
    the enumeration table for the command generator, return a
    dict with all the keys and values for the Visual Studio overrides
    for this file.

    Args:
        rule_list: Iterable of a list of rules
        base_name: Name of the source file to check
        tool_enums: Enumeration lookup for the command generator

    Returns:
        dict of values for file overrides, can be empty

    """

    # Extract the rules
    element_dict = {}

    # Iterate over the rule list tuple
    for rule in rule_list:

        # The key is a regex
        for key in rule:

            # Match the filename?
            if not key(base_name):
                # No? Skip it
                continue

            # Get the list of records
            records = rule[key]
            for item in records:
                value = records[item]

                # Is it an enumeration?
                enum_table = lookup_enum_value(
                    tool_enums, item, None)

                # Look it up from the table
                if enum_table:
                    new_value = lookup_enum_value(
                        enum_table[1], value, None)
                    if new_value is not None:
                        value = str(new_value)

                # Set the command line switch
                element_dict[item] = value

    # Return the generated dict
    return element_dict


########################################


def get_custom_list(custom_list, rule_list, codefiles):
    """
    Scan the custom rules and create a list of bespoke builders

    Args:
        custom: list object to receive new entries
        rule_list: Tuple of rules
        codefiles: List of SourceFile objects to check

    Return:
        custom_list
    """

    # Iterate over every file
    for codefile in codefiles:

        # Only process hlsl and glsl files for watcom
        if codefile.type not in (FileTypes.hlsl, FileTypes.glsl):
            continue

        # Get the dispatcher for the file type
        if codefile.type is FileTypes.hlsl:
            make_command = make_hlsl_command
            tool_enums = HLSL_ENUMS
        else:
            # Assume glsl
            make_command = make_glsl_command
            tool_enums = {}

        # Get the base name for comparison
        full_path = convert_to_linux_slashes(codefile.relative_pathname)
        index = full_path.rfind("/")
        base_name = full_path if index == -1 else full_path[index + 1:]

        # Extract the rules
        element_dict = get_element_dict(rule_list, base_name, tool_enums)

        # Create the command to build the custom data
        cmd, description, outputs = make_command(
            element_dict, codefile)

        # Sort the list, to make sure the comparison below works
        outputs.sort()

        # Check if this rule has already been created
        for item in custom_list:
            if item[2] == outputs:

                # It's already done, skip it
                break
        else:

            # Add the rule to the list
            custom_list.append((cmd, description, outputs, codefile))

    return custom_list

########################################


def get_output_list(custom_list):
    """
    Scan the custom_list and return the output files

    Args:
        custom_list: List of custom commands

    Return:
        List of output file names
    """

    # Use a set to remove duplicates
    output_list = set()

    # Scan the list
    for item in custom_list:

        # Add every output file
        for output in item[2]:
            output_list.add(output)

    # Convert to a linked list
    output_list = list(output_list)

    # Sort it
    output_list.sort()
    return output_list
