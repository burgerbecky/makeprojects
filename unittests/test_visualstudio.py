#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unit tests for makeprojects.visual_studio

Copyright 2013-2025 by Rebecca Ann Heineman becky@burgerbecky.com

It is released under an MIT Open Source license. Please see LICENSE
for license details. Yes, you can use it in a
commercial title without paying anything, just give me a credit.
Please? It's not like I'm asking you for money!

"""

# pylint: disable=wrong-import-position

import unittest
import os
import sys

# Insert the location of makeprojects at the begining so it's the first
# to be processed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from makeprojects.visual_studio_utils import get_uuid
from makeprojects.visual_studio import VS2003XML
from makeprojects.validators import VSStringProperty

########################################


class TestVisualStudio(unittest.TestCase):
    """
    Test visual studio text generation
    """

########################################

    def test_get_uuid(self):
        """
        Test makeprojects.visual_studio.get_uuid
        """

        tests = (
            ('testme', '7A67F5D4-50FD-36F7-BBEB-1C739AB40B8C'),
            ('helloworldvc7win.vcproj', 'D4B7B275-B4D2-3FEF-86CF-D2D640314544')
        )

        for test in tests:
            self.assertEqual(get_uuid(test[0]), test[1])


########################################


    def test_vs2003xml(self):
        """
        Test makeprojects.visual_studio.VS2003XML
        """

        # Test several combinations for XML for Visual Studio 2003

        # Empty entry
        vs_project = VS2003XML('VisualStudioProject')
        self.assertEqual(
            str(vs_project),
            '<VisualStudioProject>\n</VisualStudioProject>')

        # Entry with only attributes
        vs_project.add_attribute(VSStringProperty('ProjectType', 'Visual C++'))
        self.assertEqual(str(vs_project), (
            '<VisualStudioProject\n'
            '\tProjectType="Visual C++"\n/>'))

        # Test a second element
        platform = VS2003XML('Platform')
        platform.add_attribute(VSStringProperty('Name', 'Win32'))
        self.assertEqual(str(platform), '<Platform\n\tName="Win32"\n/>')

        # Test an element in an element
        vs_project = VS2003XML('VisualStudioProject')
        vs_project.add_element(platform)
        self.assertEqual(str(vs_project), (
            '<VisualStudioProject>\n'
            '\t<Platform\n'
            '\t\tName="Win32"\n\t/>\n'
            '</VisualStudioProject>'))

        # Test with element in an element with attributes
        vs_project.add_attribute(VSStringProperty('ProjectType', 'Visual C++'))
        self.assertEqual(str(vs_project), (
            '<VisualStudioProject\n'
            '\tProjectType="Visual C++"\n\t>\n'
            '\t<Platform\n'
            '\t\tName="Win32"\n\t/>\n'
            '</VisualStudioProject>'))

        vs_project.set_attribute('ProjectType', 'Visual C')
        self.assertEqual(str(vs_project), (
            '<VisualStudioProject\n'
            '\tProjectType="Visual C"\n\t>\n'
            '\t<Platform\n'
            '\t\tName="Win32"\n\t/>\n'
            '</VisualStudioProject>'))

        vs_project.add_attribute(VSStringProperty('ProjectGUID', 'GUID'))
        self.assertEqual(str(vs_project), (
            '<VisualStudioProject\n'
            '\tProjectType="Visual C"\n'
            '\tProjectGUID="GUID"\n\t>\n'
            '\t<Platform\n'
            '\t\tName="Win32"\n\t/>\n'
            '</VisualStudioProject>'))

        # Intentionally do nothing
        vs_project.remove_attribute('foofar')
        self.assertEqual(str(vs_project), (
            '<VisualStudioProject\n'
            '\tProjectType="Visual C"\n'
            '\tProjectGUID="GUID"\n\t>\n'
            '\t<Platform\n'
            '\t\tName="Win32"\n\t/>\n'
            '</VisualStudioProject>'))

        # Test removal
        vs_project.remove_attribute('ProjectType')
        self.assertEqual(str(vs_project), (
            '<VisualStudioProject\n'
            '\tProjectGUID="GUID"\n\t>\n'
            '\t<Platform\n'
            '\t\tName="Win32"\n\t/>\n'
            '</VisualStudioProject>'))

        vs_project.remove_attribute('ProjectGUID')
        self.assertEqual(str(vs_project), (
            '<VisualStudioProject>\n'
            '\t<Platform\n'
            '\t\tName="Win32"\n\t/>\n'
            '</VisualStudioProject>'))

########################################


if __name__ == '__main__':
    unittest.main()
