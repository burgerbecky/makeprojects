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
from operator import attrgetter
from burger import convert_to_array, import_py_script
from .config import BUILD_RULES_PY, save_default, _XCODEPROJECT_FILE
from .__init__ import _XCODEPROJ_MATCH, __version__
from .util import get_build_rules, getattr_build_rules, was_processed, \
    fixup_args
from .core import BuildError
from .modules import MODULES
from .python import create_clean_rules_objects, BuildPythonFile

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


def add_clean_rules(projects, working_directory,
                    file_name, args, build_rules=None):
    """
    Add a build_rules.py to the clean list.

    Given a build_rules.py to parse, check for the function "clean"
    and use that for scanning for functions to call.

    All valid entries will be appended to the projects list.

    Args:
        projects: List of projects to clean.
        file_name: Pathname to the build_rules.py file.
        args: Args for determining verbosity for output.
        build_rules: Preloaded build_rules.py object.
    See Also:
        add_project
    """

    file_name = os.path.abspath(file_name)

    # Was the build_rules already loaded?
    if not build_rules:
        build_rules = import_py_script(file_name)

    dependencies = []

    # Was a build_rules.py file found?
    if build_rules:
        if args.verbose:
            print('Using configuration file {}'.format(file_name))

        # Test for functions and append all that are found
        if working_directory is None:
            working_directory = os.path.dirname(file_name)
        parms = {
            'working_directory': working_directory}

        # Get the dependency list
        dependencies = getattr(build_rules, 'CLEANME_DEPENDENCIES', None)
        if dependencies is None:
            # Try the generic one
            dependencies = getattr(build_rules, 'DEPENDENCIES', None)

        if dependencies:
            # Ensure it's an iterable of strings
            items = convert_to_array(dependencies)
            dependencies = []
            for item in items:
                if not os.path.isabs(item):
                    dependencies.append(os.path.abspath(
                        os.path.join(working_directory, item)))
                else:
                    dependencies.append(item)
        else:
            dependencies = []

        # Add build object found in the build_rules.py file
        projects.extend(
            create_clean_rules_objects(
                file_name,
                build_rules,
                parms,
                args.verbose))
    return dependencies


########################################


def add_project(projects, processed, file_name, args):
    """
    Detect the project type and add it to the list.

    Args:
        projects: List of projects to build.
        processed: List of directories already processed.
        file_name: Pathname to the build_rules.py file.
        args: Args for determining verbosity for output.
    Returns:
        True if the file was buildable, False if not.
    """

    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches

    # Check if the file is accepted by a build module
    for module in MODULES:

        # Match the file?
        if module.match(file_name):

            # Test for recursion
            if was_processed(processed, file_name, args.verbose):
                return True

            # Create the build objects
            projects.extend(
                module.create_clean_object(
                    file_name,
                    configurations=args.configurations,
                    verbose=args.verbose))
            return True

    return False

########################################


def process_projects(results, projects, args):
    """
    Process a list of projects

    Sort the projects by priority and build all of them.
    """
    # Sort the list by priority (The third parameter is priority from 1-99)
    error = 0
    projects = sorted(projects, key=attrgetter('priority'))

    # If in preview mode, just show the generated build objects
    # and exit
    if args.preview:
        for project in projects:
            print(project)
        return False

    # Clean all the projects
    # Note, python objects are a special case, if any return a
    # non "None" error code, don't call any others

    python_none = False
    for project in projects:

        # Skip all python clean objects if a numeric error code
        # was already obtained
        if isinstance(project, BuildPythonFile) and python_none:
            continue

        berror = project.clean()
        error = 0
        if berror is not None:
            results.append(berror)
            error = berror.error

            # Check the error code, was it None?
            if error is not None:
                if isinstance(project, BuildPythonFile):
                    # Don't parse any more python "clean" scripts
                    python_none = True

        # Abort on error?
        if error and args.fatal:
            return True
    return False

########################################


def process_files(results, processed, files, args):
    """
    Process a list of files.
    """
    projects = []
    for item in files:
        full_name = os.path.abspath(item)
        base_name = os.path.basename(full_name)
        if base_name == args.rules_file:
            if not was_processed(processed, full_name, args.verbose):
                process_dependencies(
                    results, processed, add_clean_rules(
                        projects, None, full_name, args), args)
        elif not add_project(projects, processed, full_name, args):
            print('"{}" is not supported.'.format(full_name))
            return True
    return process_projects(results, projects, args)

########################################


def process_directories(results, processed, directories, args):
    """
    Process a list of directories.

    Args:
        results: list object to append BuildError objects
        processed: List of directories already processed.
        directories: iterable list of directories to process
        args: parsed argument list for verbosity
    Returns:
        True if processing should abort, False if not.
    """

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-nested-blocks

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
            msg = "{} is not a directory.".format(working_directory)
            results.append(BuildError(10, working_directory, msg=msg))
            if args.fatal:
                return True
            continue

        # Are there build rules in this directory?
        build_rules_list = get_build_rules(
            working_directory, args.verbose, args.rules_file, "CLEANME")

        # Is recursion allowed?
        allow_recursion = not getattr_build_rules(
            build_rules_list, ("CLEANME_NO_RECURSE", "NO_RECURSE"), False)

        allow_files = getattr_build_rules(
            build_rules_list, ("CLEANME_PROCESS_PROJECT_FILES",), True)

        # Pass one, create a list of all projects to build
        projects = []

        # Process all of the dependencies first, then this folder
        for build_rules in build_rules_list:
            process_dependencies(
                results,
                processed,
                add_clean_rules(
                    projects,
                    working_directory,
                    build_rules.__file__,
                    args,
                    build_rules),
                args)

        # Iterate over the directory to find all the other files
        if allow_files:
            for entry in os.listdir(working_directory):

                full_name = os.path.join(working_directory, entry)

                # If it's a directory, check for recursion
                if os.path.isdir(full_name):

                    # Special case for xcode, if it's a *.xcodeproj
                    if _XCODEPROJ_MATCH.match(entry):

                        # Check if it's an xcode project file, if so, add it
                        if not add_project(projects, processed, os.path.join(
                                full_name, _XCODEPROJECT_FILE), args):
                            print(
                                ('"{}" is not supported on this platform.')
                                .format(full_name))
                            return True
                        continue

                    if args.recursive and allow_recursion:
                        # Process the directory first
                        if process_directories(
                                results, processed, [full_name],
                                args):
                            # Abort?
                            return True
                    continue

                # It's a file, process it, if possible
                # Don't double process the rules file
                if args.rules_file != entry:
                    add_project(projects, processed, full_name, args)

        # The list is ready, process it in priority order
        # and then loop to the next directory to process
        temp = process_projects(results, projects, args)
        if temp:
            return temp
    return False

########################################


def process_dependencies(results, processed, dependencies, args):
    """
    Process a mixed string list of both directories and files.

    Iterate over the dependencies list and test each object if it's a directory,
    and if so, dispatch to the directory handler, otherwise, process as a file.

    Args:
        results: list object to append BuildError objects
        processed: List of directories already processed.
        dependencies: iterable list of files/directories to process
        args: parsed argument list for verbosity
    Returns:
        True if processing should abort, False if not.
    """

    if dependencies:
        for item in dependencies:
            if os.path.isdir(item):
                error = process_directories(results, processed, [item], args)
            elif os.path.isfile(item):
                error = process_files(results, processed, [item], args)
            else:
                error = 0
            if error:
                return error
    return 0


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

    # List of errors created during building
    results = []
    processed = set()

    # Try building all individual files first
    if not process_files(results, processed, files, args):

        # If successful, process all directories
        process_directories(results, processed, directories, args)

    # Was there a build error?
    error = 0
    for item in results:
        if item.error:
            print('Errors detected in clean.')
            error = item.error
            break
    else:
        if args.verbose:
            print('Clean is successful!')

    # Dump the error log if requested or an error
    if args.verbose or error:
        for item in results:
            if args.verbose or item.error:
                print(item)
    return error


# If called as a function and not a class,
# call my main

if __name__ == "__main__":
    sys.exit(main())
