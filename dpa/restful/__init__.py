"""A framework for restful APIs."""
# -----------------------------------------------------------------------------
# Module: dpa.restful
# Author: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------
 
import copy

from .client import RestfulClientError
from .mixins import ListMixin, GetMixin

# -----------------------------------------------------------------------------
# Public Classes
# -----------------------------------------------------------------------------
class RestfulObject(object):

    exception_class = None
    
    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, data):
        self._data = _RestfulData(data)

    # -------------------------------------------------------------------------
    def __getattr__(self, attr):

        # look up the attribute in the _data
        try:
            return self._data.get(attr)
        except _RestfulDataError:
            raise AttributeError(
                '{cls} instance has no attribute "{attr}"'.format(
                    cls=self.__class__.__name__,
                    attr=attr,
                )
            )

# -----------------------------------------------------------------------------
class RestfulObjectError(RestfulClientError):
    pass

RestfulObject.exception_class = RestfulObjectError

# -----------------------------------------------------------------------------
class ReadOnlyRestfulObject(ListMixin, GetMixin, RestfulObject):
    pass

# -----------------------------------------------------------------------------
# Private Classes:
# -----------------------------------------------------------------------------
class _RestfulData(object):

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, data_dict):
        """Constructor."""

        super(_RestfulData, self).__init__()
        self._data = data_dict

    # -------------------------------------------------------------------------
    # Instance methods:
    # -------------------------------------------------------------------------
    def get(self, attr):

        try:
            return self._data[attr]
        except KeyError:
            raise _RestfulDataError(
                "No attribute '{a}' in data object.".format(a=attr))

    # -------------------------------------------------------------------------
    def set(self, attr, value):

        if not attr in self._data.keys():
            raise _RestfulDataError(
                "No attribute '{a}' in data object.".format(a=attr))

        self._data[attr] = value

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def data_dict(self):
        return self._data

    # -------------------------------------------------------------------------
    @data_dict.setter
    def data_dict(self, data):
        self._data = data

# -----------------------------------------------------------------------------
# Public exception classes:
# -----------------------------------------------------------------------------
class _RestfulDataError(Exception):
    pass

