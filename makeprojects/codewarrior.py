#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sub file for makeprojects.

This module contains classes needed to generate
project files intended for use by Metrowerks /
Freescale Codewarrior

- Version 5.0 is MacOS Codewarrior 9 and Windows Codewarrior 9
- Version 5.8 is MacOS Codewarrior 10
- Version 5.9 is Freescale Codewarrior for Nintendo

@package makeprojects.codewarrior
"""

# Copyright 2019-2022 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

# pylint: disable=invalid-name
# pylint: disable=consider-using-f-string
# pylint: disable=too-few-public-methods
# pylint: disable=useless-object-inheritance

from __future__ import absolute_import, print_function, unicode_literals

import os
import operator
import subprocess
import sys
from struct import unpack as struct_unpack
from re import compile as re_compile
from burger import save_text_file_if_newer, perforce_edit, PY2, is_string, \
    convert_to_linux_slashes, convert_to_windows_slashes, truefalse, \
    read_zero_terminated_string, get_windows_host_type, run_command, \
    create_folder_if_needed, get_mac_host_type, is_codewarrior_mac_allowed
from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes
from .util import source_file_filter
from .core import BuildObject, BuildError

_MCPFILE_MATCH = re_compile('(?is).*\\.mcp\\Z')

if not PY2:
    unicode = str

SUPPORTED_IDES = (
    IDETypes.codewarrior50,
    IDETypes.codewarrior58,
    IDETypes.codewarrior59)

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


def match(filename):
    """
    Check if the filename is a type that this module supports

    Args:
        filename: Filename to match
    Returns:
        False if not a match, True if supported
    """

    return _MCPFILE_MATCH.match(filename)

########################################


def create_build_object(file_name, priority=50,
                 configurations=None, verbose=False):
    """
    Create BuildMakeFile build records for every desired configuration

    Args:
        file_name: Pathname to the *.mcp to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output
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
    if not configurations and 'Everything' in targetlist:
        targetlist = ['Everything']

    results = []
    for target in targetlist:
        # Check if
        accept = True
        if configurations:
            accept = False
            for item in configurations:
                if item in target:
                    accept = True
                    break
        if accept:
            results.append(
                BuildCodeWarriorFile(
                    file_name,
                    priority,
                    target,
                    verbose,
                    linkers))

    return results

########################################


def test(ide, platform_type):
    """ Filter for supported platforms

    Args:
        ide: IDETypes
        platform_type: PlatformTypes
    Returns:
        True if supported, False if not
    """

    # pylint: disable=unused-argument

    return platform_type in (
        PlatformTypes.win32,)


TAB = '\t'


class SETTING(object):
    """
    Class for a simple setting entry

    This class handles the Name, Value and sub entries

    Attributes:
        name: Name of the setting
        value: Value of the setting
        subsettings: Child settings
    """

    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value
        self.subsettings = []

    def addsetting(self, name=None, value=None):
        """
        Add a sub setting
        """
        entry = SETTING(name, value)
        self.subsettings.append(entry)
        return entry

    def generate(self, line_list, level=4):
        """
        Write out a setting record, and all of its
        sub settings
        """
        tabs = TAB * level
        entry = tabs + '<SETTING>'

        # Write the name record if one exists
        if self.name is not None:
            entry = entry + '<NAME>' + self.name + '</NAME>'

        # Write the value record if one exists
        if self.value is not None:
            if is_string(self.value):
                entry = entry + '<VALUE>' + self.value + '</VALUE>'
            else:
                entry = entry + '<VALUE>'
                for item in self.value:
                    line_list.append(entry + item)
                    entry = ''
                entry = entry + '</VALUE>'

        # If there are sub settings, recurse and use
        # a tabbed /SETTING record
        if self.subsettings:
            line_list.append(entry)
            for item in self.subsettings:
                item.generate(line_list, level + 1)
            line_list.append(tabs + '</SETTING>')
        else:
            # Close the setting record on the same line
            line_list.append(entry + '</SETTING>')


class UserSourceTree(object):

    """
    Create an entry for UserSourceTrees
    """

    def __init__(self, name):
        """
        Create the setting list
        """
        self.settings = SETTING()
        self.settings.addsetting('Name', name)
        self.settings.addsetting('Kind', 'EnvironmentVariable')
        self.settings.addsetting('VariableName', name)

    def generate(self, line_list, level=4):
        """
        Output the settings
        """
        self.settings.generate(line_list, level)


class SearchPath(object):
    """
    Create a path entry for UserSearchPaths or SystemSearchPaths.

    The title defaults to SearchPath, however it can be overridden
    such as OutputDirectory
    """

    def __init__(self, platform, path, root=None, title='SearchPath'):
        self.settings = SETTING(title)

        if path.startswith('$('):
            index = path.find(')')
            if index != -1:
                root = path[2:index]
                path = path[index + 1:]
                if path[0] in ('\\', '/'):
                    path = path[1:]

        if platform.is_windows():
            self.settings.addsetting(
                'Path', convert_to_windows_slashes(path))
            pathformat = 'Windows'
        else:
            self.settings.addsetting(
                'Path', convert_to_linux_slashes(path))
            pathformat = 'Unix'
        self.settings.addsetting('PathFormat', pathformat)
        if root is not None:
            self.settings.addsetting('PathRoot', root)

    def generate(self, line_list, level=4):
        """
        Output the settings
        """
        self.settings.generate(line_list, level)


class SearchPathAndFlags(object):
    """
    Create a path entry for with flags for recursion
    """

    def __init__(self, platform, path, root=None, recursive=False):
        if path.startswith('$(CodeWarrior)'):
            recursive = True

        self.settings = [
            SearchPath(platform, path, root, 'SearchPath'),
            SETTING('Recursive', truefalse(recursive)),
            SETTING('FrameworkPath', 'false'),
            SETTING('HostFlags', 'All')
        ]

    def generate(self, line_list, level=4):
        """
        Output the settings
        """
        for item in self.settings:
            item.generate(line_list, level)


class MWProject_X86(object):
    """
    Write out the settings for MWProject_X86
    """

    def __init__(self, projecttype, filename):
        if projecttype == ProjectTypes.library:
            x86type = 'Library'
            extension = '.lib'
        else:
            x86type = 'Application'
            extension = '.exe'

        self.settings = [
            SETTING('MWProject_X86_type', x86type),
            SETTING('MWProject_X86_outfile', filename + extension)
        ]

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        for item in self.settings:
            item.generate(line_list, level)


class MWFrontEnd_C(object):
    """
    MWFrontEnd_C generator

    Attributes:
        settings: List of setting objects for this generator
    """

    def __init__(self):
        """
        Initialize
        """
        self.settings = [
            SETTING('MWFrontEnd_C_cplusplus', '1'),
            SETTING('MWFrontEnd_C_templateparser', '0'),
            SETTING('MWFrontEnd_C_instance_manager', '0'),
            SETTING('MWFrontEnd_C_enableexceptions', '0'),
            SETTING('MWFrontEnd_C_useRTTI', '0'),
            SETTING('MWFrontEnd_C_booltruefalse', '1'),
            SETTING('MWFrontEnd_C_wchar_type', '0'),
            SETTING('MWFrontEnd_C_ecplusplus', '0'),
            SETTING('MWFrontEnd_C_dontinline', '0'),
            SETTING('MWFrontEnd_C_inlinelevel', '0'),
            SETTING('MWFrontEnd_C_autoinline', '1'),
            SETTING('MWFrontEnd_C_defer_codegen', '0'),
            SETTING('MWFrontEnd_C_bottomupinline', '1'),
            SETTING('MWFrontEnd_C_ansistrict', '0'),
            SETTING('MWFrontEnd_C_onlystdkeywords', '0'),
            SETTING('MWFrontEnd_C_trigraphs', '0'),
            SETTING('MWFrontEnd_C_arm', '0'),
            SETTING('MWFrontEnd_C_checkprotos', '1'),
            SETTING('MWFrontEnd_C_c99', '1'),
            SETTING('MWFrontEnd_C_gcc_extensions', '1'),
            SETTING('MWFrontEnd_C_enumsalwaysint', '1'),
            SETTING('MWFrontEnd_C_unsignedchars', '0'),
            SETTING('MWFrontEnd_C_poolstrings', '1'),
            SETTING('MWFrontEnd_C_dontreusestrings', '0')
        ]

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        for item in self.settings:
            item.generate(line_list, level)


class C_CPP_Preprocessor(object):
    """
    C_CPP_Preprocessor generator

    Attributes:
        settings: List of setting objects for this generator
    """

    def __init__(self, defines):
        """
        Initialize
        """
        definestring = []
        for item in defines:
            definestring.append('#define ' + item)

        self.settings = [
            SETTING('C_CPP_Preprocessor_PrefixText', definestring),
            SETTING('C_CPP_Preprocessor_MultiByteEncoding', 'encASCII_Unicode'),
            SETTING('C_CPP_Preprocessor_PCHUsesPrefixText', 'false'),
            SETTING('C_CPP_Preprocessor_EmitPragmas', 'true'),
            SETTING('C_CPP_Preprocessor_KeepWhiteSpace', 'false'),
            SETTING('C_CPP_Preprocessor_EmitFullPath', 'false'),
            SETTING('C_CPP_Preprocessor_KeepComments', 'false'),
            SETTING('C_CPP_Preprocessor_EmitFile', 'true'),
            SETTING('C_CPP_Preprocessor_EmitLine', 'false')
        ]

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        for item in self.settings:
            item.generate(line_list, level)


class MWWarning_C(object):
    """
    MWWarning_C generator

    Attributes:
        settings: List of setting objects for this generator
    """

    def __init__(self):
        """
        Initialize
        """
        self.settings = [
            SETTING('MWWarning_C_warn_illpragma', '1'),
            SETTING('MWWarning_C_warn_possunwant', '1'),
            SETTING('MWWarning_C_pedantic', '1'),
            SETTING('MWWarning_C_warn_illtokenpasting', '0'),
            SETTING('MWWarning_C_warn_hidevirtual', '1'),
            SETTING('MWWarning_C_warn_implicitconv', '1'),
            SETTING('MWWarning_C_warn_impl_f2i_conv', '1'),
            SETTING('MWWarning_C_warn_impl_s2u_conv', '1'),
            SETTING('MWWarning_C_warn_impl_i2f_conv', '1'),
            SETTING('MWWarning_C_warn_ptrintconv', '1'),
            SETTING('MWWarning_C_warn_unusedvar', '1'),
            SETTING('MWWarning_C_warn_unusedarg', '1'),
            SETTING('MWWarning_C_warn_resultnotused', '0'),
            SETTING('MWWarning_C_warn_missingreturn', '1'),
            SETTING('MWWarning_C_warn_no_side_effect', '1'),
            SETTING('MWWarning_C_warn_extracomma', '1'),
            SETTING('MWWarning_C_warn_structclass', '1'),
            SETTING('MWWarning_C_warn_emptydecl', '1'),
            SETTING('MWWarning_C_warn_filenamecaps', '0'),
            SETTING('MWWarning_C_warn_filenamecapssystem', '0'),
            SETTING('MWWarning_C_warn_padding', '0'),
            SETTING('MWWarning_C_warn_undefmacro', '0'),
            SETTING('MWWarning_C_warn_notinlined', '0'),
            SETTING('MWWarning_C_warningerrors', '0')
        ]

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        for item in self.settings:
            item.generate(line_list, level)


class MWCodeGen_X86(object):
    """
    MWCodeGen_X86 generator

    Attributes:
        settings: List of setting objects for this generator
    """

    def __init__(self, configuration):
        """
        Initialize
        """
        if configuration == 'Debug':
            disableopt = '1'
            optimizeasm = '0'
        else:
            disableopt = '0'
            optimizeasm = '1'

        self.settings = [
            SETTING('MWCodeGen_X86_processor', 'PentiumIV'),
            SETTING('MWCodeGen_X86_use_extinst', '1'),
            SETTING('MWCodeGen_X86_extinst_mmx', '0'),
            SETTING('MWCodeGen_X86_extinst_3dnow', '0'),
            SETTING('MWCodeGen_X86_extinst_cmov', '1'),
            SETTING('MWCodeGen_X86_extinst_sse', '0'),
            SETTING('MWCodeGen_X86_extinst_sse2', '0'),
            SETTING('MWCodeGen_X86_use_mmx_3dnow_convention', '0'),
            SETTING('MWCodeGen_X86_vectorize', '0'),
            SETTING('MWCodeGen_X86_profile', '0'),
            SETTING('MWCodeGen_X86_readonlystrings', '1'),
            SETTING('MWCodeGen_X86_alignment', 'bytes8'),
            SETTING('MWCodeGen_X86_intrinsics', '1'),
            SETTING('MWCodeGen_X86_optimizeasm', optimizeasm),
            SETTING('MWCodeGen_X86_disableopts', disableopt),
            SETTING('MWCodeGen_X86_relaxieee', '1'),
            SETTING('MWCodeGen_X86_exceptions', 'ZeroOverhead'),
            SETTING('MWCodeGen_X86_name_mangling', 'MWWin32')
        ]

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        for item in self.settings:
            item.generate(line_list, level)


class GlobalOptimizer_X86(object):
    """
    GlobalOptimizer_X86 generator

    Attributes:
        settings: List of setting objects for this generator
    """

    def __init__(self, configuration):
        """
        Initialize
        """
        if configuration == 'Debug':
            level = 'Level0'
        else:
            level = 'Level4'

        self.settings = [
            SETTING('GlobalOptimizer_X86__optimizationlevel', level),
            SETTING('GlobalOptimizer_X86__optfor', 'Size')
        ]

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        for item in self.settings:
            item.generate(line_list, level)


class PDisasmX86(object):
    """
    PDisasmX86 generator

    Attributes:
        settings: List of setting objects for this generator
    """

    def __init__(self):
        """
        Initialize
        """
        self.settings = [
            SETTING('PDisasmX86_showHeaders', 'true'),
            SETTING('PDisasmX86_showSectHeaders', 'true'),
            SETTING('PDisasmX86_showSymTab', 'true'),
            SETTING('PDisasmX86_showCode', 'true'),
            SETTING('PDisasmX86_showData', 'true'),
            SETTING('PDisasmX86_showDebug', 'false'),
            SETTING('PDisasmX86_showExceptions', 'false'),
            SETTING('PDisasmX86_showRelocation', 'true'),
            SETTING('PDisasmX86_showRaw', 'false'),
            SETTING('PDisasmX86_showAllRaw', 'false'),
            SETTING('PDisasmX86_showSource', 'false'),
            SETTING('PDisasmX86_showHex', 'true'),
            SETTING('PDisasmX86_showComments', 'false'),
            SETTING('PDisasmX86_resolveLocals', 'false'),
            SETTING('PDisasmX86_resolveRelocs', 'true'),
            SETTING('PDisasmX86_showSymDefs', 'true'),
            SETTING('PDisasmX86_unmangle', 'false'),
            SETTING('PDisasmX86_verbose', 'false')
        ]

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        for item in self.settings:
            item.generate(line_list, level)


class MWLinker_X86(object):
    """
    MWLinker_X86 generator

    Attributes:
        settings: List of setting objects for this generator
    """

    def __init__(self):
        """
        Initialize
        """
        self.settings = [
            SETTING('MWLinker_X86_runtime', 'Custom'),
            SETTING('MWLinker_X86_linksym', '0'),
            SETTING('MWLinker_X86_linkCV', '1'),
            SETTING('MWLinker_X86_symfullpath', 'false'),
            SETTING('MWLinker_X86_linkdebug', 'true'),
            SETTING('MWLinker_X86_debuginline', 'true'),
            SETTING('MWLinker_X86_subsystem', 'Unknown'),
            SETTING('MWLinker_X86_entrypointusage', 'Default'),
            SETTING('MWLinker_X86_entrypoint', ''),
            SETTING('MWLinker_X86_codefolding', 'Any'),
            SETTING('MWLinker_X86_usedefaultlibs', 'true'),
            SETTING('MWLinker_X86_adddefaultlibs', 'false'),
            SETTING('MWLinker_X86_mergedata', 'true'),
            SETTING('MWLinker_X86_zero_init_bss', 'false'),
            SETTING('MWLinker_X86_generatemap', '0'),
            SETTING('MWLinker_X86_checksum', 'false'),
            SETTING('MWLinker_X86_linkformem', 'false'),
            SETTING('MWLinker_X86_nowarnings', 'false'),
            SETTING('MWLinker_X86_verbose', 'false'),
            SETTING('MWLinker_X86_commandfile', '')
        ]

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        for item in self.settings:
            item.generate(line_list, level)


class FILE(object):
    """
    File name object

    Attributes:
        filename: Name of the file
        format: Windows or linux slashes
    """

    def __init__(self, platform, configuration, filename):
        """
        Initialize
        """
        if platform.is_windows():
            self.filename = convert_to_windows_slashes(filename)
            self.format = 'Windows'
        else:
            self.filename = convert_to_linux_slashes(filename)
            self.format = 'Unix'

        self.flags = ''
        if self.filename.endswith('.lib') or self.filename.endswith('.a'):
            self.kind = 'Library'
        else:
            self.kind = 'Text'
            if configuration != 'Release' and \
                    self.filename.endswith(('.c', '.cpp')):
                self.flags = 'Debug'

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        tabs = TAB * level
        tabs2 = tabs + TAB
        line_list.append(tabs + '<FILE>')
        line_list.append(tabs2 + '<PATHTYPE>Name</PATHTYPE>')
        line_list.append(tabs2 + '<PATH>' + self.filename + '</PATH>')
        line_list.append(tabs2 + '<PATHFORMAT>' + self.format + '</PATHFORMAT>')
        line_list.append(tabs2 + '<FILEKIND>' + self.kind + '</FILEKIND>')
        line_list.append(tabs2 + '<FILEFLAGS>' + self.flags + '</FILEFLAGS>')
        line_list.append(tabs + '</FILE>')


class FILEREF(object):
    """
    File reference object

    Attributes:
        configuration: Attached configuration
        filename: Name of the file
        format: Slash format
    """

    def __init__(self, platform, configuration, filename):
        """
        Initialize
        """
        self.configuration = configuration
        if platform.is_windows():
            self.filename = convert_to_windows_slashes(filename)
            self.format = 'Windows'
        else:
            self.filename = convert_to_linux_slashes(filename)
            self.format = 'Unix'

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        tabs = TAB * level
        tabs2 = tabs + TAB
        line_list.append(tabs + '<FILEREF>')
        if self.configuration is not None:
            line_list.append(tabs2 +
                             '<TARGETNAME>' +
                             str(self.configuration) +
                             '</TARGETNAME>')
        line_list.append(tabs2 + '<PATHTYPE>Name</PATHTYPE>')
        line_list.append(tabs2 + '<PATH>' + self.filename + '</PATH>')
        line_list.append(tabs2 + '<PATHFORMAT>' + self.format + '</PATHFORMAT>')
        line_list.append(tabs + '</FILEREF>')


class GROUP(object):
    """
    Each file group

    Attributes:
        name: Name of the group
        groups: Sub groups
        filerefs: List of files in this group
    """

    def __init__(self, name):
        """ Initialize """
        self.name = name
        self.groups = []
        self.filerefs = []

    def addfileref(self, platform, configuration, filename):
        """
        Add a file reference
        """
        # Was this filename already in the list?
        for item in self.filerefs:
            if item.filename == filename:
                return
        # Add to the list
        self.filerefs.append(FILEREF(platform, configuration, filename))

    def addgroup(self, name):
        """
        Add group
        """
        for item in self.groups:
            if item.name == name:
                return item
        item = GROUP(name)
        self.groups.append(item)
        return item

    def generate(self, line_list, level=2):
        """
        Generate output
        """
        if level == 1:
            groupstring = 'GROUPLIST'
        else:
            groupstring = 'GROUP'
        tabs = TAB * level
        entry = tabs + '<' + groupstring + '>'
        if self.name is not None:
            entry = entry + '<NAME>' + self.name + '</NAME>'
        line_list.append(entry)

        groups = sorted(self.groups, key=operator.attrgetter('name'))
        for item in groups:
            item.generate(line_list, level + 1)

        filerefs = sorted(
            self.filerefs,
            key=lambda s: s.filename.lower())
        for item in filerefs:
            item.generate(line_list, level + 1)
        line_list.append(tabs + '</' + groupstring + '>')


class SUBTARGET(object):
    """
    Class for a sub target entry for the master target list.

    Attributes:
        target: Sub target to build first
    """

    def __init__(self, target):
        """
        Initialize
        """
        self.target = target

    def generate(self, line_list, level=4):
        """
        Generate text
        """
        tabs = TAB * level
        tabs2 = tabs + TAB
        line_list.append(tabs + '<SUBTARGET>')
        line_list.append(tabs2 +
                         '<TARGETNAME>' +
                         str(self.target.name) +
                         '</TARGETNAME>')
        line_list.append(tabs + '</SUBTARGET>')


class TARGET(object):
    """
    Each TARGET entry

    One entry is needed for each configuration to generate
    in a project file

    Attribute:
        name: Name of the target
        linker: Linker used for the target
        settinglist: List of settings
        filelist: List of files
        linkorder: Order of linkage
        subtargetlist: List of sub targets
    """

    def __init__(self, name, linker):
        self.name = name
        self.linker = linker
        self.settinglist = [
            SETTING(
                'Linker', linker), SETTING(
                'Targetname', name)]
        self.filelist = []
        self.linkorder = []
        self.subtargetlist = []

    def addsetting(self, name=None, value=None):
        """
        Add a generic setting to this target
        """
        entry = SETTING(name, value)
        self.settinglist.append(entry)
        return entry

    def addsubtarget(self, target):
        """
        Add a sub target reference to this target
        """
        entry = SUBTARGET(target)
        self.subtargetlist.append(entry)

    def generate(self, line_list, level=2):
        """
        Write out this target record.
        """
        tabs = TAB * level
        tabs2 = tabs + TAB
        line_list.append(tabs + '<TARGET>')
        line_list.append(tabs2 + '<NAME>' + str(self.name) + '</NAME>')

        line_list.append(tabs2 + '<SETTINGLIST>')
        for item in self.settinglist:
            item.generate(line_list, level + 2)
        line_list.append(tabs2 + '</SETTINGLIST>')

        line_list.append(tabs2 + '<FILELIST>')
        for item in self.filelist:
            item.generate(line_list, level + 2)
        line_list.append(tabs2 + '</FILELIST>')

        line_list.append(tabs2 + '<LINKORDER>')
        for item in self.linkorder:
            item.generate(line_list, level + 2)
        line_list.append(tabs2 + '</LINKORDER>')

        line_list.append(tabs2 + '<SUBTARGETLIST>')
        for item in self.subtargetlist:
            item.generate(line_list, level + 2)
        line_list.append(tabs2 + '</SUBTARGETLIST>')

        line_list.append(tabs + '</TARGET>')


class ORDEREDTARGET(object):
    """
    Each TARGETORDER entry

    Attributes:
        target: Target to build
    """

    def __init__(self, target):
        """
        Initialize
        """
        self.target = target

    def generate(self, line_list, level=2):
        """
        Generate the text
        """
        tabs = TAB * level
        line_list.append(tabs +
                         '<ORDEREDTARGET><NAME>' +
                         str(self.target.name) +
                         '</NAME></ORDEREDTARGET>')


class Project(object):
    """
    Root object for an CodeWarrior IDE project file.

    Created with the name of the project, the IDE code (c50, c58)
    the platform code (win,mac)

    Attributes:
        solution: Parent solution
        configuration_list: List of all configurations
        projectname: Name of the project
        idecode: IDE code for the project
        platformcode: Ascii code for the platform
        projectnamecode: projectname + idecode + platformcode
        project_list: List of sub projects
        orderedtargets: Target order
        group: Group list
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, solution, projectname=None,
                 idecode=None, platformcode=None):
        """
        Initialize the exporter.
        """

        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-locals

        self.solution = solution
        self.configuration_list = []

        self.projectname = projectname
        self.idecode = idecode
        self.platformcode = platformcode
        self.projectnamecode = ''  # str(projectname + idecode + platformcode)

        # Data chunks
        self.project_list = []
        self.orderedtargets = []
        self.group = GROUP(None)

        # Create a phony empty project called "Everything" that will
        # build all sub project
        rootproject = self.addtarget('Everything', 'None')

        # Process all the projects and configurations
        for project in solution.get_project_list():

            # Make sure a platform was present
            if project.platform is None:
                project.platform = project.configuration_list[0].platform

            # Process the filenames
            project.get_file_list([FileTypes.h,
                                   FileTypes.cpp,
                                   FileTypes.c,
                                   FileTypes.rc
                                   ])

            # Add to the master list
            self.configuration_list.extend(project.configuration_list)

            # Get the source files that are compatible
            listh = source_file_filter(project.codefiles, FileTypes.h)
            listcpp = source_file_filter(project.codefiles, FileTypes.cpp)
            listwindowsresource = []
            if project.platform.is_windows():
                listwindowsresource = source_file_filter(
                    project.codefiles, FileTypes.rc)
            alllists = listh + listcpp + listwindowsresource

            # Select the project linker for the platform
            if project.platform.is_windows():
                linker = 'Win32 x86 Linker'
            else:
                linker = 'MacOS PPC Linker'

            # Create sets of configuration names and projects
            for configuration in project.configuration_list:
                if not configuration.library_folders_list:
                    if project.platform.is_windows():
                        configuration.library_folders_list = [
                            '$(CodeWarrior)/MSL',
                            '$(CodeWarrior)/Win32-x86 Support']
                        if not configuration.project_type.is_library():
                            if configuration.debug:
                                configuration.libraries_list.append(
                                    'MSL_All_x86_D.lib')
                            else:
                                configuration.libraries_list.append(
                                    'MSL_All_x86.lib')

                configuration.cw_name = configuration.name

                # Create the project for the configuration
                # and add to the "Everything" project
                target = self.addtarget(configuration.cw_name, linker)
                rootproject.addsubtarget(target)

                # Add any environment variables if needed

                temp_list = configuration.get_unique_chained_list(
                    'cw_environment_variables')
                if temp_list:
                    entry = target.addsetting('UserSourceTrees')
                    for item in temp_list:
                        entry.subsettings.append(UserSourceTree(item))

                # Create a OutputDirectory record for saving
                # the output to the bin folder
                target.settinglist.append(
                    SearchPath(
                        configuration.platform,
                        'bin',
                        'Project',
                        'OutputDirectory'))

                # User include folders
                temp_list = configuration.get_unique_chained_list(
                    '_source_include_list')
                temp_list.extend(configuration.get_unique_chained_list(
                    'include_folders_list'))

                if temp_list:
                    usersearchpaths = target.addsetting('UserSearchPaths')
                    for item in temp_list:
                        entry = usersearchpaths.addsetting()
                        entry.subsettings.append(
                            SearchPathAndFlags(
                                configuration.platform,
                                item,
                                'Project',
                                False))

                # System include folders
                temp_list = configuration.get_unique_chained_list(
                    '_library_folders_list')
                if temp_list:
                    systemsearchpaths = target.addsetting('SystemSearchPaths')
                    for item in temp_list:
                        entry = systemsearchpaths.addsetting()
                        entry.subsettings.append(
                            SearchPathAndFlags(
                                solution.project_list[0].platform,
                                item,
                                'CodeWarrior',
                                False))

                # Generic settings for all platforms

                # C/C++ Language
                target.settinglist.append(MWFrontEnd_C())

                definelist = configuration.get_chained_list('define_list')
                # C/C++ Preprocessor
                target.settinglist.append(C_CPP_Preprocessor(definelist))
                # C/C++ Warnings
                target.settinglist.append(MWWarning_C())

                # Windows settings
                if configuration.platform.is_windows():

                    # x86 Target
                    target.settinglist.append(
                        MWProject_X86(
                            configuration.project_type,
                            solution.name +
                            solution.ide.get_short_code() +
                            'w32' +
                            configuration.short_code))

                    # x86 CodeGen
                    target.settinglist.append(MWCodeGen_X86(configuration.name))

                    # Global Optimizations
                    target.settinglist.append(
                        GlobalOptimizer_X86(
                            configuration.name))

                    # x86 Dissassembler
                    target.settinglist.append(PDisasmX86())

                    # x86 Linker
                    target.settinglist.append(MWLinker_X86())

                # Create the list of libraries to add to the project if
                # it's an application

                liblist = []
                if not configuration.project_type.is_library():
                    liblist = configuration.get_unique_chained_list(
                        'libraries_list')

                # Generate the file and group lists
                if alllists or liblist:
                    filelist = []
                    for item in alllists:
                        parts = convert_to_linux_slashes(
                            item.relative_pathname).split('/')
                        filelist.append(unicode(parts[len(parts) - 1]))
                        # Add to file group
                        self.addtogroups(
                            configuration.platform, configuration.name, parts)

                    filelist = sorted(filelist, key=unicode.lower)
                    for item in filelist:
                        target.filelist.append(
                            FILE(
                                configuration.platform,
                                configuration.name,
                                item))
                        target.linkorder.append(
                            FILEREF(
                                configuration.platform,
                                None,
                                item))

                    # Sort case insensitive
                    liblist = sorted(liblist, key=unicode.lower)
                    for item in liblist:
                        target.filelist.append(
                            FILE(
                                configuration.platform,
                                configuration.name,
                                item))
                        target.linkorder.append(
                            FILEREF(
                                configuration.platform,
                                None,
                                item))
                        # Add to file group
                        self.addtogroups(
                            configuration.platform, configuration.name, [
                                'Libraries', item])

    def addtarget(self, targetname, linker):
        """
        Add a new TARGET
        """
        entry = TARGET(targetname, linker)
        self.project_list.append(entry)
        self.orderedtargets.append(ORDEREDTARGET(entry))
        return entry

    def addtogroups(self, platform, configuration, parts):
        """
        Add a new group
        """
        # Discard any .. or . directory prefixes
        while parts and (parts[0] == '.' or parts[0] == '..'):
            parts.pop(0)

        if parts:
            # Nothing left?
            group = self.group

            while True:
                if len(parts) == 1:
                    group.addfileref(platform, configuration, parts[0])
                    return
                group = group.addgroup(parts[0])
                parts.pop(0)

    def generate(self, line_list=None):
        """
        Write out the Codewarrior project.

        Args:
            line_list: string list to save the XML text
        """

        # Always use UTF-8 encoding
        line_list.append(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>')

        # Set the version for the desired version of the Codewarrior IDE
        ide = self.solution.ide
        if ide is IDETypes.codewarrior59:
            # Freescale Codewarrior for Nintendo DS
            exportversion = '2.0'
            ideversion = '5.9.0'
        elif ide is IDETypes.codewarrior58:
            # Codewarrior 10 for Mac OS
            exportversion = '2.0'
            ideversion = '5.8'
        else:
            # Codewarrior 9 for Windows or MacOS
            exportversion = '1.0.1'
            ideversion = '5.0'

        line_list.append('<?codewarrior exportversion="' + exportversion +
                         '" ideversion="' + ideversion + '" ?>')

        # Write out the XML description template
        line_list.extend([
            '',
            '<!DOCTYPE PROJECT [',
            ('<!ELEMENT PROJECT (TARGETLIST, TARGETORDER, '
                'GROUPLIST, DESIGNLIST?)>'),
            '<!ELEMENT TARGETLIST (TARGET+)>',
            ('<!ELEMENT TARGET (NAME, SETTINGLIST, FILELIST?, '
                'LINKORDER?, SEGMENTLIST?, '
                'OVERLAYGROUPLIST?, SUBTARGETLIST?, SUBPROJECTLIST?, '
                'FRAMEWORKLIST?, PACKAGEACTIONSLIST?)>'),
            '<!ELEMENT NAME (#PCDATA)>',
            '<!ELEMENT USERSOURCETREETYPE (#PCDATA)>',
            '<!ELEMENT PATH (#PCDATA)>',
            '<!ELEMENT FILELIST (FILE*)>',
            ('<!ELEMENT FILE (PATHTYPE, PATHROOT?, ACCESSPATH?, PATH, '
                'PATHFORMAT?, ROOTFILEREF?, FILEKIND?, FILEFLAGS?)>'),
            '<!ELEMENT PATHTYPE (#PCDATA)>',
            '<!ELEMENT PATHROOT (#PCDATA)>',
            '<!ELEMENT ACCESSPATH (#PCDATA)>',
            '<!ELEMENT PATHFORMAT (#PCDATA)>',
            ('<!ELEMENT ROOTFILEREF (PATHTYPE, PATHROOT?, '
                'ACCESSPATH?, PATH, PATHFORMAT?)>'),
            '<!ELEMENT FILEKIND (#PCDATA)>',
            '<!ELEMENT FILEFLAGS (#PCDATA)>',
            ('<!ELEMENT FILEREF (TARGETNAME?, PATHTYPE, PATHROOT?, '
                'ACCESSPATH?, PATH, PATHFORMAT?)>'),
            '<!ELEMENT TARGETNAME (#PCDATA)>',
            '<!ELEMENT SETTINGLIST ((SETTING|PANELDATA)+)>',
            '<!ELEMENT SETTING (NAME?, (VALUE|(SETTING+)))>',
            '<!ELEMENT PANELDATA (NAME, VALUE)>',
            '<!ELEMENT VALUE (#PCDATA)>',
            '<!ELEMENT LINKORDER (FILEREF*)>',
            '<!ELEMENT SEGMENTLIST (SEGMENT+)>',
            '<!ELEMENT SEGMENT (NAME, ATTRIBUTES?, FILEREF*)>',
            '<!ELEMENT ATTRIBUTES (#PCDATA)>',
            '<!ELEMENT OVERLAYGROUPLIST (OVERLAYGROUP+)>',
            '<!ELEMENT OVERLAYGROUP (NAME, BASEADDRESS, OVERLAY*)>',
            '<!ELEMENT BASEADDRESS (#PCDATA)>',
            '<!ELEMENT OVERLAY (NAME, FILEREF*)>',
            '<!ELEMENT SUBTARGETLIST (SUBTARGET+)>',
            '<!ELEMENT SUBTARGET (TARGETNAME, ATTRIBUTES?, FILEREF?)>',
            '<!ELEMENT SUBPROJECTLIST (SUBPROJECT+)>',
            '<!ELEMENT SUBPROJECT (FILEREF, SUBPROJECTTARGETLIST)>',
            '<!ELEMENT SUBPROJECTTARGETLIST (SUBPROJECTTARGET*)>',
            '<!ELEMENT SUBPROJECTTARGET (TARGETNAME, ATTRIBUTES?, FILEREF?)>',
            '<!ELEMENT FRAMEWORKLIST (FRAMEWORK+)>',
            '<!ELEMENT FRAMEWORK (FILEREF, DYNAMICLIBRARY?, VERSION?)>',
            '<!ELEMENT PACKAGEACTIONSLIST (PACKAGEACTION+)>',
            '<!ELEMENT PACKAGEACTION (#PCDATA)>',
            '<!ELEMENT LIBRARYFILE (FILEREF)>',
            '<!ELEMENT VERSION (#PCDATA)>',
            '<!ELEMENT TARGETORDER (ORDEREDTARGET|ORDEREDDESIGN)*>',
            '<!ELEMENT ORDEREDTARGET (NAME)>',
            '<!ELEMENT ORDEREDDESIGN (NAME, ORDEREDTARGET+)>',
            '<!ELEMENT GROUPLIST (GROUP|FILEREF)*>',
            '<!ELEMENT GROUP (NAME, (GROUP|FILEREF)*)>',
            '<!ELEMENT DESIGNLIST (DESIGN+)>',
            '<!ELEMENT DESIGN (NAME, DESIGNDATA)>',
            '<!ELEMENT DESIGNDATA (#PCDATA)>',
            ']>',
            ''
        ])

        # Start the project
        line_list.append('<PROJECT>')

        # Target settings
        line_list.append(TAB + '<TARGETLIST>')
        for item in self.project_list:
            item.generate(line_list, 2)
        line_list.append(TAB + '</TARGETLIST>')

        # Order of targets in the list
        line_list.append(TAB + '<TARGETORDER>')
        for item in self.orderedtargets:
            item.generate(line_list, 2)
        line_list.append(TAB + '</TARGETORDER>')

        # File group list (Source file groupings)
        self.group.generate(line_list, 1)

        # Wrap up the project file
        line_list.append('</PROJECT>')
        return 0


########################################


def generate(solution):
    """
    Create a project file for Metrowerks CodeWarrior.

    Given a Solution object, create an appropriate Watcom WMAKE
    file to allow this project to build.

    Args:
        solution: Solution instance.

    Returns:
        Zero if no error, non-zero on error.
    """

    # Failsafe
    if solution.ide not in SUPPORTED_IDES:
        return 10

    # Create the output filename and pass it to the generator
    # so it can reference itself in make targets
    solution.codewarrior_filename = '{}{}{}.mcp'.format(
        solution.name, solution.ide_code, solution.platform_code)

    exporter = Project(solution)

    # Output the actual project file
    codewarrior_lines = []
    error = exporter.generate(codewarrior_lines)
    if error:
        return error

    # Save the file if it changed
    xml_filename = os.path.join(
        solution.working_directory,
        solution.codewarrior_filename + '.xml')

    error = 0
    if not save_text_file_if_newer(
            xml_filename,
            codewarrior_lines,
            bom=False,
            perforce=solution.perforce,
            verbose=solution.verbose):

        # If a file was updated and codewarrior is installed, create the MCP
        # file

        cwfile = os.getenv('CWFolder')
        if cwfile is not None and solution.ide in (IDETypes.codewarrior50,):
            mcp_filename = os.path.join(
                solution.working_directory,
                solution.codewarrior_filename)

            perforce_edit(mcp_filename)
            cwfile = os.path.join(cwfile, 'Bin', 'ide')
            cmd = '"' + cwfile + '" /x "' + xml_filename + \
                '" "' + mcp_filename + '" /s /c /q'
            if solution.verbose:
                print(cmd)
            error = subprocess.call(
                cmd, cwd=os.path.dirname(xml_filename), shell=True)
    return error
