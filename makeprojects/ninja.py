#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 1995-2022 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

"""
Sub file for makeprojects.
Handler for Ninja projects

@package makeprojects.ninja
This module contains classes needed to generate
project files intended for use by ninja
"""

# pylint: disable=consider-using-f-string
# pylint: disable=useless-object-inheritance
# pylint: disable=super-with-arguments

from __future__ import absolute_import, print_function, unicode_literals

from re import compile as re_compile

from .core import BuildObject

_NINJAFILE_MATCH = re_compile('(?is).*\\.ninja\\Z')


########################################


class BuildNinjaFile(BuildObject):
    """
    Class to build Ninja make files

    Attributes:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority, configuration, verbose=False):
        """
        Class to handle Ninja make files

        Args:
            file_name: Pathname to the makefile to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
        """

        super(BuildNinjaFile, self).__init__(
            file_name, priority, configuration=configuration)
        self.verbose = verbose

    def build(self):
        """
        Build build.ninja using ``ninja``.

        The default target built is ``all``.

        Returns:
            List of BuildError objects
        """

        # Build the requested target configuration
        cmd = ['ninja', '-f', self.file_name, self.configuration]

        if self.verbose:
            print(' '.join(cmd))

        return self.run_command(cmd, self.verbose)

########################################


def match(filename):
    """
    Check if the filename is a type that this module supports

    Args:
        filename: Filename to match
    Returns:
        False if not a match, True if supported
    """

    return _NINJAFILE_MATCH.match(filename)

########################################


def create_build_object(file_name, priority=50,
                 configurations=None, verbose=False):
    """
    Create BuildNinjaFile build records for every desired configuration

    Args:
        file_name: Full pathname to the make file
        args: parser argument list
    Returns:
        list of BuildNinjaFile classes
    """

    if not configurations:
        return [BuildNinjaFile(file_name, priority, 'all', verbose)]

    results = []
    for configuration in configurations:
        results.append(
            BuildNinjaFile(
                file_name,
                priority,
                configuration,
                verbose))
    return results
