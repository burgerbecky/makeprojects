#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Remove all temporary files in a project's folder.

Scan the current directory for the file build_rules.py and look for
the function ``clean_rules`` and call it.

This is the default function prototype for directory cleaning. It will
only be called in the directory that the file build_rules.py resides.
@code
def clean_rules(working_directory):
    return 0
@endcode

This version will be called from any directory, it's preferred for generic
cleaning functions that check for specific files for removal.
@code
def clean_rules(working_directory=None):
    return 0
@endcode

This version will be called from a specific directory. It's useful for generic
cleaning functions that are limited to a specific folder.
@code
def clean_rules(working_directory='C:\\projects\\mygreatapplication'):
    return 0
@endcode

If the parameter ``root`` exists, the default parameter will be checked for
``True`` to determine if this cleaning function is the last one to execute and
no more build_rules.py files will be searched for. The value ``root`` is not
set by cleanme and is not expected to be used by ``clean_rules``.
@code
def clean_rules(working_directory, root=True):
    return 0
@endcode

See Also:
    main, makeprojects.buildme, makeprojects.rebuildme

@package makeprojects.cleanme
"""

# pylint: disable=useless-object-inheritance
# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import argparse
from burger import convert_to_array
from .config import BUILD_RULES_PY, DEFAULT_BUILD_RULES
from .__init__ import __version__, _XCODEPROJ_MATCH
from .buildme import remove_os_sep, was_processed
from .util import add_build_rules

########################################


def get_build_rules(working_directory, args):
    """
    Find all build_rules.py that apply to this directory.

    Args:
        working_directory: Directory to scan for build_rules.py
        args: Args for determining verbosity for output
    Returns:
        List of loaded build_rules.py files.
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
                temp_dir, args.rules_file), args.verbose, is_root, "CLEANME"):
            # Abort if CLEANME_CONTINUE = False
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
                args.verbose,
                True,
                "CLEANME")
            break
        # Use the new folder
        temp_dir = temp_dir2
    return build_rules_list

########################################


def getattr_build_rules(build_rules_list, attribute, default):
    """
    Find an attribute in a list of build rules.

    Iterate over the build rules list until an entry has an attribute value.
    It will return the first one found.

    Args:
        build_rules_list: List of build_rules.py instances.
        attribute: Attribute name to check for.
        default: Value to return if the attribute was not found.
    Returns:
        default or attribute value.
    """

    for build_rules in build_rules_list:
        # Does the entry have this attribute?
        try:
            return getattr(build_rules, attribute)
        except AttributeError:
            pass
    # Return the default value
    return default

########################################


def create_parser():
    """
    Create the parser to process the command line for buildme

    The returned object has these member variables

    - version boolean if version is requested
    - recursive boolean for directory recursion
    - verbose boolean for verbose output
    - generate_build_rules boolean create build rules and exit
    - rules_file string override build_rules.py
    - directories string array of directories to process

    Returns:
        argparse.ArgumentParser() object
    """

    # Parse the command line
    parser = argparse.ArgumentParser(
        description='Remove project output files. '
        'Copyright by Rebecca Ann Heineman')

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)

    parser.add_argument('-r', '-all', dest='recursive', action='store_true',
                        default=False, help='Perform a recursive clean')

    parser.add_argument('-v', '-verbose', dest='verbose', action='store_true',
                        default=False, help='Verbose output.')

    parser.add_argument('--generate-rules', dest='generate_build_rules',
                        action='store_true', default=False,
                        help='Generate a sample configuration file and exit.')

    parser.add_argument(
        '--rules-file',
        dest='rules_file',
        metavar='<file>',
        default=BUILD_RULES_PY,
        help='Specify a configuration file.')

    parser.add_argument('-d', dest='directories', action='append',
                        metavar='<directory>', default=[],
                        help='List of directories to clean.')

    return parser

########################################


def fixup_args(args):
    """
    Perform argument cleanup

    Args:
        args: args class from argparser
    """

    # Remove trailing os seperator
    args.directories = remove_os_sep(args.directories)
    args.directories = [os.path.abspath(item) for item in args.directories]

########################################


def process_directories(processed, directories, args):
    """
    Clean a list of directories.

    Args:
        processed: Set of directories already processed.
        directories: iterable list of directories to process
        args: parsed argument list for verbosity
    Returns:
        Zero on no error, non zero integer on error
    """

    error = 0

    # Process the directory list
    for working_directory in directories:

        # Sanitize the directory
        working_directory = os.path.abspath(working_directory)

        # Was this directory already processed?
        if was_processed(processed, working_directory):
            # Technically not an error to abort processing, so skip
            continue

        if args.verbose:
            print('Cleaning "{}".'.format(working_directory))

        # Are there build rules?
        build_rules_list = get_build_rules(working_directory, args)

        # Is recursion allowed?
        allow_recursion = not getattr_build_rules(
            build_rules_list, 'CLEANME_NO_RECURSE', False)

        # Process all files needed.

        for build_rules in build_rules_list:

            item = getattr(build_rules, 'CLEANME_DEPENDENCIES', None)
            if item:
                # Ensure it's an iterable of strings
                dir_list = []
                item = convert_to_array(item)
                for i in item:
                    if not os.path.isabs(i):
                        i = os.path.join(working_directory, i)
                        # Ensure there is a directory
                        # This prevents recursion issues
                        if not os.path.isdir(i):
                            continue
                    dir_list.append(i)
                error = process_directories(
                    processed, dir_list, args)
                if error:
                    break

            clean_proc = getattr(build_rules, 'clean', None)
            if callable(clean_proc):
                # pylint: disable=not-callable
                error = clean_proc(working_directory=working_directory)
                if error:
                    break

        # If recursive, process all the sub folders
        if args.recursive and not error and allow_recursion:
            # Iterate over the directory
            for item in os.listdir(working_directory):

                # Ignore xcode project directories
                if _XCODEPROJ_MATCH.match(item):
                    continue

                # Ignore the build_rules.py file
                if item == args.rules_file:
                    continue

                path_name = os.path.join(working_directory, item)
                if os.path.isdir(path_name):
                    error = process_directories(processed, [path_name], args)
                    if error:
                        break

    return error

########################################


def main(working_directory=None, args=None):
    """
    Command line shell for ``cleanme``.

    Entry point for the program ``cleanme``, this function
    will either get the parameters from sys.argv or the paramater ``args``.

    - ``--version``, show version.
    - ``-r``, Perform a recursive clean.
    - ``-v``, Verbose output.
    - ``--generate-rules``, Create build_rules.py and exit.
    - ``--rules-file``, Override the configruration file.
    - ``-d``, List of directories to clean.

    Args:
        working_directory: Directory to operate on, or None for os.getcwd()
        args: Command line to use instead of sys.argv
    Returns:
        Zero on no error, non-zero on error
    """

    # Create the parser
    parser = create_parser()

    # Parse everything
    args = parser.parse_args(args=args)

    # Make sure working_directory is properly set
    if working_directory is None:
        working_directory = os.getcwd()

    # Output default configuration
    if args.generate_build_rules:
        # pylint: disable=import-outside-toplevel
        from .config import save_default
        if args.verbose:
            print(
                'Saving {}'.format(
                    os.path.join(
                        working_directory,
                        BUILD_RULES_PY)))
        save_default(working_directory)
        return 0

    # Handle extra arguments
    fixup_args(args)

    # Make a list of directories to process
    if not args.directories:
        args.directories = [working_directory]

    # Process the list of directories.
    # Pass an empty set for recursion testing
    error = process_directories(set(), args.directories, args)

    # Wrap up!
    if args.verbose:
        print('cleanme is complete.')
    return error


# If called as a function and not a class,
# call my main

if __name__ == "__main__":
    sys.exit(main())
