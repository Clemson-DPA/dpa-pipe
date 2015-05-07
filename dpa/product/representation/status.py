"""Classes and functions related to DPA pipeline product representation statuses."""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

from dpa.location import Location
from dpa.ptask.spec import PTaskSpec
from dpa.restful import RestfulObject, RestfulObjectError
from dpa.restful.mixins import CreateMixin, GetMixin, ListMixin, UpdateMixin
from dpa.user import User

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class ProductRepresentationStatus(CreateMixin, GetMixin, ListMixin,
    RestfulObject): 
    """Product Representation API.

    .product_representation
    .product_representation_spec
    .location
    .location_code
    .status
    .spec

    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'product-representation-statuses'

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, product_representation, location, status):

        # XXX validation

        data = {
            "product_representation": product_representation,
            "location": location,
            "status": status,
        }

        return super(ProductRepresentationStatus, cls).create(data)

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, product_representation_spec, location_spec, relative_to=None):

        # XXX PTaskSpec >> ContextSpec
        # XXX PTaskArea >> ContextArea
        # XXX PTaskEnv  >> ContextEnv
        if not isinstance(product_representation_spec, PTaskSpec):
            product_representation_spec = PTaskSpec.get(
                product_representation_spec, relative_to=relative_to)

        spec = ",".join([product_representation_spec, location_spec])

        return super(ProductRepresentationStatus, cls).get(spec)

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
    def product_representation(self):
        from dpa.product.representation import ProductRepresentation
        return ProductRepresentation.get(self.product_representation_spec)

    # -------------------------------------------------------------------------
    @property
    def product_representation_spec(self):
        return self._data.get('product_representation')

    # -------------------------------------------------------------------------
    @property
    def location(self):
        return Location.get(self.location_code)

    # -------------------------------------------------------------------------
    @property
    def location_code(self):
        return self._data.get('location')

# -----------------------------------------------------------------------------
class ProductRepresentationStatusError(RestfulObjectError):
    pass

ProductRepresentationStatus.exception_class = ProductRepresentationStatusError
