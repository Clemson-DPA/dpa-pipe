
from PySide import QtCore, QtGui

from dpa.config import Config
from dpa.ui.icon.factory import IconFactory

REQUIRED = "<a>&#x2727;</a>" 

# -----------------------------------------------------------------------------
class ActionOptionHeader(QtGui.QWidget):

    # -------------------------------------------------------------------------
    def __init__(self, text, icon_path=None, parent=None):

        super(ActionOptionHeader, self).__init__(parent=parent)

        self._label = QtGui.QLabel(text + " :")
        self._label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        font = self._label.font()
        self._size = font.pointSize() + 16

        self._layout = QtGui.QHBoxLayout()
        self._layout.setSpacing(4)
        self._layout.setContentsMargins(0, 0, 0, 0)

        if icon_path:
            pixmap = QtGui.QPixmap(icon_path)
            pixmap = pixmap.scaledToHeight(
                self._size, QtCore.Qt.SmoothTransformation)
            self._icon_lbl = QtGui.QLabel()
            self._icon_lbl.setPixmap(pixmap)
            self._layout.addWidget(self._icon_lbl)

        self._layout.addWidget(self._label)
        self._layout.addStretch()
        self._layout.setStretchFactor(self._label, 99)

        self.setLayout(self._layout)

    # -------------------------------------------------------------------------
    def setText(self, text):
        self.label.setText(text)

    # -------------------------------------------------------------------------
    def text(self):
        return self.label.text()

    # -------------------------------------------------------------------------
    @property
    def label(self):
        return self._label

    # -------------------------------------------------------------------------
    @property
    def layout(self):
        return self._layout

# -----------------------------------------------------------------------------
class ActionOptionGroupHeader(ActionOptionHeader):

    # -------------------------------------------------------------------------
    def __init__(self, text, icon_path=None, parent=None):

        super(ActionOptionGroupHeader, self).__init__(
            text, icon_path=icon_path, parent=parent)

        font = self._label.font()
        font.setBold(True)
        self._label.setFont(font)

        self._btn = QtGui.QPushButton('+')
        self._btn.setFixedSize(QtCore.QSize(self._size, self._size))
        self._btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self._btn.setCheckable(True)

        self._layout.insertWidget(0, self._btn)
        self._btn.toggled.connect(self._toggle)

    # -------------------------------------------------------------------------
    def _toggle(self, checked):
        
        if checked:
            self.button.setText('-')
        else:
            self.button.setText('+')

    # -------------------------------------------------------------------------
    @property
    def button(self):
        return self._btn

# -----------------------------------------------------------------------------
class ActionOption(object):

    option_type = None
    _registry = {}
    _icon_factory = IconFactory()

    # -----------------------------------------------------------------------------
    @classmethod
    def register(cls, option_cls):
        cls._registry[option_cls.option_type] = option_cls

    # -----------------------------------------------------------------------------
    @classmethod
    def factory(cls, option_type):
        
        try:
            return cls._registry[option_type]
        except KeyError:
            raise TypeError("Unknown option type: " + str(option_type))

    # -----------------------------------------------------------------------------
    def __init__(self, name, config):
        
        self._name = name
        self._default = config.get('default', None)
        self._help = config.get('help', None)
        self._icon_path = self.__class__._icon_factory.disk_path(
            config.get('icon', None))
        self._header = ActionOptionHeader(
            config.get('label', name),
            icon_path=self.icon_path,
        )
        self._required = config.get('required', False)
        self._disabled = config.get('disabled', False)

    # -----------------------------------------------------------------------------
    @property
    def value_ok(self):
        if not self.required:
            return True

        return self.value is not None

    # -----------------------------------------------------------------------------
    @property
    def default(self):
        return self._default

    # -----------------------------------------------------------------------------
    @property
    def help(self):
        return self._help

    # -----------------------------------------------------------------------------
    @property
    def icon_path(self):
        return self._icon_path

    # -----------------------------------------------------------------------------
    @property
    def header(self):
        return self._header

    # -----------------------------------------------------------------------------
    @property
    def name(self):
        return self._name

    # -----------------------------------------------------------------------------
    @property
    def layout(self):
        return QtCore.Qt.Vertical

    # -----------------------------------------------------------------------------
    @property
    def required(self):
        return self._required

    # -----------------------------------------------------------------------------
    @property
    def disabled(self):
        return self._disabled
    
    # -----------------------------------------------------------------------------
    @property
    def tooltip(self):
        return """
            <b>{hlp}</b><br><br>
            type: <b>{typ}</b><br>
            required: <b>{req}</b><br>
            default: <b>{default}</b><br>
        """.format(
            hlp=self.help,
            typ=self.type,
            req=str(self.required),
            default=str(self.default)
        )

    # -----------------------------------------------------------------------------
    @property
    def type(self):
        return self.__class__.option_type

# -----------------------------------------------------------------------------
class ActionOptionNumeric(ActionOption):

    # -----------------------------------------------------------------------------
    def __init__(self, name, config):
        
        super(ActionOptionNumeric, self).__init__(name, config)

        self._min = config.get('min', 0)
        self._max = config.get('max', 100)
        self._step = config.get('step', 1)

    # -----------------------------------------------------------------------------
    @property
    def min(self):
        return self._min

    # -----------------------------------------------------------------------------
    @property
    def max(self):
        return self._max

    # -----------------------------------------------------------------------------
    @property
    def step(self):
        return self._step

# -----------------------------------------------------------------------------
class ActionOptionBool(ActionOption, QtGui.QCheckBox):

    option_type = 'bool'

    value_changed = QtCore.Signal()

    # -------------------------------------------------------------------------
    def __init__(self, name, config, parent=None):
        
        ActionOption.__init__(self, name, config)
        QtGui.QCheckBox.__init__(self, parent=parent)

        self.setChecked(bool(self.default))
        self.setDisabled(bool(self.disabled))
        self.setToolTip(self.tooltip)

        self.stateChanged.connect(lambda s: self.value_changed.emit())

    # -----------------------------------------------------------------------------
    @property
    def layout(self):
        return QtCore.Qt.Horizontal

    # -------------------------------------------------------------------------
    @property
    def value(self):
        return self.isChecked()

# -----------------------------------------------------------------------------
class ActionOptionFloat(ActionOptionNumeric, QtGui.QDoubleSpinBox):

    option_type = 'float' 

    value_changed = QtCore.Signal()

    # -------------------------------------------------------------------------
    def __init__(self, name, config, parent=None):
        
        ActionOptionNumeric.__init__(self, name, config)
        QtGui.QDoubleSpinBox.__init__(self, parent=parent)

        self.setMaximum(float(self.max))
        self.setMinimum(float(self.min))
        self.setSingleStep(float(self.step))

        self.setToolTip(self.tooltip)
        self.setValue(float(self.default))

        self.valueChanged.connect(lambda v: self.value_changed.emit())

    # -------------------------------------------------------------------------
    @property
    def value(self):
        return QtGui.QDoubleSpinBox.value(self)

# -----------------------------------------------------------------------------
class ActionOptionInt(ActionOptionNumeric, QtGui.QSpinBox):

    option_type = 'int'

    value_changed = QtCore.Signal()

    # -------------------------------------------------------------------------
    def __init__(self, name, config, parent=None):
        
        ActionOptionNumeric.__init__(self, name, config)
        QtGui.QSpinBox.__init__(self, parent=parent)

        self.setMaximum(int(self.max))
        self.setMinimum(int(self.min))
        self.setSingleStep(int(self.step))

        self.setToolTip(self.tooltip)
        self.setValue(int(self.default))

        self.valueChanged.connect(lambda v: self.value_changed.emit())

    # -------------------------------------------------------------------------
    @property
    def value(self):
        return QtGui.QSpinBox.value(self)

# -----------------------------------------------------------------------------
class ActionOptionList(ActionOption, QtGui.QListWidget):

    option_type = 'list'

    value_changed = QtCore.Signal()
    
    # -------------------------------------------------------------------------
    def __init__(self, name, config, parent=None):
        
        ActionOption.__init__(self, name, config)
        QtGui.QListWidget.__init__(self, parent=parent)

        self._choices = config.get('choices', [])
        self._multiple = config.get('multiple', False)

        self.setToolTip(self.tooltip)
        self.addItems(self.choices)
        if self.multiple:
            self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        else:
            self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        if self.multiple:
            for text in self.default:
                items = self.findItems(text, QtCore.Qt.MatchExactly) 
                for item in items:
                    item.setSelected(True)
        else:
            items = self.findItems(self.default, QtCore.Qt.MatchExactly) 
            for item in items:
                item.setSelected(True)

        self.itemSelectionChanged.connect(lambda: self.value_changed.emit())

    # -----------------------------------------------------------------------------
    @property
    def value_ok(self):
        if not self.required:
            return True

        # something must be selected
        return len(self.selectedItems()) > 0

    # -------------------------------------------------------------------------
    @property
    def choices(self):
        return self._choices

    # -------------------------------------------------------------------------
    @property
    def multiple(self):
        return self._multiple

    # -------------------------------------------------------------------------
    @property
    def value(self):
        return [str(i.text()) for i in self.selectedItems()]

# -----------------------------------------------------------------------------
class ActionOptionStr(ActionOption, QtGui.QLineEdit):

    option_type = 'str'

    value_changed = QtCore.Signal()

    # -------------------------------------------------------------------------
    def __init__(self, name, config, parent=None):
        
        ActionOption.__init__(self, name, config)
        QtGui.QLineEdit.__init__(self, parent=parent)

        self.setToolTip(self.tooltip)
        self.setText(str(self.default))

        self.textChanged.connect(lambda t: self.value_changed.emit())

    # -----------------------------------------------------------------------------
    @property
    def value_ok(self):

        if not self.required:
            print "NOT REQUIRED????"
            return True

        val = str(self.value)
        val.strip()

        # something must be selected
        return val != ""

    # -------------------------------------------------------------------------
    @property
    def value(self):
        return str(self.text())

# -----------------------------------------------------------------------------
class ActionOptionText(ActionOption, QtGui.QTextEdit):

    option_type = 'text'

    value_changed = QtCore.Signal()

    # -------------------------------------------------------------------------
    def __init__(self, name, config, parent=None):
        
        ActionOption.__init__(self, name, config)
        QtGui.QTextEdit.__init__(self, parent=parent)

        self.setToolTip(self.tooltip)
        self.setText(str(self.default))

        self.textChanged.connect(lambda: self.value_changed.emit())

    # -----------------------------------------------------------------------------
    @property
    def value_ok(self):
        if not self.required:
            return True

        val = self.value
        val.strip()

        # something must be selected
        return val != ""

    # -------------------------------------------------------------------------
    @property
    def value(self):
        return str(self.toPlainText())

# -----------------------------------------------------------------------------
class ActionOptionGroup(ActionOption, QtGui.QWidget):

    option_type = 'group'

    value_changed = QtCore.Signal()

    # -------------------------------------------------------------------------
    def __init__(self, name, config, parent=None):
        
        ActionOption.__init__(self, name, config)
        QtGui.QWidget.__init__(self, parent=parent)

        self._open = config.get('open', True)
        self._options = config.get('options', Config())

        self._main_layout = QtGui.QVBoxLayout() 
        self._main_layout.setSpacing(6)
        self._main_layout.setContentsMargins(4, 4, 4, 4)

        self._widgets = []


        for (option_name, option_config) in self._options.iteritems():

            if not isinstance(option_config, Config):
                continue

            option_type = option_config.get('type', None)
            widget_cls = ActionOption.factory(option_type)
            widget = widget_cls(option_name, option_config)
            widget.value_changed.connect(lambda: self.value_changed.emit())

            self._widgets.append(widget)

            if widget.layout == QtCore.Qt.Horizontal:
                option_layout = QtGui.QHBoxLayout()
            else:
                option_layout = QtGui.QVBoxLayout()

            option_layout.setSpacing(1)
            option_layout.setContentsMargins(0, 0, 0, 0)
            option_layout.addWidget(widget.header)
            option_layout.addWidget(widget)
            option_layout.setStretchFactor(widget, 90)

            self._main_layout.addLayout(option_layout)

            if widget.required:
                required_lbl = QtGui.QLabel(REQUIRED)
                if widget.layout == QtCore.Qt.Horizontal:
                    option_layout.addWidget(required_lbl)
                else:
                    widget.header.layout.addWidget(required_lbl)

        if len(self._widgets) == 0:
            self._main_layout.addWidget(QtGui.QLabel("No options"))

        self.setLayout(self._main_layout)

        self._header = ActionOptionGroupHeader(
            config.get('label', name),
            icon_path=self.icon_path,
        )
        self._header.button.toggled.connect(self.toggle)

        if self.open:
            self._header.button.setDown(True)
            self._header.button.setText('-')
        else:
            self.hide()

    # -------------------------------------------------------------------------
    def toggle(self, checked):
        
        if checked:
            self.show()
        else:
            self.hide()

    # -------------------------------------------------------------------------
    @property
    def value_ok(self):

        for widget in self.widgets:
            if not widget.value_ok:
                return False

        return True

    # -------------------------------------------------------------------------
    @property
    def open(self):
        return self._open

    # -------------------------------------------------------------------------
    @property
    def options(self):
        return self._options

    # -----------------------------------------------------------------------------
    @property
    def required(self):
        
        for widget in self.widgets:
            if widget.required:
                return True

        return False

    # -------------------------------------------------------------------------
    @property
    def value(self):
        
        value = Config()
        for widget in self.widgets:
            value[widget.name] = widget.value

        return value

    # -------------------------------------------------------------------------
    @property
    def widgets(self):
        return self._widgets

# -----------------------------------------------------------------------------
class ActionOptionWidget(ActionOptionGroup):

    # -------------------------------------------------------------------------
    def __init__(self, config, name='root', parent=None):

        super(ActionOptionWidget, self).__init__(name, config)

        show_required_label = False
        for widget in self.widgets:
            if widget.required:
                show_required_label = True
                break

        if show_required_label:
            required_label = QtGui.QLabel(REQUIRED + ' required options')
            required_label.setAlignment(QtCore.Qt.AlignRight)
            self._main_layout.addWidget(required_label)
    
# -----------------------------------------------------------------------------
# register all the option types
ActionOption.register(ActionOptionBool)
ActionOption.register(ActionOptionFloat)
ActionOption.register(ActionOptionGroup)
ActionOption.register(ActionOptionInt)
ActionOption.register(ActionOptionList)
ActionOption.register(ActionOptionStr)
ActionOption.register(ActionOptionText)
ActionOption.register(ActionOptionGroup)

# XXX ability to highlight/clear required widgets that aren't properly filled
# out
