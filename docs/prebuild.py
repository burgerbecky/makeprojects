#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Preprocess READEME.rst

Doxygen doesn't support the importation of .rst files, and the
support for .md files doesn't support images that
also have links. To get around this limitation, this preprocessor
will use docutils to convert the README.rst into an html file
which will be directly imported into the Doxygen documentation
so only one copy of the README is needed.

"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import pypandoc
import burger


def main(working_dir):

    """
    Copy README.rst to docs/temp/README.html

    """

    # Doxygen may not create the output folder, ensure it exists.

    burger.create_folder_if_needed(os.path.join(working_dir, 'temp'))

    # Get the input and output file names
    source = os.path.join(os.path.dirname(working_dir), 'README.rst')
    dest = os.path.join(working_dir, 'temp', 'README.html')

    # Was the file already created and newer than the source?
    if burger.is_source_newer(source, dest):

        # Load pandoc if needed to do the conversion
        if hasattr(pypandoc, 'ensure_pandoc_installed'):
            pypandoc.ensure_pandoc_installed(quiet=True, delete_installer=True)
        else:
            try:
                pypandoc.get_pandoc_path()
            except OSError:
                pypandoc.download_pandoc()
        pypandoc.convert_file(source, to='html', outputfile=dest)

    return 0


# If called as a function and not a class,
# call my main

if __name__ == "__main__":
    sys.exit(main(os.path.dirname(os.path.abspath(__file__))))
