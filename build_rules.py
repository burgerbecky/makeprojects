#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Build rules for the makeprojects suite of build tools.

This file is parsed by the cleanme, buildme, rebuildme and makeprojects
command line tools to clean, build and generate project files.

When any of these tools are invoked, this file is loaded and parsed to
determine special rules on how to handle building the code and / or data.

python -m twine upload --verbose dist/*

cd docs
sphinx-build -M html . temp\build

"""

# pylint: disable=unused-argument

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
from burger import clean_directories, run_command, delete_file, \
    delete_directory, clean_files, lock_files, unlock_files, \
    create_setup_py

# Buildme and Cleanme are invoked from another folder
# so Python will pull in the version of makeprojects that's
# already installed. To force it to use the one in this
# folder, manually purge it first, then insert the current
# working directory into the search path, then reload
# with the import call

# Remove old copy of makeprojects
if "makeprojects" in sys.modules:
    del sys.modules["makeprojects"]

# Update the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import this copy of makeprojects
# pylint: disable=wrong-import-position
from makeprojects import __version__

# If set to True, ``buildme -r``` will not parse directories in this folder.
BUILDME_NO_RECURSE = False

# If set to True, ``cleanme -r``` will not parse directories in this folder.
CLEANME_NO_RECURSE = True

# Directories to clean
CLEAN_DIR_LIST = [
    "makeprojects.egg-info",
    "dist",
    "build",
    "temp",
    ".pytest_cache",
    ".tox",
    ".vscode"
]

# Recurse these directories clean
CLEAN_DIR_RECURSE_LIST = (
    "temp",
    "__pycache__",
    "_build"
)

# Delete any files with these extensions
CLEAN_EXTENSION_LIST = (
    "*.pyc",
    "*.pyo"
)

########################################


def build(working_directory, configuration):
    """
    Build the module so it's ready for upload to Pypi with Twine.

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

    # Create setup.py for Python 2.7 distribution
    input_file = os.path.join(working_directory, "pyproject.toml")
    output_file = os.path.join(working_directory, "setup.py")
    create_setup_py(input_file, output_file)

    # Unlock the files to handle Perforce locking
    lock_list = unlock_files(working_directory) + \
        unlock_files(os.path.join(working_directory, "makeprojects"))

    try:
        # Use "build" from python to build everything
        run_command(
            ("python", "-m", "build"),
            working_dir=working_directory)

    # If any files were unlocked, relock them
    finally:
        lock_files(lock_list)

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

    # Delete all folders, including read only files
    for item in CLEAN_DIR_LIST:
        delete_directory(os.path.join(working_directory, item))

    # Get rid of extra binaries
    delete_file(os.path.join(working_directory, "setup.py"))

    clean_directories(
        working_directory,
        CLEAN_DIR_RECURSE_LIST,
        recursive=True)

    # Delete all *.pyc and *.pyo files
    clean_files(
        working_directory,
        name_list=CLEAN_EXTENSION_LIST,
        recursive=True,
        delete_read_only=True)

    return 0


# If called as a command line and not a class, perform the build
if __name__ == "__main__":
    sys.exit(build(os.path.dirname(os.path.abspath(__file__)), "all"))
