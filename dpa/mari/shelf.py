
import mari

from dpa.ui.icon.factory import IconFactory
from PySide import QtGui, QtCore

# -----------------------------------------------------------------------------
class MariShelf(object):

    # -------------------------------------------------------------------------
    def __init__(self, name, layout=None, widget=None, palette=None):
        self._name = name

        if not layout:
            layout = QtGui.QVBoxLayout()
        self._layout = layout

        if not widget:
            widget = QtGui.QWidget()
            widget.setLayout(self.layout)
        self._widget = widget

        if not palette:
            palette = mari.palettes.create(name, widget)
        self._palette = palette

        self._palette.show()

    # -------------------------------------------------------------------------
    def add_button(self, **kwargs):

        import sys
        # so not sure if this is going to work, yay programming!
        # intercept/adjust some of the arguments
        label = ''
        cmd = ''

        for (key, val) in kwargs.iteritems():

            # get label
            if key.startswith("label"):
                label = val

            # get command...
            if key.startswith("command"):
                cmd = val

            # get full image path
            if key.startswith("image") and IconFactory.is_icon_path(val):
                button = QtGui.QPushButton(
                    QtGui.QPixmap(self.icon_factory.disk_path(val)), label)
                button.clicked.connect(lambda: self._exec_cmd(cmd))
                self.layout.addWidget(button)

    # -------------------------------------------------------------------------
    def create(self):
        self._palette = mari.palettes.create(self.name, self.widget)
        self._palette.show()

    # -------------------------------------------------------------------------
    def delete(self):
        mari.palettes.remove(self.name)

    # -------------------------------------------------------------------------
    @property
    def exists(self):
        return mari.palettes.find(self.name)

    # -------------------------------------------------------------------------
    @property
    def icon_factory(self):
        
        if not hasattr(self, '_icon_factory'):
            self._icon_factory = IconFactory()

        return self._icon_factory

    # -------------------------------------------------------------------------
    @property
    def palette(self):
        return self._palette

    # -------------------------------------------------------------------------
    @property
    def layout(self):
        return self._layout
    
    # -------------------------------------------------------------------------
    @property
    def name(self):
        return self._name

    # -------------------------------------------------------------------------
    @property
    def widget(self):
        return self._widget

    # -------------------------------------------------------------------------
    def _exec_cmd(self, cmd):
        # to work with the way the shelves.cfg is setup
        if cmd:
            exec cmd
