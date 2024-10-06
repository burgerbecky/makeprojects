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

from .util import iterate_configurations
from .validators import lookup_enum_value
from .enums import FileTypes, PlatformTypes, ProjectTypes
from .hlsl_support import HLSL_ENUMS, make_hlsl_command
from .glsl_support import make_glsl_command

########################################


def fixup_env(item):
    r"""
    Check if a path has an environment variable.
    If an pathname starts with \$(XXX), then it needs to be invoking
    an environment variable. Watcom uses the form $(%%XXX) so insert a
    percent sign to convert to Watcom format if needed. If it already
    has a percent sign, don't change the string.

    Args:
        item: String to check

    Returns:
        Updated pathname using $(%%XXX) format
    """

    # Convert the macros
    item = item.replace("$(", "$(%")

    # In case there were already $(%) entries, fix them
    return item.replace("$(%%", "$(%")


########################################


def convert_file_name_watcom(item):
    r"""
    Convert macros from Visual Studio to Open Watcom

    This table shows the conversions

    | Visual Studio | Watcom |
    | ------------- | ------ |
    | %(RootDir)%(Directory) | $[: |
    | %(FileName) | $[& |
    | %(FullPath) | $[@ |
    | %(Identity) | $[@ |
    | \$(TargetPath) | $^@ |

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
        item = item.replace("$(TargetPath)", "$^@")
    return item

########################################


def get_element_dict(rule_list, base_name, tool_enums):
    """
    Create Visual Studio style element list

    Given a list of rules, the base name of the source file, and
    the enumeration table for the command generator, return a
    dict with all the keys and values for the Visual Studio overrides
    for this file.

    This is usually parsed by the HLSL and GLSL command generators.

    Note:
        The returned value is a dict using Visual Studio elements as keys
        with the parameter template string as the value. Example keys are
        ``ObjectFileName``, ``VariableName``, and ``HeaderFileName``.

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
        for file_regex in rule:

            # Match the filename?
            if not file_regex(base_name):
                # No? Skip it
                continue

            # Get the list of records
            records = rule[file_regex]
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
    Scan the custom rules and create a list of bespoke builders.

    First, convert the rule list into the Visual Studio dictionaries,
    and then use the GLSL or HLSL command line generators to create

    Next, iterate over the codefiles for any GLSL or HLSL files and
    apply the rules (If found) and create the command lines needed
    to build the files.

    If any custom build commands are generated, they are appended to
    ``custom_list`` as a 4 entry tuple, with the first entry being the
    command line, the second is a text description of the command, the
    third is the name of the output file(s) and lastly the input filename.

    Args:
        custom_list: list object to receive new entries
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

    Create a list of output filenames and sort them before returning
    the list. The third entry of the ``custom_list`` is the output filename.

    Args:
        custom_list: List of custom commands

    Return:
        List of output file names

    See Also:
        get_custom_list
    """

    # Use a set to remove duplicates
    output_list = set()

    # Scan the list
    for item in custom_list:

        # Add every output file to the set
        for output in item[2]:
            output_list.add(output)

    # Convert to a linked list
    output_list = list(output_list)

    # Sort it and exit
    output_list.sort()
    return output_list

########################################


def get_obj_list(codefiles, type_list):
    """
    Extract a list of file names without extensions

    Given a codefiles list and a list of acceptable types,
    return a list of filenames stripped of their extensions
    and directories.

    Args:
        codefiles: Codefiles list from the project
        type_list: List of enums.FileTypes objects

    Returns:
        List of processed matching filenames, or empty list

    See Also:
        enums.FileTypes
    """

    # Create result list
    obj_list = []

    # Process
    for item in codefiles:

        # Acceptable?
        if item.type not in type_list:
            continue

        # Ensure the pathname slashes are consistent
        tempfile = convert_to_linux_slashes(
            item.relative_pathname)

        # Strip the extension
        index = tempfile.rfind(".")
        if index == -1:
            entry = tempfile
        else:
            entry = tempfile[:index]

        # Strip the directory prefix
        index = entry.rfind("/")
        if index != -1:
            entry = entry[index + 1:]

        # Add the base filename without extension to the list
        obj_list.append(entry)

    return obj_list

########################################


def add_obj_list(line_list, obj_list, prefix, suffix):
    r"""
    Create a list of object files with prefix

    Give a list of filenames without extensions, create
    a Watcom compatible list with an \$(A) prefix for runtime
    pathname substitution. Add the supplied prefix to all
    filenames.

    The filename list is sorted before processing.

    Args:
        line_list: Output file
        obj_list: List of filenames without extensions
        prefix: Variable name for the list
        suffix: Object file suffix
    """

    # Only the first pass will prefix be the variable declaration
    # All other passes, it's a tab
    for item in sorted(obj_list):
        line_list.append(prefix + "$(A)/" + item + suffix + " &")
        prefix = "\t"

    # Remove the " &" from the last line
    line_list[-1] = line_list[-1][:-2]

########################################


def add_post_build(line_list, configuration):
    """
    If there are custom build rules, add them

    Scan the configuration attribute ``post_build`` and if
    it exists, append the commands to ``line_list``.

    Args:
        line_list: Output stream
        configuration: Project configuration

    See Also:
        convert_file_name_watcom, fixup_env
    """

    # Is there custom post build rule?
    post_build = configuration.get_chained_value("post_build")
    if not post_build:
        return

    # Get the command line
    cmd = post_build[1]

    # Convert Visual Studio environment variables
    cmd = convert_file_name_watcom(cmd)

    # Convert to Watcom format
    cmd = fixup_env(cmd)

    # Add the lines
    line_list.extend([
        "\t@echo " + post_build[0],
        "\t@" + cmd
    ])

########################################


def watcom_linker_system(configuration):
    """
    Determine the watcom system for linkage

    Scan the configuration and return the string "system ???"
    where ??? is replaced with dos4g, nt, etc.

    Can be overriden with the attribute ``wat_system``. If this
    exists, use it to declare "system ???" or "" to disable.

    Args:
        configuration: Project configuration

    Return:
        String "system " + actual type
    """

    # Get the override
    system = configuration.get_chained_value("wat_system")
    if system == "":
        # Disable adding "system"
        return system

    # Not overridden?
    if system is None:

        # Linking for Dos4GW
        if configuration.platform is PlatformTypes.msdos4gw:
            system = "dos4g"

        # Linking for X32 dos extender
        elif configuration.platform is PlatformTypes.msdosx32:
            system = "x32r"

        # Windows DLL?
        elif configuration.project_type is ProjectTypes.sharedlibrary:
            system = "nt_dll"

        # Windows Application?
        elif configuration.project_type is ProjectTypes.app:
            system = "nt_win"

        # Windows console is the default
        else:
            system = "nt"

    return "system " + system

########################################


def warn_if_invalid(solution):
    """
    Iterate over the solution and determine if there are errors

    Test for use of use_mfc or use_atl

    Args:
        solution: Reference to a solution record

    Returns:
        Zero if no error, non-zero if error
    """

    # Create sets of configuration names and projects
    for configuration in iterate_configurations(solution):

        # Only test on windows platforms
        if configuration.platform.is_windows():
            # Test for MFC
            if configuration.use_mfc:
                print(
                    "Watcom doesn't support Microsoft Foundation "
                    "Classes, use_mfc must be False")

            # Test for MFC
            if configuration.use_atl:
                print(
                    "Watcom doesn't support Active Template Library, "
                    "use_atl must be False")

    return 0
