# -----------------------------------------------------------------------------
# Module: dpa.user
# Author: Josh Tomlinson (jtomlin@clemson.edu)
# -----------------------------------------------------------------------------
"""Classes and functions related to DPA pipeline users

Classes
-------
User
    Read-only interface to registered dpa users.
 
Examples
--------

    # get an instance of a user
    >>> from dpa.users import User
    >>> user = User.get('jtomlin')
    >>> print user.email
    "jtomlin@clemson.edu"
 
    # get all dpa users 
    >>> from dpa.users import User
    >>> users = User.list()
    >>> print str([user.username for user in users])
    ['jtomlin', 'jtessen']

    # get a filtered list of users by property
    >>> from dpa.users import User 
    >>> users = User.list(active=True)
    >>> print str([user.username for user in users])
    ['jtomlin', 'jtessen']

User objects are read-only. If you feel you need to create a new or modify
an existing user, please see the DPA pipeline support team.

"""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------
 
# Built-in imports:
import os

# attempt to be portable. pwd is unix-only, so if this is running on windows,
# we can fall back to getpass. 
try:
    import pwd
except ImportError:
    import getpass
    pwd = None

from dateutil import parser as date_parser

from dpa.restful import ReadOnlyRestfulObject, RestfulObjectError

# -----------------------------------------------------------------------------
# Public Functions: 
# -----------------------------------------------------------------------------
def current_username():
    """Retrieve the username of the current user.

    :rtype: str
    :return: The username of the current user.
 
    >>> from dpa.user import current_username
    >>> username = current_username()
    >>> print username
    'jtomlin'

    """ 

    # see this StackOverflow thread for a discussion on a portable way to 
    # get the current user name: http://tinyurl.com/ykecvzc
    if pwd:
        return pwd.getpwuid(os.geteuid()).pw_name
    else:
        return getpass.getuser()

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class User(ReadOnlyRestfulObject):
    """Read-only interface to registered dpa users.
    
    Instance properties:
        
        user.email
        user.first_name
        user.full_name
        user.id
        user.is_active
        user.is_staff
        user.is_superuser
        user.last_name
        user.username
    
    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'users'

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def current(cls):
        return cls.get(current_username())

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __eq__(self, other):
        return self.username == other.username

    # -------------------------------------------------------------------------
    def __ne__(self, other):
        return self.username != other.username

    # -------------------------------------------------------------------------
    def __repr__(self):
        return self.__class__.__name__ + "('" + self.username + "')"

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def full_name(self):
        """:returns: User's full name as a str."""
        return self._data.get("first_name") + ' ' + self._data.get("last_name")

# -----------------------------------------------------------------------------
class UserError(RestfulObjectError):
    pass

User.exception_class = UserError

