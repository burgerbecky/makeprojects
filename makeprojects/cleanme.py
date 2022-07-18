#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Remove all temporary files in a project's folder.

Scan the current directory for the file build_rules.py and look for
the function ``clean`` and call it.

Full documentation on the operation of [``cleanme`` is here](cleanme_man.md).

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
from .config import BUILD_RULES_PY, save_default
from .__init__ import __version__, _XCODEPROJ_MATCH
from .util import get_build_rules, getattr_build_rules, was_processed, \
    fixup_args

########################################


def create_parser():
    """
    Create the parser to process the command line for buildme

    The returned object has these member variables

    - version boolean if version is requested
    - recursive boolean for directory recursion
    - verbose boolean for verbose output
    - preview boolean for previewing the clean process
    - generate_build_rules boolean create build rules and exit
    - rules_file string override build_rules.py
    - fatal boolean abort if error occurs in processing
    - directories string array of directories to process
    - files string array of project files to process
    - configurations string array of configurations to process
    - args string array of unknown parameters

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

    parser.add_argument('-n', '-preview', dest='preview', action='store_true',
                        default=False, help='Preview clean commands.')

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

    parser.add_argument('-q', dest='fatal', action='store_true',
                        default=False, help='Quit immediately on any error.')

    parser.add_argument('-f', dest='files', action='append',
                        metavar='<filename>',
                        help='Project file to process.')

    parser.add_argument('-d', dest='directories', action='append',
                        metavar='<directory>', default=[],
                        help='List of directories to clean.')

    parser.add_argument('-c', dest='configurations', action='append',
                        metavar='<configuration>',
                        help='Configuration to process.')

    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='project filenames')

    return parser

########################################


def process_directories(processed, directories, args):
    """
    Clean a list of directories.

    The ``args`` parameter list is an object with these attributes:
    * ``verbose`` If True, verbose output will be printed to the console
    * ``rules_file`` Name of the rules file, should be ``build_rules.py``
    * ``recursive`` If True, recursively process all directories

    Args:
        processed: Set of directories already processed.
        directories: iterable list of directories to process
        args: parsed argument list for verbosity
    Returns:
        Zero on no error, non zero integer on error
    """

    # pylint: disable=too-many-nested-blocks
    # pylint: disable=too-many-branches

    error = 0

    # Process the directory list
    for working_directory in directories:

        # Sanitize the directory
        working_directory = os.path.abspath(working_directory)

        # Was this directory already processed?
        if was_processed(processed, working_directory, args.verbose):
            # Technically not an error to abort processing, so skip
            continue

        # Only process directories
        if not os.path.isdir(working_directory):
            print("{} is not a directory.".format(working_directory))
            error = 10
            break

        # Are there build rules in this directory?
        build_rules_list = get_build_rules(
            working_directory, args.verbose, args.rules_file, "CLEANME")

        # Is recursion allowed?
        allow_recursion = not getattr_build_rules(
            build_rules_list, ("CLEANME_NO_RECURSE", "NO_RECURSE"), False)

        # Process all of the dependencies first, then this folder
        for build_rules in build_rules_list:

            # Check if there is dependency list
            dependencies = getattr(build_rules, 'CLEANME_DEPENDENCIES', None)
            if dependencies is None:
                dependencies = getattr(build_rules, 'DEPENDENCIES', None)

            if dependencies:
                # Ensure it's an iterable of strings
                dir_list = []
                dependencies = convert_to_array(dependencies)
                for item in dependencies:
                    if not os.path.isabs(item):
                        item = os.path.join(working_directory, item)
                        # Ensure there is a directory
                        # This prevents recursion issues
                        if not os.path.isdir(item):
                            continue
                    dir_list.append(item)

                # Process these directories first.
                error = process_directories(
                    processed, dir_list, args)
                if error:
                    break

            # Call the clean() proc in the build_rules.py file, if it exists
            clean_proc = getattr(build_rules, 'clean', None)
            if not callable(clean_proc):
                print(
                    "Function clean in {} is not a callable function".format(
                        build_rules.__file__))
                error = 12
                break

            error = clean_proc(working_directory=working_directory)
            if error is not None:
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

                # Only deal with directories, ignore all files
                path_name = os.path.join(working_directory, item)
                if os.path.isdir(path_name):
                    # Prevent double processing
                    if path_name not in processed:
                        error = process_directories(
                            processed, [path_name], args)
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
    - ``-n``, Preview clean commands
    - ``--generate-rules``, Create build_rules.py and exit.
    - ``--rules-file``, Override the configruration file.
    - ``-q``, Quit after the first error
    - ``-f``, List of files to build.
    - ``-d``, List of directories to clean.
    - ``-c``, List of configurations to build
    - Additional terms are considered specific files or configurations to clean.

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
        if args.verbose:
            print(
                "Saving {}".format(
                    os.path.join(
                        working_directory,
                        args.rules_file)))
        save_default(working_directory, destinationfile=args.rules_file)
        return 0

    # Handle extra arguments
    fixup_args(args)

    # Get lists of files/directories to build
    files = args.files
    directories = args.directories

    # If there are no entries, use the working directory
    if not directories and not files:
        directories = [working_directory]

    # Process the list of directories.
    # Pass an empty set for recursion testing
    error = process_directories(set(), directories, args)

    # Wrap up!
    if args.verbose:
        print('Clean is successful!')
    return error


# If called as a function and not a class,
# call my main

if __name__ == "__main__":
    sys.exit(main())
