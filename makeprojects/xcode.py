#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sub file for makeprojects.
Handler for Apple Computer XCode projects
"""

# Copyright 1995-2019 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

#
## \package makeprojects.xcode
# This module contains classes needed to generate
# project files intended for use by Apple's XCode IDE
#

from __future__ import absolute_import, print_function, unicode_literals

import hashlib
import os
import operator
import string

from burger import create_folder_if_needed, save_text_file_if_newer, \
    convert_to_windows_slashes, convert_to_linux_slashes
from .enums import FileTypes, ProjectTypes, PlatformTypes, IDETypes
from .core import SourceFile, Configuration
from .core import Project as CoreProject

# pylint: disable=useless-object-inheritance, too-few-public-methods
# pylint: disable=invalid-name

## Default tab format for XCode
TABS = '\t'

## Build executable pathname
TEMP_EXE_NAME = '${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}'

## Valid characters for XCode strings without quoting
_XCODESAFESET = frozenset(string.ascii_letters + string.digits + '_$./')

## Path of the perforce executable
_PERFORCE_PATH = '/opt/local/bin/p4'

## Supported IDE codes for the XCode exporter
SUPPORTED_IDES = (
    IDETypes.xcode3,
    IDETypes.xcode4,
    IDETypes.xcode5,
    IDETypes.xcode6,
    IDETypes.xcode7,
    IDETypes.xcode8,
    IDETypes.xcode9,
    IDETypes.xcode10,
    IDETypes.xcode11)

## Version values
# Tuple of objectVersion, , compatibilityVersion, developmentRegion
OBJECT_VERSIONS = {
    IDETypes.xcode3: ('45', None, 'Xcode 3.1', None),
    IDETypes.xcode4: ('46', '0420', 'Xcode 3.2', 'English'),
    IDETypes.xcode5: ('46', '0510', 'Xcode 3.2', 'English'),
    IDETypes.xcode6: ('47', '0600', 'Xcode 6.3', None),
    IDETypes.xcode7: ('47', '0700', 'Xcode 6.3', None),
    IDETypes.xcode8: ('48', '0800', 'Xcode 8.0', None),
    IDETypes.xcode9: ('50', '0900', 'Xcode 9.3', None),
    IDETypes.xcode10: ('51', '1030', 'Xcode 10.0', None),
    IDETypes.xcode11: ('52', '1100', 'Xcode 11.0', None)
}

## Order of XCode objects
# This is the order of XCode chunks that match the way
# that XCode outputs them.
OBJECT_ORDER = (
    'PBXAggregateTarget',
    'PBXBuildFile',
    'PBXBuildRule',
    'PBXContainerItemProxy',
    'PBXCopyFilesBuildPhase',
    'PBXFileReference',
    'PBXFrameworksBuildPhase',
    'PBXGroup',
    'PBXNativeTarget',
    'PBXProject',
    'PBXReferenceProxy',
    'PBXResourcesBuildPhase',
    'PBXShellScriptBuildPhase',
    'PBXSourcesBuildPhase',
    'PBXTargetDependency',
    'XCBuildConfiguration',
    'XCConfigurationList'
)

## List of XCode objects that flatten their children
FLATTENED_OBJECTS = (
    'PBXBuildFile',
    'PBXFileReference'
)

## List of XCBuildConfiguration settings for compilation
# Name, type, default
XCBUILD_FLAGS = (
    # Locations of any sparse SDKs
    ('ADDITIONAL_SDKS', 'string', None),

    # Group permission of deployment
    ('ALTERNATE_GROUP', 'string', None),

    # File permissions of deployment
    ('ALTERNATE_MODE', 'string', None),

    # Owner permission of deployment
    ('ALTERNATE_OWNER', 'string', None),

    # Specific files to apply deployment permissions
    ('ALTERNATE_PERMISSIONS_FILES', 'string', None),

    # Always search user paths in C++
    ('ALWAYS_SEARCH_USER_PATHS', 'boolean', None),

    # Copy Files Build Phase will plist and strings to encoding
    ('APPLY_RULES_IN_COPY_FILES', 'boolean', None),

    # Default CPUs
    ('ARCHS', 'stringarray', None),

    # List of build variants
    ('BUILD_VARIANTS', 'stringarray', None),

    # Name of executable that loads the bundle
    ('BUNDLE_LOADER', 'string', None),

    # Name of the code signing certificate
    ('CODE_SIGN_IDENTITY', 'string', None),

    # Path to property list containing rules for signing
    ('CODE_SIGN_RESOURCE_RULES_PATH', 'string', None),

    # Path for build products
    ('CONFIGURATION_BUILD_DIR', 'string',
     '$(SYMROOT)/$(PRODUCT_NAME)$(SUFFIX)'),

    # Path for temp files
    ('CONFIGURATION_TEMP_DIR', 'string',
     '$(SYMROOT)/$(PRODUCT_NAME)$(SUFFIX)'),

    # Does copying preserve classic mac resource forks?
    ('COPYING_PRESERVES_HFS_DATA', 'boolean', None),

    # Strip debug symbols?
    ('COPY_PHASE_STRIP', 'boolean', None),

    # Numeric project version
    ('CURRENT_PROJECT_VERSION', 'string', None),

    # Strip dead code?
    ('DEAD_CODE_STRIPPING', 'boolean', 'YES'),

    # Type of debug symbols
    ('DEBUG_INFORMATION_FORMAT', 'string', 'dwarf'),

    # Are there valid deployment location settings?
    ('DEPLOYMENT_LOCATION', 'boolean', None),

    # Process deployment files
    ('DEPLOYMENT_POSTPROCESSING', 'boolean', None),

    # Destination root folder for deployment
    ('DSTROOT', 'string', None),

    # Compatible version of the dynamic library
    ('DYLIB_COMPATIBILITY_VERSION', 'string', None),

    # Numeric version of the dynamic library
    ('DYLIB_CURRENT_VERSION', 'string', None),

    # Enable OpenMP
    ('ENABLE_OPENMP_SUPPORT', 'boolean', None),

    # Files and folders to ignore on search.
    ('EXCLUDED_RECURSIVE_SEARCH_PATH_SUBDIRECTORIES', 'string', None),

    # Extension for executables
    ('EXECUTABLE_EXTENSION', 'string', None),

    # Prefix for executables
    ('EXECUTABLE_PREFIX', 'string', None),

    # File with symbols to export
    ('EXPORTED_SYMBOLS_FILE', 'string', None),

    # Array of directories to search for Frameworks
    ('FRAMEWORK_SEARCH_PATHS', 'stringarray', None),

    # Version of the framework being generated
    ('FRAMEWORK_VERSION', 'string', None),

    # PowerPC only, enable altivec
    ('GCC_ALTIVEC_EXTENSIONS', 'boolean', None),

    # Enable vectorization on loops
    ('GCC_AUTO_VECTORIZATION', 'boolean', None),

    # Default 'char' to unsigned if set to true
    ('GCC_CHAR_IS_UNSIGNED_CHAR', 'boolean', None),

    # It true, assume no exceptions on new()
    ('GCC_CHECK_RETURN_VALUE_OF_OPERATOR_NEW', 'boolean', None),

    # Use CodeWarrior inline assembly syntax
    ('GCC_CW_ASM_SYNTAX', 'boolean', 'YES'),

    # Use the latest version of the Objective C++ dialect
    ('GCC_C_LANGUAGE_STANDARD', 'string', 'gnu99'),

    # Sets the level of debugging symbols in the output
    ('GCC_DEBUGGING_SYMBOLS', 'string', None),

    # Set YES for no relocatable code
    ('GCC_DYNAMIC_NO_PIC', 'boolean', 'NO'),
    ('GCC_DYNAMIC_NO_PIC[arch=i386]', 'boolean', 'YES'),
    ('GCC_DYNAMIC_NO_PIC[arch=ppc64]', 'boolean', 'YES'),
    ('GCC_DYNAMIC_NO_PIC[arch=ppc]', 'boolean', 'YES'),

    # Enable the asm keyword
    ('GCC_ENABLE_ASM_KEYWORD', 'boolean', None),

    # Enable built in functions like memcpy().
    ('GCC_ENABLE_BUILTIN_FUNCTIONS', 'boolean', None),

    # Disable CPP Exceptions
    ('GCC_ENABLE_CPP_EXCEPTIONS', 'boolean', 'NO'),

    # Disable CPP RTTI
    ('GCC_ENABLE_CPP_RTTI', 'boolean', 'NO'),

    # Build everything as Objective C++
    ('GCC_INPUT_FILETYPE', 'string', 'sourcecode.cpp.objcpp'),

    # Program flow for profiling.
    ('GCC_INSTRUMENT_PROGRAM_FLOW_ARCS', 'boolean', None),

    # Link with static to dynamic libraries
    ('GCC_LINK_WITH_DYNAMIC_LIBRARIES', 'boolean', None),

    # Enable 64 bit registers for powerpc 64 bit
    ('GCC_MODEL_PPC64', 'boolean', 'NO'),
    ('GCC_MODEL_PPC64[arch=ppc64]', 'boolean', 'YES'),

    # Tune for specific cpu
    ('GCC_MODEL_TUNING', 'string', 'G4'),
    ('GCC_MODEL_TUNING[arch=ppc64]', 'string', 'G5'),

    # Don't share global variables
    ('GCC_NO_COMMON_BLOCKS', 'boolean', None),

    # Call C++ constuctors on objective-c code
    ('GCC_OBJC_CALL_CXX_CDTORS', 'boolean', None),

    # bool takes one byte, not 4
    ('GCC_ONE_BYTE_BOOL', 'boolean', None),

    # Optimizations level
    ('GCC_OPTIMIZATION_LEVEL', 'string', 's'),

    # C++ dialects
    ('GCC_PFE_FILE_C_DIALECTS', 'string', None),

    # Use a precompiled header
    ('GCC_PRECOMPILE_PREFIX_HEADER', 'boolean', None),

    # Name of the precompiled header
    ('GCC_PREFIX_HEADER', 'string', None),

    # Defines
    ('GCC_PREPROCESSOR_DEFINITIONS', 'stringarray', None),

    # Disabled defines
    ('GCC_PREPROCESSOR_DEFINITIONS_NOT_USED_IN_PRECOMPS', 'string', None),

    # Reuse constant strings
    ('GCC_REUSE_STRINGS', 'boolean', None),

    # Shorten enums
    ('GCC_SHORT_ENUMS', 'boolean', None),

    # Use strict aliasing
    ('GCC_STRICT_ALIASING', 'boolean', None),

    # Assume extern symbols are private
    ('GCC_SYMBOLS_PRIVATE_EXTERN', 'boolean', None),

    # Don't emit code to make the static constructors thread safe
    ('GCC_THREADSAFE_STATICS', 'boolean', 'NO'),

    # Causes warnings about missing function prototypes to become errors
    ('GCC_TREAT_IMPLICIT_FUNCTION_DECLARATIONS_AS_ERRORS', 'boolean', None),

    # Non conformant code errors become warnings.
    ('GCC_TREAT_NONCONFORMANT_CODE_ERRORS_AS_WARNINGS', 'boolean', None),

    # Warnings are errors
    ('GCC_TREAT_WARNINGS_AS_ERRORS', 'boolean', None),

    # Enable unrolling loops
    ('GCC_UNROLL_LOOPS', 'boolean', None),

    # Allow native prcompiling support
    ('GCC_USE_GCC3_PFE_SUPPORT', 'boolean', None),

    # Default to using a register for all function calls
    ('GCC_USE_INDIRECT_FUNCTION_CALLS', 'boolean', None),

    # Default to long calls
    ('GCC_USE_REGISTER_FUNCTION_CALLS', 'boolean', None),

    # Allow searching default system include folders.
    ('GCC_USE_STANDARD_INCLUDE_SEARCHING', 'boolean', None),

    # Which compiler to use
    ('GCC_VERSION', 'string', 'com.apple.compilers.llvm.clang.1_0'),

    # Note: com.apple.compilers.llvmgcc42 generates BAD CODE for ppc64 and 4.2
    # doesn't work at all for ppc64. Only gcc 4.0 is safe for ppc64
    # i386 compiler llvmgcc42 has issues with 64 bit code in xcode3
    ('GCC_VERSION[sdk=macosx10.4]', 'string', 'com.apple.compilers.llvmgcc42'),
    ('GCC_VERSION[sdk=macosx10.5]', 'string', 'com.apple.compilers.llvmgcc42'),
    ('GCC_VERSION[sdk=macosx10.5][arch=i386]', 'string', '4.2'),
    ('GCC_VERSION[sdk=macosx10.5][arch=ppc64]', 'string', '4.0'),

    # Warn of 64 bit value become 32 bit automatically
    ('GCC_WARN_64_TO_32_BIT_CONVERSION', 'boolean', 'YES'),

    # Warn about deprecated functions
    ('GCC_WARN_ABOUT_DEPRECATED_FUNCTIONS', 'boolean', None),

    # Warn about invalid use of offsetof()
    ('GCC_WARN_ABOUT_INVALID_OFFSETOF_MACRO', 'boolean', None),

    # Warn about missing ending newline in source code.
    ('GCC_WARN_ABOUT_MISSING_NEWLINE', 'boolean', None),

    # Warn about missing function prototypes
    ('GCC_WARN_ABOUT_MISSING_PROTOTYPES', 'boolean', 'YES'),

    # Warn if the sign of a pointer changed.
    ('GCC_WARN_ABOUT_POINTER_SIGNEDNESS', 'boolean', 'YES'),

    # Warn if return type is missing a value.
    ('GCC_WARN_ABOUT_RETURN_TYPE', 'boolean', 'YES'),

    # Objective-C Warn if required methods are missing in class implementation
    ('GCC_WARN_ALLOW_INCOMPLETE_PROTOCOL', 'boolean', 'YES'),

    # Warn if a switch statement is missing enumeration entries
    ('GCC_WARN_CHECK_SWITCH_STATEMENTS', 'boolean', 'YES'),

    # Warn if Effective C++ violations are present.
    ('GCC_WARN_EFFECTIVE_CPLUSPLUS_VIOLATIONS', 'boolean', None),

    # Warn is macOS stype 'APPL' 4 character constants exist.
    ('GCC_WARN_FOUR_CHARACTER_CONSTANTS', 'boolean', None),

    # Warn if virtual functions become hidden.
    ('GCC_WARN_HIDDEN_VIRTUAL_FUNCTIONS', 'boolean', 'YES'),

    # Disable all warnings.
    ('GCC_WARN_INHIBIT_ALL_WARNINGS', 'boolean', None),

    # Warn if union initializers are not fully bracketed.
    ('GCC_WARN_INITIALIZER_NOT_FULLY_BRACKETED', 'boolean', 'NO'),

    # Warn if parentheses are missing from nested statements.
    ('GCC_WARN_MISSING_PARENTHESES', 'boolean', 'YES'),

    # Warn if a class didn't declare its destructor as virtual if derived.
    ('GCC_WARN_NON_VIRTUAL_DESTRUCTOR', 'boolean', 'YES'),

    # Warn if non-C++ standard keywords are used
    ('GCC_WARN_PEDANTIC', 'boolean', None),

    # Warn if implict type conversions occur.
    ('GCC_WARN_PROTOTYPE_CONVERSION', 'boolean', 'YES'),

    # Warn if a variable becomes shadowed.
    ('GCC_WARN_SHADOW', 'boolean', 'YES'),

    # Warn if signed and unsigned values are compared.
    ('GCC_WARN_SIGN_COMPARE', 'boolean', None),

    # Validate printf() and scanf().
    ('GCC_WARN_TYPECHECK_CALLS_TO_PRINTF', 'boolean', 'YES'),

    # Warn if a variable is clobbered by setjmp() or not initialized.
    ('GCC_WARN_UNINITIALIZED_AUTOS', 'boolean', 'YES'),

    # Warn if a pragma is used that's not know by this compiler.
    ('GCC_WARN_UNKNOWN_PRAGMAS', 'boolean', None),

    # Warn if a static function is never used.
    ('GCC_WARN_UNUSED_FUNCTION', 'boolean', 'YES'),

    # Warn if a label is declared but not used.
    ('GCC_WARN_UNUSED_LABEL', 'boolean', 'YES'),

    # Warn if a function parameter isn't used.
    ('GCC_WARN_UNUSED_PARAMETER', 'boolean', 'YES'),

    # Warn if a value isn't used.
    ('GCC_WARN_UNUSED_VALUE', 'boolean', 'YES'),

    # Warn if a variable isn't used.
    ('GCC_WARN_UNUSED_VARIABLE', 'boolean', 'YES'),

    # Merge object files into a single file (static libraries)
    ('GENERATE_MASTER_OBJECT_FILE', 'boolean', None),

    # Force generating a package information file
    ('GENERATE_PKGINFO_FILE', 'boolean', None),

    # Insert profiling code
    ('GENERATE_PROFILING_CODE', 'boolean', 'NO'),

    # List of search paths for headers
    ('HEADER_SEARCH_PATHS', 'stringarray', None),

    # Directories for recursive search
    ('INCLUDED_RECURSIVE_SEARCH_PATH_SUBDIRECTORIES', 'string', None),

    # Expand the build settings in the plist file
    ('INFOPLIST_EXPAND_BUILD_SETTINGS', 'boolean', None),

    # Name of the plist file
    ('INFOPLIST_FILE', 'string', None),

    # Preprocessor flags for the plist file
    ('INFOPLIST_OTHER_PREPROCESSOR_FLAGS', 'string', None),

    # Output file format for the plist
    ('INFOPLIST_OUTPUT_FORMAT', 'string', None),

    # Prefix header for plist
    ('INFOPLIST_PREFIX_HEADER', 'string', None),

    # Allow preprocessing of the plist file
    ('INFOPLIST_PREPROCESS', 'boolean', None),

    # Defines for the plist file
    ('INFOPLIST_PREPROCESSOR_DEFINITIONS', 'stringarray', None),

    # Initialization routine name
    ('INIT_ROUTINE', 'string', None),

    # BSD group to attach for the installed executable
    ('INSTALL_GROUP', 'string', None),

    # File mode flags for installed executable
    ('INSTALL_MODE_FLAG', 'string', None),

    # Owner account for installed executable
    ('INSTALL_OWNER', 'string', None),

    # Path for installed executable
    ('INSTALL_PATH', 'string', None),

    # Keep private externs private
    ('KEEP_PRIVATE_EXTERNS', 'boolean', None),

    # Change the interal  name of the dynamic library
    ('LD_DYLIB_INSTALL_NAME', 'string', None),

    # Generate a map file for dynamic libraries
    ('LD_GENERATE_MAP_FILE', 'boolean', None),

    # Path for the map file
    ('LD_MAP_FILE_PATH', 'string', None),

    # Flags to pass to a library using OpenMP
    ('LD_OPENMP_FLAGS', 'string', None),

    # List of paths to search for a library
    ('LD_RUNPATH_SEARCH_PATHS', 'string', None),

    # List of directories to search for libraries
    ('LIBRARY_SEARCH_PATHS', 'stringarray', None),

    # Display mangled names in linker
    ('LINKER_DISPLAYS_MANGLED_NAMES', 'boolean', None),

    # Link the standard libraries
    ('LINK_WITH_STANDARD_LIBRARIES', 'boolean', None),

    # Type of Mach-O file
    ('MACH_O_TYPE', 'string', 'mh_execute'),

    # Deployment minimum OS
    ('MACOSX_DEPLOYMENT_TARGET', 'string', '10.4'),

    # Kernel module name
    ('MODULE_NAME', 'string', None),

    # Kernel driver start function name
    ('MODULE_START', 'string', None),

    # Kernel driver stop function name
    ('MODULE_STOP', 'string', None),

    # Version number of the kernel driver
    ('MODULE_VERSION', 'string', None),

    # Root folder for intermediate files
    ('OBJROOT', 'string', 'temp'),

    # If YES, only build the active CPU for fast recompilation
    ('ONLY_ACTIVE_ARCH', 'boolean', 'NO'),

    # Path to file for order of functions to link
    ('ORDER_FILE', 'string', None),

    # Extra flags to pass to the C compiler
    ('OTHER_CFLAGS', 'string', None),

    # Extra flags to pass to the code sign tool
    ('OTHER_CODE_SIGN_FLAGS', 'string', None),

    # Extra flags to pass to the C++ compiler
    ('OTHER_CPLUSPLUSFLAGS', 'string', None),

    # Extra flags to pass to the linker
    ('OTHER_LDFLAGS', 'string', None),

    # Extra flags to pass to the unit test tool
    ('OTHER_TEST_FLAGS', 'string', None),

    # Output file format for the plist file
    ('PLIST_FILE_OUTPUT_FORMAT', 'string', None),

    # Prebind the functions together
    ('PREBINDING', 'boolean', 'YES'),

    # Include headers included in precompiler header
    ('PRECOMPS_INCLUDE_HEADERS_FROM_BUILT_PRODUCTS_DIR', 'boolean', None),

    # Flags to pass for pre-linker
    ('PRELINK_FLAGS', 'string', None),

    # Libraries to use for pre-linking
    ('PRELINK_LIBS', 'string', None),

    # Don't deleate dead code initializers
    ('PRESERVE_DEAD_CODE_INITS_AND_TERMS', 'boolean', None),

    # Path to copy private headers for building
    ('PRIVATE_HEADERS_FOLDER_PATH', 'string', None),

    # Product name
    ('PRODUCT_NAME', 'string', '$(TARGET_NAME)'),

    # Path to copy public headers for building
    ('PUBLIC_HEADERS_FOLDER_PATH', 'string', None),

    # Paths to search for rez
    ('REZ_SEARCH_PATHS', 'string', None),

    # Scan source code for include files for dependency graph generation.
    ('SCAN_ALL_SOURCE_FILES_FOR_INCLUDES', 'boolean', None),

    # SDK to use to for this build
    ('SDKROOT', 'string', 'macosx10.5'),

    # Flags for the section reordering
    ('SECTORDER_FLAGS', 'string', None),

    # Strip symbols in a seperate pass
    ('SEPARATE_STRIP', 'boolean', None),

    # Edit symbols with nmedit
    ('SEPARATE_SYMBOL_EDIT', 'boolean', None),

    # Path for directory for precompiled header files
    ('SHARED_PRECOMPS_DIR', 'string', None),

    # Skip the install phase in deployment
    ('SKIP_INSTALL', 'boolean', None),

    # Type of libary for Standard C
    ('STANDARD_C_PLUS_PLUS_LIBRARY_TYPE', 'string', None),

    # Encoding for Strings file for localization
    ('STRINGS_FILE_OUTPUT_ENCODING', 'string', 'UTF-8'),

    # Flags to pass to the symbol stripper
    ('STRIPFLAGS', 'string', None),

    # Set to YES to strip symbols from installed product
    ('STRIP_INSTALLED_PRODUCT', 'boolean', None),

    # Style of symbol stripping
    ('STRIP_STYLE', 'string', None),

    # Custom label for configuration short code
    ('SUFFIX', 'string', 'osxrel'),

    # Products are placed in this folder
    ('SYMROOT', 'string', 'temp'),

    # Path to the executable that accepts unit test bundles
    ('TEST_HOST', 'string', None),

    # Path to unit test tool
    ('TEST_RIG', 'string', None),

    # Path to file with symbols to NOT export
    ('UNEXPORTED_SYMBOLS_FILE', 'string', None),

    # Paths to user headers
    ('USER_HEADER_SEARCH_PATHS', 'string', None),

    # List of allowable cpu architectures
    ('VALID_ARCHS', 'string', None),

    # Name of the executable that creates the version info.
    ('VERSIONING_SYSTEM', 'string', None),

    # User name of the invoker of the version tool
    ('VERSION_INFO_BUILDER', 'string', None),

    # Allow exporting the version information
    ('VERSION_INFO_EXPORT_DECL', 'string', None),

    # Name of the file for version information
    ('VERSION_INFO_FILE', 'string', None),

    # Version info prefix
    ('VERSION_INFO_PREFIX', 'string', None),

    # Version info suffix
    ('VERSION_INFO_SUFFIX', 'string', None),

    # List of additional warning flags to pass to the compiler.
    ('WARNING_CFLAGS', 'stringarray', None),

    # List of additional warning flags to pass to the linker.
    ('WARNING_LDFLAGS', 'stringarray', None),

    # Extension for product wrappers
    ('WRAPPER_EXTENSION', 'string', None)
)

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
        PlatformTypes.ios32, PlatformTypes.ios64,
        PlatformTypes.iosemu32, PlatformTypes.iosemu64)

########################################


def calcuuid(input_str):
    """
    Given a string, create a 96 bit unique hash for XCode

    Args:
        input_str: string to hash
    Return:
        96 bit hash string in upper case.
    """

    temphash = hashlib.md5(convert_to_windows_slashes(
        input_str).encode('utf-8')).hexdigest()

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
            return '""'
        return input_path

    # Quote the escaped string.
    return '"{}"'.format(input_path.replace('"', '\\"'))

########################################


class JSONRoot(object):
    """
    XCode JSON root object

    Every JSON entry for XCode derives from this object and has a minimum of a
    name, comment, uuid and an enabled flag.
    """

    def __init__(self, name, comment=None, uuid=None,
                 suffix=';', enabled=True, value=None):
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

        # pylint: disable=too-many-arguments

        ## Object's name (Can also be the uuid)
        self.name = name

        ## Optional object's comment field
        self.comment = comment

        ## Optional uuid
        self.uuid = uuid

        ## If True, output this object in generated output.
        self.enabled = enabled

        ## Optional suffix used in generated output.
        self.suffix = suffix

        ## Value
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

    def __init__(self, name, comment=None, value=None,
                 suffix=';', enabled=True):
        """
        Initialize the JSONEntry.

        Args:
            name: Name of this object
            comment: Optional comment
            value: Optional value
            suffix: string to append at the end of the generated line of output.
            enabled: If False, don't output this object in the generated object.
        """

        # pylint: disable=too-many-arguments

        JSONRoot.__init__(
            self,
            name=name,
            comment=comment,
            suffix=suffix,
            enabled=enabled,
            value=value)

    def generate(self, line_list, indent=0):
        """
        Generate the text lines for this XML element.

        Args:
            line_list: list object to have text lines appended to
            indent: number of tabs to insert (For recursion)
        """

        if not self.enabled:
            return 0

        # Determine the indentation
        tabs = TABS * indent

        # Set the value string
        value = '' if self.value is None else ' = ' + \
            quote_string_if_needed(self.value)

        # Set the comment string
        comment = '' if self.comment is None else ' /* {} */'.format(
            self.comment)

        line_list.append(
            '{}{}{}{}{}'.format(
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
    """

    def __init__(self, name, comment=None, value=None, suffix=';',
                 enabled=True, disable_if_empty=False):
        """
        Initialize the entry.

        Args:
            name: Name of this object
            comment: Optional comment
            value: List of default values
            suffix: Suffix, either ';' or ','
            enabled: If False, don't output this object in the generated object.
            disable_if_empty: If True, don't output if no items in the list.
        """

        # pylint: disable=too-many-arguments

        if value is None:
            value = []

        JSONRoot.__init__(
            self,
            name=name,
            comment=comment,
            suffix=suffix,
            enabled=enabled,
            value=value)

        ## True if output is disabled if the list is empty
        self.disable_if_empty = disable_if_empty

    def generate(self, line_list, indent=0):
        """
        Generate the text lines for this XML element.
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
        comment = '' if self.comment is None else ' /* {} */'.format(
            self.comment)

        # Generate the array opening
        line_list.append('{}{}{} = ('.format(tabs, self.name, comment))

        # Generate the array
        for item in self.value:
            item.generate(line_list, indent=indent)

        # Generate the array closing
        line_list.append('{}){}'.format(tabs, self.suffix))
        return 0


def make_jsonarray(input_array):
    """
    Convert an iterable of strings into JSONArray entries.

    Args:
        input_array: Iterable of strings.
    Returns:
        list of JSONEntry items.
    """

    result = []
    for item in input_array:
        result.append(JSONEntry(item, suffix=','))
    return result

########################################


class JSONDict(JSONRoot):
    """
    XCode JSON dictionary

    Each JSON entry for XCode consists of the name followed by an optional
    comment, and an optional value and then a mandatory suffix.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, name, isa=None, comment=None, value=None,
                 suffix=';', uuid=None, enabled=True, disable_if_empty=False):
        """
        Initialize the entry.

        Args:
            name: Name of this object
            isa: "Is a" type of dictionary object
            comment: Optional comment
            value: List of default values
            suffix: Suffix, either ';' or ','
            uuid: uuid hash of the object
            enabled: If False, don't output this object in the generated object.
            disable_if_empty: If True, don't output if no items in the list.
        """

        if uuid is None:
            uuid = ''

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

        ## True if output is disabled if the list is empty
        self.disable_if_empty = disable_if_empty

        ## "Is a" name
        self.isa = isa

        if isa is not None:
            self.add_item(JSONEntry('isa', value=isa))

    def generate(self, line_list, indent=0):
        """
        Generate the text lines for this XML element.
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
        comment = '' if self.comment is None else ' /* {} */'.format(
            self.comment)

        # Generate the dictionary opening
        line_list.append('{}{}{} = {{'.format(tabs, self.name, comment))

        # Generate the dictionary
        for item in self.value:
            item.generate(line_list, indent=indent)

        # Generate the dictionary closing
        line_list.append('{}}}{}'.format(tabs, self.suffix))
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
        Generate the text lines for this XML element.
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
        comment = '' if self.comment is None else ' /* {} */'.format(
            self.comment)

        # Generate the dictionary opening
        line_list.append('{}{}{} = {{'.format(tabs, self.name, comment))

        # Output the objects in "isa" order for XCode
        for object_group in OBJECT_ORDER:
            item_list = []
            for item in self.value:
                if item.isa == object_group:
                    item_list.append(item)

            if item_list:

                # Sort by uuid
                item_list = sorted(item_list, key=operator.attrgetter('uuid'))

                # Using the name of the class, output the array of data items
                line_list.append('')
                line_list.append('/* Begin {} section */'.format(object_group))
                for item in item_list:

                    # Because Apple hates me. Flatten these records instead
                    # of putting the data on individual lines, because, just
                    # because.

                    if object_group in FLATTENED_OBJECTS:
                        # Generate the lines
                        temp_list = []
                        item.generate(temp_list, indent=0)
                        # Flatten it and strip the tabs
                        temp = ' '.join(temp_list).replace(TABS, '')

                        # Remove this space to match the output of XCode
                        temp = temp.replace(' isa', 'isa')

                        # Insert the flattened line
                        line_list.append(tabs + TABS + temp)
                    else:

                        # Output the item as is
                        item.generate(line_list, indent=indent)
                line_list.append('/* End {} section */'.format(object_group))

        line_list.append('{}}}{}'.format(tabs, self.suffix))
        return 0

########################################


class PBXBuildFile(JSONDict):
    """
    Create a PBXBuildFile entry
    """

    def __init__(self, file_reference, output_reference):
        """
        Init the PBXBuildFile record.

        Args:
            file_reference: File reference of object to build
            output_reference: File reference of lib/exe being built.
        """

        # Sanity check
        if not isinstance(file_reference, PBXFileReference):
            raise TypeError(
                "parameter 'file_reference' must be of type PBXFileReference")

        if not isinstance(output_reference, PBXFileReference):
            raise TypeError(
                "parameter 'output_reference' must be of type PBXFileReference")

        # Make the uuid
        uuid = calcuuid(
            'PBXBuildFile' +
            file_reference.source_file.relative_pathname +
            output_reference.source_file.relative_pathname)

        basename = os.path.basename(
            file_reference.source_file.relative_pathname)

        ref_type = 'Frameworks' \
            if file_reference.source_file.type is FileTypes.frameworks \
            else 'Sources'

        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXBuildFile',
            comment='{} in {}'.format(basename, ref_type),
            uuid=uuid)

        # Add the uuid of the file reference
        self.add_item(
            JSONEntry(
                name='fileRef',
                value=file_reference.uuid,
                comment=basename))

        ## PBXFileReference of the file being compiled
        self.file_reference = file_reference

########################################


class BuildGLSL(JSONDict):
    """
    Each PBXBuildRule entry for building GLSL files.
    """

    def __init__(self):
        """
        Initialize the PBXBuildRule for GLSL
        """

        uuid = calcuuid('PBXBuildRule' 'BuildGLSL')

        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXBuildRule',
            comment='PBXBuildRule',
            uuid=uuid)

        self.add_item(
            JSONEntry(
                name='compilerSpec',
                value='com.apple.compilers.proxy.script'))
        self.add_item(JSONEntry(name='filePatterns', value='*.glsl'))
        self.add_item(JSONEntry(name='fileType', value='pattern.proxy'))
        self.add_item(JSONEntry(name='isEditable', value='1'))

        output_files = JSONArray(name='outputFiles')
        self.add_item(output_files)

        output_files.add_item(
            JSONEntry(
                '${INPUT_FILE_DIR}/generated/${INPUT_FILE_BASE}.h',
                suffix=','))
        self.add_item(
            JSONEntry(
                name='script',
                value='${BURGER_SDKS}/macosx/bin/stripcomments '
                '${INPUT_FILE_PATH}'
                ' -c -l g_${INPUT_FILE_BASE} '
                '${INPUT_FILE_DIR}/generated/${INPUT_FILE_BASE}.h'))

########################################


class PBXContainerItemProxy(JSONDict):
    """
    Each PBXContainerItemProxy entry
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
                "parameter 'native_target' must be of type PBXNativeTarget")

        uuid = calcuuid('PBXContainerItemProxy' + native_target.target_name)
        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXContainerItemProxy',
            comment='PBXContainerItemProxy',
            uuid=uuid)
        self.add_item(
            JSONEntry(
                name='containerPortal',
                value=project_uuid,
                comment='Project object'))
        self.add_item(JSONEntry(name='proxyType', value='1'))
        self.add_item(
            JSONEntry(
                name='remoteGlobalIDString',
                value=native_target.uuid))
        self.add_item(
            JSONEntry(
                name='remoteInfo',
                value='"{}"'.format(
                    native_target.target_name)))

        ## PBXNativeTarget to build.
        self.native_target = native_target


########################################

## Dictionary for mapping FileTypes to XCode file types
FILE_REF_LAST_KNOWN = {
    FileTypes.library: None,
    FileTypes.exe: None,
    FileTypes.frameworks: 'wrapper.framework',
    FileTypes.glsl: 'sourcecode.glsl',
    FileTypes.xml: 'text.xml',
    FileTypes.xcconfig: 'text.xcconfig',
    FileTypes.cpp: 'sourcecode.cpp.cpp',
    FileTypes.h: 'sourcecode.c.h'
}

## Map of root directories
FILE_REF_DIR = {
    FileTypes.library: 'BUILT_PRODUCTS_DIR',
    FileTypes.exe: 'BUILT_PRODUCTS_DIR',
    FileTypes.frameworks: 'SDKROOT',
    FileTypes.cpp: 'SOURCE_ROOT'
}


class PBXFileReference(JSONDict):
    """
    Each PBXFileReference entry.

    Get the filename path and XCode type
    """

    def __init__(self, source_file, ide):
        """
        Initialize the PBXFileReference object.

        Args:
            source_file: core.SourceFile record
            ide: IDETypes of the ide being built for.
        """

        # Sanity check
        if not isinstance(source_file, SourceFile):
            raise TypeError(
                "parameter 'source_file' must be of type SourceFile")

        source_file.relative_pathname = convert_to_linux_slashes(
            source_file.relative_pathname)

        uuid = calcuuid('PBXFileReference' + source_file.relative_pathname)
        basename = os.path.basename(source_file.relative_pathname)

        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXFileReference',
            comment=basename,
            uuid=uuid)

        # If not binary, assume UTF-8 encoding
        if source_file.type not in (FileTypes.library, FileTypes.exe,
                                    FileTypes.frameworks):
            self.add_item(JSONEntry(name='fileEncoding', value='4'))

        # If an output file, determine the output type
        if source_file.type in (FileTypes.library, FileTypes.exe):
            value = 'archive.ar' if source_file.type is FileTypes.library \
                else 'wrapper.application' if basename.endswith('.app') else \
                'compiled.mach-o.executable'
            self.add_item(JSONEntry(name='explicitFileType', value=value))
            self.add_item(JSONEntry(name='includeInIndex', value='0'))

        # lastKnownFileType
        value = FILE_REF_LAST_KNOWN.get(source_file.type, 'sourcecode.c.h')
        if value:

            # XCode 3 doesn't support sourcecode.glsl
            if ide < IDETypes.xcode5:
                if value.endswith('.glsl'):
                    value = 'sourcecode'

            self.add_item(JSONEntry(name='lastKnownFileType', value=value))

        if source_file.type not in (FileTypes.library, FileTypes.exe):
            self.add_item(JSONEntry(name='name', value=basename))

        if source_file.type in (FileTypes.library, FileTypes.exe):
            value = basename
        elif source_file.type is FileTypes.frameworks:
            value = 'System/Library/Frameworks/' + basename
        else:
            value = source_file.relative_pathname
        self.add_item(
            JSONEntry(name='path', value=value))

        self.add_item(
            JSONEntry(
                name='sourceTree',
                value=FILE_REF_DIR.get(source_file.type, 'SOURCE_ROOT')))

        ## core.SourceFile record
        self.source_file = source_file


########################################


class PBXFrameworksBuildPhase(JSONDict):
    """
    Each PBXFrameworksBuildPhase entry
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
                "parameter 'file_reference' must be of type PBXFileReference")

        uuid = calcuuid(
            'PBXFrameworksBuildPhase' +
            file_reference.source_file.relative_pathname)

        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXFrameworksBuildPhase',
            comment='Frameworks',
            uuid=uuid)

        self.add_item(JSONEntry(name='buildActionMask', value='2147483647'))

        files = JSONArray(name='files')
        self.add_item(files)

        self.add_item(
            JSONEntry(
                name='runOnlyForDeploymentPostprocessing',
                value='0'))

        ## JSONArray of PBXBuildFile records
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
                "parameter 'build_file' must be of type PBXBuildFile")

        self.files.add_item(
            JSONEntry(
                build_file.uuid,
                comment=os.path.basename(
                    build_file.file_reference.source_file.relative_pathname) +
                ' in Frameworks', suffix=','))

    @staticmethod
    def get_phase_name():
        """
        Return the build phase name for XCode.
        """
        return 'Frameworks'


########################################


class PBXGroup(JSONDict):
    """
    Each PBXGroup entry
    """

    def __init__(self, group_name, path):
        """
        Init the PBXGroup.
        """

        # Create uuid, and handle an empty path
        uuid_path = path
        if path is None:
            uuid_path = '<group>'
        uuid = calcuuid('PBXGroup' + group_name + uuid_path)

        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXGroup',
            comment=group_name,
            uuid=uuid)

        children = JSONArray('children')
        self.add_item(children)

        self.add_item(
            JSONEntry(
                'name',
                value=group_name,
                enabled=path is None or group_name != path))

        self.add_item(JSONEntry('path', value=path, enabled=path is not None))

        value = 'SOURCE_ROOT' if path is not None else '<group>'
        self.add_item(JSONEntry('sourceTree', value=value))

        ## Children list
        self.children = children

        ## Name of this group
        self.group_name = group_name

        ## Root path for this group
        self.path = path

        ## List of child groups
        self.group_list = []

        ## List of child files
        self.file_list = []

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
                "parameter 'file_reference' must be of type PBXFileReference")

        self.file_list.append(
            (file_reference.uuid, os.path.basename(
                file_reference.source_file.relative_pathname)))

    def add_group(self, group):
        """
        Append a group to the end of the list.

        Args:
            group: PBXGroup item to attach to this group.
        """

        # Sanity check
        if not isinstance(group, PBXGroup):
            raise TypeError(
                "parameter 'group' must be of type PBXGroup")

        self.group_list.append((group.uuid, group.group_name))

    def generate(self, line_list, indent=0):
        """
        Write this record to output.

        Args:
            line_list: Line list to append new lines.
            indent: number of tabs to insert (For recursion)
        """

        # Output groups first
        for item in sorted(self.group_list, key=operator.itemgetter(1)):
            self.children.add_item(
                JSONEntry(
                    item[0],
                    comment=item[1],
                    suffix=','))

        # Output files last
        for item in sorted(self.file_list, key=operator.itemgetter(1)):
            self.children.add_item(
                JSONEntry(
                    item[0],
                    comment=item[1],
                    suffix=','))

        return JSONDict.generate(self, line_list, indent)

########################################


class PBXNativeTarget(JSONDict):
    """
    Each PBXNative entry
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments

    def __init__(self, parent, name, productreference,
                 productname, producttype):

        uuid = calcuuid('PBXNativeTarget' + name)
        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXNativeTarget',
            comment=name,
            uuid=uuid)

        self.build_config_list = JSONEntry(
            'buildConfigurationList',
            comment=(
                'Build configuration list '
                'for PBXNativeTarget "{}"').format(name),
            enabled=False)
        self.add_item(self.build_config_list)

        self.build_phases = JSONArray('buildPhases')
        self.add_item(self.build_phases)

        self.build_rules = JSONArray('buildRules')
        self.add_item(self.build_rules)

        self.dependencies = JSONArray('dependencies')
        self.add_item(self.dependencies)

        self.add_item(JSONEntry('name', value=name))
        self.add_item(JSONEntry('productName', value=productname))

        self.add_item(
            JSONEntry(
                'productReference',
                value=productreference.uuid,
                comment=productreference.source_file.relative_pathname))

        self.add_item(
            JSONEntry(
                'productType',
                value=producttype))

        ## Objects record (Parent)
        self.parent = parent

        ## Name of the target
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
                suffix=','))

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
                suffix=','))

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

        for item in self.parent.objects.get_entries('PBXBuildRule'):
            self.build_rules.add_item(
                JSONEntry(
                    item.name,
                    comment='PBXBuildRule',
                    suffix=','))

        return JSONDict.generate(self, line_list, indent)

########################################


class PBXProject(JSONDict):
    """
    Each PBXProject entry
    """

    def __init__(self, uuid, solution):
        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXProject',
            comment='Project object',
            uuid=uuid)

        # Look up versioning information
        object_versions = OBJECT_VERSIONS.get(solution.ide)

        # Attributes record
        attributes = JSONDict('attributes')
        self.add_item(attributes)

        attributes.add_item(
            JSONEntry(
                'BuildIndependentTargetsInParallel',
                value='YES'))

        upgrade = object_versions[1]
        attributes.add_item(
            JSONEntry(
                'LastUpgradeCheck',
                value=upgrade, enabled=upgrade is not None))

        self.build_config_list = JSONEntry(
            'buildConfigurationList',
            comment=('Build configuration list '
                     'for PBXProject "{}"').format(solution.name),
            enabled=False)
        self.add_item(self.build_config_list)

        self.add_item(
            JSONEntry(
                'compatibilityVersion',
                value=object_versions[2]))

        self.add_item(
            JSONEntry(
                'developmentRegion',
                value=object_versions[3],
                enabled=object_versions[3] is not None))

        self.add_item(JSONEntry('hasScannedForEncodings', value='1'))

        known_regions = JSONArray('knownRegions')
        self.add_item(known_regions)
        known_regions.add_item(JSONEntry('en', suffix=','))

        self.main_group = JSONEntry('mainGroup', enabled=False)
        self.add_item(self.main_group)

        self.add_item(JSONEntry('projectDirPath', value=''))
        self.add_item(JSONEntry('projectRoot', value=''))

        self.targets = JSONArray('targets')
        self.add_item(self.targets)

    def append_target(self, item):
        """
        Append a PBXNative target
        """

        self.targets.add_item(
            JSONEntry(
                item.uuid,
                comment=item.target_name,
                suffix=','))

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


class PBXShellScriptBuildPhase(JSONDict):
    """
    Each PBXShellScriptBuildPhase entry
    """

    def __init__(self, input_data, output, command):

        uuid = calcuuid(
            'PBXShellScriptBuildPhase' +
            ''.join(input_data) +
            output +
            command)
        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXShellScriptBuildPhase',
            comment='ShellScript',
            uuid=uuid)

        self.add_item(JSONEntry('buildActionMask', value='2147483647'))
        files = JSONArray('files')
        self.add_item(files)
        self.files = files

        input_paths = JSONArray('inputPaths', disable_if_empty=True)
        self.add_item(input_paths)
        for item in input_data:
            input_paths.add_item(JSONEntry(item, suffix=','))

        output_paths = JSONArray('outputPaths')
        self.add_item(output_paths)
        output_paths.add_item(JSONEntry(output, suffix=','))

        self.add_item(
            JSONEntry(
                'runOnlyForDeploymentPostprocessing',
                value='0'))
        self.add_item(JSONEntry('shellPath', value='/bin/sh'))
        self.add_item(JSONEntry('shellScript', value='{}\\n'.format(command)))
        self.add_item(JSONEntry('showEnvVarsInLog', value='0'))

    @staticmethod
    def get_phase_name():
        """
        Return the build phase name for XCode.
        """
        return 'ShellScript'

########################################


class PBXSourcesBuildPhase(JSONDict):
    """
    Each PBXSourcesBuildPhase entry
    """

    def __init__(self, owner):

        uuid = calcuuid(
            'PBXSourcesBuildPhase' +
            owner.source_file.relative_pathname)
        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXSourcesBuildPhase',
            comment='Sources',
            uuid=uuid)

        self.add_item(JSONEntry('buildActionMask', value='2147483647'))
        files = JSONArray('files')
        self.files = files
        self.add_item(files)
        self.add_item(
            JSONEntry(
                'runOnlyForDeploymentPostprocessing',
                value='0'))
        self.owner = owner
        self.buildfirstlist = []
        self.buildlist = []

    def append_file(self, item):
        """
        Append a file uuid and name to the end of the list
        """

        if item.file_reference.source_file.type == FileTypes.glsl:
            self.buildfirstlist.append([item, os.path.basename(
                item.file_reference.source_file.relative_pathname)])
        else:
            self.buildlist.append([item, os.path.basename(
                item.file_reference.source_file.relative_pathname)])

    @staticmethod
    def get_phase_name():
        """
        Return the build phase name for XCode.
        """
        return 'Sources'

    def generate(self, line_list, indent=0):
        """
        Write this record to output
        """

        self.buildfirstlist = sorted(
            self.buildfirstlist, key=operator.itemgetter(1))
        self.buildlist = sorted(
            self.buildlist, key=operator.itemgetter(1))
        for item in self.buildfirstlist:
            self.files.add_item(
                JSONEntry(
                    item[0].uuid,
                    comment='{} in Sources'.format(
                        item[1]), suffix=','))

        for item in self.buildlist:
            self.files.add_item(
                JSONEntry(
                    item[0].uuid,
                    comment='{} in Sources'.format(
                        item[1]), suffix=','))
        return JSONDict.generate(self, line_list, indent)


########################################


class PBXTargetDependency(JSONDict):
    """
    Each PBXTargetDependency entry
    """

    def __init__(self, proxy, nativetarget):
        uuid = calcuuid(
            'PBXTargetDependency' +
            proxy.native_target.target_name +
            nativetarget.target_name)
        JSONDict.__init__(
            self,
            name=uuid,
            isa='PBXTargetDependency',
            comment='PBXTargetDependency',
            uuid=uuid)

        self.add_item(
            JSONEntry(
                'target',
                value=nativetarget.uuid,
                comment=nativetarget.target_name))
        self.add_item(
            JSONEntry(
                'targetProxy',
                value=proxy.uuid,
                comment='PBXContainerItemProxy'))

########################################


class XCBuildConfiguration(JSONDict):
    """
    Each XCBuildConfiguration entry
    """

    def __init__(self, configuration, configfilereference, owner, sdkroot,
                 installpath):
        """
        Initialize a XCBuildConfiguration object.
        """

        # pylint: disable=too-many-arguments

        if not isinstance(configuration, Configuration):
            raise TypeError(
                "parameter 'configuration' must be of type Configuration")

        self.configuration = configuration

        # pylint: disable=too-many-arguments
        uuid = calcuuid('XCBuildConfiguration' +
                        owner.pbxtype + owner.targetname + configuration.name)
        JSONDict.__init__(
            self,
            name=uuid,
            isa='XCBuildConfiguration',
            comment=configuration.name,
            uuid=uuid)

        if configfilereference is not None:
            self.add_item(
                JSONEntry(
                    'baseConfigurationReference',
                    value=configfilereference.uuid,
                    comment=os.path.basename(
                        configfilereference.filename)))

        build_settings = JSONDict('buildSettings')
        self.add_item(build_settings)
        self.build_settings = build_settings
        if sdkroot is not None:
            build_settings.add_item(JSONEntry('SDKROOT', value=sdkroot))

        if installpath:
            build_settings.add_item(JSONEntry(
                'INSTALL_PATH',
                value='"$(HOME)/Applications"'))

        if owner.pbxtype == 'PBXProject':
            # Insert the flags (and overrides)
            for item in XCBUILD_FLAGS:
                if item[1] in ('string', 'boolean'):
                    build_settings.add_item(
                        JSONEntry(
                            item[0],
                            value=item[2],
                            enabled=bool(item[2])))
                elif item[1] == 'stringarray':
                    temp_array = JSONArray(item[0], disable_if_empty=True)
                    build_settings.add_item(temp_array)
                    if item[2]:
                        for item2 in item[2]:
                            temp_array.add_item(JSONEntry(item2, suffix=','))

            # Set ARCHS
            self.fixup_archs()

            if configuration.platform.is_ios():
                platform_suffix = 'ios'
            else:
                platform_suffix = 'osx'

            # Set profiling
            if configuration.get_chained_value('profile'):
                item = build_settings.find_item('GENERATE_PROFILING_CODE')
                item.value = 'YES'

            # Set defines
            item = build_settings.find_item('GCC_PREPROCESSOR_DEFINITIONS')
            for define in configuration.get_chained_list('define_list'):
                item.add_item(JSONEntry(define, suffix=','))

            # Set optimization
            item = build_settings.find_item('GCC_OPTIMIZATION_LEVEL')
            if configuration.optimization:
                item.value = 's'
            else:
                item.value = '0'

            # Warn on autos is suprious for Debug builds
            item = build_settings.find_item('GCC_WARN_UNINITIALIZED_AUTOS')
            if configuration.optimization:
                item.value = 'YES'
            else:
                item.value = 'NO'

            # Customize the build directories.
            idecode = configuration.ide.get_short_code()
            item = build_settings.find_item('CONFIGURATION_BUILD_DIR')
            item.value = (
                '$(SYMROOT)/$(PRODUCT_NAME){}{}{}'
            ).format(idecode, platform_suffix, configuration.short_code)

            item = build_settings.find_item('CONFIGURATION_TEMP_DIR')
            item.value = (
                '$(SYMROOT)/$(PRODUCT_NAME){}{}{}'
            ).format(idecode, platform_suffix, configuration.short_code)

            item = build_settings.find_item('SUFFIX')
            item.value = platform_suffix + configuration.short_code

        self.add_item(JSONEntry('name', value=configuration.name))

    def fixup_archs(self):
        """
        Based on the SDKROOT entry, set the default CPUs.
        """

        # Start by getting SDKROOT
        build_settings = self.build_settings
        item = build_settings.find_item('SDKROOT')
        if item is None:
            return

        # Start with no CPUs
        cpus = []

        if item.value.startswith('macosx'):
            digits = item.value[6:].split('.')
            version = float(digits[1])

            # macosx 10.3.9 is ppc 32 bit only
            if version < 4:
                cpus.append('ppc')

            # Leopard support all 4 CPUs
            elif version < 6:
                cpus.extend(('ppc', 'ppc64', 'i386', 'x86_64'))

            # macOS from 10.6 to 10.14 support intel 32 and 64
            elif version < 15:
                cpus.extend(('i386', 'x86_64'))

            # macOS 10.15 and higher is 64 bit only
            else:
                cpus.append('x86_64')
        elif item.value.startswith('iphonesimulator'):
            cpus.extend(('i386', 'x86_64'))

        elif item.value.startswith('iphoneos'):
            cpus.extend(('armv7', 'armv7s', 'arm64'))

        item = build_settings.find_item('ARCHS')
        item.value = make_jsonarray(cpus)

########################################


class XCConfigurationList(JSONDict):
    """
    Each XCConfigurationList entry
    """

    def __init__(self, pbxtype, targetname):

        uuid = calcuuid('XCConfigurationList' + pbxtype + targetname)
        JSONDict.__init__(
            self,
            name=uuid,
            isa='XCConfigurationList',
            comment='Build configuration list for {} "{}"'.format(
                pbxtype,
                targetname),
            uuid=uuid)
        self.build_configurations = JSONArray('buildConfigurations')
        self.add_item(self.build_configurations)
        self.add_item(JSONEntry('defaultConfigurationIsVisible', value='0'))
        self.default_config = JSONEntry(
            'defaultConfigurationName', value='Release')
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
            if item.configuration.name == 'Release':
                default = 'Release'
            elif default is None:
                default = item.configuration.name
            self.build_configurations.add_item(
                JSONEntry(
                    item.uuid,
                    comment=item.configuration.name,
                    suffix=','))

        if default is None:
            default = 'Release'

        self.default_config.value = default

        return JSONDict.generate(self, line_list, indent)


########################################

class Project(JSONDict):
    """
    Root object for an XCode IDE project file
    Created with the name of the project, the IDE code (xc3, xc5)
    the platform code (ios, osx)
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

        ## Parent solution
        self.solution = solution

        uuid = calcuuid('PBXProjectRoot' + solution.xcode_folder_name)

        # Init the solution
        JSONDict.__init__(self, solution.name, uuid=uuid)

        # Initialize entries for master dictionary for the XCode project.
        self.add_item(JSONEntry('archiveVersion', value='1'))
        self.add_item(JSONDict('classes'))
        self.add_item(
            JSONEntry(
                'objectVersion',
                value=OBJECT_VERSIONS.get(solution.ide)[0]))

        # Main object list
        objects = JSONObjects('objects')
        self.objects = objects
        self.add_item(objects)

        # UUID of the root object
        rootobject = JSONEntry(
            'rootObject',
            value=uuid,
            comment='Project object')
        self.add_item(rootobject)

        idecode = solution.ide.get_short_code()
        rootproject = PBXProject(uuid, solution)
        objects.add_item(rootproject)

        found_glsl = False

        # Process all the projects and configurations
        for project in solution.project_list:

            # Process the filenames
            project.get_file_list([FileTypes.icns,
                                   FileTypes.h,
                                   FileTypes.cpp,
                                   FileTypes.c,
                                   FileTypes.frameworks,
                                   FileTypes.exe,
                                   FileTypes.library,
                                   FileTypes.glsl])

            framework_list = []
            for configuration in project.configuration_list:

                for item in configuration.frameworks_list:
                    if item not in framework_list:
                        framework_list.append(item)
                        project.codefiles.append(SourceFile(
                            item, '', FileTypes.frameworks))

            for item in project.codefiles:

                # If there were GLSL source files, add a custom build step
                if not found_glsl and item.type is FileTypes.glsl:
                    objects.add_item(BuildGLSL())
                    found_glsl = True

                objects.add_item(PBXFileReference(item, solution.ide))

            # What's the final output file?
            if project.project_type is ProjectTypes.library:
                if project.platform is PlatformTypes.ios:
                    libextension = 'ios.a'
                else:
                    libextension = 'osx.a'
                outputfilereference = PBXFileReference(SourceFile(
                    'lib' + solution.name + idecode + libextension, '',
                    FileTypes.library), solution.ide)
                objects.add_item(outputfilereference)
            elif project.project_type is ProjectTypes.app:
                outputfilereference = PBXFileReference(SourceFile(
                    solution.name + '.app', '', FileTypes.exe), solution.ide)
                objects.add_item(outputfilereference)
            elif project.project_type is not ProjectTypes.empty:
                outputfilereference = PBXFileReference(SourceFile(
                    solution.name, '', FileTypes.exe), solution.ide)
                objects.add_item(outputfilereference)
            else:
                outputfilereference = None

            # If a fat library, add references for dev and sim targets
            ioslibrary = False
            if project.platform is PlatformTypes.ios:
                if project.project_type is ProjectTypes.library:
                    ioslibrary = True

            if ioslibrary:
                devfilereference = PBXFileReference(
                    SourceFile(
                        'lib' + solution.name +
                        idecode + 'dev.a', '',
                        FileTypes.library), solution.ide)
                objects.add_item(devfilereference)
                simfilereference = PBXFileReference(
                    SourceFile(
                        'lib' + solution.name +
                        idecode + 'sim.a', '',
                        FileTypes.library), solution.ide)
                objects.add_item(simfilereference)

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

                for item in objects.get_entries('PBXFileReference'):
                    if item.source_file.type is FileTypes.cpp or \
                            item.source_file.type is FileTypes.glsl:

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

                    for item in objects.get_entries('PBXFileReference'):
                        if item.source_file.type is FileTypes.cpp or \
                                item.source_file.type is FileTypes.glsl:

                            build_file = PBXBuildFile(item, outputfilereference)
                            objects.add_item(build_file)
                            buildphase1.append_file(build_file)

                        elif item.source_file.type is FileTypes.frameworks:
                            build_file = PBXBuildFile(item, outputfilereference)
                            objects.add_item(build_file)
                            framephase1.add_build_file(build_file)

            # Create the root file group and the Products group
            groupproducts = PBXGroup('Products', None)

            grouproot = PBXGroup(solution.name, None)
            objects.add_item(grouproot)

            # No frameworks group unless one is warranted

            frameworksgroup = None

            # Insert all the file references into group
            for item in objects.get_entries('PBXFileReference'):
                # Products go into a special group
                if item.source_file.type is FileTypes.exe:
                    groupproducts.add_file(item)
                elif item.source_file.type is FileTypes.library:
                    groupproducts.add_file(item)
                elif item.source_file.type is FileTypes.frameworks:

                    # Create the group if needed

                    if frameworksgroup is None:
                        frameworksgroup = PBXGroup('Frameworks', None)
                        objects.add_item(frameworksgroup)
                        grouproot.add_group(frameworksgroup)

                    frameworksgroup.add_file(item)
                else:
                    # Isolate the path
                    index = item.source_file.relative_pathname.rfind('/')
                    if index == -1:
                        # Put in the root group
                        grouproot.add_file(item)
                    else:
                        # Separate the path and name
                        path = item.source_file.relative_pathname[0:index]
                        #
                        # See if a group already exists
                        #
                        found = False
                        for matchgroup in objects.get_entries('PBXGroup'):
                            if matchgroup.path is not None and \
                                    matchgroup.path == path:
                                # Add to a pre-existing group
                                matchgroup.add_file(item)
                                found = True
                                break
                        if found:
                            continue

                        # Group not found. Iterate and create the group
                        # May need multiple levels

                        #
                        # Hack to remove preceding ../ entries
                        #

                        if path.startswith('../'):
                            index = 3
                        elif path.startswith('../../'):
                            index = 6
                        else:
                            index = 0

                        notdone = True
                        previousgroup = grouproot
                        while notdone:
                            endindex = path[index:].find('/')
                            if endindex == -1:
                                # Final level, create group and add reference
                                matchgroup = PBXGroup(
                                    path[index:], path)
                                objects.add_item(matchgroup)
                                matchgroup.add_file(item)
                                previousgroup.add_group(matchgroup)
                                notdone = False
                            else:
                                #
                                # See if a group already exists
                                #
                                temppath = path[0:index + endindex]
                                found = False
                                for matchgroup in objects.get_entries(
                                        'PBXGroup'):
                                    if matchgroup.path is None:
                                        continue
                                    if matchgroup.path == temppath:
                                        found = True
                                        break

                                if not found:
                                    matchgroup = PBXGroup(
                                        path[index:index + endindex], temppath)
                                    objects.add_item(matchgroup)
                                    previousgroup.add_group(matchgroup)
                                previousgroup = matchgroup
                                index = index + endindex + 1

            # Any output?
            if not groupproducts.is_empty():
                objects.add_item(groupproducts)
                grouproot.add_group(groupproducts)
            # Create the config list for the root project

            configlistref = XCConfigurationList('PBXProject', solution.name)
            objects.add_item(configlistref)
            for configuration in project.configuration_list:
                entry = self.addxcbuildconfigurationlist(
                    configuration, None, configlistref, None, False)
                configlistref.configuration_list.append(entry)

            rootproject.set_config_list(configlistref)
            rootproject.set_root_group(grouproot)

            #
            # Create the PBXNativeTarget config chunks
            #

            sdkroot = None
            if project.platform is PlatformTypes.ios:
                sdkroot = 'iphoneos'

            if project.project_type is ProjectTypes.library:
                outputtype = 'com.apple.product-type.library.static'
            elif project.project_type is ProjectTypes.screensaver:
                outputtype = 'com.apple.product-type.bundle'
            elif project.project_type is ProjectTypes.app:
                outputtype = 'com.apple.product-type.application'
            else:
                outputtype = 'com.apple.product-type.tool'

            # For a normal project, attach the config to a native target and
            # we're done
            if not ioslibrary and outputfilereference:
                configlistref = XCConfigurationList(
                    'PBXNativeTarget', solution.name)
                objects.add_item(configlistref)
                install = False
                if project.project_type is ProjectTypes.app:
                    install = True
                for configuration in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            configuration, None, configlistref, sdkroot, install))
                nativetarget1 = PBXNativeTarget(
                    self,
                    solution.name,
                    outputfilereference,
                    solution.name,
                    outputtype)
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
                    'PBXNativeTarget', targetname)
                objects.add_item(configlistref)
                for configuration in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            configuration, None, configlistref, None, False))
                nativetarget1 = PBXNativeTarget(
                    self,
                    solution.name,
                    outputfilereference,
                    solution.name,
                    outputtype)
                objects.add_item(nativetarget1)
                nativetarget1.set_config_list(configlistref)
                rootproject.append_target(nativetarget1)

                targetname = solution.name + idecode + 'dev'
                configlistref = XCConfigurationList(
                    'PBXNativeTarget', targetname)
                objects.add_item(configlistref)
                for configuration in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            configuration, None, configlistref, 'iphoneos', False))
                nativeprojectdev = PBXNativeTarget(
                    self,
                    targetname,
                    devfilereference,
                    solution.name,
                    outputtype)
                objects.add_item(nativeprojectdev)
                nativeprojectdev.set_config_list(configlistref)
                rootproject.append_target(nativeprojectdev)

                nativeprojectdev.add_build_phase(buildphase1)
                nativeprojectdev.add_build_phase(framephase1)
                devcontainer = PBXContainerItemProxy(
                    nativeprojectdev, self.uuid)
                objects.add_item(devcontainer)

                targetname = solution.name + idecode + 'sim'
                configlistref = XCConfigurationList(
                    'PBXNativeTarget', targetname)
                objects.add_item(configlistref)
                for configuration in project.configuration_list:
                    configlistref.configuration_list.append(
                        self.addxcbuildconfigurationlist(
                            configuration,
                            None,
                            configlistref,
                            'iphonesimulator',
                            False))
                nativeprojectsim = PBXNativeTarget(
                    self,
                    targetname,
                    simfilereference,
                    solution.name,
                    outputtype)
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
                if project.project_type is ProjectTypes.tool:

                    # Copy the tool to the bin folder
                    input_data = [TEMP_EXE_NAME]
                    output = (
                        '${{SRCROOT}}/bin/'
                        '${{EXECUTABLE_NAME}}{}${{SUFFIX}}').format(idecode)

                    command = (
                        'if [ ! -d ${{SRCROOT}}/bin ];'
                        ' then mkdir ${{SRCROOT}}/bin; fi\\n'
                        '${{CP}} {} {}').format(TEMP_EXE_NAME, output)

                    shellbuildphase = PBXShellScriptBuildPhase(
                        input_data, output, command)
                    objects.add_item(shellbuildphase)
                    nativetarget1.add_build_phase(shellbuildphase)

                elif project.project_type is ProjectTypes.app:

                    # Copy the exe into the .app folder
                    input_file = (
                        '{}.app/Contents/MacOS/'
                        '${{EXECUTABLE_NAME}}').format(TEMP_EXE_NAME)

                    input_data = [input_file]
                    output = (
                        '${{SRCROOT}}/bin/'
                        '${{EXECUTABLE_NAME}}{0}${{SUFFIX}}.app'
                        '/Contents/MacOS/'
                        '${{EXECUTABLE_NAME}}{0}${{SUFFIX}}').format(idecode)

                    command = 'if [ ! -d ${SRCROOT}/bin ]; then mkdir ${SRCROOT}/bin; fi\\n' \
                        '${CP} -r ' + TEMP_EXE_NAME + '.app/ ' \
                        '${SRCROOT}/bin/${EXECUTABLE_NAME}' + idecode + '${SUFFIX}.app/\\n' \
                        'mv ${SRCROOT}/bin/${EXECUTABLE_NAME}' + idecode + '${SUFFIX}.app' \
                        '/Contents/MacOS/${EXECUTABLE_NAME} ' \
                        '${SRCROOT}/bin/${EXECUTABLE_NAME}' + idecode + '${SUFFIX}.app' \
                        '/Contents/MacOS/${EXECUTABLE_NAME}' + idecode + '${SUFFIX}'
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
                    deploy_folder = deploy_folder.replace('(', '{')
                    deploy_folder = deploy_folder.replace(')', '}')

            if deploy_folder is not None:
                if ioslibrary is False:
                    input_data = [TEMP_EXE_NAME]
                else:
                    input_data = [
                        '${BUILD_ROOT}/' + solution.name + idecode +
                        'dev${SUFFIX}/lib' + solution.name + idecode + 'dev.a',
                        '${BUILD_ROOT}/' + solution.name + idecode +
                        'sim${SUFFIX}/lib' +
                        solution.name + idecode + 'sim.a'
                    ]

                if ioslibrary is True:

                    output = deploy_folder + '${PRODUCT_NAME}'
                    command = _PERFORCE_PATH + ' edit ' + deploy_folder + '${PRODUCT_NAME}\\n' + \
                        'lipo -output ' + deploy_folder + \
                        '${PRODUCT_NAME} -create ${BUILD_ROOT}/' + \
                        solution.name + idecode + \
                        'dev${SUFFIX}/lib' + solution.name + idecode + \
                        'dev.a ${BUILD_ROOT}/' + \
                        solution.name + idecode + \
                        'sim${SUFFIX}/lib' + solution.name + \
                        idecode + 'sim.a\\n'
                elif project.project_type is ProjectTypes.library:

                    output = ('{0}lib${{PRODUCT_NAME}}{1}${{SUFFIX}}.a').format(
                        deploy_folder, idecode)
                    command = (
                        '{0} edit {1}\\n'
                        '${{CP}} {2} {1}\\n'
                    ).format(_PERFORCE_PATH, output, TEMP_EXE_NAME, )
                else:
                    output = deploy_folder + '${PRODUCT_NAME}'
                    command = 'if [ \\"${CONFIGURATION}\\" == \\"Release\\" ]; then \\n' + \
                        _PERFORCE_PATH + ' edit ' + deploy_folder + \
                        '${PRODUCT_NAME}\\n${CP} ' + \
                        TEMP_EXE_NAME + ' ' + \
                        deploy_folder + '${PRODUCT_NAME}\\nfi\\n'

                shellbuildphase = PBXShellScriptBuildPhase(
                    input_data, output, command)
                objects.add_item(shellbuildphase)
                nativetarget1.add_build_phase(shellbuildphase)

    def addxcbuildconfigurationlist(self, configuration, configfilereference,
                                    owner, sdkroot, installpath):
        """
        Add a new configuration list
        """

        # pylint: disable=too-many-arguments
        entry = XCBuildConfiguration(
            configuration,
            configfilereference,
            owner,
            sdkroot,
            installpath)
        for item in self.objects.get_entries('XCBuildConfiguration'):
            if item.uuid == entry.uuid:
                entry = item
                break
        else:
            self.objects.add_item(entry)
        return entry

    def generate(self, line_list, indent=0):
        """
        Generate an XCode project files

        Args:
            line_list: Line list to append new lines.
            indent: number of tabs to insert (For recursion)
        Return:
            Non-zero on error.
        """

        # Write the XCode header
        line_list.append('// !$*UTF8*$!')
        line_list.append('{')

        # Increase indentatiopn
        indent = indent + 1
        for item in self.value:
            item.generate(line_list, indent)

        # Close up the project file
        line_list.append('}')
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

    # Failsafe
    if solution.ide not in SUPPORTED_IDES:
        return 10

    # Create the output filename and pass it to the generator
    # so it can reference itself in make targets
    solution.xcode_folder_name = '{}{}{}.xcodeproj'.format(
        solution.name, solution.ide_code, solution.platform_code)
    create_folder_if_needed(solution.xcode_folder_name)

    # Xcode requires configurations, if none are present, add some

    if not solution.project_list:
        project = CoreProject(
            name=solution.name,
            project_type=ProjectTypes.empty)
        project.source_folders_list = []
        solution.project_list.append(project)

    for project in solution.project_list:
        if not project.configuration_list:
            project.configuration_list.append(Configuration('Debug'))
            project.configuration_list.append(Configuration('Release'))

    exporter = Project(solution)

    # Output the actual project file
    xcode_lines = []
    error = exporter.generate(xcode_lines)
    if error:
        return error

    # Save the file if it changed
    xcode_filename = os.path.join(
        solution.working_directory,
        solution.xcode_folder_name,
        'project.pbxproj')

    save_text_file_if_newer(
        xcode_filename,
        xcode_lines,
        bom=False,
        perforce=solution.perforce,
        verbose=solution.verbose)

    return 0
