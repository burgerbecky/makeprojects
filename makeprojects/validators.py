#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Validation objects for project data generators.
"""

## \package makeprojects.validators

# pylint: disable=no-name-in-module,useless-object-inheritance
# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

from burger import is_string, packed_paths, truefalse, \
    BooleanProperty as BooleanProp, StringProperty as StringProp, \
    StringListProperty as StringListProp, \
    IntegerProperty as IntegerProp

########################################


def lookup_enum(cmd, enum_lookup, value):
    """ Look up a command line option from an enum
    Args:
        cmd: list of command line options to append the new entry
        enum_lookup: dict of enumeration entries
        value: integer enumeration value to look up
    """

    # None aborts
    if value is not None:

        # Convert strings to an integer
        value = int(value)

        # Scan the table until a match is found
        for key, index in enum_lookup.items():

            # Match?
            if index == value:

                if key is not None:
                    # Append the command
                    cmd.append(key)
                break

########################################


def lookup_enums(cmd, enum_dicts, command_dict):
    """ Look up a set of enum command line options

    An enumeration table is a dict with each key being a
    value to enumerate and the value the integer enumeration
    value. Synonyms are allowed by having previously used
    integer value. Reverse lookup of the command line
    switch is performed by scanning the integer values and
    stopping on the first match. If the key starts with
    ``_NOT_USED``, it is assumed to be an enumeration that
    purposefully does not have a command line switch.

    Args:
        cmd: list of command line options to append the new entry
        enum_dicts: dict of enumeration entries
        command_dict: dict of command entries
    """

    # Read from the master list
    for key, item in enum_dicts.items():
        # Process the enumeration
        value = command_dict.get(key, None)

        # Discard phony keys
        if is_string(value):
            if value.startswith('_NOT_USED'):
                value = None

        if value is None:
            # Use the default
            value = item[0]
            if value is None:
                continue
        lookup_enum(cmd, item[1], value)

########################################


def lookup_strings(cmd, string_dict, command_dict):
    """ Lookup string items and add them to the command line
    Args:
        cmd: list of command line options to append the new entry
        string_dict: dict of string entries
        command_dict: dict of command entries
    Returns:
        String list of string items the generate output
    """

    # Initialize the output
    outputs = []

    for key, table in string_dict.items():
        # Was there an override?
        temp = command_dict.get(key, None)
        if temp is None:
            # Use the default instead
            temp = table[0]
            # No default?
            if not temp:
                continue

        # Create the command line entry
        if table[2]:
            quoted = '"{}"'.format(temp)
        else:
            quoted = temp

        cmd.append('{}{}'.format(table[1], quoted))
        if table[2]:
            outputs.append(temp)

    return outputs

########################################


def lookup_string_list(cmd, command, entry_list, spacing=False, quotes=True):
    """ Create a command line with an entry list
    Args:
        cmd: list of command line options to append the new entry
        command: Command prefix
        entry_list: List of
        spacing: True causes the parameter to be a seperate entry
        quotes: True caused the entries to be quoted
    """

    for item in entry_list:

        if quotes:
            item = '"{}"'.format(item)

        # Seperate lines
        if spacing:
            cmd.append(command)
            cmd.append(item)
        else:
            # One line
            cmd.append('{}{}'.format(command, item))

########################################


def lookup_string_lists(cmd, string_list_dict, command_dict):
    """ Lookup string items and add them to the command line
    Args:
        cmd: list of command line options to append the new entry
        string_list_dict: dict of string list entries
        command_dict: dict of command entries
    Returns:
        String list of string items the generate output
    """

    for key, table in string_list_dict.items():
        # Was there an override?
        temp = command_dict.get(key, [])
        if temp:
            switch = table[0]
            spacing = switch.endswith(' ')
            if spacing:
                switch = switch[:-1]
            lookup_string_list(cmd, switch, temp, spacing, table[1])

########################################


def lookup_booleans(cmd, boolean_lookup, command_dict):
    """ Look up a command line option from a list of booleans
    Args:
        cmd: list of command line options to append the new entry
        boolean_lookup: dict of boolean entries
        command_dict: dict of command entries
    """

    # Scan the table until a match is found
    for key, table in boolean_lookup.items():

        # Was there an override?
        temp = command_dict.get(key, None)
        if temp is None:
            # Use the default instead
            temp = table[0]

            # If no override or default, skip
            if temp is None:
                continue

        # Check if the value actually sets a command line entry
        for key2, table2 in table[1].items():
            if table2 is temp:
                cmd.append(key2)
                break

########################################


class BooleanProperty(object):
    """
    Value can only be true or false.
    """

    ## Boolean value
    value = BooleanProp('_value')

    def __init__(self, name, default=None):
        """
        Initialize the default value

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
        """

        ## Name of the validator
        self.name = name

        ## Init the default value
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
        """ Check if there is a default
        Args:
            key: Name of the XML attribute key
            configuration: configuration to scan for an override
            default: Value to use in case there is no override.
            options_key: Attribute to scan for commmand line options
            options: Iterable with options / Value pairs
        Returns:
            None or BooleanProperty() instance
        """
        if options_key is not None:
            options_key = configuration.get_chained_value(options_key)
            if options_key:
                for item in options:
                    if item[0] in options_key:
                        default = item[1]
                        break

        if default is None:
            return None
        return BooleanProperty(key, default)

    ########################################

    @staticmethod
    def vs_validate(key, configuration, default=None,
                    options_key=None, options=None):
        """ Check if there is an override
        Args:
            key: Name of the XML attribute key
            configuration: configuration to scan for an override
            default: Value to use in case there is no override.
            options_key: Attribute to scan for commmand line options
            options: Iterable with options / Value pairs
        Returns:
            None or BooleanProperty() instance
        """
        value = configuration.get_chained_value('vs_' + key)
        if value is None:
            return BooleanProperty.validate(
                key, configuration, default, options_key, options)
        return BooleanProperty(key, value)

    ########################################

    def __repr__(self):
        """
        Convert to string.

        Returns:
            Value as a string
        """

        if self.value is None:
            return 'None'
        return truefalse(self.value)

    ## Allow str() to work.
    __str__ = __repr__


########################################


class IntegerProperty(object):
    """
    Value can only be integer or None
    """

    ## Integer value
    value = IntegerProp('_value')

    def __init__(self, name, default=None, switch=None):
        """
        Initialize the default value

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
            switch: Switch for integer found
        """

        ## Name of the validator
        self.name = name

        ## Value if enabled
        self.switch = switch

        # Init the default value
        self.value = default

    ########################################

    def get_value(self):
        """
        Return the string representation of the string, or None
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
            Value as a string
        """

        if self.value is None:
            return 'None'
        return str(self.value)

    ## Allow str() to work.
    __str__ = __repr__

########################################


class StringProperty():
    """
    Value can be any string.
    """

    ## String value
    value = StringProp('_value')

    def __init__(self, name, default=None):
        """
        Initialize the default value

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
        """

        ## Name of the validator
        self.name = name

        ## Active value
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

        return '{}'.format(self.value)

    ## Allow str() to work.
    __str__ = __repr__


########################################


class StringListProperty():
    """
    List of strings or directories.
    """

    ## String list value
    value = StringListProp('_value')

    # pylint: disable=too-many-arguments
    def __init__(self, name, default, slashes=None, seperator=None,
                 force_ending_slash=False):
        """
        Initialize the default value

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
            slashes: None for no conversion, '/' or '\\' path seperator
            seperator: Character to use to seperate entries, ';' for None
            force_ending_slash: Enforce a trailing slash if True
        """

        # Ensure the value is always a list
        if default is None:
            default = []

        ## Name of the validator
        self.name = name

        ## Default values of the validator
        self.default = default

        ## Slashes for directory
        self.slashes = slashes

        ## Seperator character instead of ';'
        self.seperator = seperator

        ## True if an endling slash is needed for a directory
        self.force_ending_slash = force_ending_slash

        ## Active value
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
                self.value, slashes=self.slashes, seperator=self.seperator,
                force_ending_slash=self.force_ending_slash)
        return None

    ########################################

    def __repr__(self):
        """
        Convert to string.

        Returns:
            Value as a string
        """

        return '{}'.format(self.value)

    ## Allow str() to work.
    __str__ = __repr__

########################################


class EnumProperty():
    """
    Enumeration integer value.
    """

    def __init__(self, name, default, enumerations):
        """
        Initialize the default value

        Args:
            name: Name of the validator
            default: Default value, ``None`` is acceptable
            enumerations: List of enumeration alias tuples.
        """

        ## Name of the validator
        self.name = name

        ## Default value of the validator
        self.default = default

        ## Active value
        self.value = None

        ## Enumeration alias list
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
                        '"{}": {} was not found in enumeration list'.format(
                            self.name, value))

            # Perform a sanity check on the integer value
            if int_value < 0 or int_value >= len(self.enumerations):
                raise ValueError(
                    '"{}": Index {} must be between 0 and {} inclusive.'.format(
                        self.name, value, len(
                            self.enumerations) - 1))

            # Convert integer to a string
            self.value = '{}'.format(int_value)

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

        return '{}'.format(self.value)

    ## Allow str() to work.
    __str__ = __repr__
