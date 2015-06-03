
from PySide import QtCore, QtGui

from dpa.action import ActionError
from dpa.app.entity import EntityRegistry
from dpa.ptask.area import PTaskArea
from dpa.ui.app.session import SessionActionDialog
from dpa.ui.icon.factory import IconFactory
        
# -----------------------------------------------------------------------------

IMPORT_ICON_URI = "icon:///images/icons/import_32x32.png"
IMPORT_OPTIONS_CONFIG = "config/mari/geom/import.cfg"

# -----------------------------------------------------------------------------
class ImportDialog(SessionActionDialog):
    
    # -------------------------------------------------------------------------
    def __init__(self):

        ptask_area = PTaskArea.current()
        options_config = ptask_area.config(IMPORT_OPTIONS_CONFIG,
            composite_ancestors=True)

        self.get_files()
        options_config.add('choices', self.sublist.keys())
        options_config.add('default', self.sublist.keys()[0])

        icon_path = IconFactory().disk_path(IMPORT_ICON_URI)

        super(FailDialog, self).__init__(
            title='Import Product',
            options_config=options_config,
            icon_path=icon_path,
            action_button_text='Import',
            modal=False,
        )

    # -------------------------------------------------------------------------
    def accept(self):

        # handles closing the dialog
        super(ImportDialog, self).accept()

        try:
            entity_classes = EntityRegistry.get_entity_classes(
                self.session.app_name)

            entity_class = None
            for ec in entity_classes:
                if ec.category == 'geom'
                    entity_class = ec
                    has_import_product = True
                else:
                    has_import_product = False

            if has_import_product:
                ec.import_product(self.sublist[**self.options.value][1],
                    self.sublist[**self.options.value][0])

        except ActionError as e:
            error_dialog = QtGui.QErrorMessage(self.parent())
            error_dialog.setWindowTitle('Import Product Failure')
            error_dialog.showMessage(
                "There was an error trying to import the product."
            )
            
    # -------------------------------------------------------------------------
    def get_files(self):
        sublist = defaultdict(dict)

        # for now, get only products available from existing subs with 
        # same category
        for sub in self.session.ptask_version.subscriptions:
            prod_ver = sub.product_version
            prod = prod_ver.product

            # this should change if geomentity ever becomes NOT just OBJ
            for sub_rep in prod_ver.representations:
                full_path = os.path.join(sub.import_path(),
                    sub_rep.type, sub_rep.resolution)
                # actual files wont always be named the same as the
                # product (eg, maps, so be wary of this)
                full_path += prod.name + '.' + sub_rep.type

                # still don't know if using the spec is the best option
                sublist[prod.spec] = [full_path, prod.name]

        self._sublist = sublist

    #  -------------------------------------------------------------------------
    @property
    def sublist(self):
        if not hasattr(self, '_sublist'):
            return defaultdict(dict)

        return self._sublist