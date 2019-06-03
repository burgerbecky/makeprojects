#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Sub file for makeprojects.
# Handler for Codeblocks projects
#

# Copyright 1995-2019 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

#
## \package makeprojects.codeblocks
# This module contains classes needed to generate
# project files intended for use by Codeblocks
#

from __future__ import absolute_import, print_function, unicode_literals
import os
import burger
from .enums import FileTypes, ProjectTypes
from .core import source_file_filter

#
# Create a codeblocks 13.12 project
#


def generate(solution):

    #
    # Now, let's create the project file
    #

    codefiles, includedirectories = solution.getfilelist(
        [FileTypes.h, FileTypes.cpp, FileTypes.rc, FileTypes.hlsl, FileTypes.glsl])
    platformcode = solution.project_list[0].get_attribute('platform').get_short_code()
    idecode = solution.ide.get_short_code()
    projectfilename = str(solution.attributes['name'] + idecode + platformcode)
    projectpathname = os.path.join(
        solution.attributes['working_directory'], projectfilename + '.cbp')

    #
    # Save out the filenames
    #

    listh = source_file_filter(codefiles, FileTypes.h)
    listcpp = source_file_filter(codefiles, FileTypes.cpp)
    listwindowsresource = []
    if platformcode == 'win':
        listwindowsresource = source_file_filter(codefiles, FileTypes.rc)

    alllists = listh + listcpp + listwindowsresource

    burger.perforce_edit(projectpathname)
    fp = open(projectpathname, 'w')

    #
    # Save the standard XML header for CodeBlocks
    #

    fp.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
    fp.write('<CodeBlocks_project_file>\n')
    fp.write('\t<FileVersion major="1" minor="6" />\n')
    fp.write('\t<Project>\n')

    #
    # Output the project settings
    #

    fp.write('\t\t<Option title="burgerlib" />\n')
    fp.write('\t\t<Option makefile="makefile" />\n')
    fp.write('\t\t<Option pch_mode="2" />\n')
    fp.write('\t\t<Option compiler="ow" />\n')

    #
    # Output the per target build settings
    #

    fp.write('\t\t<Build>\n')

    fp.write('\t\t\t<Target title="Debug">\n')
    fp.write('\t\t\t\t<Option output="bin/burgerlibcdbwatw32dbg.lib" prefix_auto="0" extension_auto="0" />\n')
    fp.write('\t\t\t\t<Option working_dir="" />\n')
    fp.write('\t\t\t\t<Option object_output="temp/burgerlibcbpwatw32dbg/" />\n')
    if solution.project_list[0].get_attribute('project_type') == ProjectTypes.tool:
        fp.write('\t\t\t\t<Option type="1" />\n')
    else:
        fp.write('\t\t\t\t<Option type="2" />\n')
    fp.write('\t\t\t\t<Option compiler="ow" />\n')
    fp.write('\t\t\t\t<Option createDefFile="1" />\n')
    fp.write('\t\t\t\t<Compiler>\n')
    fp.write('\t\t\t\t\t<Add option="-d2" />\n')
    fp.write('\t\t\t\t\t<Add option="-wx" />\n')
    fp.write('\t\t\t\t\t<Add option="-fp6" />\n')
    fp.write('\t\t\t\t\t<Add option="-6r" />\n')
    fp.write('\t\t\t\t\t<Add option="-fr=$(ERROR_FILE)" />\n')
    fp.write('\t\t\t\t\t<Add option="-d_DEBUG" />\n')
    fp.write('\t\t\t\t</Compiler>\n')
    fp.write('\t\t\t</Target>\n')

    fp.write('\t\t\t<Target title="Internal">\n')
    fp.write('\t\t\t\t<Option output="bin/burgerlibcdbwatw32int.lib" prefix_auto="0" extension_auto="0" />\n')
    fp.write('\t\t\t\t<Option working_dir="" />\n')
    fp.write('\t\t\t\t<Option object_output="temp/burgerlibcbpwatw32int/" />\n')
    if solution.project_list[0].get_attribute('project_type') == ProjectTypes.tool:
        fp.write('\t\t\t\t<Option type="1" />\n')
    else:
        fp.write('\t\t\t\t<Option type="2" />\n')
    fp.write('\t\t\t\t<Option compiler="ow" />\n')
    fp.write('\t\t\t\t<Option createDefFile="1" />\n')
    fp.write('\t\t\t\t<Compiler>\n')
    fp.write('\t\t\t\t\t<Add option="-ox" />\n')
    fp.write('\t\t\t\t\t<Add option="-ot" />\n')
    fp.write('\t\t\t\t\t<Add option="-wx" />\n')
    fp.write('\t\t\t\t\t<Add option="-fr=$(ERROR_FILE)" />\n')
    fp.write('\t\t\t\t\t<Add option="-fp6" />\n')
    fp.write('\t\t\t\t\t<Add option="-6r" />\n')
    fp.write('\t\t\t\t\t<Add option="-d_DEBUG" />\n')
    fp.write('\t\t\t\t</Compiler>\n')
    fp.write('\t\t\t</Target>\n')

    fp.write('\t\t\t<Target title="Release">\n')
    fp.write('\t\t\t\t<Option output="bin/burgerlibcdbwatw32rel.lib" prefix_auto="0" extension_auto="0" />\n')
    fp.write('\t\t\t\t<Option working_dir="" />\n')
    fp.write('\t\t\t\t<Option object_output="temp/burgerlibcbpwatw32rel/" />\n')
    if solution.project_list[0].get_attribute('project_type') == ProjectTypes.tool:
        fp.write('\t\t\t\t<Option type="1" />\n')
    else:
        fp.write('\t\t\t\t<Option type="2" />\n')
    fp.write('\t\t\t\t<Option compiler="ow" />\n')
    fp.write('\t\t\t\t<Option createDefFile="1" />\n')
    fp.write('\t\t\t\t<Compiler>\n')
    fp.write('\t\t\t\t\t<Add option="-ox" />\n')
    fp.write('\t\t\t\t\t<Add option="-ot" />\n')
    fp.write('\t\t\t\t\t<Add option="-wx" />\n')
    fp.write('\t\t\t\t\t<Add option="-fr=$(ERROR_FILE)" />\n')
    fp.write('\t\t\t\t\t<Add option="-fp6" />\n')
    fp.write('\t\t\t\t\t<Add option="-6r" />\n')
    fp.write('\t\t\t\t\t<Add option="-dNDEBUG" />\n')
    fp.write('\t\t\t\t</Compiler>\n')
    fp.write('\t\t\t</Target>\n')

    fp.write('\t\t\t<Environment>\n')
    fp.write(
        '\t\t\t\t<Variable name="ERROR_FILE" value="$(TARGET_OBJECT_DIR)foo.err" />\n')
    fp.write('\t\t\t</Environment>\n')
    fp.write('\t\t</Build>\n')

    #
    # Output the virtual target
    #

    fp.write('\t\t<VirtualTargets>\n')
    fp.write('\t\t\t<Add alias="Everything" targets="')
    for target in solution.project_list[0].configurations:
        fp.write(target.attributes['name'] + ';')
    fp.write('" />\n')
    fp.write('\t\t</VirtualTargets>\n')

    #
    # Output the global compiler settings
    #

    fp.write('\t\t<Compiler>\n')
    fp.write('\t\t\t<Add option="-dGLUT_DISABLE_ATEXIT_HACK" />\n')
    fp.write('\t\t\t<Add option="-dGLUT_NO_LIB_PRAGMA" />\n')
    fp.write('\t\t\t<Add option="-dTARGET_CPU_X86=1" />\n')
    fp.write('\t\t\t<Add option="-dTARGET_OS_WIN32=1" />\n')
    fp.write('\t\t\t<Add option="-dTYPE_BOOL=1" />\n')
    fp.write('\t\t\t<Add option="-dUNICODE" />\n')
    fp.write('\t\t\t<Add option="-d_UNICODE" />\n')
    fp.write('\t\t\t<Add option="-dWIN32_LEAN_AND_MEAN" />\n')

    for dirnameentry in includedirectories:
        fp.write('\t\t\t<Add directory=\'&quot;' + burger.convert_to_linux_slashes(dirnameentry) +
                 '&quot;\' />\n')

    if solution.project_list[0].get_attribute('project_type') != ProjectTypes.library or solution.attributes['name'] != 'burgerlib':
        fp.write(
            '\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/burgerlib&quot;\' />\n')
    fp.write(
        '\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/perforce&quot;\' />\n')
    fp.write('\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/opengl&quot;\' />\n')
    fp.write(
        '\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/directx9&quot;\' />\n')
    fp.write(
        '\t\t\t<Add directory=\'&quot;$(BURGER_SDKS)/windows/windows5&quot;\' />\n')
    fp.write('\t\t</Compiler>\n')

    #
    # Output the list of source files
    #

    filelist = []
    for i in alllists:
        filelist.append(burger.convert_to_linux_slashes(i.relative_pathname))

    filelist = sorted(filelist)

    for i in filelist:
        fp.write('\t\t<Unit filename="' + i + '" />\n')

    #
    # Add the extensions (If any)
    #

    fp.write('\t\t<Extensions>\n')
    fp.write('\t\t\t<code_completion />\n')
    fp.write('\t\t\t<envvars />\n')
    fp.write('\t\t\t<debugger />\n')
    fp.write('\t\t</Extensions>\n')

    #
    # Close the file
    #

    fp.write('\t</Project>\n')
    fp.write('</CodeBlocks_project_file>\n')
    fp.close()
    return 0
