"""Classes and functions related to DPA pipeline product representations."""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

from dateutil import parser as date_parser

from dpa.location import Location
from dpa.product.version import ProductVersion
from dpa.ptask.spec import PTaskSpec
from dpa.restful import RestfulObject, RestfulObjectError
from dpa.restful.mixins import CreateMixin, GetMixin, ListMixin
from dpa.user import User

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class ProductRepresentation(CreateMixin, GetMixin, ListMixin, RestfulObject):
    """Product Representation API.


        .creator
        .creator_username
        .creation_location
        .creation_location_code
        .id
        .product_version
        .product_version_spec
        .spec
        .type
        .resolution

    """
    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'product-representations'

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, product_version, resolution, representation_type,
        creation_location=None, creator=None):

        # XXX validation

        data = {
            "product_version": product_version,
            "resolution": resolution,
            "representation_type": representation_type,
            "creation_location": creation_location,
            "creator": creator
        }

        return super(ProductRepresentation, cls).create(data)

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, spec, relative_to=None):

        # convenience that allows calling code to not have to type check 
        # input that allows either spec or ptask 
        if isinstance(spec, ProductRepresentation):
            return spec

        # XXX PTaskSpec >> ContextSpec
        # XXX PTaskArea >> ContextArea
        # XXX PTaskEnv  >> ContextEnv
        if not isinstance(spec, PTaskSpec):
            spec = PTaskSpec.get(spec, relative_to=relative_to)

        return super(ProductRepresentation, cls).get(spec)

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
        """:returns: Unique string represntation of the product."""
        return self.__class__.__name__ + "('" + self.spec + "')"

    # -------------------------------------------------------------------------
    @property
    def creator(self):
        return User.get(self.creator_username)

    # -------------------------------------------------------------------------
    @property
    def creator_username(self):
        return self._data.get('creator')

    # -------------------------------------------------------------------------
    @property
    def creation_location(self):
        return Location.get(self.creation_location_code)

    # -------------------------------------------------------------------------
    @property
    def creation_location_code(self):
        return self._data.get('creation_location')

    # -------------------------------------------------------------------------
    @property
    def directory(self):
        from dpa.ptask.area import PTaskArea    
        area = PTaskArea(self.spec, validate=False)
        return area.path

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        return self.product_version.ptask

    # -------------------------------------------------------------------------
    @property
    def product_version(self):
        from dpa.product.version import ProductVersion
        return ProductVersion.get(self.product_version_spec)

    # -------------------------------------------------------------------------
    @property
    def product_version_spec(self):
        return self._data.get('product_version')

    # -------------------------------------------------------------------------
    @property
    def type(self):
        return self._data.get('representation_type')

# -----------------------------------------------------------------------------
class ProductRepresentationError(RestfulObjectError):
    pass

ProductRepresentation.exception_class = ProductRepresentationError
