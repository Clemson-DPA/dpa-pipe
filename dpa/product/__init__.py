
"""Classes and functions related to DPA pipeline products."""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

from dateutil import parser as date_parser
import re

from dpa.location import Location
from dpa.ptask import PTask
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec
from dpa.restful import RestfulObject, RestfulObjectError
from dpa.restful.mixins import CreateMixin, GetMixin, ListMixin, UpdateMixin
from dpa.user import User

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class Product(CreateMixin, GetMixin, ListMixin, UpdateMixin, RestfulObject):
    """Product API.
    
        .category
        .created
        .creator
        .description
        .id
        .name
        .official_version_number
        .ptask
        .spec
    
    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    data_type = 'products'

    # -------------------------------------------------------------------------
    # Class Methods
    # -------------------------------------------------------------------------
    @classmethod
    def category_names(cls):
        if not hasattr(cls, '_category_names'):
            from dpa.product.category import ProductCategory
            cls._category_names = [c.name for c in ProductCategory.list()]
        return cls._category_names

    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, ptask, name, category, description=None, creator=None):

        # XXX validation

        data = {
            "ptask": ptask,
            "name": name,
            "category": category,
            "description": description,
            "creator": creator,
        }

        return super(Product, cls).create(data)

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, spec, relative_to=None):

        # convenience that allows calling code to not have to type check 
        # input that allows either spec or ptask 
        if isinstance(spec, Product):
            return spec

        # XXX PTaskSpec >> ContextSpec
        # XXX PTaskArea >> ContextArea
        # XXX PTaskEnv  >> ContextEnv
        if not isinstance(spec, PTaskSpec):
            spec = PTaskSpec.get(spec, relative_to=relative_to)

        return super(Product, cls).get(spec)

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
    def update(self, description=None):
    

        data = {
            "description": description,
        }

        return super(Product, self).update(self.spec, data)

    # -------------------------------------------------------------------------
    def set_official(self, product_version):

        return super(Product, self).update(self.spec, 
            {"official_version_number": product_version.number})

    # -------------------------------------------------------------------------
    def clear_official(self):

        return super(Product, self).update(
            self.spec, {"official_version_number": 0})

    # -------------------------------------------------------------------------
    def latest_published(self, deprecated=False):
        """Returns the latest published version of the product.

        If deprecated is True, allow for the latest version to be deprecated.
        If False, returns the latest non-deprecated version. Default is False.
        """

        from dpa.product.version import ProductVersion
        versions = ProductVersion.list(
            product=self.spec,
            published=True,
        )

        if not deprecated:
            versions = [v for v in versions if not v.deprecated]

        if len(versions) == 0:
            return None
        elif len(versions) == 1:
            return versions[0]
        else:
            # sort by version number, return the last one
            versions.sort(key=lambda v:v.number)
            return versions[-1]

    # -------------------------------------------------------------------------
    def version(self, version_number):

        from dpa.product.version import ProductVersion
        try:
            versions = ProductVersion.list(
                product=self.spec,
                number=int(version_number),
            )
        except:
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
        """:returns: PTaskArea for this product."""
        if not hasattr(self, '_area'):
            self._area = PTaskArea(self.spec)

        return self._area

    # -------------------------------------------------------------------------
    @property
    def created(self):
        """:returns: a datetime object for the creation of this product."""
        return date_parser.parse(self._data.get('created'))

    # -------------------------------------------------------------------------
    @property
    def creator(self):
        """:returns: a User object for the creator of this product."""
        return User.get(self.creator_username)

    # -------------------------------------------------------------------------
    @property
    def creator_username(self):
        """:returns: username str for the creator of this product."""
        return self._data.get("creator")

    # -------------------------------------------------------------------------
    @property
    def dependent_ptasks(self):
        """:returns: list of ptasks with subs to a version of this product."""

        from dpa.product.subscription import ProductSubscription

        ptasks = []

        # XXX db heavy. see about reducing number of queries here
        subs = ProductSubscription.list(search=self.spec)
        for sub in subs:
            ptasks.append(sub.ptask_version.ptask) 

        return ptasks

    # -------------------------------------------------------------------------
    @property
    def name_spec(self):
        return PTaskSpec.SEPARATOR.join([self.name, self.category])

    # -------------------------------------------------------------------------
    @property
    def official_version(self):
        num = self.official_version_number
        if num < 1:
            return None
        else:
            return self.version(num)

    # -------------------------------------------------------------------------
    @property
    def official_version_number_padded(self):
        return str(self._data.get("official_version_number")).zfill(4)

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        return PTask.get(self.ptask_spec)
        
    # -------------------------------------------------------------------------
    @property
    def ptask_spec(self):
        return self._data.get('ptask')

    # -------------------------------------------------------------------------
    @property
    def spec(self):
        """:returns: PTaskSpec object representing this product's spec."""
        return PTaskSpec.get(self._data.get('spec'))

    # -------------------------------------------------------------------------
    @property
    def version_specs(self):
        return self._data.get('versions')

    # -------------------------------------------------------------------------
    @property
    def versions(self):
        from dpa.product.version import ProductVersion
        return ProductVersion.list(product=self.spec)
        
# -----------------------------------------------------------------------------
class ProductError(RestfulObjectError):
    pass

Product.exception_class = ProductError

# -----------------------------------------------------------------------------
def validate_product_name(name):

    # starts with a letter
    if not re.match("^[a-zA-Z]", name):
        raise ProductError("Product name must begin with a letter.")

    # only contains letter, underscore, digits
    if not re.match("^\w+$", name):
        raise ProductError(
            "Product name can only contain alpha numeric characters."
        )

    # must be at least 3 characters long
    if len(name) < 3:
        raise ProductError(
            "Product name must be at least 3 characters long."
        )

    return name

