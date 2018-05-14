#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Rebuild a project

Copyright 2013-2018 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!
"""

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os
from makeprojects import buildme
from makeprojects import cleanme

#
## \package makeprojects.rebuildme
# Module that contains the code for the command line "rebuildme"
#


def main(working_dir=None):
	"""
	Invoke the command line 'rebuildme'

	Args:
		working_dir: Directory to rebuild
	Returns:
		Zero on no error, non-zero on error
	"""

	# Make sure the working directory is set
	if working_dir is None:
		working_dir = os.getcwd()

	# Clean and then build, couldn't be simpler!
	error = cleanme.main(working_dir)
	if error == 0:
		error = buildme.main(working_dir)
	return error

#
# If called as a function and not a class, call my main
#

if __name__ == "__main__":
	sys.exit(main())
