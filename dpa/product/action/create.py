
# -----------------------------------------------------------------------------

import os

from dpa.action import Action, ActionError, ActionAborted
from dpa.location import current_location_code
from dpa.product import Product, ProductError, validate_product_name
from dpa.product.version import ProductVersion, ProductVersionError
from dpa.product.representation import (
    ProductRepresentation,
    ProductRepresentationError,
)
from dpa.product.representation.status import (
    ProductRepresentationStatus,
    ProductRepresentationStatusError,
)
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask.cli import ParsePTaskSpecArg
from dpa.ptask.spec import PTaskSpec
from dpa.shell.output import Output, Style
from dpa.sync.action import SyncAction
from dpa.user import current_username

# -----------------------------------------------------------------------------
class ProductCreateAction(Action):
    """Create a new product."""

    name = "create"
    target_type = "product"

    # -------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):

        # product name
        parser.add_argument(
            "product",
            help="The spec representing the ptask to create.",
        )

        # ptask spec
        parser.add_argument(
            "ptask",
            action=ParsePTaskSpecArg,
            nargs="?",
            help="The ptask creating the product.",
        )

        parser.add_argument(
            "-c", "--category",
            default=None,
            help="The category of product to create.",
        )

        # description
        parser.add_argument(
            "-d", "--description", 
            default=None,
            help="A description of the ptask being created.",
        )

        parser.add_argument(
            "-r", "--resolution", 
            default=None,
            help="The resolution of the product being created.",
        )

        parser.add_argument(
            "-t", "--type",
            dest="file_type",
            default=None,
            help="The file type for this product.",
        )

        parser.add_argument(
            "-p", "--path",
            default=None,
            help="Path to existing file/dir for this product.",
        )
                            
        parser.add_argument(
            "-v", "--version",
            type=int,
            default=None,
            help="Version of the product to create.",
        )
                                
        parser.add_argument(
            "-n", "--note",
            default=None,
            help="Release note for this particular version.",
        )

    # -------------------------------------------------------------------------
    def __init__(self, product, ptask, category=None, description=None,
        resolution=None, file_type=None, path=None, version=None, note=None):

        super(ProductCreateAction, self).__init__(
            product,
            ptask,
            category=category,
            description=description,
            resolution=resolution,
            file_type=file_type,
            path=path,
            version=version,
            note=note,
        )

        self._product = product
        self._ptask = ptask
        self._category = category
        self._description = description
        self._resolution = resolution
        self._file_type = file_type
        self._path = path
        self._version = version
        self._note = note

        if self._path:
            if not os.path.exists(self._path):
                raise ActionError("Supplied path does not exist.")
            file_type = os.path.splitext(self._path)[1].lstrip(".")
            if self._file_type and self._file_type != file_type:
                raise ActionError(
                    "Different file types specified: {t1} & {t2}".format(
                        t1=self._file_type, t2=file_type))
            else:
                self._file_type = file_type

        self._parse_product()
    
    # -------------------------------------------------------------------------
    def execute(self):

        # create the product
        self._create_product()
        self._create_version()
        self._create_representation()
        self._create_status() 
        self._create_area()
        self._sync_path()

        if self.interactive:
            print "\nProduct created successfully.\n"
       
    # -------------------------------------------------------------------------
    def prompt(self):

        print ""

        product_display = " [{b}{p}{r}]".format(
            b=Style.bright,
            p=self._product,
            r=Style.reset,
        )

        # category menu
        if not self._category:
            self._category = Output.prompt_menu(
                "Product categories",
                "{pd} category".format(pd=product_display),
                zip(*[Product.category_names()] * 2),
            )
       
        # description
        if not self._description:
            self._description = Output.prompt(
                '{pd} description'.format(pd=product_display),
                blank=False,
            )
        
        # file type
        if not self._file_type:
            if not self._file_type:
                self._file_type = Output.prompt(
                    "{pd} file type".format(pd=product_display),
                    blank=False,
                )

        # resolution
        if not self._resolution:
            self._resolution = Output.prompt(
                "{pd} resolution (Return if none)".format(pd=product_display),
                blank=True,
            )
            if not self._resolution:
                self._resolution = 'none'

    # -------------------------------------------------------------------------
    def undo(self):

        if hasattr(self, '_product') and isinstance(self._product, Product):
            self.logger.warning("Cannot undo attempted product creation. " + \
                "See pipeline admin for help cleaning up unwanted products.")

    # -------------------------------------------------------------------------
    def validate(self):

        if self.interactive:
            print "\nValidating product arguments ..."

        # should have a valid product name, 
        self._name = validate_product_name(self._name)

        if self._category:
            if not self._category in Product.category_names():
                raise ActionError("Unrecognized category.")
        else:
            raise ActionError("Category is required.")

        if not self._description:
            raise ActionError("Description is required.")

        # ptask
        if not isinstance(self._ptask, PTask):
            try:
                self._ptask = PTask.get(self._ptask)
            except PTaskError:
                raise ActionError("Could not determine ptask.")
                
        if self._version:
            self._ptask_version = self._ptask.version(self._version)
        else:
            self._ptask_version = self._ptask.latest_version

        if not self._ptask_version:
            raise ActionError("Could not determine ptask version.")

        if not self._note:
            self._note = "None"

        if self._path:
            if not os.path.exists(self._path):
                raise ActionError("Supplied path does not exist.")
            if (os.path.isdir(self._path) and 
                not self._path.endswith(os.path.sep)):
                self._path += os.path.sep

    # -------------------------------------------------------------------------
    def verify(self):

        name = "Name"
        category = "Category"
        description = "Description"
        file_type = "File type"
        resolution = "Resolution"
        ptask_ver = "PTask version"
        path = "Path"
        note = "Note"

        output = Output()
        output.header_names = [
            name,
            category,
            description,
            file_type,
            resolution,
            ptask_ver,
            path,
            note,
        ]

        output.add_item(
            {
                name: self._name,
                category: self._category,
                description: self._description,
                file_type: self._file_type,
                resolution: self._resolution,
                ptask_ver: self._ptask_version.spec,
                path: self._path,
                note: self._note,
            },
            color_all=Style.bright,
        )

        output.title = "Confirm create:"
        output.dump()

        if not Output.prompt_yes_no(Style.bright + "Create" + Style.reset):
            raise ActionAborted("User chose not to proceed.")

    # -------------------------------------------------------------------------
    @property
    def name(self):
        return self._name

    # -------------------------------------------------------------------------
    @property
    def product(self):
        return self._product

    # -------------------------------------------------------------------------
    @property
    def product_area(self):
        return self._product_area

    # -------------------------------------------------------------------------
    @property
    def product_version(self):
        return self._product_version

    # -------------------------------------------------------------------------
    @property
    def product_repr(self):
        return self._product_repr

    # -------------------------------------------------------------------------
    @property
    def product_repr_status(self):
        return self._product_repr_status

    # -------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

    # -------------------------------------------------------------------------
    @property
    def ptask_version(self):
        return self._ptask_version

    # -------------------------------------------------------------------------
    @property
    def category(self):
        return self._category

    # -------------------------------------------------------------------------
    @property
    def description(self):
        return self._description

    # -------------------------------------------------------------------------
    @property
    def resolution(self):
        return self._resolution

    # -------------------------------------------------------------------------
    @property
    def file_type(self):
        return self._file_type

    # -------------------------------------------------------------------------
    @property
    def path(self):
        return self._path

    # -------------------------------------------------------------------------
    @property
    def version(self):
        return self._version

    # -------------------------------------------------------------------------
    @property
    def note(self):
        return self._note

    # -------------------------------------------------------------------------
    def _create_product(self):

        existing = Product.list(
            name=self._name,
            category=self._category,
            ptask=self._ptask.spec,
        )
        
        if len(existing) == 1:
            self._product = existing.pop()
            self._product.update(description=self._description)
            if self.interactive:
                print "\nBase product exists: " + \
                    Style.bright + self._product.spec + Style.reset
        else:
            try:
                self._product = Product.create(
                    ptask=self._ptask.spec,
                    name=self._name,
                    category=self._category,
                    description=self._description,
                    creator=current_username(),
                )
            except ProductError as e:
                raise ActionError("Unable to create product: " + str(e))
            else:
                if self.interactive:
                    print "\nCreated base product: " + \
                        Style.bright + self._product.spec + Style.reset

    # -------------------------------------------------------------------------
    def _create_version(self):

        existing = ProductVersion.list(
            ptask_version=self._ptask_version.spec,
            product=self._product.spec,
        )

        if len(existing) == 1:
            self._product_version = existing.pop()
            self._product_version.update(release_note=self._note)
            if self.interactive:
                print "\nProduct version exists: " + \
                    Style.bright + self._product_version.spec + Style.reset
        else:
            try:
                self._product_version = ProductVersion.create(
                    ptask_version=self._ptask_version.spec,
                    product=self._product.spec,
                    release_note=self._note,
                    creator=current_username(),
                )
            except ProductVersionError as e:
                raise ActionError("Unable to create product version: " + str(e))
            else:
                if self.interactive:
                    print "\nCreated product version: " + \
                        Style.bright + self._product_version.spec + Style.reset

    # -------------------------------------------------------------------------
    def _create_representation(self):

        existing = ProductRepresentation.list(
            product_version=self._product_version.spec,
            resolution=self._resolution,
            representation_type=self._file_type,
        )

        if len(existing) == 1:
            self._product_repr = existing.pop()
            if self.interactive:
                print "\nProduct representation exists: " + \
                    Style.bright + self._product_repr.spec + Style.reset
        else:
            try:
                self._product_repr = ProductRepresentation.create(
                     product_version=self._product_version.spec,
                     resolution=self._resolution,
                     representation_type=self._file_type,
                     creation_location=current_location_code(),
                     creator=current_username(),
                )
            except ProductRepresentationError as e:
                raise ActionError(
                    "Unable to create product representation: " + str(e))
            else:
                if self.interactive:
                    print "\nCreated product representation: " + \
                        Style.bright + self._product_repr.spec + Style.reset
    
    # -------------------------------------------------------------------------
    def _create_status(self):
        
        existing = ProductRepresentationStatus.list(
            product_representation=self._product_repr.spec,
            location=current_location_code(),
        )

        if len(existing) == 1:
            self._product_repr_status = existing.pop()
            if self.interactive:
                print "\nProduct representation status exists: " + \
                    Style.bright + self._product_repr_status.spec + Style.reset
        else:
            try:
                self._product_repr_status = ProductRepresentationStatus.create(
                    product_representation=self._product_repr.spec,
                    location=current_location_code(),
                    status=1,
                )
            except ProductRepresentationStatusError as e:
                raise ActionError(
                    "Unable to create product representation status: " + str(e))
            else:
                if self.interactive:
                    print "\nCreated product representation status: " + \
                        Style.bright + self._product_repr_status.spec + \
                        Style.reset

    # -------------------------------------------------------------------------
    def _create_area(self):
        
        try:
            self._product_area = PTaskArea.create(self.product_repr)
        except PTaskAreaError as e:
            raise ActionError(
                "Unable to create product area on disk: " + str(e))

    # -------------------------------------------------------------------------
    def _parse_product(self):

        # split the supplied product string to determine additional parts. 
        # this sets unknown values to None
        (name, cat, ver, file_type, res) = list(
            self._product.split(PTaskSpec.SEPARATOR, 5) + [None] * 5
        )[0:5]

        # name
        self._name = name

        # category
        if cat:
            if self._category and self._category != cat:
                raise ActionError(
                    "Different categories specified: {c1} & {c2}".format(
                        c1=self._category, c2=cat))
            self._category = cat

        # version 
        if ver:
            try:
                ver = int(ver)
            except ValueError:
                raise ActionError("Invalid version specified.")

            if self._version and self._version != ver:
                raise ActionError(
                    "Different versions specified: {v1} & {v2}".format(
                        v1=self._version, v2=ver))
            self._version = ver

        # file_type
        if file_type:
            if self._file_type and self._file_type != file_type:
                raise ActionError(
                    "Different file types specified: {t1} & {t2}".format(
                        t1=self._file_type, t2=file_type))
            self._file_type = file_type

        # resolution
        if res: 
            if self._resolution and self._resolution != res:
                raise ActionError(
                    "Different resolutions specified: {r1} & {r2}".format(
                        r1=self._resolution, c2=res))
            self._resolution = res

    # -------------------------------------------------------------------------
    def _sync_path(self):

        if self._product_version.published:
            raise ActionError(
                "Product version is already published at this version. Can " + \
                "not overwrite: " + self._product_version.spec)
        
        if not self._path:
            return

        sync = SyncAction(
            source=self._path,
            destination=self._product_area.path,
        )

        try:
            sync()
        except ActionError as e:
            raise ActionError("Failed to sync product source: " + str(e))

