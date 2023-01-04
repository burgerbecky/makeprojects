#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021-2023 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

"""
The util module contains subroutines used everywhere.

@package makeprojects.util

@var makeprojects._BUILD_RULES_CACHE
Dict of build rules loaded
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import fnmatch
from burger import string_to_bool, is_string, import_py_script, norm_paths
from .config import DEFAULT_BUILD_RULES, _XCODEPROJECT_FILE

# pylint: disable=consider-using-f-string

# Cache of Build_rules.py python scripts
_BUILD_RULES_CACHE = {}

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
            msg = "\"{}\" must be of type \"{}\".".format(
                value, data_type.__name__)
            raise TypeError(msg)
        # Save the converted type
        value = new_value
    return value

########################################


def regex_dict(value):
    """
    Convert *.cpp keys to regex keys

    Given a dict where the keys are all filenames with wildcards, convert only
    the keys into equivalent regexes and leave the values intact.

    Examples:

    rules = {
        "*.cpp":
            {"a": "arf", "b": "bark", "c": "coo"},
        "*.h":
            {"h": "help"}
    }
    regex_keys = regex_dict(rules)

    Args:
        value: dict to convert
    Returns:
        dict with keys converted to regexes
    """

    output = {}
    for key in value:
        output[re.compile(fnmatch.translate(key)).match] = value[key]
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
            raise ValueError("\"{}\" must be a string.".format(value))
    return value

########################################


def clear_build_rules_cache():
    """
    Clear the build rules cache

    See Also:
        load_build_rules
    """

    global _BUILD_RULES_CACHE
    _BUILD_RULES_CACHE = {}

########################################


def load_build_rules(path_name, clear_cache=False):
    """
    Load build_rules using a cache.
    Check if the path was already loaded. If so, use the cached
    version, otherwise load and cache the build_rules.py script

    Args:
        path_name: Full pathname to the build_rules.py script
        clear_cache: Boolean, if true, clear the cache first

    See Also:
        clear_build_rules_cache
    """

    # pylint: disable=global-statement
    global _BUILD_RULES_CACHE

    # Check if the cache was to be cleared
    if clear_cache:
        _BUILD_RULES_CACHE = {}

    # Get rid of the trailing slash to ensure hits for duplicate files
    path_name = os.path.abspath(path_name)
    if len(path_name) >= 2 and path_name.endswith(os.sep):
        path_name = path_name[:-1]

    # Is it in the cache?
    build_rules = _BUILD_RULES_CACHE.get(path_name, None)
    if not build_rules:

        # Load and insert into the cache
        build_rules = import_py_script(path_name)
        if build_rules:
            _BUILD_RULES_CACHE[path_name] = build_rules

    return build_rules

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
    build_rules = load_build_rules(file_name)

    # Not found? Continue parsing folders.
    if not build_rules:
        return True

    if is_root or getattr(build_rules, basename + "_GENERIC",
                          False) or getattr(build_rules, "GENERIC", False):
        # Add to the list
        build_rules_list.append(build_rules)

    if verbose:
        print("Using configuration file {}".format(file_name))

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

########################################


def getattr_build_rules(build_rules_list, attributes, value):
    """
    Find an attribute in a list of build rules.

    Iterate over the build rules list until an entry has an attribute value.
    It will return the first one found. If none are found, or there were no
    entries in ``build_rules_list``, this function returns ``value``.

    Args:
        build_rules_list: List of ``build_rules.py`` instances.
        attributes: Attribute name(s) to check for.
        value: Value to return if the attribute was not found.

    Returns:
        Attribute value found in ``build_rules_list`` entry, or ``value``.
    """

    # Ensure if it is a single string

    if is_string(attributes):
        for build_rules in build_rules_list:
            # Does the entry have this attribute?
            try:
                return getattr(build_rules, attributes)
            except AttributeError:
                pass
    else:
        # Assume attributes is an iterable of strings
        for build_rules in build_rules_list:
            # Does the rules file have this attribute?
            for attribute in attributes:
                try:
                    return getattr(build_rules, attribute)
                except AttributeError:
                    pass

    # Return the default value
    return value

########################################


def remove_ending_os_sep(input_list):
    """
    Iterate over a string list and remove trailing os separator characters.

    Each string is tested if its length is greater than one and if the last
    character is the pathname separator. If so, the pathname separator character
    is removed.

    Args:
        input_list: list of strings

    Returns:
        Processed list of strings

    Raises:
        TypeError
    """

    # Input could be None, so test for that case
    if input_list is None:
        return []

    return [item[:-1] if len(item) >= 2 and item.endswith(os.sep)
            else item for item in input_list]

########################################


def was_processed(processed, path_name, verbose):
    """
    Check if a file or directory has already been processed.

    To prevent recursion, expand the path name to an absolution path
    call this function with a set that will store all the entries and
    the entry to test. If the entry is already in the set, report the issue
    and return ``True``. Otherwise, add the entry to the set and return
    ``False`` to allow the path to be processed.

    Args:
        processed: Set to store processed pathnames
        path_name: Path to a directory or file
        verbose: True if verbose output is requested

    Returns:
        True if it's already in the set. False if not.
    """

    # Test for recursion
    if path_name in processed:
        if verbose:
            print("{} has already been processed".format(path_name))
        return True

    # Mark this list as "processed" to prevent recursion
    if verbose:
        print("Processing {}.".format(path_name))
    processed.add(path_name)
    return False

########################################


def fixup_args(args):
    """
    Check unused args if they are directories, files or configurations

    The args object has the attributes ``args``, ``directories``,
    ``configurations``, and ``files``. The attribute args has all the unparsed
    arguments that will be tested to see if they are a file, directory or a
    string. The entries will be added to their appropriate attribute, with
    strings appended to ``configurations``. Attribute ``args`` is set to None.

    Args:
        args: args class from argparser
    """

    # Remove trailing os separator
    # This caused issues with parsing Xcode folders
    args.args = remove_ending_os_sep(args.args)
    args.directories = remove_ending_os_sep(args.directories)

    # Insure configurations is initialized
    if not args.configurations:
        args.configurations = []

    # Insure file list is initialized
    if not args.files:
        args.files = []

    # Process the orphaned arguments and determine if they
    # are configurations, files or directories
    if args.args:
        for item in args.args:
            filename = os.path.abspath(item)
            if os.path.isfile(filename):
                args.files.append(filename)
            elif os.path.isdir(filename):
                args.directories.append(filename)
            else:
                args.configurations.append(item)
        args.args = None

    # Ensure all files and directories are absolute paths
    cwd = os.getcwd()
    args.directories = norm_paths(cwd, args.directories)
    args.files = norm_paths(cwd, args.files)

    # Hack to convert XCode directories into files
    temp_list = []
    for item in args.directories:
        if item.endswith(".xcodeproj"):
            filename = os.path.join(item, _XCODEPROJECT_FILE)
            if os.path.isfile(filename):
                # Convert to a file
                args.files.append(filename)
                continue
        # Leave the directory in the list
        temp_list.append(item)
    args.directories = temp_list
