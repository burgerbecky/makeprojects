#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Root namespace for the makeprojects tool

"""

#
## \package makeprojects
#
# Makeprojects is a set of functions to generate project files
# for the most popular IDEs and build systems. Included are
# tools to automate building, cleaning and rebuilding projects.
#

#
## \mainpage
#
# \htmlinclude README.html
#
# \par To use in your own script:
#
# \code
# from makeprojects import *
#
# solution = newsolution(name='myproject')
# project = newproject(name='myproject')
# solution.add_project(project=project)
#
# project.addsourcefiles(os.path.join(os.getcwd(),'*.*'),recursive=True)
# solution.save(solution.xcode3)
#
# \endcode
#

from __future__ import absolute_import, print_function, unicode_literals

from re import compile as re_compile

from .core import SourceFile, Configuration, Project, Solution
from .enums import IDETypes, PlatformTypes, FileTypes, ProjectTypes, \
    add_burgerlib
from .__pkginfo__ import NUMVERSION, VERSION, AUTHOR, TITLE, SUMMARY, \
    URI, EMAIL, LICENSE, COPYRIGHT
from .defaults import _CONFIGURATION_DEFAULTS

########################################

## Current version of the library as a numeric tuple
__numversion__ = NUMVERSION

## Current version of the library
__version__ = VERSION

## Author's name
__author__ = AUTHOR

## Name of the module
__title__ = TITLE

## Summary of the module's use
__summary__ = SUMMARY

## Home page
__uri__ = URI

## Email address for bug reports
__email__ = EMAIL

## Type of license used for distribution
__license__ = LICENSE

## Copyright owner
__copyright__ = COPYRIGHT

## Match *.xcodeproj
_XCODEPROJ_MATCH = re_compile('(?ms).*\\.xcodeproj\\Z')

## Match *.hlsl
_HLSL_MATCH = re_compile('(?ms).*\\.hlsl\\Z')

## Match *.glsl
_GLSL_MATCH = re_compile('(?ms).*\\.glsl\\Z')

## Match *.x360sl
_X360SL_MATCH = re_compile('(?ms).*\\.x360sl\\Z')

## Match *.vitacg
_VITACG_MATCH = re_compile('(?ms).*\\.vitacg\\Z')

## Items to import on "from makeprojects import *"

__all__ = [
    'build',
    'clean',
    'rebuild',
    'makeprojects',
    'new_solution',
    'new_project',
    'new_configuration',

    'FileTypes',
    'ProjectTypes',
    'IDETypes',
    'PlatformTypes',
    'add_burgerlib',

    'SourceFile',
    'Configuration',
    'Project',
    'Solution'
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
    return main(working_directory, args)


########################################


def new_solution(**kargs):
    """
    Create a new instance of a core.Solution

    Convenience routine to create a core.Solution instance.

    Args:
        kargs: dict of arguments.
    See Also:
        core.Solution
    """

    return Solution(**kargs)

########################################


def new_project(**kargs):
    """
    Create a new instance of a core.Project

    Convenience routine to create a core.Project instance.

    Args:
        kargs: dict of arguments.

    Returns:
        Project class instance.
    See Also:
        core.Project
    """

    return Project(**kargs)

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
        platform = config_item.get('platform')
        if platform is None:
            results.append(Configuration(**config_item))
        else:
            platform_type = PlatformTypes.lookup(platform)
            if platform_type is None:
                raise TypeError(
                    "parameter 'platform_type' must be of type PlatformTypes")
            for item in platform_type.get_expanded():
                config_item['platform'] = item
                results.append(Configuration(**config_item))

    # If a single object, pass back as is.
    if len(results) == 1:
        return results[0]
    return results

########################################

def new(name=None, platform=None, project_type=None):
    """
    Create a new instance of a full solution

    Convenience routine to create a Solution with a
    Project and three configurations 'Debug', 'Release', 'Internal'

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
    configurations = new_configuration(_CONFIGURATION_DEFAULTS[:3])
    solution.add_project(project)
    project.add_configuration(configurations)
    return solution
