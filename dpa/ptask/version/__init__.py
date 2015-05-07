# -----------------------------------------------------------------------------
# Module: dpa.ptask.version
# Author: Josh Tomlinson (jtomlin@clemson.edu)
# -----------------------------------------------------------------------------
"""Classes and functions related to DPA pipeline ptask versions

Classes
-------
PTaskVersion
    Interface to ptask versions 
 
Examples
--------

    ... TODO ...


"""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

from dateutil import parser as date_parser

from dpa.restful import RestfulObject, RestfulObjectError
from dpa.restful.mixins import CreateMixin, GetMixin, ListMixin, UpdateMixin
from dpa.location import Location
from dpa.user import User

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class PTaskVersion(CreateMixin, GetMixin, ListMixin, UpdateMixin, RestfulObject):
    """Interface to ptask versions.
    
    Instance properties:
        
        .children
        .created
        .creator
        .description
        .id
        .location
        .number
        .parent
        .parent_spec
        .ptask
        .ptask_spec
        .spec
    
    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'ptask-versions'

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, creator, description, location_code, ptask_spec, number,
        parent_spec=None):

        # XXX validate arguments

        data = {
            "creator": creator,
            "description": description,
            "location": location_code,
            "number": number,
            "parent": parent_spec,
            "ptask": ptask_spec,
        }

        return super(PTaskVersion, cls).create(data)

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------
    def __eq__(self, other):
        return self.spec == other.spec

    # -------------------------------------------------------------------------
    def __ne__(self, other):
        return self.spec != other.spec

    # -------------------------------------------------------------------------
    def __repr__(self):
        
        return self.__class__.__name__ + "('" + self.spec + "')"

    # -------------------------------------------------------------------------
    # Public methods:
    # -------------------------------------------------------------------------
    def is_subscribed(self, product):
        from dpa.product.subscription import ProductSubscription
        from dpa.ptask.spec import PTaskSpec
        sub_spec = self.spec + "," + product.spec + PTaskSpec.SEPARATOR
        subs = ProductSubscription.list(search=sub_spec)

        if len(subs) == 0:
            return None
        elif len(subs) > 1:
            raise PTaskVersionError(
                "Subscribed to multiple version of the same product! " + \
                "This should not be possible. Please report to the " + \
                "pipeline team."
            )
        else:
            return subs[0]

    # -------------------------------------------------------------------------
    def update(self, description=None, location=None):

        data = {
            "description": description,
            "location": location,
        }

        return super(PTaskVersion, self).update(self.spec, data)

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def children(self):
        """:returns: PTaskVersion list for this version's children."""
        return PTaskVersion.list(parent=self.spec)

    # -------------------------------------------------------------------------
    @property
    def child_specs(self):
        """:returns: str list of version specs for this version's children."""
        return self._data.get("children")

    # -------------------------------------------------------------------------
    @property
    def created(self):
        """:returns: a datetime object for the creation date of this version."""
        return date_parser.parse(self._data.get('created'))

    # -------------------------------------------------------------------------
    @property
    def creator(self):
        """:returns: a User object for the creator of this version."""
        return User.get(self.creator_username)

    # -------------------------------------------------------------------------
    @property
    def creator_username(self):
        """:returns: username str for the creator of this version."""
        return self._data.get("creator")

    # -------------------------------------------------------------------------
    @property
    def location(self):
        """:returns: Location that owns this version."""
        return Location.get(self.location_code)

    # -------------------------------------------------------------------------
    @property
    def location_code(self):
        """:returns: the code str for this version's location."""
        return self._data.get("location")

    # -------------------------------------------------------------------------
    @property
    def number_padded(self):
        """:returns: 4 digit padded string of the version number."""
        return str(self._data.get("number")).zfill(4)

    # -------------------------------------------------------------------------
    @property
    def parent(self):
        """:returns: a PTaskVersion object for the parent of this version."""
        if not self.parent_spec:
            return None 
        return PTaskVersion.get(self.parent_spec)

    # -------------------------------------------------------------------------
    @property
    def parent_spec(self):
        """:returns: a spec string for the parent of this version."""
        spec = self._data.get('parent')
        if not spec:
            spec = ""
        return spec

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        """:returns: PTask object for this version."""
        if not self.ptask_spec:
            return None 

        # import here to avoid circular dependencies
        from dpa.ptask import PTask
        return PTask.get(self.ptask_spec)

    # -------------------------------------------------------------------------
    @property
    def ptask_spec(self):
        """:returns: a spec string for the ptask of this version."""
        spec = self._data.get('ptask')
        if not spec:
            spec = ""
        return spec

    # -------------------------------------------------------------------------
    @property
    def published(self):
        """:returns: True if any products from this version are published."""
        from dpa.product.version import ProductVersion
        pubs = ProductVersion.list(
            ptask_version=self.spec, 
            published=True,
        )
        return len(pubs) > 0

    # -------------------------------------------------------------------------
    @property
    def subscriptions(self):
        """:returns: a list of ProductSubscriptions for this ptask version."""
        from dpa.product.subscription import ProductSubscription
        return ProductSubscription.list(ptask_version=self.spec)

# -----------------------------------------------------------------------------
class PTaskVersionError(RestfulObjectError):
    pass

PTaskVersion.exception_class = PTaskVersionError

