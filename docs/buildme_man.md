# Buildme

``buildme`` is a build system launcher that by using a single command, multiple build systems could be launched using a singluar command line. The tool has the ability to build all projects in a single directory, or even recursively through subdirectories with the ``-r`` parameter.

This is the launcher for the ``makeprojects`` project creation system and the ``build_rules.py`` file.

The tool has the ability to parse all project files to determine which version of Visual Studio, XCode, etc. to invoke so there is no needed to determine what build system to use, since it has the ability to determine the proper IDE/build tool to invoke.

``buildme`` also handles most video game console build systems automatically. If any of these are missing, the default behavior will be used.

## build_rules.py

A ``build_rules.py`` file can control the behavior of buildme by listing dependencies and custom build rules.

### BUILDME_DEPENDENCIES

Set BUILDME_DEPENDENCIES with either a single string of a folder or file that must be built first. Also, a list of files or folders can be set and they will be built in the order of their position in the list. The default is no dependencies.

### BUILDME_NO_RECURSE

Set BUILDME_NO_RECURSE to True if all subdirectories below this folder are not to be processed due to them not having any build project files. This defaults to ``False``, but set this to ``True`` to prevent parsing folders that don't need processing.

### prebuild(working_directory, configuration)

If this function exists, it will be called **FIRST** with the directory that the build_rules.py file exists in and the configuration requested to build. Normally the configuration is set to "all", but can be ignored if it isn't relevant to the custom build rules.

### build(working_directory, configuration)

If this function exists, it will be called with the directory that the build_rules.py file exists in and the configuration requested to build. Normally the configuration is set to "all", but can be ignored if it isn't relevant to the custom build rules.

### postbuild(working_directory, configuration)

If this function exists, it will be called **LAST** with the directory that the build_rules.py file exists in and the configuration requested to build. Normally the configuration is set to "all", but can be ignored if it isn't relevant to the custom build rules.

## Usage

Navigate to a directory of interest or use a full directory path and run ``buildme``. By default, it check the folder for a ``build_rules.py`` file for override rules, and it will either use the rules found to build the projects in the directory, and then it will scan the directory for known project files and invoke the appropriate build system to build the project. If a configuration is passed a parameter, only that configuration will be built in all projects being compiled.

"``buildme`` Release", build only the "Release" configuration of all project files.

"``buildme``", build all configurations of the project files.

"``buildme`` helloworld.sln", build all configurations in helloworld.sln.

## Visual Studio

If the project file ends with .sln, it's assumed to be a Visual Studio project file.

If the host is Windows, MSYS2, Cygwin, or Windows Subsystem for Linux, it will build Visual Studio projects if the appropriate version of Visual Studio was installed.

These are the supported versions of Visual Studio:

- Visual Studio 2003 .NET
- Visual Studio 2005
- Visual Studio 2008
- Visual Studio 2010
- Visual Studio 2012
- Visual Studio 2013
- Visual Studio 2015
- Visual Studio 2017
- Visual Studio 2019

These are the supported Visual Studio plug ins.

- Win32 (Windows 32 bit x86)
- x64 (Windows 64 bit x64)
- ARM (Windows 32 bit ARM)
- ARM64 (Windows 64 bit ARM)
- Xbox (Xbox classic)
- Xbox 360
- Durango (Xbox ONE)
- PS3
- PS4
- PSVita
- NX32 (Switch 32 bit)
- NX64 (Switch 64 bit)
- Tegra-Android (nVidia Shield)

## XCode

If the folder ends with .xcodeproj and contains the file project.pbxproj, it's assumed to be Apple XCode. This type of project can only be built on macOS hosts.

## Watcom

If the file ends with .wmk, it's assumed to be a Watcom WMAKE file. It can be built on Linux and Windows hosts.

## Codeblocks

If the file ends with .cdp, it's assumed to be a CodeBlocks project file. It's invoked on Windows and Linux hosts.

## CodeWarrior

If the file ends with .mcp, it's assumed to be a Metrowerks / NXP CodeWarrior file. It's invoked on a Windows or macOS hosts.

## Linux Make

If the file is makefile, it's assumed to be a Linux make file and is invoked only on Linux hosts.

## Ninja

If the file ends with .ninja, it's assumed to be a ninja file and is invoked on all hosts.

## Credits

``buildme`` is the insane creation of Rebecca Ann Heineman.

If bugs are found, please send all information on how to recreate the bug to [becky@burgerbecky.com](mailto:becky@burgerbecky.com)
