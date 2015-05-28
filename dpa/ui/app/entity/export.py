from collections import defaultdict

from PySide import QtCore, QtGui

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import EntityError
from dpa.app.session import SessionRegistry
from dpa.product import Product
from dpa.product.version import ProductVersion
from dpa.ui.app.entity import EntityTreeWidget
from dpa.ui.action.options import ActionOptionWidget
from dpa.ui.icon.factory import IconFactory

# -----------------------------------------------------------------------------
class EntityExportWizard(QtGui.QWizard):

    # -------------------------------------------------------------------------
    def __init__(self, session=None, parent=None):

        super(EntityExportWizard, self).__init__(parent=parent)

        self.setModal(True)

        if not session:
            session = SessionRegistry().current()

        self._session = session

        logo_pixmap = QtGui.QPixmap(
            IconFactory().disk_path("icon:///images/icons/export_32x32.png"))

        self.setWindowTitle("Entity Export")
        self.setPixmap(QtGui.QWizard.LogoPixmap, logo_pixmap)

        self._query_entities()

        selection_id = self.addPage(self.entity_selection_page)
        options_id = self.addPage(self.export_options_page)
        confirm_id = self.addPage(self.export_confirm_page)

        if len(self.exportable_entities) == 1:
            self.entity_widget.select_all_entities()
            self.setStartId(options_id)

        self.setOption(QtGui.QWizard.CancelButtonOnLeft, on=True)

        self.entity_widget.itemSelectionChanged.connect(self._toggle_options)

        self.setButtonText(QtGui.QWizard.FinishButton, 'Export')

        self.currentIdChanged.connect(self._check_descriptions)

        if not self.exportable_entities: 
            QtGui.QMessageBox.warning(self.parent(), "Export Warning",
                "<b>No entities available to Export</b>. If all entities " + \
                "have been published at this version already, you will " + \
                "need to <b>version up</b> before continuing."
            )
            self.NO_ENTITIES = True

    # -------------------------------------------------------------------------
    def accept(self):

        # XXX currently assuming exports are fast. exports could be time 
        # consuming. should probably do these in a separate thread or at 
        # least give the user some more feedback about what is happening.

        self.setEnabled(False)

        errors = []

        publish = self._publish_check.isChecked()
        version_up = self._version_check.isChecked()

        for entity in self.entity_widget.selected_entities():
            
            option_widget = self._options[entity]['widget']
            desc_edit = self._descriptions[entity]['widget']

            try:
                product_reprs = entity.export(
                    product_desc=desc_edit.text(),
                    version_note=self._note_edit.text(),
                    **option_widget.value
                )
            except EntityError as e:
                errors.append(e)
            else:
                # XXX should use product update action
                if publish:
                    for product_repr in product_reprs:
                        product_ver = product_repr.product_version
                        if not product_ver.published:
                            product_ver.publish()

        if version_up and not errors:
            version_action_cls = ActionRegistry().get_action('version', 'work')            
            if not version_action_cls:
                errors.append(
                    "Unable to version up. Could not location version action.")
            else:
                version_action = version_action_cls(
                    spec=self.session.ptask_area.spec,
                    description=self._note_edit.text(),
                )

                try:
                    version_action()
                except ActionError as e:
                    errors.append("Unable to version up: "  + str(e))

        if errors:
            error_dialog = QtGui.QErrorMessage(self)
            error_dialog.setWindowTitle("Export Errors")
            error_dialog.showMessage(
                "There were errors during export:<br><br>" + \
                "<br>".join([str(e) for e in errors])
            )

        super(EntityExportWizard, self).accept()

    # -------------------------------------------------------------------------
    def showEvent(self, event):
        super(EntityExportWizard, self).showEvent(event)
        self._toggle_options()

    # -------------------------------------------------------------------------
    def _query_entities(self):

        ptask_version = self.session.ptask_version
        published_products = ProductVersion.list(
            ptask_version=ptask_version.spec, published=True)

        product_lookup = defaultdict(dict)

        for product_ver in published_products:
            product = product_ver.product
            product_lookup[product.name][product.category] = product_ver

        self._exportable_entities = []
        self._published_entities = []

        all_entities = self.session.list_entities()
        for entity in all_entities:
            if not entity.exportable:
                continue

            entity_name = entity.display_name

            try:
                publish_match = product_lookup[entity_name][entity.category]
            except:
                self._exportable_entities.append(entity)
            else:
                self._published_entities.append(entity) 

    # -------------------------------------------------------------------------
    @property
    def exportable_entities(self):
        
        if not hasattr(self, '_exportable_entities'):
            return []

        return self._exportable_entities

    # -------------------------------------------------------------------------
    @property
    def published_entities(self):
        
        if not hasattr(self, '_published_entities'):
            return []

        return self._published_entities

    # -------------------------------------------------------------------------
    @property
    def session(self):
        return self._session

    # -------------------------------------------------------------------------
    @property
    def entity_selection_page(self):

        if hasattr(self, '_entity_selection_page'):
            return self._entity_selection_page

        page = QtGui.QWizardPage()
        page.setTitle("Selection")
        page.setSubTitle(
            "Select the entities you'd like to export to products.")

        self._entity_widget = EntityTreeWidget(self.exportable_entities)
        self._entity_widget.setFocusPolicy(QtCore.Qt.NoFocus)

        self._published_widget = EntityTreeWidget(self.published_entities)
        self._published_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self._published_widget.setFixedHeight(100)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Available for export :'))
        layout.addWidget(self._entity_widget)
        layout.addSpacing(5)
        layout.addWidget(QtGui.QLabel('Already published at this version :'))
        layout.addWidget(self._published_widget)

        page.setLayout(layout)

        self._entity_selection_page = page
        return self._entity_selection_page

    # -------------------------------------------------------------------------
    @property
    def entity_widget(self):

        if hasattr(self, '_entity_widget'):
            return self._entity_widget

        return None

    # -------------------------------------------------------------------------
    @property
    def export_options_page(self):

        if hasattr(self, '_export_options_page'):
            return self._export_options_page

        page = QtGui.QWizardPage()
        page.setTitle("Options")
        page.setSubTitle(
            "Set the options for the entities being exported.")

        self._options = defaultdict(dict)

        options_layout = QtGui.QVBoxLayout()

        for entity_item in self.entity_widget.entity_items:
            entity = entity_item.entity 

            option_config = entity.option_config('export')

            display_name = entity.display_name + "  (" + entity.category + ")"

            option_widget = ActionOptionWidget(option_config, 
                name=display_name)
            option_header = option_widget.header

            form_layout = QtGui.QFormLayout()
            form_layout.addRow(option_header)

            spacer = QtGui.QLabel()
            spacer.setFixedWidth(10)

            form_layout.addRow(option_widget)

            options_layout.addLayout(form_layout)

            h_rule = QtGui.QFrame()
            h_rule.setLineWidth(0)
            h_rule.setMidLineWidth(0)
            h_rule.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Plain)

            options_layout.addWidget(h_rule)

            self._options[entity]['widget'] = option_widget
            self._options[entity]['header'] = option_header

            option_widget.value_changed.connect(self._check_option_values)

        options_layout.addStretch()

        options_widget = QtGui.QWidget()
        options_widget.setLayout(options_layout)

        scroll_area = QtGui.QScrollArea()
        scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(options_widget)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(scroll_area)

        page.setLayout(layout)

        self._export_options_page = page
        return self._export_options_page

    # -------------------------------------------------------------------------
    @property
    def export_confirm_page(self):

        if hasattr(self, '_export_confirm_page'):
            return self._export_confirm_page

        self._descriptions = defaultdict(dict)

        ptask_version = self.session.ptask_version
        ptask = ptask_version.ptask

        layout = QtGui.QVBoxLayout()

        note_lbl = QtGui.QLabel(
            "Describe the work you did on the entities being exported:   (required)")
        self._note_edit = QtGui.QLineEdit()
        self._note_edit.setFocus()

        self._note_edit.textChanged.connect(
            lambda t: self._check_descriptions())

        layout.addWidget(note_lbl)
        layout.addWidget(self._note_edit)
        layout.addSpacing(5)

        products_layout = QtGui.QFormLayout()

        # get this ptask's products
        products = Product.list(ptask=ptask.spec)

        for entity_item in self.entity_widget.entity_items:

            entity = entity_item.entity

            existing_products = [p for p in products 
                if p.name == entity.display_name and 
                   p.category == entity.category]

            product_desc = QtGui.QLineEdit()
            if existing_products:
                product_desc.setText(existing_products[0].description)

            product_lbl = QtGui.QLabel("<b>{n}</b>".format(n=entity.product_name))
                
            products_layout.addRow(product_lbl, product_desc)

            self._descriptions[entity]['label'] = product_lbl
            self._descriptions[entity]['widget'] = product_desc

            product_desc.textChanged.connect(
                lambda t: self._check_descriptions())

        products_widget = QtGui.QWidget()
        products_widget.setLayout(products_layout)

        scroll_area = QtGui.QScrollArea()
        scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(products_widget)

        product_lbl = QtGui.QLabel(
            "Enter/update descriptions for the products:   (required)")
        product_lbl.setWordWrap(True)

        layout.addWidget(product_lbl)
        layout.addWidget(scroll_area)
        layout.addSpacing(5)

        self._publish_check = QtGui.QCheckBox("Publish all after Export")
        self._publish_check.setChecked(True)

        self._version_check = QtGui.QCheckBox("Version up after Publish")
        self._version_check.setChecked(True)
        
        # if publish gets toggled, update the version check accordingly
        self._publish_check.toggled.connect(
            lambda s: self._version_check.setEnabled(s) or 
                      self._version_check.setChecked(s)
        )

        layout.addWidget(self._publish_check)
        layout.addWidget(self._version_check)
        layout.addSpacing(5)

        confirm_lbl = QtGui.QLabel("<b>Export to {p} v{v}?</b>".\
            format(p=ptask.spec, v=ptask_version.number))
        confirm_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(confirm_lbl)

        self._export_confirm_page = QtGui.QWizardPage()
        self._export_confirm_page.setTitle("Confirm")
        self._export_confirm_page.setSubTitle(
            "Describe and confirm the folowing exports :")
        self._export_confirm_page.setLayout(layout)

        return self._export_confirm_page

    # -------------------------------------------------------------------------
    def _check_descriptions(self):

        finish_btn = self.button(QtGui.QWizard.FinishButton)

        if not str(self._note_edit.text()):        
            finish_btn.setEnabled(False)
            return

        for entity_item in self.entity_widget.entity_items:

            entity = entity_item.entity
            desc_edit = self._descriptions[entity]['widget']

            if not desc_edit.isVisible():
                continue

            if not str(desc_edit.text()):
                finish_btn.setEnabled(False)
                return
        
        finish_btn.setEnabled(True)

    # -------------------------------------------------------------------------
    def _check_option_values(self):

        next_btn = self.button(QtGui.QWizard.NextButton) 

        for entity_item in self.entity_widget.entity_items:

            entity = entity_item.entity
            option_widget = self._options[entity]['widget']

            if not option_widget.isVisible():
                continue

            if not option_widget.value_ok:
                next_btn.setEnabled(False)
                return
        
        next_btn.setEnabled(True)

    # -------------------------------------------------------------------------
    def _toggle_options(self):

        some_selected = False

        for entity_item in self.entity_widget.entity_items:

            entity = entity_item.entity

            option_header = self._options[entity]['header']
            option_widget = self._options[entity]['widget']

            desc_lbl = self._descriptions[entity]['label']
            desc_edit = self._descriptions[entity]['widget']

            if entity_item.isSelected():
                option_header.show() 
                option_widget.show() 
                desc_lbl.show() 
                desc_edit.show() 
                some_selected = True
            else:
                option_header.hide() 
                option_widget.hide() 
                desc_lbl.hide() 
                desc_edit.hide() 

        next_btn = self.button(QtGui.QWizard.NextButton) 
            
        if some_selected:
            next_btn.setEnabled(True) 
        else:
            next_btn.setEnabled(False)

