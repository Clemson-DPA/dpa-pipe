#!/usr/bin/env python
"""Goodbye World in pyqt."""

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import sys
from PySide import QtCore, QtGui

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class GoodbyeWorldWidget(QtGui.QPushButton):
    """A simple button that quits the application."""
    
    # -------------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor."""

        super(GoodbyeWorldWidget, self).__init__(parent)

        self.setText("Goodbye World!")

        self.clicked.connect(QtCore.QCoreApplication.quit)
        
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    
    app = QtGui.QApplication(sys.argv)
    win = GoodbyeWorldWidget()
    win.show()
    sys.exit(app.exec_())

