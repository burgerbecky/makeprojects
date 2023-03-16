#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2022-2023 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

"""
Sub file for makeprojects.
Subroutines for Apple Computer XCode projects

@package makeprojects.xcode_utils
This module contains classes needed to generate
project files intended for use by Apple's XCode IDE
"""

from __future__ import absolute_import, print_function, unicode_literals

########################################


def get_sdk_root(solution):
    """
    Determine the main Xcode root sdk

    Args:
        solution: Solution object

    Returns:
        String of the Xcode SDKROOT
    """

    # Check if there is an override?
    for project in solution.project_list:
        for configuration in project.configuration_list:
            sdkroot = configuration.get_chained_value("xc_sdkroot")

            # Use the override
            if sdkroot:
                return sdkroot

    # Punt
    if solution.project_list[0].configuration_list[0].platform.is_ios():
        return "iphoneos"
    return "macosx"
