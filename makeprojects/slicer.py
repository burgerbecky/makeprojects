#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that handles slicer script files.

Build and clean slicer data

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

    def __init__(self, file_name, priority=None, verbose=False):
        """
        Class to handle .slicerscript files

        Args:
            file_name: Pathname to the *.slicerscript to build
            priority: Priority to build this object
            verbose: True if verbose output
        """

        # pylint: disable=super-with-arguments

        if priority is None:
            # Make sure this number is lower than makerez, because makerez
            # usually needs the output of this tool as input
            priority = 20

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


def match(filename):
    """
    Check if the filename is a type that this module supports

    Slicer scripts end with .slicerscript.

    Args:
        filename: Filename to match
    Returns:
        False if not a match, True if supported
    """

    return _SLICERFILE_MATCH.match(filename)

########################################


def create_build_object(file_name, priority=None,
                 configurations=None, verbose=False):
    """
    Return an array of BuildSlicerFile build objects

    Given a filename to a slicer script, create a BuildObject that will
    invoke the tool and slicer the art as needed.

    Args:
        file_name: Pathname to the *.slicerscript to build
        priority: Priority to build this object
        configurations: Configuration list to build (Not used)
        verbose: True if verbose output
    """

    # pylint: disable=unused-argument

    return [BuildSlicerFile(file_name, priority, verbose=verbose)]
