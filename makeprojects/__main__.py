#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2015 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

import sys
import os
from .makeprojects import main

#
# If invoked as a tool, call the main with the current working directory
#

if __name__ == '__main__':
	exit = main()
	if exit:
		sys.exit(exit)
