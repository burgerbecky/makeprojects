#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2022-2025 by Rebecca Ann Heineman becky@burgerbecky.com

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

@var makeprojects.xcode_utils.TEMP_EXE_NAME
Build executable pathname

@var makeprojects.xcode_utils.PERFORCE_PATH
Path of the perforce executable

@var makeprojects.xcode_utils.TABS
Default tab format for XCode

@var makeprojects.xcode_utils.OBJECT_ORDER
Order of XCode objects

@var makeprojects.xcode.FILE_REF_DIR
Map of root directories

@var makeprojects.xcode.FILE_REF_LAST_KNOWN
Dictionary for mapping FileTypes to XCode file types

@var makeprojects.xcode_utils._XCODESAFESET
Valid characters for XCode strings without quoting
"""

# pylint: disable=useless-object-inheritance
# pylint: disable=consider-using-f-string
# pylint: disable=too-many-lines

from __future__ import absolute_import, print_function, unicode_literals

import hashlib
import os
import string
from operator import attrgetter, itemgetter

from burger import convert_to_windows_slashes, convert_to_linux_slashes

from .core import SourceFile
from .enums import IDETypes, FileTypes

# Build executable pathname
TEMP_EXE_NAME = "${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}"

# Path of the perforce executable
PERFORCE_PATH = "/opt/local/bin/p4"

# Default tab format for XCode
TABS = "\t"

# This is the order of XCode chunks that match the way
# that XCode outputs them.
OBJECT_ORDER = (
    "PBXAggregateTarget",
    "PBXBuildFile",
    "PBXBuildRule",
    "PBXContainerItemProxy",
    "PBXCopyFilesBuildPhase",
    "PBXFileReference",
    "PBXFrameworksBuildPhase",
    "PBXGroup",
    "PBXNativeTarget",
    "PBXProject",
    "PBXReferenceProxy",
    "PBXResourcesBuildPhase",
    "PBXShellScriptBuildPhase",
    "PBXSourcesBuildPhase",
    "PBXTargetDependency",
    "XCBuildConfiguration",
    "XCConfigurationList"
)

# Map of root directories
FILE_REF_DIR = {
    FileTypes.library: "BUILT_PRODUCTS_DIR",
    FileTypes.exe: "BUILT_PRODUCTS_DIR",
    FileTypes.frameworks: "SDKROOT",
    FileTypes.x86: "SOURCE_ROOT",
    FileTypes.x64: "SOURCE_ROOT",
    FileTypes.arm: "SOURCE_ROOT",
    FileTypes.arm64: "SOURCE_ROOT",
    FileTypes.ppc: "SOURCE_ROOT",
    FileTypes.cpp: "SOURCE_ROOT",
    FileTypes.c: "SOURCE_ROOT",
    FileTypes.m: "SOURCE_ROOT",
    FileTypes.mm: "SOURCE_ROOT"
}

# Dictionary for mapping FileTypes to XCode file types
FILE_REF_LAST_KNOWN = {
    FileTypes.library: None,
    FileTypes.exe: None,
    FileTypes.frameworks: "wrapper.framework",
    FileTypes.glsl: "sourcecode.glsl",
    FileTypes.xml: "text.xml",
    FileTypes.xcconfig: "text.xcconfig",
    FileTypes.x86: "sourcecode.asm.asm",
    FileTypes.x64: "sourcecode.asm.asm",
    FileTypes.arm: "sourcecode.asm.asm",
    FileTypes.arm64: "sourcecode.asm.asm",
    FileTypes.ppc: "sourcecode.asm.asm",
    FileTypes.cpp: "sourcecode.cpp.objcpp",
    FileTypes.c: "source.c.c",
    FileTypes.h: "sourcecode.c.h",
    FileTypes.m: "source.c.objc",
    FileTypes.mm: "sourcecode.cpp.objcpp"
}

# Valid characters for XCode strings without quoting
_XCODESAFESET = frozenset(string.ascii_letters + string.digits + "_$./")

########################################


def calcuuid(input_str):
    """
    Given a string, create a 96 bit unique hash for XCode

    Args:
        input_str: string to hash
    Returns:
        96 bit hash string in upper case.
    """

    temphash = hashlib.md5(convert_to_windows_slashes(
        input_str).encode("utf-8")).hexdigest()

    # Take the hash string and only use the top 96 bits

    return temphash[0:24].upper()

########################################


def quote_string_if_needed(input_path):
    """
    Quote a string for XCode.

    XCode requires quotes for certain characters. If any illegal character
    exist in the string, the string will be reencoded to a quoted string using
    XCode JSON rules.

    Args:
        input_path: string to encapsulate.
    Returns:
        Original input string if XCode can accept it or properly quoted
    """

    # If there are any illegal characters, break
    for item in input_path:
        if item not in _XCODESAFESET:
            break
    else:
        # No illegal characters in the string
        if not input_path:
            return "\"\""
        return input_path

    # Quote the escaped string.
    return "\"{}\"".format(input_path.replace("\"", "\\\""))

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

########################################


class JSONRoot(object):
    """
    XCode JSON root object

    Every JSON entry for XCode derives from this object and has a minimum of a
    name, comment, uuid and an enabled flag.

    Attributes:
        name: Object's name (Can also be the uuid)
        comment: Optional object's comment field
        uuid: Optional uuid
        enabled: If True, output this object in generated output.
        suffix: Optional suffix used in generated output.
        value: Value
    """

    # pylint: disable=too-many-arguments

    def __init__(self, name, comment=None, uuid=None,
                 suffix=";", enabled=True, value=None):
        """
        Initialize the JSONRoot entry.

        Args:
            name: Name of this object
            comment: Optional comment
            uuid: uuid hash of the object
            suffix: string to append at the end of the generated line of output.
            enabled: If False, don't output this object in the generated object.
            value: Optional value
        """

        self.name = name
        self.comment = comment
        self.uuid = uuid
        self.enabled = enabled
        self.suffix = suffix
        self.value = value

    def add_item(self, item):
        """
        Append an item to the array.

        Args:
            item: JSONRoot based object.
        """

        self.value.append(item)

    def find_item(self, name):
        """
        Find a named item.

        Args:
            name: Name of the item to locate
        Returns:
            Reference to item or None if not found.
        """

        for item in self.value:
            if item.name == name:
                return item

        return None

########################################


class JSONEntry(JSONRoot):
    """
    XCode JSON single line entry.

    Each JSON entry for XCode consists of the name followed by an optional
    comment, and an optional value and then a mandatory suffix.
    """

    # pylint: disable=too-many-arguments

    def __init__(self, name, comment=None, value=None,
                 suffix=";", enabled=True):
        """
        Initialize the JSONEntry.

        Args:
            name: Name of this object
            comment: Optional comment
            value: Optional value
            suffix: string to append at the end of the generated line of output.
            enabled: If False, don't output this object in the generated object.
        """

        JSONRoot.__init__(
            self,
            name=name,
            comment=comment,
            suffix=suffix,
            enabled=enabled,
            value=value)

    def generate(self, line_list, indent=0):
        """
        Generate the text lines for this JSON element.

        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
        """

        if not self.enabled:
            return 0

        # Determine the indentation
        tabs = TABS * indent

        # Set the value string
        value = "" if self.value is None else " = " + \
            quote_string_if_needed(self.value)

        # Set the comment string
        comment = "" if self.comment is None else " /* {} */".format(
            self.comment)

        # Generate the JSON line
        line_list.append(
            "{}{}{}{}{}".format(
                tabs,
                quote_string_if_needed(self.name),
                value,
                comment,
                self.suffix))
        return 0

########################################


class JSONArray(JSONRoot):
    """
    XCode JSON array.

    Each JSON entry for XCode consists of the name followed by an optional
    comment, and an optional value and then a mandatory suffix.

    Attributes:
        disable_if_empty: True if output is disabled if the list is empty
    """

    # pylint: disable=too-many-arguments

    def __init__(self, name, comment=None, value=None, suffix=";",
                 enabled=True, disable_if_empty=False, fold_array=False):
        """
        Initialize the entry.

        Args:
            name: Name of this object
            comment: Optional comment
            value: List of default values
            suffix: Suffix, either ";" or ","
            enabled: If False, don't output this object in the generated object.
            disable_if_empty: If True, don't output if no items in the list.
            fold_array: True if the array should be in one line
        """

        if value is None:
            value = []

        JSONRoot.__init__(
            self,
            name=name,
            comment=comment,
            suffix=suffix,
            enabled=enabled,
            value=value)

        self.disable_if_empty = disable_if_empty

        ## Default array folding
        self.fold_array = fold_array

    def add_array_entry(self, name):
        """
        Create a new JSONEntry record and add to the array

        Take the string passed in and append it to the end of the array

        Args:
            name: String to append to the array
        Returns:
            JSONEntry created that was added
        """

        new_entry = JSONEntry(name, suffix=",")
        self.add_item(new_entry)
        return new_entry

    def generate(self, line_list, indent=0):
        """
        Generate the text lines for this JSON element.

        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
        """

        if not self.enabled:
            return 0

        # Disable if there are no values?
        if self.disable_if_empty and not self.value:
            return 0

        # Determine the indentation
        tabs = TABS * indent
        indent = indent + 1

        # Get the optional comment
        comment = "" if self.comment is None else " /* {} */".format(
            self.comment)

        # If there is only one entry, and array folding is enabled,
        # only output a single item, not an array
        if self.fold_array and len(self.value) == 1:
            line_list.append("{}{}{} = {}{}".format(
                tabs, self.name, comment,
                quote_string_if_needed(self.value[0].name), self.suffix))

        else:
            # Generate the array opening
            line_list.append("{}{}{} = (".format(tabs, self.name, comment))

            # Generate the array
            for item in self.value:
                item.generate(line_list, indent=indent)

            # Generate the array closing
            line_list.append("{}){}".format(tabs, self.suffix))
        return 0

########################################


class JSONDict(JSONRoot):
    """
    XCode JSON dictionary

    Each JSON entry for XCode consists of the name followed by an optional
    comment, and an optional value and then a mandatory suffix.

    Attributes:
        disable_if_empty: True if output is disabled if the list is empty
        isa: "Is a" name
    """

    # pylint: disable=too-many-arguments

    def __init__(self, name, isa=None, comment=None, value=None,
                 suffix=";", uuid=None, enabled=True, disable_if_empty=False,
                 flattened=False):
        """
        Initialize the entry.

        Args:
            name: Name of this object
            isa: "Is a" type of dictionary object
            comment: Optional comment
            value: List of default values
            suffix: Suffix, either ";" or ","
            uuid: uuid hash of the object
            enabled: If False, don't output this object in the generated object.
            disable_if_empty: If True, don't output if no items in the list.
            flattened: If True, flatten the child objects
        """

        if uuid is None:
            uuid = ""

        if value is None:
            value = []

        JSONRoot.__init__(
            self,
            name=name,
            comment=comment,
            uuid=uuid,
            suffix=suffix,
            enabled=enabled,
            value=value)

        self.disable_if_empty = disable_if_empty
        self.isa = isa

        ## Default flattened state
        self.flattened = flattened

        if isa is not None:
            self.add_dict_entry("isa", isa)

    def add_dict_entry(self, name, value=None):
        """
        Create a new JSONEntry record and add to the dictionary

        Take the string passed in and append it to dict

        Args:
            name: String for the JSONEntry name
            value: String to use as the value for the entry
        Returns:
            JSONEntry created that was added
        """

        new_entry = JSONEntry(name, value=value)
        self.add_item(new_entry)
        return new_entry

    def generate(self, line_list, indent=0):
        """
        Generate the text lines for this JSON element.
        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
        """

        if not self.enabled:
            return 0

        # Disable if there are no values?
        if self.disable_if_empty and self.value is not None:
            return 0

        # Determine the indentation
        tabs = TABS * indent
        indent = indent + 1

        # Get the optional comment"
        comment = "" if self.comment is None else " /* {} */".format(
            self.comment)

        # Generate the dictionary opening
        line_list.append("{}{}{} = {{".format(tabs, self.name, comment))

        # Generate the dictionary
        for item in self.value:
            item.generate(line_list, indent=indent)

        # Generate the dictionary closing
        line_list.append("{}}}{}".format(tabs, self.suffix))
        return 0

########################################


class JSONObjects(JSONDict):
    """
    XCode JSON dictionary

    Each JSON entry for XCode consists of the name followed by an optional
    comment, and an optional value and then a mandatory suffix.
    """

    def __init__(self, name, uuid=None, enabled=True):
        """
        Initialize the entry.

        Args:
            name: Name of this object
            uuid: uuid hash of the object
            enabled: If False, don't output this object in the generated object.
        """

        JSONDict.__init__(self, name, uuid=uuid, enabled=enabled)

    def get_entries(self, isa):
        """
        Return a list of items that match the isa name.

        Args:
            isa: isa name string.
        Returns:
            List of entires found, can be an empty list.
        """

        item_list = []
        for item in self.value:
            if item.isa == isa:
                item_list.append(item)
        return item_list

    def generate(self, line_list, indent=0):
        """
        Generate the text lines for this JSON element.

        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
        """

        if not self.enabled:
            return 0

        # Determine the indentation
        tabs = TABS * indent
        indent = indent + 1

        # Set the optional comment
        comment = "" if self.comment is None else " /* {} */".format(
            self.comment)

        # Generate the dictionary opening
        line_list.append("{}{}{} = {{".format(tabs, self.name, comment))

        # Output the objects in "isa" order for XCode
        for object_group in OBJECT_ORDER:

            # Find all entries by this name
            item_list = []
            for item in self.value:
                if item.isa == object_group:
                    item_list.append(item)

            # Any items in this group?
            if item_list:

                # Sort by uuid
                item_list = sorted(item_list, key=attrgetter("uuid"))

                # Using the name of the class, output the array of data items
                line_list.append("")
                line_list.append("/* Begin {} section */".format(object_group))
                for item in item_list:

                    # Because Apple hates me. Check if a record needs to be
                    # flattened instead of putting the data on individual lines,
                    # because, just because.

                    if getattr(item, "flattened", None):
                        # Generate the lines
                        temp_list = []
                        item.generate(temp_list, indent=0)
                        # Flatten it and strip the tabs
                        temp = " ".join(temp_list).replace(TABS, "")

                        # Remove this space to match the output of XCode
                        temp = temp.replace(" isa", "isa")

                        # Insert the flattened line
                        line_list.append(tabs + TABS + temp)
                    else:

                        # Output the item as is
                        item.generate(line_list, indent=indent)
                line_list.append("/* End {} section */".format(object_group))

        line_list.append("{}}}{}".format(tabs, self.suffix))
        return 0

########################################


class PBXBuildRuleGLSL(JSONDict):
    """
    Create a PBXBuildRule entry for building GLSL files.

    If *.glsl files are found, this rule will invoke stripcomments
    to build the headers out of them.

    This object is referenced by PBXNativeTarget
    """

    def __init__(self, ide):
        """
        Initialize the PBXBuildRule for GLSL

        Args:
            ide: IDE used for build for
        """

        uuid = calcuuid("PBXBuildRule" + "BuildGLSL")

        # Init the parent as a PBXBuildRule
        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXBuildRule",
            comment="PBXBuildRule",
            uuid=uuid)

        # The rule is a bash/zsh script
        self.add_dict_entry("compilerSpec",
                            "com.apple.compilers.proxy.script")

        # Apply to all *.glsl files
        self.add_dict_entry("filePatterns", "*.glsl")

        # filePatterns is a wildcard
        self.add_dict_entry("fileType", "pattern.proxy")

        # XCode 12 and higher needs the list of input files
        if ide >= IDETypes.xcode12:
            input_files = JSONArray("inputFiles")
            self.add_item(input_files)

            # The source file is the only input
            input_files.add_array_entry("${INPUT_FILE_PATH}")

        # This rule can be edited
        self.add_dict_entry("isEditable", "1")

        # Create the list of output files
        output_files = JSONArray("outputFiles")
        self.add_item(output_files)

        # This is the file generated
        output_files.add_array_entry(
            "${INPUT_FILE_DIR}/generated/${INPUT_FILE_BASE}.h")

        # Only build once, don't build for each CPU type
        if ide >= IDETypes.xcode12:
            self.add_dict_entry("runOncePerArchitecture", "0")

        # The actual script to run stripcomments
        self.add_dict_entry(
            "script",
            "${BURGER_SDKS}/macosx/bin/stripcomments "
            "${INPUT_FILE_PATH}"
            " -c -l g_${INPUT_FILE_BASE} "
            "${INPUT_FILE_DIR}/generated/${INPUT_FILE_BASE}.h\\n")

########################################


class PBXFileReference(JSONDict):
    """
    A PBXFileReference entry.

    For each and every file managed by an XCode project, a PBXFileReference
    object will exist to reference it. Other sections of XCode will use the
    UUID of this object to act upon the file referenced by this object.

    The UUID is used for both PBXGroup for file hierachical display and
    PBXBuildFile if the file needs to be built with a compiler.

    Attributes:
        source_file: core.SourceFile record
    """

    def __init__(self, source_file, ide):
        """
        Initialize the PBXFileReference object.

        Args:
            source_file: core.SourceFile record
            ide: IDETypes of the ide being built for.
        """

        # pylint: disable=too-many-branches

        # Sanity check
        if not isinstance(source_file, SourceFile):
            raise TypeError(
                "parameter \"source_file\" must be of type SourceFile")

        # XCode is hosted by MacOSX, so use linux slashes
        relative_pathname = convert_to_linux_slashes(
            source_file.relative_pathname)

        # Generate the UUID
        uuid = calcuuid("PBXFileReference" + relative_pathname)
        basename = os.path.basename(relative_pathname)

        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXFileReference",
            comment=basename,
            uuid=uuid,
            flattened=True)

        # core.SourceFile record
        self.source_file = source_file

        ## Save the MacOS version of the relative pathname
        self.relative_pathname = relative_pathname

        # If not binary, assume UTF-8 encoding
        if source_file.type not in (FileTypes.library, FileTypes.exe,
                                    FileTypes.frameworks):
            self.add_dict_entry("fileEncoding", "4")

        # If an output file, determine the output type and mark
        # as "explicitFileType"
        if source_file.type in (FileTypes.library, FileTypes.exe):
            if source_file.type is FileTypes.library:
                value = "archive.ar"
            elif basename.endswith(".app"):
                value = "wrapper.application"
            else:
                value = "compiled.mach-o.executable"

            self.add_dict_entry("explicitFileType", value)

            # Never add to the index
            self.add_dict_entry("includeInIndex", "0")

        # lastKnownFileType
        value = FILE_REF_LAST_KNOWN.get(source_file.type, "sourcecode.c.h")

        # Library and exe return None
        if value:

            # XCode 3 and 4 doesn't support sourcecode.glsl
            # Use sourcecode instead
            if ide < IDETypes.xcode5:
                if value.endswith(".glsl"):
                    value = "sourcecode"

            self.add_dict_entry("lastKnownFileType", value)

        # name record
        if source_file.type not in (FileTypes.library, FileTypes.exe):
            self.add_dict_entry("name", basename)

        if source_file.type is FileTypes.library:
            value = basename
        elif source_file.type is FileTypes.frameworks:
            value = "System/Library/Frameworks/" + basename
        else:
            value = relative_pathname
        self.add_dict_entry("path", value)

        self.add_dict_entry(
            "sourceTree",
            FILE_REF_DIR.get(source_file.type, "SOURCE_ROOT"))

########################################


class PBXGroup(JSONDict):
    """
    Each PBXGroup entry

    Attributes:
        children: Children list
        group_name: Name of this group
        path: Root path for this group
        group_list: List of child groups
        file_list: List of child files
    """

    def __init__(self, group_name, path):
        """
        Init the PBXGroup.
        """

        # Create uuid, and handle an empty path
        uuid_path = path
        if path is None:
            uuid_path = "<group>"
        uuid = calcuuid("PBXGroup" + group_name + uuid_path)

        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXGroup",
            comment=group_name,
            uuid=uuid)

        self.group_name = group_name
        self.path = path
        self.group_list = []
        self.file_list = []

        children = JSONArray("children")
        self.add_item(children)
        self.children = children

        self.add_dict_entry(
            "name", group_name).enabled = path is None or group_name != path

        self.add_dict_entry("path", path).enabled = path is not None

        # Source tree root path
        value = "SOURCE_ROOT" if path is not None else "<group>"
        self.add_dict_entry("sourceTree", value)

    def is_empty(self):
        """
        Return True if there are no entries in this group.

        Returns:
            True if this PBXGroup has no entries.
        """

        return not (self.group_list or self.file_list)

    def add_file(self, file_reference):
        """
        Append a file uuid and name to the end of the list.

        Args:
            file_reference: PBXFileReference item to attach to this group.
        """

        # Sanity check
        if not isinstance(file_reference, PBXFileReference):
            raise TypeError(
                "parameter \"file_reference\" must be of type PBXFileReference")

        self.file_list.append(
            (file_reference.uuid, os.path.basename(
                file_reference.relative_pathname)))

    def add_group(self, group):
        """
        Append a group to the end of the list.

        Args:
            group: PBXGroup item to attach to this group.
        """

        # Sanity check
        if not isinstance(group, PBXGroup):
            raise TypeError(
                "parameter \"group\" must be of type PBXGroup")

        self.group_list.append((group.uuid, group.group_name))

    def generate(self, line_list, indent=0):
        """
        Write this record to output.

        Args:
            line_list: Line list to append new lines.
            indent: number of tabs to insert (For recursion)
        """

        # Output groups first
        for item in sorted(self.group_list, key=itemgetter(1)):
            self.children.add_array_entry(item[0]).comment = item[1]

        # Output files last
        for item in sorted(self.file_list, key=itemgetter(1)):
            self.children.add_array_entry(item[0]).comment = item[1]

        return JSONDict.generate(self, line_list, indent)


########################################


class PBXBuildFile(JSONDict):
    """
    Create a PBXBuildFile entry

    Attributes:
        file_reference: PBXFileReference of the file being compiled
    """

    def __init__(self, input_reference, output_reference):
        """
        Init the PBXBuildFile record.

        Args:
            input_reference: File reference of object to build
            output_reference: File reference of lib/exe being built.
        """

        # Sanity check
        if not isinstance(input_reference, PBXFileReference):
            raise TypeError(
                "parameter \"input_reference\""
                " must be of type PBXFileReference")

        if not isinstance(output_reference, PBXFileReference):
            raise TypeError(
                "parameter \"output_reference\""
                " must be of type PBXFileReference")

        # Make the uuid
        uuid = calcuuid(
            "PBXBuildFile" +
            input_reference.relative_pathname +
            output_reference.relative_pathname)

        basename = os.path.basename(
            input_reference.relative_pathname)

        ref_type = "Frameworks" \
            if input_reference.source_file.type is FileTypes.frameworks \
            else "Sources"

        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXBuildFile",
            comment="{} in {}".format(basename, ref_type),
            uuid=uuid,
            flattened=True)

        # PBXFileReference of the file being compiled
        self.file_reference = input_reference

        # Add the uuid of the file reference
        self.add_dict_entry(
            "fileRef", input_reference.uuid).comment = basename

########################################


class PBXShellScriptBuildPhase(JSONDict):
    """
    Each PBXShellScriptBuildPhase entry

    Attributes:
        files: JSONArray of files
    """

    def __init__(self, input_data, output, command):
        """
        Init PBXShellScriptBuildPhase

        Args:
            input_data: Input file references
            output: String for the output file that will be built
            command: Script to build
        """

        # Get the UUID
        uuid = calcuuid(
            "PBXShellScriptBuildPhase" + "".join(input_data) +
            output + command)

        # Init the parent
        JSONDict.__init__(
            self,
            name=uuid,
            isa="PBXShellScriptBuildPhase",
            comment="ShellScript",
            uuid=uuid)

        self.add_dict_entry("buildActionMask", "2147483647")

        # Internal files, if any
        files = JSONArray("files")
        self.files = files
        self.add_item(files)

        # Paths to input files
        input_paths = JSONArray("inputPaths", disable_if_empty=True)
        for item in input_data:
            input_paths.add_array_entry(item)
        self.add_item(input_paths)

        # Path to the output file
        output_paths = JSONArray("outputPaths")
        output_paths.add_array_entry(output)
        self.add_item(output_paths)

        # Always run
        self.add_dict_entry(
            "runOnlyForDeploymentPostprocessing", "0")

        # Path to the shell
        self.add_dict_entry("shellPath", "/bin/sh")

        # The actual script to run
        self.add_dict_entry("shellScript", "{}\\n".format(command))

        # Don't show the environment variables
        self.add_dict_entry("showEnvVarsInLog", "0")

    @staticmethod
    def get_phase_name():
        """
        Return the build phase name for XCode.
        """
        return "ShellScript"


########################################

def copy_tool_to_bin():
    """
    Create a PBXShellScriptBuildPhase to copy to bin

    Create a PBXShellScriptBuildPhase to take a binary tool file,
    append a suffix, and then copy it to a "bin" folder.

    Return:
        PBXShellScriptBuildPhase set up for the operation
    """

    # Get the input file
    input_data = [TEMP_EXE_NAME]

    # Store to bin folder with suffix
    output = ("${SRCROOT}/bin/${EXECUTABLE_PREFIX}${PRODUCT_NAME}"
              "${SUFFIX}${EXECUTABLE_SUFFIX}")

    # Create the bin folder, then perform the copy
    command = (
        "if [ ! -d ${{SRCROOT}}/bin ];"
        " then mkdir ${{SRCROOT}}/bin; fi\\n"
        "${{CP}} {0} {1}").format(TEMP_EXE_NAME, output)

    return PBXShellScriptBuildPhase(input_data, output, command)
