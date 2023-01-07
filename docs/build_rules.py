#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Build rules for the makeprojects suite of build tools.

This file is parsed by the cleanme, buildme, rebuildme and makeprojects
command line tools to clean, build and generate project files.

When any of these tools are invoked, this file is loaded and parsed to
determine special rules on how to handle building the code and / or data.
"""

# pylint: disable=unused-argument
# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
from re import compile as re_compile
import pypandoc
from burger import create_folder_if_needed, is_source_newer, \
    clean_directories, clean_files, run_command

# If set to True, ``buildme -r``` will not parse directories in this folder.
BUILDME_NO_RECURSE = True

# ``buildme``` will build these files and folders first.
BUILDME_DEPENDENCIES = []

# If set to True, ``cleanme -r``` will not parse directories in this folder.
CLEANME_NO_RECURSE = True

# ``cleanme`` will clean the listed folders using their rules before cleaning.
# this folder.
CLEANME_DEPENDENCIES = []

# Match *.dot
_DOT_MATCH = re_compile("(?ms).*\\.dot\\Z")

########################################


def build(working_directory, configuration):
    """
    Preprocess READEME.rst

    Doxygen doesn't support the importation of .rst files, and the
    support for .md files doesn't support images that
    also have links. To get around this limitation, this preprocessor
    will use docutils to convert the README.rst into an html file
    which will be directly imported into the Doxygen documentation
    so only one copy of the README is needed.

    On exit, return 0 for no error, or a non zero error code if there was an
    error to report.

    Args:
        working_directory
            Directory this script resides in.

        configuration
            Configuration to build, ``all`` if no configuration was requested.

    Returns:
        None if not implemented, otherwise an integer error code.
    """

    # Copy README.rst to docs/temp/README.html
    # Doxygen may not create the output folder, ensure it exists.

    temp_dir = os.path.join(working_directory, "temp")
    create_folder_if_needed(temp_dir)

    # Needed for dot generated docs
    create_folder_if_needed(os.path.join(temp_dir, "images"))

    # Process all the .dot files
    for item in os.listdir(working_directory):

        # Process the .dot files
        if _DOT_MATCH.match(item):
            # Call dot to create the files
            run_command(
                ("dot", "-Tpng", item, "-otemp{0}images{0}{1}.png".format(
                    os.sep, item[:-4])),
                    working_dir=working_directory)


    # Get the input and output file names
    source = os.path.join(os.path.dirname(working_directory), "README.rst")
    dest = os.path.join(temp_dir, "README.html")

    # Was the file already created and newer than the source?
    if is_source_newer(source, dest):

        # Load pandoc if needed to do the conversion
        pypandoc.ensure_pandoc_installed(delete_installer=True)
        pypandoc.convert_file(source, to="html", outputfile=dest)
    return 0

########################################


def clean(working_directory):
    """
    Delete temporary files.

    This function is called by ``cleanme`` to remove temporary files.

    On exit, return 0 for no error, or a non zero error code if there was an
    error to report.

    Args:
        working_directory
            Directory this script resides in.

    Returns:
        None if not implemented, otherwise an integer error code.
    """

    clean_directories(working_directory, ("temp", "_build"))
    clean_files(working_directory, ".DS_Store")
    return 0


# If called as a command line and not a class, perform the build
if __name__ == "__main__":
    sys.exit(build(os.path.dirname(os.path.abspath(__file__)), "all"))
