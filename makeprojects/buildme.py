#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains the code for the command line ``buildme``.

Scan the current directory and all project files will be built.

If BUILD_RULES_PY is found, it will be checked for function entry points
``prebuild``, ``build`` and ``postbuild`` will be called in that order.

If ``prebuild.py``, ``postbuild.py``, or ``custom_build.py`` files are found
then function ``main`` is called.

Build commands are performed from lowest priority value to highest value.

Full documentation is here, @subpage md_buildme_man

See Also:
    main, makeprojects.cleanme, makeprojects.rebuildme

@package makeprojects.buildme

@var makeprojects.buildme.BUILD_LIST
Default build_rules.py command list, priority / entrypoint

@var makeprojects.buildme.CODEWARRIOR_ERRORS
Error code messages from Codewarrior

@var makeprojects.buildme._CW_SUPPORTED_LINKERS
List of supported Codewarrior Linkers

@var makeprojects.buildme._VS_VERSION_YEARS
Lookup for Visual Studio year in SLN file.

@var makeprojects.buildme._VS_OLD_VERSION_YEARS
Lookup for Visual Studio year in SLN file pre-2012.

@var makeprojects.buildme._VS_SDK_ENV_VARIABLE
Lookup for Visual Studio SDK detector.

@var makeprojects.buildme._XCODE_SUFFIXES
XCode version for file suffix

"""

# pylint: disable=useless-object-inheritance
# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import argparse
from struct import unpack as struct_unpack
from operator import attrgetter
import xml.etree.ElementTree as ET
from burger import where_is_doxygen, create_folder_if_needed, \
    get_windows_host_type, get_mac_host_type, delete_file, save_text_file, \
    load_text_file, run_command, read_zero_terminated_string, \
    where_is_watcom, host_machine, import_py_script, where_is_visual_studio, \
    is_codewarrior_mac_allowed, where_is_codeblocks, run_py_script, \
    where_is_xcode, convert_to_array
from .config import BUILD_RULES_PY
from .__init__ import _XCODEPROJ_MATCH, __version__, _XCODEPROJECT_FILE
from .util import remove_ending_os_sep, was_processed
from .core import BuildError, BuildObject

BUILD_LIST = (
    (1, 'prebuild'),
    (40, 'build'),
    (99, 'postbuild')
)

CODEWARRIOR_ERRORS = (
    None,
    'error opening file',
    'project not open',
    'IDE is already building',
    'invalid target name (for /t flag)',
    'error changing current target',
    'error removing objects',
    'build was cancelled',
    'build failed',
    'process aborted',
    'error importing project',
    'error executing debug script',
    'attempted use of /d together with /b and/or /r'
)

_CW_SUPPORTED_LINKERS = (
    'MW ARM Linker Panel',      # ARM for Nintendo DSI
    'x86 Linker',               # Windows
    'PPC Linker',               # macOS PowerPC
    '68K Linker',               # macOS 68k
    'PPC EABI Linker'           # PowerPC for Nintendo Wii
)

_VS_VERSION_YEARS = {
    '2012': 2012,
    '2013': 2013,
    '14': 2015,
    '15': 2017,
    '16': 2019,
    '17': 2022
}

_VS_OLD_VERSION_YEARS = {
    '8.00': 2003,
    '9.00': 2005,
    '10.00': 2008,
    '11.00': 2010,
    '12.00': 2012
}

_VS_SDK_ENV_VARIABLE = {
    'PSP': 'SCE_ROOT_DIR',          # PSP
    'PS3': 'SCE_PS3_ROOT',          # PS3
    'ORBIS': 'SCE_ORBIS_SDK_DIR',   # PS4
    'PSVita': 'SCE_PSP2_SDK_DIR',   # PS Vita
    'Xbox': 'XDK',                  # Xbox classic
    'Xbox 360': 'XEDK',             # Xbox 360
    'Xbox ONE': 'DurangoXDK',       # Xbox ONE
    'Wii': 'REVOLUTION_SDK_ROOT',   # Nintendo Wii
    'NX32': 'NINTENDO_SDK_ROOT',    # Nintendo Switch
    'NX64': 'NINTENDO_SDK_ROOT',    # Nintendo Switch
    'Android': 'ANDROID_NDK_ROOT',  # Generic Android tools
    'ARM-Android-NVIDIA': 'NVPACK_ROOT',        # nVidia android tools
    'AArch64-Android-NVIDIA': 'NVPACK_ROOT',    # nVidia android tools
    'x86-Android-NVIDIA': 'NVPACK_ROOT',        # nVidia android tools
    'x64-Android-NVIDIA': 'NVPACK_ROOT',        # nVidia android tools
    'Tegra-Android': 'NVPACK_ROOT'              # nVidia android tools
}

_XCODE_SUFFIXES = (
    ('xc3', 3),
    ('xc4', 4),
    ('xc5', 5),
    ('xc6', 6),
    ('xc7', 7),
    ('xc8', 8),
    ('xc9', 9),
    ('x10', 10),
    ('x11', 11),
    ('x12', 12),
    ('x13', 13)
)

########################################


def create_parser():
    """
    Create the parser to process the command line for buildme

    The returned object has these member variables

    - version boolean if version is requested
    - recursive boolean for directory recursion
    - verbose boolean for verbose output
    - preview boolean for previewing the build process
    - generate_build_rules boolean create build rules and exit
    - rules_file string override build_rules.py
    - directories string array of directories to process
    - files string array of project files to process
    - configurations string array of configurations to process
    - documentation boolean if Doxygen is be executed
    - fatal boolean abort if error occurs in processing
    - args string array of unknown parameters

    Returns:
        argparse.ArgumentParser() object
    """

    # Create the initial parser
    parser = argparse.ArgumentParser(
        description='Build project files. Copyright by Rebecca Ann Heineman. '
        'Builds *.sln, *.mcp, *.cbp, *.wmk, *.rezscript, *.slicerscript, '
        'doxyfile, makefile and *.xcodeproj files')

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)

    parser.add_argument('-r', '-all', dest='recursive', action='store_true',
                        default=False, help='Perform a recursive build')

    parser.add_argument('-v', '-verbose', dest='verbose', action='store_true',
                        default=False, help='Verbose output.')

    parser.add_argument('-n', '-preview', dest='preview', action='store_true',
                        default=False, help='Preview build commands.')

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
                        metavar='<directory>',
                        help='Directory to process.')

    parser.add_argument('-c', dest='configurations', action='append',
                        metavar='<configuration>',
                        help='Configuration to process.')

    parser.add_argument('-docs', dest='documentation', action='store_true',
                        default=False, help='Compile Doxyfile files.')

    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='project filenames')

    return parser

########################################


def fixup_args(args):
    """
    Check unused args if they are directories, files or configurations

    Args:
        args: args class from argparser
    """

    # Remove trailing os seperator
    args.args = remove_ending_os_sep(args.args)
    args.directories = remove_ending_os_sep(args.directories)

    if not args.configurations:
        args.configurations = []

    if not args.files:
        args.files = []

    # Process the orphaned arguments and determine if they
    # are configurations, files or directories
    if args.args:
        for item in args.args:
            filename = os.path.abspath(item)
            if os.path.isfile(filename):
                args.files.append(filename)
            elif os.path.isdir(filename):
                args.directories.append(filename)
            else:
                args.configurations.append(item)
        args.args = None

    args.directories = [os.path.abspath(item) for item in args.directories]
    args.files = [os.path.abspath(item) for item in args.files]

    # Hack to convert XCode directories into files
    temp_list = []
    for item in args.directories:
        if item.endswith(".xcodeproj"):
            filename = os.path.join(item, _XCODEPROJECT_FILE)
            if os.path.isfile(filename):
                args.files.append(filename)
                continue
        temp_list.append(item)
    args.directories = temp_list

########################################


def parse_sln_file(full_pathname):
    """
    Find build targets in .sln file.

    Given a .sln file for Visual Studio 2003, 2005, 2008, 2010,
    2012, 2013, 2015, 2017 or 2019, locate and extract all of the build
    targets available and return the list.

    It will also determine which version of Visual
    Studio this solution file requires.

    Args:
        full_pathname: Pathname to the .sln file
    Returns:
        tuple(list of configuration strings, integer Visual Studio version year)
    See Also:
        build_visual_studio
    """

    # Load in the .sln file, it's a text file
    file_lines = load_text_file(full_pathname)

    # Version not known yet
    vs_version = 0

    # Start with an empty list
    target_list = []

    if file_lines:
        # Not looking for 'Visual Studio'
        looking_for_visual_studio = False

        # Not looking for EndGlobalSection
        looking_for_end_global_section = False

        # Parse
        for line in file_lines:

            # Scanning for 'EndGlobalSection'?

            if looking_for_end_global_section:

                # Once the end of the section is reached, end
                if 'EndGlobalSection' in line:
                    looking_for_end_global_section = False
                else:

                    # The line contains 'Debug|Win32 = Debug|Win32'
                    # Split it in half at the equals sign and then
                    # remove the whitespace and add to the list
                    target = line.split('=')[-1].strip()
                    if target not in target_list:
                        target_list.append(target)
                continue

            # Scanning for the secondary version number in Visual Studio 2012 or
            # higher

            if looking_for_visual_studio and '# Visual Studio' in line:
                # The line contains '# Visual Studio 15' or '# Visual Studio
                # Version 16'

                # Use the version number to determine which visual studio to
                # launch
                vs_version = _VS_VERSION_YEARS.get(line.rsplit()[-1], 0)
                looking_for_visual_studio = False
                continue

            # Get the version number
            if 'Microsoft Visual Studio Solution File' in line:
                # The line contains
                # 'Microsoft Visual Studio Solution File, Format Version 12.00'
                # The number is in the last part of the line
                # Use the version string to determine which visual studio to
                # launch
                vs_version = _VS_OLD_VERSION_YEARS.get(line.split()[-1], 0)
                if vs_version == 2012:
                    # 2012 or higher requires a second check
                    looking_for_visual_studio = True
                continue

            # Look for this section, it contains the configurations
            if '(SolutionConfigurationPlatforms)' in line or \
                    '(ProjectConfiguration)' in line:
                looking_for_end_global_section = True

    # Exit with the results
    if not vs_version:
        print(
            ('The visual studio solution file {} '
             'is corrupt or an unknown version!').format(full_pathname),
            file=sys.stderr)
    return (target_list, vs_version)

########################################


def parse_mcp_file(full_pathname):
    """
    Extract configurations from a Metrowerks CodeWarrior project file.

    Given an .mcp file for Metrowerks Codewarrior, determine
    which version of Codewarrrior was used to build it.

    It will parse Freescale Codewarrior for Nintendo (59), Metrowerks
    Codewarrior 9.0 for Windows (50) and Metrowerks Codewarrior 10.0
    for macOS (58)

    Args:
        full_pathname: Pathname to the .mcp file
    Returns:
        tuple(list of configuration strings, integer CodeWarrior Version)
    See Also:
        build_codewarrior
    """

    # Handle ../../
    full_pathname = os.path.abspath(full_pathname)

    try:
        # Load in the .mcp file, it's a binary file
        with open(full_pathname, 'rb') as filep:

            # Get the signature and the endian
            cool = filep.read(4)
            if cool == b'cool':
                # Big endian
                endian = '>'
            elif cool == b'looc':
                # Little endian
                endian = '<'
            else:
                print(
                    'Codewarrior "cool" signature not found!',
                    file=sys.stderr)
                return None, None, None

            # Get the offset to the strings
            filep.seek(16)
            index_offset = struct_unpack(endian + 'I', filep.read(4))[0]
            filep.seek(index_offset)
            string_offset = struct_unpack(endian + 'I', filep.read(4))[0]

            # Read in the version
            filep.seek(28)
            cw_version = bytearray(filep.read(4))

            # Load the string 'CodeWarrior Project'
            filep.seek(40)
            if filep.read(19) != b'CodeWarrior Project':
                print(
                    '"Codewarrior Project" signature not found!',
                    file=sys.stderr)
                return None, None, None

            # Read in the strings for the targets
            filep.seek(string_offset)
            targets = []
            linkers = []
            # Scan for known linkers
            while True:
                item = read_zero_terminated_string(filep)
                if not item:
                    break

                # Only strings with a colon are parsed
                parts = item.split(':')
                if len(parts) == 2:
                    # Target:panel
                    target = parts[0]
                    panel = parts[1]

                    # Add the target
                    if target not in targets:
                        targets.append(target)

                    # Add the linker if supported
                    if panel in _CW_SUPPORTED_LINKERS:
                        if panel not in linkers:
                            linkers.append(panel)

            return targets, linkers, cw_version

    except IOError as error:
        print(str(error), file=sys.stderr)

    return None, None, None

########################################


def parse_xcodeproj_file(full_pathname):
    """
    Extract configurations from an XCode project file.

    Given a .xcodeproj directory for XCode for macOS
    locate and extract all of the build targets
    available and return the list.

    Args:
        full_pathname: Pathname to the .xcodeproj folder
    Returns:
        list of configuration strings
    See Also:
        build_xcode
    """

    # Start with an empty list

    targetlist = []
    try:
        with open(full_pathname, 'r') as filep:
            projectfile = filep.read().splitlines()

    except IOError as error:
        print(str(error), file=sys.stderr)
        return targetlist

    configurationfound = False
    for line in projectfile:
        # Look for this section. Immediately after it
        # has the targets
        if configurationfound is False:
            if 'buildConfigurations' in line:
                configurationfound = True
        else:
            # Once the end of the section is reached, end
            if ');' in line:
                break
            # Format 1DEB923608733DC60010E9CD /* Debug */,
            # The third entry is the data needed
            targetlist.append(line.rsplit()[2])

    # Exit with the results
    return targetlist

########################################


def parse_codeblocks_file(full_pathname):
    """
    Extract configurations from a Codeblocks project file.

    Given a .cbp file for Codeblocks
    locate and extract all of the build targets
    available and return the list.

    Args:
        full_pathname: Pathname to the .cdp file
    Returns:
        list of configuration strings
    See Also:
        build_codeblocks
    """

    # Too many nested blocks
    # pylint: disable=R0101

    # Start with an empty list
    targetlist = []

    # Parse the XML file
    try:
        tree = ET.parse(full_pathname)
    except IOError as error:
        print(str(error), file=sys.stderr)
        return targetlist

    # Traverse the tree and extract the targets
    root = tree.getroot()
    for child in root:
        if child.tag == 'Project':
            for item in child:
                if item.tag == 'Build':
                    for item2 in item:
                        if item2.tag == 'Target':
                            target = item2.attrib.get('title')
                            if target:
                                targetlist.append(target)
                elif item.tag == 'VirtualTargets':
                    for item2 in item:
                        if item2.tag == 'Add':
                            target = item2.attrib.get('alias')
                            if target:
                                targetlist.append(target)

    # Exit with the results
    return targetlist

#######################################


class BuildRezFile(BuildObject):
    """
    Class to build rez files

    Attributes:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority, verbose=False):
        """
        Class to handle .rezfile.

        Args:
            file_name: Pathname to the *.rezscript to build
            priority: Priority to build this object
            verbose: True if verbose output
        """

        super().__init__(file_name, priority)
        self.verbose = verbose

    def build(self):
        """
        Build a rezfile using ``makerez``.

        Execute the program ``makerez`` to build the script.

        Returns:
            BuildError object
        """

        # Create the build command
        cmd = ['makerez', self.file_name]
        if self.verbose:
            # Have makerez be verbose
            cmd.insert(1, '-v')
            print(' '.join(cmd))

        # Issue it
        return self.run_command(cmd, self.verbose)

#######################################


class BuildSlicerFile(BuildObject):
    """
    Class to build slicer files

    Attributes:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority, verbose=False):
        """
        Class to handle .slicerscript files

        Args:
            file_name: Pathname to the *.slicerscript to build
            priority: Priority to build this object
            verbose: True if verbose output
        """

        super().__init__(file_name, priority)
        self.verbose = verbose

    def build(self):
        """
        Build an art slice using ``slicer``.

        Execute the program ``slicer`` to build the script.

        Returns:
            BuildError object
        """

        # Create the build command
        cmd = ['slicer', self.file_name]
        if self.verbose:
            print(' '.join(cmd))

        # Issue it
        return self.run_command(cmd, self.verbose)

########################################


class BuildDoxygenFile(BuildObject):
    """
    Class to build doxygen files

    Attributes:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority, verbose=False):
        """
        Class to handle Doxyfile files

        Args:
            file_name: Pathname to the Doxyfile to build
            priority: Priority to build this object
            verbose: True if verbose output
        """

        super().__init__(file_name, priority)
        self.verbose = verbose

    def build(self):
        """
        Build documentation using Doxygen.

        Execute the program ``doxygen`` to create documentation for the
        project building built.

        If the input file is found to have CR/LF line endings on a macOS
        or Linux platform, the file will have the CRs stripped before
        being passed to Doxygen to get around a bug in Doxygen where
        the macOS/Linux versions require LF only line endings.

        All Doxygen errors will be captured and stored in a file called
        temp/doxygenerrors.txt. If there were no errors, this file
        will be deleted if it exists.

        Returns:
            BuildError object
        """

        # Is Doxygen installed?
        doxygenpath = where_is_doxygen(verbose=self.verbose)
        if doxygenpath is None:
            msg = '{} requires Doxygen to be installed to build!'.format(
                self.file_name)
            return BuildError(10, self.file_name, msg=msg)

        # Determine the working directory
        doxyfile_dir = os.path.dirname(self.file_name)

        # Make the output folder for errors (If needed)
        temp_dir = os.path.join(doxyfile_dir, 'temp')
        create_folder_if_needed(temp_dir)

        # The macOS/Linux version will die if the text file isn't Linux
        # format, copy the config file with the proper line feeds
        if get_windows_host_type() is False:
            doxyfile_data = load_text_file(self.file_name)
            temp_doxyfile = self.file_name + '.tmp'
            save_text_file(temp_doxyfile, doxyfile_data, line_feed='\n')
        else:
            temp_doxyfile = self.file_name

        # Create the build command
        cmd = [doxygenpath, temp_doxyfile]
        if self.verbose:
            print(' '.join(cmd))

        # Capture the error output
        stderr = run_command(cmd, working_dir=doxyfile_dir,
                             quiet=not self.verbose, capture_stderr=True)[2]

        # If there was a temp doxyfile, get rid of it.
        if temp_doxyfile != self.file_name:
            delete_file(temp_doxyfile)

        # Location of the log file
        log_filename = os.path.join(temp_dir, 'doxygenerrors.txt')

        # If the error log has something, save it.
        if stderr:
            save_text_file(log_filename, stderr.splitlines())
            msg = 'Errors stored in {}'.format(log_filename)
            return BuildError(10, self.file_name, msg=msg)

        # Make sure it's gone since there's no errors
        delete_file(log_filename)
        return BuildError(0, self.file_name)

########################################


class BuildWatcomFile(BuildObject):
    """
    Class to build watcom make files

    Attribute:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority, configuration, verbose=False):
        """
        Class to handle watcom make files

        Args:
            file_name: Pathname to the *.wmk to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
        """

        super().__init__(file_name, priority, configuration=configuration)
        self.verbose = verbose

    def build(self):
        """
        Build Watcom MakeFile.
        @details
        On Linux and Windows hosts, this function will invoke the ``wmake``
        tool to build the watcom make file.

        The PATH will be temporarily adjusted to include the watcom tools so
        wmake can find its shared libraries.

        The default target built is ``all``.

        Returns:
            List of BuildError objects
        """

        # Is Watcom installed?
        watcom_path = where_is_watcom(verbose=self.verbose)
        if watcom_path is None:
            return BuildError(
                0, self.file_name,
                msg='{} requires Watcom to be installed to build!'.format(
                    self.file_name))

        # Watcom requires the path set up so it can access link files
        saved_path = os.environ['PATH']
        if get_windows_host_type():
            new_path = os.pathsep.join(
                (os.path.join(
                    watcom_path, 'binnt'), os.path.join(
                        watcom_path, 'binw')))
        else:
            new_path = os.path.join(watcom_path, 'binl')

        exe_name = where_is_watcom('wmake', verbose=self.verbose)
        os.environ['PATH'] = new_path + os.pathsep + saved_path

        # Set the configuration target
        cmd = [exe_name, '-e', '-h', '-f', self.file_name, self.configuration]

        # Iterate over the commands
        if self.verbose:
            print(' '.join(cmd))

        result = self.run_command(cmd, self.verbose)

        # Restore the path variable
        os.environ['PATH'] = saved_path

        # Return the error code
        return result

########################################


def add_watcom_configurations(file_name, args):
    """
    Create BuildWatcomFile build records for every desired configuration

    Args:
        file_name: Full pathname to the make file
        args: parser argument list
    Returns:
        list of BuildWatcomFile classes
    """

    if not args.configurations:
        return [BuildWatcomFile(file_name, 50, 'all', args.verbose)]

    results = []
    for configuration in args.configurations:
        results.append(
            BuildWatcomFile(
                file_name,
                50,
                configuration,
                args.verbose))
    return results

########################################


class BuildMakeFile(BuildObject):
    """
    Class to build Linux make files

    Attributes:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority, configuration, verbose=False):
        """
        Class to handle Linux make files

        Args:
            file_name: Pathname to the makefile to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
        """

        super().__init__(file_name, priority, configuration=configuration)
        self.verbose = verbose

    def build(self):
        """
        Build MakeFile using ``make``.

        For Linux hosts, invoke ``make`` for building a makefile.

        The default target built is ``all``.

        Returns:
            List of BuildError objects
        """

        # Running under Linux?
        if host_machine() != 'linux':
            return BuildError(
                0, self.file_name, msg='{} can only build on Linux!'.format(
                    self.file_name))

        # Build the requested target configuration
        cmd = ['make', '-s', '-f', self.file_name, self.configuration]

        if self.verbose:
            print(' '.join(cmd))

        return self.run_command(cmd, self.verbose)

########################################


def add_make_configurations(file_name, args):
    """
    Create BuildMakeFile build records for every desired configuration

    Args:
        file_name: Full pathname to the make file
        args: parser argument list
    Returns:
        list of BuildMakeFile classes
    """

    if not args.configurations:
        return [BuildMakeFile(file_name, 50, 'all', args.verbose)]

    results = []
    for configuration in args.configurations:
        results.append(
            BuildMakeFile(
                file_name,
                50,
                configuration,
                args.verbose))
    return results

########################################


class BuildNinjaFile(BuildObject):
    """
    Class to build Ninja make files

    Attributes:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority, configuration, verbose=False):
        """
        Class to handle Ninja make files

        Args:
            file_name: Pathname to the makefile to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
        """

        super().__init__(file_name, priority, configuration=configuration)
        self.verbose = verbose

    def build(self):
        """
        Build build.ninja using ``ninja``.

        The default target built is ``all``.

        Returns:
            List of BuildError objects
        """

        # Build the requested target configuration
        cmd = ['ninja', '-f', self.file_name, self.configuration]

        if self.verbose:
            print(' '.join(cmd))

        return self.run_command(cmd, self.verbose)

########################################


def add_ninja_configurations(file_name, args):
    """
    Create BuildNinjaFile build records for every desired configuration

    Args:
        file_name: Full pathname to the make file
        args: parser argument list
    Returns:
        list of BuildNinjaFile classes
    """

    if not args.configurations:
        return [BuildNinjaFile(file_name, 50, 'all', args.verbose)]

    results = []
    for configuration in args.configurations:
        results.append(
            BuildNinjaFile(
                file_name,
                50,
                configuration,
                args.verbose))
    return results

########################################


class BuildVisualStudioFile(BuildObject):
    """
    Class to build Visual Studio files

    Attributes:
        verbose: The verbose flag
        vs_version: The required version of Visual Studio
    """

    # pylint: disable=too-many-arguments
    def __init__(self, file_name, priority, configuration,
                 verbose=False, vs_version=0):
        """
        Class to handle Visual Studio solution files

        Args:
            file_name: Pathname to the *.sln to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
            vs_version: Integer Visual Studio version
        """

        super().__init__(file_name, priority, configuration=configuration)
        self.verbose = verbose
        self.vs_version = vs_version

    def build(self):
        """
        Build a visual studio .sln file.

        Supports Visual Studio 2005 - 2022. Supports platforms Win32, x64,
        Android, nVidia Tegra, PS3, ORBIS, PSP, PSVita, Xbox, Xbox 360,
        Xbox ONE, Switch, Wii

        Returns:
            List of BuildError objects
        See Also:
            parse_sln_file
        """

        # Locate the proper version of Visual Studio for this .sln file
        vstudiopath = where_is_visual_studio(self.vs_version)

        # Is Visual studio installed?
        if vstudiopath is None:
            msg = (
                '{} requires Visual Studio version {}'
                ' to be installed to build!').format(
                self.file_name, self.vs_version)
            print(msg, file=sys.stderr)
            return BuildError(0, self.file_name, msg=msg)

        # Certain targets require an installed SDK
        # verify that the SDK is installed before trying to build

        targettypes = self.configuration.rsplit('|')
        if len(targettypes) >= 2:
            test_env = _VS_SDK_ENV_VARIABLE.get(targettypes[1], None)
            if test_env:
                if os.getenv(test_env, default=None) is None:
                    msg = (
                        'Target {} was detected but the environment variable {}'
                        ' was not found.').format(
                        targettypes[1], test_env)
                    print(msg, file=sys.stderr)
                    return BuildError(
                        0,
                        self.file_name,
                        configuration=self.configuration,
                        msg=msg)

        # Create the build command
        # Note: Use the single line form, because Windows will not
        # process the target properly due to the presence of the | character
        # which causes piping.

        # Visual Studio 2003 doesn't support setting platforms, just use the
        # configuration name
        if self.vs_version == 2003:
            target = targettypes[0]
        else:
            target = self.configuration

        cmd = [vstudiopath, self.file_name, '/Build', target]
        if self.verbose:
            print(' '.join(cmd))
        sys.stdout.flush()

        return self.run_command(cmd, self.verbose)

########################################


def add_vs_configurations(file_name, args):
    """
    Create BuildMakeFile build records for every desired configuration

    Args:
        file_name: Full pathname to the make file
        args: parser argument list
    Returns:
        list of BuildMakeFile classes
    """

    # Get the list of build targets
    targetlist, vs_version = parse_sln_file(file_name)

    # Was the file corrupted?
    if not vs_version:
        print(file_name + ' is corrupt!')
        return []

    results = []
    for target in targetlist:
        if args.configurations:
            targettypes = target.rsplit('|')
            if targettypes[0] not in args.configurations and \
                    targettypes[1] not in args.configurations:
                continue
        results.append(
            BuildVisualStudioFile(
                file_name,
                50,
                target,
                args.verbose,
                vs_version))

    return results

########################################


class BuildCodeWarriorFile(BuildObject):
    """
    Class to build CodeWarrior files

    Attributes:
        verbose: The verbose flag
        linkers: The linker list
    """

    # pylint: disable=too-many-arguments
    def __init__(self, file_name, priority, configuration,
                 verbose=False, linkers=None):
        """
        Class to handle CodeWarrior files

        Args:
            file_name: Pathname to the *.mcp to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
            linkers: List of linkers required
        """

        super().__init__(file_name, priority, configuration=configuration)
        self.verbose = verbose
        self.linkers = linkers

    def build(self):
        """
        Build a Metrowerks Codewarrior file.

        Supports .mcp files for Windows, Mac, Wii and DSI.

        Returns:
            List of BuildError objects
        See Also:
            parse_mcp_file
        """

        # pylint: disable=too-many-branches

        # Test which version of the CodeWarrior IDE that should be launched to
        # build a project with specific linkers.

        cw_path = None
        if get_windows_host_type():
            # Determine which version of CodeWarrior to run.
            # Test for 3DS or DSI
            if 'MW ARM Linker Panel' in self.linkers:
                cw_path = os.getenv('CWFOLDER_NITRO', default=None)
                if cw_path is None:
                    cw_path = os.getenv('CWFOLDER_TWL', default=None)

            # Test for Nintendo Wii
            elif 'PPC EABI Linker' in self.linkers:
                cw_path = os.getenv('CWFOLDER_RVL', default=None)

            # Test for Windows
            elif 'x86 Linker' in self.linkers:
                cw_path = os.getenv('CWFolder', default=None)

            if cw_path is None:
                return BuildError(
                    0, self.file_name,
                    msg="CodeWarrior with propler linker is not installed.")

            # Note: CmdIDE is preferred, however, Codewarrior 9.4 has a bug
            # that it will die horribly if the pathname to it
            # has a space, so ide is used instead.
            cw_path = os.path.join(cw_path, 'Bin', 'IDE.exe')
        else:

            # Handle mac version

            # Only CodeWarrior 9 has the Windows linker
            if 'x86 Linker' in self.linkers:
                cw_path = (
                    '/Applications/Metrowerks CodeWarrior 9.0'
                    '/Metrowerks CodeWarrior/CodeWarrior IDE')
                if not os.path.isfile(cw_path):
                    # Try an alternate path
                    cw_path = (
                        '/Applications/Metrowerks CodeWarrior 9.0'
                        '/Metrowerks CodeWarrior/CodeWarrior IDE 9.6')

            # Build with CodeWarrior 10
            elif any(i in ('68K Linker', 'PPC Linker') for i in self.linkers):
                cw_path = (
                    '/Applications/Metrowerks CodeWarrior 10.0'
                    '/Metrowerks CodeWarrior/CodeWarrior IDE')
                if not os.path.isfile(cw_path):
                    # Alternate path
                    cw_path = (
                        '/Applications/Metrowerks CodeWarrior 10.0'
                        '/Metrowerks CodeWarrior/CodeWarrior IDE 10')
            if cw_path is None:
                return BuildError(
                    0, self.file_name,
                    msg="CodeWarrior with proper linker is not installed.")

        # Create the temp folder in case there's an error file generated
        mytempdir = os.path.join(os.path.dirname(self.file_name), 'temp')
        create_folder_if_needed(mytempdir)

        # Use the proper dispatcher
        if get_windows_host_type():
            # Create the build command
            # /s New instance
            # /t Project name
            # /b Build
            # /c close the project after completion
            # /q Close Codewarrior on completion
            cmd = [
                cw_path,
                self.file_name,
                '/t',
                self.configuration,
                '/s',
                '/c',
                '/q',
                '/b']
        else:
            # Create the folder for the error log
            error_file = os.path.join(
                mytempdir,
                '{}-{}.err'.format(
                    os.path.splitext(
                        os.path.basename(
                            self.file_name))[0],
                    self.configuration))
            cmd = ['cmdide', '-proj', '-bcwef', error_file,
                '-y', cw_path, '-z', self.configuration, self.file_name]

        if self.verbose:
            print(' '.join(cmd))

        try:
            error_code = run_command(
                cmd, working_dir=os.path.dirname(self.file_name),
                quiet=not self.verbose)[0]
            msg = None
            if error_code and error_code < len(CODEWARRIOR_ERRORS):
                msg = CODEWARRIOR_ERRORS[error_code]
        except OSError as error:
            error_code = getattr(error, 'winerror', error.errno)
            msg = str(error)
            print(msg, file=sys.stderr)

        return BuildError(
            error_code,
            self.file_name,
            configuration=self.configuration,
            msg=msg)


########################################


def add_cw_configurations(file_name, args):
    """
    Create BuildMakeFile build records for every desired configuration

    Args:
        file_name: Full pathname to the make file
        args: parser argument list
    Returns:
        list of BuildMakeFile classes
    """

    # pylint: disable=too-many-branches

    # Test for older macOS or Windows
    if get_mac_host_type():
        if not is_codewarrior_mac_allowed():
            print('Codewarrior is not compatible with this version of macOS')
            return []
    elif not get_windows_host_type():
        print('Codewarrior is not compatible with this operating system')
        return []

    # Parse the MCP file to get the build targets and detected linkers
    targetlist, linkers, _ = parse_mcp_file(file_name)

    # Was the file corrupted?
    if targetlist is None:
        print(file_name + ' is corrupt')
        return []

    # Test for linkers that are not available on Windows
    if get_windows_host_type():
        if '68K Linker' in linkers:
            print(
                ('"{}" requires a 68k linker '
                'which Windows doesn\'t support.').format(file_name))
            return []

        if 'PPC Linker' in linkers:
            print(
                ('"{}" requires a PowerPC linker '
                'which Windows doesn\'t support.').format(file_name))
            return []

    # If everything is requested, then only build 'Everything'
    if not args.configurations and 'Everything' in targetlist:
        targetlist = ['Everything']

    results = []
    for target in targetlist:
        # Check if
        accept = True
        if args.configurations:
            accept = False
            for item in args.configurations:
                if item in target:
                    accept = True
                    break
        if accept:
            results.append(
                BuildCodeWarriorFile(
                    file_name,
                    50,
                    target,
                    args.verbose,
                    linkers))

    return results

########################################


class BuildXCodeFile(BuildObject):
    """
    Class to build Apple XCode files

    Attributes:
        verbose: The verbose flag
    """

    # pylint: disable=too-many-arguments
    def __init__(self, file_name, priority, configuration,
                 verbose=False):
        """
        Class to handle XCode files

        Args:
            file_name: Pathname to the *.xcodeproj to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
        """

        super().__init__(file_name, priority, configuration=configuration)
        self.verbose = verbose

    def build(self):
        """
        Build a macOS XCode file.

        Supports .xcodeproj files from Xcode 3 and later.

        Returns:
            List of BuildError objects
        See Also:
            parse_xcodeproj_file
        """

        # Get the list of build targets
        file_dir_name = os.path.dirname(self.file_name)
        file_name_lower = file_dir_name.lower()

        for item in _XCODE_SUFFIXES:
            if item[0] in file_name_lower:
                version = item[1]
                break
        else:
            version = None

        # Find XCode for the version needed
        xcode = where_is_xcode(version)

        # Is this version of XCode installed?
        if not xcode or not os.path.isfile(xcode[0]):
            msg = ('Can\'t build {}, the proper version '
                'of XCode is not installed').format(file_dir_name)
            print(msg)
            return BuildError(0, file_dir_name,
                            msg=msg)

        xcodebuild = xcode[0]
        # Create the build command
        cmd = [
            xcodebuild,
            '-project',
            os.path.basename(file_dir_name),
            '-alltargets',
            '-parallelizeTargets',
            '-configuration',
            self.configuration]

        if self.verbose:
            print(' '.join(cmd))

        try:
            error_code = run_command(
                cmd, working_dir=os.path.dirname(file_dir_name),
                quiet=not self.verbose)[0]
            msg = None
        except OSError as error:
            error_code = getattr(error, 'winerror', error.errno)
            msg = str(error)
            print(msg, file=sys.stderr)

        return BuildError(
            error_code,
            file_dir_name,
            configuration=self.configuration)

########################################


def add_xcode_configurations(file_name, args):
    """
    Create BuildXCodeFile build records for every desired configuration

    Args:
        file_name: Full pathname to the make file
        args: parser argument list
    Returns:
        list of BuildXCodeFile classes
    """

    # Don't build if not running on macOS
    if not get_mac_host_type():
        if args.verbose:
            print('{} can only be built on macOS hosts'.format(file_name))
        return []

    targetlist = parse_xcodeproj_file(file_name)

    # Was the file corrupted?
    if not targetlist:
        print(file_name + ' is corrupt!')
        return []

    results = []
    for target in targetlist:
        if args.configurations:
            if target not in args.configurations:
                continue
        results.append(
            BuildXCodeFile(
                file_name,
                50,
                target,
                args.verbose))

    return results

########################################


class BuildCodeBlocksFile(BuildObject):
    """
    Class to build Codeblocks files

    Attributes:
        verbose: The verbose flag
    """

    # pylint: disable=too-many-arguments
    def __init__(self, file_name, priority, configuration,
                 verbose=False):
        """
        Class to handle Codeblocks files

        Args:
            file_name: Pathname to the *.cbp to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
        """

        super().__init__(file_name, priority, configuration=configuration)
        self.verbose = verbose

    def build(self):
        """
        Build a Codeblocks project.

        Support .cbp files for Codeblocks on all host platforms.

        Returns:
            List of BuildError objects
        See Also:
        parse_codeblocks_file
        """

        # Commands available as of 13.12
        # --safe-mode
        # --no-check-associations
        # --no-dde
        # --no-splash-screen
        # --multiple-instance
        # --debug-log
        # --no-crash-handler
        # --verbose
        # --no-log
        # --log-to-file
        # --debug-log-to-file
        # --rebuild
        # --build
        # --clean
        # --target=
        # --no-batch-window-close
        # --batch-build-notify
        # --script=
        # --file=

        # Is Codeblocks installed?
        codeblocks_path = where_is_codeblocks()
        if codeblocks_path is None:
            return BuildError(
                0, self.file_name,
                msg='Requires Codeblocks to be installed to build!')

        if get_windows_host_type():
            if self.file_name.endswith('osx.cbp'):
                return BuildError(0, self.file_name,
                                msg="Can only be built on macOS")
            codeblocksflags = ['--no-check-associations', '--no-dde']
        else:
            if not self.file_name.endswith('osx.cbp'):
                return BuildError(0, self.file_name,
                                  msg="Can not be built on macOS")
            codeblocksflags = ['--no-ipc']

        # Parse the CBP file to get the build targets and detected linkers

        # Create the build command
        cmd = [codeblocks_path]
        cmd.extend(codeblocksflags)
        cmd.extend(['--no-splash-screen',
                    '--no-batch-window-close',
                    '--build', self.file_name,
                    '--target=' + self.configuration])

        if self.verbose:
            print(' '.join(cmd))

        return self.run_command(cmd, self.verbose)

########################################


def add_codeblocks_configurations(file_name, args):
    """
    Create BuildCodeBlocksFile build records for every desired configuration

    Args:
        file_name: Full pathname to the make file
        args: parser argument list
    Returns:
        list of BuildCodeBlocksFile classes
    """

    # pylint: disable=too-many-branches

    codeblocks_path = where_is_codeblocks()
    if codeblocks_path is None:
        print('Requires Codeblocks to be installed to build!')
        return []

    # Parse the CBP file to get the build targets and detected linkers
    targetlist = parse_codeblocks_file(file_name)

    # Was the file corrupted?
    if targetlist is None:
        print(file_name + ' is corrupt')
        return []

    # If everything is requested, then only build 'Everything'
    if not args.configurations and 'Everything' in targetlist:
        targetlist = ['Everything']

    results = []
    for target in targetlist:
        # Check if
        accept = True
        if args.configurations:
            accept = False
            for item in args.configurations:
                if item in target:
                    accept = True
                    break
        if accept:
            results.append(
                BuildCodeBlocksFile(
                    file_name,
                    50,
                    target,
                    args.verbose))

    return results

########################################


class BuildPythonFile(BuildObject):
    """
    Class to build with python scripts

    Attributes:
        verbose: the verbose flag
        command: Command for function
        function_ref: Function pointer
    """

    # pylint: disable=too-many-arguments
    def __init__(self, file_name, priority, verbose=False,
                 function_ref=None, command=None):
        """
        Class to handle Python files

        Args:
            file_name: Pathname to the *.py to build
            priority: Priority to build this object
            verbose: True if verbose output
            function_ref: Python function pointer
            command: Command to issue to the function
        """

        super().__init__(file_name, priority)
        self.verbose = verbose
        self.command = command
        self.function_ref = function_ref

    def has_python_function(self):
        """
        Return True if there's a callable python function.

        Returns:
            True if there is a callable python function.
        """
        return callable(self.function_ref)

    def create_parm_string(self):
        """
        Merge the command parameters into a single string.
        """
        parms = []
        for item in self.command:
            parms.append('{}="{}"'.format(item, self.command[item]))
        return ','.join(parms)

    def build(self):
        """
        Invoke a python function
        """
        if not self.has_python_function():
            if self.verbose:
                print('Invoking ' + self.file_name)
            error = run_py_script(
                self.file_name, 'main', os.path.dirname(self.file_name))
        else:
            if self.verbose:
                print(
                    'Calling {}({}) in {}'.format(
                        self.function_ref.__name__,
                        self.create_parm_string(),
                        self.file_name))
            error = self.function_ref(**self.command)
        return BuildError(error, self.file_name)

    def __repr__(self):
        """
        Convert the object into a string.

        Returns:
            A full string.
        """

        result = (
            '{} for file "{}" with priority {}').format(
                type(self).__name__,
                self.file_name,
                self.priority)
        if self.function_ref:
            result += ', function {}'.format(self.function_ref.__name__)
        if self.command:
            result += '({})'.format(self.create_parm_string())
        else:
            result += '()'
        return result

    def __str__(self):
        """
        Convert the object into a string.

        Returns:
            A full string.
        """

        return self.__repr__()

########################################


def add_build_rules(projects, file_name, args, build_rules=None):
    """
    Add a build_rules.py to the build list.

    Given a build_rules.py to parse, check it for a BUILD_LIST
    and use that for scanning for functions to call. If BUILD_LIST
    doesn't exist, use @ref buildme.BUILD_LIST instead.

    All valid entries will be appended to the projects list.

    Args:
        projects: List of projects to build.
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
        working_directory = os.path.dirname(file_name)
        command = {
            'working_directory': working_directory,
            'configuration': 'all'}

        # Get the dependency list
        dependencies = getattr(build_rules, 'BUILDME_DEPENDENCIES', None)
        if dependencies is None:
            # Try the generic one
            dependencies = getattr(build_rules, 'DEPENDENCIES', None)

        if dependencies:
            # Ensure it's an iterable of strings
            dependencies = convert_to_array(dependencies)
        else:
            dependencies = []

        for item in BUILD_LIST:
            # Only add if it's a function
            function_ref = getattr(build_rules, item[1], None)
            if function_ref:
                projects.append(
                    BuildPythonFile(
                        file_name,
                        item[0],
                        args.verbose,
                        function_ref=function_ref,
                        command=command))
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

    # Test for recursion
    if was_processed(processed, file_name, args.verbose):
        return True

    # Only process project files
    base_name = os.path.basename(file_name)
    base_name_lower = base_name.lower()

    # Test for python scripts.
    if base_name_lower == 'prebuild.py':
        projects.append(
            BuildPythonFile(
                file_name,
                1,
                args.verbose,
                command='main'))
        return True

    if base_name_lower == 'custombuild.py':
        projects.append(
            BuildPythonFile(
                file_name,
                40,
                args.verbose,
                command='main'))
        return True

    if base_name_lower == 'postbuild.py':
        projects.append(
            BuildPythonFile(
                file_name,
                99,
                args.verbose,
                command='main'))
        return True

    # Test for simple build files

    if base_name_lower.endswith('.slicerscript'):
        projects.append(BuildSlicerFile(file_name, 20, args.verbose))
        return True

    if base_name_lower.endswith('.rezscript'):
        projects.append(BuildRezFile(file_name, 25, args.verbose))
        return True

    if base_name_lower == 'doxyfile':
        if args.documentation:
            projects.append(BuildDoxygenFile(file_name, 90, args.verbose))
        return True

    # Test for IDE files
    if base_name_lower.endswith('.sln'):
        projects.extend(add_vs_configurations(file_name, args))
        return True

    if base_name_lower.endswith('.mcp'):
        projects.extend(add_cw_configurations(file_name, args))
        return True

    if base_name_lower.endswith('.wmk'):
        projects.extend(add_watcom_configurations(file_name, args))
        return True

    if base_name_lower == 'makefile' or base_name_lower.endswith('.mak'):
        projects.extend(add_make_configurations(file_name, args))
        return True

    if base_name_lower.endswith('.xcodeproj'):
        projects.extend(add_xcode_configurations(
            os.path.join(file_name, _XCODEPROJECT_FILE), args))
        return True

    if base_name_lower.endswith('.pbxproj'):
        projects.extend(add_xcode_configurations(file_name, args))
        return True

    if base_name_lower.endswith('.cbp'):
        projects.extend(add_codeblocks_configurations(file_name, args))
        return True

    if base_name_lower.endswith('.ninja'):
        projects.extend(add_ninja_configurations(file_name, args))
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

    # Build all the projects
    for project in projects:
        berror = project.build()
        error = 0
        if berror is not None:
            results.append(berror)
            error = berror.error

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
                    results, processed, add_build_rules(
                        projects, full_name, args), args)
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
            print("{} is not a directory.".format(working_directory))
            return 10

        # Pass one, create a list of all projects to build
        projects = []

        # Are there build rules?
        build_rules_name = os.path.join(working_directory, args.rules_file)
        build_rules = import_py_script(build_rules_name)
        allow_recursion = True
        if build_rules:
            # Check for recursion override
            if getattr(build_rules, 'BUILDME_NO_RECURSE', False):
                allow_recursion = False

            if not was_processed(processed, build_rules_name, args.verbose):
                process_dependencies(results, processed, add_build_rules(
                    projects, build_rules_name, args, build_rules), args)

        # Iterate over the directory to find all the other files
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
                            '"{}" is not supported on this platform.'.format(
                                full_name))
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
            else:
                error = process_files(results, processed, [item], args)
            if error:
                return error
    return 0

########################################


def main(working_directory=None, args=None):
    """
    Command line shell for ``buildme``.

    Entry point for the program ``buildme``, this function
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
        working_directory: Directory to operate on, or ``None``.
        args: Command line to use instead of ``sys.argv``.
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
        # pylint: disable=import-outside-toplevel
        from .config import save_default
        if args.verbose:
            print(
                'Saving {}'.format(
                    os.path.join(
                        working_directory,
                        BUILD_RULES_PY)))
        save_default(working_directory)
        return 0

    # Handle extra arguments
    fixup_args(args)

    # Make a list of directories to process if no entries
    if not args.directories and not args.files:
        args.directories = [working_directory]

    # List of errors created during building
    results = []
    processed = set()

    # Try building all individual files first
    if not process_files(results, processed, args.files, args):

        # If successful, process all directories
        process_directories(results, processed, args.directories, args)

    # Was there a build error?
    error = 0
    for item in results:
        if item.error:
            print('Errors detected in the build.', file=sys.stderr)
            error = item.error
            break
    else:
        if args.verbose:
            print('Build successful!')

    # Dump the error log if requested or an error
    if args.verbose or error:
        for item in results:
            if args.verbose or item.error:
                print(item)
    return error


# If called as a function and not a class, call my main
if __name__ == "__main__":
    sys.exit(main())
