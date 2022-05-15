#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Namespace for the makeprojects modules.

@package makeprojects.modules

Each module controls the building, cleaning and generation of specific IDEs
build tools.
"""

from __future__ import absolute_import, print_function, unicode_literals

# pylint: disable=useless-object-inheritance
# pylint: disable=unused-argument
# pylint: disable=no-self-use
# pylint: disable=consider-using-f-string

########################################


class Root(object):
    """
    Makeprojects root build module object

    Every build/clean/generation object derives from this object
    to allow the command line functions to be extended for all
    supported IDEs and tools.

    Attributes:
        name: Module's name
        priority: Module's priority for invocation
    """

    def __init__(self, name, priority):
        """
        Initialize the root build object.

        Args:
            name: Name of this module
            priority: Integer priority from 0-100
        """

        self.name = name
        self.priority = priority

    ########################################

    def __repr__(self):
        """
        Prints the type of object this is.

        Returns:
            String object with user readable name of the object
        """

        return 'Build module for {} with priority {}'.format(
            self.name, self.priority)

    def __str__(self):
        """
        Prints the type of object this is.

        Returns:
            String object with user readable name of the object
        """
        return self.__repr__()

    ########################################

    def build(self, working_directory, file_name=None, configuration=None):
        """
        Build code or data.

        When this module is called for building, the file that is to be built
        is passed in and the module will invoke the tool with the appropriate
        command line parameters to build using an optional configuration.

        On exit, return 0 for no error, or a non zero error code if there was an
        error to report. None if not implemented.

        Args:
            working_directory: Directory this script resides in.
            file_name: Project file to build.
            configuration: Configuration build, ``all`` if no
                configuration was requested.

        Returns:
            None if not implemented, otherwise an integer error code.
        """

        return None

    ########################################

    def clean(self, working_directory, file_name=None):
        """
        Delete temporary files.

        This function is called by ``cleanme`` to remove temporary files.

        On exit, return 0 for no error, or a non zero error code if there was an
        error to report. None if not implemented or not applicable.

        Args:
            working_directory: Directory this script resides in.
            file_name: Project file to invoke clean

        Returns:
            None if not implemented, otherwise an integer error code.
        """
        return None
