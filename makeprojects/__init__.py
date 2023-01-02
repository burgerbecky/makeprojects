#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Root namespace for the makeprojects tool

@package makeprojects

Makeprojects is a set of functions to generate project files
for the most popular IDEs and build systems. Included are
tools to automate building, cleaning and rebuilding projects.

@mainpage

@htmlinclude README.html

Chapter list
============

- @subpage md_buildme_man Instructions for buildme
- @subpage md_cleanme_man Instructions for cleanme
- @subpage md_rebuildme_man Instructions for rebuildme
- @subpage md_build_rules_man Layout of ``build_rules.py``

@par To use in your own script:

from makeprojects import *

solution = newsolution(name="myproject")
project = newproject(name="myproject")
solution.add_project(project=project)

project.addsourcefiles(os.path.join(os.getcwd(),"*.*"),recursive=True)
solution.save(solution.xcode3)

@var makeprojects.__numversion__
Current version of the library as a numeric tuple

@var makeprojects.__version__
Current version of the library

@var makeprojects.__author__
Author's name

@var makeprojects.__title__
Name of the module

@var makeprojects.__summary__
Summary of the module's use

@var makeprojects.__uri__
Home page

@var makeprojects.__email__
Email address for bug reports

@var makeprojects.__license__
Type of license used for distribution

@var makeprojects.__copyright__
Copyright owner

@var makeprojects._XCODEPROJ_MATCH
Match *.xcodeproj

@var makeprojects._HLSL_MATCH
Match *.hlsl

@var makeprojects._GLSL_MATCH
Match *.glsl

@var makeprojects._X360SL_MATCH
Match *.x360sl

@var makeprojects._VITACG_MATCH
Match *.vitacg

@var makeprojects.__all__
Items to import on "from makeprojects import *"
"""

# pylint: disable=import-outside-toplevel

from __future__ import absolute_import, print_function, unicode_literals

from re import compile as re_compile

from .core import SourceFile, Configuration, Project, Solution
from .enums import IDETypes, PlatformTypes, FileTypes, ProjectTypes, \
    add_burgerlib
from .defaults import get_configuration_settings

########################################

# Current version of the library as a numeric tuple
__numversion__ = (0, 13, 1)

# Current version of the library
__version__ = ".".join([str(num) for num in __numversion__])

# Author's name
__author__ = "Rebecca Ann Heineman <becky@burgerbecky.com>"

# Name of the module
__title__ = "makeprojects"

# Summary of the module's use
__summary__ = "IDE project generator for Visual Studio, XCode, etc..."

# Home page
__uri__ = "http://makeprojects.readthedocs.io"

# Email address for bug reports
__email__ = "becky@burgerbecky.com"

# Type of license used for distribution
__license__ = "MIT License"

# Copyright owner
__copyright__ = "Copyright 2013-2023 Rebecca Ann Heineman"

# Match *.xcodeproj
_XCODEPROJ_MATCH = re_compile("(?ms).*\\.xcodeproj\\Z")

# Match *.hlsl
_HLSL_MATCH = re_compile("(?ms).*\\.hlsl\\Z")

# Match *.glsl
_GLSL_MATCH = re_compile("(?ms).*\\.glsl\\Z")

# Match *.x360sl
_X360SL_MATCH = re_compile("(?ms).*\\.x360sl\\Z")

# Match *.vitacg
_VITACG_MATCH = re_compile("(?ms).*\\.vitacg\\Z")

# Items to import on "from makeprojects import *"
__all__ = [
    "build",
    "clean",
    "rebuild",
    "makeprojects",
    "new_solution",

    "FileTypes",
    "ProjectTypes",
    "IDETypes",
    "PlatformTypes",
    "add_burgerlib",

    "SourceFile",
    "Configuration",
    "Project",
    "Solution"
]

########################################


def build(working_directory=None, args=None):
    """
    Invoke the buildme command line from within Python

    Args:
        working_directory: ``None`` for current working directory.
        args: Argument list to pass to the command, None uses sys.argv.
    Returns:
        Zero on success, system error code on failure
    See Also:
        makeprojects.buildme
    """
    from .buildme import main
    if args is None:
        args = []
    return main(working_directory, args)

########################################


def clean(working_directory=None, args=None):
    """
    Invoke the cleanme command line from within Python

    Args:
        working_directory: ``None`` for current working directory.
        args: Argument list to pass to the command, None uses sys.argv
    Returns:
        Zero on success, system error code on failure
    See Also:
        makeprojects.cleanme
    """

    from .cleanme import main
    if args is None:
        args = []
    return main(working_directory, args)

########################################


def rebuild(working_directory=None, args=None):
    """
    Invoke the rebuildme command line from within Python

    Args:
        working_directory: Directory to rebuild
        args: Command line to use instead of sys.argv
    Returns:
        Zero on no error, non-zero on error
    See Also:
        makeprojects.rebuildme, makeprojects.rebuildme.main
    """

    from .rebuildme import main
    if args is None:
        args = []
    return main(working_directory, args)

########################################


def makeprojects(working_directory=None, args=None):
    """
    Invoke the makeprojects command line from within Python

    Args:
        working_directory: ``None`` for current working directory.
        args: Argument list to pass to the command, None uses sys.argv
    Returns:
        Zero on success, system error code on failure
    See Also:
        makeprojects.buildme
    """
    from .__main__ import main
    if args is None:
        args = []
    return main(working_directory, args)

########################################


def new_configuration(configuration_list):
    """
    Create a new instance of a core.Configuration

    Convenience routine to create a core.Configuration instance.

    Args:
        configuration_list: Array of dict() records to describe configurations

    Returns:
        None, a single Configuration or a list of valid Configuration records.
    See Also:
        core.Configuration
    """

    if isinstance(configuration_list, dict):
        configuration_list = [configuration_list]
    results = []
    for config_item in configuration_list:

        # Special case, if the platform is an expandable, convert to an array
        # of configurations that fit the bill.
        platform = config_item.get("platform")
        if platform is None:
            results.append(Configuration(**config_item))
        else:
            platform_type = PlatformTypes.lookup(platform)
            if platform_type is None:
                raise TypeError(
                    "parameter \"platform_type\" must be of type PlatformTypes")
            for item in platform_type.get_expanded():
                config_item["platform"] = item
                results.append(Configuration(**config_item))

    # If a single object, pass back as is.
    if len(results) == 1:
        return results[0]
    return results

########################################


def new_solution(name=None, platform=None, project_type=None):
    """
    Create a new instance of a full solution

    Convenience routine to create a Solution with a
    Project and three configurations "Debug", "Release", "Internal"

    Args:
        name: Name of the project
        platform: Platform for the project
        project_type: Type of project

    Returns:
        None, a fully stocked Solution
    See Also:
        core.Solution
    """

    solution = Solution(name=name)
    project = Project(name=name, platform=platform, project_type=project_type)
    solution.add_project(project)
    for item in ("Debug", "Internal", "Release"):
        settings = get_configuration_settings(item)
        settings["platform"] = platform
        project.add_configuration(new_configuration(settings))
    return solution
