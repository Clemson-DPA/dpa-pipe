#!/usr/bin/env python
"""Hello World in pyqt."""

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import sys
from PyQt4 import QtGui

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class HelloWorldWidget(QtGui.QLabel):

    # -------------------------------------------------------------------------
    def __init__(self, parent=None):
        """A label with a greeting."""

        super(HelloWorldWidget, self).__init__(parent)

        self.setText("Hello World!")
        
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    
    app = QtGui.QApplication(sys.argv)
    win = HelloWorldWidget()
    win.show()
    sys.exit(app.exec_())

