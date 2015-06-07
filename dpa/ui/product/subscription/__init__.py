
from PySide import QtCore, QtGui

# -----------------------------------------------------------------------------
class SubscriptionTreeWidget(QtGui.QTreeWidget):

    # -------------------------------------------------------------------------
    def __init__(self, subscriptions, show_categories=None, parent=None):

        self._show_categories = show_categories
        self._category_items = dict()
        self._repr_items = []

        super(SubscriptionTreeWidget, self).__init__(parent=parent)

        self.setAllColumnsShowFocus(True)
        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        self.setHeaderLabels(['Subscriptions', 'Produced by'])
        self.setRootIsDecorated(False)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.add_subscriptions(subscriptions)

        for col in range(0, self.columnCount()):
            self.resizeColumnToContents(col)

    # -------------------------------------------------------------------------
    def add_category(self, category):

        category_item = QtGui.QTreeWidgetItem([category])
        category_item.setFlags(QtCore.Qt.ItemIsEnabled)
        self.addTopLevelItem(category_item)
        category_item.setExpanded(True)
        self._category_items[category] = category_item

    # -------------------------------------------------------------------------
    def add_subscriptions(self, subscriptions):

        for subscription in subscriptions:
            self.add_subscription(subscription)

    # -------------------------------------------------------------------------
    def add_subscription(self, subscription):

        for product_repr in subscription.product_version.representations:
            self.add_representation(product_repr)

    # -------------------------------------------------------------------------
    def add_representation(self, representation):

        repr_item = SubscriptionTreeWidgetItem(representation)
        category = repr_item.product.category

        if self.show_categories and category not in self.show_categories:
            return None

        if not category in self._category_items.keys():
            self.add_category(category)

        category_item = self._category_items[category]
        category_item.addChild(repr_item)
        self.repr_items.append(repr_item)

    # -------------------------------------------------------------------------
    def select_all_representations(self):
        
        for repr_item in self.repr_items:
            repr_item.setSelected(True)

    # -------------------------------------------------------------------------
    def selected_representations(self):
        
        reprs = []
        for repr_item in self.repr_items:
            if repr_item.isSelected():
                reprs.append(repr_item.representation)

        return reprs

    # -------------------------------------------------------------------------
    def selected_repr_items(self):
        
        repr_items = []
        for repr_item in self.repr_items:
            if repr_item.isSelected():
                repr_items.append(repr_item)

        return repr_items

    # -------------------------------------------------------------------------
    @property
    def repr_items(self):
        return self._repr_items

    # -------------------------------------------------------------------------
    @property
    def show_categories(self):
        if not self._show_categories:
            return []

        return self._show_categories

# -----------------------------------------------------------------------------
class SubscriptionTreeWidgetItem(QtGui.QTreeWidgetItem):
    
    # -------------------------------------------------------------------------
    def __init__(self, representation):

        self._representation = representation
        self._product_version = self._representation.product_version
        self._product = self._product_version.product

        display_name = self._product.name
        if representation.resolution != "none":
            display_name += " @" + representation.resolution
        display_name += " (" + representation.type + ")"

        super(SubscriptionTreeWidgetItem, self).__init__(
            [display_name, self._product.ptask_spec + ' v' + \
                self._product_version.number_padded])
        self.setFlags(QtCore.Qt.ItemIsSelectable| QtCore.Qt.ItemIsEnabled)

    # -------------------------------------------------------------------------
    @property
    def representation(self):
        return self._representation

    # -------------------------------------------------------------------------
    @property
    def product_version(self):
        return self._product_version

    # -------------------------------------------------------------------------
    @property
    def product(self):
        return self._product
    
