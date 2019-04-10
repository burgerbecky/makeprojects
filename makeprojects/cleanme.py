#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Remove all temporary files in a project's folder
"""

## \package makeprojects.cleanme

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import argparse
from .config import import_configuration
from .__pkginfo__ import VERSION

########################################


def recurse(build_rules, working_dir):
    """
    Process every directory
    """

    error = build_rules.clean_rules(working_dir)
    if not error:
        # Iterate over the directory
        for item in os.listdir(working_dir):
            path_name = os.path.join(working_dir, item)
            if os.path.isdir(path_name):
                error = recurse(build_rules, path_name)
                if error:
                    break
    return error


########################################

def main(working_dir=None, args=None):
    """
    Command line shell for cleanme

    Args:
        working_dir: Directory to operate on, or None for os.getcwd()
        args: Command line to use instead of sys.argv
    Returns:
        Zero
    """

    # Make sure working_dir is properly set
    if working_dir is None:
        working_dir = os.getcwd()

    # Parse the command line
    parser = argparse.ArgumentParser(
        description='Remove project output files. '
        'Copyright by Rebecca Ann Heineman',
        add_help=True)

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument('-r', '-all', dest='recursive', action='store_true',
                        default=False, help='Perform a recursive clean')
    parser.add_argument('-v', '-verbose', dest='verbose', action='store_true',
                        default=False, help='Verbose output.')
    parser.add_argument('--generate-rules', dest='generate_build_rules',
                        action='store_true', default=False,
                        help='Generate a sample configuration file and exit.')
    parser.add_argument('--rules-file', dest='rules_file',
                        metavar='<file>', default=None, help='Specify a configuration file.')

    # Parse everything
    args = parser.parse_args(args=args)

    # Output default configuration
    if args.generate_build_rules:
        from .config import savedefault
        savedefault(working_dir)
        return 0

    # True if debug spew is requested
    verbose = args.verbose

    # Load the configuration file
    build_rules = import_configuration(file_name=args.rules_file, verbose=verbose)
    if build_rules is None:
        if verbose:
            print('build_rules.py was corrupt.')
        return 1

    error = 0
    if hasattr(build_rules, 'clean_rules'):
        if args.recursive:
            error = recurse(build_rules, working_dir)
        else:
            error = build_rules.clean_rules(working_dir)

    # Wrap up!
    if verbose:
        print('cleanme is complete.')
    return error


# If called as a function and not a class,
# call my main

if __name__ == "__main__":
    sys.exit(main())
