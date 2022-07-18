#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeproject cleanme

Copyright 2013-2022 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

# pylint: disable=wrong-import-position

import sys
import unittest
import os
import tempfile
import shutil
from burger import save_text_file, delete_file, Interceptstdout

# Insert the location of makeprojects at the begining so it's the first
# to be processed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import makeprojects

# Line to import the burger library
_IMPORT_BURGER = "import burger"

# Entry point for clean
_DEF_CLEAN = "def clean(working_directory):"

# Return no error
_RETURN_ZERO = "\treturn 0"

# Return error
_RETURN_ONE = "\treturn 1"

# Return None
_RETURN_NONE = "\treturn None"

# Garbage string
_ABC = (
    "abc",
)

########################################


class TestCleanme(unittest.TestCase):
    """
    Test cleanme
    """


########################################

    def setUp(self):
        """
        Handle temporary directory
        """
        self.saved_cwd = os.getcwd()
        self.tmpdir = os.path.realpath(tempfile.mkdtemp())
        # Make sure anything left behind is removed
        self.addCleanup(shutil.rmtree, self.tmpdir)


########################################

    def tearDown(self):
        """
        Restore directory
        """

        # Restore the working directory, if the test did not.
        os.chdir(self.saved_cwd)


########################################

    @staticmethod
    def mkdir(path, *paths):
        """
        Create a directory and return the full pathname.
        """

        # Pass the arguments straight to os.path.join()
        result = os.path.join(path, *paths)

        # Make the directory
        os.mkdir(result)

        # Return the full pathname
        return result

########################################

    @staticmethod
    def save_text_file(path, *paths):
        """
        Create a directory and return the full pathname.
        """

        # Pass the arguments straight to os.path.join()
        result = os.path.join(path, *paths)

        # Write out a text file with a single dummy line
        save_text_file(result, _ABC)

        # Return the full pathname
        return result

########################################

    def test_cleanme(self):
        """
        Test to see if cleanme loads build_rules.py.
        """

        # The script will delete temp and bin but leave source alone
        # If this did not occur, the script did not execute

        # Create some temp folders
        temp_dir = self.mkdir(self.tmpdir, "temp")
        bin_dir = self.mkdir(self.tmpdir, "bin")

        # Create a folder that should not be deleted
        source_dir = self.mkdir(self.tmpdir, "source")

        # Write out the build_rules.py file
        build_rules_py = os.path.join(self.tmpdir, "build_rules.py")

        # First test is to check if clean() is callable
        save_text_file(build_rules_py, [
            "clean = \"clean\""]
        )
        # Make sure it was written
        self.assertTrue(os.path.isfile(build_rules_py))

        # Call cleanme using the directory with the build_rules.py file
        with Interceptstdout() as output:
            makeprojects.clean(self.tmpdir)
        self.assertTrue("not a callable function" in output[0])

        # Perform a test of the clean() function
        save_text_file(build_rules_py, [
            _IMPORT_BURGER,
            _DEF_CLEAN,
            ("\tburger.clean_directories(working_directory, "
            "(\"temp\", \"bin\"))"),
            _RETURN_NONE]
        )
        # Make sure it was written
        self.assertTrue(os.path.isfile(build_rules_py))

        # Call cleanme using the directory with the build_rules.py file
        makeprojects.clean(self.tmpdir)

        # temp and bin should disappear, but not the others
        self.assertFalse(os.path.isdir(temp_dir))
        self.assertFalse(os.path.isdir(bin_dir))
        self.assertTrue(os.path.isdir(source_dir))

########################################

    def test_cleanme_generic(self):
        """
        Test to see if cleanme handles CLEANME_GENERIC.
        """

        # Create some temp folders
        a_dir = self.mkdir(self.tmpdir, "a")

        # Write out the test files
        a_foo_txt = self.save_text_file(a_dir, "foo.txt")
        a_foo_cpp = self.save_text_file(a_dir, "foo.cpp")

        # Write out the build_rules.py files
        build_rules = os.path.join(self.tmpdir, "build_rules.py")

        save_text_file(build_rules, [
            "CLEANME_GENERIC = True",
            _IMPORT_BURGER,
            _DEF_CLEAN,
            "\tburger.clean_files(working_directory, \"*.txt\")",
            _RETURN_NONE]
        )

        # "a" doesn't have a build_rules.py file, so it should
        # check the parent folder
        makeprojects.clean(a_dir)

        # Check if foo.txt is missing but the .cpp is fine
        self.assertFalse(os.path.isfile(a_foo_txt))
        self.assertTrue(os.path.isfile(a_foo_cpp))

        # Try again, but without the generic flag
        # If called, force an exception
        a_foo_txt = self.save_text_file(a_dir, "foo.txt")
        save_text_file(build_rules, [
            'CLEANME_GENERIC = False',
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\traise RuntimeError("CLEANME_GENERIC = False not handled")',
            _RETURN_NONE]
        )
        makeprojects.clean(a_dir)

        # Test the default state
        save_text_file(build_rules, [
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\traise RuntimeError("CLEANME_GENERIC missing not handled")',
            _RETURN_NONE]
        )
        makeprojects.clean(a_dir)

########################################

    def test_cleanme_continue(self):
        """
        Test to see if cleanme handles CLEANME_CONTINUE.
        """

        # Create some temp folders
        a_dir = self.mkdir(self.tmpdir, 'a')

        # Write out the test files
        foo_txt = self.save_text_file(self.tmpdir, 'foo.txt')
        foo_cpp = self.save_text_file(self.tmpdir, 'foo.cpp')
        a_foo_txt = self.save_text_file(a_dir, 'foo.txt')
        a_foo_cpp = self.save_text_file(a_dir, 'foo.cpp')

        # Write out the build_rules.py files
        build_rules = os.path.join(self.tmpdir, 'build_rules.py')
        a_build_rules = os.path.join(a_dir, 'build_rules.py')

        # Test CLEANME_CONTINUE = False
        save_text_file(build_rules, [
            'CLEANME_GENERIC = True',
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\traise RuntimeError("CLEANME_CONTINUE False not handled")',
            _RETURN_NONE]
        )

        save_text_file(a_build_rules, [
            "CLEANME_CONTINUE = False",
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.cpp")',
            _RETURN_NONE]
        )
        makeprojects.clean(a_dir)
        self.assertTrue(os.path.isfile(foo_txt))
        self.assertTrue(os.path.isfile(foo_cpp))
        self.assertTrue(os.path.isfile(a_foo_txt))
        self.assertFalse(os.path.isfile(a_foo_cpp))

        # Test CLEANME_GENERIC = True / CLEANME_CONTINUE = True
        # Reset
        a_foo_cpp = self.save_text_file(a_dir, 'foo.cpp')

        save_text_file(build_rules, [
            "CLEANME_GENERIC = True",
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.txt")',
            _RETURN_NONE]
        )

        save_text_file(a_build_rules, [
            "CLEANME_CONTINUE = True",
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.cpp")',
            _RETURN_NONE]
        )

        makeprojects.clean(a_dir)

        # "a" should delete *.txt and tmp should delete *.cpp
        self.assertTrue(os.path.isfile(foo_txt))
        self.assertTrue(os.path.isfile(foo_cpp))
        self.assertFalse(os.path.isfile(a_foo_txt))
        self.assertFalse(os.path.isfile(a_foo_cpp))

        # Test CLEANME_CONTINUE = not present
        # Reset
        a_foo_txt = self.save_text_file(a_dir, "foo.txt")
        a_foo_cpp = self.save_text_file(a_dir, "foo.cpp")
        save_text_file(build_rules, [
            "CLEANME_GENERIC = True",
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\traise RuntimeError("CLEANME_CONTINUE not present")',
            _RETURN_NONE]
        )

        save_text_file(a_build_rules, [
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.cpp")',
            _RETURN_NONE]
        )
        makeprojects.clean(a_dir)
        self.assertTrue(os.path.isfile(foo_txt))
        self.assertTrue(os.path.isfile(foo_cpp))
        self.assertTrue(os.path.isfile(a_foo_txt))
        self.assertFalse(os.path.isfile(a_foo_cpp))

        # Test for return value abort
        save_text_file(build_rules, [
            "CLEANME_GENERIC = True",
            _DEF_CLEAN,
            "\traise RuntimeError(\"RETURN 0 didn't abort clean()\")",
            _RETURN_NONE]
        )

        save_text_file(a_build_rules, [
            "CONTINUE = True",
            _DEF_CLEAN,
            _RETURN_ZERO]
        )
        makeprojects.clean(a_dir)

        # Test for returning an error code
        save_text_file(build_rules, [
            "CLEANME_GENERIC = True",
            _DEF_CLEAN,
            "\traise RuntimeError(\"RETURN 0 didn't abort clean()\")",
            _RETURN_NONE]
        )

        save_text_file(a_build_rules, [
            "CONTINUE = True",
            _DEF_CLEAN,
            _RETURN_ONE]
        )
        makeprojects.clean(a_dir)

########################################

    def test_cleanme_dependencies(self):
        """
        Test to see if cleanme handles CLEANME_DEPENDENCIES.
        """

        # Create some temp folders
        a_dir = self.mkdir(self.tmpdir, "a")

        # Write out the test files
        foo_txt = self.save_text_file(self.tmpdir, "foo.txt")
        foo_cpp = self.save_text_file(self.tmpdir, "foo.cpp")
        a_foo_txt = self.save_text_file(a_dir, "foo.txt")
        a_foo_cpp = self.save_text_file(a_dir, "foo.cpp")

        # Write out the build_rules.py files
        build_rules = os.path.join(self.tmpdir, "build_rules.py")
        a_build_rules = os.path.join(a_dir, "build_rules.py")

        # Test CLEANME_CONTINUE = False
        save_text_file(build_rules, [
            'CLEANME_DEPENDENCIES = ["a"]',
            'CLEANME_GENERIC = True',
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.cpp")',
            _RETURN_NONE]
        )
        makeprojects.clean(self.tmpdir)
        self.assertTrue(os.path.isfile(foo_txt))
        self.assertFalse(os.path.isfile(foo_cpp))
        self.assertTrue(os.path.isfile(a_foo_txt))
        self.assertFalse(os.path.isfile(a_foo_cpp))

        # Test CLEANME_CONTINUE = False
        foo_cpp = self.save_text_file(self.tmpdir, 'foo.cpp')
        a_foo_cpp = self.save_text_file(a_dir, 'foo.cpp')
        save_text_file(build_rules, [
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.txt")',
            _RETURN_NONE]
        )

        save_text_file(a_build_rules, [
            'CLEANME_DEPENDENCIES = [".."]',
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.cpp")',
            _RETURN_NONE]
        )

        makeprojects.clean(a_dir)
        self.assertFalse(os.path.isfile(foo_txt))
        self.assertTrue(os.path.isfile(foo_cpp))
        self.assertTrue(os.path.isfile(a_foo_txt))
        self.assertFalse(os.path.isfile(a_foo_cpp))

########################################

    def test_cleanme_no_recurse(self):
        """
        Test to see if cleanme handles CLEANME_NO_RECURSE.
        """

        # Create some temp folders
        a_dir = self.mkdir(self.tmpdir, "a")

        # Write out the test files
        foo_txt = self.save_text_file(self.tmpdir, "foo.txt")
        foo_cpp = self.save_text_file(self.tmpdir, "foo.cpp")
        a_foo_txt = self.save_text_file(a_dir, "foo.txt")
        a_foo_cpp = self.save_text_file(a_dir, "foo.cpp")

        # Write out the build_rules.py files
        build_rules = os.path.join(self.tmpdir, "build_rules.py")
        a_build_rules = os.path.join(a_dir, "build_rules.py")

        # Test CLEANME_NO_RECURSE = True
        save_text_file(build_rules, [
            "CLEANME_NO_RECURSE = True",
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.cpp")',
            _RETURN_NONE]
        )
        save_text_file(a_build_rules, [
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\traise RuntimeError("CLEANME_NO_RECURSE not parsed")',
            _RETURN_NONE]
        )

        makeprojects.clean(self.tmpdir, ["-r"])
        self.assertTrue(os.path.isfile(foo_txt))
        self.assertFalse(os.path.isfile(foo_cpp))
        self.assertTrue(os.path.isfile(a_foo_txt))
        self.assertTrue(os.path.isfile(a_foo_cpp))

        # Test CLEANME_NO_RECURSE = False
        foo_cpp = self.save_text_file(self.tmpdir, "foo.cpp")
        save_text_file(build_rules, [
            "CLEANME_NO_RECURSE = False",
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.cpp")',
            _RETURN_NONE]
        )
        save_text_file(a_build_rules, [
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.txt")',
            _RETURN_NONE]
        )

        makeprojects.clean(self.tmpdir, ["-r"])
        self.assertTrue(os.path.isfile(foo_txt))
        self.assertFalse(os.path.isfile(foo_cpp))
        self.assertFalse(os.path.isfile(a_foo_txt))
        self.assertTrue(os.path.isfile(a_foo_cpp))

        # Test if a generic rules file prevents recursion
        # No rules in a, failure in b and generic in root.

        foo_cpp = self.save_text_file(self.tmpdir, "foo.cpp")
        a_foo_txt = self.save_text_file(a_dir, "foo.txt")
        b_dir = self.mkdir(a_dir, "b")
        b_build_rules = os.path.join(b_dir, "build_rules.py")
        b_foo_txt = self.save_text_file(b_dir, "foo.txt")
        b_foo_cpp = self.save_text_file(b_dir, "foo.cpp")

        save_text_file(build_rules, [
            "CLEANME_NO_RECURSE = True",
            "CLEANME_GENERIC = True",
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.cpp")',
            _RETURN_NONE]
        )
        delete_file(a_build_rules)
        save_text_file(b_build_rules, [
            _IMPORT_BURGER,
            _DEF_CLEAN,
            '\traise RuntimeError("CLEANME_NO_RECURSE not parsed")',
            _RETURN_NONE]
        )

        makeprojects.clean(a_dir, ["-r"])
        self.assertTrue(os.path.isfile(foo_txt))
        self.assertTrue(os.path.isfile(foo_cpp))
        self.assertTrue(os.path.isfile(a_foo_txt))
        self.assertFalse(os.path.isfile(a_foo_cpp))
        self.assertTrue(os.path.isfile(b_foo_txt))
        self.assertTrue(os.path.isfile(b_foo_cpp))

########################################

    def test_cleanme_missing_clean(self):
        """
        Test for a special case where a file doesn't have the clean() function.

        It was found that if a build_rules.py file did not have a clean()
        function, cleanme would report "clean is not a callable
        function". This is a bug. It should skip the build_rules file.
        """

        # Create a temp folder
        a_dir = self.mkdir(self.tmpdir, "a")

        a_foo_cpp = self.save_text_file(a_dir, "foo.cpp")

        # Write out the build_rules.py files
        build_rules = os.path.join(self.tmpdir, "build_rules.py")
        a_build_rules = os.path.join(a_dir, "build_rules.py")

        # Test CLEANME_NO_RECURSE = True
        save_text_file(build_rules, [
            _IMPORT_BURGER,
            "GENERIC = True",
            _DEF_CLEAN,
            '\tburger.clean_files(working_directory, "*.cpp")',
            _RETURN_ONE]
        )
        save_text_file(a_build_rules, [
            "CONTINUE = True"]
        )
        self.assertEqual(makeprojects.clean(a_dir), 1)
        self.assertFalse(os.path.isfile(a_foo_cpp))

########################################


if __name__ == "__main__":
    unittest.main()
