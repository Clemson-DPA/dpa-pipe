
import os.path
import re

from PySide import QtGui, QtCore

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError
from dpa.config import Config


# -----------------------------------------------------------------------------
class GeomEntity(Entity):

    category = "geom"
    exportable = False

    # -------------------------------------------------------------------------
    # I'm hacking this until we get a proper subscribe and import dialogue
    def export(self):
        pass

    # -------------------------------------------------------------------------
    def import_product(self):
        # if OBJ file....
        if self.session.mari.projects.current():
            raise EntityError("Cannot have a project open when importing.")

        self.create_ui()

    # -------------------------------------------------------------------------
    @classmethod
    def get_files(cls, session, app, category):
        sublist = defaultdict(dict)

        # for now, get only products available from existing subs with 
        # same category
        for sub in session.ptask_version.subscriptions:
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

        return sublist

    # -------------------------------------------------------------------------
    def create_ui(self):
        # get available products and configuration
        self._get_importables()
        self._read_cfg('channels')

        # should become a part of the UI import wizard class
        import_menu = QtGui.QDialog()

        # should really only import one at a time
        fileChoice = QtGui.QComboBox()
        for (spec, values) in self.sublist:
            fileChoice.addItem(spec, values)

        self._file_selected = [
            fileChoice.itemData(fileChoice.currentIndex())[0],
            fileChoice.itemData(fileChoice.currentIndex())[1]
        ]
        
        fileChoice.currentIndexChanged.connect(
            lambda: self._get_selected([
                fileChoice.itemData(fileChoice.currentIndex())[0], 
                fileChoice.itemData(fileChoice.currentIndex())[1]
            ])
        )

        file_menu = QtGui.QFormLayout()
        file_menu.addRow('Choose Product: ', fileChoice)

        import_btn = QtGui.QPushButton("Import")
        import_btn.clicked.connect(self._create_project())

        layout = QtGui.GridLayosut()
        layout.addItem(file_menu, 1, 0)
        layout.addItem(import_btn, 1, 1)

        import_menu.setLayout(layout)
        import_menu.setWindowTitle("Import Subscription File")
        import_menu.setMinimumWidth(500)
        import_menu.setMinimumHeight(150)

        self.session.mari.utils.execDialog(import_menu)

    # -------------------------------------------------------------------------
    def create_project(self, file_name, file_path):
        # very mari specific
        add_channels = []

        for (ch_name, opts) in self.opts.channels.iteritems():
            if 'color' in opts:
                color = self.sesion.mari.Color(opts['color'][0],
                    opts['color'][1], opts['color'][2], opts['color'][3])
            else:
                color = self.session.mari.Color(0.5,0.5,0.5,1.0)

            if 'alpha' in opts:
                alpha = opts['alpha']
            else:
                alpha = True

            # create channels
            ch = self.session.mari.app.ChannelInfo(ch_name, use_alpha=alpha,
                fill_color=color)

            if 'depth' in opts:
                ch.setDepth(opts['depth'][0])
            else:
                ch.setDepth(16)

            # create the srgb2linear layer if needed
            # should consider other layers in cfg but not right now
            for (layer_type, vals) in opts['layer']:
                try:
                    if layer_type == 'adjustment':
                        ch.createAdjustmentLayer(vals[0],vals[1])
                except:
                    raise EntityError('Must have 2 values for layer type: ' +
                        layer_type + '. Name and then layer primary key. '
                        'Otherwise, please make sure the layer primary key is '
                        'correct.')

            add_channels.append(ch)

        # creates project
        self.session.mari.projects.create(file_name, work_name, 
            add_channels)

    # -------------------------------------------------------------------------
    def _read_cfg(self, action):
        app_name = self.session_app_name

        self._opts = defaultdict(dict)
        
        rel_cfg = os.path.join('config', app_name, self.category, action)
        rel_cfg += '.cfg'

        ptask_area = self.session.ptask_area
        action_cfg = ptask_area.config(rel_cfg, composite_ancestors=True)

        if not action_acfg or not hasattr(action_cfg, 'channels'):
            raise ActionError(
                "Cannot create mari project without set config.")

        self._opts = action_cfg

    #  -------------------------------------------------------------------------
    @property
    def opts(self):
        if not hasattr(self, '_opts'):
            return defaultdict(dict)

        return self._opts

# -----------------------------------------------------------------------------
EntityRegistry().register('mari', GeomEntity)
