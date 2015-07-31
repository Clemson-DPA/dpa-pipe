
from collections import defaultdict
import os

from dpa.action import Action, ActionError
from dpa.product import Product
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec
from dpa.shell.output import Output, Style

# -----------------------------------------------------------------------------
class ProductionStats(object):

    def __init__(self):

        self.ptasks = defaultdict(int)
        self.ptask_versions = defaultdict(int)
        self.ptask_products = defaultdict(int)
        self.ptask_product_versions = defaultdict(int)
        self.ptask_subscriptions = defaultdict(int)
        self.products = defaultdict(int)
        self.product_versions = defaultdict(int)
        self.product_representations = defaultdict(int)
        self.product_repr_files = defaultdict(int)
        self.product_repr_files_by_type = defaultdict(int)
     
# -----------------------------------------------------------------------------
class ProductionStatsAction(Action):
    
    name = "info"
    target_type = "stats"

    # -----------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):
        
        parser.add_argument(
            "ptask", 
            nargs="?", 
            default=".",
            help="Print info for this ptask spec. First checks relative to " + \
                 "the currently set ptask. If no match is found, checks " + \
                 "relative to the project root.",
        )

    # -----------------------------------------------------------------------------
    def __init__(self, ptask):
        super(ProductionStatsAction, self).__init__(ptask)
        self._ptask = ptask

    # -----------------------------------------------------------------------------
    def execute(self):

        self._data = ProductionStats()
        self._process_ptask(self.ptask)
        self._print_ptask_stats()
        self._print_product_stats()

    # -----------------------------------------------------------------------------
    def _process_ptask(self, ptask):

        print " PTASK: " + ptask.spec + " ..."

        ptask_type = ptask.type

        self._data.ptasks[ptask_type] += 1

        for ptask_ver in ptask.versions:

            #if ptask_ver.number > 2: continue  # speed up testing XXX

            print "  VER: " + ptask_ver.spec

            self._data.ptask_versions[ptask_type] += 1
            
            for sub in ptask_ver.subscriptions:

                print "   SUB: " + sub.product_version_spec

                sub_product = sub.product_version.product
                self._data.ptask_subscriptions[ptask_type] += 1 

        for product in Product.list(ptask=ptask.spec):

            print "  PRODUCT: " + product.name_spec

            category = product.category
            self._data.ptask_products[ptask_type] += 1
            self._data.products[category] += 1

            for product_ver in product.versions:

                print "   PRODUCT VER: " + product_ver.spec

                self._data.ptask_product_versions[ptask_type] += 1
                self._data.product_versions[category] += 1
        
                for product_repr in product_ver.representations:

                    print "    PRODUCT REPR: " + product_repr.spec
                    
                    file_type = product_repr.type
                    self._data.product_representations[category] += 1

                    if os.path.exists(product_repr.area.path):
                        for file_name in os.listdir(product_repr.area.path):
                            if file_name.endswith(file_type):
                                print "          FILE: " + file_name
                                self._data.product_repr_files[category] += 1
                                self._data.product_repr_files_by_type[file_type] += 1

        # recursively iterate over all children
        for child_ptask in ptask.children:
            self._process_ptask(child_ptask)

    # -------------------------------------------------------------------------
    def _print_ptask_stats(self):

        total_ptasks = 0
        total_vers = 0
        total_subs = 0
        total_products = 0
        total_product_vers = 0

        type_name = "Type"
        type_total = "Count"
        type_vers = "Versions"
        type_ver_avg = "Vers/PTask"
        type_products = "Products"
        type_prod_avg = "Prods/PTask"
        type_product_vers = "ProductVers"
        type_product_vers_avg1 = "ProductVer/PTaskVer"
        type_product_vers_avg2= "ProductVer/Product"
        type_subs = "Subs"
        type_subs_avg = "Subs/Ver"

        type_out = Output()
        type_out.title = "PTask Totals for : {pt} (by type)".format(
            pt=self._ptask.spec)

        type_out.header_names = [
            type_name,
            type_total,
            type_vers,
            type_ver_avg,
            type_products,
            type_prod_avg,
            type_product_vers,
            type_product_vers_avg1,
            type_product_vers_avg2,
            type_subs, 
            type_subs_avg
        ]

        type_out.set_header_alignment(
            {
                type_name: "right",
                type_total: "right",
                type_vers: "right",
                type_ver_avg: "right",
                type_products: "right",
                type_prod_avg: "right",
                type_product_vers: "right",
                type_product_vers_avg1: "right",
                type_product_vers_avg2: "right",
                type_subs: "right",
                type_subs_avg: "right",
            })

        for (ptask_type, ptask_type_count) in \
            sorted(self._data.ptasks.iteritems()):

            total_ptasks += ptask_type_count

            if ptask_type in self._data.ptask_versions:
                ver_count = self._data.ptask_versions[ptask_type]
                total_vers += ver_count
            else:
                ver_count = 0

            if ptask_type in self._data.ptask_products:
                product_count = self._data.ptask_products[ptask_type]
                total_products += product_count
            else:
                product_count = 0

            if ptask_type in self._data.ptask_product_versions:
                product_ver_count = self._data.ptask_product_versions[ptask_type]
                total_product_vers += product_ver_count
            else:
                product_ver_count = 0

            if ptask_type in self._data.ptask_subscriptions:
                subs_count = self._data.ptask_subscriptions[ptask_type]
                total_subs += subs_count
            else:
                subs_count = 0

            if ptask_type_count:
                type_ver_avg_val = \
                    '%.2f' % (ver_count / float(ptask_type_count))
                type_prod_avg_val = \
                    '%.2f' % (product_count / float(ptask_type_count))
            else:
                type_ver_avg_val = "?"
                type_prod_avg_val = "?"

            if ver_count:
                type_product_vers_avg1_val = \
                    "%.2f" % (product_ver_count / float(ver_count))
                type_subs_avg_val = \
                    '%.2f' % (subs_count / float(ver_count))
            else:
                type_product_vers_avg1_val = "?"
                type_subs_avg_val = "?"

            if product_count:
                type_product_vers_avg2_val = \
                    "%.2f" % (product_ver_count / float(product_count))
            else:
                type_product_vers_avg2_val = "?"

            type_out.add_item(
                {
                    type_name: ptask_type,
                    type_total: ptask_type_count,
                    type_vers: ver_count,
                    type_ver_avg: type_ver_avg_val,
                    type_products: product_count,
                    type_prod_avg: type_prod_avg_val,
                    type_product_vers: product_ver_count,
                    type_product_vers_avg1: type_product_vers_avg1_val, 
                    type_product_vers_avg2: type_product_vers_avg2_val,
                    type_subs: subs_count,
                    type_subs_avg: type_subs_avg_val,
                },
                color_all=Style.bright,
            )

        count = 'PTasks'
        versions = 'Versions'
        products = 'Products'
        product_vers = "ProductVers"
        subs = 'Subs'

        totals_out = Output()
        totals_out.title = "PTask Totals for : {pt}".format(pt=self._ptask.spec)
        totals_out.header_names = [
            count,
            versions,
            subs,
            products,
            product_vers,
        ]

        totals_out.set_header_alignment(
            {
                count: "right",
                versions: "right",
                products: "right",
                product_vers: "right",
                subs: "right",
            })
        totals_out.add_item(
            {
                count: total_ptasks,
                versions: total_vers,
                products: total_products,
                product_vers: total_product_vers,
                subs: total_subs,
            },
            color_all=Style.bright,
        )
        
        totals_out.dump(output_format='table')
        type_out.dump(output_format='table')

    # -------------------------------------------------------------------------
    def _print_product_stats(self):

        total_products = 0
        total_versions = 0
        total_reprs = 0
        total_files = 0

            # category
            # products
            # versions
            # representations
            # files

        cat_name = "Category"
        cat_products = "Products"
        cat_vers = "Versions"
        cat_reprs = "Representatiosn"
        cat_files = "Files"

        cat_out = Output()
        cat_out.title = "Product Totals for : {pt} (by category)".format(
            pt=self._ptask.spec)

        cat_out.header_names = [
            cat_name,
            cat_products,
            cat_vers,
            cat_reprs,
            cat_files,
        ]

        cat_out.set_header_alignment(
            {
                cat_name: "right",
                cat_products: "right",
                cat_vers: "right",
                cat_reprs: "right",
                cat_files: "right",
            })

        for (category, category_count) in sorted(self._data.products.iteritems()):

            total_products += category_count

            if category in self._data.product_versions:
                ver_count = self._data.product_versions[category]
                total_versions += ver_count
            else:
                ver_count = 0

            if category in self._data.product_representations:
                repr_count = self._data.product_representations[category]
                total_reprs += repr_count
            else:
                repr_count = 0

            if category in self._data.product_repr_files:
                file_count = self._data.product_repr_files[category] 
                total_files += file_count
            else:
                file_count = 0

            cat_out.add_item(
                {
                    cat_name: category,
                    cat_products: category_count,
                    cat_vers: ver_count,
                    cat_reprs: repr_count,
                    cat_files: file_count,
                },
                color_all=Style.bright,
            )
             
        count = 'Products'
        vers = 'Versions'
        reprs = 'Representations'
        files = 'Files'
        vers_product = "Vers/Product"
        reprs_version = "Reprs/Vers"
        files_repr = "Files/Repr"

        totals_out = Output()
        totals_out.title = "Product Totals for : {pt}".format(pt=self._ptask.spec)
        totals_out.header_names = [
            count,
            vers,
            reprs,
            files,
            vers_product,
            reprs_version,
            files_repr,
        ]

        totals_out.set_header_alignment(
            {
                count: "right",
                vers: "right",
                reprs: "right",
                files: "right",
                vers_product: "right",
                reprs_version: "right",
                files_repr: "right",
            }
        )

        if total_products:
            vers_product_val = \
                "%.2f" % (total_versions / float(total_products))
        else:
            vers_product_val = "?"

        if total_versions:
            reprs_version_val = \
                "%.2f" % (total_reprs / float(total_versions))
        else:
            reprs_version_val = "?"

        if total_reprs:
            files_repr_val = \
                "%.2f" % (total_files / float(total_reprs))
        else:
            files_repr_val = "?"

        totals_out.add_item(
            {
                count: total_products,
                vers: total_versions,
                reprs: total_reprs,
                files: total_files,
                vers_product: vers_product_val,
                reprs_version: reprs_version_val,
                files_repr: files_repr_val,
            },
            color_all=Style.bright,
        )
        
        totals_out.dump(output_format='table')

        file_type_hdr = 'Type'
        count = 'Count'

        types_out = Output()
        types_out.title = "Product Totals for : {pt} (by type)".format(
            pt=self._ptask.spec)

        types_out.header_names = [
            file_type_hdr,
            count,
        ]

        types_out.set_header_alignment(
            {
                file_type_hdr: "right",
                count: "right",
            }
        )

        for (file_type, file_type_count) in \
            sorted(self._data.product_repr_files_by_type.iteritems()):

            types_out.add_item(
                {
                    file_type_hdr: file_type,
                    count: file_type_count,
                },
                color_all=Style.bright,
            )

        cat_out.dump(output_format='table')
        types_out.dump(output_format='table')
        
    # -------------------------------------------------------------------------
    def undo(self):
        pass

    # -------------------------------------------------------------------------
    def validate(self):

        if not isinstance(self._ptask, PTask):
            try:
                cur_spec = PTaskArea.current().spec
                full_spec = PTaskSpec.get(self._ptask, relative_to=cur_spec)
                self._ptask = PTask.get(full_spec)
            except PTaskError:
                raise ActionError("Could not determine ptask from: {p}".format(
                    p=self._ptask))

    # ------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

