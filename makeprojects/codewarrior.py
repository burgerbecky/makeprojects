#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Sub file for makeprojects.
# Handler for Codewarrior projects
#
# Version 5.0 is MacOS Codewarrior 9 and Windows Codewarrior 9
# Version 5.8 is MacOS Codewarrior 10
# Version 5.9 is Freescale Codewarrior for Nintendo
#

# Copyright 2019 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

from __future__ import absolute_import, print_function, unicode_literals
import os
import operator
import subprocess
import sys
import makeprojects.core
import burger
from makeprojects import AutoIntEnum, FileTypes, ProjectTypes, \
    IDETypes, PlatformTypes, Property
from .enums import configuration_short_code

if not burger.PY2:
    unicode = str

TAB = '\t'

#
## \package makeprojects.codewarrior
# This module contains classes needed to generate
# project files intended for use by Metrowerks /
# Freescale Codewarrior
#

#
# Class to hold the defaults and settings to output a Codewarrior
# compatible project file.
# json keyword "codewarrior" for dictionary of overrides
#


class Defaults(object):

    #
    # Power up defaults
    #

    def __init__(self):
        self.environmentvariables = []
        self.burgersdkspaths = []
        self.systemsearchpaths = []
        self.libraries = []

    #
    # The solution has been set up, perform setup
    # based on the type of project being created
    #

    def defaults(self, solution, configuration=None):
        self.environmentvariables = []
        self.burgersdkspaths = []
        self.systemsearchpaths = []
        self.libraries = []

        # In windows, set BURGER_SDKS as an environment variable
        if solution.projects[0].platform.is_windows():
            self.environmentvariables = ['BURGER_SDKS']

            # Add the default system directories
            if solution.projects[0].projecttype != ProjectTypes.library or \
                    solution.name != 'burgerlib':
                self.burgersdkspaths.append('windows\\burgerlib')
            self.burgersdkspaths.append('windows\\perforce')
            self.burgersdkspaths.append('windows\\opengl')
            self.burgersdkspaths.append('windows\\directx9')

            self.systemsearchpaths = ['MSL', 'Win32-x86 Support']

            self.libraries = [
                'advapi32.lib',
                'comctl32.lib',
                'gdi32.lib',
                'kernel32.lib',
                'ole32.lib',
                'opengl32.lib',
                'shell32.lib',
                'shlwapi.lib',
                'user32.lib',
                'version.lib',
                'winmm.lib'
            ]

        elif solution.projects[0].platform.is_macos():
            if solution.projects[0].projecttype != ProjectTypes.library or \
                    solution.name != 'burgerlib':
                self.burgersdkspaths.append('mac/burgerlib')
            self.burgersdkspaths.append('mac/gamesprockets')
            self.burgersdkspaths.append('mac/opengl')
            self.burgersdkspaths.append('codewarrior')

            if solution.projects[0].platform.is_macos_carbon():
                self.systemsearchpaths = ['MSL', 'MacOS Support']
                self.libraries = [
                    'CarbonLib',
                    'DrawSprocketStubLib',
                    'InputSprocketStubLib'
                ]

            elif solution.projects[0].platform.is_macos_classic():
                self.systemsearchpaths = ['MSL', 'MacOS Support']

                self.libraries = [
                    'DriverLoaderLib',
                    'InterfaceLib',
                    'MathLib'
                ]

    #
    # A json file had the key "codewarrior" with a dictionary.
    # Parse the dictionary for extra control
    #

    def loadjson(self, myjson):
        error = 0
        for key in myjson.keys():
            if key == 'systemsearchpaths':
                self.systemsearchpaths = burger.convert_to_array(myjson[key])
            elif key == 'burgersdkspaths':
                self.burgersdkspaths = burger.convert_to_array(myjson[key])
            elif key == 'environmentvariables':
                self.environmentvariables = burger.convert_to_array(myjson[key])
            else:
                print('Unknown keyword "' + str(key) + '" with data "' + str(myjson[key]) +
                      '" found in loadjson')
                error = 1

        return error

#
## Class for a simple setting entry
# This class handles the Name, Value and sub entries
#


class SETTING(object):
    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value
        self.subsettings = []

    #
    # Add a sub setting
    #

    def addsetting(self, name=None, value=None):
        entry = SETTING(name, value)
        self.subsettings.append(entry)
        return entry

    #
    # Write out a setting record, and all of its
    # sub settings
    #

    def write(self, fileref, level=4):
        tabs = TAB * level
        fileref.write(tabs + '<SETTING>')

        # Write the name record if one exists
        if self.name is not None:
            fileref.write('<NAME>' + self.name + '</NAME>')

        # Write the value record if one exists
        if self.value is not None:
            fileref.write('<VALUE>' + str(self.value) + '</VALUE>')

        # If there are sub settings, recurse and use
        # a tabbed /SETTING record
        if self.subsettings:
            fileref.write('\n')
            for item in self.subsettings:
                item.write(fileref, level + 1)
            fileref.write(tabs + '</SETTING>\n')
        else:
            # Close the setting record on the same line
            fileref.write('</SETTING>\n')

#
## Create an entry for UserSourceTrees
#


class UserSourceTree(object):

    #
    # Create the setting list
    #

    def __init__(self, name):
        self.settings = SETTING()
        self.settings.addsetting('Name', name)
        self.settings.addsetting('Kind', 'EnvironmentVariable')
        self.settings.addsetting('VariableName', name)

    #
    # Output the settings
    #

    def write(self, fileref, level=4):
        self.settings.write(fileref, level)

#
## Create a path entry for UserSearchPaths or SystemSearchPaths
#
# The title defaults to SearchPath, however it can be overridden
# such as OutputDirectory
#


class SearchPath(object):
    def __init__(self, platform, path, root=None, title='SearchPath'):
        self.settings = SETTING(title)
        if platform.is_windows():
            self.settings.addsetting('Path', burger.convert_to_windows_slashes(path))
            pathformat = 'Windows'
        else:
            self.settings.addsetting('Path', burger.convert_to_linux_slashes(path))
            pathformat = 'Unix'
        self.settings.addsetting('PathFormat', pathformat)
        if root is not None:
            self.settings.addsetting('PathRoot', root)

    #
    # Output the settings
    #

    def write(self, fileref, level=4):
        self.settings.write(fileref, level)

#
## Create a path entry for with flags for recursion
#


class SearchPathAndFlags(object):
    def __init__(self, platform, path, root=None, recursive=False):
        self.settings = [
            SearchPath(platform, path, root, 'SearchPath'),
            SETTING('Recursive', burger.truefalse(recursive)),
            SETTING('FrameworkPath', 'false'),
            SETTING('HostFlags', 'All')
        ]

    #
    # Output the settings
    #

    def write(self, fileref, level=4):
        for item in self.settings:
            item.write(fileref, level)

#
# Write out the settings for MWProject_X86
#


class MWProject_X86(object):
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

    def write(self, fileref, level=4):
        for item in self.settings:
            item.write(fileref, level)


class MWFrontEnd_C(object):
    def __init__(self):
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

    def write(self, fileref, level=4):
        for item in self.settings:
            item.write(fileref, level)


class C_CPP_Preprocessor(object):
    def __init__(self, defines):
        definestring = ''
        for item in defines:
            definestring = definestring + '#define ' + item + '\n'

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

    def write(self, fileref, level=4):
        for item in self.settings:
            item.write(fileref, level)


class MWWarning_C(object):
    def __init__(self):
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

    def write(self, fileref, level=4):
        for item in self.settings:
            item.write(fileref, level)


class MWCodeGen_X86(object):
    def __init__(self, configuration):
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

    def write(self, fileref, level=4):
        for item in self.settings:
            item.write(fileref, level)


class GlobalOptimizer_X86(object):
    def __init__(self, configuration):
        if configuration == 'Debug':
            level = 'Level0'
        else:
            level = 'Level4'

        self.settings = [
            SETTING('GlobalOptimizer_X86__optimizationlevel', level),
            SETTING('GlobalOptimizer_X86__optfor', 'Size')
        ]

    def write(self, fileref, level=4):
        for item in self.settings:
            item.write(fileref, level)


class PDisasmX86(object):
    def __init__(self):
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

    def write(self, fileref, level=4):
        for item in self.settings:
            item.write(fileref, level)


class MWLinker_X86(object):
    def __init__(self):
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

    def write(self, fileref, level=4):
        for item in self.settings:
            item.write(fileref, level)


class FILE(object):
    def __init__(self, platform, configuration, filename):
        if platform.is_windows():
            self.filename = burger.convert_to_windows_slashes(filename)
            self.format = 'Windows'
        else:
            self.filename = burger.convert_to_linux_slashes(filename)
            self.format = 'Unix'

        self.flags = ''
        if self.filename.endswith('.lib') or self.filename.endswith('.a'):
            self.kind = 'Library'
        else:
            self.kind = 'Text'
            if configuration != 'Release' and \
                    self.filename.endswith(('.c', '.cpp')):
                self.flags = 'Debug'

    def write(self, fileref, level=4):
        tabs = TAB * level
        tabs2 = tabs + TAB
        fileref.write(tabs + '<FILE>\n')
        fileref.write(tabs2 + '<PATHTYPE>Name</PATHTYPE>\n')
        fileref.write(tabs2 + '<PATH>' + self.filename + '</PATH>\n')
        fileref.write(tabs2 + '<PATHFORMAT>' + self.format + '</PATHFORMAT>\n')
        fileref.write(tabs2 + '<FILEKIND>' + self.kind + '</FILEKIND>\n')
        fileref.write(tabs2 + '<FILEFLAGS>' + self.flags + '</FILEFLAGS>\n')
        fileref.write(tabs + '</FILE>\n')


class FILEREF(object):
    def __init__(self, platform, configuration, filename):
        self.configuration = configuration
        if platform.is_windows():
            self.filename = burger.convert_to_windows_slashes(filename)
            self.format = 'Windows'
        else:
            self.filename = burger.convert_to_linux_slashes(filename)
            self.format = 'Unix'

    def write(self, fileref, level=4):
        tabs = TAB * level
        tabs2 = tabs + TAB
        fileref.write(tabs + '<FILEREF>\n')
        if self.configuration is not None:
            fileref.write(tabs2 + '<TARGETNAME>' + str(self.configuration) + '</TARGETNAME>\n')
        fileref.write(tabs2 + '<PATHTYPE>Name</PATHTYPE>\n')
        fileref.write(tabs2 + '<PATH>' + self.filename + '</PATH>\n')
        fileref.write(tabs2 + '<PATHFORMAT>' + self.format + '</PATHFORMAT>\n')
        fileref.write(tabs + '</FILEREF>\n')

#
# Each file group
#

class GROUP(object):
    def __init__(self, name):
        self.name = name
        self.groups = []
        self.filerefs = []

    def addfileref(self, platform, configuration, filename):
        # Was this filename already in the list?
        for item in self.filerefs:
            if item.filename == filename:
                return
        # Add to the list
        self.filerefs.append(FILEREF(platform, configuration, filename))

    def addgroup(self, name):
        for item in self.groups:
            if item.name == name:
                return item
        item = GROUP(name)
        self.groups.append(item)
        return item

    def write(self, fileref, level=2):
        if level == 1:
            groupstring = 'GROUPLIST'
        else:
            groupstring = 'GROUP'
        tabs = TAB * level
        fileref.write(tabs + '<' + groupstring + '>')
        if self.name is not None:
            fileref.write('<NAME>' + self.name + '</NAME>')
        fileref.write('\n')

        groups = sorted(self.groups, key=operator.attrgetter('name'))
        for item in groups:
            item.write(fileref, level + 1)

        filerefs = sorted(
            self.filerefs,
            key=lambda s: s.filename.lower())
        for item in filerefs:
            item.write(fileref, level + 1)
        fileref.write(tabs + '</' + groupstring + '>\n')

#
## Class for a sub target entry for the master target list
#


class SUBTARGET(object):
    def __init__(self, target):
        self.target = target

    def write(self, fileref, level=4):
        tabs = TAB * level
        tabs2 = tabs + TAB
        fileref.write(tabs + '<SUBTARGET>\n')
        fileref.write(tabs2 + '<TARGETNAME>' + str(self.target.name) + '</TARGETNAME>\n')
        fileref.write(tabs + '</SUBTARGET>\n')

#
## Each TARGET entry
# One entry is needed for each configuration to generate
# in a project file
#


class TARGET(object):
    def __init__(self, name, linker):
        self.name = name
        self.linker = linker
        self.settinglist = [SETTING('Linker', linker), SETTING('Targetname', name)]
        self.filelist = []
        self.linkorder = []
        self.subtargetlist = []

    #
    # Add a generic setting to this target
    #

    def addsetting(self, name=None, value=None):
        entry = SETTING(name, value)
        self.settinglist.append(entry)
        return entry

    #
    # Add a sub target reference to this target
    #

    def addsubtarget(self, target):
        entry = SUBTARGET(target)
        self.subtargetlist.append(entry)

    #
    # Write out this target record
    #

    def write(self, fileref, level=2):
        tabs = TAB * level
        tabs2 = tabs + TAB
        fileref.write(tabs + '<TARGET>\n')
        fileref.write(tabs2 + '<NAME>' + str(self.name) + '</NAME>\n')

        fileref.write(tabs2 + '<SETTINGLIST>\n')
        for item in self.settinglist:
            item.write(fileref, level + 2)
        fileref.write(tabs2 + '</SETTINGLIST>\n')

        fileref.write(tabs2 + '<FILELIST>\n')
        for item in self.filelist:
            item.write(fileref, level + 2)
        fileref.write(tabs2 + '</FILELIST>\n')

        fileref.write(tabs2 + '<LINKORDER>\n')
        for item in self.linkorder:
            item.write(fileref, level + 2)
        fileref.write(tabs2 + '</LINKORDER>\n')

        fileref.write(tabs2 + '<SUBTARGETLIST>\n')
        for item in self.subtargetlist:
            item.write(fileref, level + 2)
        fileref.write(tabs2 + '</SUBTARGETLIST>\n')

        fileref.write(tabs + '</TARGET>\n')

#
# Each TARGETORDER entry
#


class ORDEREDTARGET(object):
    def __init__(self, target):
        self.target = target

    def write(self, fileref, level=2):
        tabs = TAB * level
        fileref.write(tabs +
    '<ORDEREDTARGET><NAME>' +
    str(self.target.name) +
            '</NAME></ORDEREDTARGET>\n')

#
# Root object for an Code IDE project file
# Created with the name of the project, the IDE code (c50, c58)
# the platform code (win,mac)
#


class Project(object):
    def __init__(self, projectname, idecode, platformcode):
        self.projectname = projectname
        self.idecode = idecode
        self.platformcode = platformcode
        self.projectnamecode = str(projectname + idecode + platformcode)

        # Data chunks
        self.projects = []
        self.orderedtargets = []
        self.group = GROUP(None)

    #
    # Add a new TARGET
    #

    def addtarget(self, targetname, linker):
        entry = TARGET(targetname, linker)
        self.projects.append(entry)
        self.orderedtargets.append(ORDEREDTARGET(entry))
        return entry

    def addtogroups(self, platform, configuration, parts):
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

    #
    # Dump out the entire file
    #

    def write(self, fileref):

        #
        # Write the Codewarrior header
        #

        # Always use UTF-8 encoding
        fileref.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')

        # Set the version for the desired version of the Codewarrior IDE
        if self.idecode == 'c59':
            # Freescale Codewarrior for Nintendo DS
            exportversion = '2.0'
            ideversion = '5.9.0'
        elif self.idecode == 'c58':
            # Codewarrior 10 for Mac OS
            exportversion = '2.0'
            ideversion = '5.8'
        else:
            # Codewarrior 9 for Windows or MacOS
            exportversion = '1.0.1'
            ideversion = '5.0'

        fileref.write('<?codewarrior exportversion="' + exportversion +
                      '" ideversion="' + ideversion + '" ?>\n\n')

        # Write out the XML description template
        fileref.write(
            '<!DOCTYPE PROJECT [\n'
            '<!ELEMENT PROJECT (TARGETLIST, TARGETORDER, GROUPLIST, DESIGNLIST?)>\n'
            '<!ELEMENT TARGETLIST (TARGET+)>\n'
            '<!ELEMENT TARGET (NAME, SETTINGLIST, FILELIST?, LINKORDER?, SEGMENTLIST?, '
            'OVERLAYGROUPLIST?, SUBTARGETLIST?, SUBPROJECTLIST?, FRAMEWORKLIST?, PACKAGEACTIONSLIST?)>\n'
            '<!ELEMENT NAME (#PCDATA)>\n'
            '<!ELEMENT USERSOURCETREETYPE (#PCDATA)>\n'
            '<!ELEMENT PATH (#PCDATA)>\n'
            '<!ELEMENT FILELIST (FILE*)>\n'
            '<!ELEMENT FILE (PATHTYPE, PATHROOT?, ACCESSPATH?, PATH, PATHFORMAT?, '
            'ROOTFILEREF?, FILEKIND?, FILEFLAGS?)>\n'
            '<!ELEMENT PATHTYPE (#PCDATA)>\n'
            '<!ELEMENT PATHROOT (#PCDATA)>\n'
            '<!ELEMENT ACCESSPATH (#PCDATA)>\n'
            '<!ELEMENT PATHFORMAT (#PCDATA)>\n'
            '<!ELEMENT ROOTFILEREF (PATHTYPE, PATHROOT?, ACCESSPATH?, PATH, PATHFORMAT?)>\n'
            '<!ELEMENT FILEKIND (#PCDATA)>\n'
            '<!ELEMENT FILEFLAGS (#PCDATA)>\n'
            '<!ELEMENT FILEREF (TARGETNAME?, PATHTYPE, PATHROOT?, ACCESSPATH?, PATH, PATHFORMAT?)>\n'
            '<!ELEMENT TARGETNAME (#PCDATA)>\n'
            '<!ELEMENT SETTINGLIST ((SETTING|PANELDATA)+)>\n'
            '<!ELEMENT SETTING (NAME?, (VALUE|(SETTING+)))>\n'
            '<!ELEMENT PANELDATA (NAME, VALUE)>\n'
            '<!ELEMENT VALUE (#PCDATA)>\n'
            '<!ELEMENT LINKORDER (FILEREF*)>\n'
            '<!ELEMENT SEGMENTLIST (SEGMENT+)>\n'
            '<!ELEMENT SEGMENT (NAME, ATTRIBUTES?, FILEREF*)>\n'
            '<!ELEMENT ATTRIBUTES (#PCDATA)>\n'
            '<!ELEMENT OVERLAYGROUPLIST (OVERLAYGROUP+)>\n'
            '<!ELEMENT OVERLAYGROUP (NAME, BASEADDRESS, OVERLAY*)>\n'
            '<!ELEMENT BASEADDRESS (#PCDATA)>\n'
            '<!ELEMENT OVERLAY (NAME, FILEREF*)>\n'
            '<!ELEMENT SUBTARGETLIST (SUBTARGET+)>\n'
            '<!ELEMENT SUBTARGET (TARGETNAME, ATTRIBUTES?, FILEREF?)>\n'
            '<!ELEMENT SUBPROJECTLIST (SUBPROJECT+)>\n'
            '<!ELEMENT SUBPROJECT (FILEREF, SUBPROJECTTARGETLIST)>\n'
            '<!ELEMENT SUBPROJECTTARGETLIST (SUBPROJECTTARGET*)>\n'
            '<!ELEMENT SUBPROJECTTARGET (TARGETNAME, ATTRIBUTES?, FILEREF?)>\n'
            '<!ELEMENT FRAMEWORKLIST (FRAMEWORK+)>\n'
            '<!ELEMENT FRAMEWORK (FILEREF, DYNAMICLIBRARY?, VERSION?)>\n'
            '<!ELEMENT PACKAGEACTIONSLIST (PACKAGEACTION+)>\n'
            '<!ELEMENT PACKAGEACTION (#PCDATA)>\n'
            '<!ELEMENT LIBRARYFILE (FILEREF)>\n'
            '<!ELEMENT VERSION (#PCDATA)>\n'
            '<!ELEMENT TARGETORDER (ORDEREDTARGET|ORDEREDDESIGN)*>\n'
            '<!ELEMENT ORDEREDTARGET (NAME)>\n'
            '<!ELEMENT ORDEREDDESIGN (NAME, ORDEREDTARGET+)>\n'
            '<!ELEMENT GROUPLIST (GROUP|FILEREF)*>\n'
            '<!ELEMENT GROUP (NAME, (GROUP|FILEREF)*)>\n'
            '<!ELEMENT DESIGNLIST (DESIGN+)>\n'
            '<!ELEMENT DESIGN (NAME, DESIGNDATA)>\n'
            '<!ELEMENT DESIGNDATA (#PCDATA)>\n'
            ']>\n\n')

        # Start the project
        fileref.write('<PROJECT>\n')

        # Target settings
        fileref.write(TAB + '<TARGETLIST>\n')
        for item in self.projects:
            item.write(fileref, 2)
        fileref.write(TAB + '</TARGETLIST>\n')

        # Order of targets in the list
        fileref.write(TAB + '<TARGETORDER>\n')
        for item in self.orderedtargets:
            item.write(fileref, 2)
        fileref.write(TAB + '</TARGETORDER>\n')

        # File group list (Source file groupings)
        self.group.write(fileref, 1)

        # Wrap up the project file
        fileref.write('</PROJECT>\n')

#
# Create a project file for Codewarrior
#


def generate(solution):

    #
    # Find the files to put into the project
    #

    codefiles, includedirectories = solution.getfilelist([
        FileTypes.h, FileTypes.cpp, FileTypes.rc,
        FileTypes.hlsl, FileTypes.glsl])

    #
    # Configure the codewarrior writer to the type
    # of solution requested
    #

    solution.codewarrior.defaults(solution)

    #
    # Ensure the slashes are in Linux format (For MacOS)
    #

    for item in codefiles:
        item.filename = burger.convert_to_linux_slashes(item.filename)

    #
    # Determine the ide and target type for the final file name
    #

    idecode = solution.ide.get_short_code()
    platformcode = solution.projects[0].platform.get_short_code()
    codewarriorprojectfile = Project(solution.name, idecode, platformcode)

    #
    # Create a phony empty project called "Everything" that will
    # build all sub projects
    #

    rootproject = codewarriorprojectfile.addtarget('Everything', 'None')

    #
    # Get the source files that are compatible
    #

    listh = makeprojects.core.pickfromfilelist(codefiles, FileTypes.h)
    listcpp = makeprojects.core.pickfromfilelist(codefiles, FileTypes.cpp)
    listwindowsresource = []
    if solution.projects[0].platform.is_windows():
        listwindowsresource = makeprojects.core.pickfromfilelist(codefiles,
                                                                 FileTypes.rc)

    alllists = listh + listcpp + listwindowsresource

    #
    # Select the project linker for the platform
    #

    if solution.projects[0].platform.is_windows():
        linker = 'Win32 x86 Linker'
    else:
        linker = 'MacOS PPC Linker'

    #
    # Add every configuration to the project
    #

    for configuration in solution.projects[0].configurations:

        #
        # Create the project for the configuration
        # and add to the "Everything" project
        #

        target = codewarriorprojectfile.addtarget(configuration.name, linker)
        rootproject.addsubtarget(target)

        #
        # Add any environment variables if needed
        #

        if solution.codewarrior.environmentvariables:
            entry = target.addsetting('UserSourceTrees')
            for item in solution.codewarrior.environmentvariables:
                entry.subsettings.append(UserSourceTree(item))

        #
        # Create a OutputDirectory record for saving the output to the bin folder
        #
        target.settinglist.append(
            SearchPath(
                solution.projects[0].platform,
                'bin',
                'Project',
                'OutputDirectory'))

        #
        # User include folders
        #

        if includedirectories:
            usersearchpaths = target.addsetting('UserSearchPaths')
            for item in includedirectories:
                entry = usersearchpaths.addsetting()
                entry.subsettings.append(
                    SearchPathAndFlags(
                        solution.projects[0].platform,
                        item,
                        'Project',
                        False))

        #
        # System include folders
        #

        systemsearchpaths = target.addsetting('SystemSearchPaths')
        for item in solution.codewarrior.burgersdkspaths:
            entry = systemsearchpaths.addsetting()
            entry.subsettings.append(
                SearchPathAndFlags(
                    solution.projects[0].platform,
                    item,
                    'BURGER_SDKS',
                    False))

        for item in solution.codewarrior.systemsearchpaths:
            entry = systemsearchpaths.addsetting()
            entry.subsettings.append(
                SearchPathAndFlags(
                    solution.projects[0].platform,
                    item,
                    'CodeWarrior',
                    True))

        #
        # Generic settings for all platforms
        #

        # C/C++ Language
        target.settinglist.append(MWFrontEnd_C())

        platform = solution.projects[0].platform
        if platform.is_windows():
            platform = PlatformTypes.win32
        definelist = Property.getdata(
            solution.projects[0].properties,
            name="DEFINE",
            configuration=configuration.name,
            platform=platform)
        # C/C++ Preprocessor
        target.settinglist.append(C_CPP_Preprocessor(definelist))
        # C/C++ Warnings
        target.settinglist.append(MWWarning_C())

        #
        # Windows settings
        #

        if solution.projects[0].platform.is_windows():

            # x86 Target
            target.settinglist.append(
                MWProject_X86(
                    solution.projects[0].projecttype,
                    solution.name + idecode + 'w32'
                    + configuration_short_code(configuration.name)))

            # x86 CodeGen
            target.settinglist.append(MWCodeGen_X86(configuration.name))

            # Global Optimizations
            target.settinglist.append(GlobalOptimizer_X86(configuration.name))

            # x86 Dissassembler
            target.settinglist.append(PDisasmX86())

            # x86 Linker
            target.settinglist.append(MWLinker_X86())

        #
        # MacOS settings
        #

        #
        # Create the list of libraries to add to the project if
        # it's an application
        #

        liblist = []
        if solution.projects[0].projecttype != ProjectTypes.library:
            if configuration.name == 'Debug':
                liblist.append('burgerlibc50w32dbg.lib')
            elif configuration.name == 'Internal':
                liblist.append('burgerlibc50w32int.lib')
            else:
                liblist.append('burgerlibc50w32rel.lib')

            if configuration.name == 'Debug':
                liblist.append('MSL_All_x86_D.lib')
            else:
                liblist.append('MSL_All_x86.lib')

            liblist += solution.codewarrior.libraries

        #
        # Generate the file and group lists
        #

        if alllists or liblist:
            filelist = []
            for item in alllists:
                parts = item.filename.split('/')
                filelist.append(unicode(parts[len(parts) - 1]))
                # Add to file group
                codewarriorprojectfile.addtogroups(solution.projects[0].platform, configuration.name, parts)

            filelist = sorted(filelist, key=unicode.lower)
            for item in filelist:
                target.filelist.append(FILE(solution.projects[0].platform, configuration.name, item))
                target.linkorder.append(FILEREF(solution.projects[0].platform, None, item))

            # Sort case insensitive
            liblist = sorted(liblist, key=unicode.lower)
            for item in liblist:
                target.filelist.append(FILE(solution.projects[0].platform, configuration.name, item))
                target.linkorder.append(FILEREF(solution.projects[0].platform, None, item))
                # Add to file group
                codewarriorprojectfile.addtogroups(
                    solution.projects[0].platform, configuration.name, [
                        'Libraries', item])

    #
    # Let's create the solution file!
    #

    projectpathname = os.path.join(solution.working_directory,
                                   codewarriorprojectfile.projectnamecode + '.mcp.xml')

    #
    # Write out the file
    #

    burger.perforce_edit(projectpathname)
    fileref = open(projectpathname, 'w')
    codewarriorprojectfile.write(fileref)
    fileref.close()

    #
    # If codewarrior is installed, create the MCP file
    #

    cwfile = os.getenv('CWFolder')
    if cwfile is not None and solution.projects[0].platform.is_windows():
        mcppathname = os.path.join(solution.working_directory,
                                   codewarriorprojectfile.projectnamecode + '.mcp')
        burger.perforce_edit(mcppathname)
        cwfile = os.path.join(cwfile, 'Bin', 'ide')
        cmd = '"' + cwfile + '" /x "' + projectpathname + '" "' + mcppathname + '" /s /c /q'
        sys.stdout.flush()
        error = subprocess.call(cmd, cwd=os.path.dirname(projectpathname), shell=True)
        #if error==0:
        #    os.remove(projectpathname)
        return error
    return 0
