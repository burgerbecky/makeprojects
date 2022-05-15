#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The util module contains subroutines used everywhere.

@package makeprojects.util
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import fnmatch
from burger import string_to_bool, is_string, import_py_script
from .enums import FileTypes
from .config import DEFAULT_BUILD_RULES

# pylint: disable=consider-using-f-string

########################################


def validate_enum_type(value, data_type):
    """
    Verify a value is a specific data type.

    Check if the value is either None or an instance of a
    specfic data type. If so, return immediately. If the value is a string,
    call the lookup() function of the data type for conversion.

    Args:
        value: Value to check.
        data_type: Type instance of the class type to match.

    Returns:
        Value converted to data_type or None.

    Raises:
        TypeError

    """

    if value is not None:
        # Perform the lookup
        new_value = data_type.lookup(value)
        if new_value is None:
            msg = '"{}" must be of type "{}".'.format(
                value, data_type.__name__)
            raise TypeError(msg)
        # Save the converted type
        value = new_value
    return value

########################################


def regex_dict(item):
    """
    Convert *.cpp keys to regex keys

    Given a dict where the keys are all filenames with wildcards, convert only
    the keys into equivalent regexes and leave the values intact.

    Example:

    rules = {
        '*.cpp':
            {'a': 'arf', 'b': 'bark', 'c': 'coo'},
        '*.h':
            {'h': 'help'}
    }
    regex_keys = regex_dict(rules)

    Args:
        item: dict to convert
    Returns:
        dict with keys converted to regexes
    """

    output = {}
    for key in item:
        output[re.compile(fnmatch.translate(key)).match] = item[key]
    return output

########################################


def validate_boolean(value):
    """
    Verify a value is a boolean.

    Check if the value can be converted to a bool, if so, return the value as
    bool. None is converted to False.

    Args:
        value: Value to check.

    Returns:
        Value converted to data_type or None.

    Raises:
        ValueError
    """

    if value is not None:
        # Convert to bool
        value = string_to_bool(value)
    return value

########################################


def validate_string(value):
    """
    Verify a value is a string.

    Check if the value is a string, if so, return the value as is or None.

    Args:
        value: Value to check.

    Returns:
        Value is string or None.

    Raises:
        ValueError
    """

    if value is not None:
        # Convert to bool
        if not is_string(value):
            raise ValueError('"{}" must be a string.'.format(value))
    return value

########################################


def source_file_filter(file_list, file_type_list):
    """
    Prune the file list for a specific type.

    Note: file_type_list can either be a single enums.FileTypes enum or an
        iterable list of enums.FileTypes

    Args:
        file_list: list of core.SourceFile entries.
        file_type_list: enums.FileTypes to match.
    Returns:
        list of matching core.SourceFile entries.
    """

    result_list = []

    # If a single item was passed, use a simple loop
    if isinstance(file_type_list, FileTypes):
        for item in file_list:
            if item.type is file_type_list:
                result_list.append(item)
    else:
        # A list was passed, so test against the list
        for item in file_list:
            if item.type in file_type_list:
                result_list.append(item)
    return result_list

########################################


def add_build_rules(build_rules_list, file_name, verbose, is_root, basename):
    """
    Load in the file ``build_rules.py``

    Load the build_rules.py file. If the variable ``*_GENERIC`` is ``True``
    or if ``is_root`` is ``True``, append the module to ``build_rules_list``.
    If the variable ``*_CONTINUE`` was found in the file, check if it is set
    to ``True``. If so, return ``True`` to allow processing to continue. If
    the file is not found, return ``True`` to allow processing the parent
    folder.

    Since this is called from ``buildme``, ``cleanme``, and ``makeprojects``,
    the prefix needed for the tool is passed in ``basename``. An example is
    "CLEANME".

    Args:
        build_rules_list: List to add ``build_rules.py`` instances.
        file_name: Full path name of the build_rules.py to load.
        verbose: True for verbose output.
        is_root: True if *_GENERIC is ignored.
        basename: Variable prefix to substitute * in *_GENERIC
    Returns:
        True if the parent folder should be checked, False if not.
    """

    # Ensure the absolute path is used.
    file_name = os.path.abspath(file_name)
    build_rules = import_py_script(file_name)

    # Not found? Continue parsing folders.
    if not build_rules:
        return True

    if is_root or getattr(build_rules, basename + "_GENERIC",
                          False) or getattr(build_rules, "GENERIC", False):
        # Add to the list
        build_rules_list.append(build_rules)

    if verbose:
        print('Using configuration file {}'.format(file_name))

    # Test if this is considered the last one in the chain.
    result = getattr(build_rules, basename + "_CONTINUE", None)

    # Not found?
    if result is None:
        # Try the catch all version
        result = getattr(build_rules, "CONTINUE", False)
    return result

########################################


def get_build_rules(working_directory, verbose, build_rules_name, basename):
    """
    Find all ``build_rules.py`` files that apply to this directory.

    If no files are found, return an empty list.

    Args:
        working_directory: Directory to scan for ``build_rules.py``
        verbose: True if verbose output is desired
        build_rules_name: ``build_rules.py`` or an override
        basename: "CLEANME", "BUILDME", etc.
    Returns:
        List of loaded ``build_rules.py`` file modules
    """

    # Test if there is a specific build rule
    build_rules_list = []

    # Load the configuration file at the current directory
    temp_dir = os.path.abspath(working_directory)

    # Is this the first pass?
    is_root = True
    while True:

        # Attempt to load in the build rules.
        if not add_build_rules(
            build_rules_list, os.path.join(
                temp_dir, build_rules_name), verbose, is_root, basename):
            # Abort if *_CONTINUE = False
            break

        # Directory traversal is active, require CLEANME_GENERIC
        is_root = False

        # Pop a folder to check for higher level build_rules.py
        temp_dir2 = os.path.dirname(temp_dir)

        # Already at the top of the directory?
        if temp_dir2 is None or temp_dir2 == temp_dir:
            add_build_rules(
                build_rules_list,
                DEFAULT_BUILD_RULES,
                verbose,
                True,
                basename)
            break
        # Use the new folder
        temp_dir = temp_dir2
    return build_rules_list
