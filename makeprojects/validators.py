#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Validation objects for project data generators.

@package makeprojects.validators
"""

# pylint: disable=no-name-in-module,useless-object-inheritance
# pylint: disable=consider-using-f-string
# pylint: disable=raise-missing-from

from __future__ import absolute_import, print_function, unicode_literals

import numbers

from burger import is_string, packed_paths, truefalse, convert_to_array, \
    BooleanProperty, IntegerProperty, StringProperty, \
    StringListProperty as StringListProp


########################################

def lookup_enum_value(enum_lookup, key, default):
    """
    Find a value in a list of enums.


    Iterate over a list of two entry tuples, the first entry is the key and the
    second is the value. Essentually, it's a dict implemented as a list/tuple.

    Args:
        enum_lookup: iterable of enumeration entries (key, integer)
        key: Key value to match in enumeration keys
        default: Value to return if there is no match

    Returns:
        Second value in the enumeration entry where the key matches, or
        ``default``
    """

    # Scan the table until a match is found
    for item in enum_lookup:

        # Match?
        if item[0] == key:
            return item[1]

    return default


########################################


def lookup_enum_append_key(cmd, enum_lookup, value):
    """
    Look up a command line option from an enumeration

    Iterate over a list of tuples, with the first entry is a command line entry
    and the second entry is the integer enumeration value. If the value is a
    match to the enumeration value, append the command line entry to ``cmd``.

    Args:
        cmd: list of command line options to append the new entry
        enum_lookup: iterable of enumeration entries (key, integer)
        value: integer enumeration value to match in enum_lookup
    Returns:
        cmd, which may have been modified.
    """

    # None exits immediately
    if value is None:
        return cmd

    # Check for bool
    if isinstance(value, bool):
        raise ValueError(
            "bool \"{}\" is not allowed".format(str(value)))

    # If it's a string, convert
    if is_string(value):
        # Can raise an exception if not able to convert
        value = int(value)

    # Convert strings to an integer
    if not isinstance(value, numbers.Number):
        raise ValueError(
            "\"{}\" is not a numeric value".format(str(value)))

    # Scan the table until a match is found
    for item in enum_lookup:

        # Match?
        if item[1] == value:

            # If the key is None, abort, no value needed.
            if item[0] is not None:
                # Append the command
                cmd.append(item[0])
            break
    return cmd

########################################


def lookup_enum_append_keys(cmd, enum_dicts, command_dict):
    """
    Look up a set of enum command line options

    A command_dict has keys in the form of Visual Studio XML entries with the
    data being the expected setting, or None for default. If the value starts
    with ``_NOT_USED``, it's considered None and will use the default.

    Note:
        Enumeration entries are a list of tuples where the first entry is the
        command line switch and the second entry is an integer as the enumeration
        value. If multiple entries have the same integer, the first entry is the
        default.

    Args:
        cmd: list of command line options to append the new entry
        enum_dicts: Iterable of enumeration entries
        command_dict: dict of command entries

    Returns:
        cmd is returned
    """

    # Read from the master list
    for item in enum_dicts:

        # Get the key from the dictionary
        value = command_dict.get(item[0], None)

        # Discard phony keys
        if is_string(value):
            if value.startswith("_NOT_USED"):
                value = None

        # Is the default requested?
        if value is None:
            value = item[1][0]

            # Is the default to skip?
            if value is None:
                continue

        # It's a command line option, so append it, if needed
        lookup_enum_append_key(cmd, item[1][1], value)

    return cmd

########################################


def lookup_strings(cmd, string_entries, command_dict):
    """
    Lookup string items and add them to the command line

    The command dictionary has a key of the Visual Studio XML name and
    the data is a valid string, usually a filename. If the data is None,
    the default string is used.

    String entries are a list of tuples where the first entry is the key
    and the second entry is a four entry tuple with the actions.

    The function will return a list of strings of output files so the
    caller can properly create the ``make`` entries for output files
    for the dependency tree.

    The four entry tuple is as follows:
        1. String/None, Output filename if any, or None for no output
        2. String, command line switch, may have a space at the end.
        3. Boolean, if True, encapsulate the output filename with quotes
        4. Boolean, if True, add the string to the return list

    Args:
        cmd: list of command line options to append the new entry
        string_entries: dict of string entries
        command_dict: dict of command entries

    Returns:
        String list of string items the generate output
    """

    # Initialize the output(s)
    outputs = []

    for item in string_entries:

        # Get the tuple table
        table = item[1]

        # Was there an entry?
        value = command_dict.get(item[0], None)
        if not value:

            # Use the default instead
            value = table[0]

            # No default? Skip the entry
            if not value:
                continue

        # Check if the string needs to be quoted
        if table[2]:
            quoted = "\"{}\"".format(value)
        else:
            quoted = value
        cmd.append("{}{}".format(table[1], quoted))

        # Check if the output filename should be appended to outputs
        if table[3]:
            outputs.append(value)

    return outputs

########################################


def lookup_string_list(cmd, switch, entry_list, quotes=True):
    """
    Create a command line with an entry list

    Given a list of strings in entry_list, add to a command line a compiler
    switch followed by each string with or without quotes. If the switch
    has an ending space, the space is removed and entries are stored in
    separate lines.

    Args:
        cmd: list of command line options to append the new entry
        switch: String, Command line switch string
        entry_list: List of parameter strings
        quotes: Boolean, True caused the entries to be quoted
    Returns:
        None
    """

    # Check if the command switch requires a space, if so, remove the
    # space and pass as separate lines

    spacing = switch.endswith(" ")
    if spacing:
        switch = switch[:-1]

    for item in entry_list:

        # Quote the string if needed
        if quotes:
            item = "\"{}\"".format(item)

        # Seperate lines
        if spacing:
            cmd.append(switch)
            cmd.append(item)
        else:
            # One line
            cmd.append("{}{}".format(switch, item))

########################################


def lookup_string_lists(cmd, string_list, command_dict):
    """
    Lookup string items and add them to the command line.

    The command_dict has the overrides where the value is either a single
    string or an array of strings or None.

    The string_list is an iterable of tuples where the first entry is a
    string of the Visual Studio XML name and the second entry is a 2 entry
    tuple, where the first entry is the command line switch and the second
    entry is a boolean where if ``True`` will have the string in quotes.

    Note:
        If a command line switch ends with a space, it will be used as a flag
        to append the parameter string as a separate line in the cmd list.

    Args:
        cmd: list of command line options to append the new entry
        string_list: dict of string list entries
        command_dict: dict of command entries
    Returns:
        None
    """

    for item in string_list:

        # Was there an override?
        temp = command_dict.get(item[0], None)
        if temp:
            table = item[1]
            lookup_string_list(cmd, table[0], convert_to_array(temp), table[1])

########################################


def lookup_booleans(cmd, boolean_list, command_dict):
    """
    Look up a command line option from a list of booleans

    The command dict is a dict of Visual Studio XML entries where the value is
    None, or a value that will be converted into a boolean.

    The boolean list is an iterable of tuples where the first entry is the
    Visual Studio XML entry and the second is a variable length tuple where
    the first entry is the default value followed by pairs of values of a
    string for the command line switch and then the boolean to match.

    Args:
        cmd: list of command line options to append the new entry
        boolean_list: list of boolean entries
        command_dict: dict of command entries
    Returns:
        None
    """

    # Scan the table until a match is found
    for item in boolean_list:
        key = item[0]
        table = item[1]

        # Was there an override?
        value = command_dict.get(key, None)
        if value is None:
            # Use the default instead
            value = table[0]

            # If no override or default, skip
            if value is None:
                continue

        # Ensure value is a boolean
        value = bool(value)

        # Check if the value actually sets a command line entry
        for index in range(1, len(table), 2):
            if table[index + 1] is value:
                cmd.append(table[index])
                break

########################################


class VSBooleanProperty(object):
    """
    Value can only be true or false.

    Attributes:
        name: Name of the validator
        value: BooleanProperty boolean value
    """

    value = BooleanProperty("_value")

    def __init__(self, name, default=None):
        """
        Initialize the default value

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
        """

        # Init the defaults
        self.name = name
        self.value = default

    ########################################

    def get_value(self):
        """
        Return the string representation of the string, or None
        """
        temp = self.value
        if temp is not None:
            temp = truefalse(temp)
        return temp

    ########################################

    @staticmethod
    def validate(key, configuration, default=None,
                 options_key=None, options=None):
        """
        Check if there is a command line switch override.
        Given a configuration, scan for the ``options_key`` and if found,
        check if that list has one of the option tuples. If there's a
        match, use the options tuple entry, otherwise use the default value.

        Args:
            key: Name of the XML attribute key
            configuration: configuration to scan for an override
            default: Value to use in case there is no override.
            options_key: Attribute to scan for commmand line options
            options: Iterable with options / Value pairs

        Returns:
            None or VSBooleanProperty() instance
        """

        if options_key is not None:

            # Check the configuration for the options
            options_key = configuration.get_chained_value(options_key)
            if options_key:

                # Iterate over the options
                for item in options:
                    if item[0] in options_key:
                        # Match, use this
                        default = item[1]
                        break

        if default is None:
            return None

        # Set the value (May assert if not a boolean)
        return VSBooleanProperty(key, default)

    ########################################

    @staticmethod
    def vs_validate(key, configuration, default=None,
                    options_key=None, options=None):
        """
        Check if there is an override with a vs_ prefix.
        Check if the configuration has a key of \"vs_\" + key in the
        configuration and if not found or None, use the key as is.

        Args:
            key: Name of the XML attribute key
            configuration: configuration to scan for an override
            default: Value to use in case there is no override.
            options_key: Attribute to scan for commmand line options
            options: Iterable with options / Value pairs
        Returns:
            None or VSBooleanProperty() instance
        """

        value = configuration.get_chained_value("vs_" + key)
        if value is None:
            return VSBooleanProperty.validate(
                key, configuration, default, options_key, options)
        return VSBooleanProperty(key, value)

    ########################################

    def __repr__(self):
        """
        Convert to string

        Returns:
            \"true\", \"false\" or \"None\"
        """

        if self.value is None:
            return "None"
        return truefalse(self.value)

    def __str__(self):
        """
        Convert to string.

        Returns:
            \"true\", \"false\" or \"None\"
        """
        return self.__repr__()

########################################


class VSIntegerProperty(object):
    """
    Value can only be integer or None

    Attributes:
        name: Name of the validator
        switch: Value if enabled
        value: Integer value
    """

    value = IntegerProperty("_value")

    def __init__(self, name, default=None, switch=None):
        """
        Initialize the default values.
        Set the name (Required), value and compiler switch.

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
            switch: Switch for integer found
        """

        # Init the defaults
        self.name = name
        self.switch = switch
        self.value = default

    ########################################

    def get_value(self):
        """
        Return the string representation of the integer, or None

        Returns:
            String of number or None
        """
        temp = self.value
        if temp is not None:
            temp = str(temp)
        return temp

    ########################################

    def __repr__(self):
        """
        Convert to string.

        Returns:
            Value as a string or "None"
        """

        if self.value is None:
            return "None"
        return str(self.value)

    def __str__(self):
        """
        Convert to string.

        Returns:
            Value as a string or "None"
        """
        return self.__repr__()


########################################


class VSStringProperty(object):
    """
    Value can be any string.

    Attributes:
        name: Name of the validator
        value: String value
    """

    value = StringProperty("_value")

    def __init__(self, name, default=None):
        """
        Initialize the default value

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
        """

        # Set defaults
        self.name = name
        self.value = default

    ########################################

    def get_value(self):
        """
        Return the string representation of the string, or None
        """
        return self.value

    ########################################

    def __repr__(self):
        """
        Convert to string.

        Returns:
            Value as a string
        """

        # None becomes "None"
        return "{}".format(self.value)

    def __str__(self):
        """
        Convert to string.

        Returns:
            Value as a string
        """
        return self.__repr__()


########################################


class StringListProperty(object):
    """
    List of strings or directories.

    Attributes:
        name: Name of the validator
        default: Default values of the validator
        slashes: Slashes for directory
        separator: Seperator character instead of ";"
        force_ending_slash: True if an endling slash is needed for a directory
        value: String list value
    """

    value = StringListProp("_value")

    # pylint: disable=too-many-arguments
    def __init__(self, name, default, slashes=None, separator=None,
                 force_ending_slash=False):
        """
        Initialize the default value

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
            slashes: "/" or '\\' or None for no conversion
            separator: Character to use to seperate entries, ";" for None
            force_ending_slash: Enforce a trailing slash if True
        """

        # Ensure the value is always a list
        if default is None:
            default = []

        self.name = name
        self.default = default
        self.slashes = slashes
        self.separator = separator
        self.force_ending_slash = force_ending_slash

        # Initial value
        self.value = []

        # Check if the default value is valid
        self.set_value(default)

    ########################################

    def set_value(self, value):
        """
        Update the value with a string.

        Value can be a boolean, a number, a string or None
        to set to default.

        Args:
            value: None, bool, number, or string.
        """

        # Reset to default?
        if value is None:
            self.value = self.default
        else:
            # Update the list
            self.value = value

    ########################################

    def get_value(self):
        """
        Return the string representation of the string, or None
        """

        if self.value:
            return packed_paths(
                self.value, slashes=self.slashes, separator=self.separator,
                force_ending_slash=self.force_ending_slash)
        return None

    ########################################

    def __repr__(self):
        """
        Convert to string.

        Returns:
            Value as a string
        """

        return "{}".format(self.value)

    def __str__(self):
        """
        Convert to string.

        Returns:
            Value as a string
        """
        return self.__repr__()

########################################


class EnumProperty():
    """
    Enumeration integer value.

    Attributes:
        name: Name of the validator
        default: Default value of the validator
        value: Active value
        enumerations: Enumeration alias list
    """

    def __init__(self, name, default, enumerations):
        """
        Initialize the default value

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
            enumerations: List of enumeration alias tuples.
        """

        self.name = name
        self.default = default
        self.value = None
        self.enumerations = enumerations

        # Check if the default value is valid
        self.set_value(default)

    ########################################

    def set_value(self, value):
        """
        Update with an index or an enumeration string.

        Value can be a number, a string or None
        to set to default.

        Args:
            value: None, number, or string.
        Except:
            ValueError on input error
        """

        # Reset to default?
        if value is None:
            self.value = self.default
        else:
            # In case of error, kill value
            self.value = None

            # Try the easy way first, is it a number?
            try:
                int_value = int(value)

            # Do a string lookup instead.
            except ValueError:

                # Go down the list
                for int_value, item in enumerate(self.enumerations):

                    # Single item?
                    if is_string(item):
                        # Match?
                        if item == value:
                            break
                    else:
                        # Is it in the list?
                        if value in item:
                            break
                else:
                    raise ValueError(
                        "\"{}\": {} was not found in enumeration list".format(
                            self.name, value))

            # Perform a sanity check on the integer value
            if int_value < 0 or int_value >= len(self.enumerations):
                raise ValueError(
                    "\"{}\": Index {} must be between 0 and {} inclusive.".format(
                        self.name, value, len(
                            self.enumerations) - 1))

            # Convert integer to a string
            self.value = "{}".format(int_value)

    ########################################

    def get_value(self):
        """
        Return the string representation of the string, or None
        """
        return self.value

    ########################################

    def __repr__(self):
        """
        Convert to string.

        Returns:
            Value as a string
        """

        return "{}".format(self.value)

    def __str__(self):
        """
        Convert to string.

        Returns:
            Value as a string
        """
        return self.__repr__()
