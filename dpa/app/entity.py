
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import defaultdict
import os

from dpa.config import Config
from dpa.ptask.spec import PTaskSpec
from dpa.singleton import Singleton

# -----------------------------------------------------------------------------
class EntityRegistry(Singleton):

    # -------------------------------------------------------------------------
    def init(self):
        self._registry = defaultdict(list)

    # -------------------------------------------------------------------------
    def get_entity_classes(self, app_name):

        # XXX should be filtered based on current ptask. 
        # for example, anim stages may want to expose different entity types
        # than modeling or lighting

        return self._registry.get(app_name, [])

    # -------------------------------------------------------------------------
    def register(self, app_name, cls):
        self._registry[app_name].append(cls)
        
# -----------------------------------------------------------------------------
class Entity(object):

    __metaclass__ = ABCMeta

    category = None

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, session, instance=None):
        """Retrieve an entity instance from the supplied session."""
        return None

    # -------------------------------------------------------------------------
    @classmethod
    def import_file(cls, file_path, session, *args, **kwargs):
        """Import a file into the session.
        
        Returns the newly imported file as an entity.
        """
        pass

    # -------------------------------------------------------------------------
    @classmethod
    def list(cls, session):
        """Retrieve all entities of this type from the supplied session."""
        return []

    # -------------------------------------------------------------------------
    def __init__(self, name, session, instance=None):
        self._name = name
        self._session = session
        self._instance = instance

    # -------------------------------------------------------------------------
    @abstractmethod
    def export(self, *args, **kwargs):
        """Export this entity to a product."""

    # -------------------------------------------------------------------------
    def option_config(self, action):
        """Get a config option for this entity for the given action."""

        if hasattr(self, '_option_config'):
            return self._option_config

        app_name = self.session.app_name
        type_lookup = self.session.ptask.types

        rel_config = os.path.join('config', app_name, self.category, action)
        rel_config += '.cfg'

        ptask_area = self.session.ptask_area
        action_config = ptask_area.config(rel_config, composite_ancestors=True)

        configs_to_composite = []

        for (section_name, section_config) in action_config.iteritems():

            if section_name == "global":
                configs_to_composite.append(
                    section_config.get('options', Config()))
            else:
                match = True
                for (filter_name, val) in section_config.iteritems():
                    if filter_name == 'options':
                        continue
                    
                    if not filter_name in type_lookup:
                        match = False
                        break

                    if not type_lookup[filter_name] == val:
                        match = False
                        break

                if match:
                    configs_to_composite.append(
                        section_config.get('options', Config())
                    )

        composited = Config.composite(configs_to_composite)

        self._option_config = Config()
        self._option_config.add('options', composited)

        return self._option_config

    # -------------------------------------------------------------------------
    @property
    def category(self):
        """Returns the category name for this entity."""
        return self.__class__.category

    # -------------------------------------------------------------------------
    @property
    def display_name(self):

        if not hasattr(self, "_display_name"):

            self._display_name = self.name
            if self.instance:
                self._display_name += str(self.instance)

        return self._display_name

    # -------------------------------------------------------------------------
    @property
    def exportable(self):
        return True

    # -------------------------------------------------------------------------
    @property
    def instance(self):
        return self._instance

    # -------------------------------------------------------------------------
    @property
    def name(self):
        """Returns the name of this entity."""
        return self._name

    # -------------------------------------------------------------------------
    @property
    def product_name(self):
        """Returns the product name for this entity."""

        return PTaskSpec.SEPARATOR.join([self.display_name, self.category])

    # -------------------------------------------------------------------------
    @property
    def session(self):
        """Returns the session instance for this entity."""
        return self._session

# -----------------------------------------------------------------------------
class EntityError(Exception):
    pass

