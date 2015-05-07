
from dpa.restful import RestfulObject, RestfulObjectError
from dpa.restful.mixins import ListMixin

# -----------------------------------------------------------------------------
class ProductCategory(ListMixin, RestfulObject):
    """Product Category API.

        .name
        .description

    """

    data_type = "product-categories"
    
    # -------------------------------------------------------------------------
    def __eq__(self, other):
        return self.name == other.name

    # -------------------------------------------------------------------------
    def __ne__(self, other):
        return self.name != other.name

    # -------------------------------------------------------------------------
    def __repr__(self):
        """:returns: Unique string represntation of the product."""
        return self.__class__.__name__ + "('" + self.name + "')"

    # -------------------------------------------------------------------------
    @property
    def name(self):
        return self._data.get('name')

    # -------------------------------------------------------------------------
    @property
    def description(self):
        return self._data.get('description')

# -----------------------------------------------------------------------------
class ProductCategoryError(RestfulObjectError):
    pass

ProductCategory.exception_class = ProductCategoryError

