#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains the code for the command line "makeprojects".

Scan the current directory and generate one or more project files
based on the source code found.

If build_rules.py is found, it will be scanned for information on how
to generate the IDE for different platforms and configurations if needed.

See Also:
    makeprojects.cleanme, makeprojects.buildme, makeprojects.rebuildme

@package makeprojects.__main__
"""

# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os
import argparse

from burger import convert_to_array

from .core import Solution, Project, Configuration
from .config import BUILD_RULES_PY
from .__init__ import __version__
from .defaults import get_project_name, get_platform, get_ide, \
    get_project_type, get_configuration_list
from .util import get_build_rules, load_build_rules, do_generate_build_rules

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
        prog="makeprojects", description=(
            "Make project files. Copyright by Rebecca Ann Heineman. "
            "Creates files for XCode, Visual Studio, "
            "CodeBlocks, Watcom, make, Codewarrior..."))

    parser.add_argument("--version", action="version",
                        version="%(prog)s " + __version__)
    parser.add_argument("-v", "-verbose", dest="verbose", action="store_true",
                        default=False, help="Verbose output.")
    parser.add_argument("--generate-rules", dest="generate_build_rules",
                        action="store_true", default=False,
                        help="Generate a sample configuration file and exit.")
    parser.add_argument(
        "--rules-file",
        dest="rules_file",
        metavar="<file>",
        default=BUILD_RULES_PY,
        help="Specify a configuration file.")
    parser.add_argument("-d", dest="directories", action="append",
                        metavar="<directory>",
                        help="Directorie(s) to create projects in.")
    parser.add_argument("-c", dest="configurations", action="append",
                        metavar="<configuration>",
                        help="Configuration(s) to create.")
    parser.add_argument("-g", dest="ide", action="store",
                        metavar="<IDE>", default=None,
                        help="IDE to generate for.")
    parser.add_argument("-p", dest="platform", action="store",
                        metavar="<platform>", default=None,
                        help="Platform to create.")
    parser.add_argument("-n", dest="name", action="store",
                        metavar="<name>", default=None,
                        help="Name of the project create.")
    parser.add_argument("-t", dest="project_type", action="store",
                        metavar="<project type>", default=None,
                        help="Type of project to create.")

    parser.add_argument("-xcode3", dest="xcode3", action="store_true",
                        default=False, help="Build for Xcode 3.")
    parser.add_argument("-xcode4", dest="xcode4", action="store_true",
                        default=False, help="Build for Xcode 4.")
    parser.add_argument("-xcode5", dest="xcode5", action="store_true",
                        default=False, help="Build for Xcode 5.")
    parser.add_argument("-xcode6", dest="xcode6", action="store_true",
                        default=False, help="Build for Xcode 6.")
    parser.add_argument("-xcode7", dest="xcode7", action="store_true",
                        default=False, help="Build for Xcode 7.")
    parser.add_argument("-xcode8", dest="xcode8", action="store_true",
                        default=False, help="Build for Xcode 8.")
    parser.add_argument("-xcode9", dest="xcode9", action="store_true",
                        default=False, help="Build for Xcode 9.")
    parser.add_argument("-xcode10", dest="xcode10", action="store_true",
                        default=False, help="Build for Xcode 10.")

    parser.add_argument("-vs2005", dest="vs2005", action="store_true",
                        default=False, help="Build for Visual Studio 2005.")
    parser.add_argument("-vs2008", dest="vs2008", action="store_true",
                        default=False, help="Build for Visual Studio 2008.")
    parser.add_argument("-vs2010", dest="vs2010", action="store_true",
                        default=False, help="Build for Visual Studio 2010.")
    parser.add_argument("-vs2012", dest="vs2012", action="store_true",
                        default=False, help="Build for Visual Studio 2012.")
    parser.add_argument("-vs2013", dest="vs2013", action="store_true",
                        default=False, help="Build for Visual Studio 2013.")
    parser.add_argument("-vs2015", dest="vs2015", action="store_true",
                        default=False, help="Build for Visual Studio 2015.")
    parser.add_argument("-vs2017", dest="vs2017", action="store_true",
                        default=False, help="Build for Visual Studio 2017.")
    parser.add_argument("-vs2019", dest="vs2019", action="store_true",
                        default=False, help="Build for Visual Studio 2019.")
    parser.add_argument("-vs2022", dest="vs2022", action="store_true",
                        default=False, help="Build for Visual Studio 2022.")

    parser.add_argument("-codeblocks", dest="codeblocks", action="store_true",
                        default=False, help="Build for CodeBlocks 16.01")
    parser.add_argument(
        "-codewarrior",
        dest="codewarrior",
        action="store_true",
        default=False,
        help="Build for Metrowerks / Freescale CodeWarrior")
    parser.add_argument("-watcom", dest="watcom", action="store_true",
                        default=False, help="Build for Watcom WMAKE")
    parser.add_argument("-linux", dest="linux", action="store_true",
                        default=False, help="Build for Linux make")
    parser.add_argument(
        "-ios",
        dest="ios",
        action="store_true",
        default=False,
        help="Build for iOS with XCode 5 or higher.")
    parser.add_argument(
        "-vita",
        dest="vita",
        action="store_true",
        default=False,
        help="Build for PS Vita with Visual Studio 2010.")
    parser.add_argument(
        "-360",
        dest="xbox360",
        action="store_true",
        default=False,
        help="Build for XBox 360 with Visual Studio 2010.")
    parser.add_argument(
        "-wiiu",
        dest="wiiu",
        action="store_true",
        default=False,
        help="Build for WiiU with Visual Studio 2013.")
    parser.add_argument(
        "-dsi",
        dest="dsi",
        action="store_true",
        default=False,
        help="Build for Nintendo DSI with Visual Studio 2015.")

    parser.add_argument(
        "-finalfolder",
        dest="deploy_folder",
        action="store_true",
        default=False,
        help="Add a script to copy a release build to a "
        "folder and check in with Perforce")
    parser.add_argument(
        "-app",
        dest="app",
        action="store_true",
        default=False,
        help="Build an application instead of a tool")
    parser.add_argument("-lib", dest="library", action="store_true",
                        default=False, help="Build a library instead of a tool")

    parser.add_argument("args", nargs=argparse.REMAINDER,
                        help="project filenames")

    return parser

########################################


def get_project_list(parsed, build_rules_list, working_directory):
    """
    From the command line or the build rules, determine the project target list.
    """

    # pylint: disable=too-many-locals

    # Start with determining the project name
    project_name = get_project_name(
        build_rules_list, working_directory, parsed.verbose, parsed.name)

    # Determine the project type
    project_type = get_project_type(
        build_rules_list, parsed.verbose, parsed.project_type)

    # Determine the list of platforms to generate projects for.
    platform = get_platform(
        build_rules_list, parsed.verbose, parsed.platform)

    # Determine the list of IDEs to generate projects for.
    ide = get_ide(build_rules_list, parsed.verbose, parsed.ide, platform)

    # Start with the solution
    solution = Solution(
        name=project_name,
        verbose=parsed.verbose,
        working_directory=working_directory,
        ide=ide)

    project = Project(
        name=project_name,
        project_type=project_type,
        working_directory=working_directory,
        platform=platform)

    solution.add_project(project)
    project.parse_attributes(build_rules_list)

    # Add all the configurations
    for platform_item in platform.get_expanded():
        # Create the configurations for this platform
        for config_item in get_configuration_list(
                build_rules_list, parsed.configurations,
                platform_item, ide):

            # Set the platform
            configuration = Configuration(
                name=config_item, platform=platform_item)
            project.add_configuration(configuration)
            configuration.parse_attributes(build_rules_list)

    # Add in any smart libraries
    for configuration in project.configuration_list:
        for library_rules in configuration.get_unique_chained_list(
                "library_rules_list"):

            # Is it a directory? Append build_rules.py
            if os.path.isdir(library_rules):
                library_rules = os.path.join(library_rules, BUILD_RULES_PY)

            build_rules = load_build_rules(library_rules)
            if not build_rules:
                print(
                    "Error: {} doesn't contain a build_rules file".format(
                        library_rules))
                continue

            # Rules found

            function_ref = getattr(build_rules, "library_settings", None)
            if not callable(function_ref):
                print(
                    "Error: Function library_settings() not found in {}".format(
                        library_rules))
                continue

            # Call the function
            error = function_ref(configuration)
            if error is not None:
                break

    # Perform the generation
    solution.generate(ide)
    return 0


########################################


def process(working_directory, parsed):
    """
    Process a solution.

    Args:
        working_directory: Directory to process.
        parsed: Args for determining verbosity for output
    Returns:
        Zero on no error, non zero integer on error
    """

    if parsed.verbose:
        print("Making \"{}\".".format(working_directory))

    # Are there build rules in this directory?
    build_rules_list = get_build_rules(
        working_directory, parsed.verbose, parsed.rules_file, "MAKEPROJECTS")

    if not build_rules_list:
        print("Fatal error, no " + BUILD_RULES_PY + " exist anywhere.")
        return 10

    return get_project_list(parsed, build_rules_list, working_directory)

########################################


def process_project_configurations(
        parsed, working_directory, entry, args):
    """
    Generate project file with configurations

    Given a dict with keys to generate a project, create all the
    project files for all requested IDEs

    Assume -n, -p, -t and -g are preset

    Args:
        parsed: An ArgumentParser object with attribute generate_build_rules
        working_directory: Directory to store the build_rules.py
        entry: Dictionary of keys to use to create the project files
        args: Arguments so far
    Returns:
        Integer error code
    """

    # Are there configurations?
    configurations = entry.get("configuration")
    new_args = []

    # Is verbose mode enabled?
    if parsed.verbose:
        new_args.append("-v")

    # Any configuration to add?
    if configurations:

        # Make sure it's an array
        configurations = convert_to_array(configurations)
        for configuration in configurations:
            new_args.append("-c")
            new_args.append(configuration)

    # Generate the project file
    return main(working_directory, args + new_args)

########################################


def process_project_types(
        parsed, working_directory, entry, args):
    """
    Process a dict entry with the -n, -p, -g parameters already set

    Given a dict with keys to generate a project, create all the
    project files for all requested IDEs

    Args:
        parsed: An ArgumentParser object with attribute generate_build_rules
        working_directory: Directory to store the build_rules.py
        entry: Dictionary of keys to use to create the project files
        args: Arguments so far
    Returns:
        Integer error code
    """

    # Is there an ide?
    types = entry.get("type")
    if not types:
        return process_project_configurations(
            parsed, working_directory, entry, args)

    # Make sure it's an array
    types = convert_to_array(types)
    error = 0
    for item in types:
        new_args = ["-t", item]
        error = process_project_configurations(
            parsed, working_directory, entry, args + new_args)
        if error:
            return error

    return error

########################################


def process_project_ides(
        parsed, working_directory, entry, args):
    """
    Process a dict entry with the -n and -p parameters already set

    Given a dict with keys to generate a project, create all the
    project files for all requested IDEs

    Args:
        parsed: An ArgumentParser object with attribute generate_build_rules
        working_directory: Directory to store the build_rules.py
        entry: Dictionary of keys to use to create the project files
        args: Arguments so far
    Returns:
        Integer error code
    """

    # Is there an ide?
    ide = entry.get("ide")
    if not ide:
        return process_project_types(parsed, working_directory, entry, args)

    # Make sure it's an array
    ide = convert_to_array(ide)
    error = 0
    for item in ide:
        new_args = ["-g", item]
        error = process_project_types(
            parsed, working_directory, entry, args + new_args)
        if error:
            return error

    return error

########################################


def process_project_platforms(
        parsed, working_directory, entry, args):
    """
    Process a dict entry with the -n parameter already set

    Given a dict with keys to generate a project, create all the
    project files for all requested IDEs

    Args:
        parsed: An ArgumentParser object with attribute generate_build_rules
        working_directory: Directory to store the build_rules.py
        entry: Dictionary of keys to use to create the project files
        args: Arguments so far
    Returns:
        Integer error code
    """

    # Is there a platform?
    platform = entry.get("platform")
    if not platform:
        return process_project_ides(parsed, working_directory, entry, args)

    # Make sure it's an array
    platform = convert_to_array(platform)
    error = 0
    for item in platform:
        new_args = ["-p", item]
        error = process_project_ides(
            parsed, working_directory, entry, args + new_args)
        if error:
            return error

    return error

########################################


def process_proj_names(parsed, working_directory, entry):
    """
    Process a dict entry to generate project files

    Given a dict with keys to generate a project, create all the
    project files for all requested IDEs

    Args:
        parsed: An ArgumentParser object with attribute generate_build_rules
        working_directory: Directory to store the build_rules.py
        entry: Dictionary of keys to use to create the project files
    Returns:
        Integer error code
    """

    # Is there a name?
    name = entry.get("name")
    if not name:
        return process_project_platforms(parsed, working_directory, entry, [])

    # Make sure it's an array
    name = convert_to_array(name)
    error = 0
    for item in name:
        args = ["-n", item]
        error = process_project_platforms(
            parsed, working_directory, entry, args)
        if error:
            return error

    return error

########################################


def process_makeprojects(parsed, working_directory):
    """
    Process using default behavior from MAKEPROJECTS

    Check if there is a build_rules.py in the current directory
    and if so, if there's a MAKEPROJECTS value, use it to process
    all the project files. If not, traverse the directory until the
    first file with MAKEPROJECTS and GENERIC = True, and then process.

    Args:
        parsed: An ArgumentParser object with attribute generate_build_rules
        working_directory: Directory to store the build_rules.py
    Returns:
        None or an integer error code
    """

    # Load the configuration file at the current directory
    temp_dir = os.path.abspath(working_directory)

    # Is this the first pass?
    is_root = True

    # pylint: disable=too-many-nested-blocks
    while True:

        # Get the path to the requested rules
        library_rules = os.path.join(temp_dir, BUILD_RULES_PY)

        # Load in build_rules.py
        build_rules = load_build_rules(library_rules)

        # Found? Try this one
        if build_rules:

            # Root entry, or a GENERIC entry?
            if is_root or getattr(build_rules, "GENERIC", False):

                # Does the file have the attribute?
                make_proj = getattr(build_rules, "MAKEPROJECTS", False)
                if make_proj:

                    # No error at all
                    error = 0

                    # Iterate over every MAKEPROJECTS entry
                    for entry in make_proj:
                        error = process_proj_names(
                            parsed, working_directory, entry)
                        if error:
                            return error
                    return error

                # Test if this is considered the last one in the chain.
                if not getattr(build_rules, "CONTINUE", False):
                    break

        # Directory traversal is active, require GENERIC
        is_root = False

        # Pop a folder to check for higher level build_rules.py
        temp_dir2 = os.path.dirname(temp_dir)

        # Already at the top of the directory?
        if temp_dir2 is None or temp_dir2 == temp_dir:
            break
        # Use the new folder
        temp_dir = temp_dir2

    # Never found anything
    return None

########################################


def main(working_directory=None, args=None):
    """
    Main entry point when invoked as a tool.

    When makeprojects is invoked as a tool, this main() function
    is called with the current working directory. Arguments will
    be obtained using the argparse class.

    Args:
        working_directory: Directory to operate on or None.
        args: Command line to use instead of ``sys.argv``.
    Returns:
        Zero if no error, non-zero on error

    """

    # pylint: disable=too-many-statements

    # Make sure working_directory is properly set
    if working_directory is None:
        working_directory = os.getcwd()

    # Create the parser
    parser = create_parser()

    # Parse everything
    parsed = parser.parse_args(args=args)

    # If --generate-rules was created, output the file, and exit
    error = do_generate_build_rules(parsed, working_directory)
    if error is not None:
        return error

    # If invoked without any parameters, try if build_rules.py
    # has a list of projects to build
    if args is None and len(sys.argv) < 2:
        error = process_makeprojects(parsed, working_directory)
        if error is not None:
            return error

    # Make a list of directories to process
    if not parsed.directories:
        parsed.directories = (working_directory,)

    # Process the directories
    for item in parsed.directories:
        error = process(os.path.abspath(item), parsed)
        if error:
            break
    else:
        if parsed.verbose:
            print("Makeprojects successful!")
        error = 0

    return error


# If called as a function and not a class, call my main
if __name__ == "__main__":
    sys.exit(main())
