#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration file on how to build and clean projects in a specific folder.

This file is parsed by the cleanme, buildme, rebuildme and makeprojects
command line tools to clean, build and generate project files.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import pypandoc
import burger

########################################


def build_readme(working_directory):
    """
    Preprocess READEME.rst

    Doxygen doesn't support the importation of .rst files, and the
    support for .md files doesn't support images that
    also have links. To get around this limitation, this preprocessor
    will use docutils to convert the README.rst into an html file
    which will be directly imported into the Doxygen documentation
    so only one copy of the README is needed.

    Arg:
        working_directory: Directory for this function to build.
    Returns:
        Zero on no error, non-zero on error.
    """

    # Copy README.rst to docs/temp/README.html
    # Doxygen may not create the output folder, ensure it exists.

    temp_dir = os.path.join(working_directory, 'temp')
    burger.create_folder_if_needed(temp_dir)

    # Get the input and output file names
    source = os.path.join(os.path.dirname(working_directory), 'README.rst')
    dest = os.path.join(temp_dir, 'README.html')

    # Was the file already created and newer than the source?
    if burger.is_source_newer(source, dest):

        # Load pandoc if needed to do the conversion
        if hasattr(pypandoc, 'ensure_pandoc_installed'):
            # pylint: disable=E1101
            pypandoc.ensure_pandoc_installed(quiet=True, delete_installer=True)
        else:
            try:
                pypandoc.get_pandoc_path()
            except OSError:
                pypandoc.download_pandoc()
        pypandoc.convert_file(source, to='html', outputfile=dest)
    return 0

########################################


def rules(command, working_directory, root=True):
    """
    Main entry point for build_rules.py.

    When makeprojects, cleanme, or buildme is executed, they will call this
    function to perform the actions required for build customization.

    The parameter working_directory is required, and if it has no default
    parameter, this function will only be called with the folder that this
    file resides in. If there is a default parameter of None, it will be called
    with any folder that it is invoked on. If the default parameter is a
    directory, this function will only be called if that directory is desired.

    The optional parameter of root alerts the tool if subsequent processing of
    other build_rules.py files are needed or if set to have a default parameter
    of True, processing will end once the calls to this rules() function are
    completed.

    Commands are 'build', 'clean', 'prebuild', 'postbuild', 'project',
    'configurations'

    Arg:
        command: Command to execute.
        working_directory: Directory for this function to clean
        root: If set to True, exit cleaning upon completion of this function
    Return:
        Zero on success, non-zero on failure, and a list for 'configurations'

    """

    # Unused arguments
    # pylint: disable=W0613

    if command == 'clean':
        burger.clean_directories(working_directory, ('temp', '_build'))
        burger.clean_files(working_directory, '.DS_Store')
    elif command == 'build':
        return build_readme(working_directory)
    return 0


# If called as a command line and not a class, perform the build
if __name__ == "__main__":
    sys.exit(rules('build', os.path.dirname(os.path.abspath(__file__))))
