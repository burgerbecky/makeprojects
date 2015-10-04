#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2015 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

#
# Note: This is only executed if makeprojects is imported as a module
#

#
# Describe this module
#

## Current version of the library
__version__ = '0.3.7'

## Author's name
__author__ = 'Rebecca Ann Heineman <becky@burgerbecky.com>'

## Name of the module
__title__ = 'makeprojects'

## Summary of the module's use
__summary__ = 'IDE project generator for Visual Studio, XCode, etc...'

## Home page
__uri__ = 'http://burgerbecky.com'

## Email address for bug reports
__email__ = 'becky@burgerbecky.com'

## Type of license used for distribution
__license__ = 'MIT License'

## Copyright owner
__copyright__ = 'Copyright 2013-2015 Rebecca Ann Heineman'

#
## Items to import on "from makeprojects import *"
#

__all__ = [
	'__version__',
	'__author__',
	'__title__',
	'__summary__',
	'__uri__',
	'__email__',
	'__license__',
	'__copyright__',
	'core',
#	'vs',
#	'watcom',
#	'codeblocks',
#	'codewarrior',
	'xcode'
]
