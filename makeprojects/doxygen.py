#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module handles doxygen

Build and clean doxygen data

See Also:
    makeprojects.cleanme, makeprojects.buildme

@package makeprojects.doxygen
"""

# pylint: disable=consider-using-f-string
# pylint: disable=super-with-arguments

from __future__ import absolute_import, print_function, unicode_literals

import os

from burger import load_text_file, delete_file, where_is_doxygen, \
    save_text_file, create_folder_if_needed, get_windows_host_type, run_command
from .build_objects import BuildObject, BuildError

########################################


class BuildDoxygenFile(BuildObject):
    """
    Class to build doxygen files

    Attributes:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority=90, verbose=False):
        """
        Class to handle Doxyfile files

        Args:
            file_name: Pathname to the Doxyfile to build
            priority: Priority to build this object
            verbose: True if verbose output
        """

        super(BuildDoxygenFile, self).__init__(file_name, priority)
        self.verbose = verbose

    def build(self):
        """
        Build documentation using Doxygen.

        Execute the program ``doxygen`` to create documentation for the
        project building built.

        If the input file is found to have CR/LF line endings on a macOS
        or Linux platform, the file will have the CRs stripped before
        being passed to Doxygen to get around a bug in Doxygen where
        the macOS/Linux versions require LF only line endings.

        All Doxygen errors will be captured and stored in a file called
        temp/doxygenerrors.txt. If there were no errors, this file
        will be deleted if it exists.

        Returns:
            BuildError object
        """

        # Is Doxygen installed?
        doxygenpath = where_is_doxygen(verbose=self.verbose)
        if doxygenpath is None:
            msg = '{} requires Doxygen to be installed to build!'.format(
                self.file_name)
            return BuildError(10, self.file_name, msg=msg)

        # Determine the working directory
        doxyfile_dir = os.path.dirname(self.file_name)

        # Make the output folder for errors (If needed)
        temp_dir = os.path.join(doxyfile_dir, 'temp')
        create_folder_if_needed(temp_dir)

        # The macOS/Linux version will die if the text file isn't Linux
        # format, copy the config file with the proper line feeds
        if get_windows_host_type() is False:
            doxyfile_data = load_text_file(self.file_name)
            temp_doxyfile = self.file_name + '.tmp'
            save_text_file(temp_doxyfile, doxyfile_data, line_feed='\n')
        else:
            temp_doxyfile = self.file_name

        # Create the build command
        cmd = [doxygenpath, temp_doxyfile]
        if self.verbose:
            print(' '.join(cmd))

        # Capture the error output
        stderr = run_command(cmd, working_dir=doxyfile_dir,
                             quiet=not self.verbose, capture_stderr=True)[2]

        # If there was a temp doxyfile, get rid of it.
        if temp_doxyfile != self.file_name:
            delete_file(temp_doxyfile)

        # Location of the log file
        log_filename = os.path.join(temp_dir, 'doxygenerrors.txt')

        # If the error log has something, save it.
        if stderr:
            save_text_file(log_filename, stderr.splitlines())
            msg = 'Errors stored in {}'.format(log_filename)
            return BuildError(10, self.file_name, msg=msg)

        # Make sure it's gone since there's no errors
        delete_file(log_filename)
        return BuildError(0, self.file_name)

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
        return BuildError(0, self.file_name,
                          msg="Doxygen doesn't support cleaning")

########################################


def match(filename):
    """
    Check if the filename is a type that this module supports

    Args:
        filename: Filename to match
    Returns:
        False if not a match, True if supported
    """

    base_name = os.path.basename(filename)
    base_name_lower = base_name.lower()
    return base_name_lower == 'doxyfile'

########################################


def create_build_object(file_name, priority=90,
                 configurations=None, verbose=False):
    """
    Return an array of BuildDoxygenFile build objects

    Args:
        file_name: Pathname to the Doxyfile to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output
    """

    # pylint: disable=unused-argument

    return [BuildDoxygenFile(file_name, priority, verbose=verbose)]

########################################


def create_clean_object(file_name, priority=90,
                 configurations=None, verbose=False):
    """
    Return an array of BuildDoxygenFile build objects

    Args:
        file_name: Pathname to the Doxyfile to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output
    """

    # pylint: disable=unused-argument

    return [BuildDoxygenFile(file_name, priority, verbose=verbose)]
