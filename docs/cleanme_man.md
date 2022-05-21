# 🧹 Cleanme

``cleanme`` is a tool to quickly and easily remove all temporary and generated files to force a full rebuild of a project on the next time a build is invoked. The tool has the ability to clean all projects in a single directory, or recursively through subdirectories with the ``-r`` parameter.

The tool has the ability to parse all project files to determine which version of Visual Studio, XCode, etc. to invoke so there is no needed to determine what build system to use, since it has the ability to determine the proper IDE/build tool to invoke. Custom clean rules are defined in the file ``build_rules.py`` <*see below*>

## Usage

Navigate to a directory of interest or use a full directory path and run ``cleanme``. By default, it checks the folder for a ``build_rules.py`` file for override rules, and it will either use the rules found to clean the projects in the directory, and then it will scan the directory for known project files and invoke the appropriate clean system to remove the files. If a configuration is passed a parameter, only that configuration will be cleaned.

"``cleanme`` Release", clean only the "Release" configuration of all project files.

"``cleanme``", clean all configurations of the project files.

"``cleanme`` helloworld.sln", clean all configurations in helloworld.sln.

## Directory traversal

When the command line option ``-r`` is used, ``cleanme`` will traverse all folders recursively and process all folders found. Due to the nature of cleaning, for performance reasons, the directories will be processed under the current directory first, and then it will process all child directories secondly. This is the reverse order of ``buildme`` because in most cases, directories will be deleted when being cleaned, which will not exist when the directory is scanned for subdirectories to prevent processing directories that were removed.

Example:

If ``build_rules.py`` deletes ``temp``, then if ``cleanme`` is executed at the root with ``-r``, ``build_rules.py`` will be executed at the root which will remove the folder ``temp``, and then it will process the remaining folders ``source`` and ``data``, skipping over temp because it doesn't exist.

In this example, the folders ``.``, ``data``, and ``source`` will be processed but ``temp`` will not because it and its contents are removed.

![Cleanme directory traversal tree](cleanme_dir.png "Cleanme directory traversal tree")

``` bash
.
+-- .gitignore
+-- build_rules.py
+-- data
|   +--- build_rules.py
|   +--- foo.png
+-- temp
|   +--- foo.obj
+-- source
|   +--- foo.cpp
```

## build_rules.py

A build_rules file contains both static variables and a function to process a folder for cleaning. The static variables are checked first to guide the behavior of the ``cleanme`` tool, and if present, the function ``clean(working_directory)`` is called for custom clean rules. The function can return an error code which is returned to the command shell that invoked ``cleanme``. Returning ``None`` acts if no error occured.

Full documentation on the operation of [``build_rules.py`` is here](build_rules_man.md).

## Visual Studio

If the project file ends with .sln, it's assumed to be a Visual Studio project file.

If the host is Windows, MSYS2, Cygwin, or Windows Subsystem for Linux, it will clean Visual Studio projects if the appropriate version of Visual Studio was installed.

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
- Visual Studio 2022

## XCode

If the folder ends with .xcodeproj and contains the file project.pbxproj, it's assumed to be Apple XCode. This type of project can only be built on macOS hosts.

## Watcom

If the file ends with .wmk, it's assumed to be a Watcom WMAKE file. It can be built on Linux and Windows hosts. It will invoke the "clean" target.

## Codeblocks

If the file ends with .cdp, it's assumed to be a CodeBlocks project file. It's invoked on Windows and Linux hosts.

## CodeWarrior

If the file ends with .mcp, it's assumed to be a Metrowerks / NXP CodeWarrior file. It's invoked on a Windows or macOS hosts.

## Linux Make

If the file is makefile, it's assumed to be a Linux make file and is invoked only on Linux hosts. It will invoke the "clean" target.

## Ninja

If the file ends with .ninja, it's assumed to be a ninja file and is invoked on all hosts. It will invoke the "clean" target.

## Credits

``cleanme`` is the insane creation of Rebecca Ann Heineman.

If bugs are found, please send all information on how to recreate the bug to [becky@burgerbecky.com](mailto:becky@burgerbecky.com)
