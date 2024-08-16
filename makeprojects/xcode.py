#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 1995-2024 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

"""
Sub file for makeprojects.
Handler for Apple Computer XCode projects

@package makeprojects.xcode
This module contains classes needed to generate
project files intended for use by Apple's XCode IDE

@var makeprojects.xcode._PBXPROJFILE_MATCH
Regex for matching files with *.pbxproj

@var makeprojects.xcode._XCODEPROJFILE_MATCH
Regex for matching files with *.xcodeproj

@var makeprojects.xcode._XCODE_SUFFIXES
List of filename suffixes for xcode versions

@var makeprojects.xcode.SUPPORTED_IDES
Supported IDE codes for the XCode exporter

@var makeprojects.xcode.OBJECT_VERSIONS
Version values
"""

# pylint: disable=too-many-arguments
# pylint: disable=consider-using-f-string
# pylint: disable=useless-object-inheritance
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name
# pylint: disable=too-many-lines

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys

from re import compile as re_compile
from operator import attrgetter, itemgetter

from burger import create_folder_if_needed, save_text_file_if_newer, \
    convert_to_linux_slashes, PY2, \
    get_mac_host_type, where_is_xcode, run_command
from .enums import FileTypes, ProjectTypes, PlatformTypes, IDETypes, \
    source_file_detect
from .core import SourceFile, Configuration, Project
from .config import _XCODEPROJECT_FILE
from .build_objects import BuildError, BuildObject
from .xcode_utils import get_sdk_root, calcuuid, JSONDict, JSONEntry, \
    JSONArray, JSONObjects, PBXBuildRuleGLSL, PBXFileReference, \
    PBXShellScriptBuildPhase, PBXBuildFile, PBXGroup, PERFORCE_PATH, \
    TEMP_EXE_NAME, copy_tool_to_bin

# Notes for macOS:
# Xcode 3 is the only one that builds PowerPC
# Xcode 3-13 can build x64 and x86
# Xcode 12 and up build x64 and arm64

# Regex to match *.pbxproj files
_PBXPROJFILE_MATCH = re_compile("(?is).*\\.pbxproj\\Z")

# Regex to match *.xcodeproj folders
_XCODEPROJFILE_MATCH = re_compile("(?is).*\\.xcodeproj\\Z")

# Filename suffixes for xcode versions
_XCODE_SUFFIXES = (
    ("xc3", 3), ("xc4", 4), ("xc5", 5),
    ("xc6", 6), ("xc7", 7), ("xc8", 8),
    ("xc9", 9), ("x10", 10), ("x11", 11),
    ("x12", 12), ("x13", 13)
)

# Supported IDE codes for the XCode exporter
SUPPORTED_IDES = (
    IDETypes.xcode3, IDETypes.xcode4, IDETypes.xcode5,
    IDETypes.xcode6, IDETypes.xcode7, IDETypes.xcode8,
    IDETypes.xcode9, IDETypes.xcode10, IDETypes.xcode11,
    IDETypes.xcode12, IDETypes.xcode13, IDETypes.xcode14
)

# Tuple of objectVersion, , compatibilityVersion, developmentRegion
OBJECT_VERSIONS = {
    IDETypes.xcode3: ("45", None, "Xcode 3.1", "English"),
    IDETypes.xcode4: ("46", "0420", "Xcode 3.2", "English"),
    IDETypes.xcode5: ("46", "0510", "Xcode 3.2", "English"),
    IDETypes.xcode6: ("47", "0600", "Xcode 6.3", None),
    IDETypes.xcode7: ("47", "0700", "Xcode 6.3", None),
    IDETypes.xcode8: ("48", "0800", "Xcode 8.0", None),
    # No version 49
    IDETypes.xcode9: ("50", "0900", "Xcode 9.3", None),
    IDETypes.xcode10: ("51", "1030", "Xcode 10.0", None),
    IDETypes.xcode11: ("52", "1100", "Xcode 11.0", None),
    # 53 is 11.4 or higher
    IDETypes.xcode12: ("54", "1200", "Xcode 12.0", None),
    IDETypes.xcode13: ("55", "1300", "Xcode 13.0", None),
    IDETypes.xcode14: ("56", "1400", "Xcode 14.0", None)
}

# Supported input files
SUPPORTED_FILES = (
    FileTypes.icns, FileTypes.h, FileTypes.cpp, FileTypes.c,
    FileTypes.m, FileTypes.mm, FileTypes.ppc, FileTypes.x64,
    FileTypes.x86, FileTypes.arm, FileTypes.arm64,
    FileTypes.frameworks, FileTypes.exe, FileTypes.library,
    FileTypes.glsl
)

########################################


def parse_xcodeproj_file(full_pathname):
    """
    Extract configurations from an XCode project file.

    Given a .xcodeproj directory for XCode for macOS
    locate and extract all of the build targets
    available and return the list.

    Args:
        full_pathname: Pathname to the .xcodeproj folder
    Returns:
        list of configuration strings
    See Also:
        build_xcode
    """

    # Start with an empty list
    targetlist = []

    try:
        if PY2:
            # pylint: disable=unspecified-encoding
            with open(full_pathname, "r") as filep:
                projectfile = filep.read().splitlines()
        else:
            with open(full_pathname, "r", encoding="utf-8") as filep:
                projectfile = filep.read().splitlines()

    except IOError as error:
        print(str(error), file=sys.stderr)
        return targetlist

    configurationfound = False
    for line in projectfile:

        # Look for this section. Immediately after it
        # has the targets
        if configurationfound is False:
            if "buildConfigurations" in line:
                configurationfound = True
        else:
            # Once the end of the section is reached, end
            if ");" in line:
                break
            # Format 1DEB923608733DC60010E9CD /* Debug */,
            # The third entry is the data needed
            targetlist.append(line.rsplit()[2])

    # Exit with the results
    return targetlist

########################################


class BuildXCodeFile(BuildObject):
    """
    Class to build Apple XCode files

    Attributes:
        verbose: The verbose flag
    """

    def __init__(self, file_name, priority, configuration,
                 verbose=False):
        """
        Class to handle XCode files

        Args:
            file_name: Pathname to the *.xcodeproj to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
        """

        super().__init__(file_name, priority, configuration=configuration)
        self.verbose = verbose

    ########################################

    def build_clean(self, build=True):
        """
        Build a macOS XCode file.

        Supports .xcodeproj files from Xcode 3 and later.

        Returns:
            List of BuildError objects
        See Also:
            parse_xcodeproj_file
        """

        # Get the list of build targets
        file_dir_name = os.path.dirname(self.file_name)
        file_name_lower = file_dir_name.lower()

        for item in _XCODE_SUFFIXES:
            if item[0] in file_name_lower:
                version = item[1]
                break
        else:
            version = None

        # Find XCode for the version needed
        xcode = where_is_xcode(version)

        # Is this version of XCode installed?
        if not xcode or not os.path.isfile(xcode[0]):
            msg = ("Can't build {}, the proper version "
                "of XCode is not installed").format(file_dir_name)
            print(msg)
            return BuildError(0, file_dir_name,
                            msg=msg)

        xcodebuild = xcode[0]
        # Create the build command
        cmd = [
            xcodebuild,
            "-project",
            os.path.basename(file_dir_name),
            "-alltargets",
            "-parallelizeTargets",
            "-configuration",
            self.configuration]

        # Issue a build or a clean command
        if build:
            cmd.append("build")
        else:
            cmd.append("clean")

        if self.verbose:
            print(" ".join(cmd))

        try:
            error_code = run_command(
                cmd, working_dir=os.path.dirname(file_dir_name),
                quiet=not self.verbose)[0]
            msg = None
        except OSError as error:
            error_code = getattr(error, "winerror", error.errno)
            msg = str(error)
            print(msg, file=sys.stderr)

        return BuildError(
            error_code,
            file_dir_name,
            configuration=self.configuration)

    ########################################

    def build(self):
        """
        Build a macOS XCode file.

        Supports .xcodeproj files from Xcode 3 and later.

        Returns:
            List of BuildError objects
        See Also:
            parse_xcodeproj_file
        """

        return self.build_clean(True)

    ########################################

    def clean(self):
        """
        Delete temporary files.

        This function is called by ``cleanme`` to remove temporary files.

        On exit, return 0 for no error, or a non zero error code if there was an
        error to report. None if not implemented or not applicable.

        Returns:
            None if not implemented, otherwise an integer error code.
        """

        return self.build_clean(False)


########################################


def match(filename):
    """
    Check if the filename is a type that this module supports

    Args:
        filename: Filename to match
    Returns:
        False if not a match, True if supported
    """

    if _PBXPROJFILE_MATCH.match(filename):
        return True
    return _XCODEPROJFILE_MATCH.match(filename)

########################################


def create_build_object(file_name, priority=50,
                 configurations=None, verbose=False):
    """
    Create BuildXCodeFile build records for every desired configuration

    Args:
        file_name: Pathname to the *.pbxproj to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output

    Returns:
        list of BuildXCodeFile classes
    """

    # Don't build if not running on macOS
    if not get_mac_host_type():
        if verbose:
            print("{} can only be built on macOS hosts".format(file_name))
        return []

    # If it's the directory, convert to project filename
    if _XCODEPROJFILE_MATCH.match(file_name):
        file_name = os.path.join(file_name, _XCODEPROJECT_FILE)

    targetlist = parse_xcodeproj_file(file_name)

    # Was the file corrupted?
    if not targetlist:
        print(file_name + " is corrupt!")
        return []

    results = []
    for target in targetlist:
        if configurations:
            if target not in configurations:
                continue
        results.append(
            BuildXCodeFile(file_name, priority, target, verbose))

    return results

########################################


def create_clean_object(file_name, priority=50,
                 configurations=None, verbose=False):
    """
    Create BuildXCodeFile build records for every desired configuration

    Args:
        file_name: Pathname to the *.pbxproj to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output
    Returns:
        list of BuildXCodeFile classes
    """

    # Don't build if not running on macOS
    if not get_mac_host_type():
        if verbose:
            print("{} can only be built on macOS hosts".format(file_name))
        return []

    # If it's the directory, convert to project filename
    if _XCODEPROJFILE_MATCH.match(file_name):
        file_name = os.path.join(file_name, _XCODEPROJECT_FILE)

    targetlist = parse_xcodeproj_file(file_name)

    # Was the file corrupted?
    if not targetlist:
        print(file_name + " is corrupt!")
        return []

    results = []
    for target in targetlist:
        if configurations:
            if target not in configurations:
                continue

        results.append(
            BuildXCodeFile(file_name, priority, target, verbose))

    return results

########################################


def test(ide, platform_type):
    """ Filter for supported platforms

    Args:
        ide: IDETypes
        platform_type: PlatformTypes
    Returns:
        True if supported, False if not
    """

    # pylint: disable=unused-argument
    return platform_type in (
        PlatformTypes.macosxintel32, PlatformTypes.macosxintel64,
        PlatformTypes.macosxppc32, PlatformTypes.macosxppc64,
        PlatformTypes.macosxarm64,
        PlatformTypes.ios32, PlatformTypes.ios64,
        PlatformTypes.iosemu32, PlatformTypes.iosemu64)

########################################


def add_XCBuildConfiguration(build_settings, configuration):
    """
    Update the settings for a XCBuildConfiguration

    Args:
        build_settings: List of build settings
        configuration: Configuration to use
    """

    # pylint: disable=protected-access

    ide = configuration.ide
    solution = configuration.project.solution

    # Xcode 13 and higher (ARM), requires code signing
    if ide >= IDETypes.xcode13:
        build_settings.add_dict_entry(
            "CODE_SIGN_IDENTITY", "-")
        build_settings.add_dict_entry(
            "CODE_SIGN_IDENTITY[sdk=macosx*]", "Apple Development")
        build_settings.add_dict_entry(
            "CODE_SIGN_STYLE", "Automatic")
        build_settings.add_dict_entry(
            "CONFIGURATION_BUILD_DIR", "$(SYMROOT)/$(PRODUCT_NAME)$(SUFFIX)")
        build_settings.add_dict_entry(
            "CONFIGURATION_TEMP_DIR", "$(SYMROOT)/$(PRODUCT_NAME)$(SUFFIX)")
        build_settings.add_dict_entry(
            "DEVELOPMENT_TEAM", "SK433TW842")
        build_settings.add_dict_entry(
            "PROVISIONING_PROFILE_SPECIFIER", "")

    # Set the default SDKROOT
    build_settings.add_dict_entry("SDKROOT", solution._xc_sdkroot)

    # Only add for Xcode 3, since Xcode 4 and higher doesn't support PPC
    if configuration.platform.is_macosx() and ide < IDETypes.xcode4:
        build_settings.add_dict_entry(
            "SDKROOT[arch=ppc64]", "macosx10.5")
        build_settings.add_dict_entry(
            "SDKROOT[arch=ppc]", "macosx10.5")

    if ide >= IDETypes.xcode13:
        build_settings.add_dict_entry(
            "SUFFIX",
            solution.ide_code +
            solution.platform_code +
            configuration.short_code)


########################################


class PBXContainerItemProxy(JSONDict):
    """
    Each PBXContainerItemProxy entry

    Attributes:
        native_target: PBXNativeTarget to build.
    """

    def __init__(self, native_target, project_uuid):
        """
        Initialize a PBXContainerItemProxy record.

        Args:
            native_target: Parent PBXNativeTarget
            project_uuid: Parent uuid
        """

        # Sanity check
        if not isinstance(native_target, PBXNativeTarget):
            raise TypeError(
                "parameter \"native_target\" must be of type PBXNativeTarget")

        uuid = calcuuid("PBXContainerItemProxy" + native_target.target_name)
        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXContainerItemProxy",
            comment="PBXContainerItemProxy",
            uuid=uuid)
        self.add_item(
            JSONEntry(
                name="containerPortal",
                value=project_uuid,
                comment="Project object"))
        self.add_item(JSONEntry(name="proxyType", value="1"))
        self.add_item(
            JSONEntry(
                name="remoteGlobalIDString",
                value=native_target.uuid))
        self.add_item(
            JSONEntry(
                name="remoteInfo",
                value="\"{}\"".format(
                    native_target.target_name)))

        # PBXNativeTarget to build.
        self.native_target = native_target

########################################


class PBXFrameworksBuildPhase(JSONDict):
    """
    Each PBXFrameworksBuildPhase entry

    Attributes:
        files: JSONArray of PBXBuildFile records
    """

    def __init__(self, file_reference):
        """
        Initialize PBXFrameworksBuildPhase
        Args:
            file_reference: PBXFileReference record
        """

        # Sanity check
        if not isinstance(file_reference, PBXFileReference):
            raise TypeError(
                "parameter \"file_reference\" must be of type PBXFileReference")

        uuid = calcuuid(
            "PBXFrameworksBuildPhase" +
            file_reference.relative_pathname)

        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXFrameworksBuildPhase",
            comment="Frameworks",
            uuid=uuid)

        self.add_item(JSONEntry(name="buildActionMask", value="2147483647"))

        files = JSONArray(name="files")
        self.add_item(files)

        self.add_item(
            JSONEntry(
                name="runOnlyForDeploymentPostprocessing",
                value="0"))

        # JSONArray of PBXBuildFile records
        self.files = files

    def add_build_file(self, build_file):
        """
        Add a framework to the files record

        Args:
            build_file: PBXBuildFile record
        """

        # Sanity check
        if not isinstance(build_file, PBXBuildFile):
            raise TypeError(
                "parameter \"build_file\" must be of type PBXBuildFile")

        self.files.add_item(
            JSONEntry(
                build_file.uuid,
                comment=os.path.basename(
                    build_file.file_reference.relative_pathname) +
                " in Frameworks", suffix=","))

    @staticmethod
    def get_phase_name():
        """
        Return the build phase name for XCode.
        """
        return "Frameworks"


########################################


class PBXNativeTarget(JSONDict):
    """
    Each PBXNative entry

    Attributes:
        parent: Objects record (Parent)
        target_name: Name of the target
        build_config_list: JSONEntry of configurations
        build_phases: JSONArray of build phases
        build_rules: JSONArray of build rules
        dependencies: JSONArray of dependencies
    """

    def __init__(self, parent, name, productreference,
                 productname, producttype, build_rules):
        """
        Init PBXNativeTarget

        Args:
            parent: Parent object
            name: Name of the Native target
            productreference: Reference to the object being built
            productname: Name of the project being built
            producttype: Type of product being built
        """

        uuid = calcuuid("PBXNativeTarget" + name)
        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXNativeTarget",
            comment=name,
            uuid=uuid)

        self.build_config_list = JSONEntry(
            "buildConfigurationList",
            comment=(
                "Build configuration list "
                "for PBXNativeTarget \"{}\"").format(name),
            enabled=False)
        self.add_item(self.build_config_list)

        self.build_phases = JSONArray("buildPhases")
        self.add_item(self.build_phases)

        self.build_rules = JSONArray("buildRules")
        self.add_item(self.build_rules)
        for item in build_rules:
            self.build_rules.add_array_entry(
                item.name).comment = "PBXBuildRule"

        self.dependencies = JSONArray("dependencies")
        self.add_item(self.dependencies)

        self.add_item(JSONEntry("name", value=name))
        self.add_item(JSONEntry("productName", value=productname))

        self.add_item(
            JSONEntry(
                "productReference",
                value=productreference.uuid,
                comment=productreference.relative_pathname))

        self.add_item(
            JSONEntry(
                "productType",
                value=producttype))

        self.parent = parent
        self.target_name = name

    def add_build_phase(self, build_phase):
        """
        Append a Buildphase target

        Args:
            build_phase: Build phase object
        """

        self.build_phases.add_item(
            JSONEntry(
                build_phase.uuid,
                comment=build_phase.get_phase_name(),
                suffix=","))

    def add_dependency(self, target_dependency):
        """
        Append a dependency.

        Args:
            target_dependency: Target to depend on.
        """

        self.dependencies.add_item(
            JSONEntry(
                target_dependency.uuid,
                comment=target_dependency.isa,
                suffix=","))

    def set_config_list(self, config_list_reference):
        """
        Attach a configuration list.
        """
        self.build_config_list.value = config_list_reference.uuid
        self.build_config_list.enabled = True

    def generate(self, line_list, indent=0):
        """
        Write this record to output
        """

        return JSONDict.generate(self, line_list, indent)

########################################


class PBXProject(JSONDict):
    """
    Each PBXProject entry

    Attributes:
        build_config_list: List of build configurations
        main_group: JSONEntry of the main group
        targets: JSONArray of the targets
    """

    def __init__(self, uuid, solution):
        """
        Init PBXProject

        Args:
            uuid: Unique UUID
            solution: Parent solution
        """
        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXProject",
            comment="Project object",
            uuid=uuid)

        # Look up versioning information
        object_versions = OBJECT_VERSIONS.get(solution.ide)

        # Attributes record
        attributes = JSONDict("attributes")
        self.add_item(attributes)

        attributes.add_item(
            JSONEntry(
                "BuildIndependentTargetsInParallel",
                value="YES"))

        upgrade = object_versions[1]
        attributes.add_item(
            JSONEntry(
                "LastUpgradeCheck",
                value=upgrade, enabled=upgrade is not None))

        self.build_config_list = JSONEntry(
            "buildConfigurationList",
            comment=(
                "Build configuration list "
                "for PBXProject \"{}\""
            ).format(solution.name), enabled=False)
        self.add_item(self.build_config_list)

        self.add_item(
            JSONEntry(
                "compatibilityVersion",
                value=object_versions[2]))

        self.add_item(
            JSONEntry(
                "developmentRegion",
                value=object_versions[3],
                enabled=object_versions[3] is not None))

        ide = solution.ide
        if ide >= IDETypes.xcode12:
            self.add_item(
                JSONEntry("developmentRegion", value="en"))

        self.add_item(JSONEntry("hasScannedForEncodings", value="1"))

        known_regions = JSONArray("knownRegions")
        self.add_item(known_regions)
        known_regions.add_array_entry("en")

        self.main_group = JSONEntry("mainGroup", enabled=False)
        self.add_item(self.main_group)

        self.add_item(JSONEntry("projectDirPath", value=""))
        self.add_item(JSONEntry("projectRoot", value=""))

        self.targets = JSONArray("targets")
        self.add_item(self.targets)

    def append_target(self, item):
        """
        Append a PBXNative target
        """

        self.targets.add_item(
            JSONEntry(
                item.uuid,
                comment=item.target_name,
                suffix=","))

    def set_config_list(self, config_list_reference):
        """
        Attach a configuration list.
        """
        self.build_config_list.value = config_list_reference.uuid
        self.build_config_list.enabled = True

    def set_root_group(self, rootgroup):
        """
        Set the root group.
        """
        self.main_group.value = rootgroup.uuid
        self.main_group.comment = rootgroup.group_name
        self.main_group.enabled = True


########################################


class PBXSourcesBuildPhase(JSONDict):
    """
    Each PBXSourcesBuildPhase entry

    Attributes:
        files: JSONArray of files
        owner: Owner object
        buildfirstlist: List of files to build first
        buildlist: List of file to build later
    """

    def __init__(self, owner):
        """
        Init PBXSourcesBuildPhase

        Args:
            owner: Parent object
        """
        uuid = calcuuid(
            "PBXSourcesBuildPhase" +
            owner.relative_pathname)
        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXSourcesBuildPhase",
            comment="Sources",
            uuid=uuid)

        self.add_item(JSONEntry("buildActionMask", value="2147483647"))
        files = JSONArray("files")
        self.files = files
        self.add_item(files)
        self.add_item(
            JSONEntry(
                "runOnlyForDeploymentPostprocessing",
                value="0"))
        self.owner = owner
        self.buildfirstlist = []
        self.buildlist = []

    def append_file(self, item):
        """
        Append a file uuid and name to the end of the list
        """

        if item.file_reference.source_file.type == FileTypes.glsl:
            self.buildfirstlist.append([item, os.path.basename(
                item.file_reference.relative_pathname)])
        else:
            self.buildlist.append([item, os.path.basename(
                item.file_reference.relative_pathname)])

    @staticmethod
    def get_phase_name():
        """
        Return the build phase name for XCode.
        """
        return "Sources"

    def generate(self, line_list, indent=0):
        """
        Write this record to output
        """

        self.buildfirstlist = sorted(
            self.buildfirstlist, key=itemgetter(1))
        self.buildlist = sorted(
            self.buildlist, key=itemgetter(1))
        for item in self.buildfirstlist:
            self.files.add_item(
                JSONEntry(
                    item[0].uuid,
                    comment="{} in Sources".format(
                        item[1]), suffix=","))

        for item in self.buildlist:
            self.files.add_item(
                JSONEntry(
                    item[0].uuid,
                    comment="{} in Sources".format(
                        item[1]), suffix=","))
        return JSONDict.generate(self, line_list, indent)


########################################


class PBXTargetDependency(JSONDict):
    """
    Each PBXTargetDependency entry
    """

    def __init__(self, proxy, nativetarget):
        """
        Init PBXTargetDependency

        Args:
            proxy: target proxy
            nativetarget: Native target
        """
        uuid = calcuuid(
            "PBXTargetDependency" +
            proxy.native_target.target_name +
            nativetarget.target_name)
        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXTargetDependency",
            comment="PBXTargetDependency",
            uuid=uuid)

        self.add_item(
            JSONEntry(
                "target",
                value=nativetarget.uuid,
                comment=nativetarget.target_name))
        self.add_item(
            JSONEntry(
                "targetProxy",
                value=proxy.uuid,
                comment="PBXContainerItemProxy"))

########################################


class XCBuildConfiguration(JSONDict):
    """
    Each XCBuildConfiguration entry

    Attributes:
        build_settings: JSONDict of build settings
        configuration: Parent configuration
    """

    def __init__(self, configuration, configfilereference, owner,
                 installpath):
        """
        Initialize a XCBuildConfiguration object.

        Args:
            configuration: Configuration
            configfilereference: Reference to a config file
            owner: Owner object
            installpath: Path to install the final product
        """

        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        if not isinstance(configuration, Configuration):
            raise TypeError(
                "parameter \"configuration\" must be of type Configuration")

        self.configuration = configuration
        ide = configuration.ide
        project = configuration.project
        solution = project.solution

        uuid = calcuuid("XCBuildConfiguration" +
                        owner.pbxtype + owner.targetname + configuration.name)
        JSONDict.__init__(
            self,
            name=uuid,
            isa="XCBuildConfiguration",
            comment=configuration.name,
            uuid=uuid)

        # Was there a configuration file?
        if configfilereference is not None:
            self.add_dict_entry(
                "baseConfigurationReference",
                configfilereference.uuid).comment = os.path.basename(
                configfilereference.filename)

        build_settings = JSONDict("buildSettings")
        self.add_item(build_settings)
        self.build_settings = build_settings

        if installpath:
            build_settings.add_dict_entry(
                "INSTALL_PATH", "\"$(HOME)/Applications\"")

        if (ide < IDETypes.xcode4 and owner.pbxtype == "PBXProject") or \
                (ide >= IDETypes.xcode4 and owner.pbxtype != "PBXProject"):

            add_XCBuildConfiguration(build_settings, configuration)

        if owner.pbxtype == "PBXProject":

            # Locations of any sparse SDKs
            # build_settings.add_dict_entry("ADDITIONAL_SDKS")

            # Group permission of deployment
            # build_settings.add_dict_entry("ALTERNATE_GROUP")

            # File permissions of deployment
            # build_settings.add_dict_entry("ALTERNATE_MODE")

            # Owner permission of deployment
            # build_settings.add_dict_entry("ALTERNATE_OWNER")

            # Specific files to apply deployment permissions
            # build_settings.add_dict_entry("ALTERNATE_PERMISSIONS_FILES")

            # Always search user paths in C++ (Hard code)
            build_settings.add_dict_entry("ALWAYS_SEARCH_USER_PATHS", "NO")

            # Copy Files Build Phase will plist and strings to encoding
            # build_settings.add_dict_entry("APPLY_RULES_IN_COPY_FILES")

            # Default CPUs
            temp_array = JSONArray(
                "ARCHS", disable_if_empty=True, fold_array=True)
            build_settings.add_item(temp_array)
            self.fixup_archs(temp_array)

            # List of build variants
            temp_array = JSONArray(
                "BUILD_VARIANTS", disable_if_empty=True, fold_array=True)
            build_settings.add_item(temp_array)

            # Name of executable that loads the bundle
            # build_settings.add_dict_entry("BUNDLE_LOADER")

            # Xcode 14 has C++20, use it
            if ide >= IDETypes.xcode14:
                build_settings.add_dict_entry(
                    "CLANG_CXX_LANGUAGE_STANDARD", "gnu++20")

            # Name of the code signing certificate
            # build_settings.add_dict_entry("CODE_SIGN_IDENTITY")

            # Path to property list containing rules for signing
            # build_settings.add_dict_entry("CODE_SIGN_RESOURCE_RULES_PATH")

            # Path for build products
            if ide < IDETypes.xcode13:
                build_settings.add_dict_entry(
                    "CONFIGURATION_BUILD_DIR",
                    "$(SYMROOT)/$(PRODUCT_NAME)$(SUFFIX)")

                # Path for temp files
                build_settings.add_dict_entry(
                    "CONFIGURATION_TEMP_DIR",
                    "$(SYMROOT)/$(PRODUCT_NAME)$(SUFFIX)")

            # Does copying preserve classic mac resource forks?
            # build_settings.add_dict_entry("COPYING_PRESERVES_HFS_DATA")

            # Strip debug symbols?
            # build_settings.add_dict_entry("COPY_PHASE_STRIP")

            # Numeric project version
            # build_settings.add_dict_entry("CURRENT_PROJECT_VERSION")

            # Strip dead code?
            build_settings.add_dict_entry("DEAD_CODE_STRIPPING", "YES")

            # Type of debug symbols (Use dwarf)
            build_settings.add_dict_entry("DEBUG_INFORMATION_FORMAT", "dwarf")

            # Are there valid deployment location settings?
            # build_settings.add_dict_entry("DEPLOYMENT_LOCATION")

            # Process deployment files
            # build_settings.add_dict_entry("DEPLOYMENT_POSTPROCESSING")

            # Destination root folder for deployment
            # build_settings.add_dict_entry("DSTROOT")

            # Compatible version of the dynamic library
            # build_settings.add_dict_entry("DYLIB_COMPATIBILITY_VERSION")

            # Numeric version of the dynamic library
            # build_settings.add_dict_entry("DYLIB_CURRENT_VERSION")

            # Enable OpenMP
            # build_settings.add_dict_entry("ENABLE_OPENMP_SUPPORT")

            # Files and folders to ignore on search.
            # build_settings.add_dict_entry(
            #   "EXCLUDED_RECURSIVE_SEARCH_PATH_SUBDIRECTORIES")

            # Extension for executables
            # build_settings.add_dict_entry("EXECUTABLE_EXTENSION")

            # Prefix for executables
            # build_settings.add_dict_entry("EXECUTABLE_PREFIX")

            # File with symbols to export
            # build_settings.add_dict_entry("EXPORTED_SYMBOLS_FILE")

            # Array of directories to search for Frameworks
            # build_settings.add_dict_entry("FRAMEWORK_SEARCH_PATHS")

            # Version of the framework being generated
            # build_settings.add_dict_entry("FRAMEWORK_VERSION")

            # PowerPC only, enable altivec
            # build_settings.add_dict_entry("GCC_ALTIVEC_EXTENSIONS")

            # Enable vectorization on loops
            # build_settings.add_dict_entry("GCC_AUTO_VECTORIZATION")

            # Default "char" to unsigned if set to true
            # build_settings.add_dict_entry("GCC_CHAR_IS_UNSIGNED_CHAR")

            # It true, assume no exceptions on new()
            # build_settings.add_dict_entry(
            #   "GCC_CHECK_RETURN_VALUE_OF_OPERATOR_NEW")

            # Use CodeWarrior inline assembly syntax
            build_settings.add_dict_entry("GCC_CW_ASM_SYNTAX", "YES")

            # Use the latest version of the Objective C++ dialect
            item = "gnu99" if ide < IDETypes.xcode10 else "gnu11"
            build_settings.add_dict_entry("GCC_C_LANGUAGE_STANDARD", item)

            # Sets the level of debugging symbols in the output
            # build_settings.add_dict_entry("GCC_DEBUGGING_SYMBOLS")

            # Set YES for no relocatable code (NO is default)
            if configuration.project_type is not ProjectTypes.sharedlibrary:
                if ide < IDETypes.xcode12:
                    build_settings.add_dict_entry("GCC_DYNAMIC_NO_PIC", "NO")
                    build_settings.add_dict_entry(
                        "GCC_DYNAMIC_NO_PIC[arch=i386]", "YES")
                    if ide < IDETypes.xcode4:
                        build_settings.add_dict_entry(
                            "GCC_DYNAMIC_NO_PIC[arch=ppc64]", "YES")
                        build_settings.add_dict_entry(
                            "GCC_DYNAMIC_NO_PIC[arch=ppc]", "YES")

            # Enable the asm keyword
            # build_settings.add_dict_entry("GCC_ENABLE_ASM_KEYWORD")

            # Enable built in functions like memcpy().
            # build_settings.add_dict_entry("GCC_ENABLE_BUILTIN_FUNCTIONS")

            # Disable CPP Exceptionsstaticlib
            item = "YES" if configuration.exceptions else "NO"
            build_settings.add_dict_entry("GCC_ENABLE_CPP_EXCEPTIONS", item)

            # Disable CPP RTTI
            build_settings.add_dict_entry("GCC_ENABLE_CPP_RTTI", "NO")

            # Build everything as Objective C++
            # build_settings.add_dict_entry("GCC_INPUT_FILETYPE")

            # Program flow for profiling.
            # build_settings.add_dict_entry("GCC_INSTRUMENT_PROGRAM_FLOW_ARCS")

            # Link with static to dynamic libraries
            # build_settings.add_dict_entry("GCC_LINK_WITH_DYNAMIC_LIBRARIES")

            # Enable 64 bit registers for powerpc 64 bit
            if ide < IDETypes.xcode4:
                build_settings.add_dict_entry(
                    "GCC_MODEL_PPC64", "NO")
                build_settings.add_dict_entry(
                    "GCC_MODEL_PPC64[arch=ppc64]", "YES")

            # Tune for specific cpu
            if ide < IDETypes.xcode4:
                build_settings.add_dict_entry(
                    "GCC_MODEL_TUNING", "G4")
                build_settings.add_dict_entry(
                    "GCC_MODEL_TUNING[arch=ppc64]", "G5")

            # Don't share global variables
            # build_settings.add_dict_entry("GCC_NO_COMMON_BLOCKS")

            # Call C++ constuctors on objective-c code
            # build_settings.add_dict_entry("GCC_OBJC_CALL_CXX_CDTORS")

            # bool takes one byte, not 4
            # build_settings.add_dict_entry("GCC_ONE_BYTE_BOOL")

            # Optimizations level
            item = "s" if configuration.optimization else "0"
            build_settings.add_dict_entry("GCC_OPTIMIZATION_LEVEL", item)

            # C++ dialects
            # build_settings.add_dict_entry("GCC_PFE_FILE_C_DIALECTS")

            # Use a precompiled header
            # build_settings.add_dict_entry("GCC_PRECOMPILE_PREFIX_HEADER")

            # Name of the precompiled header
            # build_settings.add_dict_entry("GCC_PREFIX_HEADER")

            # Set defines
            temp_array = JSONArray("GCC_PREPROCESSOR_DEFINITIONS",
                             disable_if_empty=True, fold_array=True)
            build_settings.add_item(temp_array)
            for item in configuration.get_chained_list("define_list"):
                temp_array.add_array_entry(item)

            # Disabled defines
            # build_settings.add_dict_entry(
            #   "GCC_PREPROCESSOR_DEFINITIONS_NOT_USED_IN_PRECOMPS")

            # Reuse constant strings
            # build_settings.add_dict_entry("GCC_REUSE_STRINGS")

            # Shorten enums
            # build_settings.add_dict_entry("GCC_SHORT_ENUMS")

            # Use strict aliasing
            # build_settings.add_dict_entry("GCC_STRICT_ALIASING")

            # Assume extern symbols are private
            # build_settings.add_dict_entry("GCC_SYMBOLS_PRIVATE_EXTERN")

            # Don't emit code to make the static constructors thread safe
            build_settings.add_dict_entry("GCC_THREADSAFE_STATICS", "NO")

            # Causes warnings about missing function prototypes to become errors
            # build_settings.add_dict_entry(
            #   "GCC_TREAT_IMPLICIT_FUNCTION_DECLARATIONS_AS_ERRORS")

            # Non conformant code errors become warnings.
            # build_settings.add_dict_entry(
            #   "GCC_TREAT_NONCONFORMANT_CODE_ERRORS_AS_WARNINGS")

            # Warnings are errors
            # build_settings.add_dict_entry("GCC_TREAT_WARNINGS_AS_ERRORS")

            # Enable unrolling loops
            # build_settings.add_dict_entry("GCC_UNROLL_LOOPS")

            # Allow native prcompiling support
            # build_settings.add_dict_entry("GCC_USE_GCC3_PFE_SUPPORT")

            # Default to using a register for all function calls
            # build_settings.add_dict_entry("GCC_USE_INDIRECT_FUNCTION_CALLS")

            # Default to long calls
            # build_settings.add_dict_entry("GCC_USE_REGISTER_FUNCTION_CALLS")

            # Allow searching default system include folders.
            # build_settings.add_dict_entry(
            #   "GCC_USE_STANDARD_INCLUDE_SEARCHING")

            # Which compiler to use
            if ide < IDETypes.xcode4 and configuration.platform.is_macosx():
                build_settings.add_dict_entry("GCC_VERSION", "")

                # Note: com.apple.compilers.llvmgcc42 generates BAD CODE for
                # ppc64 and 4.2 doesn't work at all for ppc64. Only gcc 4.0 is
                # safe for ppc64 i386 compiler llvmgcc42 has issues with 64 bit
                # code in xcode3
                build_settings.add_dict_entry("GCC_VERSION[arch=ppc64]", "4.0")
                build_settings.add_dict_entry("GCC_VERSION[arch=ppc]", "4.0")

            # Warn of 64 bit value become 32 bit automatically
            build_settings.add_dict_entry(
                "GCC_WARN_64_TO_32_BIT_CONVERSION", "YES")

            # Warn about deprecated functions
            # build_settings.add_dict_entry(
            #   "GCC_WARN_ABOUT_DEPRECATED_FUNCTIONS")

            # Warn about invalid use of offsetof()
            # build_settings.add_dict_entry(
            #   "GCC_WARN_ABOUT_INVALID_OFFSETOF_MACRO")

            # Warn about missing ending newline in source code.
            # build_settings.add_dict_entry("GCC_WARN_ABOUT_MISSING_NEWLINE")

            # Warn about missing function prototypes
            build_settings.add_dict_entry(
                "GCC_WARN_ABOUT_MISSING_PROTOTYPES", "YES")

            # Warn if the sign of a pointer changed.
            build_settings.add_dict_entry(
                "GCC_WARN_ABOUT_POINTER_SIGNEDNESS", "YES")

            # Warn if return type is missing a value.
            build_settings.add_dict_entry("GCC_WARN_ABOUT_RETURN_TYPE", "YES")

            # Objective-C Warn if required methods are missing in class
            # implementation
            build_settings.add_dict_entry(
                "GCC_WARN_ALLOW_INCOMPLETE_PROTOCOL", "YES")

            # Warn if a switch statement is missing enumeration entries
            build_settings.add_dict_entry(
                "GCC_WARN_CHECK_SWITCH_STATEMENTS", "YES")

            # Warn if Effective C++ violations are present.
            # build_settings.add_dict_entry(
            #   "GCC_WARN_EFFECTIVE_CPLUSPLUS_VIOLATIONS")

            # Warn is macOS stype "APPL" 4 character constants exist.
            # build_settings.add_dict_entry("GCC_WARN_FOUR_CHARACTER_CONSTANTS")

            # Warn if virtual functions become hidden.
            build_settings.add_dict_entry(
                "GCC_WARN_HIDDEN_VIRTUAL_FUNCTIONS", "YES")

            # Disable all warnings.
            # build_settings.add_dict_entry("GCC_WARN_INHIBIT_ALL_WARNINGS")

            # Warn if union initializers are not fully bracketed.
            build_settings.add_dict_entry(
                "GCC_WARN_INITIALIZER_NOT_FULLY_BRACKETED", "NO")

            # Warn if parentheses are missing from nested statements.
            build_settings.add_dict_entry(
                "GCC_WARN_MISSING_PARENTHESES", "YES")

            # Warn if a class didn't declare its destructor as virtual if
            # derived.
            build_settings.add_dict_entry(
                "GCC_WARN_NON_VIRTUAL_DESTRUCTOR", "YES")

            # Warn if non-C++ standard keywords are used
            # build_settings.add_dict_entry("GCC_WARN_PEDANTIC")

            # Warn if implict type conversions occur.
            if ide < IDETypes.xcode12:
                build_settings.add_dict_entry(
                    "GCC_WARN_PROTOTYPE_CONVERSION", "YES")

            # Warn if a variable becomes shadowed.
            build_settings.add_dict_entry("GCC_WARN_SHADOW", "YES")

            # Warn if signed and unsigned values are compared.
            # build_settings.add_dict_entry("GCC_WARN_SIGN_COMPARE")

            # Validate printf() and scanf().
            build_settings.add_dict_entry(
                "GCC_WARN_TYPECHECK_CALLS_TO_PRINTF", "YES")

            # Warn if a variable is clobbered by setjmp() or not initialized.
            # Warn on autos is spurious for Debug builds
            item = "YES" if configuration.optimization else "NO"
            build_settings.add_dict_entry("GCC_WARN_UNINITIALIZED_AUTOS", item)

            # Warn if a pragma is used that"s not know by this compiler.
            # build_settings.add_dict_entry("GCC_WARN_UNKNOWN_PRAGMAS")

            # Warn if a static function is never used.
            build_settings.add_dict_entry("GCC_WARN_UNUSED_FUNCTION", "YES")

            # Warn if a label is declared but not used.
            build_settings.add_dict_entry("GCC_WARN_UNUSED_LABEL", "YES")

            # Warn if a function parameter isn"t used.
            build_settings.add_dict_entry("GCC_WARN_UNUSED_PARAMETER", "YES")

            # Warn if a value isn't used.
            build_settings.add_dict_entry("GCC_WARN_UNUSED_VALUE", "YES")

            # Warn if a variable isn't used.
            build_settings.add_dict_entry("GCC_WARN_UNUSED_VARIABLE", "YES")

            # Merge object files into a single file (static libraries)
            # build_settings.add_dict_entry("GENERATE_MASTER_OBJECT_FILE")

            # Force generating a package information file
            # build_settings.add_dict_entry("GENERATE_PKGINFO_FILE")

            # Insert profiling code
            item = "YES" if configuration.get_chained_value(
                "profile") else "NO"
            build_settings.add_dict_entry("GENERATE_PROFILING_CODE", item)

            # List of search paths for headers
            temp_array = JSONArray("HEADER_SEARCH_PATHS",
                                   disable_if_empty=True, fold_array=True)
            build_settings.add_item(temp_array)
            # Location of extra header paths
            for item in configuration.get_chained_list(
                    "include_folders_list"):
                temp_array.add_array_entry(item)

            # Directories for recursive search
            # build_settings.add_dict_entry(
            #   "INCLUDED_RECURSIVE_SEARCH_PATH_SUBDIRECTORIES")

            # Expand the build settings in the plist file
            # build_settings.add_dict_entry("INFOPLIST_EXPAND_BUILD_SETTINGS")

            # Name of the plist file
            # build_settings.add_dict_entry("INFOPLIST_FILE")

            # Preprocessor flags for the plist file
            # build_settings.add_dict_entry(
            #   "INFOPLIST_OTHER_PREPROCESSOR_FLAGS")

            # Output file format for the plist
            # build_settings.add_dict_entry("INFOPLIST_OUTPUT_FORMAT")

            # Prefix header for plist
            # build_settings.add_dict_entry("INFOPLIST_PREFIX_HEADER")

            # Allow preprocessing of the plist file
            # build_settings.add_dict_entry("INFOPLIST_PREPROCESS")

            # Defines for the plist file
            # build_settings.add_dict_entry(
            #   "INFOPLIST_PREPROCESSOR_DEFINITIONS")

            # Initialization routine name
            # build_settings.add_dict_entry("INIT_ROUTINE")

            # BSD group to attach for the installed executable
            # build_settings.add_dict_entry("INSTALL_GROUP")

            # File mode flags for installed executable
            # build_settings.add_dict_entry("INSTALL_MODE_FLAG")

            # Owner account for installed executable
            # build_settings.add_dict_entry("INSTALL_OWNER")

            # Keep private externs private
            # build_settings.add_dict_entry("KEEP_PRIVATE_EXTERNS")

            # Change the interal  name of the dynamic library
            # build_settings.add_dict_entry("LD_DYLIB_INSTALL_NAME")

            # Generate a map file for dynamic libraries
            # build_settings.add_dict_entry("LD_GENERATE_MAP_FILE")

            # Path for the map file
            # build_settings.add_dict_entry("LD_MAP_FILE_PATH")

            # Flags to pass to a library using OpenMP
            # build_settings.add_dict_entry("LD_OPENMP_FLAGS")

            # List of paths to search for a library
            # build_settings.add_dict_entry("LD_RUNPATH_SEARCH_PATHS")

            # List of directories to search for libraries
            temp_array = JSONArray(
                "LIBRARY_SEARCH_PATHS", disable_if_empty=True, fold_array=True)
            build_settings.add_item(temp_array)
            # Location of libraries
            for item in configuration.get_chained_list(
                    "library_folders_list"):
                temp_array.add_array_entry(item)

            # Display mangled names in linker
            # build_settings.add_dict_entry("LINKER_DISPLAYS_MANGLED_NAMES")

            # Link the standard libraries
            # build_settings.add_dict_entry("LINK_WITH_STANDARD_LIBRARIES")

            # Type of Mach-O file
            if configuration.project_type is ProjectTypes.library:
                item = "staticlib"
            elif configuration.project_type is ProjectTypes.sharedlibrary:
                item = "mh_dylib"
            else:
                item = "mh_execute"
            build_settings.add_dict_entry("MACH_O_TYPE", item)

            # Deployment minimum OS
            item = "10.5" if ide < IDETypes.xcode4 else "10.13"
            build_settings.add_dict_entry("MACOSX_DEPLOYMENT_TARGET", item)
            if ide < IDETypes.xcode4:
                build_settings.add_dict_entry(
                    "MACOSX_DEPLOYMENT_TARGET[arch=ppc]", "10.4")

            # Kernel module name
            # build_settings.add_dict_entry("MODULE_NAME")

            # Kernel driver start function name
            # build_settings.add_dict_entry("MODULE_START")

            # Kernel driver stop function name
            # build_settings.add_dict_entry("MODULE_STOP")

            # Version number of the kernel driver
            # build_settings.add_dict_entry("MODULE_VERSION")

            # Root folder for intermediate files
            build_settings.add_dict_entry("OBJROOT", "temp")

            # If YES, only build the active CPU for fast recompilation
            build_settings.add_dict_entry("ONLY_ACTIVE_ARCH", "NO")

            # Path to file for order of functions to link
            # build_settings.add_dict_entry("ORDER_FILE")

            # Extra flags to pass to the C compiler
            # build_settings.add_dict_entry("OTHER_CFLAGS")

            # Extra flags to pass to the code sign tool
            # build_settings.add_dict_entry("OTHER_CODE_SIGN_FLAGS")

            # Extra flags to pass to the C++ compiler
            # build_settings.add_dict_entry("OTHER_CPLUSPLUSFLAGS")

            # Extra flags to pass to the linker
            temp_array = JSONArray(
                "OTHER_LDFLAGS", disable_if_empty=True, fold_array=True)
            build_settings.add_item(temp_array)
            # Additional libraries
            for item in configuration.get_chained_list(
                    "libraries_list"):
                # Get rid of lib and .a
                if item.startswith("lib"):
                    item = item[3:]
                if item.endswith(".a"):
                    item = item[:-2]
                temp_array.add_array_entry("-l" + item)

            # Extra flags to pass to the unit test tool
            # build_settings.add_dict_entry("OTHER_TEST_FLAGS")

            # Output file format for the plist file
            # build_settings.add_dict_entry("PLIST_FILE_OUTPUT_FORMAT")

            # Prebind the functions together
            if ide < IDETypes.xcode12:
                build_settings.add_dict_entry("PREBINDING", "YES")

            # Include headers included in precompiler header
            # build_settings.add_dict_entry(
            #   "PRECOMPS_INCLUDE_HEADERS_FROM_BUILT_PRODUCTS_DIR")

            # Flags to pass for pre-linker
            # build_settings.add_dict_entry("PRELINK_FLAGS")

            # Libraries to use for pre-linking
            # build_settings.add_dict_entry("PRELINK_LIBS")

            # Don't deleate dead code initializers
            # build_settings.add_dict_entry(
            #   "PRESERVE_DEAD_CODE_INITS_AND_TERMS")

            # Path to copy private headers for building
            # build_settings.add_dict_entry("PRIVATE_HEADERS_FOLDER_PATH")

            # Product name
            build_settings.add_dict_entry("PRODUCT_NAME", "$(TARGET_NAME)")

            # Path to copy public headers for building
            # build_settings.add_dict_entry("PUBLIC_HEADERS_FOLDER_PATH")

            # Paths to search for rez
            # build_settings.add_dict_entry("REZ_SEARCH_PATHS")

            # Scan source code for include files for dependency
            # graph generation.
            # build_settings.add_dict_entry(
            #   "SCAN_ALL_SOURCE_FILES_FOR_INCLUDES")

            # SDK to use to for this build
            if ide >= IDETypes.xcode10:
                build_settings.add_dict_entry("SDKROOT", solution._xc_sdkroot)

            # Flags for the section reordering
            # build_settings.add_dict_entry("SECTORDER_FLAGS")

            # Strip symbols in a seperate pass
            # build_settings.add_dict_entry("SEPARATE_STRIP")

            # Edit symbols with nmedit
            # build_settings.add_dict_entry("SEPARATE_SYMBOL_EDIT")

            # Path for directory for precompiled header files
            # build_settings.add_dict_entry("SHARED_PRECOMPS_DIR")

            # Skip the install phase in deployment
            # build_settings.add_dict_entry("SKIP_INSTALL")

            # Type of libary for Standard C
            # build_settings.add_dict_entry("STANDARD_C_PLUS_PLUS_LIBRARY_TYPE")

            # Encoding for Strings file for localization
            build_settings.add_dict_entry(
                "STRINGS_FILE_OUTPUT_ENCODING", "UTF-8")

            # Flags to pass to the symbol stripper
            # build_settings.add_dict_entry("STRIPFLAGS")

            # Set to YES to strip symbols from installed product
            # build_settings.add_dict_entry("STRIP_INSTALLED_PRODUCT")

            # Style of symbol stripping
            # build_settings.add_dict_entry("STRIP_STYLE")

            # Suffix needed
            if ide < IDETypes.xcode13:
                build_settings.add_dict_entry(
                    "SUFFIX",
                    solution.ide_code +
                    solution.platform_code +
                    configuration.short_code)

            # Products are placed in this folder
            build_settings.add_dict_entry("SYMROOT", "temp")

            # Path to the executable that accepts unit test bundles
            # build_settings.add_dict_entry("TEST_HOST")

            # Path to unit test tool
            # build_settings.add_dict_entry("TEST_RIG")

            # Path to file with symbols to NOT export
            # build_settings.add_dict_entry("UNEXPORTED_SYMBOLS_FILE")

            # Paths to user headers
            # build_settings.add_dict_entry("USER_HEADER_SEARCH_PATHS")

            # List of allowable cpu architectures
            # build_settings.add_dict_entry("VALID_ARCHS")

            # Name of the executable that creates the version info.
            # build_settings.add_dict_entry("VERSIONING_SYSTEM")

            # User name of the invoker of the version tool
            # build_settings.add_dict_entry("VERSION_INFO_BUILDER")

            # Allow exporting the version information
            # build_settings.add_dict_entry("VERSION_INFO_EXPORT_DECL")

            # Name of the file for version information
            # build_settings.add_dict_entry("VERSION_INFO_FILE")

            # Version info prefix
            # build_settings.add_dict_entry("VERSION_INFO_PREFIX")

            # Version info suffix
            # build_settings.add_dict_entry("VERSION_INFO_SUFFIX")

            # List of additional warning flags to pass to the compiler.
            # build_settings.add_dict_entry("WARNING_CFLAGS")

            # List of additional warning flags to pass to the linker.
            # build_settings.add_dict_entry("WARNING_LDFLAGS")

            # Extension for product wrappers
            # build_settings.add_dict_entry("WRAPPER_EXTENSION")

        else:

            # Is this a simulator target?
            if configuration.platform.is_ios():
                if solution._xc_sdkroot == "iphoneos" and \
                    configuration.platform in (
                        PlatformTypes.iosemu32, PlatformTypes.iosemu64):
                    build_settings.add_dict_entry("SDKROOT", "iphonesimulator")

        # Make sure they are in sorted order
        build_settings.value = sorted(
            build_settings.value, key=attrgetter("name"))

        self.add_dict_entry("name", configuration.name)

    ########################################

    def fixup_archs(self, archs):
        """
        Based on the SDKROOT entry, set the default CPUs.
        """

        # pylint: disable=protected-access

        # Check for an override
        xc_archs = self.configuration.get_chained_value("xc_archs")
        if xc_archs:
            for item in xc_archs:
                archs.add_array_entry(item)
            return None

        # Start by getting the IDE and platform
        ide = self.configuration.ide
        sdkroot = self.configuration.project.solution._xc_sdkroot

        # Test for supported cpus for macosx
        if self.configuration.platform.is_macosx():
            digits = sdkroot[6:].split(".")
            if len(digits) > 1:
                version = float(digits[1])
            else:
                version = 6

            if ide is IDETypes.xcode3:
                archs.add_array_entry("ppc")

                # macosx 10.3.9 is ppc 32 bit only
                if version >= 4:
                    archs.add_array_entry("ppc64")

            # Xcode 14 dropped x86
            if ide < IDETypes.xcode14:
                archs.add_array_entry("i386")

            # Everyone has x64
            archs.add_array_entry("x86_64")

            # Xcode 12 supports arm64
            if ide >= IDETypes.xcode12:
                archs.add_array_entry("arm64")
            return None

        if self.configuration.platform in (
                PlatformTypes.iosemu32, PlatformTypes.iosemu64):
            archs.add_array_entry("i386")
            archs.add_array_entry("x86_64")
            return None

        if self.configuration.platform in (
                PlatformTypes.ios32, PlatformTypes.ios64):
            archs.add_array_entry("armv6")
            archs.add_array_entry("armv7")
            archs.add_array_entry("i386")
            archs.add_array_entry("x86_64")

        return None

########################################


class XCConfigurationList(JSONDict):
    """
    Each XCConfigurationList entry

    Attributes:
        build_configurations: Build configurations
        default_config: Default configuration
        pbxtype: Type of project builder
        targetname: Name of this target
        configuration_list: Configations
    """

    def __init__(self, pbxtype, targetname):
        """
        Init XCConfigurationList

        Args:
            pbxtype: Project type
            targetname: Name of the target
        """

        uuid = calcuuid("XCConfigurationList" + pbxtype + targetname)
        JSONDict.__init__(
            self,
            name=uuid,
            isa="XCConfigurationList",
            comment="Build configuration list for {} \"{}\"".format(
                pbxtype,
                targetname),
            uuid=uuid)
        self.build_configurations = JSONArray("buildConfigurations")
        self.add_item(self.build_configurations)
        self.add_item(JSONEntry("defaultConfigurationIsVisible", value="0"))
        self.default_config = JSONEntry(
            "defaultConfigurationName", value="Release")
        self.add_item(self.default_config)

        self.pbxtype = pbxtype
        self.targetname = targetname
        self.configuration_list = []

    def generate(self, line_list, indent=0):
        """
        Write this record to output
        """

        default = None
        found = set()
        for item in self.configuration_list:
            if item.configuration.name in found:
                continue
            found.add(item.configuration.name)
            if item.configuration.name == "Release":
                default = "Release"
            elif default is None:
                default = item.configuration.name
            self.build_configurations.add_item(
                JSONEntry(
                    item.uuid,
                    comment=item.configuration.name,
                    suffix=","))

        if default is None:
            default = "Release"

        self.default_config.value = default

        return JSONDict.generate(self, line_list, indent)


########################################

class XCProject(JSONDict):
    """
    Root object for an XCode IDE project file.
    Created with the name of the project, the IDE code (xc3, xc5)
    the platform code (ios, osx)

    Attributes:
        solution: Parent solution
        objects: JSONObjects of objects
    """

    def __init__(self, solution):
        """
        Init the project generator.

        Args:
            solution: Project solution to generate from.
        """

        # pylint: disable=too-many-statements
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches

        # Set the parent, uuid, and solution
        self.solution = solution
        uuid = calcuuid("PBXProjectRoot" + solution.xcode_folder_name)

        # Init the solution
        JSONDict.__init__(self, solution.name, uuid=uuid)

        # Initialize entries for master dictionary for the XCode project.
        objects = self.init_root_entries()
        self.objects = objects

        idecode = solution.ide.get_short_code()
        rootproject = PBXProject(self.uuid, solution)
        objects.add_item(rootproject)

        # Process all the projects and configurations
        for project in solution.project_list:

            # Find all the input files
            project.get_file_list(SUPPORTED_FILES)

            # Determine if there are frameworks, if so, add them to
            # the input file list
            framework_set = set()
            for configuration in project.configuration_list:

                for item in configuration.frameworks_list:
                    if item not in framework_set:
                        framework_set.add(item)
                        project.codefiles.append(SourceFile(
                            item, "", FileTypes.frameworks))

            # Make a list of build rules for files that need custom compilers
            build_rules = []

            # Check if there are GLSL Files
            if source_file_detect(project.codefiles, FileTypes.glsl):
                glsl_build_rule = PBXBuildRuleGLSL(solution.ide)
                objects.add_item(glsl_build_rule)
                build_rules.append(glsl_build_rule)

            # Create all the file references
            file_references = []
            for item in project.codefiles:
                file_reference = PBXFileReference(item, solution.ide)
                objects.add_item(file_reference)
                file_references.append(file_reference)

            # What's the final output file?
            if project.project_type is ProjectTypes.library:
                if project.platform is PlatformTypes.ios:
                    libextension = "ios.a"
                else:
                    libextension = "osx.a"
                outputfilereference = PBXFileReference(SourceFile(
                    "lib" + solution.name + idecode + libextension, "",
                    FileTypes.library), solution.ide)
                objects.add_item(outputfilereference)

            elif project.project_type is ProjectTypes.app:
                outputfilereference = PBXFileReference(SourceFile(
                    solution.name + ".app", "", FileTypes.exe), solution.ide)
                objects.add_item(outputfilereference)

            elif project.project_type is not ProjectTypes.empty:
                outputfilereference = PBXFileReference(SourceFile(
                    solution.name, "", FileTypes.exe), solution.ide)
                objects.add_item(outputfilereference)
            else:
                outputfilereference = None

            if outputfilereference:
                file_references.append(outputfilereference)

            # If a fat library, add references for dev and sim targets
            ioslibrary = False
            if project.platform is PlatformTypes.ios:
                if project.project_type is ProjectTypes.library:
                    ioslibrary = True

            if ioslibrary:
                devfilereference = PBXFileReference(
                    SourceFile(
                        "lib" + solution.name + "dev.a", "",
                        FileTypes.library), solution.ide)
                objects.add_item(devfilereference)
                file_references.append(devfilereference)

                simfilereference = PBXFileReference(
                    SourceFile(
                        "lib" + solution.name + "sim.a", "",
                        FileTypes.library), solution.ide)
                objects.add_item(simfilereference)
                file_references.append(simfilereference)

                # Two targets for "fat" libraries
                buildphase1 = PBXSourcesBuildPhase(
                    devfilereference)
                objects.add_item(buildphase1)
                buildphase2 = PBXSourcesBuildPhase(
                    simfilereference)
                objects.add_item(buildphase2)
                framephase1 = PBXFrameworksBuildPhase(devfilereference)
                objects.add_item(framephase1)
                framephase2 = PBXFrameworksBuildPhase(simfilereference)
                objects.add_item(framephase2)

                # Add source files to compile for the ARM and the Intel libs

                for item in file_references:
                    if item.source_file.type in (FileTypes.m, FileTypes.mm,
                            FileTypes.cpp, FileTypes.c,
                            FileTypes.glsl, FileTypes.ppc, FileTypes.x64,
                            FileTypes.x86, FileTypes.arm, FileTypes.arm64):

                        build_file = PBXBuildFile(item, devfilereference)
                        objects.add_item(build_file)
                        buildphase1.append_file(build_file)

                        build_file = PBXBuildFile(item, simfilereference)
                        objects.add_item(build_file)
                        buildphase2.append_file(build_file)
                    elif item.source_file.type is FileTypes.frameworks:

                        build_file = PBXBuildFile(item, devfilereference)
                        objects.add_item(build_file)
                        framephase1.add_build_file(build_file)

                        build_file = PBXBuildFile(item, simfilereference)
                        objects.add_item(build_file)
                        framephase2.add_build_file(build_file)

            else:
                if outputfilereference:
                    devfilereference = None
                    simfilereference = None
                    buildphase1 = PBXSourcesBuildPhase(
                        outputfilereference)
                    objects.add_item(buildphase1)
                    framephase1 = PBXFrameworksBuildPhase(outputfilereference)
                    objects.add_item(framephase1)

                    for item in file_references:
                        if item.source_file.type in (FileTypes.m, FileTypes.mm,
                                FileTypes.cpp, FileTypes.c,
                                FileTypes.glsl, FileTypes.ppc, FileTypes.x64,
                                FileTypes.x86, FileTypes.arm, FileTypes.arm64):

                            build_file = PBXBuildFile(
                                item, outputfilereference)
                            objects.add_item(build_file)
                            buildphase1.append_file(build_file)

                        elif item.source_file.type is FileTypes.frameworks:
                            build_file = PBXBuildFile(
                                item, outputfilereference)
                            objects.add_item(build_file)
                            framephase1.add_build_file(build_file)

            # Given the list of file references, create the
            # directory tree for organizing the files
            rootproject.set_root_group(
                self.create_directory_tree(file_references))

            # Create the config list for the root project
            configlistref = XCConfigurationList(
                "PBXProject", solution.name)
            objects.add_item(configlistref)
            for configuration in project.configuration_list:
                entry = self.addxcbuildconfigurationlist(
                    configuration, None, configlistref, False)
                configlistref.configuration_list.append(entry)

            rootproject.set_config_list(configlistref)

            #
            # Create the PBXNativeTarget config chunks
            #

            if project.project_type is ProjectTypes.library:
                outputtype = "com.apple.product-type.library.static"
            elif project.project_type is ProjectTypes.screensaver:
                outputtype = "com.apple.product-type.bundle"
            elif project.project_type is ProjectTypes.app:
                outputtype = "com.apple.product-type.application"
            else:
                outputtype = "com.apple.product-type.tool"

            # For a normal project, attach the config to a native target and
            # we're done
            if not ioslibrary and outputfilereference:
                configlistref = XCConfigurationList(
                    "PBXNativeTarget", solution.name)
                objects.add_item(configlistref)
                install = False
                if project.project_type is ProjectTypes.app:
                    install = True
                for configuration in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            configuration,
                            None,
                            configlistref,
                            install))
                nativetarget1 = PBXNativeTarget(
                    self,
                    solution.name,
                    outputfilereference,
                    solution.name,
                    outputtype,
                    build_rules)
                objects.add_item(nativetarget1)
                nativetarget1.set_config_list(configlistref)
                rootproject.append_target(nativetarget1)
                nativetarget1.add_build_phase(buildphase1)
                nativetarget1.add_build_phase(framephase1)

            #
            # For fat binary iOS projects, it's a lot messier
            #

            elif outputfilereference:
                targetname = solution.name
                configlistref = XCConfigurationList(
                    "PBXNativeTarget", targetname)
                objects.add_item(configlistref)
                for configuration in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            configuration, None, configlistref, False))

                nativetarget1 = PBXNativeTarget(
                    self,
                    solution.name,
                    outputfilereference,
                    solution.name,
                    outputtype,
                    [])
                objects.add_item(nativetarget1)
                nativetarget1.set_config_list(configlistref)
                rootproject.append_target(nativetarget1)

                targetname = solution.name + "dev"
                configlistref = XCConfigurationList(
                    "PBXNativeTarget", targetname)
                objects.add_item(configlistref)
                for configuration in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            configuration,
                            None,
                            configlistref,
                            False))
                nativeprojectdev = PBXNativeTarget(
                    self,
                    targetname,
                    devfilereference,
                    solution.name,
                    outputtype,
                    build_rules)
                objects.add_item(nativeprojectdev)
                nativeprojectdev.set_config_list(configlistref)
                rootproject.append_target(nativeprojectdev)

                nativeprojectdev.add_build_phase(buildphase1)
                nativeprojectdev.add_build_phase(framephase1)
                devcontainer = PBXContainerItemProxy(
                    nativeprojectdev, self.uuid)
                objects.add_item(devcontainer)

                targetname = solution.name + "sim"
                configlistref = XCConfigurationList(
                    "PBXNativeTarget", targetname)
                objects.add_item(configlistref)
                for configuration in project.configuration_list:

                    # Hack to change ios native to ios emulation platforms
                    tempplatform = configuration.platform
                    configuration.platform = {
                        PlatformTypes.ios32: PlatformTypes.iosemu32,
                        PlatformTypes.ios64: PlatformTypes.iosemu64}.get(
                        tempplatform, tempplatform)

                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            configuration,
                            None,
                            configlistref,
                            False))
                    # Restore configuration
                    configuration.platform = tempplatform

                nativeprojectsim = PBXNativeTarget(
                    self,
                    targetname,
                    simfilereference,
                    solution.name,
                    outputtype,
                    build_rules)
                objects.add_item(nativeprojectsim)
                nativeprojectsim.set_config_list(configlistref)
                rootproject.append_target(nativeprojectsim)

                nativeprojectsim.add_build_phase(buildphase2)
                nativeprojectsim.add_build_phase(framephase2)
                simcontainer = PBXContainerItemProxy(
                    nativeprojectsim, self.uuid)
                objects.add_item(simcontainer)

                depend_target = PBXTargetDependency(
                    devcontainer, nativeprojectdev)
                objects.add_item(depend_target)
                nativetarget1.add_dependency(depend_target)

                depend_target = PBXTargetDependency(
                    simcontainer, nativeprojectsim)
                objects.add_item(depend_target)
                nativetarget1.add_dependency(depend_target)

            # Add in a shell script build phase if needed
            # Is this an application?

            if project.platform is PlatformTypes.macosx:
                if project.project_type in (
                    ProjectTypes.tool, ProjectTypes.library,
                        ProjectTypes.sharedlibrary):

                    # Copy the output to the bin folder
                    item = copy_tool_to_bin()
                    objects.add_item(item)
                    nativetarget1.add_build_phase(item)

                elif project.project_type is ProjectTypes.app:

                    # Copy the exe into the .app folder
                    input_file = (
                        "{}.app/Contents/MacOS/"
                        "${{EXECUTABLE_NAME}}").format(TEMP_EXE_NAME)

                    input_data = [input_file]
                    output = (
                        "${SRCROOT}/bin/"
                        "${EXECUTABLE_NAME}.app"
                        "/Contents/MacOS/"
                        "${EXECUTABLE_NAME}")

                    command = "if [ ! -d ${SRCROOT}/bin ]; then mkdir " \
                        "${SRCROOT}/bin; fi\\n" \
                        "${CP} -r " + TEMP_EXE_NAME + ".app/ " \
                        "${SRCROOT}/bin/${EXECUTABLE_NAME}" + ".app/\\n" \
                        "mv ${SRCROOT}/bin/${EXECUTABLE_NAME}" + ".app" \
                        "/Contents/MacOS/${EXECUTABLE_NAME} " \
                        "${SRCROOT}/bin/${EXECUTABLE_NAME}" + ".app" \
                        "/Contents/MacOS/${EXECUTABLE_NAME}" + \
                        idecode
                    shellbuildphase = PBXShellScriptBuildPhase(
                        input_data, output, command)
                    objects.add_item(shellbuildphase)
                    nativetarget1.add_build_phase(shellbuildphase)

            # Is there a deployment folder?

            deploy_folder = None
            for configuration in project.configuration_list:
                if configuration.deploy_folder:
                    deploy_folder = convert_to_linux_slashes(
                        configuration.deploy_folder, force_ending_slash=True)
                    deploy_folder = deploy_folder.replace("(", "{")
                    deploy_folder = deploy_folder.replace(")", "}")

            if deploy_folder is not None:
                if ioslibrary is False:
                    input_data = [TEMP_EXE_NAME]
                else:
                    input_data = [
                        "${BUILD_ROOT}/" + solution.name +
                        "dev${SUFFIX}/lib" + solution.name + "dev.a",
                        "${BUILD_ROOT}/" + solution.name +
                        "sim${SUFFIX}/lib" + solution.name + "sim.a"
                    ]

                if ioslibrary is True:

                    output = deploy_folder + "lib${PRODUCT_NAME}${SUFFIX}.a"
                    command = PERFORCE_PATH + " edit " + output + "\\n" + \
                        "lipo -output " + output + \
                        " -create ${BUILD_ROOT}/" + \
                        solution.name + "dev${SUFFIX}/lib" + \
                        solution.name + "dev.a ${BUILD_ROOT}/" + \
                        solution.name + "sim${SUFFIX}/lib" + \
                        solution.name + "sim.a\\n" + \
                        PERFORCE_PATH + " revert -a " + \
                        output + "\\n"
                elif project.project_type is ProjectTypes.library:

                    output = ("{0}lib${{PRODUCT_NAME}}${{SUFFIX}}.a").format(
                        deploy_folder)
                    command = (
                        "{0} edit {1}\\n"
                        "${{CP}} {2} {1}\\n"
                        "{0} revert -a {1}\\n"
                    ).format(PERFORCE_PATH, output, TEMP_EXE_NAME)

                elif project.project_type is ProjectTypes.sharedlibrary:

                    output = ("{0}lib${{TARGET_NAME}}.dylib").format(
                        deploy_folder)
                    command = (
                        "if [ \"${{CONFIGURATION}}\" == \"Release\" ]; then \\n"
                        "{0} edit {1}\\n"
                        "${{CP}} {2} {1}\\n"
                        "{0} revert -a {1}\\n"
                        "fi\\n").format(PERFORCE_PATH, output, TEMP_EXE_NAME)
                else:
                    output = deploy_folder + "${TARGET_NAME}"
                    command = (
                        "if [ \"${{CONFIGURATION}}\" == \"Release\" ]; then \\n"
                        "{0} edit {1}\\n"
                        "${{CP}} {2} {1}\\n"
                        "fi\\n").format(PERFORCE_PATH, output, TEMP_EXE_NAME)

                shellbuildphase = PBXShellScriptBuildPhase(
                    input_data, output, command)
                objects.add_item(shellbuildphase)
                nativetarget1.add_build_phase(shellbuildphase)

    def addxcbuildconfigurationlist(self, configuration, configfilereference,
                                    owner, installpath):
        """
        Add a new configuration list
        """

        entry = XCBuildConfiguration(
            configuration,
            configfilereference,
            owner,
            installpath)
        for item in self.objects.get_entries("XCBuildConfiguration"):
            if item.uuid == entry.uuid:
                entry = item
                break
        else:
            self.objects.add_item(entry)
        return entry

    ########################################

    def init_root_entries(self):
        """
        Init the root items for the XCProject

        Creates the entries archiveVersion, classes, objectVersion,
        objects, and rootObject

        Returns:
            objects, which is a JSONObjects object
        """

        # Always 1
        self.add_item(JSONEntry("archiveVersion", value="1"))

        # Always empty
        self.add_item(JSONDict("classes"))

        # Set to the version of XCode being generated for
        self.add_item(
            JSONEntry(
                "objectVersion",
                value=OBJECT_VERSIONS.get(self.solution.ide)[0]))

        # Create the master object list
        objects = JSONObjects("objects")
        self.add_item(objects)

        # UUID of the root object
        rootobject = JSONEntry(
            "rootObject",
            value=self.uuid,
            comment="Project object")
        self.add_item(rootobject)

        return objects

    ########################################

    def create_directory_tree(self, file_references):
        """
        Create the directory tree for all files in the project

        Args:
            file_references: List of all file references to map
        """

        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        # Main JSON object list
        objects = self.objects

        # Create the root file group and the Products group
        group_products = PBXGroup("Products", None)

        # No frameworks group unless one is warranted
        framework_group = PBXGroup("Frameworks", None)

        # Origin of the directory tree (This will be returned)
        group_root = PBXGroup(self.solution.name, None)
        objects.add_item(group_root)

        # List of groups already made, to avoid making duplicates
        groups_made = []

        # pylint: disable=too-many-nested-blocks

        # Insert all the file references into the proper group
        for item in file_references:

            # Products go into a special group
            if item.source_file.type in (FileTypes.exe, FileTypes.library):
                group_products.add_file(item)
                continue

            # Frameworks go into the FrameWorks group
            if item.source_file.type is FileTypes.frameworks:
                framework_group.add_file(item)
                continue

            # Add to the hierarchical groups

            # Isolate the path
            index = item.relative_pathname.rfind("/")
            if index == -1:
                # Put in the root group
                group_root.add_file(item)
                continue

            # Separate the path and name
            path = item.relative_pathname[0:index]

            # See if a group already exists
            for match_group in groups_made:

                # Add to a pre-existing group if found
                if match_group.path == path:
                    match_group.add_file(item)
                    break
            else:

                # Group not found. Iterate and create the group
                # May need multiple levels

                # Hack to remove preceding ../ entries
                if path.startswith("../"):
                    index = 3
                elif path.startswith("../../"):
                    index = 6
                else:
                    index = 0

                previous_group = group_root
                while True:

                    # At the final directory level?
                    endindex = path[index:].find("/")
                    if endindex == -1:

                        # Final level, create group and add reference
                        match_group = PBXGroup(path[index:], path)
                        objects.add_item(match_group)
                        groups_made.append(match_group)
                        previous_group.add_group(match_group)
                        match_group.add_file(item)
                        break

                    # See if a group already exists at this level
                    temppath = path[0:index + endindex]
                    for match_group in groups_made:
                        if match_group.path == temppath:
                            break
                    else:

                        # Create an empty intermediate group
                        match_group = PBXGroup(
                            path[index:index + endindex], temppath)
                        objects.add_item(match_group)
                        groups_made.append(match_group)
                        previous_group.add_group(match_group)

                    # Next level into the group
                    previous_group = match_group
                    index = index + endindex + 1

        # Add in the Products group if needed
        if not group_products.is_empty():
            objects.add_item(group_products)
            group_root.add_group(group_products)

        # Add in the Frameworks group if needed
        if not framework_group.is_empty():
            objects.add_item(framework_group)
            group_root.add_group(framework_group)

        return group_root

    ########################################

    def generate(self, line_list, indent=0):
        """
        Generate an entire XCode project file

        Args:
            line_list: Line list to append new lines.
            indent: number of tabs to insert (For recursion)
        Returns:
            Non-zero on error.
        """

        # Write the XCode header for charset
        line_list.append("// !$*UTF8*$!")

        # Open brace for beginning
        line_list.append("{")

        # Increase indentatiopn
        indent = indent + 1

        # Dump everything in the project
        for item in self.value:
            item.generate(line_list, indent)

        # Close up the project file
        line_list.append("}")
        return 0

########################################


def generate(solution):
    """
    Create a project file for XCode file format version 3.1

    Args:
        solution: solution to generate an XCode project from
    Returns:
        Numeric error code.
    """

    # pylint: disable=protected-access

    # Failsafe
    if solution.ide not in SUPPORTED_IDES:
        return 10

    # Create the output filename and pass it to the generator
    # so it can reference itself in make targets
    solution.xcode_folder_name = "{}{}{}.xcodeproj".format(
        solution.name, solution.ide_code, solution.platform_code)
    create_folder_if_needed(os.path.join(solution.working_directory,
        solution.xcode_folder_name))

    # Xcode requires configurations, if none are present, add one
    if not solution.project_list:
        project = Project(
            name=solution.name,
            project_type=ProjectTypes.empty)
        project.source_folders_list = []
        solution.project_list.append(project)

    # Make sure all projects have configurations
    for project in solution.project_list:
        if not project.configuration_list:
            project.configuration_list.append(
                Configuration("Debug", project.platform))
            project.configuration_list.append(
                Configuration("Release", project.platform))

    # Determine the sdk to use for the project
    solution._xc_sdkroot = get_sdk_root(solution)

    # Create the exporter
    exporter = XCProject(solution)

    # Output the actual project file
    xcode_lines = []
    error = exporter.generate(xcode_lines)
    if error:
        return error

    # Save the file if it changed
    xcode_filename = os.path.join(solution.working_directory,
        solution.xcode_folder_name, _XCODEPROJECT_FILE)

    save_text_file_if_newer(
        xcode_filename, xcode_lines, bom=False,
        perforce=solution.perforce, verbose=solution.verbose)

    return 0
