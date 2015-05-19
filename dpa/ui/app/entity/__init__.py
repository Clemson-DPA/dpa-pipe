
from PySide import QtCore, QtGui

# -----------------------------------------------------------------------------
class EntityTreeWidget(QtGui.QTreeWidget):

    # -------------------------------------------------------------------------
    def __init__(self, entities=None, parent=None):

        self._category_items = dict()
        self._entity_items = []

        super(EntityTreeWidget, self).__init__(parent=parent)

        self.setAllColumnsShowFocus(True)
        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        self.setHeaderLabels(['Entity'])
        self.setRootIsDecorated(False)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        if entities:
            self.add_entities(entities)

    # -------------------------------------------------------------------------
    def add_category(self, category):

        category_item = QtGui.QTreeWidgetItem([category])
        category_item.setFlags(QtCore.Qt.ItemIsEnabled)
        self.addTopLevelItem(category_item)
        category_item.setExpanded(True)
        self._category_items[category] = category_item

    # -------------------------------------------------------------------------
    def add_entities(self, entities):

        for entity in entities:
            self.add_entity(entity)

    # -------------------------------------------------------------------------
    def add_entity(self, entity):

        if not entity.category in self._category_items.keys():
            self.add_category(entity.category)

        category_item = self._category_items[entity.category]

        entity_item = EntityTreeWidgetItem(entity)
        category_item.addChild(entity_item)

        self.entity_items.append(entity_item)

    # -------------------------------------------------------------------------
    def select_all_entities(self):
        
        for entity_item in self.entity_items:
            entity_item.setSelected(True)

    # -------------------------------------------------------------------------
    def selected_entities(self):
        
        entities = []
        for entity_item in self.entity_items:
            if entity_item.isSelected():
                entities.append(entity_item.entity)

        return entities

    # -------------------------------------------------------------------------
    @property
    def entity_items(self):
        return self._entity_items

# -----------------------------------------------------------------------------
class EntityTreeWidgetItem(QtGui.QTreeWidgetItem):
    
    # -------------------------------------------------------------------------
    def __init__(self, entity):

        self._entity = entity

        super(EntityTreeWidgetItem, self).__init__([entity.display_name])
        self.setFlags(QtCore.Qt.ItemIsSelectable| QtCore.Qt.ItemIsEnabled)

    # -------------------------------------------------------------------------
    @property
    def entity(self):
        return self._entity

