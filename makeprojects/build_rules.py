#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Build rules for the makeprojects suite of build tools.

This file is parsed by the cleanme, buildme, rebuildme and makeprojects
command line tools to clean, build and generate project files.

When any of these tools are invoked, this file is loaded and parsed to
determine special rules on how to handle building the code and / or data.
"""

# pylint: disable=unused-argument

from __future__ import absolute_import, print_function, unicode_literals

import sys

# from makeprojects.enums import PlatformTypes, ProjectTypes, IDETypes

# Name of the project, default is the directory name
# PROJECT_NAME = "Project"

# Type of the project, default is ProjectTypes.tool
# PROJECT_TYPE = ProjectTypes.application

# Recommended IDE for the project. Default is IDETypes.default()
# PROJECT_IDE = IDETypes.vs2022

# Recommend target platform for the project.
# PROJECT_PLATFORM = PlatformTypes.windows

# ``cleanme`` will process any child directory with the clean() function if
# True. Overrides GENERIC
# CLEANME_GENERIC = False

# ``buildme`` will process any child directory with the prebuild(), build(),
# and postbuild() functions if True. Overrides GENERIC
# BUILDME_GENERIC = False

# Both ``cleanme`` and ``buildme`` will process any child directory with the
# clean(), prebuild(), build(), and postbuild() functions if True.
# Can be overridden above
GENERIC = False

# ``cleanme`` will process build_rules.py in the parent folder if True.
# Overrides CONTINUE
# CLEANME_CONTINUE = False

# ``buildme`` will process build_rules.py in the parent folder if True.
# Overrides CONTINUE
# BUILDME_CONTINUE = False

# ``cleanme`` and ``buildme`` will process build_rules.py in the parent folder
# if True. Default is false
# Can be overridden above
CONTINUE = False

# ``cleanme`` will clean the listed folders using their rules before cleaning
# this folder. Overrides DEPENDENCIES
# CLEANME_DEPENDENCIES = []

# ``buildme``` will build these files and folders first. Overrides DEPENDENCIES
# BUILDME_DEPENDENCIES = []

# Process these folders before processing this folder
# Can be overridden above
DEPENDENCIES = None

# If set to True, ``cleanme -r`` will not parse directories in this folder.
# Overrides NO_RECURSE
# CLEANME_NO_RECURSE = True

# If set to True, ``buildme -r`` will not parse directories in this folder.
# Overrides NO_RECURSE
# BUILDME_NO_RECURSE = True

# If set to True, Don't parse directories in this folder when ``-r``
# is active.
# Can be overridden above
NO_RECURSE = False

# ``cleanme`` will assume only the function ``clean()`` is used if False.
# Overrides PROCESS_PROJECT_FILES
# CLEANME_PROCESS_PROJECT_FILES = False

# ``buildme`` will assume only the three functions are used if False.
# Overrides PROCESS_PROJECT_FILES
# BUILDME_PROCESS_PROJECT_FILES = False

# If any IDE file is present, cleanme and buildme will process them.
# Can be overridden above
PROCESS_PROJECT_FILES = True

########################################


def prebuild(working_directory, configuration):
    """
    Perform actions before building any IDE based projects.

    This function is called before any IDE or other script is invoked. This is
    perfect for creating headers or other data that the other build projects
    need before being invoked.

    On exit, return 0 for no error, or a non zero error code if there was an
    error to report. Return None to allow a parent folder's prebuild() function
    to execute.

    Args:
        working_directory
            Directory this script resides in.

        configuration
            Configuration to build, ``all`` if no configuration was requested.

    Returns:
        None if allowing parent folder to execute, otherwise an integer error
        code.
    """
    return None

########################################


def build(working_directory, configuration):
    """
    Build code or data before building IDE project but after data generation.

    Commands like ``makerez`` and ``slicer`` are called before this function is
    invoked so it can assume headers and / or data has been generated before
    issuing custom build commands.

    On exit, return 0 for no error, or a non zero error code if there was an
    error to report. Return None to allow a parent folder's build() function
    to execute.

    Args:
        working_directory
            Directory this script resides in.

        configuration
            Configuration to build, ``all`` if no configuration was requested.

    Returns:
        None if allowing parent folder to execute, otherwise an integer error
        code.
    """
    return None

########################################


def postbuild(working_directory, configuration):
    """
    Issue build commands after all IDE projects have been built.

    This function can assume all other build projects have executed for final
    deployment or cleanup

    On exit, return 0 for no error, or a non zero error code if there was an
    error to report. Return None to allow a parent folder's postbuild() function
    to execute.

    Args:
        working_directory
            Directory this script resides in.

        configuration
            Configuration to build, ``all`` if no configuration was requested.

    Returns:
        None if allowing parent folder to execute, otherwise an integer error
        code.
    """
    return None

########################################


def clean(working_directory):
    """
    Delete temporary files.

    This function is called by ``cleanme`` to remove temporary files.

    On exit, return 0 for no error, or a non zero error code if there was an
    error to report.

    Args:
        working_directory
            Directory this script resides in.

    Returns:
        None if not implemented, otherwise an integer error code.
    """
    return None

########################################


def configuration_list(platform, ide):
    """
    Return names of configurations.

    The default is to generate configuration names of "Release",
    "Debug", etc. If an override is desired, return a list of strings
    containing the names of the default configurations.

    Args:
        platform: PlatformTypes of the platform being built
        ide: IDE project being generated for.
    Returns:
        None or list of configuration names.
    """

    # Only generate for the Release configuration
    # return ["Release"]
    return None

########################################


def project_settings(project):
    """
    Set up defines and default libraries.

    Adjust the default settings for the project to generate. Usually it's
    setting the location of source code or perforce support.

    Args:
        project: Project record to update.

    Returns:
        None, to continue processing, zero is no error and stop processing,
        any other number is an error code.
    """
    return None

########################################


def configuration_settings(configuration):
    """
    Set up defines and libraries on a configuration basis.

    For each configation, set all configuration specific seting. Use
    configuration.name to determine which configuration is being processed.

    Args:
        configuration: Configuration class instance to update.

    Returns:
        None, to continue processing, zero is no error and stop processing,
        any other number is an error code.
    """
    return None


########################################

def library_settings(configuration):
    """
    Add settings when using this project at a library

    When configuration.add_library[] is set to a list of directories,
    if the directory has a build_rules.py file, it will run this
    function on every configuration to add the library this rules
    file describes.

    Args:
        configuration: Configuration class instance to update.

    Returns:
        None, to continue processing, zero is no error and stop processing,
        any other number is an error code.
    """
    return None


# If called as a command line, replace 0 with a call the function
# for the default action. Return a numeric error code, or zero.
if __name__ == "__main__":
    sys.exit(0)
