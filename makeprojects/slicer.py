#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module handles Rezfile

Build and clean rezfile data

See Also:
    makeprojects.cleanme, makeprojects.buildme

@package makeprojects.slicer

@var makeprojects.buildme._SLICERFILE_MATCH
Regex for matching files with *.slicerscript
"""

from __future__ import absolute_import, print_function, unicode_literals
from re import compile as re_compile
from .core import BuildObject

_SLICERFILE_MATCH = re_compile('(?is).*\\.slicerscript\\Z')

#######################################


class BuildSlicerFile(BuildObject):
    """
    Class to build slicer files

    Attributes:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority=20, verbose=False):
        """
        Class to handle .slicerscript files

        Args:
            file_name: Pathname to the *.slicerscript to build
            priority: Priority to build this object
            verbose: True if verbose output
        """

        # pylint: disable=super-with-arguments

        super(BuildSlicerFile, self).__init__(file_name, priority)
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

    def clean(self):
        """
        Delete temporary files.

        This function is called by ``cleanme`` to remove temporary files.

        On exit, return 0 for no error, or a non zero error code if there was an
        error to report. None if not implemented or not applicable.

        Returns:
            None if not implemented, otherwise an integer error code.
        """
        return None

########################################


def match(filename):
    """
    Check if the filename is a type that this module supports

    Args:
        filename: Filename to match
    Returns:
        False if not a match, True if supported
    """

    return _SLICERFILE_MATCH.match(filename)

########################################


def create_build_object(file_name, priority=20,
                 configurations=None, verbose=False):
    """
    Return an array of BuildSlicerFile build objects

    Args:
        file_name: Pathname to the *.rezscript to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output
    """

    # pylint: disable=unused-argument

    return [BuildSlicerFile(file_name, priority, verbose=verbose)]
