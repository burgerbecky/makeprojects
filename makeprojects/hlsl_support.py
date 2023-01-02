#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data and code to support HLSL targets

This module contains data, classes and functions to support
building HLSL files

@package makeprojects.hlsl_support

@var makeprojects.hlsl_support.HLSL_OPTIMIZATION
Enumerations for HLSL Optimization

@var makeprojects.hlsl_support.HLSL_MATRICES
Enumerations for HLSL MatricesPacking

@var makeprojects.hlsl_support.HLSL_FLOW_CONTROL
Enumerations for HLSL FlowControl

@var makeprojects.hlsl_support.HLSL_TARGET_PROFILES
Enumerations for HLSL TargetProfile

@var makeprojects.hlsl_support.HLSL_ENUMS
Names, default, lookup tables for HLSL enums

@var makeprojects.hlsl_support.HLSL_BOOLEANS
Boolean list for HLSL, Name, Default, switches

@var makeprojects.hlsl_support.HLSL_STRINGS
String entries for HLSL

@var makeprojects.hlsl_support.HLSL_STRING_LISTS
String list entries for HLSL, switch, quote parameters
"""

# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

from .validators import lookup_enum_append_keys, lookup_booleans, \
    lookup_strings, lookup_string_lists

# Enumerations for HLSL Optimization
HLSL_OPTIMIZATION = (
    ("/Od", 0), ("/O0", 1), ("/O1", 2), ("/O2", 3), ("/O3", 4)
)

# Enumerations for HLSL MatricesPacking
HLSL_MATRICES = (
    ("/Zpr", 0), ("Row", 0), ("/Zpc", 1), ("Column", 1)
)

# Enumerations for HLSL FlowControl
HLSL_FLOW_CONTROL = (
    ("/Gfa", 0), ("Avoid", 0), ("/Gfp", 1), ("Prefer", 1)
)

# Enumerations for HLSL TargetProfile
HLSL_TARGET_PROFILES = (
    ("/Tvs_1_1", 0), ("vs_1_1", 0),
    ("/Tvs_2_0", 1), ("vs_2_0", 1),
    ("/Tvs_2_a", 2), ("vs_2_a", 2),
    ("/Tvs_2_sw", 3), ("vs_2_sw", 3),
    ("/Tvs_3_0", 4), ("vs_3_0", 4),
    ("/Tvs_3_sw", 5), ("vs_3_sw", 5),
    ("/Tvs_4_0", 6), ("vs_4_0", 6),
    ("/Tvs_4_1", 7), ("vs_4_1", 7),
    ("/Tps_2_0", 8), ("ps_2_0", 8),
    ("/Tps_2_a", 9), ("ps_2_a", 9),
    ("/Tps_2_b", 10), ("ps_2_b", 10),
    ("/Tps_2_sw", 11), ("ps_2_sw", 11),
    ("/Tps_3_0", 12), ("ps_3_0", 12),
    ("/Tps_3_sw", 13), ("ps_3_sw", 13),
    ("/Tps_4_0", 14), ("ps_4_0", 14),
    ("/Tps_4_1", 15), ("ps_4_1", 15),
    ("/Ttx_1_0", 16), ("tx_1_0", 16),
    ("/Tgs_4_0", 17), ("gs_4_0", 17),
    ("/Tgs_4_1", 18), ("gs_4_1", 18),
    ("/Tfx_2_0", 19), ("fx_2_0", 19),
    ("/Tfx_4_0", 20), ("fx_4_0", 20),
    ("/Tfx_4_1", 21), ("fx_4_1", 21)
)

# Names, default, lookup tables for HLSL enums
HLSL_ENUMS = (
    ("Optimization", (4, HLSL_OPTIMIZATION)),
    ("MatricesPacking", (1, HLSL_MATRICES)),
    ("FlowControl", (1, HLSL_FLOW_CONTROL)),
    ("TargetProfile", (8, HLSL_TARGET_PROFILES))
)

# Boolean list for HLSL, Name, Default, switches
HLSL_BOOLEANS = {
    "GenerateDebugInformation": (None, {"/Zi": True}),
    "NoLogo": (True, {"/nologo": True}),
    "DisableValidation": (None, {"/Vd": True}),
    "TreatWarningsAsErrors": (None, {"/WX": True}),
    "StripReflectionData": (None, {"/Qstrip_reflect": True}),
    "StripDebugInformation": (None, {"/Qstrip_debug": True}),
    "ForcePartialPrecision": (None, {"/Gpp": True}),
    "DisablePreshaders": (None, {"/Op": True}),
    "DisableEffectPerformanceMode": (None, {"/Gdp": True}),
    "EnableStrictMode": (None, {"/Ges": True}),
    "EnableBackwardsCompatibility": (None, {"/Gec": True}),
    "ForceIEEEStrictness": (None, {"/Gis": True}),
    "ShowIncludeProcess": (None, {"/Vi": True}),
    "ColorCodeAssembly": (None, {"/Cc": True}),
    "OutputInstructionNumbers": (None, {"/Ni": True}),
    "LoadDX931": (None, {"/LD": True}),
    "CompressDX10": (None, {"/compress": True}),
    "DecompressDX10": (None, {"/decompress": True}),
    "CompileChildFx4": (None, {"/Gch": True})
}

# String entries for HLSL, Name, default, switch, generates output, quote
# parameter
HLSL_STRINGS = (
    ("ObjectFileName", (
        None, "/Fo", True, True)),
    ("HeaderFileName", (
        "%(RootDir)%(Directory)%(FileName).h", "/Fh", True, True)),
    ("EntryPointName", (
        None, "/E", False, False)),
    ("VariableName", (
        "g_%(FileName)", "/Vn", False, False))
)

# String list entries for HLSL, switch, quote parameters
HLSL_STRING_LISTS = {
    "PreprocessorDefinitions": ("/D", False),
    "AdditionalIncludeDirectories": ("/I ", True)
}

########################################


def make_hlsl_command(command_dict):
    """ Create HLSL command line
    Args:
        command_dict: Dict with command overrides
    Returns:
        Command line, Description, Output list
    """

    # Create the initial command line
    cmd = ["\"$(DXSDK_DIR)utilities\\bin\\x86\\fxc.exe\"",
           "\"%(FullPath)\""]

    lookup_booleans(cmd, HLSL_BOOLEANS, command_dict)
    lookup_enum_append_keys(cmd, HLSL_ENUMS, command_dict)
    outputs = lookup_strings(cmd, HLSL_STRINGS, command_dict)
    lookup_string_lists(cmd, HLSL_STRING_LISTS, command_dict)

    if command_dict.get("GeneratePreprocessedSourceListing", False):
        temp = command_dict.get(
            "PreprocessedSourceListingName", "$(IntDir)%(FileName).lst")
        cmd.append("/P\"{}\"".format(temp))
        outputs.append(temp)

    if command_dict.get("GenerateWarningFile", False):
        temp = command_dict.get("WarningsFileName",
                                "$(IntDir)%(FileName).log")
        cmd.append("/Fe\"{}\"".format(temp))
        outputs.append(temp)

    temp_int = int(command_dict.get("AssemblerOutput", 0))
    if temp_int == 1:
        # Assembly code
        temp_int = "/Fc"
    elif temp_int == 2:
        # Assembly code and hex
        temp_int = "/Fx"
    else:
        temp_int = None
    if temp_int:
        temp = command_dict.get(
            "AssemblyListingFileName",
            "$(IntDir)%(FileName).asm")
        cmd.append("{}\"{}\"".format(temp_int, temp))
        outputs.append(temp)

    description = "fxc %(FileName)%(Extension)..."
    return " ".join(cmd), description, outputs
