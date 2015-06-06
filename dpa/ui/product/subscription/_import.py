from collections import defaultdict

from PySide import QtCore, QtGui

from dpa.app.entity import EntityRegistry
from dpa.app.entity import EntityError
from dpa.app.session import SessionRegistry
from dpa.ui.action.options import ActionOptionWidget
from dpa.ui.icon.factory import IconFactory
from dpa.ui.product.subscription import SubscriptionTreeWidget

# list product representations for all subscriptions
# select representations
# show import options per representation
# options stored as category+file_type (maya/workfile_ma.cfg)

# -----------------------------------------------------------------------------
class SubscriptionImportWizard(QtGui.QWizard):

    # -------------------------------------------------------------------------
    def __init__(self, session=None, parent=None):

        super(SubscriptionImportWizard, self).__init__(parent=parent)

        self.setModal(True)

        if not session:
            session = SessionRegistry().current()

        self._session = session

        logo_pixmap = QtGui.QPixmap(
            IconFactory().disk_path("icon:///images/icons/import_32x32.png"))

        self.setWindowTitle("Subscription Import")
        self.setPixmap(QtGui.QWizard.LogoPixmap, logo_pixmap)

        # get entity classes
        entity_classes = EntityRegistry().get_entity_classes(
            self.session.app_name)

        # map entity category to class
        self._category_lookup = {cls.category: cls for cls in entity_classes}

        selection_id = self.addPage(self.sub_selection_page)
        options_id = self.addPage(self.import_options_page)

        self.setOption(QtGui.QWizard.CancelButtonOnLeft, on=True)
        self.setButtonText(QtGui.QWizard.FinishButton, 'Import')

        self._subs_widget.itemSelectionChanged.connect(self._toggle_options)

        if not self._subs_widget.repr_items: 
            QtGui.QMessageBox.warning(self.parent(), "Import Warning",
                "<b>No subs available to Import</b>."
            )
            self.NO_SUBS = True

    # -------------------------------------------------------------------------
    def accept(self):

        # XXX currently assuming imports are fast. imports could be time 
        # consuming. should probably do these in a separate thread or at 
        # least give the user some more feedback about what is happening.

        self.setEnabled(False)

        errors = []

        for repr_item in self._subs_widget.selected_repr_items():
            
            representation = repr_item.representation
            category = repr_item.product.category
            entity_class = self._category_lookup[category]

            option_widget = self._options[representation]['widget']

            try:
                entity = entity_class.import_product_representation(
                    self.session,
                    representation,
                    **option_widget.value
                )
            except EntityError as e:
                errors.append(e)

        if errors:
            error_dialog = QtGui.QErrorMessage(self)
            error_dialog.setWindowTitle("Import Errors")
            error_dialog.showMessage(
                "There were errors during import:<br><br>" + \
                "<br>".join([str(e) for e in errors])
            )

        super(SubscriptionImportWizard, self).accept()

    # -------------------------------------------------------------------------
    def showEvent(self, event):
        super(SubscriptionImportWizard, self).showEvent(event)
        self._toggle_options()

    # -------------------------------------------------------------------------
    @property
    def import_options_page(self):

        if hasattr(self, '_import_options_page'):
            return self._import_options_page

        page = QtGui.QWizardPage()
        page.setTitle("Options")
        page.setSubTitle(
            "Set the options for the subs being imported.")

        self._options = defaultdict(dict)

        options_layout = QtGui.QVBoxLayout()

        for repr_item in self._subs_widget.repr_items:
            representation = repr_item.representation

            entity_class = self._category_lookup[repr_item.product.category]
            option_config = entity_class.option_config(
                self.session, 'import', file_type=representation.type)

            display_name = repr_item.product.name
            if representation.resolution != "none":
                display_name += " @" + representation.resolution
            display_name += " (." + representation.type + " " + \
                repr_item.product.category + ")"

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

            self._options[representation]['widget'] = option_widget
            self._options[representation]['header'] = option_header

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

        self._import_options_page = page
        return self._import_options_page

    # -------------------------------------------------------------------------
    @property
    def sub_selection_page(self):

        if hasattr(self, '_sub_selection_page'):
            return self._sub_selection_page

        page = QtGui.QWizardPage()
        page.setTitle("Selection")
        page.setSubTitle(
            "Select the subs you'd like to import.")

        self._subs_widget = SubscriptionTreeWidget(self.subs, 
            show_categories=self._category_lookup.keys())
        self._subs_widget.setFocusPolicy(QtCore.Qt.NoFocus)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel('Available for import :'))
        layout.addWidget(self._subs_widget)

        page.setLayout(layout)

        self._sub_selection_page = page
        return self._sub_selection_page

    # -------------------------------------------------------------------------
    @property
    def session(self):
        return self._session

    # -------------------------------------------------------------------------
    @property
    def subs(self):

        if not hasattr(self, '_subs'):

            ptask_version = self.session.ptask_version
            self._subs = ptask_version.subscriptions

        return self._subs

    # -------------------------------------------------------------------------
    def _check_option_values(self):

        finish_btn = self.button(QtGui.QWizard.FinishButton)
        
        for repr_item in self._subs_widget.repr_items:

            representation = repr_item.representation
            option_widget = self._options[representation]['widget']

            if not option_widget.isVisible():
                continue

            if not option_widget.value_ok:
                finish_btn.setEnabled(False)
                return
        
        finish_btn.setEnabled(True)

    # -------------------------------------------------------------------------
    def _toggle_options(self):

        some_selected = False

        for repr_item in self._subs_widget.repr_items:

            representation = repr_item.representation

            option_header = self._options[representation]['header']
            option_widget = self._options[representation]['widget']

            if repr_item.isSelected():
                option_header.show() 
                option_widget.show() 
                some_selected = True
            else:
                option_header.hide() 
                option_widget.hide() 

        next_btn = self.button(QtGui.QWizard.NextButton)
        finish_btn = self.button(QtGui.QWizard.FinishButton)

        if some_selected:
            next_btn.setEnabled(True) 
            finish_btn.setEnabled(True) 
        else:
            next_btn.setEnabled(False)
            finish_btn.setEnabled(False)

