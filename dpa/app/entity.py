
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import defaultdict
import os

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
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

    _option_configs = {}

    # -------------------------------------------------------------------------
    @classmethod
    def option_config(cls, session, action, file_type=None):
        """Get a config option for this entity class for the given action."""

        app_name = session.app_name
        id_str = app_name + action + str(file_type)

        if id_str in cls._option_configs:
            return cls._option_configs[id_str]

        ptask_type_lookup = session.ptask.types

        rel_config = os.path.join('config', app_name, cls.category, action)
        if file_type:
            rel_config += "_" + file_type
        rel_config += '.cfg'

        ptask_area = session.ptask_area
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
                    
                    if not filter_name in ptask_type_lookup:
                        match = False
                        break

                    if not ptask_type_lookup[filter_name] == val:
                        match = False
                        break

                if match:
                    configs_to_composite.append(
                        section_config.get('options', Config())
                    )

        composited = Config.composite(configs_to_composite)

        config = Config()
        config.add('options', composited)

        cls._option_configs[id_str] = config

        return config

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
    def _create_product(self, product_desc, version_note, file_type,
        resolution="none"):

        # use the product create action to create the product if it doesn't
        # exist.
        create_action_cls = ActionRegistry().get_action('create', 'product')
        if not create_action_cls:
            raise EntityError("Unable to find product creation action.")

        create_action = create_action_cls(
            product=self.display_name,
            ptask=self.session.ptask_version.ptask_spec,
            version=self.session.ptask_version.number,
            category=self.category,
            description=product_desc,
            file_type=file_type,
            resolution=resolution,
            note=version_note,
        )

        try:
            create_action()
        except ActionError as e:
            raise EntityError("Unable to export entity: " + str(e))

        return create_action.product_repr

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
                self._display_name += "_" + str(self.instance)

        return self._display_name

    # -------------------------------------------------------------------------
    @property
    def exportable(self):
        return True

    # -------------------------------------------------------------------------
    @property
    def importable(self):
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

