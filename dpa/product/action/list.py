
import re

from dpa.action import Action, ActionError
from dpa.shell.output import Output, Style
from dpa.product import Product, ProductError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec

# -----------------------------------------------------------------------------
class ProductListAction(Action):
    """List products matching a supplied wildcard spec string."""

    name = "list"
    target_type = "products"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        parser.add_argument(
            "wild_spec", 
            nargs="?", 
            default=".=%",
            help="List products matching this wildcard spec. (wildcard is %%)",
        )

    # -------------------------------------------------------------------------
    def __init__(self, wild_spec):
        super(ProductListAction, self).__init__(wild_spec)

        self._wild_spec = wild_spec

    # -------------------------------------------------------------------------
    def execute(self):

        products = _get_products(self.wild_spec)

        if len(products) == 0:
            print '\nFound 0 products matching: "{s}"\n'.\
                format(s=self.wild_spec)
            return

        name = "Name"
        category = "Category"
        description = "Description"
        official = "Official"
        spec = "Spec"

        output = Output()
        output.vertical_separator = None
        output.table_cell_separator = '  '
        output.table_header_separator = '-'
        output.header_names = [
            name,
            category,
            description,
            official,
            spec,
        ]

        output.set_header_alignment({
            official: "right" 
        })

        if len(products) == 1:
            output.title = "{s}: 1 match".format(s=self.wild_spec)
        else:
            output.title = "{s}: {n} matches".format(
                s=self.wild_spec, n=len(products))

        for product in sorted(products, key=lambda p: p.name + p.category + p.ptask_spec):
            output.add_item(
                {
                    name: product.name,
                    category: product.category,
                    description: product.description,
                    official: _official(product),
                    spec: product.spec,
                },
                colors={
                    spec: Style.bright,
                }
            )
            
        output.dump(output_format='table')

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    @property
    def wild_spec(self):
        return self._wild_spec

# -------------------------------------------------------------------------
def _get_products(wild_spec):

    ptask_spec = PTaskArea.current().spec
    full_spec = PTaskSpec.get(wild_spec, relative_to=ptask_spec)

    if PTaskSpec.WILDCARD in full_spec:

        search_str = ",".join(
            filter(None, full_spec.strip().split(PTaskSpec.WILDCARD))
        )

    # no wildcard, match all products under current location
    else:
        search_str = full_spec

    # XXX this is inefficient. need better filtering on the backend
    products = Product.list(search=search_str)

    matching_products = []

    # the rest api's search filter isn't that great. it doesn't maintain any
    # knowledge of order for the supplied filters. So, it will return products
    # that match all of the search terms, but not necessarily in the order
    # supplied. Do one more match against the returned products specs keeping
    # the order of the supplied wildcard spec. 

    regex_spec = "^" + \
        full_spec.replace(PTaskSpec.WILDCARD, "([\w=]+)?") + "$"

    regex_spec = re.compile(regex_spec)

    for product in products:
        if regex_spec.match(product.spec):
            matching_products.append(product)

    return matching_products

# -----------------------------------------------------------------------------
def _official(product):
    if product.official_version_number:
        return product.official_version_number_padded
    else:
        return 'None'
    
