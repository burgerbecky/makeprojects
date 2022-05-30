#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module handles Rezfile

Build and clean rezfile data

See Also:
    makeprojects.cleanme, makeprojects.buildme

@package makeprojects.rezfile

@var makeprojects.rezfile._REZFILE_MATCH
Regex for matching files with *.rezscript
"""

from __future__ import absolute_import, print_function, unicode_literals

from re import compile as re_compile
from .core import BuildObject

_REZFILE_MATCH = re_compile('(?is).*\\.rezscript\\Z')

#######################################


class BuildRezFile(BuildObject):
    """
    Class to build rez files

    Attributes:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority=25,
                 configuration=None, verbose=False):
        """
        Class to handle .rezfile.

        Args:
            file_name: Pathname to the *.rezscript to build
            priority: Priority to build this object
            configuration: Configuration to build
            verbose: True if verbose output
        """

        # pylint: disable=super-with-arguments

        super(BuildRezFile, self).__init__(
            file_name,
            priority,
            configuration=configuration)
        self.verbose = verbose

    def build(self):
        """
        Build a rezfile using ``makerez``.

        Execute the program ``makerez`` to build the script.

        Returns:
            BuildError object
        """

        # Create the build command
        cmd = ['makerez', self.file_name]
        if self.verbose:
            # Have makerez be verbose
            cmd.insert(1, '-v')
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

    return _REZFILE_MATCH.match(filename)

########################################


def create_build_object(file_name, priority=25,
                 configurations=None, verbose=False):
    """
    Return an array of BuildRezFile build objects

    Args:
        file_name: Pathname to the *.rezscript to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output
    """

    # pylint: disable=unused-argument

    return [BuildRezFile(file_name, priority, verbose=verbose)]
