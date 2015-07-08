#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2015 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

import sys
import os
from .core import run

#
## \mainpage makeprojects for Python Index
#
# A tool to generate projects for popular IDEs
#
# \par List of IDE classes
# 
# \li \ref makeprojects.xcode
# \li \ref makeprojects.vs
# \li \ref makeprojects.codewarrior
#
#
# To use in your own script:
#
# \code
# import makeprojects
#
# makeprojects.make()
# \endcode
#
#
# To install type in 'easy_install makeprojects' from your python command line
#
# The source can be found at github at https://github.com/burgerbecky/makeprojects
#
# Email becky@burgerbecky.com for comments, bugs or coding suggestions.
#

#
## \package makeprojects
# A tool to generate projects for popular IDEs
#

#
# If invoked as a tool, call the main with the current working directory
#

def main():
	exit = run(os.getcwd())
	if exit:
		sys.exit(exit)
