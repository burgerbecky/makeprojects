#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Rebuild a project.

Package that handles the command line program ``rebuildme``.

The command ``rebuildme`` calls ``cleanme`` and then ``buildme`` in that order.

See Also:
    main, makeprojects.buildme, makeprojects.cleanme

@package makeprojects.rebuildme
"""

# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os
import argparse
from makeprojects import buildme, cleanme
from .__init__ import __version__
from .config import BUILD_RULES_PY, save_default

########################################


def main(working_directory=None, args=None):
    """
    Invoke the command line ``rebuildme``.

    Entry point for the program ``rebuildme``, this function
    will either get the parameters from ``sys.argv`` or the paramater ``args``.

    - ``--version``, show version.
    - ``-r``, Perform a recursive rebuild.
    - ``-v``, Verbose output.
    - ``--generate-rules``, Create build_rules.py and exit.
    - ``--rules-file``, Override the configruration file.
    - ``-f``, Stop building on the first build failure.
    - ``-d``, List of directories to rebuild.
    - ``-docs``, Compile Doxyfile files.
    - Additional terms are considered specific files to build.

    Args:
        working_directory: Directory to rebuild, or ``None`` for ``os.getcwd()``
        args: Command line to use instead of ``sys.argv``
    Returns:
        Zero on no error, non-zero on error
    """

    # Too many branches
    # pylint: disable=R0912

    # Make sure the working directory is set
    if working_directory is None:
        working_directory = os.getcwd()

    # Parse the command line
    parser = argparse.ArgumentParser(
        description='Rebuild project files. Copyright by Rebecca Ann Heineman. '
        'Invokes cleanme and then buildme.')

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('-r', '-all', dest='recursive', action='store_true',
                        default=False, help='Perform a recursive rebuild')
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

    parser.add_argument('-f', dest='fatal', action='store_true',
                        default=False, help='Quit immediately on any error.')
    parser.add_argument('-d', dest='directories', action='append',
                        metavar='<directory>', default=[],
                        help='List of directories to build in.')
    parser.add_argument('-docs', dest='documentation', action='store_true',
                        default=False, help='Compile Doxyfile files.')

    # Parse everything
    args, project_files = parser.parse_known_args(args=args)

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

    # Generate command lines for the tools
    cleanargs = []
    buildargs = []

    # Recursive
    if args.recursive:
        cleanargs.append('-r')
        buildargs.append('-r')

    # Verbose output
    if args.verbose:
        cleanargs.append('-v')
        buildargs.append('-v')

    # Config file
    if args.rules_file:
        cleanargs.extend(['--rules-file', args.rules_file])
        buildargs.extend(['--rules-file', args.rules_file])

    # Fatal
    if args.fatal:
        buildargs.append('-f')

    # Doxygen
    if args.documentation:
        buildargs.append('-docs')

    # Directories to build
    for item in args.directories:
        cleanargs.extend(['-d', item])
        buildargs.extend(['-d', item])

    # Excess entries
    for item in project_files:
        buildargs.append(item)

    # Clean and then build, couldn't be simpler!
    if args.verbose:
        print('cleanme ' + ' '.join(cleanargs))
    error = cleanme.main(working_directory, args=cleanargs)
    if not error:
        if args.verbose:
            print('buildme ' + ' '.join(buildargs))
        error = buildme.main(working_directory, args=buildargs)
    return error


# If called as a function and not a class, call my main
if __name__ == "__main__":
    sys.exit(main())
