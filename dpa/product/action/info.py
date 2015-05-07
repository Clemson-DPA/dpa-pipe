
# -----------------------------------------------------------------------------

from dpa.action import Action, ActionError
from dpa.shell.output import Output, Style, Fg, Bg
from dpa.product import Product, ProductError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec

# -----------------------------------------------------------------------------
class ProductInfoAction(Action):
    """Print information about a product."""

    name = "info"
    target_type = "product"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):
        
        parser.add_argument(
            "spec",
            nargs="?",
            default="",
            help="Print info for this product spec.",
        )

    # -------------------------------------------------------------------------
    def __init__(self, spec):
        super(ProductInfoAction, self).__init__(spec)
        self._spec = spec
    
    # -------------------------------------------------------------------------
    def execute(self):
        
        if not self.product:
            print "\nCould not determine product.\n"

        self._info_product()
        self._info_versions()

    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):

        cur_spec = PTaskArea.current().spec
        full_spec = PTaskSpec.get(self.spec, relative_to=cur_spec)

        if full_spec:
            try:
                product = Product.get(full_spec)
            except ProductError as e:
                # fall back to input spec
                try:
                    product = Product.get(self.spec)
                except ProductError:
                    raise ActionError(
                        'Could not determine product from: "{s}"'.format(
                            s=self.spec
                        )
                    )
        else:
            product = None

        self._product = product

    # -------------------------------------------------------------------------
    @property
    def spec(self):
        return self._spec

    # -------------------------------------------------------------------------
    @property
    def product(self):
        return self._product

    # -------------------------------------------------------------------------
    def _info_product(self):
    
        # fields:
        name = "Name"
        category = "Category"
        description = "Description"
        official = "Official"
        created = "Created"
        creator = "Creator"
        ptask = "PTask"

        output = Output()
        output.header_names = [
            name,
            category,
            description,
            official,
            created,
            creator,
            ptask,
        ]
        
        output.add_item(
            {
                name: self.product.name,
                category: self.product.category,
                description: self.product.description,
                official: self.product.official_version_number_padded \
                    if self.product.official_version_number != 0 else 'None',
                creator: self.product.creator_username,
                created: _datetime_format(self.product.created),
                ptask: self.product.ptask_spec,
            },
            color_all=Style.bright,
        )

        # build the title
        title = " {p.spec} ".format(p=self.product)
        output.title = title

        # dump the output as a list of key/value pairs
        output.dump()

    # -------------------------------------------------------------------------
    def _info_versions(self):

        self._versions = self.product.versions

        if len(self._versions) == 0:
            print "Found no versions for product!\n"
            return

        number = "Ver"
        published = "P"
        deprecated = "D"
        note = "Release note"
        reps = "Reps"
        creator = "Creator"
        created = "Created"

        output = Output()
        output.vertical_padding = 0
        output.vertical_separator = None
        output.table_header_separator="-"
        output.header_names = [
            published,
            number,
            note,
            reps,
            creator,
            created,
        ]

        output.set_header_alignment({
            number: "right",
            published: "right",
        })

        for version in sorted(self._versions, key=lambda v: v.number):

            is_official = version.number == self.product.official_version_number
            is_published = version.published
            is_deprecated = version.deprecated

            style = Style.dim
            if is_official or is_published:
                style = Style.normal

            output.add_item(
                {
                    number: version.number_padded,
                    note: version.release_note,
                    published: _published(is_published, is_official),
                    reps: _representations(version),
                    creator: version.creator_username,
                    created: _datetime_format(version.created),
                },
                colors={
                    published: _published_color(
                        is_published, is_official, is_deprecated),
                    number: _published_color(
                        is_published, is_official, is_deprecated),
                    note: style,
                    reps: style,
                    creator: style,
                    created: style,
                }
            )

        output.dump(output_format='table')

        print ""

# -----------------------------------------------------------------------------
def _datetime_format(datetime):
    return datetime.strftime("%Y/%m/%d %H:%M:%S")

# -----------------------------------------------------------------------------
def _published(value, official):

    if not value:
        return ""
    else:
        if official:
            indicator = ">>>"
        else:
            indicator = "*"

    return indicator

# -----------------------------------------------------------------------------
def _published_color(published, official, deprecated):
    
    if deprecated:
        return Fg.red + Style.dim
    elif official:
        return Fg.green + Style.bright
    elif published:
        return Fg.reset + Style.bright
    else:
        return Fg.reset + Style.dim

# -----------------------------------------------------------------------------
def _representations(version):

    reps = []
    for rep in version.representations:
        rep_str = rep.spec.replace(version.spec, "")
        reps.append(rep_str.lstrip("=").rstrip("=none"))
    
    return ",".join(reps)

