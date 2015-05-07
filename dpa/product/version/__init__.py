"""Classes and functions related to DPA pipeline product versions."""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

from dateutil import parser as date_parser
from dpa.ptask.spec import PTaskSpec
from dpa.restful import RestfulObject, RestfulObjectError
from dpa.restful.mixins import CreateMixin, GetMixin, ListMixin, UpdateMixin
from dpa.user import User

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class ProductVersion(CreateMixin, GetMixin, ListMixin, UpdateMixin, 
    RestfulObject):
    """Product Version API.
    
        .creator
        .creator_username
        .created
        .deprecated
        .id
        .number
        .number_padded
        .product
        .product_spec
        .ptask_version
        .ptask_version_spec
        .published
        .release_note
        .spec
    
    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'product-versions'

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, ptask_version, product, release_note=None, creator=None):

        # XXX validation

        data = {
            "ptask_version": ptask_version,
            "product": product,
            "release_note": release_note,
            "creator": creator,
        }

        return super(ProductVersion, cls).create(data)

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, spec, relative_to=None):

        # convenience that allows calling code to not have to type check 
        # input that allows either spec or ptask 
        if isinstance(spec, ProductVersion):
            return spec

        # XXX PTaskSpec >> ContextSpec
        # XXX PTaskArea >> ContextArea
        # XXX PTaskEnv  >> ContextEnv
        if not isinstance(spec, PTaskSpec):
            spec = PTaskSpec.get(spec, relative_to=relative_to)

        return super(ProductVersion, cls).get(spec)

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
    # Public methods:
    # -------------------------------------------------------------------------
    def deprecate(self):
        self.update(deprecated=True)

    # -------------------------------------------------------------------------
    def undeprecate(self):
        self.update(deprecated=False)

    # -------------------------------------------------------------------------
    def official(self):
        self.product.set_official(self)

    # -------------------------------------------------------------------------
    def publish(self):
        self.update(published=True)

    # -------------------------------------------------------------------------
    def unpublish(self):
        self.update(published=False)

    # -------------------------------------------------------------------------
    def update(self, release_note=None, published=None, deprecated=None):

        data = {
            "release_note": release_note,
            "published": published,
            "deprecated": deprecated,
        }

        return super(ProductVersion, self).update(self.spec, data)

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
    def created(self):
        return date_parser.parse(self._data.get('created'))    

    # -------------------------------------------------------------------------
    @property
    def is_official(self):
        return self.product.official_version_number == self.number 

    # -------------------------------------------------------------------------
    @property
    def number_padded(self):
        return str(self._data.get("number")).zfill(4) 

    # -------------------------------------------------------------------------
    @property
    def product(self):
        from dpa.product import Product
        return Product.get(self.product_spec)

    # -------------------------------------------------------------------------
    @property
    def product_spec(self):
        return self._data.get('product')

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        return self.ptask_version.ptask

    # -------------------------------------------------------------------------
    @property
    def ptask_version(self):
        from dpa.ptask.version import PTaskVersion
        return PTaskVersion.get(self.ptask_version_spec)

    # -------------------------------------------------------------------------
    @property
    def ptask_version_spec(self):
        return self._data.get('ptask_version')

    # -------------------------------------------------------------------------
    @property
    def representations(self):
        from dpa.product.representation import ProductRepresentation
        return ProductRepresentation.list(product_version=self.spec)

    # -------------------------------------------------------------------------
    @property
    def subscribers(self):
        return [sub.ptask_version for sub in self.subscriptions]

    # -------------------------------------------------------------------------
    @property
    def subscriptions(self):
        from dpa.product.subscription import ProductSubscription
        return ProductSubscription.list(product_version=self.spec)

# -----------------------------------------------------------------------------
class ProductVersionError(RestfulObjectError):
    pass

ProductVersion.exception_class = ProductVersionError
