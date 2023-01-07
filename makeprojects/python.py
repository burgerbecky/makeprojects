#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module the handles python script execution

Manages, and creates BuildObjects that are tailored for executing python
scripts.

See Also:
    makeprojects.cleanme, makeprojects.buildme

@package makeprojects.python

@var makeprojects.python.BUILD_LIST
Default build_rules.py command list, priority / entrypoint

@var makeprojects.python.CUSTOM_SCRIPTS
Names of custom scripts and their priorities
"""

# pylint: disable=consider-using-f-string
# pylint: disable=super-with-arguments

from __future__ import absolute_import, print_function, unicode_literals

import os
from burger import is_string, run_py_script
from .build_objects import BuildObject, BuildError

BUILD_LIST = (
    (1, "prebuild"),
    (40, "build"),
    (99, "postbuild")
)

# If these scripts are found, call main with a single parameter
# of the directory the script resides in.
CUSTOM_SCRIPTS = (
    (1, "prebuild.py"),
    (40, "custombuild.py"),
    (99, "postbuild.py")
)

########################################


class BuildPythonFile(BuildObject):
    """
    Class to build with python scripts

    When this object is created, it can either open a python script and invoke a
    specific function by name with a single parameter of the working directory,
    or it can be given a callable python object and a {} object that is
    passed to the function using the double asterisk parameter list.

    If function_ref is a string, it's the entry point to the file, if it is
    a callable python object, it's invoked directly.

    Attributes:
        verbose: the verbose flag
        function_ref: Function pointer or name of function
        parms: Parameters for function
    """

    # pylint: disable=too-many-arguments
    def __init__(self, file_name, priority=None, verbose=False,
                 function_ref=None, parms=None):
        """
        Class to execute python code in a script.
        @details
        The ``file_name`` parameter must have the pathname to the python script
        so it can be tracked for debugging. If ``function_ref`` is a string, it
        will be used as the entry point to the python script, otherwise it has
        to be a callable object that accepts the ``parms`` value for the
        parameter list.

        Args:
            file_name: Pathname to the *.py to build
            priority: Priority to build this object
            verbose: True if verbose output
            function_ref: Python function pointer or name
            parms: Parameter list to issue to the function

        Raises:
            ValueError
        """

        super(BuildPythonFile, self).__init__(file_name, priority)

        # Sanity checks
        if not callable(function_ref) and not is_string(function_ref):
            raise ValueError(
                ("function_ref \"{}\" is not either a callable "
                "function or a string ").format(
                    str(function_ref)))

        # Use default parameter list
        if parms is None:
            parms = {}

        self.verbose = verbose
        self.function_ref = function_ref
        self.parms = parms

    ########################################

    def has_python_function(self):
        """
        Return True if there's a callable python function.

        Returns:
            True if there is a callable python function.
        """
        return callable(self.function_ref)

    ########################################

    def create_parm_string(self):
        """
        Merge the command parameters into a single string.

        Returns:
            String of all the parameters. Can be an empty string.
        """

        if not self.parms:
            return ""

        parms = []
        for item in self.parms:
            parms.append("{}=\"{}\"".format(item, self.parms[item]))
        return ",".join(parms)

    ########################################

    def build(self):
        """
        Execute a python script.

        Execute either a python function, or load a python script and invoke
        a specific entry point.

        The function must return an integer error code, with zero being no
        error.

        Returns:
            BuildError object
        """

        # Is this a file? If so, call the function "main(working_directory)"
        if not self.has_python_function():

            # Show debug info
            if self.verbose:
                print(
                    "Invoking {}(\"{}\") in file {}".format(
                        self.function_ref,
                        os.path.dirname(
                            self.file_name),
                        self.file_name))

            # Perform the call
            error = run_py_script(
                self.file_name,
                self.function_ref,
                os.path.dirname(
                    self.file_name))
        else:

            # It's a function, output what is being called.
            if self.verbose:
                print(
                    "Calling {}({}) in {}".format(
                        self.function_ref.__name__,
                        self.create_parm_string(),
                        self.file_name))

            # Call the functions with the parameter list
            error = self.function_ref(**self.parms)
        return BuildError(error, self.file_name)

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
        return self.build()

    ########################################

    def __repr__(self):
        """
        Convert the object into a string.

        Returns:
            A full string.
        """

        result = (
            "{} for file \"{}\" with priority {}").format(
                type(self).__name__,
                self.file_name,
                self.priority)

        # If callable, use the parameter list
        if callable(self.function_ref):
            result += ", function {}".format(self.function_ref.__name__)
            if self.parms:
                result += "({})".format(self.create_parm_string())
            else:
                result += "()"
        else:
            # If a script, show the actual passed parameter
            result += ", function {}(\"{}\")".format(self.function_ref,
                                        os.path.dirname(self.file_name))

        return result

    ########################################

    def __str__(self):
        """
        Convert the object into a string.

        Returns:
            A full string.
        """

        return self.__repr__()

########################################


def match(file_name):
    """
    Check if the filename is a type that this module supports

    Args:
        file_name: Filename to match
    Returns:
        False if not a match, True if supported
    """

    # Get the script name
    base_name = os.path.basename(file_name)

    # Ignore case
    base_name_lower = base_name.lower()

    # Match?
    for item in CUSTOM_SCRIPTS:
        if base_name_lower == item[1]:
            return True
    return False

########################################


def create_simple_script_object(file_name, entry=None, verbose=False):
    """
    Create a BuildPythonFile for a script with a single entry point.

    Given a filename and an name to an entry point, create and return
    a single BuildPythonFile entry in a list. The entry point must accept
    a single parameter of the directory that the script resides in and
    the function returns an integer error code or None.

    If entry is None, the function will assume the entry point is named
    ``main``.

    Args:
        file_name: Pathname to the *.py to build
        entry: Name of the function to call in the python file
        verbose: True if verbose output

    Returns:
        List of a single BuildPythonFile object, can be empty
    """

    if entry is None:
        entry = "main"

    base_name = os.path.basename(file_name)
    base_name_lower = base_name.lower()
    for item in CUSTOM_SCRIPTS:
        if base_name_lower == item[1]:
            return [
                BuildPythonFile(file_name, priority=item[0],
                     verbose=verbose, function_ref=entry)]
    return []


########################################

def create_build_rules_objects(
        file_name, build_rules, parms=None, verbose=False):
    """
    Create BuildObjects from a loaded build_rules.py file.

    After loading a build_rules.py module, this function will check for all
    entry points used by ``buildme`` such as ``prebuild`` and ``postbuild`` and
    it will create BuildPythonFile objects for every entry point found.

    If there are no entry points in the module, this function will return an
    empty list.

    Args:
        file_name: Name of the loaded file
        build_rules: Loaded python module, usually build_rules.py
        parms: Dictionary of parameters for the function call
        verbose: True if verbose output is required

    Returns:
        List of BuildPythonFile objects, can be empty
    """

    projects = []
    for item in BUILD_LIST:

        # Check if the entry point exists
        function_ref = getattr(build_rules, item[1], None)
        if function_ref:

            # Add a BuildPythonFile object
            projects.append(
                BuildPythonFile(
                    file_name,
                    priority=item[0],
                    verbose=verbose,
                    function_ref=function_ref,
                    parms=parms))
    return projects

########################################


def create_clean_rules_objects(
        file_name, build_rules, parms=None, verbose=False):
    """
    Create BuildObjects from a loaded build_rules.py file.

    After loading a build_rules.py module, this function will check for the
    entry point used by ``cleanme`` ``clean`` and it will create a
    BuildPythonFile objects for the entry point found.

    If there are no entry point in the module, this function will return an
    empty list.

    Args:
        file_name: Name of the loaded file
        build_rules: Loaded python module, usually build_rules.py
        parms: Dictionary of parameters for the function call
        verbose: True if verbose output is required

    Returns:
        List of BuildPythonFile objects, can be empty
    """

    projects = []

    # Check if the entry point exists
    function_ref = getattr(build_rules, "clean", None)
    if function_ref:
        if not callable(function_ref):
            print(
                ("Function clean in file {} "
                "is not a callable function").format(
                    build_rules.__file__))
        else:
            # Add a BuildPythonFile object
            projects.append(
                BuildPythonFile(
                    file_name,
                    priority=10,
                    verbose=verbose,
                    function_ref=function_ref,
                    parms=parms))
    return projects
