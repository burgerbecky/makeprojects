#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module contains the core classes for makeproject.
"""

## \package makeprojects.core

from __future__ import absolute_import, print_function, unicode_literals
import os
import uuid
import operator
import burger
import makeprojects.xcode
import makeprojects.codeblocks
from makeprojects import FileTypes, ProjectTypes, IDETypes, PlatformTypes, SourceFile, Property

########################################


class Configuration:
    """
    Object for containing attributes specific to a build configuration.

    This object contains all of the items needed to create a specific configuration of
    a project.

    See Also:
        Project, Solution
    """

    def __init__(self, name, platform=None, project_type=None):
        """
        Init defaults.

        Args:
            name: Name of the configuration
            platform: Target platform to build
        """
        # Use defaults
        if not name:
            name = 'Debug'

        if not platform:
            platform = PlatformTypes.default()
        else:
            platform = PlatformTypes.lookup(platform)
            if not isinstance(platform, PlatformTypes):
                raise TypeError("parameter 'platform' must be of type PlatformTypes")

        if not project_type:
            project_type = ProjectTypes.default()
        else:
            project_type = ProjectTypes.lookup(project_type)
            if not isinstance(project_type, ProjectTypes):
                raise TypeError("parameter 'project_type' must be of type ProjectTypes")

        ## Project this Configuration is attached to.
        self.project = None

        ## Dictionary of attributes describing how to build this configuration.
        self.attributes = {'name': name, 'platform': platform, 'project_type': project_type}
        self.init_attributes()

    def init_attributes(self):
        """
        Initialize the attributes to defaults
        """

        name = self.attributes['name']
        platform = self.attributes['platform']

        # Files to include
        self.attributes['files'] = ['*.c', '*.cpp', '*.h', '*.inl']

        # Files to exclude
        self.attributes['exclude'] = []

        # Extra directories for "include"
        self.attributes['include_folders'] = []

        # Extra directories for libraries
        self.attributes['library_folders'] = []

        # Debug/Release
        if name in ('Debug', 'Internal'):
            self.attributes['defines'] = ['_DEBUG']
        else:
            self.attributes['defines'] = ['NDEBUG']

        if name in ('Release', 'Internal', 'Profile'):
            self.attributes['optimization'] = 4
        else:
            self.attributes['optimization'] = 0

        if name in ('Profile', 'Profile_FastCap'):
            self.attributes['profile'] = True

        if name == 'Release_LTCG':
            self.attributes['link_time_code_generation'] = True

        # Windows specific defines
        if platform.is_windows():
            self.attributes['defines'].extend(
                ['_WINDOWS', 'WIN32_LEAN_AND_MEAN', '_CRT_NONSTDC_NO_WARNINGS', '_CRT_SECURE_NO_WARNINGS', 'GLUT_NO_LIB_PRAGMA'])
            if platform == PlatformTypes.win64:
                self.attributes['defines'].append('WIN64')
            else:
                self.attributes['defines'].append('WIN32')
            self.attributes['UseOfMfc'] = False
            self.attributes['UseOfAtl'] = False
            self.attributes['CLRSupport'] = False
            self.attributes['CharacterSet'] = 'Unicode'

        # Playstation 4
        if platform == PlatformTypes.ps4:
            self.attributes['defines'].append('__ORBIS2__')

        # Playstation Vita
        if platform == PlatformTypes.vita:
            self.attributes['defines'].append('SN_TARGET_PSP2')

        # Android targets
        if platform.is_android():
            self.attributes['defines'].append('DISABLE_IMPORTGL')

        # Xbox 360
        if platform == PlatformTypes.xbox360:
            self.attributes['defines'].extend(['_XBOX', 'XBOX'])

        # Mac Carbon
        if platform.is_macos_carbon():
            self.attributes['defines'].append('TARGET_API_MAC_CARBON=1')

        # Nintendo DSI specific defines
        if platform == PlatformTypes.dsi:
            self.attributes['defines'].extend([
                'NN_BUILD_DEBUG',
                'NN_COMPILER_RVCT',
                'NN_COMPILER_RVCT_VERSION_MAJOR=$(CTRSDK_RVCT_VER_MAJOR)',
                'NN_PROCESSOR_ARM',
                'NN_PROCESSOR_ARM11MPCORE',
                'NN_PROCESSOR_ARM_V6',
                'NN_PROCESSOR_ARM_VFP_V2',
                'NN_HARDWARE_CTR',
                'NN_PLATFORM_CTR',
                'NN_HARDWARE_CTR_TS',
                'NN_SYSTEM_PROCESS',
                'NN_SWITCH_ENABLE_HOST_IO=1',
                'NN_BUILD_VERBOSE',
                'NN_BUILD_NOOPT',
                'NN_DEBUGGER_KMC_PARTNER'])

        # Linux platform
        if platform == PlatformTypes.linux:
            self.attributes['defines'].append('__LINUX__')

        # macOS X platform
        if platform.is_macosx():
            self.attributes['frameworks'] = [
                'AppKit.framework',
                'AudioToolbox.framework',
                'AudioUnit.framework',
                'Carbon.framework',
                'Cocoa.framework',
                'CoreAudio.framework',
                'IOKit.framework',
                'OpenGL.framework',
                'QuartzCore.framework',
                'SystemConfiguration.framework'
            ]

        # iOS platform
        if platform.is_ios():
            self.attributes['frameworks'] = [
                'AVFoundation.framework',
                'CoreGraphics.framework',
                'CoreLocation.framework',
                'Foundation.framework',
                'QuartzCore.framework',
                'UIKit.framework'
            ]

    ########################################

    def get_attribute(self, name):
        """
        Return an attribute by key.

        If the attribute does not exist, it will check
        the project and then the solution for the key.

        Args:
            name: Name of the attribute key
        Return:
            None if the attribute is not in use, or a value.
        """

        value = self.attributes.get(name)
        if value is None:
            value = self.project.get_attribute(name)
        return value

    ########################################

    def get_attributes(self, build_rules_list, working_directory):
        """
        Initialize the default attributes.

        Args:
            build_rules_list: List to append a valid build_rules file instance.
            working_directory: Full path name of the build_rules.py to load.
        """
        self.init_attributes()
        for rules in build_rules_list:
            default = rules(
                'configuration_settings',
                working_directory=working_directory,
                configuration=self)
            if default != 0:
                break

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return 'Configuration: {}, Platform: {}, Attributes: {}'.format(
            self.attributes['name'], str(self.attributes['platform']), str(self.attributes))

    ## Allow str() to work.
    __str__ = __repr__


########################################

def configuration_short_code(configuration_name):
    """
    Convert configuration name to a 3 letter code.
    """
    codes = {
        'Debug': 'dbg',
        'Release': 'rel',
        'Internal': 'int',
        'Profile': 'pro',
        'Release_LTCG': 'ltc',
        'CodeAnalysis': 'cod',
        'Profile_FastCap': 'fas'
    }
    return codes.get(configuration_name, None)


########################################


class Project:
    """
    Object for processing a project file.

    This object contains all of the items needed to create a project

    @note On most IDEs, this is merged into one file, but Visual Studio
    2010 and higher generates a project file for each project.
    """

    def __init__(self, name=None, working_directory=None, project_type=None, platform=None):
        """
        Set defaults.
        """

        if not name:
            name = 'project'

        if not working_directory:
            working_directory = os.getcwd()

        # Type of project, tool is default ('tool', 'app', 'library')
        if not project_type:
            project_type = ProjectTypes.default()
        else:
            project_type = ProjectTypes.lookup(project_type)
            if not isinstance(project_type, ProjectTypes):
                raise TypeError("parameter 'project_type' must be of type ProjectTypes")

        # Type of platform
        if not platform:
            platform = PlatformTypes.default()
        else:
            platform = PlatformTypes.lookup(platform)
            if not isinstance(platform, PlatformTypes):
                raise TypeError("parameter 'platform' must be of type PlatformTypes")

        ## No parent solution yet
        self.solution = None

        ## Generate the three default configurations
        self.configurations = []

        ## Initial array of Project records that need to be built first
        self.projects = []

        ## Initial array of SourceFile in the solution
        self.codefiles = []

        ## Attributes used by generators
        self.attributes = {
            'name': name,
            'working_directory': working_directory,
            'project_type': project_type,
            'platform': platform,
            'source_folders': ['.', 'source', 'src'],
            'include_folders': [],
            'defines': []}

        ## Properties used by generators
        self.properties = [
            Property(name="DEFINE", data="_DEBUG", configuration='Debug'),
            Property(name="DEFINE", data="_DEBUG", configuration='Internal'),
            Property(name="DEFINE", data="NDEBUG", configuration='Release'),
            Property(name="DEFINE", data="WIN32_LEAN_AND_MEAN", platform=PlatformTypes.windows),
            Property(name="DEFINE", data="WIN32", platform=PlatformTypes.win32),
            Property(name="DEFINE", data="WIN64", platform=PlatformTypes.win64)
        ]

        ## Create default XCode object
        self.xcode = makeprojects.xcode.Defaults()

        from .codewarrior import Defaults as cw_defaults
        ## Create default Codewarrior object
        self.codewarrior = cw_defaults()

        from .visualstudio import Defaults as vs_defaults
        ## Create default Visual Studio object
        self.visualstudio = vs_defaults()

    def add_configuration(self, configuration):
        """
        Add a configuration to the list of configurations found in this project.

        Given a new Configuration class instance, append it to the list of
        configurations that this project is managing.

        Args:
            self: The 'this' reference.
            configuration: Reference to an instance of a Configuration.
        Exception:
            TypeError if configuration is not a Configuration
        """

        if configuration:
            # Singular
            if isinstance(configuration, Configuration):
                configuration.project = self
                self.configurations.append(configuration)
            else:
                # Assume iterable
                for item in configuration:
                    # Sanity check
                    if not isinstance(item, Configuration):
                        raise TypeError("parameter 'configuration' must be of type Configuration")
                    item.project = self
                    self.configurations.append(item)

    def add_project(self, project):
        """
        Add a dependent project.

        Args:
            project: Project to depend on.
        Exception:
            TypeError if project is not a Project
        """
        # Sanity check
        if not isinstance(project, Project):
            raise TypeError("parameter 'project' must be of type Project")
        self.projects.append(project)

    ########################################

    def get_attribute(self, name):
        """
        Return an attribute by key.

        If the attribute does not exist, it will check
        the solution for the key.

        Args:
            name: Name of the attribute key
        Return:
            None if the attribute is not in use, or a value.
        """

        value = self.attributes.get(name)
        if value is None:
            value = self.solution.get_attribute(name)
        return value

    ########################################

    def scan_directory(self, working_directory, file_list, include_list, recurse, acceptable):
        """
        Given a base directory and a relative directory
        scan for all the files that are to be included in the project

        Args:
            working_directory: Directory to scan
            file_list: list to store SourceFile records
        """

        # Absolute or relative?
        if not os.path.isabs(working_directory):
            working_directory = os.path.abspath(
                os.path.join(self.get_attribute('working_directory'),
                             working_directory))

        # Is this a valid directory?
        if os.path.isdir(working_directory):

            exclude = self.get_attribute('exclude')
            if not exclude:
                exclude = []

            # Scan the directory
            name_list = os.listdir(working_directory)

            # No files added, yet (Flag for adding directory to the search tree)
            for base_name in name_list:

                # Is this file in the exclusion list?
                test_name = base_name.lower()
                for item in exclude:
                    if test_name == item.lower():
                        break
                else:

                    # Is it a file? (Skip links and folders)
                    file_name = os.path.join(working_directory, base_name)
                    if os.path.isfile(file_name):

                        # Check against the extension list (Skip if not supported)
                        file_type = FileTypes.lookup(test_name)
                        if file_type is None:
                            continue

                        # Found a match, test if the type is in
                        # the acceptable list

                        if file_type in acceptable:
                            # Create a new entry (Using windows style slashes for consistency)
                            fileentry = SourceFile(
                                os.path.relpath(
                                    file_name,
                                    self.get_attribute('working_directory')),
                                working_directory,
                                file_type)
                            file_list.append(fileentry)
                            include_list.append(
                                os.path.relpath(
                                    working_directory,
                                    self.get_attribute('working_directory')))

                    # Process folders only if in recursion mode
                    elif recurse:
                        if os.path.isdir(file_name):
                            self.scan_directory(
                                file_name, file_list, include_list, recurse, acceptable)

    ########################################

    def get_file_list(self, acceptable):
        """
        Obtain the list of source files
        """

        # Get the files that were manually parsed by the json
        # record

        file_list = []
        include_list = []
        for item in self.get_attribute('source_folders'):

            # Is it a recursive test?
            recurse = False
            if item.endswith('/*.*'):
                # Remove the trailing /*.*
                item = item[0:len(item) - 4]
                recurse = True

            # Scan the folder for files
            self.scan_directory(
                item, file_list, include_list, recurse, acceptable)

        # Since the slashes are all windows (No matter what
        # host this script is running on, the sort will yield consistent
        # results so it doesn't matter what platform generated the
        # file list, it's the same output.
        self.codefiles = sorted(file_list, key=operator.attrgetter('filename'))
        self.attributes['extra_include'] = sorted(list(set(include_list)))

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return 'Project: {}, CodeFiles: {}, Attributes: {}, Configurations: {}'.format(
            self.attributes['name'],
            str(self.codefiles),
            str(self.attributes),
            str(self.configurations))

    ## Allow str() to work.
    __str__ = __repr__


class Solution:
    """
    Object for processing a solution file.

    This object contains all of the items needed to create a solution.
    """

    def __init__(self, name, working_directory=None, verbose=False, ide=None, perforce=True):
        """
        Init defaults.

        Args:
            name: Name of the project
            working_directory: Directory to store the solution.
            verbose: If True, verbose output.
            ide: IDE to build for.
        """

        # Name needs a default
        if not name:
            name = 'project'

        # Working directory needs a default
        if not working_directory:
            working_directory = os.getcwd()

        if not ide:
            ide = IDETypes.default()
        else:
            ide = IDETypes.lookup(ide)
            if not isinstance(ide, IDETypes):
                raise TypeError("parameter 'ide' must be of type IDETypes")

        ## Type of ide
        self.ide = ide

        ## Initial array of Project records for projects
        self.projects = []

        ## Dictionary of attributes describing how to build this solution.
        self.attributes = {
            'name': name,
            'working_directory': working_directory,
            'verbose': verbose,
            'suffix_enable': True,
            'perforce': perforce}

        ## Create default XCode object
        self.xcode = makeprojects.xcode.Defaults()

        from .codewarrior import Defaults as cw_defaults
        ## Create default Codewarrior object
        self.codewarrior = cw_defaults()

        from .visualstudio import Defaults as vs_defaults
        ## Create default Visual Studio object
        self.visualstudio = vs_defaults()

    def add_project(self, project):
        """
        Add a project to the list of projects found in this solution.

        Given a new Project class instance, append it to the list of
        projects that this solution is managing.

        Args:
            self: The 'this' reference.
            project: Reference to an instance of a Project.
        """

        # Sanity check
        if not isinstance(project, Project):
            raise TypeError("parameter 'project' must be of type Project")

        project.solution = self
        self.projects.append(project)

    ########################################

    def get_attribute(self, name):
        """
        Return an attribute by key.

        Args:
            name: Name of the attribute key
        """
        return self.attributes.get(name)

    ########################################

    def generate(self, ide=None):
        """
        Generate a project file and write it out to disk.
        """

        # Sanity check
        if ide is not None:
            if not isinstance(ide, IDETypes):
                raise TypeError("parameter 'ide' must be of type IDETypes")
            self.ide = ide

        # Create Visual Studio files
        if ide.is_visual_studio():
            from .visualstudio import generate as vs_generate
            return vs_generate(self)
        return 10

    def processjson(self, myjson):
        r"""
        Given a json record process, all the sub sections.
        @details
        Given a dictionary created by a json file or manually update the solution to the new data.

        Acceptable keys
        * finalfolder = pathname to store final release binary.
        * 'kind' = 'tool', 'library', 'app'.
        * 'projectname' = Name of the project's filename (basename only)
        * 'platform' = 'windows', 'macosx', 'linux', 'ps3', 'ps4', 'vita', 'xbox',
        * 'xbox360', 'xboxone', 'shield', 'ios', 'mac', 'msdos', 'beos', 'ouya', 'wiiu', 'dsi'
        * 'configurations' = ['Debug', 'Release', 'Internal']
        * 'sourcefolders' = ['.','source']
        * 'exclude' = [] (List of files to exclude from processing)
        * 'defines' = [] (List of \#define to add to the project)
        * 'includefolders' = [] (List of folders to add for \#include )
        * 'xcode' = dir (Keys and values for special cases for xcode projects)
        * 'visualstudio' = dir (Keys and values for special cases for visual studio projects)

        Args:
            self: The 'this' reference.
            myjson: Dictionary with key value pairs.

        See Also:
            makeprojects.xcode, makeprojects.visualstudio
        """

        error = 0
        for key in myjson.keys():
            if key == 'finalfolder':
                for configuration in self.projects[0].configurations:
                    if myjson[key] == "":
                        configuration.attributes['deploy_folder'] = None
                    else:
                        configuration.attributes['deploy_folder'] = myjson[key]

            elif key == 'kind':
                # Convert json token to enumeration (Will assert if not enumerated)
                self.projects[0].attributes['project_type'] = ProjectTypes[myjson[key]]
            elif key == 'projectname':
                self.attributes['name'] = myjson[key]
            elif key == 'platform':
                self.projects[0].attributes['platform'] = PlatformTypes[myjson[key]]

            elif key == 'configurations':
                self.projects[0].configurations = []
                for item in burger.convert_to_array(myjson[key]):
                    self.projects[0].configurations.append(Configuration(item))
            elif key == 'sourcefolders':
                self.projects[0].attributes['source_folders'] = burger.convert_to_array(myjson[key])
            elif key == 'exclude':
                self.projects[0].attributes['exclude'] = burger.convert_to_array(myjson[key])
            elif key == 'defines':
                definelist = burger.convert_to_array(myjson[key])
                for item in definelist:
                    self.projects[0].properties.append(Property(name="DEFINE", data=item))
                self.projects[0].attributes['defines'] = definelist
            elif key == 'includefolders':
                self.projects[0].attributes['include_folders'] = burger.convert_to_array(
                    myjson[key])

            #
            # Handle IDE specific data
            #

            elif key == 'xcode':
                error = self.xcode.loadjson(myjson[key])
            elif key == 'visualstudio':
                error = self.visualstudio.loadjson(myjson[key])
            elif key == 'codewarrior':
                error = self.codewarrior.loadjson(myjson[key])
            else:
                print('Unknown keyword "' + str(key) + '" with data "'
                      + str(myjson[key]) + '" found in json file')
                error = 1

            if error != 0:
                break

        return error

    def process(self, myjson):
        """
        The script is an array of objects containing solution settings
        and a list of IDEs to output scripts
        """

        from .codewarrior import generate as cw_generate
        from .watcom import generate as watcom_generate
        from .makefile import generate as makefile_generate
        error = 0
        from .visualstudio import generateold as vs_generateold
        for item in myjson:
            if isinstance(item, dict):
                error = self.processjson(item)
            elif item == 'vs2019':
                self.ide = IDETypes.vs2019
                error = vs_generateold(self)
            elif item == 'vs2017':
                self.ide = IDETypes.vs2017
                error = vs_generateold(self)
            elif item == 'vs2015':
                self.ide = IDETypes.vs2015
                error = vs_generateold(self)
            elif item == 'vs2013':
                self.ide = IDETypes.vs2013
                error = vs_generateold(self)
            elif item == 'vs2012':
                self.ide = IDETypes.vs2012
                error = vs_generateold(self)
            elif item == 'vs2010':
                self.ide = IDETypes.vs2010
                error = vs_generateold(self)
            elif item == 'vs2008':
                self.ide = IDETypes.vs2008
                error = createvs2008solution(self)
            elif item == 'vs2005':
                self.ide = IDETypes.vs2005
                error = createvs2005solution(self)
            elif item == 'xcode3':
                self.ide = IDETypes.xcode3
                error = makeprojects.xcode.generate(self)
            elif item == 'xcode4':
                self.ide = IDETypes.xcode4
                error = makeprojects.xcode.generate(self)
            elif item == 'xcode5':
                self.ide = IDETypes.xcode5
                error = makeprojects.xcode.generate(self)
            elif item == 'xcode6':
                self.ide = IDETypes.xcode6
                error = makeprojects.xcode.generate(self)
            elif item == 'xcode7':
                self.ide = IDETypes.xcode7
                error = makeprojects.xcode.generate(self)
            elif item == 'xcode8':
                self.ide = IDETypes.xcode8
                error = makeprojects.xcode.generate(self)
            elif item == 'xcode9':
                self.ide = IDETypes.xcode9
                error = makeprojects.xcode.generate(self)
            elif item == 'codewarrior9' or item == 'codewarrior50':
                self.ide = IDETypes.codewarrior50
                error = cw_generate(self)
            elif item == 'codewarrior10' or item == 'codewarrior58':
                self.ide = IDETypes.codewarrior58
                error = cw_generate(self)
            elif item == 'codewarrior59':
                self.ide = IDETypes.codewarrior59
                error = cw_generate(self)
            elif item == 'codeblocks':
                self.ide = IDETypes.codeblocks
                error = makeprojects.codeblocks.generate(self)
            elif item == 'watcom':
                self.ide = IDETypes.watcom
                error = watcom_generate(self)
            elif item == 'makefile':
                self.ide = IDETypes.make
                error = makefile_generate(self)
            else:
                print('Saving ' + item + ' not implemented yet')
                error = 0
            if error:
                break
        return error

    def processcommandline(self, args):
        """
        Handle the command line case
        by creating a phony json file and passing it
        in for processing
        """
        #
        # Fake json file and initialization record
        #

        dictrecord = dict()

        #
        # Use the work folder name as the project name
        #

        dictrecord['projectname'] = os.path.basename(self.attributes['working_directory'])

        if args.configurations:
            configurations = args.configurations
        else:
            configurations = [
                'Debug',
                'Internal',
                'Release']

        #
        # Only allow finalfolder when release builds are made
        #

        if 'Release' not in configurations:
            args.deploy_folder = False

        dictrecord['configurations'] = configurations

        #
        # Lib, app or tool?
        #

        if args.app is True:
            kind = 'app'
        elif args.library is True:
            kind = 'library'
        else:
            kind = 'tool'
        dictrecord['kind'] = kind

        #
        # Where to find the source
        #

        dictrecord['sourcefolders'] = ['.', 'source/*.*']

        #
        # Save the initializer in a fake json record
        # list
        #

        myjson = [dictrecord]

        #
        # Xcode projects assume a macosx platform
        # unless directed otherwise
        #

        ide_list = []
        for item in args.ides:
            idetype = IDETypes.lookup(item)
            if idetype is None:
                print('IDE {} is not supported.'.format(item))
                return 2
            ide_list.append(idetype)

        platform_list = []
        for item in args.platforms:
            platform_type = PlatformTypes.lookup(item)
            if platform_type is None:
                print('Platform {} is not supported.'.format(item))
                return 2
            platform_list.append(platform_type)

        if args.xcode3 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'macosx'
            if args.deploy_folder:
                initializationrecord['finalfolder'] = makeprojects.xcode.DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('xcode3')

        if args.xcode4 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'macosx'
            if args.deploy_folder:
                initializationrecord['finalfolder'] = makeprojects.xcode.DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('xcode4')

        if args.xcode5 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'macosx'
            if args.deploy_folder:
                initializationrecord['finalfolder'] = makeprojects.xcode.DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('xcode5')

        if args.xcode6 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'macosx'
            if args.deploy_folder:
                initializationrecord['finalfolder'] = makeprojects.xcode.DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('xcode6')

        if args.xcode7 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'macosx'
            if args.deploy_folder:
                initializationrecord['finalfolder'] = makeprojects.xcode.DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('xcode7')

        if args.xcode8 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'macosx'
            if args.deploy_folder:
                initializationrecord['finalfolder'] = makeprojects.xcode.DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('xcode8')

        if args.xcode9 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'macosx'
            if args.deploy_folder:
                initializationrecord['finalfolder'] = makeprojects.xcode.DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('xcode9')

        #
        # These are windows only
        #

        if args.vs2005 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            myjson.append(initializationrecord)
            myjson.append('vs2005')

        if args.vs2008 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            myjson.append(initializationrecord)
            myjson.append('vs2008')

        if args.vs2010 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            if args.deploy_folder:
                from .visualstudio import DEFAULT_FINAL_FOLDER as VS_DEFAULT_FINAL_FOLDER
                initializationrecord['finalfolder'] = VS_DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('vs2010')

        if args.vs2012 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            if args.deploy_folder:
                from .visualstudio import DEFAULT_FINAL_FOLDER as VS_DEFAULT_FINAL_FOLDER
                initializationrecord['finalfolder'] = VS_DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('vs2012')

        if args.vs2013 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            if args.deploy_folder:
                from .visualstudio import DEFAULT_FINAL_FOLDER as VS_DEFAULT_FINAL_FOLDER
                initializationrecord['finalfolder'] = VS_DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('vs2013')

        if args.vs2015 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            if args.deploy_folder:
                from .visualstudio import DEFAULT_FINAL_FOLDER as VS_DEFAULT_FINAL_FOLDER
                initializationrecord['finalfolder'] = VS_DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('vs2015')

        if args.vs2017 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            if args.deploy_folder:
                from .visualstudio import DEFAULT_FINAL_FOLDER as VS_DEFAULT_FINAL_FOLDER
                initializationrecord['finalfolder'] = VS_DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('vs2017')

        if args.vs2019 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            if args.deploy_folder:
                from .visualstudio import DEFAULT_FINAL_FOLDER as VS_DEFAULT_FINAL_FOLDER
                initializationrecord['finalfolder'] = VS_DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('vs2019')

        if args.codeblocks is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            myjson.append(initializationrecord)
            myjson.append('codeblocks')

        if args.codewarrior is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            myjson.append(initializationrecord)
            myjson.append('codewarrior50')

        if args.watcom is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'windows'
            if args.deploy_folder:
                from .watcom import DEFAULT_FINAL_FOLDER as watcom_DEFAULT_FINAL_FOLDER
                initializationrecord['finalfolder'] = watcom_DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('watcom')

        if args.linux is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'linux'
            if args.deploy_folder:
                from .makefile import DEFAULT_FINAL_FOLDER as makefile_DEFAULT_FINAL_FOLDER
                initializationrecord['finalfolder'] = makefile_DEFAULT_FINAL_FOLDER
            myjson.append(initializationrecord)
            myjson.append('makefile')

        #
        # These are platform specific, and as such are
        # tied to specific IDEs that are tailored to
        # the specific platforms
        #

        if args.xbox360 is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'xbox360'
            myjson.append(initializationrecord)
            myjson.append('vs2010')

        if args.ios is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'ios'
            myjson.append(initializationrecord)
            myjson.append('xcode5')

        if args.vita is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'vita'
            myjson.append(initializationrecord)
            myjson.append('vs2010')

        if args.wiiu is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'wiiu'
            myjson.append(initializationrecord)
            myjson.append('vs2013')

        if args.dsi is True:
            initializationrecord = dict()
            initializationrecord['platform'] = 'dsi'
            myjson.append(initializationrecord)
            myjson.append('vs2015')

        if len(myjson) < 2:
            print('No default "projects.json" file found nor any project type specified')
            return 2

        return self.process(myjson)

    def scandirectory(self, directory, codefiles, includedirectories, recurse, acceptable):
        """
        Given a base directory and a relative directory
        scan for all the files that are to be included in the project
        """
        #
        # Root directory is a special case
        #

        if directory == '.':
            search_dir = self.attributes['working_directory']
        else:
            search_dir = os.path.join(self.attributes['working_directory'], directory)

        #
        # Is this a valid directory?
        #
        if os.path.isdir(search_dir):

            #
            # Scan the directory
            #

            name_list = os.listdir(search_dir)

            #
            # No files added, yet (Flag for adding directory to the search tree)
            #

            found = False

            for base_name in name_list:

                #
                # Is this file in the exclusion list?
                #

                test_name = base_name.lower()
                skip = False
                for item in self.projects[0].attributes['exclude']:
                    if test_name == item.lower():
                        skip = True
                        break

                if skip is True:
                    continue

                #
                # Is it a file? (Skip links and folders)
                #

                file_name = os.path.join(search_dir, base_name)
                if os.path.isfile(file_name):

                    #
                    # Check against the extension list (Skip if not supported)
                    #

                    file_type = FileTypes.lookup(test_name)
                    if file_type is not None:

                        #
                        # Found a match, test if the type is in
                        # the acceptable list
                        #

                        if file_type in acceptable:

                            #
                            # If the directory is the root, then don't prepend a directory
                            #
                            if directory == '.':
                                newfilename = base_name
                            else:
                                newfilename = directory + os.sep + base_name

                            #
                            # Create a new entry (Using windows style slashes for consistency)
                            #

                            fileentry = SourceFile(newfilename, search_dir, file_type)
                            codefiles.append(fileentry)
                            if found is False:
                                found = True
                                includedirectories.append(directory)

                #
                # Process folders only if in recursion mode
                #

                elif recurse is True:
                    if os.path.isdir(file_name):
                        codefiles, includedirectories = self.scandirectory(
                            directory + os.sep + base_name, codefiles,
                            includedirectories, recurse, acceptable)

        return codefiles, includedirectories

    def getfilelist(self, acceptable):
        """
        Obtain the list of source files
        """
        #
        # Get the files that were manually parsed by the json
        # record
        #

        codefiles = list(self.projects[0].codefiles)
        includedirectories = []
        for item in self.projects[0].get_attribute('source_folders'):

            #
            # Is it a recursive test?
            #

            recurse = False
            if item.endswith('/*.*'):
                # Remove the trailing /*.*
                item = item[0:len(item) - 4]
                recurse = True

            #
            # Scan the folder for files
            #

            codefiles, includedirectories = self.scandirectory(
                item, codefiles, includedirectories, recurse, acceptable)

        #
        # Since the slashes are all windows (No matter what
        # host this script is running on, the sort will yield consistent
        # results so it doesn't matter what platform generated the
        # file list, it's the same output.
        #

        codefiles = sorted(codefiles, key=operator.attrgetter('filename'))
        return codefiles, includedirectories

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return 'Solution: {}, Attributes: {}, IDE: {}, ' \
            'Projects: [{}]'.format(
                self.attributes['name'],
                str(self.attributes),
                str(self.ide),
                '],['.join([str(i) for i in self.projects]))

    ## Allow str() to work.
    __str__ = __repr__


def pickfromfilelist(codefiles, itemtype):
    """
    Prune the file list for a specific type.
    """
    filelist = []
    for item in codefiles:
        if item.type == itemtype:
            filelist.append(item)
    return filelist


###################################
#                                 #
# Visual Studio 2003-2013 support #
#                                 #
###################################

#
# Used by Visual Studio 2003, 2005 and 2008
#

def dumptreevs2005(indent, string, entry, file_fp, groups):
    """
    Dump out a recursive tree of files to reconstruct a
    directory hiearchy for a file list
    """
    for item in sorted(entry):
        if item != '':
            file_fp.write('\t' * indent + '<Filter Name="' + item + '">\n')
        if string == '':
            merged = item
        else:
            merged = string + '\\' + item
        if merged in groups:
            if item != '':
                tabs = '\t' * (indent + 1)
            else:
                tabs = '\t' * indent
            sortlist = sorted(groups[merged])
            for fileitem in sortlist:
                file_fp.write(tabs + '<File RelativePath="' + fileitem + '" />\n')
        key = entry[item]
        # Recurse down the tree
        if isinstance(key, dict):
            dumptreevs2005(indent + 1, merged, key, file_fp, groups)
        if item != '':
            file_fp.write('\t' * indent + '</Filter>\n')


def createvs2005solution(solution):
    """
    Create the solution and project file for visual studio 2005
    """
    error = makeprojects.visualstudio.generateold(solution)
    if error != 0:
        return error

    #
    # Now, let's create the project file
    #

    acceptable = [FileTypes.h, FileTypes.cpp, FileTypes.rc, FileTypes.ico]
    codefiles, includedirectories = solution.getfilelist(acceptable)
    listh = pickfromfilelist(codefiles, FileTypes.h)
    listcpp = pickfromfilelist(codefiles, FileTypes.cpp)
    listwindowsresource = pickfromfilelist(codefiles, FileTypes.rc)

    platformcode = solution.projects[0].get_attribute('platform').get_short_code()
    solutionuuid = str(uuid.uuid3(uuid.NAMESPACE_DNS,
                                  str(solution.visualstudio.outputfilename))).upper()
    projectpathname = os.path.join(solution.attributes['working_directory'],
                                   solution.visualstudio.outputfilename + '.vcproj')
    burger.perforce_edit(projectpathname)
    file_fp = open(projectpathname, 'w')

    #
    # Save off the xml header
    #

    file_fp.write('<?xml version="1.0" encoding="utf-8"?>\n')
    file_fp.write('<VisualStudioProject\n')
    file_fp.write('\tProjectType="Visual C++"\n')
    file_fp.write('\tVersion="8.00"\n')
    file_fp.write('\tName="' + solution.attributes['name'] + '"\n')
    file_fp.write('\tProjectGUID="{' + solutionuuid + '}"\n')
    file_fp.write('\t>\n')

    #
    # Write the project platforms
    #

    file_fp.write('\t<Platforms>\n')
    for vsplatform in solution.projects[0].get_attribute('platform').get_vs_platform():
        file_fp.write('\t\t<Platform Name="' + vsplatform + '" />\n')
    file_fp.write('\t</Platforms>\n')

    #
    # Write the project configurations
    #

    file_fp.write('\t<Configurations>\n')
    for configuration in solution.projects[0].configurations:
        for vsplatform in solution.projects[0].get_attribute('platform').get_vs_platform():
            token = configuration.attributes['name'] + '|' + vsplatform
            file_fp.write('\t\t<Configuration\n')
            file_fp.write('\t\t\tName="' + token + '"\n')
            file_fp.write('\t\t\tOutputDirectory="bin\\"\n')
            if vsplatform == 'x64':
                platformcode2 = 'w64'
            elif vsplatform == 'Win32':
                platformcode2 = 'w32'
            else:
                platformcode2 = platformcode
            intdirectory = solution.attributes['name'] + solution.ide.get_short_code(
            ) + platformcode2 + configuration_short_code(configuration.attributes['name'])
            file_fp.write('\t\t\tIntermediateDirectory="temp\\' + intdirectory + '"\n')
            if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
                # Library
                file_fp.write('\t\t\tConfigurationType="4"\n')
            else:
                # Application
                file_fp.write('\t\t\tConfigurationType="1"\n')
            file_fp.write('\t\t\tUseOfMFC="0"\n')
            file_fp.write('\t\t\tATLMinimizesCRunTimeLibraryUsage="false"\n')
            # Unicode
            file_fp.write('\t\t\tCharacterSet="1"\n')
            file_fp.write('\t\t\t>\n')

            file_fp.write('\t\t\t<Tool\n')
            file_fp.write('\t\t\t\tName="VCCLCompilerTool"\n')
            file_fp.write('\t\t\t\tPreprocessorDefinitions="')
            if configuration.attributes['name'] == 'Release':
                file_fp.write('NDEBUG')
            else:
                file_fp.write('_DEBUG')
            if vsplatform == 'x64':
                file_fp.write(';WIN64;_WINDOWS')
            elif vsplatform == 'Win32':
                file_fp.write(';WIN32;_WINDOWS')
            for item in solution.projects[0].get_attribute('defines'):
                file_fp.write(';' + item)
            file_fp.write('"\n')

            file_fp.write('\t\t\t\tStringPooling="true"\n')
            file_fp.write('\t\t\t\tExceptionHandling="0"\n')
            file_fp.write('\t\t\t\tStructMemberAlignment="4"\n')
            file_fp.write('\t\t\t\tEnableFunctionLevelLinking="true"\n')
            file_fp.write('\t\t\t\tFloatingPointModel="2"\n')
            file_fp.write('\t\t\t\tRuntimeTypeInfo="false"\n')
            file_fp.write('\t\t\t\tPrecompiledHeaderFile=""\n')
            # 8 byte alignment
            file_fp.write('\t\t\t\tWarningLevel="4"\n')
            file_fp.write('\t\t\t\tSuppressStartupBanner="true"\n')
            if solution.projects[0].get_attribute(
                    'project_type') == ProjectTypes.library or configuration.attributes['name'] != 'Release':
                file_fp.write('\t\t\t\tDebugInformationFormat="3"\n')
                file_fp.write('\t\t\t\tProgramDataBaseFileName="$(OutDir)$(TargetName).pdb"\n')
            else:
                file_fp.write('\t\t\t\tDebugInformationFormat="0"\n')

            file_fp.write('\t\t\t\tCallingConvention="1"\n')
            file_fp.write('\t\t\t\tCompileAs="2"\n')
            file_fp.write('\t\t\t\tFavorSizeOrSpeed="1"\n')
            # Disable annoying nameless struct warnings since windows headers trigger this
            file_fp.write('\t\t\t\tDisableSpecificWarnings="4201"\n')

            if configuration.attributes['name'] == 'Debug':
                file_fp.write('\t\t\t\tOptimization="0"\n')
            else:
                file_fp.write('\t\t\t\tOptimization="2"\n')
                file_fp.write('\t\t\t\tInlineFunctionExpansion="2"\n')
                file_fp.write('\t\t\t\tEnableIntrinsicFunctions="true"\n')
                file_fp.write('\t\t\t\tOmitFramePointers="true"\n')
            if configuration.attributes['name'] == 'Release':
                file_fp.write('\t\t\t\tBufferSecurityCheck="false"\n')
                file_fp.write('\t\t\t\tRuntimeLibrary="0"\n')
            else:
                file_fp.write('\t\t\t\tBufferSecurityCheck="true"\n')
                file_fp.write('\t\t\t\tRuntimeLibrary="1"\n')

            #
            # Include directories
            #
            file_fp.write('\t\t\t\tAdditionalIncludeDirectories="')
            addcolon = False
            included = includedirectories + solution.projects[0].get_attribute('include_folders')
            if included:
                for item in included:
                    if addcolon is True:
                        file_fp.write(';')
                    file_fp.write(burger.convert_to_windows_slashes(item))
                    addcolon = True
            if platformcode == 'win':
                if addcolon is True:
                    file_fp.write(';')
                if solution.projects[0].get_attribute(
                        'project_type') != ProjectTypes.library or solution.attributes['name'] != 'burgerlib':
                    file_fp.write('$(BURGER_SDKS)\\windows\\burgerlib;')
                file_fp.write('$(BURGER_SDKS)\\windows\\directx9;$(BURGER_SDKS)\\windows\\opengl')
                addcolon = True
            file_fp.write('"\n')
            file_fp.write('\t\t\t/>\n')

            file_fp.write('\t\t\t<Tool\n')
            file_fp.write('\t\t\t\tName="VCResourceCompilerTool"\n')
            file_fp.write('\t\t\t\tCulture="1033"\n')
            file_fp.write('\t\t\t/>\n')

            if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
                file_fp.write('\t\t\t<Tool\n')
                file_fp.write('\t\t\t\tName="VCLibrarianTool"\n')
                file_fp.write(
                    '\t\t\t\tOutputFile="&quot;$(OutDir)' +
                    intdirectory +
                    '.lib&quot;"\n')
                file_fp.write('\t\t\t\tSuppressStartupBanner="true"\n')
                file_fp.write('\t\t\t/>\n')
                if configuration.attributes.get('deploy_folder') is not None:
                    deploy_folder = burger.convert_to_windows_slashes(
                        configuration.attributes.get('deploy_folder'))
                    file_fp.write('\t\t\t<Tool\n')
                    file_fp.write('\t\t\t\tName="VCPostBuildEventTool"\n')
                    file_fp.write(
                        '\t\t\t\tDescription="Copying $(TargetName)$(TargetExt) to '
                        + deploy_folder + '"\n')
                    file_fp.write('\t\t\t\tCommandLine="&quot;$(perforce)\\p4&quot; edit &quot;'
                                  + deploy_folder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
                    file_fp.write('&quot;$(perforce)\\p4&quot; edit &quot;' + deploy_folder
                                  + '$(TargetName).pdb&quot;&#x0D;&#x0A;')
                    file_fp.write('copy /Y &quot;$(OutDir)$(TargetName)$(TargetExt)&quot; &quot;'
                                  + deploy_folder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
                    file_fp.write(
                        'copy /Y &quot;$(OutDir)$(TargetName).pdb&quot; &quot;' +
                        deploy_folder +
                        '$(TargetName).pdb&quot;&#x0D;&#x0A;')
                    file_fp.write('&quot;$(perforce)\\p4&quot; revert -a &quot;' + deploy_folder
                                  + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
                    file_fp.write('&quot;$(perforce)\\p4&quot; revert -a &quot;' + deploy_folder
                                  + '$(TargetName).pdb&quot;&#x0D;&#x0A;"\n')
                    file_fp.write('\t\t\t/>\n')
            else:
                file_fp.write('\t\t\t<Tool\n')
                file_fp.write('\t\t\t\tName="VCLinkerTool"\n')
                file_fp.write(
                    '\t\t\t\tAdditionalDependencies="burgerlib' +
                    solution.ide.get_short_code() +
                    platformcode2 +
                    configuration_short_code(
                        configuration.attributes['name']) +
                    '.lib"\n')
                file_fp.write(
                    '\t\t\t\tOutputFile="&quot;$(OutDir)' +
                    intdirectory +
                    '.exe&quot;"\n')
                file_fp.write('\t\t\t\tAdditionalLibraryDirectories="')
                addcolon = False
                for item in solution.projects[0].get_attribute('include_folders'):
                    if addcolon is True:
                        file_fp.write(';')
                    file_fp.write(burger.convert_to_windows_slashes(item))
                    addcolon = True

                if addcolon is True:
                    file_fp.write(';')
                if solution.projects[0].get_attribute('project_type') != ProjectTypes.library:
                    file_fp.write('$(BURGER_SDKS)\\windows\\burgerlib;')
                file_fp.write('$(BURGER_SDKS)\\windows\\opengl"\n')
                if solution.projects[0].get_attribute('project_type') == ProjectTypes.tool:
                    # main()
                    file_fp.write('\t\t\t\tSubSystem="1"\n')
                else:
                    # WinMain()
                    file_fp.write('\t\t\t\tSubSystem="2"\n')
                file_fp.write('\t\t\t/>\n')
            file_fp.write('\t\t</Configuration>\n')

    file_fp.write('\t</Configurations>\n')

    #
    # Save out the filenames
    #

    alllists = listh + listcpp + listwindowsresource
    if alllists:

        #
        # Create groups first since Visual Studio uses a nested tree structure
        # for file groupings
        #

        groups = dict()
        for item in alllists:
            groupname = item.extractgroupname()
            # Put each filename in its proper group
            if groupname in groups:
                groups[groupname].append(burger.convert_to_windows_slashes(item.filename))
            else:
                # New group!
                groups[groupname] = [burger.convert_to_windows_slashes(item.filename)]

        #
        # Create a recursive tree in order to store out the file list
        #

        file_fp.write('\t<Files>\n')
        tree = dict()
        for group in groups:
            #
            # Get the depth of the tree needed
            #

            parts = group.split('\\')
            nexttree = tree
            #
            # Iterate over every part
            #
            for item, _ in enumerate(parts):
                # Already declared?
                if not parts[item] in nexttree:
                    nexttree[parts[item]] = dict()
                # Step into the tree
                nexttree = nexttree[parts[item]]

        # Use this tree to play back all the data
        dumptreevs2005(2, '', tree, file_fp, groups)
        file_fp.write('\t</Files>\n')

    file_fp.write('</VisualStudioProject>\n')
    file_fp.close()

    return 0


def createvs2008solution(solution):
    """
    Create the solution and project file for visual studio 2008
    """
    error = makeprojects.visualstudio.generateold(solution)
    if error != 0:
        return error
    #
    # Now, let's create the project file
    #

    acceptable = [FileTypes.h, FileTypes.cpp, FileTypes.rc, FileTypes.ico]
    codefiles, includedirectories = solution.getfilelist(acceptable)
    listh = pickfromfilelist(codefiles, FileTypes.h)
    listcpp = pickfromfilelist(codefiles, FileTypes.cpp)
    listwindowsresource = pickfromfilelist(codefiles, FileTypes.rc)

    platformcode = solution.projects[0].get_attribute('platform').get_short_code()
    solutionuuid = str(uuid.uuid3(uuid.NAMESPACE_DNS,
                                  str(solution.visualstudio.outputfilename))).upper()
    projectpathname = os.path.join(solution.attributes['working_directory'],
                                   solution.visualstudio.outputfilename + '.vcproj')
    burger.perforce_edit(projectpathname)
    file_fp = open(projectpathname, 'w')

    #
    # Save off the xml header
    #

    file_fp.write('<?xml version="1.0" encoding="utf-8"?>\n')
    file_fp.write('<VisualStudioProject\n')
    file_fp.write('\tProjectType="Visual C++"\n')
    file_fp.write('\tVersion="9.00"\n')
    file_fp.write('\tName="' + solution.attributes['name'] + '"\n')
    file_fp.write('\tProjectGUID="{' + solutionuuid + '}"\n')
    file_fp.write('\t>\n')

    #
    # Write the project platforms
    #

    file_fp.write('\t<Platforms>\n')
    for vsplatform in solution.projects[0].get_attribute('platform').get_vs_platform():
        file_fp.write('\t\t<Platform Name="' + vsplatform + '" />\n')
    file_fp.write('\t</Platforms>\n')

    #
    # Write the project configurations
    #

    file_fp.write('\t<Configurations>\n')
    for configuration in solution.projects[0].configurations:
        for vsplatform in solution.projects[0].get_attribute('platform').get_vs_platform():
            token = configuration.attributes['name'] + '|' + vsplatform
            file_fp.write('\t\t<Configuration\n')
            file_fp.write('\t\t\tName="' + token + '"\n')
            file_fp.write('\t\t\tOutputDirectory="bin\\"\n')
            if vsplatform == 'x64':
                platformcode2 = 'w64'
            elif vsplatform == 'Win32':
                platformcode2 = 'w32'
            else:
                platformcode2 = platformcode
            intdirectory = solution.attributes['name'] + solution.ide.get_short_code(
            ) + platformcode2 + configuration_short_code(configuration.attributes['name'])
            file_fp.write('\t\t\tIntermediateDirectory="temp\\' + intdirectory + '\\"\n')
            if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
                # Library
                file_fp.write('\t\t\tConfigurationType="4"\n')
            else:
                # Application
                file_fp.write('\t\t\tConfigurationType="1"\n')
            file_fp.write('\t\t\tUseOfMFC="0"\n')
            file_fp.write('\t\t\tATLMinimizesCRunTimeLibraryUsage="false"\n')
            # Unicode
            file_fp.write('\t\t\tCharacterSet="1"\n')
            file_fp.write('\t\t\t>\n')

            file_fp.write('\t\t\t<Tool\n')
            file_fp.write('\t\t\t\tName="VCCLCompilerTool"\n')
            file_fp.write('\t\t\t\tPreprocessorDefinitions="')
            if configuration.attributes['name'] == 'Release':
                file_fp.write('NDEBUG')
            else:
                file_fp.write('_DEBUG')
            if vsplatform == 'x64':
                file_fp.write(';WIN64;_WINDOWS')
            elif vsplatform == 'Win32':
                file_fp.write(';WIN32;_WINDOWS')
            for item in solution.projects[0].get_attribute('defines'):
                file_fp.write(';' + item)
            file_fp.write('"\n')

            file_fp.write('\t\t\t\tStringPooling="true"\n')
            file_fp.write('\t\t\t\tExceptionHandling="0"\n')
            file_fp.write('\t\t\t\tStructMemberAlignment="4"\n')
            file_fp.write('\t\t\t\tEnableFunctionLevelLinking="true"\n')
            file_fp.write('\t\t\t\tFloatingPointModel="2"\n')
            file_fp.write('\t\t\t\tRuntimeTypeInfo="false"\n')
            file_fp.write('\t\t\t\tPrecompiledHeaderFile=""\n')
            # 8 byte alignment
            file_fp.write('\t\t\t\tWarningLevel="4"\n')
            file_fp.write('\t\t\t\tSuppressStartupBanner="true"\n')
            if solution.projects[0].get_attribute(
                    'project_type') == ProjectTypes.library or configuration.attributes['name'] != 'Release':
                file_fp.write('\t\t\t\tDebugInformationFormat="3"\n')
                file_fp.write('\t\t\t\tProgramDataBaseFileName="$(OutDir)$(TargetName).pdb"\n')
            else:
                file_fp.write('\t\t\t\tDebugInformationFormat="0"\n')

            file_fp.write('\t\t\t\tCallingConvention="1"\n')
            file_fp.write('\t\t\t\tCompileAs="2"\n')
            file_fp.write('\t\t\t\tFavorSizeOrSpeed="1"\n')
            # Disable annoying nameless struct warnings since windows headers trigger this
            file_fp.write('\t\t\t\tDisableSpecificWarnings="4201"\n')

            if configuration.attributes['name'] == 'Debug':
                file_fp.write('\t\t\t\tOptimization="0"\n')
                # Necessary to quiet Visual Studio 2008 warnings
                file_fp.write('\t\t\t\tEnableIntrinsicFunctions="true"\n')
            else:
                file_fp.write('\t\t\t\tOptimization="2"\n')
                file_fp.write('\t\t\t\tInlineFunctionExpansion="2"\n')
                file_fp.write('\t\t\t\tEnableIntrinsicFunctions="true"\n')
                file_fp.write('\t\t\t\tOmitFramePointers="true"\n')
            if configuration.attributes['name'] == 'Release':
                file_fp.write('\t\t\t\tBufferSecurityCheck="false"\n')
                file_fp.write('\t\t\t\tRuntimeLibrary="0"\n')
            else:
                file_fp.write('\t\t\t\tBufferSecurityCheck="true"\n')
                file_fp.write('\t\t\t\tRuntimeLibrary="1"\n')

            #
            # Include directories
            #
            file_fp.write('\t\t\t\tAdditionalIncludeDirectories="')
            addcolon = False
            included = includedirectories + solution.projects[0].get_attribute('include_folders')
            if included:
                for item in included:
                    if addcolon is True:
                        file_fp.write(';')
                    file_fp.write(burger.convert_to_windows_slashes(item))
                    addcolon = True
            if platformcode == 'win':
                if addcolon is True:
                    file_fp.write(';')
                if solution.projects[0].get_attribute(
                        'project_type') != ProjectTypes.library or solution.attributes['name'] != 'burgerlib':
                    file_fp.write('$(BURGER_SDKS)\\windows\\burgerlib;')
                file_fp.write('$(BURGER_SDKS)\\windows\\directx9;$(BURGER_SDKS)\\windows\\opengl')
                addcolon = True
            file_fp.write('"\n')
            file_fp.write('\t\t\t/>\n')

            file_fp.write('\t\t\t<Tool\n')
            file_fp.write('\t\t\t\tName="VCResourceCompilerTool"\n')
            file_fp.write('\t\t\t\tCulture="1033"\n')
            file_fp.write('\t\t\t/>\n')

            if solution.projects[0].get_attribute('project_type') == ProjectTypes.library:
                file_fp.write('\t\t\t<Tool\n')
                file_fp.write('\t\t\t\tName="VCLibrarianTool"\n')
                file_fp.write(
                    '\t\t\t\tOutputFile="&quot;$(OutDir)' +
                    intdirectory +
                    '.lib&quot;"\n')
                file_fp.write('\t\t\t\tSuppressStartupBanner="true"\n')
                file_fp.write('\t\t\t/>\n')
                if configuration.attributes.get('deploy_folder')is not None:
                    deploy_folder = burger.convert_to_windows_slashes(
                        configuration.attributes.get('deploy_folder'), True)
                    file_fp.write('\t\t\t<Tool\n')
                    file_fp.write('\t\t\t\tName="VCPostBuildEventTool"\n')
                    file_fp.write(
                        '\t\t\t\tDescription="Copying $(TargetName)$(TargetExt) to '
                        + deploy_folder + '"\n')
                    file_fp.write('\t\t\t\tCommandLine="&quot;$(perforce)\\p4&quot; edit &quot;'
                                  + deploy_folder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
                    file_fp.write('&quot;$(perforce)\\p4&quot; edit &quot;' + deploy_folder
                                  + '$(TargetName).pdb&quot;&#x0D;&#x0A;')
                    file_fp.write('copy /Y &quot;$(OutDir)$(TargetName)$(TargetExt)&quot; &quot;'
                                  + deploy_folder + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
                    file_fp.write(
                        'copy /Y &quot;$(OutDir)$(TargetName).pdb&quot; &quot;' +
                        deploy_folder +
                        '$(TargetName).pdb&quot;&#x0D;&#x0A;')
                    file_fp.write('&quot;$(perforce)\\p4&quot; revert -a &quot;' + deploy_folder
                                  + '$(TargetName)$(TargetExt)&quot;&#x0D;&#x0A;')
                    file_fp.write('&quot;$(perforce)\\p4&quot; revert -a &quot;' + deploy_folder
                                  + '$(TargetName).pdb&quot;&#x0D;&#x0A;"\n')
                    file_fp.write('\t\t\t/>\n')
            else:
                file_fp.write('\t\t\t<Tool\n')
                file_fp.write('\t\t\t\tName="VCLinkerTool"\n')
                file_fp.write(
                    '\t\t\t\tAdditionalDependencies="burgerlib' +
                    solution.ide.get_short_code() +
                    platformcode2 +
                    configuration_short_code(
                        configuration.attributes['name']) +
                    '.lib"\n')
                file_fp.write(
                    '\t\t\t\tOutputFile="&quot;$(OutDir)' +
                    intdirectory +
                    '.exe&quot;"\n')
                file_fp.write('\t\t\t\tAdditionalLibraryDirectories="')
                addcolon = False
                for item in solution.projects[0].get_attribute('include_folders'):
                    if addcolon is True:
                        file_fp.write(';')
                    file_fp.write(burger.convert_to_windows_slashes(item))
                    addcolon = True

                if addcolon is True:
                    file_fp.write(';')
                if solution.projects[0].get_attribute('project_type') != ProjectTypes.library:
                    file_fp.write('$(BURGER_SDKS)\\windows\\burgerlib;')
                file_fp.write('$(BURGER_SDKS)\\windows\\opengl"\n')
                if solution.projects[0].get_attribute('project_type') == ProjectTypes.tool:
                    # main()
                    file_fp.write('\t\t\t\tSubSystem="1"\n')
                else:
                    # WinMain()
                    file_fp.write('\t\t\t\tSubSystem="2"\n')
                file_fp.write('\t\t\t/>\n')
            file_fp.write('\t\t</Configuration>\n')

    file_fp.write('\t</Configurations>\n')

    #
    # Save out the filenames
    #

    alllists = listh + listcpp + listwindowsresource
    if alllists:

        #
        # Create groups first
        #

        groups = dict()
        for item in alllists:
            groupname = item.extractgroupname()
            # Put each filename in its proper group
            if groupname in groups:
                groups[groupname].append(burger.convert_to_windows_slashes(item.filename))
            else:
                # New group!
                groups[groupname] = [burger.convert_to_windows_slashes(item.filename)]

        #
        # Create a recursive tree in order to store out the file list
        #

        file_fp.write('\t<Files>\n')
        tree = dict()
        for group in groups:
            #
            # Get the depth of the tree needed
            #

            parts = group.split('\\')
            nexttree = tree
            #
            # Iterate over every part
            #
            for item, _ in enumerate(parts):
                # Already declared?
                if not parts[item] in nexttree:
                    nexttree[parts[item]] = dict()
                # Step into the tree
                nexttree = nexttree[parts[item]]

        # Use this tree to play back all the data
        dumptreevs2005(2, '', tree, file_fp, groups)
        file_fp.write('\t</Files>\n')

    file_fp.write('</VisualStudioProject>\n')
    file_fp.close()

    return 0
