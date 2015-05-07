
from maya import cmds, mel

from dpa.ui.icon.factory import IconFactory

# -----------------------------------------------------------------------------
class MayaShelf(object):

    # -------------------------------------------------------------------------
    @staticmethod
    def top_level_layout():
        return mel.eval("$tmp=$gShelfTopLevel")

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, layout=None):
        
        if not layout:
            layout = cls.top_level_layout()

        cmds.setParent(layout)
        shelf = cmds.shelfLayout(name, q=True, exists=True)

        if shelf:
            return cls(name, layout)
        else:
            raise NameError("Unable to find shelf: " + name)

    # -------------------------------------------------------------------------
    def __init__(self, name, layout=None):
        self._name = name

        if not layout:
            layout = self.__class__.top_level_layout()
        self._layout = layout

    # -------------------------------------------------------------------------
    def add_button(self, **kwargs):

        import sys

        # intercept/adjust some of the arguments
        for (key, val) in kwargs.iteritems():

            # get full image path
            if key.startswith("image") and IconFactory.is_icon_path(val):
                kwargs[key] = self.icon_factory.disk_path(val)

        cmds.setParent("|".join([self.layout, self.name]))
        cmds.shelfButton(**kwargs)

    # -------------------------------------------------------------------------
    def create(self):
        cmds.setParent(self.layout)
        cmds.shelfLayout(self.name)
        self._shelf_error_fix()

    # -------------------------------------------------------------------------
    def delete(self):
        cmds.deleteUI("|".join([self.layout, self.name]))
        self._shelf_error_fix()

    # -------------------------------------------------------------------------
    @property
    def exists(self):
        cmds.setParent(self.layout)
        return cmds.shelfLayout(self.name, q=True, exists=True)

    # -------------------------------------------------------------------------
    @property
    def icon_factory(self):
        
        if not hasattr(self, '_icon_factory'):
            self._icon_factory = IconFactory()

        return self._icon_factory

    # -------------------------------------------------------------------------
    @property
    def layout(self):
        return self._layout

    # -------------------------------------------------------------------------
    @property
    def name(self):
        return self._name

    # -------------------------------------------------------------------------
    def _shelf_error_fix(self):

        # FIXES error in shelf.mel. reassigns optionVars for this shelf 
        shelves = cmds.shelfTabLayout(
            self.layout, query=True, tabLabelIndex=True)
        for index, shelf in enumerate(shelves):
            if shelf == self.name:
                cmds.optionVar(
                    stringValue=("shelfName{i}".format(i=index+1), str(shelf))
                )

