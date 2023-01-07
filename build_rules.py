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

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
from burger import import_py_script, run_command, clean_directories

# If set to True, ``buildme -r``` will not parse directories in this folder.
BUILDME_NO_RECURSE = False

# ``buildme``` will build these files and folders first.
DEPENDENCIES = []

# If set to True, ``cleanme -r``` will not parse directories in this folder.
CLEANME_NO_RECURSE = True

CLEANME_CONTINUE = True

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

    # Call setup.py to create the distribution files.
    run_command(
        ("python", "setup.py", "sdist", "bdist_wheel"),
        working_dir=working_directory)
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

    # Clean up tox, or pylint
    clean_directories(working_directory, "temp")

    # The function exists in setup.py.
    # It can be manually invoked with "setup.py clean"
    setup = import_py_script(os.path.join(working_directory, "setup.py"))
    setup.clean(working_directory)
    return 0


# If called as a command line and not a class, perform the build
if __name__ == "__main__":
    sys.exit(build(os.path.dirname(os.path.abspath(__file__)), "all"))
