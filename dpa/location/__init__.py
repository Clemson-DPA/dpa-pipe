# -----------------------------------------------------------------------------
# Module: dpa.locations
# Author: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------
"""Classes and methods specific to dpa pipeline physical locations.
 
Classes
-------
:py:obj:`Location`
    Read-only interface to dpa physical locations.
 
Examples
--------

Get an instance of a dpa location::

    >>> from dpa.locations import Location
    >>> location = Location.get('CU_MCADAMS_DPA')
    >>> print locaction.name
    "Clemson DPA"
 
Get all dpa locations::

    >>> from dpa.locations import Location
    >>> locations = Location.list()
    >>> print str([loc.name for loc in locations])
    ['Clemson DPA', 'Clemson Test DPA']


Get a filtered list of dpa locations by properties:

    >>> from dpa.locations import Location
    >>> locations = Location.list(timezone="US/Eastern")
    >>> print str([loc.name for loc in locations])
    ['Clemson DPA']

Locations objects are read-only. If you feel you need to create a new or modify
an existing location, please see the DPA pipeline support team.

"""

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------
 
from dpa.env.vars import DpaVars
from dpa.restful import ReadOnlyRestfulObject, RestfulObjectError

# -----------------------------------------------------------------------------
# Public Functions: 
# -----------------------------------------------------------------------------
def current_location_code():
    """Retrieve the code of the current location.

    :rtype: str
    :return: The code of the current location.
 
    >>> from dpa.location import current_location_code
    >>> code = current_location_code()
    >>> print code
    'CU_MCADAMS_DPA'

    """ 

    return DpaVars.location_code("").get()

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class Location(ReadOnlyRestfulObject):
    """Read-only interface to dpa physical locations.
    
    Instance ``properties``:
        
    :py:obj:`bool` ``active`` - ``True`` if locaiton is active, ``False``
    otherwise

    :py:obj:`str` ``code`` - Unique identifier of the location.

    :py:obj:`str` ``description`` - Description of the location.

    :py:obj:`str` ``name`` - Full name of the location.

    :py:obj:`float` ``latitude`` - Latitude portion of the physical location.

    :py:obj:`float` ``longitude`` - Longitude portion of the physical location.

    :py:obj:`str` ``timezone`` - Name of the timezone for the location, ex: 
    "US/Eastern"
    
    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'locations'
    _current = None

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def current(cls):
        
        if cls._current is None:
            cls._current = cls.get(current_location_code())
        return cls._current

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __eq__(self, other):
        return self.code == other.code

    # -------------------------------------------------------------------------
    def __ne__(self, other):
        return self.code != other.code

    # -------------------------------------------------------------------------
    def __repr__(self):
        
        return self.__class__.__name__ + "('" + self.code + "')"

# -----------------------------------------------------------------------------
class LocationError(RestfulObjectError):
    pass

Location.exception_class = LocationError

