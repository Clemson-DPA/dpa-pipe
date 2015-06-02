"""Classes and functions related to DPA pipeline product subscription."""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import os.path

from dpa.ptask.version import PTaskVersion
from dpa.product.version import ProductVersion
from dpa.ptask.spec import PTaskSpec
from dpa.ptask.area import PTaskArea
from dpa.restful import RestfulObject, RestfulObjectError
from dpa.restful.mixins import (
    CreateMixin, GetMixin, ListMixin, UpdateMixin, DeleteMixin,
)

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class ProductSubscription(CreateMixin, GetMixin, ListMixin, UpdateMixin,
    DeleteMixin, RestfulObject):
    """Product Subscription API.

    .id
    .locked
    .product_version
    .product_version_spec
    .ptask_version
    .ptask_version_spec
    .spec
    
    """
    
    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'product-subscriptions'

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, ptask_version, product_version):

        if isinstance(ptask_version, PTaskVersion):
            ptask_version = ptask_version.spec            

        if isinstance(product_version, ProductVersion):
            product_version = product_version.spec            

        # XXX validation

        data = {
            "ptask_version": ptask_version,
            "product_version": product_version,
        }

        return super(ProductSubscription, cls).create(data)

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, product_version_spec, ptask_version_spec, relative_to=None):

        # XXX PTaskSpec >> ContextSpec
        # XXX PTaskArea >> ContextArea
        # XXX PTaskEnv  >> ContextEnv
        if not isinstance(ptask_version_spec, PTaskSpec):
            ptask_version_spec = PTaskSpec.get(
                ptask_version_spec, relative_to=relative_to)

        if not isinstance(product_version_spec, PTaskSpec):
            product_version_spec = PTaskSpec.get(
                product_version_spec, relative_to=relative_to)

        spec = ",".join([product_version_spec, ptask_version_spec])

        return super(ProductSubscription, cls).get(spec)

    # -------------------------------------------------------------------------
    @classmethod
    def delete(cls, ptask_version_spec, product_version_spec, relative_to=None):

        sub = cls.get(
            ptask_version_spec, product_version_spec, relative_to=relative_to)

        return super(ProductSubscription, cls).delete(sub.spec)

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
    def lock(self):
        return super(ProductSubscription, self).update(
            self.spec, {"locked": True})

    # -------------------------------------------------------------------------
    def unlock(self):
        return super(ProductSubscription, self).update(
            self.spec, {"locked": False})

    # -------------------------------------------------------------------------
    def import_path(self, app='global'):
        product = self.product_version.product
        area = PTaskArea(self.ptask_version.ptask.spec)
        import_dir = area.dir(dir_name="import", verify=False, path=True)

        path = os.path.join(import_dir, app, product.name, product.category)
        
        if not os.path.exists(path):
            raise ProductSubscriptionError("Import path does not exist.")

        return path

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def product_version(self):
        return ProductVersion.get(self.product_version_spec)

    # -------------------------------------------------------------------------
    @property
    def product_version_spec(self):
        return self._data.get('product_version')

    # -------------------------------------------------------------------------
    @property
    def ptask_version(self):
        return PTaskVersion.get(self.ptask_version_spec)

    # -------------------------------------------------------------------------
    @property
    def ptask_version_spec(self):
        return self._data.get('ptask_version')

# -----------------------------------------------------------------------------
class ProductSubscriptionError(RestfulObjectError):
    pass

ProductSubscription.exception_class = ProductSubscriptionError

