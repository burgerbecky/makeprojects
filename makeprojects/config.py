#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Package that reads, parses and processes the configuration file
"""

## \package makeprojects.config

from __future__ import absolute_import, print_function, unicode_literals

import os
from shutil import copyfile
from burger import get_windows_host_type, import_py_script

## build_rules.py file to detect secondly
BUILD_RULES_PY = 'build_rules.py'

## BUILD_RULES_PY location environment variable
_BUILD_RULES_VAR = 'BUILD_RULES'

## Location of the user's home directory
USER_HOME = os.path.expanduser('~')

if 'MAKE_PROJECTS_HOME' in os.environ:
    ## Location of makeprojects home directory if redirected
    PROJECTS_HOME = os.environ['MAKE_PROJECTS_HOME']
else:
    PROJECTS_HOME = USER_HOME

########################################


def save_default(working_directory=None, destinationfile=BUILD_RULES_PY):
    """
    Calls the internal function to save a default .projectsrc file

    Given a pathname, create and write out a default .projectsrc file
    that can be used as input to makeprojects to generate project files.

    Args:
        working_directory: Directory to save the destination file
        destinationfile: Pathname of where to save the default configuation file
    """

    # If the destination is not an absolute path...
    if not os.path.isabs(destinationfile):
        # Prepend the working directory
        if not working_directory:
            working_directory = os.getcwd()
        # Create the path to store the configuration file
        destinationfile = os.path.join(working_directory, destinationfile)

    # Get the source file path
    src = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        BUILD_RULES_PY)

    # Copy the file
    try:
        copyfile(src, destinationfile)
    except OSError as error:
        print(error)

########################################


def find_default_build_rules():
    """
    Search for the build_rules.py file.

    Scan for the build_rules.py file starting from the current working directory
    and search downwards until the root directoy is it. If not found, search in
    the user's home directory or for linux/macOS, in /etc

    Returns:
        Pathname of the configuration file, or None if no file was found.
    """

    # See if there's an environment variable pointing to a file
    while True:
        if _BUILD_RULES_VAR in os.environ and os.path.exists(
                os.environ[_BUILD_RULES_VAR]):
            result = os.environ[_BUILD_RULES_VAR]
            if os.path.isfile(result):
                break

        # Scan the usual suspects for a global instance

        # If '~' doesn't expand or /root, use the current folder
        if USER_HOME not in ('~', '/root'):
            # Check the user's home folder
            result = os.path.join(USER_HOME, BUILD_RULES_PY)
            if os.path.isfile(result):
                break

            result = os.path.join(USER_HOME, '.config', BUILD_RULES_PY)
            if os.path.isfile(result):
                break

        # If not found, use /etc/projectsrc for system globals on non
        # windows platforms
        if not get_windows_host_type():
            result = '/etc/' + BUILD_RULES_PY
            if os.path.isfile(result):
                break

        result = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)),
            BUILD_RULES_PY)
        break

    return result


## Full pathname of the configuration file
DEFAULT_BUILD_RULES = find_default_build_rules()

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
        file_name = DEFAULT_BUILD_RULES

    build_rules = None
    if file_name and os.path.exists(file_name):
        build_rules = import_py_script(file_name)
        if verbose:
            if build_rules:
                print('Using configuration file {}'.format(file_name))
            else:
                print('build_rules.py was corrupt.')
    else:
        if verbose:
            print('No configuration file found, using defaults')
        build_rules = import_py_script(
            os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)),
                BUILD_RULES_PY))
    return build_rules
