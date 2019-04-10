#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Package that reads, parses and processes the configuration file
"""

## \package makeprojects.config

from __future__ import absolute_import, print_function, unicode_literals

import os
import shutil
import burger

## build_rules.py file to detect secondly
_BUILD_RULES = 'build_rules.py'

## BUILD_RULES location environment variable
_BUILD_RULES_VAR = 'BUILD_RULES'

## Location of the user's home directory
USER_HOME = os.path.expanduser('~')

if 'MAKE_PROJECTS_HOME' in os.environ:
    ## Location of makeprojects home directory if redirected
    PROJECTS_HOME = os.environ['MAKE_PROJECTS_HOME']
else:
    PROJECTS_HOME = USER_HOME

########################################


def savedefault(working_dir=None, destinationfile='build_rules.py'):
    """
    Calls the internal function to save a default .projectsrc file

    Given a pathname, create and write out a default .projectsrc file
    that can be used as input to makeprojects to generate project files.

    Args:
        working_dir: Directory to save the destination file if it's not a full pathname
        destinationfile: Pathname of where to save the default configuation file
    """

    # If the destination is not an absolute path...
    if not os.path.isabs(destinationfile):
        # Prepend the working directory
        if not working_dir:
            working_dir = os.getcwd()
        # Create the path to store the configuration file
        destinationfile = os.path.join(working_dir, destinationfile)

    # Get the source file path
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_rules.py')

    # Copy the file
    try:
        shutil.copyfile(src, destinationfile)
    except OSError as error:
        print(error)

########################################


def find_build_rules(working_dir=None):
    """
    Search for the build_rules.py file.

    Scan for the build_rules.py file starting from the current working directory
    and search downwards until the root directoy is it. If not found, search in
    the user's home directory or for linux/macOS, in /etc

    Args:
        working_dir: Directory to scan first for the preferences file, None to
            use the current working directory
    Returns:
        Pathname of the configuration file, or None if no file was found.
    """

    # Is there a makeprojects rc file in the current directory or
    # any directory in the chain?

    if working_dir is None:
        working_dir = os.getcwd()

    result = burger.traverse_directory(working_dir, _BUILD_RULES, True)
    if result:
        return result[0]

    # See if there's an environment variable pointing to a file
    if _BUILD_RULES_VAR in os.environ and \
            os.path.exists(os.environ[_BUILD_RULES_VAR]):
        result = os.environ[_BUILD_RULES_VAR]
    else:
        # Scan the usual suspects for a global instance

        # If '~' doesn't expand or /root, use the current folder
        if USER_HOME == '~' or USER_HOME == '/root':
            result = _BUILD_RULES
        else:
            # Check the user's home folder
            result = os.path.join(USER_HOME, _BUILD_RULES)
            if os.path.isfile(result):
                return result
            result = os.path.join(USER_HOME, '.config', _BUILD_RULES)

    if not os.path.isfile(result):

        # If not found, use /etc/projectsrc for system globals on non
        # windows platforms
        if not burger.get_windows_host_type() and \
                os.path.isfile('/etc/' + _BUILD_RULES):
            result = '/etc/' + _BUILD_RULES
        else:
            result = None
    return result


## Full pathname of the configuration file
BUILD_RULES = find_build_rules()

########################################


def import_configuration(file_name=None, verbose=True):
    """
    Load in the configuration file

    Using the file PROJECTSRC, load it in and parse it as an INI
    file using the configparser python class.

    Args:
        file_name: File to load for configuration
        verbose: If True, print the loaded file''s name.

    Returns:
        An empty parser object or filled with a successfully loaded file
    """

    if file_name is None:
        file_name = BUILD_RULES

    build_rules = None
    if file_name and os.path.exists(file_name):
        build_rules = burger.import_py_script(file_name)
        if verbose:
            print('Using configuration file {}'.format(file_name))
    elif verbose:
        print('No configuration file found, using defaults')
        build_rules = burger.import_py_script(
            os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)),
                'build_rules.py'))
    return build_rules
