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

from copy import deepcopy
from burger import convert_to_array
from .__pkginfo__ import NUMVERSION, VERSION, AUTHOR, TITLE, SUMMARY, URI, EMAIL, LICENSE, COPYRIGHT
from .enums import IDETypes, PlatformTypes, FileTypes, ProjectTypes
from .core import SourceFile, Configuration, Project, Solution

########################################

# pylint: disable=W0105

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

## Items to import on "from makeprojects import *"

__all__ = [
    'build',
    'clean',
    'rebuild',
    'new_solution',
    'new_project',
    'new_configuration',

    'FileTypes',
    'ProjectTypes',
    'IDETypes',
    'PlatformTypes',

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
        working_directory: Directory to process, ``None`` for current working directory
        args: Argument list to pass to the command, None uses sys.argv
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
        working_directory: Directory to process, ``None`` for current working directory
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


def new_solution(name=None, working_directory=None, verbose=False, ide=None, perforce=True):
    """
    Create a new instance of a core.Solution

    Convenience routine to create a core.Solution instance.

    Args:
        name: Name of the project
        working_directory: Directory to store the solution.
        verbose: If True, verbose output.
        ide: IDE to build for.
        perforce: True if perforce is present.
    See Also:
        core.Solution
    """

    return Solution(name=name, working_directory=working_directory,
                    verbose=verbose, ide=ide, perforce=perforce)

########################################


def new_project(name=None, working_directory=None, project_type=None, platform=None):
    """
    Create a new instance of a core.Project

    Convenience routine to create a core.Project instance.

    Args:
        name: Name of the project.
        working_directory: Directory of the root of this project.
        project_type: ProjectTypes to use if Configuration doesn't specify one.
        platform: PlatformTypes to use if Configuration doesn't specific one.

    Returns:
        Project class instance.
    See Also:
        core.Project
    """

    return Project(name=name, working_directory=working_directory,
                   project_type=project_type, platform=platform)

########################################


def new_configuration(name, platform=None, project_type=None):
    """
    Create a new instance of a core.Configuration

    Convenience routine to create a core.Configuration instance.

    Args:
        name: String of the name of the configuration
        platform: PlatformTypes for this configuration
        project_type: ProjectTypes for this configuration.

    Returns:
        None, a single Configuration or a list of valid Configuration records.
    See Also:
        core.Configuration
    """

    results = []
    name_array = convert_to_array(name)
    for name_item in name_array:

        # Special case, if the platform is an expandable, convert to an array
        # of configurations that fit the bill.
        if platform:
            platform_type = PlatformTypes.lookup(platform)
            if platform_type is None:
                raise TypeError("parameter 'platform_type' must be of type PlatformTypes")
            for item in platform_type.get_expanded():
                results.append(Configuration(name_item, item, project_type))
        else:
            results.append(Configuration(name_item, platform, project_type))

    # If a single object, pass back as is.
    if len(results) == 1:
        return results[0]
    return results
