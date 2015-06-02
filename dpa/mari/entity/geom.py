
import os.path
import re

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError

from dpa.config import Config
from PySide import QtGui, QtCore

# -----------------------------------------------------------------------------
class GeomEntity(Entity):

    category = "geom"
    exportable = False

    # -------------------------------------------------------------------------
    # I'm hacking this until we get a proper subscribe and import dialogue
    @classmethod
    def import_product(cls, file_path, session):
        pass

    # -------------------------------------------------------------------------
    @classmethod
    def get_products(cls, session, app, category):
        sublist = defaultdict(dict)

        # for now, get only products available from subs with same category
        for sub in session.ptask_version.subscriptions:
            product_ver = sub.product_version
            product = product_ver.product

            if product.category == category:
                import_path = os.path.join(session.ptask_area.path,
                    'import', app, product.name, product.category)

                if not os.path.exists(import_path):
                    raise EntityError("Import directory does not exist: " +
                        import_path + ". Please make sure the subscription "
                        " is correct.")

                sublist[product.name] = import_path

        return sublist

    # -------------------------------------------------------------------------
    def create_ui(self):
        # get available products and configuration
        self._get_products()
        self.read_cfg('channels')



    # -------------------------------------------------------------------------
    def create_project(self):
        # very mari specific
        pass

        

    # -------------------------------------------------------------------------
    def read_cfg(self, action):
        app_name = self.session_app_name

        self._opts = defaultdict(dict)
        
        rel_cfg = os.path.join('config', app_name, self.category, action)
        rel_cfg += '.cfg'

        ptask_area = self.session.ptask_area
        action_cfg = ptask_area.config(rel_cfg, composite_ancestors=True)

        if not action_acfg or not hasattr(action_cfg, 'channels'):
            raise ActionError(
                "Cannot create mari project without set config.")

        for (ch, options) in action_cfg.channels.iteritems():
            self._opts[ch] = options

    #  -------------------------------------------------------------------------
    @property
    def opts(self):
        if not hasattr(self, '_opts'):
            return defaultdict(dict)

        return self._opts

    #  -------------------------------------------------------------------------
    @property
    def sublist(self):
        if not hasattr(self, '_sublist'):
            return defaultdict(dict)

        return self._sublist

    # -------------------------------------------------------------------------
    def _get_products(self, app):
        self._sublist = self.__class__.get_products(self.session, app, 
            self.category)
        return self._sublist

# -----------------------------------------------------------------------------
EntityRegistry().register('mari', GeomEntity)
