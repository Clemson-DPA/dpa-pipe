# -----------------------------------------------------------------------------
# Module: dpa.ptask.assignment
# Author: Josh Tomlinson (jtomlin@clemson.edu)
# -----------------------------------------------------------------------------
"""Classes and functions related to DPA pipeline ptask assignments

Classes
-------
PTaskAssignment
    Interface to ptask assignments
 
Examples
--------

    ... TODO ...


"""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

from dateutil import parser as date_parser

from dpa.restful import RestfulObject
from dpa.restful.mixins import CreateMixin, GetMixin, ListMixin, UpdateMixin
from dpa.user import User

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class PTaskAssignment(CreateMixin, GetMixin, ListMixin, UpdateMixin,
    RestfulObject):
    """Interface to ptask assignments.
    
    Instance properties:
        
        .id
        .ptask
        .ptask_spec
        .user
        .user_username
        .start_date
        .end_date
        .active
    
    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'ptask-assignments'

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, ptask_spec, username, active=None, end_date=None,
        start_date=None):

        data = {
            "active": active,
            "end_date": end_date,
            "ptask": ptask_spec,
            "start_date": start_date,
            "user": username,
        }

        return super(PTaskAssignment, cls).create(data)

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, ptask_spec, username, **filters):

        # join the ptask_spec and username to make the pk for the query
        spec = ",".join([ptask_spec, username])
        return super(PTaskAssignment, cls).get(spec, **filters)

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __repr__(self):
        """:returns: Unique string representation of the assignment."""
        
        # since 2 fields make up the unique key, tweak the representation
        return self.__class__.__name__ + "('" + self.spec + "')"

    # -------------------------------------------------------------------------
    # Public methods:
    # -------------------------------------------------------------------------
    def update(self, start_date=None, end_date=None, active=None):

        data = {
            "active": active,
            "end_date": end_date,
            "start_date": start_date,
        }

        return super(PTaskAssignment, self).update(self.spec, data)

    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def active(self):
        """:returns: a boolean for the active state of this assignment."""
        return self._data.get('active')

    # -------------------------------------------------------------------------
    @property
    def end_date(self):
        """:returns: a date object for the end date of this assignment.""" 
        return date_parser.parse(self._data.get('end_date')).date()

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        """:returns: PTask object for this assignment."""
        if not self.ptask_spec:
            return None 

        # import here to avoid circular dependencies
        from dpa.ptask import PTask
        return PTask.get(self.ptask_spec)

    # -------------------------------------------------------------------------
    @property
    def ptask_spec(self):
        """:returns: a spec string for the ptask of this assignment."""
        spec = self._data.get('ptask')
        if not spec:
            spec = ""
        return spec

    # -------------------------------------------------------------------------
    @property
    def start_date(self):
        """:returns: a date object for the start date of this assignment.""" 
        return date_parser.parse(self._data.get('start_date')).date()

    # -------------------------------------------------------------------------
    @property
    def user(self):
        """:returns: a User object for the user assigned to the ptask."""
        return User.get(self.user_username)

    # -------------------------------------------------------------------------
    @property
    def user_username(self):
        """:returns: username str for the user assigned to the ptask."""
        return self._data.get("user")

