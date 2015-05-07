
"""Classes and functions related to DPA pipeline ptasks."""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import re
from dateutil import parser as date_parser

from dpa.location import Location
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec
from dpa.restful import RestfulObject, RestfulObjectError
from dpa.restful.mixins import CreateMixin, GetMixin, ListMixin, UpdateMixin
from dpa.user import User

# -----------------------------------------------------------------------------
# Public Methods:
# -----------------------------------------------------------------------------
def get_all_projects():

    return PTask.list(ptask_type="Project")

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class PTask(CreateMixin, GetMixin, ListMixin, UpdateMixin, RestfulObject):
    """PTask API

    A ``PTask``, short for **Production Task**, is an object that represents
    work that needs to be completed. The highest level ``PTask`` is the project
    itself, which contains other ``PTasks``.
    
    Instance properties:
        
        .active
        .assignments
        .children
        .created
        .creator
        .creator_username
        .description
        .due_date
        .id
        .name
        .parent
        .parent_spec
        .priority
        .spec
        .start_date
        .status
        .type
    
    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'ptasks'

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, name, ptask_type, description, 
        creator_username=None, parent_spec=None, start_date=None, 
        due_date=None, priority=50, status=1, active=True
    ):

        # XXX validate name
        # XXX validate ptask_type
        # XXX make sure description is not empty
        # XXX validate username
        # XXX add boolean to ptask types stating whether they require parent
        # XXX make sure start/due dates are date objects, format the strings properly

        # populate missing values with defaults if need be

        data = {
            "name": name,
            "ptask_type": ptask_type,
            "description": description,
            "creator": creator_username,
            "parent": parent_spec,
            "start_date": start_date,
            "due_date": due_date,
            "priority": priority,
            "status": status,
            "active": active,
        }

        return super(PTask, cls).create(data)

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, spec, relative_to=None):

        # convenience that allows calling code to not have to type check 
        # input that allows either spec or ptask 
        if isinstance(spec, PTask):
            return spec

        if not isinstance(spec, PTaskSpec):
            spec = PTaskSpec.get(spec, relative_to=relative_to)

        # empty spec
        if not spec:
            raise PTaskError("Invalid empty spec supplied for ptask.")

        return super(PTask, cls).get(spec)

    # -------------------------------------------------------------------------
    @classmethod
    def list(cls, **filters):

        if not filters:
            raise PTaskError("Must supply at least on filter for ptask list.")

        return super(PTask, cls).list(**filters)

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __eq__(self, other):
        return self.spec == other.spec

    # -------------------------------------------------------------------------
    def __ne__(self, other):
        return self.spec != other.spec

    # -------------------------------------------------------------------------
    def __repr__(self):
        """:returns: Unique string represntation of the ptask."""
        return self.__class__.__name__ + "('" + self.spec + "')"

    # -------------------------------------------------------------------------
    def __str__(self):
        return self.spec

    # -------------------------------------------------------------------------
    # Public methods:
    # -------------------------------------------------------------------------
    def update(self, active=None, description=None, priority=None,
        status=None, start_date=None, due_date=None):

        data = {
            "active": active,
            "description": description,
            "priority": priority,
            "status": status,
            "start_date": start_date,
            "due_date": due_date,
        }

        return super(PTask, self).update(self.spec, data)

    # -------------------------------------------------------------------------
    def version(self, version_number):

        from dpa.ptask.version import PTaskVersion, PTaskVersionError
        try:
            versions = PTaskVersion.list(
                ptask=self.spec,
                number=int(version_number),
            )
        except PTaskVersionError:
            return None
        else:
            if len(versions) != 1:
                return None
            else:
                return versions[0]

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def area(self):
        """:returns: PTaskArea for this ptask."""

        if not hasattr(self, '_area'):
            self._area = PTaskArea(self.spec)

        return self._area

    # -------------------------------------------------------------------------
    @property
    def assignments(self):
        """:returns: a list of PTaskAssignments for this ptask."""

        # import here to avoid circular dependencies
        from dpa.ptask.assignment import PTaskAssignment
        return PTaskAssignment.list(ptask=self.spec)

    # -------------------------------------------------------------------------
    @property
    def assigned_usernames(self):
        """:returns: str list of assigned usernames for this ptask."""
        return self._data.get("assignments")

    # -------------------------------------------------------------------------
    @property
    def children(self):
        """:returns: a list of PTask objects for this ptask's children."""
        return PTask.list(parent=self.spec)

    # -------------------------------------------------------------------------
    @property
    def children_recursive(self):
        """:returns: a recursive list of child ptasks."""
        ptasks = PTask.list(search=self.spec)
        return [p for p in ptasks if p != self]

    # -------------------------------------------------------------------------
    @property
    def child_specs(self):
        """:returns: str list of specs for this ptask's children."""
        return self._data.get("children")

    # -------------------------------------------------------------------------
    @property
    def created(self):
        """:returns: a datetime object for the creation date of this ptask."""
        return date_parser.parse(self._data.get('created'))

    # -------------------------------------------------------------------------
    @property
    def creator(self):
        """:returns: a User object for the creator of this ptask."""
        return User.get(self.creator_username)

    # -------------------------------------------------------------------------
    @property
    def creator_username(self):
        """:returns: username str for the creator of this ptask."""
        return self._data.get("creator")

    # -------------------------------------------------------------------------
    @property
    def due_date(self):
        """:returns: a date object for the due date of this ptask.""" 
        return date_parser.parse(self._data.get('due_date')).date()

    # -------------------------------------------------------------------------
    @property
    def parent(self):
        """:returns: a PTask object for the parent of this ptask."""
        if not self.parent_spec:
            return None 
        return PTask.get(self.parent_spec)

    # -------------------------------------------------------------------------
    @property
    def parent_spec(self):
        """:returns: a spec string for the parent of this ptask."""
        spec = self._data.get('parent')
        if not spec:
            spec = ""
        return spec

    # -------------------------------------------------------------------------
    @property
    def start_date(self):
        """:returns: a date object for the start date of this ptask.""" 
        return date_parser.parse(self._data.get('start_date')).date()

    # -------------------------------------------------------------------------
    @property
    def type(self):
        """:returns: a the name of the type of this ptask."""
        return self._data.get('ptask_type')

    # -------------------------------------------------------------------------
    @property
    def versions(self):
        """:returns: PTaskVersions created for this ptask."""

        # import here to avoid circular dependencies
        from dpa.ptask.version import PTaskVersion
        return PTaskVersion.list(ptask=self.spec)

    # -------------------------------------------------------------------------
    @property
    def latest_version(self):
        """:returns: PTaskVersion with highest version number.""" 

        return sorted(self.versions, key=lambda v: v.number)[-1]

    # -------------------------------------------------------------------------
    @property
    def next_version_number(self):
        """:returns: int representing the next (yet to be created) version."""

        latest_version = self.latest_version
        return latest_version.number + 1

    # -------------------------------------------------------------------------
    @property
    def next_version_number_padded(self):
        """:returns: padded str representing the next version."""

        latest_version = self.latest_version
        return str(latest_version.number + 1).zfill(4)

    # -------------------------------------------------------------------------
    @property
    def spec(self):
        """:returns: PTaskSpec object representing this ptask's spec."""
        return PTaskSpec.get(self._data.get('spec'))

    # -------------------------------------------------------------------------
    @property
    def types(self):

        if hasattr(self, '_types'):
            return self._types

        ancestor_specs = self.area.ancestor_specs

        types = dict()

        # XXX should be able to do 1 query to retrieve all of these. 
        # Need to fix the rest api's 'specs' query.
        for spec in ancestor_specs:
            ptask = PTask.get(spec)
            name = ptask.name
            types[ptask.type] = name
            
        self._types = types
        return self._types

# -----------------------------------------------------------------------------
class PTaskError(RestfulObjectError):
    pass

PTask.exception_class = PTaskError

# -----------------------------------------------------------------------------
def validate_ptask_name(name):

    # starts with a letter
    if not re.match("^[a-zA-Z]", name):
        raise PTaskError("PTask name must begin with a letter.")

    # only contains letter, underscore, digits
    if not re.match("^\w+$", name):
        raise PTaskError("PTask name can only contain alpha numeric characters.")

    # must be at least 2 characters long
    if len(name) < 2:
        raise PTaskError(
            "Product name must be at least 3 characters long."
        )

    return name

