#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeproject cleanme

Copyright 2013-2019 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

import os
import makeprojects

########################################


def test_cleanme(tmpdir):
    """
    Test to see if cleanme loads build_rules.py.
    """

    # Sample script
    clean_script = (
        'import burger\n'
        'def rules(command, working_directory):\n'
        '   if command=="clean":\n'
        '       burger.clean_directories(working_directory, ("temp", "bin"))\n'
    )

    # Create some temp folders
    temp_dir = tmpdir.mkdir('temp')
    bin_dir = tmpdir.mkdir('bin')
    # Create a folder that should not be deleted
    source_dir = tmpdir.mkdir('source')

    # Write out the build_rules.py file
    tmpdir.join('build_rules.py').write(clean_script)
    makeprojects.clean(str(tmpdir), [])

    # temp and bin should disappear, but not the others
    assert not os.path.isdir(str(temp_dir))
    assert not os.path.isdir(str(bin_dir))
    assert os.path.isdir(str(source_dir))
    assert os.path.isfile(str(tmpdir.join('build_rules.py')))

    # Cleanup
    tmpdir.remove()


########################################


def test_cleanme_root(tmpdir):
    """
    Test to see if cleanme handles root=True.
    """

    clean_script_root = (
        'import burger\n'
        'def rules(command, working_directory=None, root=True):\n'
        '   if command=="clean":\n'
        '       burger.clean_files(working_directory, "*.txt")\n'
    )

    clean_script_no_root = (
        'import burger\n'
        'def rules(command, working_directory):\n'
        '   if command=="clean":\n'
        '       burger.clean_files(working_directory, "*.cpp")\n'
    )


    # Create some temp folders
    a_dir = tmpdir.mkdir('a')

    # Write out the build_rules.py file
    tmpdir.join('build_rules.py').write(clean_script_root)
    a_dir.join('build_rules.py').write(clean_script_no_root)

    tmpdir.join('foo.txt').write('abc')
    tmpdir.join('foo.cpp').write('abc')
    a_dir.join('foo.txt').write('abc')
    a_dir.join('foo.cpp').write('abc')
    makeprojects.clean(str(a_dir), [])

    # Files in 'a' should disappear but not those in tmpdir
    assert os.path.isfile(str(tmpdir.join('foo.txt')))
    assert os.path.isfile(str(tmpdir.join('foo.cpp')))
    assert not os.path.isfile(str(a_dir.join('foo.txt')))
    assert not os.path.isfile(str(a_dir.join('foo.cpp')))

    # Cleanup
    tmpdir.remove()
