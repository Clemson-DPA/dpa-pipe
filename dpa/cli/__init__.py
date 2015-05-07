"""Pipeline customizations on top of the built-in argparse API."""

# -----------------------------------------------------------------------------
# Module: dpa.argparse
# Contact: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import argparse
import datetime
import sys

from parsedatetime.parsedatetime import Calendar

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class ParseDateTimeArg(argparse.Action):
    """argparse.Action subclass. parses natural language cl datetime strings.

    Use this class as an argument to the 'action' argument when calling
    add_argument on an argparse parser. When the command line arguments are 
    parsed, the resulting namespace will have a datetime.datetime object
    assigned to the argument's destination. 

    If a datetime could not be parsed from the string, a ValueError will be 
    raised. 

    Examples of parsable human readable datetime strings:

        "now", "yesterday", "2 weeks from now", "3 days ago", etc.

    Note: When the datetime string is more than one word, you should include
    the argument in quotes on the command line.

    """

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, datetime_str, option_string=None):
        parsed_datetime = date_time_from_str(datetime_str)
        setattr(namespace, self.dest, parsed_datetime)

# -----------------------------------------------------------------------------
class ParseDateArg(argparse.Action):
    """Similar to ParseDateTimeArg.
    
    Parses and returns a datetime.date object.
    
    """

    # -------------------------------------------------------------------------
    def __call__(self, parser, namespace, datetime_str, option_string=None):
        parsed_datetime = date_time_from_str(datetime_str)
        setattr(namespace, self.dest, parsed_datetime.date())

# -----------------------------------------------------------------------------
# Public functions:
# -----------------------------------------------------------------------------
def date_time_from_str(datetime_str):
    # from http://stackoverflow.com/a/5903760, updated with more reasonable 
    # variable names.

    assert datetime, "Unable to parse empty date/time string."

    parsed_result, date_type = Calendar().parse(datetime_str)

    parsed_datetime = None

    # what was returned (based on parsedatetime docs)
    # 0 = failed to parse
    # 1 = date (with current time, as a struct_time)
    # 2 = time (with current date, as a struct_time)
    # 3 = datetime

    if date_type == 3:

        # parsed_result is a datetime
        parsed_datetime = parsed_result

    elif date_type in (1, 2):

        # parsed_result is struct_time
        parsed_datetime = datetime.datetime(*parsed_result[:6])

    else:

        # Failed to parse
        raise ValueError("Could not parse date/time string: " + datetime_str)

    return parsed_datetime
     
